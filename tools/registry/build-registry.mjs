// 承天｜分支、PR、資料夾總帳產生器
// 用法：在任一工作樹執行 `node tools/registry/build-registry.mjs`
// 先執行 `git fetch origin '+refs/pull/*/head:refs/remotes/origin/pr/*'` 取得每張 PR 的原始提交。
// 讀 GitHub API（用 git credential 裡的權杖，不印出）與本機 git，輸出到 docs/registry/。
import { execSync } from 'node:child_process';
import { mkdirSync, writeFileSync } from 'node:fs';

const REPO = 'z1nnz/chengtian';
const OUT = 'docs/registry';
const sh = (cmd) => execSync(cmd, { encoding: 'utf8', maxBuffer: 1 << 28 }).trim();
const tryGit = (cmd) => { try { return sh(cmd); } catch { return ''; } };

const token = execSync('git credential fill', { input: 'protocol=https\nhost=github.com\n\n' })
  .toString().match(/password=(.*)/)[1].trim();
const headers = { 'User-Agent': 'chengtian-registry', Authorization: `Bearer ${token}`, Accept: 'application/vnd.github+json' };

async function allPulls() {
  const out = [];
  for (let page = 1; page < 20; page++) {
    const r = await fetch(`https://api.github.com/repos/${REPO}/pulls?state=all&per_page=100&page=${page}`, { headers });
    const j = await r.json();
    if (!Array.isArray(j) || j.length === 0) break;
    out.push(...j);
  }
  return out.sort((a, b) => a.number - b.number);
}

// 把路徑縮成「資料夾」：art/exports/<組>、apps/game/Assets/<x>/<y>、docs/<x>、tools/<x>
function folderOf(p) {
  const s = p.split('/');
  if (s[0] === 'art' && s.length > 2) return s.slice(0, s[1] === 'incoming' ? 4 : 3).join('/');
  if (s[0] === 'apps' && s[1] === 'game' && s.length > 4) return s.slice(0, 5).join('/');
  if (['docs', 'tools', 'apps', 'services', 'packages', 'tests'].includes(s[0]) && s.length > 2) return s.slice(0, 3).join('/');
  if (s.length > 1) return s.slice(0, 2).join('/');
  return s[0];
}
const assetFolder = (f) => /^art\/(exports|source|incoming\/dondon|references|previews)\//.test(f + '/');

function summarize(files) {
  const m = new Map();
  for (const f of files) { const k = folderOf(f); m.set(k, (m.get(k) || 0) + 1); }
  return [...m.entries()].sort((a, b) => b[1] - a[1]);
}

const who = (login) => ({ Johnnnny0823: 'A', joshsu54: 'B', 'Eli-0731': 'C', z1nnz: '核心組' }[login] || login);
const state = (p) => p.merged_at ? '已合併' : p.state === 'open' ? '開啟中' : '關閉未合併';
const esc = (s) => String(s).replace(/\|/g, '\\|').replace(/\n/g, ' ');

const pulls = await allPulls();
const prFolders = new Map();
for (const p of pulls) {
  const head = p.head.sha;
  const base = tryGit(`git merge-base ${p.base.sha} ${head}`) || p.base.sha;
  const files = tryGit(`git diff --name-only ${base} ${head}`).split('\n').filter(Boolean);
  prFolders.set(p.number, { files: files.length, folders: summarize(files) });
}

// ---- prs.md
let prs = `# PR 總帳\n\n> 由 \`tools/registry/build-registry.mjs\` 產生，**不要手改**；要更新就重跑。產生時間：${new Date().toISOString().slice(0, 16).replace('T', ' ')} UTC。\n> 人：A = Johnnnny0823（John）、B = joshsu54（Josh）、C = Eli-0731（Eli）、核心組 = z1nnz（含 Claude Code、Codex 代提交）。\n\n`;
prs += `| PR | 誰 | 狀態 | 日期 | 分支 | 做了什麼（標題） | 動到的主要資料夾（檔案數） |\n|---|---|---|---|---|---|---|\n`;
for (const p of pulls) {
  const f = prFolders.get(p.number);
  const top = f.folders.slice(0, 5).map(([k, n]) => `\`${k}\`(${n})`).join('、') + (f.folders.length > 5 ? ` 等 ${f.folders.length} 處` : '');
  const date = (p.merged_at || p.closed_at || p.created_at).slice(0, 10);
  prs += `| [#${p.number}](https://github.com/${REPO}/pull/${p.number}) | ${who(p.user.login)} | ${state(p)} | ${date} | \`${p.head.label.replace('z1nnz:', '')}\` | ${esc(p.title)} | ${top || '—'} |\n`;
}

// ---- branches.md
const prByBranch = new Map();
for (const p of pulls) if (p.head.repo && p.head.repo.full_name === REPO) {
  if (!prByBranch.has(p.head.ref)) prByBranch.set(p.head.ref, []);
  prByBranch.get(p.head.ref).push(p);
}
const refs = sh(`git for-each-ref --format=%(refname:short)%09%(committerdate:short)%09%(authorname)%09%(subject) refs/remotes/origin`)
  .split('\n').map((l) => l.split('\t')).filter(([r]) => r && !r.includes('/pr/') && r !== 'origin/HEAD' && r !== 'origin');
import { readFileSync } from 'node:fs';
const notes = JSON.parse(readFileSync(new URL('./notes.json', import.meta.url), 'utf8')).branches || {};

