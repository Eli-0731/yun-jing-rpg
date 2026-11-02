using System.Collections;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.UI;
using QingxiWorld;
using YunJing.Alchemy;

namespace YunJing.HarvestMarket
{
    // 坊市・出售, at joshsu54's herb stall (Market_HerbalStall). Left: the bundles the player brought, each "賣" or
    // "留著". Right: the stall's 今天收 board. 秤: the steelyard counterweight slides out (1 s), the coins show,
    // a coin string drops on the table, the stall keeper says a line or two. Kept bundles go back to the bag.
    // Never a loss: no haggling, nothing refused, the lowest grade still pays. Ends with market.sold.
    public sealed class QingxiMarketSellPanel : MonoBehaviour
    {
        public static QingxiMarketSellPanel Current { get; private set; }

        public Transform scaleWeight;                    // MK01 counterweight, slides on its local X
        public float weightMin = .04f, weightMax = .5f;  // MK01 spec: 0–0.5 m along the beam
        public float weighSeconds = 1f;
        public Transform coinDrop;                       // where the coin string lands on the table
        public GameObject coinStringPrefab;              // MK03 coin string; empty means a placeholder
        public int day = 4;
        public HarvestCameraRig rig; public int weighView = -1;   // close-up of the steelyard and the counter while weighing
        public GameObject[] panBundles = new GameObject[3];       // top, mid, low MK02 bundles in the MK01 pan (hidden)
        public Transform steelyard, hook;                         // MK01 root and its SOCKET_hook: the beam tilts about the hook

        public bool Open { get; private set; }
        public bool Weighed { get; private set; }
        public HarvestSettlement Last { get; private set; }
        public readonly List<bool> Sell = new List<bool>();

        Canvas canvas; RectTransform panel, left, result; readonly List<Button> toggles = new List<Button>(); readonly List<Text> keepNotes = new List<Text>();
        Button weighButton, doneButton; Text keeper, coinsText; Vector3 weightHome; bool weightHomeSet; GameObject soldCoins;

        void Awake() { Current = this; }

        public void Show()
        {
            if (Open) return;
            Open = true; Weighed = false; Balanced = false; Balancing = false; Last = null; Sell.Clear();
            foreach (var _ in HarvestCarry.Bundles) Sell.Add(true);
            if (scaleWeight != null && !weightHomeSet) { weightHome = scaleWeight.localPosition; weightHomeSet = true; }
            Build();
            QingxiFirstPerson.Current?.SetMenuOpen(true);
        }

        public void Close()
        {
            if (!Open) return;
            Open = false; if (canvas != null) Destroy(canvas.gameObject);
            QingxiFirstPerson.Current?.SetMenuOpen(false);
        }

