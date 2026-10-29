# Codex 工作包 v2（索引）

2026-10-29，z1nnz 交辦，Claude Code 撰寫。本資料夾**取代** `../codex-work-package-v1.md`、`../ui-concept-codex-brief.md`，以及室內工作樹的 `p1-codex-interior-kit-brief.md`。

| 檔案 | 內容 | 工作位置 | 需要生圖 |
|---|---|---|---|
| [01-world-update-2026-10-29.md](01-world-update-2026-10-29.md) | **遊戲更新總包（最新，開工前必讀）**：《承天》、世界不周、多文化地名、天樞、不交代、領地與大世界、先完成一個區域、規範入口。和 00 衝突時以這份為準 | — | — |
| [00-operating-rules.md](00-operating-rules.md) | **共同規範**：角色、自主權限、環境、分析優先、分階段關卡、視覺檢查循環、效能、檔案安全、交付與報告 | — | — |
| [C1-ui-concepts.md](C1-ui-concepts.md) | 介面概念圖三套＋像素版面線框（16 張圖） | `yun-jing-ui-concepts-v1\` | 多 |
| [C2-interior-kit.md](C2-interior-kit.md) | 借住處室內模組 IK01–IK12＋組裝房間 | `yun-jing-rpg-interior-kit-v1` | 中 |
| [C3-web-shell.md](C3-web-shell.md) | 網頁外殼：載入、進度、入境、橫屏、安裝、錯誤、ServiceWorker | `yun-jing-rpg-web-shell-v1` | 少 |
| [C4-distant-peaks.md](C4-distant-peaks.md) | 遠景石峰、山稜、崖松、雲帶、瀑布＋擺放表 | `yun-jing-rpg-distant-peaks-v1` | 中 |
| [C5-alchemy-table-pbr.md](C5-alchemy-table-pbr.md) | 丹房工作桌 v002：形體精修＋PBR（建模規格第一個試做） | `yun-jing-rpg-alchemy-table-pbr-v1` | 少 |
| [C6-ui-final-assets.md](C6-ui-final-assets.md) | 圖示、九宮格、四區外觀、標誌（等 Claude Code 檢查 C1） | `yun-jing-ui-concepts-v1\final\` | 中 |
| [C7-village-slot-props.md](C7-village-slot-props.md) | 青溪村格位道具：村口石燈、水井、井與洗衣石、茶棚（照區塊規劃的格位尺寸） | `yun-jing-rpg-village-props-c7`（Codex 自建工作樹） | 少 |
| [C8-plaza-elder-tree.md](C8-plaza-elder-tree.md) | 村中古樹與廣場地標套件（8 件，約 24 小時） | `yun-jing-rpg-plaza-tree-c8`（自建） | 中 |
| [C9-a3-watermill-kit.md](C9-a3-watermill-kit.md) | A3 西溪水磨坊套件：水車、引水渠、石橋、埠頭、低面數溪石與蘆葦（12 件，約 28 小時） | `yun-jing-rpg-a3-watermill-c9`（自建） | 中 |
| [C10-a2-road-kit.md](C10-a2-road-kit.md) | A2 村外官道套件：茶亭、土地祠（機緣點）、板車、路牌、圍籬（12 件，約 24 小時） | `yun-jing-rpg-a2-roadkit-c10`（自建） | 中 |

| [C11-collaborator-pack-audit.md](C11-collaborator-pack-audit.md) | 審查協作者工作包與開著的 PR，判斷是否符合現在的世界（只讀、只寫報告） | 主場景工作樹 `docs/execution/reviews/` | 無 |
| [C12-collaborator-brief-standard.md](C12-collaborator-brief-standard.md) | 依開發階段與先後順序安排協作者工作包（範本＋規則）；檢查 Claude Code 寫的 10/31 三份工作包，並提出 11/2 之後的方向 | 主場景工作樹 `docs/execution/2026-10-30/` | 無 |

**2026-10-29 晚上的新順序**：C11 → C12 → C7 → C8 → C9 → C10；C1–C5 的修正等 Claude Code 審完這一輪交件另外給。

**第一輪檢查與下一輪順序**：[review-2026-10-29.md](review-2026-10-29.md)（C5 → C3 → C2 → C4 → C6 → C7 → C8 → C9 → C10，一次做完一項）。

所有工作位置都在 `D:\yun-jing-rpg-workspace\` 底下。Codex 不 commit；Claude Code 檢查後以 z1nnz 名義提交。
