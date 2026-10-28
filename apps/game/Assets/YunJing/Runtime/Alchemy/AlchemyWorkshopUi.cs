using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.UI;

namespace YunJing.Alchemy
{
    public sealed partial class AlchemyWorkshop
    {
        Canvas canvas; Text hudTitle, hudLine, hudGuide, toast, prompt, gaugeText, gaugeState; RectTransform panel, panelBody, gauge, gaugeFill, bandMark, overlay, modal, modalBody, skipBar;
        Button interactButton, retryButton, motionButton, menuButton; Image gaugeFillImage; GameObject touchUi;
        readonly Dictionary<string, RectTransform> zones = new Dictionary<string, RectTransform>();
        readonly Dictionary<string, HerbChip> chips = new Dictionary<string, HerbChip>(); RectTransform grindPad; Text grindText;
        public string ScrollTab = "herbs";
        public readonly Dictionary<string, Button> Buttons = new Dictionary<string, Button>();

        void BuildUi()
        {
            canvas = AlchemyUi.Canvas("AlchemyCanvas"); var root = canvas.transform;
            var hud = AlchemyUi.Slips("Hud", root, new Vector2(0, 1), new Vector2(0, 1), new Vector2(24, -196), new Vector2(720, -24));
            var hudCol = AlchemyUi.Rect("Col", hud, Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero); AlchemyUi.Column(hudCol, 4, 16);
            hudTitle = AlchemyUi.Line(hudCol, "青溪丹房", 34, AlchemyUi.Ink, 40); hudTitle.fontStyle = FontStyle.Bold;
            hudLine = AlchemyUi.Line(hudCol, "", 22); hudGuide = AlchemyUi.Line(hudCol, "", 24, AlchemyUi.Cinnabar);
            toast = AlchemyUi.Label("Toast", AlchemyUi.Panel("ToastBg", root, new Vector2(.5f, 1), new Vector2(.5f, 1), new Vector2(-300, -290), new Vector2(300, -212), AlchemyUi.Shade).transform, "", 25, TextAnchor.MiddleCenter, Color.white); // below the HUD, left of the station panel
            ((RectTransform)toast.transform).offsetMin = new Vector2(12, 4); ((RectTransform)toast.transform).offsetMax = new Vector2(-12, -4);
            skipBar = AlchemyUi.Rect("RevealSkip", root, new Vector2(.5f, 0), new Vector2(.5f, 0), new Vector2(-230, 40), new Vector2(230, 104)); AlchemyUi.Column(skipBar, 0, 0);
            skipBar.gameObject.SetActive(false);
            prompt = AlchemyUi.Label("Prompt", AlchemyUi.Panel("PromptBg", root, new Vector2(.5f, 0), new Vector2(.5f, 0), new Vector2(-330, 40), new Vector2(330, 104), AlchemyUi.Shade).transform, "", 28, TextAnchor.MiddleCenter, Color.white);
            var top = AlchemyUi.Rect("TopRight", root, new Vector2(1, 1), new Vector2(1, 1), new Vector2(-560, -96), new Vector2(-24, -24));
            var topRow = top.gameObject.AddComponent<HorizontalLayoutGroup>(); topRow.spacing = 10; topRow.childForceExpandWidth = true; topRow.childControlWidth = true; topRow.childControlHeight = true;
            motionButton = AlchemyUi.Button("Btn_Motion", top, "", () => SetReducedMotion(!Director.ReducedMotion), AlchemyUi.BambooDark, 22);
            menuButton = AlchemyUi.Button("Btn_Menu", top, "返回／選單", Back, AlchemyUi.BambooDark, 22);
            retryButton = AlchemyUi.Button("Btn_Retry", AlchemyUi.Rect("RetryHolder", root, new Vector2(.5f, 1), new Vector2(.5f, 1), new Vector2(-150, -190), new Vector2(150, -124)), "連線中斷：重試", () => Api.Retry(), AlchemyUi.Cinnabar);
            panel = AlchemyUi.Slips("Panel", root, new Vector2(1, 0), new Vector2(1, 1), new Vector2(-660, 130), new Vector2(-24, -120));
            panelBody = AlchemyUi.Rect("Body", panel, Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero); AlchemyUi.Column(panelBody, 8, 22);
            gauge = AlchemyUi.Slips("FurnaceGauge", root, new Vector2(0, 0), new Vector2(0, 0), new Vector2(24, 24), new Vector2(760, 250));
            var bar = AlchemyUi.Panel("Bar", gauge, new Vector2(0, 1), new Vector2(1, 1), new Vector2(24, -86), new Vector2(-24, -50), new Color(.25f, .2f, .14f, .9f));
            gaugeFillImage = AlchemyUi.Panel("Fill", bar.transform, Vector2.zero, new Vector2(0, 1), Vector2.zero, Vector2.zero, AlchemyUi.Cinnabar); gaugeFill = (RectTransform)gaugeFillImage.transform;
            bandMark = (RectTransform)AlchemyUi.Panel("Band", bar.transform, Vector2.zero, new Vector2(0, 1), new Vector2(0, -6), new Vector2(0, 6), new Color(.4f, .85f, .7f, .55f)).transform;
            gaugeText = AlchemyUi.Label("Temp", gauge, "", 24, TextAnchor.UpperLeft, AlchemyUi.Ink); ((RectTransform)gaugeText.transform).offsetMin = new Vector2(24, 0); ((RectTransform)gaugeText.transform).offsetMax = new Vector2(-24, -12);
            gaugeState = AlchemyUi.Label("State", gauge, "", 23, TextAnchor.LowerLeft, AlchemyUi.Ink); ((RectTransform)gaugeState.transform).offsetMin = new Vector2(24, 16); ((RectTransform)gaugeState.transform).offsetMax = new Vector2(-24, -96);
            overlay = AlchemyUi.Rect("TableOverlay", root, Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero);
            foreach (var z in new[] { ("mortar", "石臼・研磨"), ("basket", "晾藥籃・陰乾"), ("main", "分料盤・君"), ("aux", "分料盤・臣") })
            {
                var marker = AlchemyUi.Panel("Zone_" + z.Item1, overlay, new Vector2(0, 0), new Vector2(0, 0), new Vector2(-95, -34), new Vector2(95, 34), new Color(.95f, .9f, .75f, .78f));
                AlchemyUi.Label("T", marker.transform, z.Item2, 22, TextAnchor.MiddleCenter, AlchemyUi.Ink); zones[z.Item1] = (RectTransform)marker.transform;
            }
            for (int i = 0; i < Herbs.Length; i++)
            {
                var chipBg = AlchemyUi.Panel("Chip_" + Herbs[i], overlay, new Vector2(.5f, 0), new Vector2(.5f, 0), new Vector2(-420 + i * 290, 130), new Vector2(-150 + i * 290, 214), AlchemyUi.Jade);
                AlchemyUi.Label("T", chipBg.transform, "", 22, TextAnchor.MiddleCenter, Color.white);
                var chip = chipBg.gameObject.AddComponent<HerbChip>(); chip.Herb = Herbs[i]; chip.Dropped = OnChipDropped; chips[Herbs[i]] = chip;
            }
            var pad = AlchemyUi.Panel("GrindPad", overlay, Vector2.zero, Vector2.zero, new Vector2(-150, -150), new Vector2(150, 150), new Color(1, 1, 1, .12f));
            pad.gameObject.AddComponent<GrindPad>().Stroke = GrindStroke; grindPad = (RectTransform)pad.transform;
            grindText = AlchemyUi.Label("T", pad.transform, "", 24, TextAnchor.LowerCenter, Color.white);
            modal = AlchemyUi.Slips("Modal", root, new Vector2(.5f, .5f), new Vector2(.5f, .5f), new Vector2(-470, -330), new Vector2(470, 330));
            modalBody = AlchemyUi.Rect("Body", modal, Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero); AlchemyUi.Column(modalBody, 8, 30);
            modal.gameObject.SetActive(false);
            interactButton = AlchemyUi.Button("Btn_Interact", AlchemyUi.Rect("InteractHolder", root, new Vector2(1, 0), new Vector2(1, 0), new Vector2(-260, 40), new Vector2(-40, 150)), "互動", TryInteract, AlchemyUi.Cinnabar, 30);
            touchUi = new GameObject("TouchStick", typeof(RectTransform)); touchUi.transform.SetParent(root, false);
            var stickPad = AlchemyUi.Panel("Pad", touchUi.transform, Vector2.zero, Vector2.zero, new Vector2(120, 120), new Vector2(340, 340), new Color(1, 1, 1, .12f));
            var knob = AlchemyUi.Panel("Knob", touchUi.transform, Vector2.zero, Vector2.zero, new Vector2(185, 185), new Vector2(275, 275), new Color(1, 1, 1, .35f));
            var stick = touchUi.AddComponent<TouchStick>(); stick.Pad = (RectTransform)stickPad.transform; stick.Knob = (RectTransform)knob.transform;
            BuildPanel();
        }