        void Build()
        {
            canvas = HarvestUi.Canvas("MarketSellCanvas", 21); toggles.Clear(); keepNotes.Clear();
            panel = AlchemyUi.Slips("SellPanel", canvas.transform, Vector2.zero, Vector2.one, new Vector2(60, 60), new Vector2(-60, -60));
            var title = HarvestUi.Label("Title", panel, "草藥攤・出售", 40, TextAnchor.UpperCenter, AlchemyUi.Ink);
            ((RectTransform)title.transform).offsetMax = new Vector2(0, -26);

            // Left: the bundles brought from the field.
            left = AlchemyUi.Rect("Bundles", panel, new Vector2(0, 0), new Vector2(.58f, 1), new Vector2(40, 40), new Vector2(-20, -100));
            var head = HarvestUi.Label("Head", left, "你帶來的草藥捆", 30, TextAnchor.UpperLeft, AlchemyUi.Ink);
            if (HarvestCarry.Bundles.Count == 0) HarvestUi.Label("Empty", left, "\n\n背簍裡沒有草藥。", 30, TextAnchor.UpperLeft, AlchemyUi.Ink);
            for (int i = 0; i < HarvestCarry.Bundles.Count; i++)
            {
                var b = HarvestCarry.Bundles[i]; int index = i;
                var card = AlchemyUi.Panel("Bundle_" + i, left, Vector2.zero, Vector2.zero, Vector2.zero, Vector2.zero, new Color(.95f, .9f, .76f, .9f));
                HarvestUi.Fixed((RectTransform)card.transform, new Vector2(0, 1), new Vector2(0, -60 - i * 190), new Vector2(980, 170));
                card.gameObject.AddComponent<Outline>().effectColor = AlchemyUi.BambooDark;
                var name = HarvestUi.Label("Name", card.transform, $"{HarvestContent.Label(b.bin)}捆・{b.grades.Count} 株", 30, TextAnchor.UpperLeft, AlchemyUi.Ink);
                ((RectTransform)name.transform).offsetMin = new Vector2(20, 0); ((RectTransform)name.transform).offsetMax = new Vector2(0, -12);
                // The sort bonus shows before weighing: careful sorting shows up as money, mixing costs nothing.
                bool clean = b.grades.All(g => g == b.bin);
                var tag = AlchemyUi.Panel("SortTag", card.transform, Vector2.zero, Vector2.zero, Vector2.zero, Vector2.zero, clean ? new Color(.27f, .55f, .4f, .95f) : new Color(.55f, .45f, .3f, .85f));
                HarvestUi.Fixed((RectTransform)tag.transform, new Vector2(0, 1), new Vector2(250, -10), new Vector2(clean ? 260 : 330, 46)); tag.raycastTarget = false;
                HarvestUi.Label("Text", tag.transform, clean ? $"整捆同級 +{HarvestContent.sortBonus}" : "混了別的等級，照實算", 26, TextAnchor.MiddleCenter, Color.white);
                // What keeping is for (the alchemy workshop takes qingling-herb), shown while the bundle is set to 留著.
                var note = HarvestUi.Label("KeepNote", card.transform, "留著：可帶去丹房煉丹", 26, TextAnchor.LowerRight, AlchemyUi.BambooDark);
                HarvestUi.Fixed((RectTransform)note.transform, new Vector2(1, 0), new Vector2(-270, 14), new Vector2(330, 40));
                note.gameObject.SetActive(false); keepNotes.Add(note);
                for (int k = 0; k < b.grades.Count; k++)
                {
                    var herb = HarvestUi.Sprite("Herb", card.transform, HarvestArt.Herb(b.grades[k]), new Vector2(110, 110));
                    HarvestUi.Fixed((RectTransform)herb.transform, new Vector2(0, 0), new Vector2(20 + k * 104, 6), new Vector2(110, 110));
                }
                var t = HarvestUi.Button("Toggle", card.transform, "賣", () => Toggle(index), new Vector2(1, .5f), new Vector2(-20, 0), new Vector2(230, 120), AlchemyUi.Jade, 36);
                toggles.Add(t);
            }

            // Right: what the stall buys today. The board is blank in the world; the words are UI.
            var board = AlchemyUi.Panel("TodayBoard", panel, Vector2.zero, Vector2.zero, Vector2.zero, Vector2.zero, new Color(.48f, .34f, .2f, .96f));
            HarvestUi.Fixed((RectTransform)board.transform, new Vector2(1, 1), new Vector2(-40, -100), new Vector2(560, 470));
            var bt = HarvestUi.Label("Title", board.transform, "今天收", 38, TextAnchor.UpperCenter, new Color(.98f, .92f, .76f));
            ((RectTransform)bt.transform).offsetMax = new Vector2(0, -18);
            var icon = HarvestUi.Sprite("Herb", board.transform, HarvestArt.Herb("mid"), new Vector2(150, 150));
            HarvestUi.Fixed((RectTransform)icon.transform, new Vector2(.5f, 1), new Vector2(0, -80), new Vector2(150, 150));
            int bonus = HarvestContent.DemandBonus(day);
            var demand = HarvestUi.Label("Demand", board.transform, bonus > 0 ? $"青靈草　每捆加 {bonus}" : "青靈草　照常收", 32, TextAnchor.UpperCenter, new Color(.98f, .92f, .76f));
            ((RectTransform)demand.transform).offsetMax = new Vector2(0, -244);
            var prices = string.Join("　", HarvestContent.gradeRows.Select(g => $"{g.label} {g.bundlePrice + bonus}"));
            var table = HarvestUi.Label("Prices", board.transform, prices + "\n（一捆三株，不滿照比例）", 26, TextAnchor.UpperCenter, new Color(.95f, .88f, .7f));
            ((RectTransform)table.transform).offsetMax = new Vector2(0, -300);

            // Weigh: the big button in the right-thumb corner.
            weighButton = HarvestUi.Button("Weigh", panel, "秤", Weigh, new Vector2(1, 0), new Vector2(-40, 40), new Vector2(560, 150), AlchemyUi.Cinnabar, 48);
            RefreshWeigh();
        }

