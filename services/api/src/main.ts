import { configuration, createApp } from './app';
async function main() {
  const config = configuration();
  const { app, game } = await createApp(config);
  await app.listen(config.port, config.host);
  console.log(`雲境 API: http://${config.host}:${config.port} (${config.mode}; growth speed ${config.speed}x)`);
  const stop = async () => { await app.close(); await game.db.close(); process.exit(0); };
  process.once('SIGINT', stop); process.once('SIGTERM', stop);
}
main().catch(error => { console.error(error.message); process.exitCode = 1; });