        void RefreshUi()
        {
            if (canvas == null) return;
            var v = View;
            hudLine.text = v == null ? "連線本機伺服器中…" :
                $"煉丹熟練 Lv{v.level}（{v.into}/{v.need}）・丹經第 {v.manualTier} 卷・青靈草 {Owned(Herbs[0])}・淨水蓮 {Owned(Herbs[1])}・松柴 {v.fuel}・靈石 {Owned("spirit-stone")}";
            hudGuide.text = Guidance;
            toast.text = Toast; toast.transform.parent.gameObject.SetActive(!string.IsNullOrEmpty(Toast));
            bool touch = Touchscreen.current != null;
            prompt.transform.parent.gameObject.SetActive(Near != null && Active == null && !RevealPlaying);
            if (Near != null) prompt.text = (touch ? "點「互動」：" : "按 E：") + Near.Label + "・" + Near.Verb;
            interactButton.transform.parent.gameObject.SetActive(Near != null && Active == null && !RevealPlaying);
            touchUi.SetActive(touch && Active == null);
            retryButton.transform.parent.gameObject.SetActive(Api != null && Api.HasPending && !Api.Busy);
            AlchemyUi.SetText(motionButton, Director.ReducedMotion ? "減少鏡頭運動：開" : "減少鏡頭運動：關");
            panel.gameObject.SetActive(Active != null && !RevealPlaying && !modal.gameObject.activeSelf);
            if (skipBar.gameObject.activeSelf != RevealPlaying) skipBar.gameObject.SetActive(RevealPlaying);
            foreach (var b in Buttons.Values) if (b != null) b.interactable = !Waiting;
            RefreshGauge(); RefreshTable();
        }