        public void Toggle(int index)
        {
            if (Weighed || index < 0 || index >= Sell.Count) return;
            Sell[index] = !Sell[index];
            AlchemyUi.SetText(toggles[index], Sell[index] ? "賣" : "留著");
            toggles[index].GetComponent<Image>().color = Sell[index] ? AlchemyUi.Jade : AlchemyUi.BambooDark;
            keepNotes[index].gameObject.SetActive(!Sell[index]);
            RefreshWeigh();
        }

        void RefreshWeigh() { if (weighButton != null) AlchemyUi.SetText(weighButton, Sell.Any(s => s) ? "秤" : "都留著"); }

        public void Weigh()
        {
            if (Weighed) return;
            Weighed = true;
            Last = HarvestRules.Settle(day, HarvestCarry.Bundles, Sell);
            HarvestCarry.Coins += Last.totalCoins;
            foreach (var (q, n) in Last.kept) HarvestCarry.Kept[q] = (HarvestCarry.Kept.TryGetValue(q, out var had) ? had : 0) + n;
            foreach (var t in toggles) t.interactable = false;
            weighButton.gameObject.SetActive(false);
            StartCoroutine(WeighRoutine());
        }

        IEnumerator WeighRoutine()
        {
            result = AlchemyUi.Slips("Result", panel, Vector2.zero, Vector2.zero, Vector2.zero, Vector2.zero);
            HarvestUi.Fixed(result, new Vector2(1, 0), new Vector2(-40, 40), new Vector2(560, 330));
            var coin = HarvestUi.Sprite("Coin", result, HarvestArt.Coin(), new Vector2(84, 84));
            HarvestUi.Fixed((RectTransform)coin.transform, new Vector2(0, 1), new Vector2(26, -28), new Vector2(84, 84));
            coinsText = HarvestUi.Label("Coins", result, "", 46, TextAnchor.UpperLeft, AlchemyUi.Ink);
            ((RectTransform)coinsText.transform).offsetMin = new Vector2(126, 0); ((RectTransform)coinsText.transform).offsetMax = new Vector2(0, -42);
            keeper = HarvestUi.Label("Keeper", result, "", 28, TextAnchor.UpperLeft, AlchemyUi.Ink);
            ((RectTransform)keeper.transform).offsetMin = new Vector2(26, 120); ((RectTransform)keeper.transform).offsetMax = new Vector2(-20, -128);

            if (Last.totalCoins > 0)
            {
                // The sheet steps aside and the view leans in over the counter so the weighing happens in the world:
                // the counterweight slides out along the beam (more coins, farther out; full beam at 12), the coin
                // string drops on the counter, and the coins fly up one by one into the count at the top.
                var group = panel.gameObject.GetComponent<CanvasGroup>() ?? panel.gameObject.AddComponent<CanvasGroup>();
                var strip = AlchemyUi.Slips("WeighStrip", canvas.transform, new Vector2(.5f, 1), new Vector2(.5f, 1), Vector2.zero, Vector2.zero);
                HarvestUi.Fixed(strip, new Vector2(.5f, 1), new Vector2(0, -24), new Vector2(520, 96));
                var count = HarvestUi.Label("Count", strip, "秤一秤……", 38, TextAnchor.MiddleCenter, AlchemyUi.Ink);
                bool lean = rig != null && weighView >= 0 && weighView < rig.views.Length;
                Vector3 backPos = lean ? rig.transform.position : Vector3.zero; Quaternion backRot = lean ? rig.transform.rotation : Quaternion.identity;
                StartCoroutine(Fade(group, 1, 0, .3f));
                if (lean) yield return rig.MoveTo(weighView, .7f); else yield return new WaitForSeconds(.3f);
                yield return LoadPan();
                yield return Balance(Mathf.Lerp(weightMin, weightMax, Mathf.Clamp01(Last.totalCoins / 12f)), count);
                yield return DropCoins();
                yield return FlyCoins(strip, count);
                coinsText.text = $"得 {Last.totalCoins} 靈石";
                yield return new WaitForSeconds(.8f);
                Destroy(strip.gameObject);
                if (lean) StartCoroutine(rig.MoveTo(backPos, backRot, .6f));
                yield return Fade(group, 0, 1, .3f);
            }
            else coinsText.text = "都留著";
            foreach (var id in Last.lines) { keeper.text = "攤主：" + HarvestContent.Line(id); yield return new WaitForSeconds(1.4f); }
            doneButton = HarvestUi.Button("Done", panel, "收好", Finish, new Vector2(1, 0), new Vector2(-40, 390), new Vector2(560, 110), AlchemyUi.Jade, 36);
        }