// 內容比對：這條分支自分岔以來改過的檔案中，現在和 main 不一樣的有幾個（= main 沒有的內容）
function notInMain(ref) {
  const mb = tryGit(`git merge-base origin/main ${ref}`);
  if (!mb) return { changed: 0, differ: 0 };
  const changed = tryGit(`git diff --name-only ${mb} ${ref}`).split('\n').filter(Boolean);
  if (!changed.length) return { changed: 0, differ: 0 };
  const differ = tryGit(`git diff --name-only origin/main ${ref}`).split('\n').filter(Boolean);
  const set = new Set(changed);
  return { changed: changed.length, differ: differ.filter((f) => set.has(f)).length };
}

const rows = refs.map(([ref, date, author, subject]) => {
  const name = ref.replace(/^origin\//, '');
  const { differ } = name === 'main' ? { differ: 0 } : notInMain(ref);
  const ps = prByBranch.get(name) || [];
  const prText = ps.length ? ps.map((p) => `[#${p.number}](https://github.com/${REPO}/pull/${p.number}) ${state(p)}`).join('、') : '沒有 PR';
  const what = ps.length ? esc(ps[ps.length - 1].title) : esc(subject);
  let kind;
  if (name === 'main') kind = '主線';
  else if (name === 'feature/qingxi-creek-chapter') kind = '核心組進行中';
  else if (ps.some((p) => p.state === 'open')) kind = '待審';
  else if (differ === 0) kind = '內容都在 main，可封存';
  else if (differ <= 6 && ps.some((p) => p.merged_at)) kind = '內容都在 main（只差幾個小檔）';
  else if (/⚠/.test(notes[name] || '')) kind = '⚠ 有 main 沒有的新內容';
  else kind = '舊版或試驗，保留參考';
  return { name, date, author, differ, prText, what, kind, note: notes[name] || '' };
}).sort((a, b) => (a.name === 'main' ? -1 : b.name === 'main' ? 1 : b.date.localeCompare(a.date)));

let br = `# 分支總帳\n\n> 由 \`tools/registry/build-registry.mjs\` 產生，**不要手改**；人工判斷寫在 \`tools/registry/notes.json\`。產生時間：${new Date().toISOString().slice(0, 16).replace('T', ' ')} UTC。\n> 「main 沒有的檔案」= 這條分支改過、而現在內容和 main 不一樣的檔案數（用內容比，不是比提交編號）。0 代表分支裡的東西都已在 main，刪掉也不會遺失，但先保留不刪。\n\n`;
const counts = rows.reduce((m, r) => (m[r.kind] = (m[r.kind] || 0) + 1, m), {});
br += Object.entries(counts).map(([k, n]) => `- ${k}：${n} 條`).join('\n') + '\n\n';
br += `| 分支 | 分類 | 最後更新 | 最後提交者 | main 沒有的檔案 | PR | 做了什麼 | 備註 |\n|---|---|---|---|---:|---|---|---|\n`;
for (const r of rows) br += `| \`${r.name}\` | ${r.kind} | ${r.date} | ${r.author} | ${r.differ} | ${r.prText} | ${r.what} | ${esc(r.note)} |\n`;

// ---- folders.md（素材資料夾 → 哪張 PR 放進來、誰做的）
const folderIndex = new Map();
for (const p of pulls) {
  if (!p.merged_at) continue;
  for (const [k, n] of prFolders.get(p.number).folders) {
    if (!assetFolder(k) && !k.startsWith('tools/') && !k.startsWith('apps/game/Assets')) continue;
    if (!folderIndex.has(k)) folderIndex.set(k, []);
    folderIndex.get(k).push({ p, n });
  }
}
const mainFolders = new Set(tryGit('git ls-tree -d --name-only origin/main art/exports/ art/source/ art/incoming/dondon/ art/references/ tools/').split('\n').filter(Boolean));
let fo = `# 資料夾總帳（素材與工具）\n\n> 由 \`tools/registry/build-registry.mjs\` 產生，**不要手改**。只列 main 上的素材與工具資料夾；「第一次放進來」是最早合併、動到這個資料夾的 PR。\n\n`;
fo += `| 資料夾 | 誰做的 | 第一次放進來 | 之後改過的 PR |\n|---|---|---|---|\n`;
for (const k of [...mainFolders].sort()) {
  const list = (folderIndex.get(k) || []).sort((a, b) => a.p.merged_at.localeCompare(b.p.merged_at));
  const first = list[0];
  const firstText = first ? `[#${first.p.number}](https://github.com/${REPO}/pull/${first.p.number}) ${esc(first.p.title).slice(0, 40)}` : '早於 PR 流程（直接提交）';
  const authors = [...new Set(list.map((x) => who(x.p.user.login)))].join('、') || '—';
  const later = list.slice(1).map((x) => `#${x.p.number}`).join('、') || '—';
  fo += `| \`${k}\` | ${authors} | ${firstText} | ${later} |\n`;
}

mkdirSync(OUT, { recursive: true });
writeFileSync(`${OUT}/prs.md`, prs);
writeFileSync(`${OUT}/branches.md`, br);
writeFileSync(`${OUT}/folders.md`, fo);
console.log(`PR ${pulls.length}、分支 ${rows.length}、資料夾 ${mainFolders.size}`);
console.log(JSON.stringify(counts));