        void RefreshGauge()
        {
            bool show = Furnace != null && (Stage == Stage.Fire || Stage == Stage.Prep) && Active != null && Active.Id == "B01";
            gauge.gameObject.SetActive(show); if (!show) return;
            var f = Furnace; float T = (float)f.T; var v = View; var phases = v?.profile?.phases ?? new AlchemyPhase[0];
            gaugeFill.anchorMax = new Vector2(Mathf.Clamp01(T / 110f), 1);
            gaugeFillImage.color = T > 95 ? new Color(.35f, .1f, .08f) : Color.Lerp(new Color(.85f, .55f, .2f), AlchemyUi.Cinnabar, Mathf.InverseLerp(20, 90, T));
            var phase = phases.Length == 0 ? null : phases[Mathf.Min(f.Phase, phases.Length - 1)];
            bool reveal = phase != null && (KnownRecipe(v.profile.recipe) || v.manualTier >= 3);
            bandMark.gameObject.SetActive(reveal);
            if (reveal) { bandMark.anchorMin = new Vector2(phase.low / 110f, 0); bandMark.anchorMax = new Vector2(phase.high / 110f, 1); }
            string phaseText = phases.Length == 0 ? "" : f.CompleteTick != null ? $"丹香已起 {(f.Tick - f.CompleteTick.Value) / 10f:0.0} 息，擇時收丹！" :
                $"第 {f.Phase + 1}/{phases.Length} 段・{phase.label}　{f.Progress[Mathf.Min(f.Phase, phases.Length - 1)]:0.0}/{phase.seconds:0} 息";
            gaugeText.text = $"爐溫 {T:0}　{phaseText}";
            string look = phase == null ? "" : T > 95 ? "爐溫過高！藥材焦糊中" : f.CompleteTick != null ? "丹香四溢" : T < phase.low ? "火候偏弱" : T > phase.high ? "火候過旺" : "火候正好，藥氣流轉";
            gaugeState.text = $"{look}\n爐蓋{(lidOpen ? "開" : "合")}・燃柴 {f.Burning}・爐邊剩柴 {FuelLeft}・排煙檔 {(f.Vent == 0 ? "閉" : f.Vent < 1 ? "半開" : "全開")}・爐中水 {f.Water} 瓢";
        }