        // --- balancing the steelyard ---------------------------------------------------------------------------
        // The player drags the counterweight along the beam (anywhere on screen; the arrow keys work too). Too close
        // in and the beam's tail tips up, too far out and it droops; within BalanceSlack it levels and, on release,
        // clicks into place. Never a fail: after BalanceAssist seconds without input it slides home by itself.
        // The beam's stars are marked in spirit stones (CoinsOnBeam over the full travel) and a reading rides on the
        // counterweight, so the balance point is the price: the player weighs out what the bundles fetch.
        // Only the first sale is by hand; later ones balance themselves (dragging still takes over).
        const int CoinsOnBeam = 12;
        public bool AutoWeigh { get; private set; }
        public bool Balancing { get; private set; }
        public bool Balanced { get; private set; }
        const float BalanceSlack = .035f, BalanceAssist = 6f, MaxTilt = 9f;
        float weightX, balanceTarget;

        Vector3 BeamPoint(float x) => scaleWeight.parent.position + scaleWeight.parent.right * x;
        public Vector2 WeightScreen => Camera.main.WorldToScreenPoint(BeamPoint(weightX));
        public Vector2 BalanceScreen => Camera.main.WorldToScreenPoint(BeamPoint(balanceTarget));

        IEnumerator Balance(float target, Text count)
        {
            if (scaleWeight == null) yield break;
            Balancing = true; Balanced = false; balanceTarget = target; weightX = weightMin;
            AutoWeigh = HarvestCarry.Weighings > 0;
            var stars = new List<(Text label, float x)>();
            for (int n = 2; n <= CoinsOnBeam; n += 2)
            {
                var star = HarvestUi.Label("BeamStar_" + n, canvas.transform, n.ToString(), 24, TextAnchor.MiddleCenter, new Color(1f, .93f, .72f));
                var srt = (RectTransform)star.transform; srt.anchorMin = srt.anchorMax = new Vector2(.5f, .5f); srt.sizeDelta = new Vector2(48, 34);
                star.gameObject.AddComponent<Outline>().effectColor = new Color(.12f, .07f, .03f, .9f);
                stars.Add((star, Mathf.Lerp(weightMin, weightMax, n / (float)CoinsOnBeam)));
            }
            var bubble = AlchemyUi.Panel("Reading", canvas.transform, new Vector2(.5f, .5f), new Vector2(.5f, .5f), Vector2.zero, Vector2.zero, new Color(.12f, .09f, .06f, .82f));
            bubble.raycastTarget = false;
            var reading = HarvestUi.Label("Text", bubble.transform, "", 32, TextAnchor.MiddleCenter, Color.white);
            float punch = 0; bool shown = false;
            Transform yard = steelyard; Vector3 hinge = hook != null ? hook.position : scaleWeight.parent.position;
            Vector3 homePos = yard != null ? yard.position : Vector3.zero; Quaternion homeRot = yard != null ? yard.rotation : Quaternion.identity;
            Vector3 axis = Vector3.Cross(scaleWeight.parent.right, Vector3.up).normalized;   // + raises the beam's outer end
            float tilt = 0, idle = 0, levelFor = 0; bool held = false, assist = AutoWeigh; var cam = Camera.main;
            while (true)
            {
                var pointer = Pointer.current; var kb = Keyboard.current; bool input = false;
                if (pointer != null && cam != null)
                {
                    if (pointer.press.wasPressedThisFrame) { held = true; assist = false; }
                    if (held && pointer.press.isPressed)
                    {
                        // project the finger onto the beam as drawn on screen
                        Vector2 s0 = cam.WorldToScreenPoint(BeamPoint(0)), s1 = cam.WorldToScreenPoint(BeamPoint(weightMax)), seg = s1 - s0;
                        weightX = Mathf.Clamp(Vector2.Dot(pointer.position.ReadValue() - s0, seg) / seg.sqrMagnitude * weightMax, weightMin, weightMax);
                        input = true;
                    }
                    else if (held) { held = false; if (Mathf.Abs(weightX - target) < BalanceSlack) weightX = target; }
                }
                if (kb != null)
                {
                    float dir = (kb.rightArrowKey.isPressed || kb.dKey.isPressed ? 1 : 0) - (kb.leftArrowKey.isPressed || kb.aKey.isPressed ? 1 : 0);
                    if (dir != 0) { weightX = Mathf.Clamp(weightX + dir * .25f * Time.deltaTime, weightMin, weightMax); input = true; assist = false; }
                    else if (kb.leftArrowKey.wasReleasedThisFrame || kb.rightArrowKey.wasReleasedThisFrame || kb.aKey.wasReleasedThisFrame || kb.dKey.wasReleasedThisFrame)
                    { if (Mathf.Abs(weightX - target) < BalanceSlack) weightX = target; }
                    if (kb.spaceKey.wasPressedThisFrame || kb.enterKey.wasPressedThisFrame) assist = true;
                }
                idle = input ? 0 : idle + Time.deltaTime;
                if (idle > BalanceAssist) assist = true;
                if (assist && !held) weightX = Mathf.MoveTowards(weightX, target, .3f * Time.deltaTime);
                scaleWeight.localPosition = weightHome + Vector3.right * weightX;

                float off = weightX - target; bool level = Mathf.Abs(off) < .002f || (!held && Mathf.Abs(off) < BalanceSlack);
                tilt = Mathf.Lerp(tilt, level ? 0 : Mathf.Clamp(-off / weightMax * 40, -MaxTilt, MaxTilt), 1 - Mathf.Exp(-Time.deltaTime * 8));
                if (yard != null) { var r = Quaternion.AngleAxis(tilt, axis); yard.SetPositionAndRotation(hinge + r * (homePos - hinge), r * homeRot); }
                if (AutoWeigh && assist) count.text = "秤一秤……";
                else count.text = Mathf.Abs(off) < BalanceSlack ? (held ? "平了！放手" : "平了！") : off < 0 ? "秤尾翹起：秤砣往外推" : "秤尾垂下：秤砣往內收";
                // stars ride just above the (tilting) beam; the reading sits over the counterweight
                float lift = 30 * canvas.scaleFactor;
                foreach (var (label, x) in stars) label.transform.position = (Vector2)cam.WorldToScreenPoint(BeamPoint(x)) + new Vector2(0, lift);
                bool settled = !held && Mathf.Abs(off) < .002f;
                if (settled && !shown) { shown = true; punch = 1; }
                punch = Mathf.MoveTowards(punch, 0, Time.deltaTime * 3);
                reading.text = settled ? $"{Last.totalCoins} 靈石" : $"{Mathf.RoundToInt(weightX / weightMax * CoinsOnBeam)}";
                bubble.color = settled ? new Color(.2f, .5f, .36f, .92f) : new Color(.12f, .09f, .06f, .82f);
                ((RectTransform)bubble.transform).sizeDelta = new Vector2(settled ? 170 : 90, 56);
                bubble.transform.position = (Vector2)cam.WorldToScreenPoint(BeamPoint(weightX)) + new Vector2(0, lift + 46 * canvas.scaleFactor);
                bubble.transform.localScale = Vector3.one * (1 + .3f * punch);
                levelFor = !held && Mathf.Abs(off) < .002f ? levelFor + Time.deltaTime : 0;
                if (levelFor > .6f) break;   // long enough to read the price
                yield return null;
            }
            if (yard != null) yard.SetPositionAndRotation(homePos, homeRot);
            foreach (var (label, _) in stars) Destroy(label.gameObject);
            Destroy(bubble.gameObject);
            count.text = $"秤得 {Last.totalCoins} 靈石";
            HarvestCarry.Weighings++;
            Balancing = false; Balanced = true;
        }

