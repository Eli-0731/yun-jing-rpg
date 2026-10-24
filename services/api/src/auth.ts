import { randomBytes, randomUUID, createHash } from 'node:crypto';
import { getApps, initializeApp } from 'firebase-admin/app';
import { getAuth } from 'firebase-admin/auth';
import { Game, ensure, hash } from './game';
import { Sql } from './database';

export class Auth {
  constructor(public game: Game, public mode: 'local' | 'production') {}
  async local(alias: unknown) {
    ensure(this.mode === 'local', 'LOCAL_DISABLED', '本機測試登入未開放', 403);
    ensure(typeof alias === 'string' && /^[a-z0-9_-]{1,24}$/.test(alias), 'INVALID_ALIAS', '測試身分請用 1–24 字元英文小寫或數字');
    const id = await this.game.playerFor(`local:${alias}`, alias);
    return this.game.db.transaction(tx => this.issue(tx, id));
  }
  async authenticate(authorization?: string) {
    ensure(typeof authorization === 'string' && authorization.startsWith('Bearer '), 'UNAUTHORIZED', '請先登入', 401);
    const token = authorization.substring(7);
    const row = await this.game.db.transaction(async tx => (await tx.query<{ player_id: string; expires_at: string }>('SELECT player_id,expires_at FROM sessions WHERE token_hash=$1', [hash(token)])).rows[0]);
    ensure(row && Number(row.expires_at) > this.game.now(), 'SESSION_EXPIRED', '登入已到期，請重新登入', 401);
    return row.player_id;
  }
  private async issue(tx: Sql, playerId: string) {
    await tx.query('SELECT id FROM players WHERE id=$1 FOR UPDATE', [playerId]);
    await tx.query('DELETE FROM sessions WHERE player_id=$1', [playerId]);
    await tx.query('DELETE FROM refresh_tokens WHERE player_id=$1', [playerId]);
    const token = randomBytes(32).toString('base64url'); const refreshToken = randomBytes(32).toString('base64url');
    const expiresAt = this.game.now() + 15 * 60_000;
    await tx.query('INSERT INTO sessions(token_hash,player_id,expires_at) VALUES($1,$2,$3)', [hash(token), playerId, expiresAt]);
    await tx.query('INSERT INTO refresh_tokens(token_hash,player_id,expires_at) VALUES($1,$2,$3)', [hash(refreshToken), playerId, this.game.now() + 30 * 86400000]);
    return { playerId, token, refreshToken, expiresAt };
  }
  async refresh(token: unknown) {
    ensure(typeof token === 'string' && token.length < 100, 'INVALID_TOKEN', '無效更新憑證', 401);
    return this.game.db.transaction(async tx => {
      // Lock the player before checking the token; simultaneous refreshes cannot both win.
      const candidate = (await tx.query<{ player_id: string }>('SELECT player_id FROM refresh_tokens WHERE token_hash=$1', [hash(token)])).rows[0];
      ensure(candidate, 'SESSION_EXPIRED', '請重新登入', 401);
      await tx.query('SELECT id FROM players WHERE id=$1 FOR UPDATE', [candidate.player_id]);
      const row = (await tx.query<{ expires_at: string }>('SELECT expires_at FROM refresh_tokens WHERE token_hash=$1', [hash(token)])).rows[0];
      ensure(row && Number(row.expires_at) > this.game.now(), 'SESSION_EXPIRED', '請重新登入', 401);
      return this.issue(tx, candidate.player_id);
    });
  }
  async challenge(codeChallenge: unknown) {
    ensure(typeof codeChallenge === 'string' && /^[A-Za-z0-9_-]{43}$/.test(codeChallenge), 'INVALID_PKCE', '需要 S256 PKCE challenge');
    const id = randomUUID();
    await this.game.db.transaction(tx => tx.query('INSERT INTO challenges(id,verifier_hash,expires_at) VALUES($1,$2,$3)', [id, codeChallenge, this.game.now() + 300000]));
    return { id, expiresIn: 300, loginPath: `/login.html?challenge=${id}` };
  }
  async authorize(challengeId: unknown, firebaseToken: unknown) {
    ensure(typeof challengeId === 'string' && typeof firebaseToken === 'string', 'INVALID_AUTH', '缺少驗證資料');
    ensure(process.env.FIREBASE_PROJECT_ID, 'AUTH_NOT_CONFIGURED', '尚未設定遊戲專用 Firebase 專案', 503);
    if (!getApps().length) initializeApp({ projectId: process.env.FIREBASE_PROJECT_ID });
    const decoded = await getAuth().verifyIdToken(firebaseToken, true);
    ensure(decoded.email_verified, 'EMAIL_NOT_VERIFIED', '請先驗證電子信箱', 403);
    const playerId = await this.game.playerFor(`firebase:${decoded.uid}`, String(decoded.name ?? decoded.email?.split('@')[0] ?? '修行者').slice(0, 32));
    return this.game.db.transaction(async tx => {
      const row = (await tx.query<{ expires_at: string; consumed: boolean; player_id: string | null }>('SELECT * FROM challenges WHERE id=$1 FOR UPDATE', [challengeId])).rows[0];
      ensure(row && !row.consumed && !row.player_id && Number(row.expires_at) > this.game.now(), 'INVALID_CHALLENGE', '登入請求已到期或使用', 409);
      await tx.query('UPDATE challenges SET player_id=$2 WHERE id=$1', [challengeId, playerId]);
      return { authorized: true, name: decoded.name ?? '修行者' };
    });
  }
  async exchange(id: unknown, verifier: unknown) {
    ensure(typeof id === 'string' && typeof verifier === 'string' && /^[A-Za-z0-9._~-]{43,128}$/.test(verifier), 'INVALID_PKCE', '無效登入交換');
    return this.game.db.transaction(async tx => {
      const row = (await tx.query<{ verifier_hash: string; expires_at: string; consumed: boolean; player_id: string | null }>('SELECT * FROM challenges WHERE id=$1 FOR UPDATE', [id])).rows[0];
      ensure(row && !row.consumed && Number(row.expires_at) > this.game.now(), 'INVALID_CHALLENGE', '登入請求已到期或使用', 409);
      ensure(createHash('sha256').update(verifier).digest('base64url') === row.verifier_hash, 'INVALID_PKCE', '登入驗證不相符', 401);
      if (!row.player_id) return { pending: true };
      await tx.query('UPDATE challenges SET consumed=true WHERE id=$1', [id]);
      return this.issue(tx, row.player_id);
    });
  }
}