        bool KnownRecipe(string id) => View?.recipes != null && View.recipes.Any(r => r.id == id && r.known);

        void RefreshTable()
        {
            bool show = Active != null && Active.Id == "TABLE" && Stage == Stage.Prep && !Director.Blending;
            overlay.gameObject.SetActive(show); if (!show) return;
            var cam = Camera.main;
            Place("mortar", Find("B03_Mortar"), .02f, cam, new Vector2(0, -70)); Place("basket", Find("B08_Basket"), .1f, cam, Vector2.zero);
            Place("main", Find("B04_Trays"), .55f, cam, new Vector2(-110, 50)); Place("aux", Find("B04_Trays"), .55f, cam, new Vector2(110, 50));
            Separate();
            foreach (var kv in chips)
            {
                bool charged = Furnace != null && Furnace.IsCharged(kv.Key); kv.Value.gameObject.SetActive(!charged);
                var q = Session?.herbs?.FirstOrDefault(h => h.item == kv.Key)?.quantity ?? 0;
                kv.Value.GetComponentInChildren<Text>().text = $"{HerbLabel(kv.Key)} ×{q}\n{PrepLabel(kv.Key)}";
            }
            grindPad.gameObject.SetActive(InMortar != null);
            if (InMortar != null)
            {
                grindPad.position = zones["mortar"].position;
                GrindProgress.TryGetValue(InMortar, out var g); grindText.text = $"畫圈研磨 {HerbLabel(InMortar)} {g / (View?.grindStrokes ?? 12):P0}";
            }
        }

        /// Anchor a drop zone over its prop, nudged by a canvas-unit offset so props that line up in depth stay readable.
        void Place(string zone, GameObject target, float up, Camera cam, Vector2 nudge)
        {
            if (target == null || cam == null) return;
            var p = cam.WorldToScreenPoint(target.transform.position + Vector3.up * up);
            var o = nudge * canvas.scaleFactor;
            zones[zone].position = new Vector3(p.x + o.x, p.y + o.y, 0); zones[zone].gameObject.SetActive(p.z > 0);
        }

        /// Push overlapping zone markers apart vertically so every drop target keeps its own area.
        void Separate()
        {
            float w = 200 * canvas.scaleFactor, h = 76 * canvas.scaleFactor; var list = zones.Values.ToList();
            for (int pass = 0; pass < 6; pass++)
                for (int i = 0; i < list.Count; i++)
                    for (int j = i + 1; j < list.Count; j++)
                    {
                        Vector3 a = list[i].position, b = list[j].position;
                        if (Mathf.Abs(a.x - b.x) >= w || Mathf.Abs(a.y - b.y) >= h) continue;
                        float push = (h - Mathf.Abs(a.y - b.y)) / 2 + 1, dir = a.y >= b.y ? 1 : -1;
                        list[i].position = a + Vector3.up * push * dir; list[j].position = b - Vector3.up * push * dir;
                    }
        }

        public string ZoneAt(Vector2 screen)
        {
            string best = null; float bestD = 120;
            foreach (var kv in zones) { if (!kv.Value.gameObject.activeSelf) continue; float d = Vector2.Distance(screen, kv.Value.position); if (d < bestD) { bestD = d; best = kv.Key; } }
            return best;
        }

        public Vector2 ZoneScreen(string zone) => zones[zone].position;

