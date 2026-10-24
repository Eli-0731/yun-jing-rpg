# 工程設計與開發邊界

## 資料流

驗證頁／Unity → HTTPS（本機 loopback HTTP）→ NestJS → PostgreSQL。
Unity 移動 → FishNet/Tugboat 專用程序 → 權威位置與校正。
獨立樹伴來源服務 → 可信內部輸送介面 → 接收物品＋唯一收據。

後兩條在本輪有原始碼／接收方實作，不能視為已完成整合。

## SQL 與一致性

`database.ts` 同一套 SQL 可用 PGlite 或 pg。PGlite 是本機 PostgreSQL WASM，不是 JSON 檔假存檔。PGlite 因單連線採 transaction queue；正式 pg 使用 Pool client 與 BEGIN／COMMIT／ROLLBACK。

資產操作目前固定鎖 world → player → read birth → check request receipt → mutate → write state＋ledger＋receipt → commit。全世界一個 world lock 是早期正確性基線，**不具正式多人擴展能力**；分區後需拆鎖但維持一致鎖順序。所有金錢目前整數。

唯一限制：players.subject、births.player_id、receipts(actor,request)、ledger(actor,request)、transfers.id、companion_links 的雙方身分。失敗交易沒有部分扣料。重送保存原回應；request ID 不能換用途。

`births.payload` 保存先天；players.state 保存後天。正式 API 不接受測試 roll。測試注入建構參數只存在自動測試內。

## API 速查

| API | 用途 |
|---|---|
| GET /v1/health、/content | 服務、版本、內容 |
| POST /v1/auth/local | loopback local 模式測試身分 |
| POST /v1/auth/challenge、/authorize、/exchange | S256 PKCE 與 Firebase 瀏覽器交換 |
| POST /v1/auth/refresh | 旋轉一次性更新憑證 |
| GET /v1/me | 角色、出生、共同世界、serverTime、version |
| POST /v1/actions | requestId＋action；actor 只能取自認證 |
| POST /v1/room/ticket | 60 秒單次青溪入場票證 |
| POST /v1/internal/room/redeem | 專用程序兌換票證 |
| POST /v1/internal/transfers | 可信連動服務輸送／取消 |

動作：birth、investigate、gather、plant、harvest、craft、claim-craft、enroll、practice、bathe、awaken、contribute、resolve、claim-project、breakthrough；v0.2 新增 talk、claim-quest、buy，v0.3 新增 build-cistern、configure-irrigation、tend-plot，v0.4 新增 appraise、practice-basic。具體欄位見 game.ts／contracts/types.ts。現行內容版本 `0.4.0`；既有出生紀錄保留當時版本。

## 入世與公開資料 v0.4.0

`playerFor` 使用 subject 唯一索引，只有 INSERT RETURNING 成功的新角色才抽先天；Player、Birth、煉氣訣資格、起始資產帳本同交易保存。並行登入、故障重試不重抽。`journey.createdAt`、`selectionAt` 固定為服務端創角時間與加十個現實日，沒有客戶端寫入介面；種植 speed 不參與此計算。

新角色 `journey.assessedAt=null` 時，公開 Snapshot 中 `birth=null`、`player.roots=null`、`player.apertures=null`。這裡 null 代表未揭露；真正凡骨會在測資後顯示空 roots、零 apertures。`birthAssigned=true` 表示已分配，客戶端不應以 birth=null 判定尚未出生。服務端內部 Player 保留真實資質，供修行計算；`PublicPlayer` 型別明確區分可空欄位。

個人資質支線在揭露前不顯示，對支線領取的探測統一拒絕；公開指引不說出精確出生級別。操作收據保存公開快照；未測資角色回放收據時再次清除出生私有欄位。實際修煉是否成功、效率可讓玩家推測資質，並不保證阻止這類玩法推測。

- `appraise {}`：服務端時間滿 selectionAt，設定一次 assessedAt；沒有重抽或獎勵。不要求某個固定鐘點登入。
- `practice-basic {discipline:'body'|'qi'}`：有煉氣訣資格即可練習，沿用 15 秒修行冷卻和真實先天效率。無根不可引氣，可練體。這是操作原型，不是完整離線閉關。
- `enroll`：新角色先測資；第一次入宗將 housing 改 cave、記錄一次 received:cave。已有水池、作物或資產不重置。新流程尚無轉宗或弟子等級，不暗中預設未核定的入門分級表。
- `plant/build-cistern/configure-irrigation`：新角色要有 cave 使用權。床、箱子、洞府空間實際互動尚未交付。

