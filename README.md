# 承天

> 天裂了，一直有人在獨自承天。你從青溪的一個新人開始修仙，一路揭開這片土地的秘密，最後和所有人一起承天。

手機優先、需連線的多人修仙生活 RPG。預計 Steam、Android、iOS 同時上線；目前仍在 **M0／M1 原型階段**。

| 名稱 | 是什麼 |
|---|---|
| 承天 | 遊戲名稱 |
| 不周 | 世界：一片有缺口的大陸 |
| 鼇極 | 新手地區，青溪村在這裡 |
| 雲境 | 天缺正下方的區域；也是專案內部代號 `YunJing`（程式、資料夾、檔名照舊） |

世界觀、故事、宗門與玩法的定案整理見 [《承天》總覽](docs/承天-總覽.md)。

## 目前能跑的內容

- NestJS API、PGlite 本機存檔與玩法驗證頁。
- 創角時唯一分配先天；十個現實日後才能正式測資。
- 採集、種植、煉製、共同工程、兩宗基礎師承與資產帳本原型。
- 山兔掉落與出售的服務端原型；API／持久化測試。
- Unity 青溪新手村與入口片區的 Windows 本機試走版。

尚未完成：手機效能、多人連線、正式角色、伺服器資產接線與人工全路線試玩。不要把這些寫成已完成。詳見 [目前狀態](docs/status.md) 與 [開發進度表](docs/development-roadmap.md)。

## 本機啟動

```powershell
cd D:\chengtian\chengtian
powershell -ExecutionPolicy Bypass -File .\tools\start-local.ps1
```

開啟 <http://127.0.0.1:4310>。`traveler-a`、`traveler-b` 是只允許 loopback 的測試身分。不要把本機服務公開到網際網路。

```powershell
npm ci
npm test
npm run smoke
```

Unity 專案位於 `apps/game`，固定使用 `6000.0.85f1`。建置前必須先取得有效 Unity 授權。

## 主要目錄

| 路徑 | 內容 |
|---|---|
| `apps/game` | Unity 客戶端、專用區域程序與 Editor 工具 |
| `apps/inspector` | 本機玩法驗證頁 |
| `services/api` | 帳號、角色、資產與生產 API |
| `packages/content` | 道具、配方與內容定義 |
| `packages/contracts` | 共用資料契約 |
| `art` | 三視圖、Blender 母檔、匯出與驗證 |
| `docs` | 設計、規範、工作包、狀態與總帳 |
| `tools` | 建置、試玩、總帳產生器等工具 |
| `tests` | API、並行、持久化與故障測試 |

## 參與開發

開工前依序讀：

1. [協作流程](CONTRIBUTING.md)：分支、PR、素材怎麼交。
2. [製作規範總綱](docs/standards/README.md)：每類工作以哪份文件為準、硬規則。
3. [標註規則](docs/standards/labeling-v1.md)：分支、PR、資料夾怎麼命名。
4. [開發規則](AGENTS.md)、[設計基準](docs/approved-plan.md)、[工作分工](docs/work-ownership.md)。

分支、PR、資料夾的總帳在 [`docs/registry/`](docs/registry/)。

## 版權

本專案為製作中作品，程式、美術與文字版權屬原作者所有，未經同意不得轉載、再散布或商用。協作者作品保留原作者署名。