        void OnChipDropped(HerbChip chip, Vector2 screen)
        {
            switch (ZoneAt(screen))
            {
                case "mortar": DropOnMortar(chip.Herb); break;
                case "basket": DropOnBasket(chip.Herb); break;
                case "main": DropOnTray(chip.Herb, true); break;
                case "aux": DropOnTray(chip.Herb, false); break;
            }
        }

        // ---------------- panels

        Button Btn(Transform parent, string key, string text, System.Action click, Color? color = null)
        {
            var b = AlchemyUi.Button("Btn_" + key, parent, text, click, color); Buttons[key] = b; return b;
        }

        void Header(string title, string sub = null)
        {
            var h = AlchemyUi.Line(panelBody, title, 32, AlchemyUi.Ink, 42); h.fontStyle = FontStyle.Bold;
            if (sub != null) AlchemyUi.Line(panelBody, sub, 21, AlchemyUi.BambooDark);
        }

        public void BuildPanel()
        {
            if (panelBody == null) return;
            Buttons.Clear(); AlchemyUi.Clear(panelBody); modal.gameObject.SetActive(false);
            AlchemyUi.Clear(skipBar); skipBar.gameObject.SetActive(RevealPlaying);
            if (RevealPlaying) { Btn(skipBar, "SkipReveal", "開爐中…　略過演出", SkipReveal, AlchemyUi.BambooDark); return; } // keep the furnace in view
            if (Active == null) return;
            switch (Active.Id)
            {
                case "B05": PanelCabinet(); break;
                case "B07": PanelFuel(); break;
                case "B06": PanelWater(); break;
                case "B11": PanelScroll(); break;
                case "TABLE": PanelTable(); break;
                case "B01": if (Stage == Stage.Result && Session?.result != null) ShowResult(Session.result, false); else PanelFurnace(); break;
            }
            Btn(panelBody, "Leave", "離開（Esc）", Back, AlchemyUi.BambooDark);
        }

        void PanelCabinet()
        {
            Header("藥櫃", "取藥、辨材。辨識只揭示藥性，不會解鎖丹方。");
            var v = View; if (v == null) return;
            for (int i = 0; i < Herbs.Length; i++)
            {
                var h = v.herbs.First(x => x.id == Herbs[i]); int idx = i;
                AlchemyUi.Line(panelBody, h.identified ? $"{h.label}　持有 {h.owned}\n{h.nature}；{h.use}" : $"？？（未辨識）　持有 {h.owned}\n外觀：{h.identifyHint}", 22, null, 56);
                if (!h.identified) { var b = Btn(panelBody, "Identify_" + h.id, "辨識" + (h.owned > 0 ? "" : "（需持有）"), () => Identify(h.id)); b.interactable = h.owned > 0; }
                else if (Stage == Stage.Idle)
                {
                    var row = AlchemyUi.Row("Qty_" + h.id, panelBody);
                    Btn(row.transform, $"Less_{h.id}", "－", () => Adjust(idx, -1), AlchemyUi.BambooDark);
                    AlchemyUi.Line(row.transform, $"份量 {Pick[i]}", 26).alignment = TextAnchor.MiddleCenter;
                    Btn(row.transform, $"More_{h.id}", "＋", () => Adjust(idx, 1), AlchemyUi.BambooDark);
                }
                if (h.owned < Pick[i] || h.owned == 0) Btn(panelBody, "Buy_" + h.id, h.id == Herbs[0] ? "向阿禾購青靈草 3 株（4 靈石）" : "向阿禾購淨水蓮 2 株（4 靈石）", () => Buy(h.id == Herbs[0] ? "qingling-bundle" : "lotus-bundle"), AlchemyUi.BambooDark);
            }
            if (Stage != Stage.Idle) { AlchemyUi.Line(panelBody, "丹爐已有一爐進行中；藥材已鎖定在工作台。", 22, AlchemyUi.Cinnabar); return; }
            if (v.herbs.All(x => x.identified))
            {
                AlchemyUi.Line(panelBody, $"配比　青靈草 {Pick[0]}：淨水蓮 {Pick[1]}", 26, AlchemyUi.Cinnabar);
                Btn(panelBody, "ChooseHerbs", HerbsChosen ? "已取出（可再調整）" : "取出藥材", ChooseHerbs);
            }
        }

