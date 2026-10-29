# 青溪 Unity 本機試走｜2026-10-27

製作：z1nnz 指導／Codex 實作。使用既有世界生成器與各自登記來源的場景模型，不重做協作者資產。此版是橫向本機探索原型，不是完成版美術、多人遊戲或正式修行進度。

## 開啟方式

在本分支根目錄執行 `./tools/unity.ps1 -Target WalkthroughWindows`，使用固定 Unity `6000.0.82f1`。生成與打包分兩個 Editor 程序，確保 Input System 設定重新載入。

完成後開啟 `artifacts/windows-walkthrough/YunJingWalkthrough.exe`，保留旁邊的 Data 目錄與 DLL。產物不提交 Git；其他電腦須自行建置或取得完整產物資料夾。

- WASD 移動，Shift 跑步，Space 跳躍，R 回入口。
- 按住滑鼠右鍵環繞，滾輪拉近／拉遠。
- 左下方有移動／跳躍試作按鈕；觸控右半部轉鏡頭尚未真機驗證。
- 角色目前是臨時膠囊輪廓，不是女主角成品。

## 實作邊界

`QingxiWalkthroughBuilder` 另存 `QingxiWorldWalkthrough.unity`，移除帳號與網路服務，保留原有網路開發場景。控制器不操作 API、道具或帳本，不能透過這個原型取得正式獎勵。世界包含聽風台、橋、房屋與道路；部分地面和建築仍是舊灰盒，河水、植被與近景尚未達到 AI 參考圖。

## 實測

Windows 非 Development 版建置成功。執行 `YunJingWalkthrough.exe --walkthrough-smoke -batchmode`，退出碼 0：

```text
QINGXI_WALKTHROUGH_SMOKE PASS: walk=4.000m camera=3.436m jump=1.094m landed=True; return=0.000m
```

這是成品程序內實際 CharacterController／鏡頭逐幀測試，檢查一秒移動、跟隨、跳躍落地及回入口。結果另存於 Application.persistentDataPath 的 walkthrough-smoke.txt；未帶參數不會自動測試或退出。

實際視窗已顯示世界，但人工鍵鼠試走被 Windows 網路權限提示覆蓋，因此不把 UI 操作、走完整條路或踏上聽風台算作通過。移除 Development profiler 後的程序未觀察到 TCP／UDP 端點，提示來源尚未確認；沒有操作防火牆設定或允許連線。手機、碰撞全路線、手感與 FPS 均尚未驗證。

## 接續開發

1. 將入口兩棟舊灰盒房替換為已交付的客舍模型，加入明確門前路與沿溪方向，避免同一區混用兩套品質。
2. 接入第一處靈草：靠近提示、採集動作、服務端判定與背包結果；不依賴本機獎勵。
3. 接入山兔動畫、追蹤、一次合法攻擊與死亡收據，形成可選的採獵小循環。
4. 將協作者的新演武、採集與告示交付接入同一區域；女主角仍按局部相似度逐步精修。