        static IEnumerator Fade(CanvasGroup g, float from, float to, float seconds)
        {
            g.blocksRaycasts = to > .5f;
            for (float t = 0; t < seconds; t += Time.deltaTime) { g.alpha = Mathf.Lerp(from, to, t / seconds); yield return null; }
            g.alpha = to;
        }

        IEnumerator DropCoins()
        {
            if (coinDrop == null) yield break;
            GameObject coins;
            if (coinStringPrefab != null) coins = Instantiate(coinStringPrefab);
            else
            {
                coins = GameObject.CreatePrimitive(PrimitiveType.Cylinder); Destroy(coins.GetComponent<Collider>());
                coins.transform.localScale = new Vector3(.12f, .006f, .03f);
                coins.GetComponent<Renderer>().material.color = new Color(.6f, .48f, .24f);
            }
            coins.name = "SoldCoins"; soldCoins = coins;
            var end = coinDrop.position; var start = end + Vector3.up * .45f; var size = coins.transform.localScale; float t = 0;
            while (t < .4f) { t += Time.deltaTime; float k = Mathf.Min(1, t / .4f); coins.transform.position = Vector3.Lerp(start, end, k * k); yield return null; }
            // lands with a squash and two small bounces
            for (t = 0; t < .45f; t += Time.deltaTime)
            {
                float k = t / .45f, hop = Mathf.Abs(Mathf.Sin(k * Mathf.PI * 2)) * (1 - k) * .05f, squash = 1 - .3f * Mathf.Exp(-k * 9);
                coins.transform.position = end + Vector3.up * hop;
                coins.transform.localScale = Vector3.Scale(size, new Vector3(2 - squash, squash, 2 - squash));
                yield return null;
            }
            coins.transform.SetPositionAndRotation(end, coins.transform.rotation); coins.transform.localScale = size;
        }