        void PanelFuel()
        {
            Header("柴箱", "松柴耐燒，一根約燃 20 息。柴多不等於火好。");
            var v = View; if (v == null) return;
            if (Stage != Stage.Idle) { AlchemyUi.Line(panelBody, $"爐邊還有 {FuelLeft} 根，添柴請在丹爐操作；煉完未燒的柴會退回。", 22); return; }
            AlchemyUi.Line(panelBody, $"持有松柴 {v.fuel} 根", 24);
            if (v.fuel == 0) { Btn(panelBody, "BuyFuel", "向阿禾購松柴 5 根（1 靈石）", () => Buy("firewood-bundle"), AlchemyUi.BambooDark); return; }
            var row = AlchemyUi.Row("FuelQty", panelBody);
            Btn(row.transform, "FuelLess", "－", () => AdjustFuel(-1), AlchemyUi.BambooDark);
            AlchemyUi.Line(row.transform, $"帶 {FuelPick} 根", 26).alignment = TextAnchor.MiddleCenter;
            Btn(row.transform, "FuelMore", "＋", () => AdjustFuel(1), AlchemyUi.BambooDark);
            Btn(panelBody, "BuyFuel", "向阿禾購松柴 5 根（1 靈石）", () => Buy("firewood-bundle"), AlchemyUi.BambooDark);
            var go = Btn(panelBody, "Begin", HerbsChosen ? $"搬柴到爐邊，開始煉製（扣除藥材與 {FuelPick} 根柴）" : "請先到藥櫃取出藥材", Begin, AlchemyUi.Cinnabar);
            go.interactable = HerbsChosen;
        }

        void PanelWater()
        {
            Header("陶水缸", "清泉水，舀到丹爐注入。");
            AlchemyUi.Line(panelBody, $"手上 {Ladles} 瓢（最多 3 瓢）", 26);
            Btn(panelBody, "Ladle", "舀一瓢", () => Ladle(1)); Btn(panelBody, "Pour", "倒回一瓢", () => Ladle(-1), AlchemyUi.BambooDark);
        }

        void PanelTable()
        {
            Header("工作台", "拖曳藥材到石臼研磨、晾藥籃陰乾、分料盤君臣兩格配伍。");
            if (Stage != Stage.Prep && Stage != Stage.Fire) { AlchemyUi.Line(panelBody, "尚未開始煉製：先到藥櫃取藥、柴箱取柴。", 22); return; }
            var v = View;
            AlchemyUi.Line(panelBody, $"陰乾需 {v?.drying.minSeconds ?? 8:0}–{v?.drying.maxSeconds ?? 24:0} 息，過久會焦乾。", 21, AlchemyUi.BambooDark);
            foreach (var h in Herbs) AlchemyUi.Line(panelBody, $"{HerbLabel(h)}：{PrepLabel(h)}", 24);
            AlchemyUi.Line(panelBody, $"君：{(MainHerb == null ? "（空）" : HerbLabel(MainHerb))}　臣：{(AuxHerb == null ? "（空）" : HerbLabel(AuxHerb))}", 24);
            foreach (var h in Herbs) if (DryIn.ContainsKey(h)) Btn(panelBody, "DryOut_" + h, "從晾藥籃取出" + HerbLabel(h), () => DryOut(h), AlchemyUi.BambooDark);
            Btn(panelBody, "Compound", Compounded ? "已配伍（可重新擺放）" : "配伍完成", Compound);
        }

