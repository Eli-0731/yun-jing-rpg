import { PGlite } from '@electric-sql/pglite';
import { Pool, PoolClient } from 'pg';
import { mkdirSync } from 'node:fs';
import { resolve } from 'node:path';

export interface Sql {
  query<T extends Record<string, any> = Record<string, unknown>>(sql: string, parameters?: unknown[]): Promise<{ rows: T[] }>;
}

const schema = `
CREATE TABLE IF NOT EXISTS schema_versions(version integer PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE IF NOT EXISTS players(id text PRIMARY KEY, subject text UNIQUE NOT NULL, state jsonb NOT NULL, version integer NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS births(player_id text PRIMARY KEY REFERENCES players(id), payload jsonb NOT NULL);
CREATE TABLE IF NOT EXISTS worlds(id text PRIMARY KEY, state jsonb NOT NULL, version integer NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS receipts(actor_id text NOT NULL, request_id text NOT NULL, fingerprint text NOT NULL, result jsonb NOT NULL, PRIMARY KEY(actor_id, request_id));
CREATE TABLE IF NOT EXISTS ledger(id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, actor_id text NOT NULL, request_id text NOT NULL, changes jsonb NOT NULL, created_at timestamptz NOT NULL DEFAULT now(), UNIQUE(actor_id,request_id));
CREATE TABLE IF NOT EXISTS sessions(token_hash text PRIMARY KEY, player_id text NOT NULL REFERENCES players(id), expires_at bigint NOT NULL);
CREATE TABLE IF NOT EXISTS refresh_tokens(token_hash text PRIMARY KEY, player_id text NOT NULL REFERENCES players(id), expires_at bigint NOT NULL);
CREATE TABLE IF NOT EXISTS challenges(id text PRIMARY KEY, verifier_hash text NOT NULL, expires_at bigint NOT NULL, consumed boolean NOT NULL DEFAULT false, player_id text REFERENCES players(id));
CREATE TABLE IF NOT EXISTS companion_links(id text PRIMARY KEY, player_id text UNIQUE NOT NULL REFERENCES players(id), companion_id text UNIQUE NOT NULL, active boolean NOT NULL DEFAULT true);
CREATE TABLE IF NOT EXISTS transfers(id text PRIMARY KEY, player_id text NOT NULL REFERENCES players(id), link_id text NOT NULL, quantity integer NOT NULL CHECK(quantity > 0), status text NOT NULL CHECK(status IN ('received','cancelled')), at_ms bigint NOT NULL);
CREATE INDEX IF NOT EXISTS transfers_window ON transfers(player_id,at_ms) WHERE status='received';
CREATE TABLE IF NOT EXISTS room_tickets(ticket_hash text PRIMARY KEY, player_id text NOT NULL REFERENCES players(id), room_id text NOT NULL, expires_at bigint NOT NULL, consumed boolean NOT NULL DEFAULT false);
CREATE TABLE IF NOT EXISTS hunt_deaths(death_id text PRIMARY KEY, room_id text NOT NULL, spawn_id text NOT NULL, fingerprint text NOT NULL, receipt jsonb NOT NULL, occurred_at bigint NOT NULL, UNIQUE(room_id,spawn_id));
CREATE TABLE IF NOT EXISTS merchant_proximity(player_id text PRIMARY KEY REFERENCES players(id), room_id text NOT NULL, merchant_id text NOT NULL, valid_until bigint NOT NULL);
INSERT INTO schema_versions(version) VALUES(1) ON CONFLICT DO NOTHING;
`;

export class Database {
  private local?: PGlite;
  private pool?: Pool;
  private queue: Promise<void> = Promise.resolve();
  constructor(options: { url?: string; directory?: string } = {}) {
    if (options.url) this.pool = new Pool({ connectionString: options.url, max: 10 });
    else {
      if (options.directory) mkdirSync(resolve(options.directory), { recursive: true });
      this.local = new PGlite(options.directory);
    }
  }
  async initialize() {
    if (this.local) { await this.local.waitReady; await this.local.exec(schema); }
    else await this.pool!.query(schema);
  }
  async query<T extends Record<string, any> = Record<string, unknown>>(sql: string, parameters: unknown[] = []): Promise<{ rows: T[] }> {
    if (this.local) return this.local.query<T>(sql, parameters);
    return this.pool!.query<T>(sql, parameters);
  }
  async transaction<T>(work: (sql: Sql) => Promise<T>): Promise<T> {
    if (this.local) {
      // PGlite has one connection. Serialize complete transactions, including read-only ones.
      const previous = this.queue;
      let release!: () => void;
      this.queue = new Promise<void>(done => { release = done; });
      await previous;
      try { return await this.local.transaction(tx => work(tx)); }
      finally { release(); }
    }
    const client: PoolClient = await this.pool!.connect();
    try {
      await client.query('BEGIN');
      const result = await work(client);
      await client.query('COMMIT');
      return result;
    } catch (error) { await client.query('ROLLBACK'); throw error; }
    finally { client.release(); }
  }
  async close() { await this.queue; await this.local?.close(); await this.pool?.end(); }
}