既有沒有 journey 的角色視為舊測試存檔，仍可沿用既有出生、田地與師承。這是有版本辨識的相容規則，不回填虛構創角日期。測試的舊資料 fixture 直接建立舊格式資料列，只存在 tests；公開 API 不提供跳過十日或刪除 journey 的能力。

## 青溪章節與補給 v0.2.0

`packages/content/qingxi.json` 定義章節、目標依賴、導師話題、調查文本與 NPC 報價。`journal.ts` 從現有 Player／Birth 推導手札，不增加另一份可能失去同步的任務狀態。領取結果保存在唯一里程碑 `quest:<id>`，並沿用玩家鎖、收據及帳本。

- `talk`: `{ mentor, topic }`；只接受定義中的導師及話題，記錄 `talked:<id>`、`topic:<mentor>:<topic>`。
- `claim-quest`: `{ quest }`；由服務端檢查適用資質、目標條件與已領取的前置目標，發出一次綁定獎勵。客戶端傳來的完成旗標／獎勵數值無效。
- `buy`: `{ offer, packs }`；packs 是 1–10 的整數。單價與每份產量只能取自內容表，無出售／兌回。任一部分付款使用綁定靈石，整批取得材料綁定，後續煉製延續綁定。
- `GET content` 增加 `chapter`；Snapshot 增加 `journal`，既有欄位保持相容。舊請求的收據仍原樣返回，驗證頁收到無 journal 的舊收據會再讀取 me。

主要目標只有5個；凡骨開靈及生態共存皆非主線強制。已有成果可以補領，但仍須依順序領取前置成果。任務／對話沒有每日刷新或連續登入要求。出生差異與修行效率沒有調整。

一次性 requestId 應在傳輸失敗後沿用；收到 5xx 不表示未入帳。採收時間與生產結果不接受客戶端裁定。頁面倒數可以有時差，最終以 API 為準。

## 認證與機密

access token 有效15分鐘、refresh30天，資料庫只保存 SHA256。登入交接撤銷舊憑證，refresh 鎖 player 後二次查驗。票證雜湊保存、到期／已消耗拒絕。內部 service key 只放伺服器環境；本機啟動器在 ignored `.data/service.key` 建立，不寫入 Unity prefab。

production 啟動需獨立 DATABASE_URL、FIREBASE_PROJECT_ID、至少32字元 internal key，禁止加速及 local login。設定齊全**不表示可以直接公開部署**：限速、風險判斷、空間驗證、完整交接／撤銷及營運安全仍待完成。網路伺服器目前只綁 loopback，非手機 LAN 測試配置。

Firebase 瀏覽器頁需要公開設定 JSON `FIREBASE_WEB_CONFIG`；後端需正確 ADC／服務身分以驗證撤銷狀態。不得複製樹伴的專案或私鑰。遊戲登入尚未接正式 Unity 瀏覽器發起流程。

## 輸送

接收方在同交易中檢查身分綁定、出生、連續28天已收數量，寫 transfers 與綁定物品／ledger。相同 id 重送回原狀態，不增量；取消未到達輸送留下 tombstone，遲到接收維持 cancelled。已入帳的取消拒絕，來源不能據此退款。

測試建立 companion_links 僅是 fixture；正式沒有可任意建立綁定的公開端點。來源 outbox、重試、對帳、雙方登入、解除／改綁需要下一階段實作後才能開正式連動。

## 已驗證與待測

Node test 涵蓋抽選邊界、並行唯一性、重送衝突、離線成熟、領取一次、回滾、共同工程、輸送額度與取消、重啟、凡骨開靈、登入交接、PKCE、HTTP 權限與票證、啟蒙流程。

未用真實 Firebase 驗證測試替代 PKCE fixture，也未用 PGlite 測試宣稱 pgPool 實際負載已通過。Unity／FishNet 需 Editor codegen 及雙端實測；純 C# 語法正確不足以證明同步正確。

## 開發操作

`tools/start-local.ps1` 前景啟動 API，Ctrl+C 正常關閉。`tools/start-room.ps1` 隱藏開啟專用程序並輸出 PID，可用該 PID 停止。禁止按程式名批次關閉其他 Unity 或 Node。

`.env.example` 是欄位說明；目前不自動載入 `.env`。設定使用 PowerShell `$env:...` 或部署環境。`infra/compose.yaml` 僅本機測試密碼，正式環境必須改用憑證管理。

資料庫備份／遷移／恢復、監控、發版與回滾流程尚未建立，因此不得發布正式資產服務。GitHub CI 先跑 API 測試，Unity CI 等授權與建置機就緒後加入。