        void PanelFurnace()
        {
            Header("青銅丹爐", "開蓋注水、依序投料，合蓋添柴點火；以排煙檔控火。");
            if (Stage == Stage.Idle) { AlchemyUi.Line(panelBody, "尚未開始：藥櫃取藥 → 柴箱取柴。", 22); var q = View?.recipes?.Where(r => r.quick).ToList(); if (q != null && q.Count > 0) AlchemyUi.Line(panelBody, "已掌握的丹方可在竹簡「丹方錄」快速煉製。", 22); return; }
            if (Furnace == null) return;
            var grid = AlchemyUi.Rect("Grid", panelBody, Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero);
            var gl = grid.gameObject.AddComponent<GridLayoutGroup>(); gl.cellSize = new Vector2(286, 58); gl.spacing = new Vector2(10, 8);
            grid.gameObject.AddComponent<LayoutElement>().minHeight = 5 * 66;
            Btn(grid, "Lid", lidOpen ? "合上爐蓋" : "掀開爐蓋", Lid);
            Btn(grid, "Water", $"注水（手上 {Ladles} 瓢）", PourWater);
            foreach (var h in Herbs) { var b = Btn(grid, "Charge_" + h, Furnace.IsCharged(h) ? HerbLabel(h) + "已入爐" : "投入" + HerbLabel(h), () => Charge(h)); b.interactable = !Furnace.IsCharged(h); }
            Btn(grid, "Fuel", $"添柴（剩 {FuelLeft}）", AddFuel, AlchemyUi.BambooDark);
            Btn(grid, "Ignite", "點火", Ignite, AlchemyUi.Cinnabar);
            Btn(grid, "Vent0", "排煙檔・閉", () => SetVent(0), AlchemyUi.BambooDark);
            Btn(grid, "Vent5", "排煙檔・半", () => SetVent(.5f), AlchemyUi.BambooDark);
            Btn(grid, "Vent1", "排煙檔・全", () => SetVent(1), AlchemyUi.BambooDark);
            Btn(grid, "Mouth", Director.Current == Shot.Mouth ? "回到過肩" : "爐口特寫", ToggleMouth, AlchemyUi.BambooDark);
            Btn(panelBody, "Condense", "收丹（結束本爐，交由伺服器判定）", Condense, AlchemyUi.Cinnabar);
            AlchemyUi.Line(panelBody, "已投料後放棄，材料作廢只得丹渣。", 20, AlchemyUi.BambooDark);
        }

        void PanelScroll()
        {
            Header("竹簡");
            var tabs = AlchemyUi.Row("Tabs", panelBody, 6);
            foreach (var t in new[] { ("herbs", "藥材錄"), ("recipes", "丹方錄"), ("manuals", "丹道推演"), ("history", "煉丹紀錄") })
                Btn(tabs.transform, "Tab_" + t.Item1, t.Item2, () => { ScrollTab = t.Item1; BuildPanel(); }, ScrollTab == t.Item1 ? AlchemyUi.Cinnabar : AlchemyUi.BambooDark);
            var v = View; if (v == null) return;
            switch (ScrollTab)
            {
                case "herbs":
                    foreach (var h in v.herbs) AlchemyUi.Line(panelBody, h.identified ? $"【{h.label}】{h.nature}\n　{h.use}" : "【？】尚未辨識", 22, null, 60);
                    break;
                case "recipes":
                    foreach (var r in v.recipes)
                    {
                        AlchemyUi.Line(panelBody, r.known ? $"【{r.label}】{r.effect}" : "【？】尚未領悟", 24, r.known ? AlchemyUi.Cinnabar : AlchemyUi.Ink);
                        if (r.known) foreach (var line in r.summary) AlchemyUi.Line(panelBody, "　" + line, 20);
                        if (r.quick && Stage == Stage.Idle) Btn(panelBody, "Quick_" + r.id, $"快速煉製{r.label}（得凡品或良品）", () => Quick(r.id));
                    }
                    break;
                case "manuals":
                    AlchemyUi.Line(panelBody, "推演只給方向，不會直接解鎖丹方。", 20, AlchemyUi.BambooDark);
                    foreach (var m in v.manuals)
                    {
                        AlchemyUi.Line(panelBody, $"{m.label}　{(m.unlocked ? "已得" : "未得：" + m.requirement)}", 23, m.unlocked ? AlchemyUi.Cinnabar : AlchemyUi.BambooDark);
                        if (m.unlocked) foreach (var group in m.lines) foreach (var line in group.lines) AlchemyUi.Line(panelBody, $"　{(KnownRecipe(group.recipe) ? RecipeLabel(group.recipe) : "某丹")}：{line}", 20);
                    }
                    break;
                case "history":
                    var hist = Api.State.player.alchemy?.history;
                    if (hist == null || hist.Length == 0) AlchemyUi.Line(panelBody, "尚無紀錄。", 22);
                    else foreach (var h in hist.Take(8)) AlchemyUi.Line(panelBody, $"{h.label}{(h.score > 0 ? $"（{h.score} 分）" : "")}{(h.reasons != null && h.reasons.Length > 0 ? "\n　" + h.reasons[0] : "")}", 20, null, 44);
                    break;
            }
        }

