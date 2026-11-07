# 標註規則 v1：每個分支、每張 PR、每個資料夾都要看得出「誰、為了哪份工作包、做了什麼」

> 2026-11-07，Claude Code 依 z1nnz 指示撰寫：「一定要標記標註好每個檔案，每個分支，每個 PR 到底都做了些什麼。」
> 起因：盤點時發現 63 條分支裡有 17 條要人工追查才知道是什麼；36 個素材資料夾只有 2 個有 README；有分支在 PR 合併後又推新提交，那些修改沒進 main 也沒人知道。
> 全部人（A、B、C、核心組、Codex）都照這份做。舊的分支、PR 不用改名，總帳已經替它們補上說明。

---

## 1. 總帳：先看這裡

| 檔案 | 內容 |
|---|---|
| [`docs/registry/branches.md`](../registry/branches.md) | 每條分支：分類、誰、最後更新、還有幾個檔案不在 main、對應 PR、做了什麼、備註 |
| [`docs/registry/prs.md`](../registry/prs.md) | 每張 PR：誰、狀態、分支、做了什麼、動到哪些資料夾 |
| [`docs/registry/folders.md`](../registry/folders.md) | main 上每個素材與工具資料夾：誰做的、哪張 PR 放進來、之後誰改過 |

- 總帳由 `node tools/registry/build-registry.mjs` 產生，**不要手改**。
- 只有判斷（例如「這條是舊版，不再合」）寫在 `tools/registry/notes.json`，產生器會放進「備註」欄。
- **核心組每次合併 PR 後重跑一次**，和合併一起提交。

## 2. 分支怎麼取名

```
<類型>/<誰>-<工作包日期>-<主題>
```

| 欄位 | 寫什麼 | 例子 |
|---|---|---|
| 類型 | `art`（模型、貼圖、動畫）、`game`（玩法、Unity 程式）、`docs`（文件、工作包）、`fix`（修正已合併的東西）、`tool`（工具） | `art` |
| 誰 | `a`、`b`、`c`、`core`、`codex` | `b` |
| 工作包日期 | 工作包的日期，月日四碼 | `1107` |
| 主題 | 英文小寫，用 `-` 連接，寫這批的 ID 或主題 | `sg-mountain-stairs` |

例子：`art/b-1107-sg-mountain-stairs`、`art/c-1107-lv-village-props`、`docs/core-1107-labeling-rules`。

**一批一條分支**：工作包說「開一張 PR」的那一段就是一批。下一批開新分支，不要在同一條分支上一直接著做。

## 3. PR 怎麼寫

**標題**：

```
【A／B／C／核心組／Codex】<工作包日期> <ID 範圍>：<一句話>
```

例子：`【B】11/07 SG01–SG04：山城大石階`、`【核心組】11/07 標註規則與總帳`。

**內容**：照 PR 範本，開頭的「這張 PR 是什麼」四行一定要填：

| 欄位 | 寫什麼 |
|---|---|
| 誰 | A／B／C／核心組／Codex |
| 工作包 | 工作包檔案路徑，例如 `docs/execution/2026-11-07/B-104h-tea-wheel-and-mountain-way.md` |
| ID | 這張 PR 交了哪些 ID，例如 `SG01–SG04` |
| 新增／修改的資料夾 | 列出來，例如 `art/exports/mountain-stairs-b/`、`art/source/mountain-stairs-b/` |

**GitHub 標籤**：核心組會加上「誰」和「類型」兩種標籤（例如 `B`、`模型`），在 PR 列表一眼就能篩出某個人或某一類。

## 4. PR 合併以後

- **不要再往同一條分支推新提交。** 合併後還要改，就開 `fix/<誰>-<日期>-<主題>` 新分支、開新 PR。
  - 原因：11/07 盤點時，`feature/world-props-a` 在 #68 合併後又推了一個修正（LOD1 上限、只交 FBX），沒有 PR，修正也就沒進 main。
- 合併後的分支**先保留不刪**；總帳會標「內容都在 main，可封存」。

## 5. 每個素材資料夾都要有 README

`art/exports/<組>/README.md`（新交的組一定要有；舊的組由核心組補）。最上面固定這一段：

```markdown
| 項目 | 內容 |
|---|---|
| 誰做的 | B（joshsu54） |
| 工作包 | docs/execution/2026-11-07/B-104h-tea-wheel-and-mountain-way.md |
| ID | SG01–SG04 |
| 分支／PR | art/b-1107-sg-mountain-stairs ／ #75 |
| 版本 | v001（舊版留在各件的 v000/ 資料夾，不覆寫） |
| 狀態 | Exported ／ Imported ／ Visually Verified ／ In-game Verified（沒驗的寫「未驗」） |
| 素材來源 | 原創／改自哪個檔案（作者） |
```

下面再寫各件說明、尺寸、數字（三角面、物件數、材質數、貼圖解析度）、已知問題。

## 6. 提交訊息

開頭寫 ID，後面一句話說做了什麼：

```
SG02: 轉折平台加石燈座插槽
```

不是某件 ID 的提交（例如整理、文件），開頭寫 `docs:`、`fix:`、`chore:`。

## 7. 誰負責什麼

| 誰 | 要做的 |
|---|---|
| A、B、C、Codex | 分支照第 2 節取名；PR 照第 3 節寫；新的素材資料夾附第 5 節 README；合併後不再推舊分支 |
| 核心組 | 加 PR 標籤；合併後重跑總帳；更新 `notes.json`；補舊資料夾的 README |