        /// The sold bundles (one per grade sold) drop into the pan before the counterweight moves.
        IEnumerator LoadPan()
        {
            var bins = new[] { "top", "mid", "low" };
            var load = Enumerable.Range(0, 3).Where(k => panBundles[k] != null && Last.bundles.Any(b => b.sold && b.bin == bins[k])).Select(k => panBundles[k].transform).ToList();
            if (load.Count == 0) yield break;
            var rest = load.Select(t => t.localPosition).ToList();
            foreach (var t in load) t.gameObject.SetActive(true);
            for (float t = 0; t < .35f; t += Time.deltaTime)
            {
                float k = t / .35f;
                for (int i = 0; i < load.Count; i++) load[i].localPosition = rest[i] + Vector3.up * (.3f * (1 - k * k));
                yield return null;
            }
            for (int i = 0; i < load.Count; i++) load[i].localPosition = rest[i];
        }

        /// One coin sprite per stone flies from the coin string up into the count; each landing ticks it up.
        IEnumerator FlyCoins(RectTransform strip, Text count)
        {
            var cam = Camera.main; int total = Last.totalCoins, landed = 0;
            Vector2 from = cam != null && coinDrop != null ? (Vector2)cam.WorldToScreenPoint(coinDrop.position) : new Vector2(Screen.width / 2f, Screen.height / 3f);
            Vector2 to = (Vector2)strip.position - new Vector2(0, 48 * canvas.scaleFactor);   // the strip hangs from its top edge
            const float flight = .45f, gap = .12f;
            var flying = new List<(RectTransform rt, float start, Vector2 bend)>();
            for (int i = 0; i < total; i++)
            {
                var img = HarvestUi.Sprite("FlyingCoin", canvas.transform, HarvestArt.Coin(), new Vector2(64, 64)); img.raycastTarget = false;
                var rt = (RectTransform)img.transform; rt.position = from; rt.gameObject.SetActive(false);
                flying.Add((rt, i * gap, new Vector2(Random.Range(-160f, 160f), Random.Range(60f, 160f)) * canvas.scaleFactor));
            }
            count.text = "0 靈石"; float punch = 0, t = 0;
            while (landed < total || punch > 0)
            {
                t += Time.deltaTime;
                foreach (var (rt, start, bend) in flying)
                {
                    if (rt == null) continue;
                    float k = (t - start) / flight; if (k < 0) continue;
                    rt.gameObject.SetActive(true);
                    if (k >= 1) { Destroy(rt.gameObject); landed++; count.text = $"{landed} 靈石"; punch = 1; continue; }
                    float e = k * k * (3 - 2 * k);   // smoothstep
                    rt.position = Vector2.Lerp(Vector2.Lerp(from, from + bend, e), Vector2.Lerp(from + bend, to, e), e);
                    rt.localScale = Vector3.one * (1.2f - .5f * k); rt.localRotation = Quaternion.Euler(0, 0, k * 540);
                }
                punch = Mathf.MoveTowards(punch, 0, Time.deltaTime * 5);
                strip.localScale = Vector3.one * (1 + .12f * punch);
                yield return null;
            }
            strip.localScale = Vector3.one; count.text = $"得 {total} 靈石";
        }

        public Button DoneButton => doneButton;
        public Button ToggleButton(int index) => toggles[index];
        public Button WeighButton => weighButton;

        public void Finish()
        {
            if (!Weighed || Last == null) return;
            HarvestMarketEvents.EmitSold(day, Last);
            HarvestCarry.Bundles = new List<HerbBundle>();
            if (scaleWeight != null) scaleWeight.localPosition = weightHome;
            foreach (var b in panBundles) if (b != null) b.SetActive(false);
            if (soldCoins != null) Destroy(soldCoins);   // the player pockets the string; the next sale lands on a clear counter
            Close();
        }

        void Update()
        {
            if (!Open) return;
            var kb = Keyboard.current; if (kb == null) return;
            for (int i = 0; i < Mathf.Min(Sell.Count, 9); i++) if (kb[(Key)((int)Key.Digit1 + i)].wasPressedThisFrame) Toggle(i);
            if (kb.spaceKey.wasPressedThisFrame || kb.enterKey.wasPressedThisFrame) { if (!Weighed) Weigh(); else if (doneButton != null) Finish(); }
            if (kb.escapeKey.wasPressedThisFrame && !Weighed) Close();   // walking away before weighing keeps everything
        }
    }
}