        string RecipeLabel(string id) => View?.recipes?.FirstOrDefault(r => r.id == id)?.label ?? "？";

        void ShowModal(System.Action<Transform> fill)
        {
            AlchemyUi.Clear(modalBody); modal.gameObject.SetActive(true); fill(modalBody);
            StartCoroutine(FitModal());
        }

        /// Size the modal to its content (cleared children are destroyed at end of frame, so measure a frame later).
        System.Collections.IEnumerator FitModal()
        {
            yield return null;
            LayoutRebuilder.ForceRebuildLayoutImmediate(modalBody);
            modal.sizeDelta = new Vector2(modal.sizeDelta.x, Mathf.Clamp(LayoutUtility.GetPreferredHeight(modalBody), 220, 900));
        }

        void ShowResult(AlchemyResult r, bool fresh)
        {
            Stage = Stage.Result; Buttons.Clear();
            if (Active == null) Active = stations.First(s => s.Id == "B01");
            ShowModal(m =>
            {
                var title = AlchemyUi.Line(m, r.success ? $"{OutputLabel(r.output)}・{r.label}" : "煉丹失敗", 44, r.success ? AlchemyUi.Cinnabar : AlchemyUi.Ink, 56); title.alignment = TextAnchor.MiddleCenter;
                if (r.firstUnlock) { var u = AlchemyUi.Line(m, $"領悟新丹方：{OutputLabel(r.output)}（已永久記入丹方錄）", 28, AlchemyUi.Jade); u.alignment = TextAnchor.MiddleCenter; }
                if (r.parts != null) AlchemyUi.Line(m, $"總分 {r.score}　配比 {r.parts.ratio:P0}・處理 {r.parts.prep:P0}・火候 {r.parts.fire:P0}・收丹 {r.parts.condense:P0}", 23);
                AlchemyUi.Line(m, r.success ? $"成丹 {r.quantity} 枚，待裝瓶。" : "得丹渣一份。", 23);
                foreach (var reason in (r.reasons ?? new string[0]).Take(5)) AlchemyUi.Line(m, "・" + reason, 21);
                AlchemyUi.Line(m, $"煉丹熟練 +{r.xpGain}（Lv{r.level}）・用柴 {r.fuelUsed} 根，退回 {r.fuelReturned} 根", 21, AlchemyUi.BambooDark);
                Btn(m, "Claim", r.success ? "以蠟封瓶裝瓶領取" : "收拾丹渣", Claim, AlchemyUi.Cinnabar);
            });
            if (fresh && r.success) sfx.PlayOneShot(chime, .8f);
        }

        void ShowRelogFire()
        {
            Active = stations.First(s => s.Id == "B01");
            ShowModal(m =>
            {
                AlchemyUi.Line(m, "爐火已熄", 40, AlchemyUi.Cinnabar);
                AlchemyUi.Line(m, "重新登入後無法接續燃燒中的一爐。藥材已入爐，結算後材料作廢、得丹渣一份。", 24);
                Btn(m, "SettleLost", "結算此爐", Abandon, AlchemyUi.Cinnabar);
            });
        }

        void ShowMenu()
        {
            bool charged = Session != null && Session.charged;
            ShowModal(m =>
            {
                AlchemyUi.Line(m, "選單", 36);
                AlchemyUi.Line(m, charged ? "已投料：放棄後材料作廢，得丹渣一份。" : "尚未投料：放棄後藥材與柴薪全數退回。", 24);
                Btn(m, "Abandon", charged ? "棄爐" : "取消本爐（退回材料）", Abandon, AlchemyUi.Cinnabar);
                Btn(m, "Resume", "繼續", () => modal.gameObject.SetActive(false), AlchemyUi.BambooDark);
            });
        }
    }
}
