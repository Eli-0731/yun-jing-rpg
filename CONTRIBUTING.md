# 共同開發

儲存庫：<https://github.com/z1nnz/chengtian>（2026-11-07 由 yun-jing-rpg 改名，舊網址會自動轉址）

## 誰負責什麼

| 組 | 誰 | 範圍 |
|---|---|---|
| 核心組 | z1nnz（擁有者，最後決定）與 AI 助手 | 整合、主場景、角色、HUD、伺服器接線、審查與合併 |
| A | Johnnnny0823 | 依工作包 |
| B | joshsu54 | 依工作包 |
| C | Eli-0731 | 依工作包（基礎建模練習） |

每個人的工作寫在 `docs/execution/<日期>/` 的工作包裡。只做自己工作包內的東西；角色（女主角等）只由核心組製作。詳見 [工作分工](docs/work-ownership.md)。

## 規則

- `main` 只透過 Pull Request 更新，不直接推送或強制推送。
- 一個 PR 只處理一批可驗收工作（工作包裡「開一張 PR」的那一段）。
- 合併前必須通過 `API and persistence tests` 與 `LFS asset integrity`，並解決所有審查討論。
- 不同人不要同時修改同一個 `.blend`、Unity 場景或其他二進位檔。
- PR 合併後**不要再推到同一條分支**；要修正就開新的 `fix/...` 分支。
- 有 Write 權限的人：joshsu54、Johnnnny0823。其他協作者用 fork 開 PR，並勾選「Allow edits by maintainers」，讓核心組可以幫忙更新分支。

## 第一次設定

```powershell
git lfs install
git clone https://github.com/z1nnz/chengtian.git
cd chengtian
git config pull.ff only
git lfs pull
npm ci
npm test
```

使用自己的 GitHub 登入，不分享 Token。開工前讀 [AGENTS.md](AGENTS.md)、[目前狀態](docs/status.md)、[製作規範總綱](docs/standards/README.md) 和自己的工作包。

## 每項工作

### 1. 開分支

分支名稱照 [標註規則](docs/standards/labeling-v1.md)：

```
<類型>/<誰>-<工作包日期>-<主題>
```

- 類型：`art`（模型、貼圖、動畫）、`game`（玩法、Unity 程式）、`docs`（文件）、`fix`（修正已合併的東西）、`tool`（工具）
- 誰：`a`、`b`、`c`、`core`、`codex`
- 例子：`art/b-1107-sg-mountain-stairs`

```powershell
git switch main
git pull --ff-only origin main
git switch -c art/b-1107-sg-mountain-stairs
```

### 2. 提交

只加入本次檔案，提交訊息以素材 ID 開頭：

```powershell
git add path/to/file
git diff --cached --stat
git lfs status
git commit -m "SG01–SG04：山城大石階第一版"
git push -u origin art/b-1107-sg-mountain-stairs
```

### 3. 開 PR

- 標題：`【A／B／C／核心組／Codex】<工作包日期> <ID 範圍>：<一句話>`，例如 `【B】11/07 SG01–SG04：山城大石階`。
- 內容照 PR 範本填寫，開頭「這張 PR 是什麼」四行（誰、工作包、ID、資料夾）一定要填。
- 模型附預覽、來源、三視圖、尺寸、面數、LOD、碰撞及動畫清單。

檢查失敗就修正同一分支，不刪測試、不關規則、不強制推送。main 更新後按 PR 頁面的「Update branch」，或執行 `git fetch origin`、`git merge origin/main`、重新測試再推送。

### 4. 合併以後

由核心組合併，合併後執行 `node tools/registry/build-registry.mjs` 更新 [`docs/registry/`](docs/registry/) 總帳並一起提交。

## 素材

- `.blend`、`.fbx`、`.glb`、圖片與音訊使用 Git LFS。
- 新模型必須先保存經檢視的 AI 三視圖，再開始建模；品質優先，效能用 LOD 與分段載入處理。
- 每個新的 `art/exports/<組>/README.md` 開頭要有標註表（誰做的、工作包、ID、分支／PR、版本、狀態、素材來源）。
- 外部素材必須附作者、來源、授權與必要標示。
- Unreal 快取、Unity 快取、建置產物、私鑰、正式資料及本機資料庫不得提交。
- `dondon2.0` 交付格式見 [素材清單](docs/素材交接清單-dondon.md)。

## 驗證

程式修改至少執行 `npm test`。Unity 修改必須附 Editor 編譯結果或明示尚未驗證；GitHub 的 CI 不包含 Unity、手機或多人實測。

審查標準見 [PR 審查清單](docs/standards/pr-review.md)。
