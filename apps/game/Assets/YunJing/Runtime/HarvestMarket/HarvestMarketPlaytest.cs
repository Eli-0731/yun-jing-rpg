using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.LowLevel;
using UnityEngine.UI;
using TouchPhase = UnityEngine.InputSystem.TouchPhase;

namespace YunJing.HarvestMarket
{
    // Scripted player for the harvest test scene (-harvestPlaytest). Unlike the tea playtest it does not call the
    // panels' methods: it drives a virtual Input System touchscreen, so every pull, drag and tap goes through the
    // same Pointer / EventSystem path a phone thumb does. Run: pull six herbs (one yanked too fast), sort them (one
    // low herb dropped on the mid bundle), walk to the stall, sell two bundles and keep one. Frames every
    // -harvestFrameEvery seconds for the recording.
    public sealed class HarvestMarketPlaytest : MonoBehaviour
    {
        [Serializable] class Step { public int index; public string name; public bool pass; public string note; public float seconds; public string shot; }
        [Serializable] class Report { public string started, resolution, input; public bool pass; public float frameEvery; public int frames; public List<Step> steps = new List<Step>(); public List<string> events = new List<string>(); }

        public QingxiHarvestPanel field; public QingxiMarketSellPanel stall; public HarvestCameraRig rig;
        string outDir; readonly Report report = new Report(); float t0, nextFrame; int index, frame; bool capturing; Touchscreen finger;

        static string Arg(string name)
        {
            var args = Environment.GetCommandLineArgs(); int i = Array.IndexOf(args, name);
            return i >= 0 && i + 1 < args.Length ? args[i + 1] : null;
        }

        void Start()
        {
            if (!Environment.GetCommandLineArgs().Contains("-harvestPlaytest")) { enabled = false; return; }
            Application.runInBackground = true;
            outDir = Arg("-harvestOut") ?? Path.Combine(Application.persistentDataPath, "harvest-playtest");
            Directory.CreateDirectory(Path.Combine(outDir, "frames"));
            report.frameEvery = float.TryParse(Arg("-harvestFrameEvery"), out var every) ? every : .1f;
            report.started = DateTime.Now.ToString("s"); report.resolution = Screen.width + "x" + Screen.height;
            report.input = "virtual Input System Touchscreen (one finger)";
            HarvestMarketEvents.Emitted += (n, j) => report.events.Add(n + " " + j);
            finger = InputSystem.AddDevice<Touchscreen>("PlaytestFinger");
            StartCoroutine(Run());
        }

        void LateUpdate() { if (capturing && Time.realtimeSinceStartup >= nextFrame) { nextFrame += report.frameEvery; StartCoroutine(Save(Path.Combine("frames", $"{frame++:00000}.png"))); } }

        IEnumerator Save(string file)
        {
            yield return new WaitForEndOfFrame();
            var tex = new Texture2D(Screen.width, Screen.height, TextureFormat.RGB24, false);
            tex.ReadPixels(new Rect(0, 0, Screen.width, Screen.height), 0, 0); tex.Apply();
            File.WriteAllBytes(Path.Combine(outDir, file), tex.EncodeToPNG()); Destroy(tex);
        }

        IEnumerator Shot(string name) { var file = $"{index:00}_{name}.png"; report.steps[report.steps.Count - 1].shot = file; yield return Save(file); }

        void Mark(string name, bool pass, string note = "")
        {
            report.steps.Add(new Step { index = ++index, name = name, pass = pass, note = note, seconds = Time.realtimeSinceStartup - t0 });
            Debug.Log($"HARVEST_PLAYTEST {(pass ? "PASS" : "FAIL")} {index:00} {name} {note}");
        }

        IEnumerator Wait(float seconds) { yield return new WaitForSeconds(seconds); }

        // --- the finger ----------------------------------------------------------------------------------------
        void Touch(TouchPhase phase, Vector2 at) => InputSystem.QueueStateEvent(finger, new TouchState { touchId = 1, phase = phase, position = at, pressure = 1 });

        IEnumerator Tap(Vector2 at) { Touch(TouchPhase.Began, at); yield return null; yield return null; Touch(TouchPhase.Stationary, at); yield return null; Touch(TouchPhase.Ended, at); yield return null; yield return null; }
        IEnumerator Tap(Component ui) => Tap(ScreenOf(ui));

        /// Press, move in a straight line over the given seconds, release.
        IEnumerator Drag(Vector2 from, Vector2 to, float seconds)
        {
            Touch(TouchPhase.Began, from); yield return null; yield return null;
            float t = 0;
            while (t < seconds) { t += Time.deltaTime; Touch(TouchPhase.Moved, Vector2.Lerp(from, to, Mathf.Clamp01(t / seconds))); yield return null; }
            Touch(TouchPhase.Moved, to); yield return null; yield return Wait(.08f);
            Touch(TouchPhase.Ended, to); yield return null; yield return null;
        }

        static Vector2 ScreenOf(Component ui) => RectTransformUtility.WorldToScreenPoint(null, ((RectTransform)ui.transform).TransformPoint(((RectTransform)ui.transform).rect.center));

        Vector2 PlantOnScreen(int i)
        {
            var p = field.Plants[i]; var cam = field.view != null ? field.view : Camera.main;
            return cam.WorldToScreenPoint(p.root.position + Vector3.up * .2f);
        }

        // --- run -----------------------------------------------------------------------------------------------
        IEnumerator Run()
        {
            yield return Wait(1.5f);
            t0 = Time.realtimeSinceStartup; nextFrame = t0; capturing = true;
            HarvestCarry.Reset(); HarvestCarry.Day = stall.day;
            Mark("start", field != null && stall != null && field.Plants.Count == 6, $"{field.fieldId}：6 株，原等級 {string.Join(" ", field.Plants.Select(p => p.original))}");
            yield return Shot("field");
            field.Begin(); yield return Wait(1f);

            // 1. Pull: a slow upward drag keeps the grade; plant 2 (a top herb) is yanked in 0.3 s and snaps to mid.
            float pullPx = field.pullPixels * 1.25f * UnityEngine.Screen.height / 1080f;
            var pulls = new[] { 1.3f, .3f, 1.2f, 1.25f, 1.4f, 1.2f };
            for (int i = 0; i < 6; i++)
            {
                var at = PlantOnScreen(i);
                var drag = StartCoroutine(Drag(at, at + field.PullDir(i) * pullPx, pulls[i]));   // along each herb's lean
                if (i == 0)
                {
                    // The root timer beside the herb: amber while the root holds, jade after 0.8 s.
                    yield return Wait(.45f);
                    Mark("pull_ring", field.RingShowing && !field.RingSafe, "按住 0.45 s：根計時圈未滿（琥珀色），草繃緊抖動、掉土");
                    yield return Shot("pull_ring");
                    yield return Wait(.5f);
                    Mark("pull_ring_safe", field.RingShowing && field.RingSafe, "按住 0.95 s：圈滿變綠「根鬆了，拉！」");
                    yield return Shot("pull_ring_safe");
                }
                yield return drag;
                yield return Wait(i == 1 ? .1f : .6f);
                var p = field.Plants[i];
                Mark($"pull_{i + 1}", p.pulled && p.grade == HarvestRules.PullGrade(p.original, pulls[i]),
                    $"{HarvestContent.Label(p.original)} → {HarvestContent.Label(p.grade)}，{p.seconds:0.00}s{(p.snapped ? "（斷根）" : "")}");
                if (i == 1) { yield return Shot("pull_snapped"); yield return Wait(.5f); }
            }
            yield return Wait(2.4f);   // sort opens 0.8 s after the last pull, then the camera moves for 1 s
            Mark("sieve_open", field.Stage == QingxiHarvestPanel.Phase.Sort && field.Plants.All(p => p.sortItem != null), "6 株躺在 MK02 竹篩上（3D 分揀台）");
            yield return Shot("sieve");

            // 2. Sort by dragging each herb into a tray. Herb 3 (low) is dropped on the mid tray on purpose.
            var bins = new[] { "mid", "mid", "mid", "mid", "top", "mid" };
            var order = new[] { 4, 0, 1, 3, 5 };
            foreach (var i in order) { yield return Drag(field.HerbScreen(i), field.TrayScreen(bins[i]), .5f); yield return Wait(.35f); }
            // The misplaced one by tap-then-tap, the other one-thumb way.
            yield return Tap(field.HerbScreen(2)); yield return Wait(.5f);
            Mark("inspect", field.Picked == 2, "拿起第 3 株細看（卡片列出看到的特徵）");
            yield return Shot("inspect");
            yield return Tap(field.TrayScreen("mid")); yield return Wait(.4f);
            Mark("sorted", field.Bins.SequenceEqual(bins), string.Join(" ", field.Bins.Select((b, i) => $"{HarvestContent.Label(field.Plants[i].grade)}→{(b == null ? "（沒放）" : HarvestContent.Label(b) + "捆")}")));
            yield return Shot("sorted");
            yield return Tap(field.TieButton); yield return Wait(.6f);
            Mark("harvest_completed", HarvestMarketEvents.Log.Any(e => e.name == HarvestMarketEvents.HarvestCompletedName) && HarvestCarry.Bundles.Count == 3,
                HarvestMarketEvents.Log.LastOrDefault(e => e.name == HarvestMarketEvents.HarvestCompletedName).json);

            // 3. To the stall.
            if (rig != null) yield return rig.MoveTo(1, 2.2f);
            yield return Wait(.6f);
            stall.Show(); yield return Wait(1f);
            Mark("stall_open", stall.Open && stall.Sell.Count == 3, string.Join("，", HarvestCarry.Bundles.Select(b => $"{HarvestContent.Label(b.bin)}捆 {b.grades.Count} 株")));
            yield return Shot("stall");
            yield return Tap(stall.ToggleButton(2)); yield return Wait(.6f);
            Mark("keep_one", stall.Sell.SequenceEqual(new[] { true, true, false }), "第三捆改成「留著」");
            yield return Shot("keep_one");
            yield return Tap(stall.WeighButton); yield return Wait(1.4f);   // view leaned in over the counter, bundles in the pan
            Mark("weighing", stall.Weighed && stall.Balancing, "鏡頭推近秤與櫃台，草藥捆落進秤盤；秤砣在內側，秤尾翹起");
            yield return Shot("weighing");
            // Drag the counterweight out past the balance point (the beam droops), then back onto it and let go.
            var past = stall.BalanceScreen + (stall.BalanceScreen - stall.WeightScreen) * .35f;
            yield return Drag(stall.WeightScreen, past, .7f);
            Touch(TouchPhase.Began, past); yield return null; yield return null;
            Touch(TouchPhase.Moved, past); yield return Wait(.25f);
            yield return Shot("weigh_droop");
            for (float t = 0; t < .5f; t += Time.deltaTime) { Touch(TouchPhase.Moved, Vector2.Lerp(past, stall.BalanceScreen, t / .5f)); yield return null; }
            Touch(TouchPhase.Moved, stall.BalanceScreen); yield return Wait(.15f);
            Touch(TouchPhase.Ended, stall.BalanceScreen); yield return null;
            yield return Wait(.3f);
            Mark("level_reading", stall.Balancing && !stall.AutoWeigh, "第一次手動秤：秤桿平，秤砣上的讀數定在 7 靈石，秤桿上標 2–12 秤星");
            yield return Shot("weigh_reading");
            float waitLevel = Time.time + 3; while (!stall.Balanced && Time.time < waitLevel) yield return null;
            Mark("balanced", stall.Balanced, "拖秤砣過頭（秤尾垂下）再收回平衡點，放手後秤桿平");
            yield return Wait(1.2f);
            yield return Shot("coins_flying");   // coin string landed, coins flying up into the count
            yield return Wait(1.1f); yield return Shot("coins_on_counter");
            float waitDone = Time.time + 12; while (stall.DoneButton == null && Time.time < waitDone) yield return null;
            var s = stall.Last;
            Mark("settled", s != null && s.totalCoins == 7 && s.lines.SequenceEqual(new[] { "mixed-lower", "demand-bonus", "thanks" }),
                s == null ? "no result" : $"得 {s.totalCoins}：{string.Join("、", s.bundles.Select(b => $"{HarvestContent.Label(b.bin)}捆 {(b.sold ? b.coins + "" : "留著")}"))}；攤主 {string.Join("／", s.lines)}");
            yield return Shot("keeper");
            yield return Tap(stall.DoneButton); yield return Wait(.6f);
            var sold = HarvestMarketEvents.Log.LastOrDefault(e => e.name == HarvestMarketEvents.MarketSoldName).json;
            Mark("market_sold", sold != null && sold.Contains("\"totalCoins\":7") && !stall.Open, sold);
            Mark("kept_in_bag", HarvestCarry.Kept.TryGetValue("mid", out var mid) && mid == 2 && HarvestCarry.Coins == 7, $"留下 中品 {mid} 株；身上 {HarvestCarry.Coins} 靈石");

            // 4. A later sale weighs itself: no touch at all after 秤, the counterweight slides to its reading.
            yield return Wait(.8f);
            HarvestCarry.Bundles = HarvestRules.BundleUp(new[] { "mid", "mid" }, new[] { "mid", "mid" });
            stall.Show(); yield return Wait(1f);
            yield return Tap(stall.WeighButton);
            float autoFrom = Time.time, autoUntil = Time.time + 8;
            while (!stall.Balanced && Time.time < autoUntil) yield return null;
            Mark("auto_weigh", stall.AutoWeigh && stall.Balanced && stall.Last.totalCoins == 4, $"第二次賣（2 株中品）：按秤後不碰，{Time.time - autoFrom:0.0} s 自己秤平，得 {stall.Last?.totalCoins}");
            yield return Wait(.3f); yield return Shot("auto_weigh");
            waitDone = Time.time + 12; while (stall.DoneButton == null && Time.time < waitDone) yield return null;
            yield return Tap(stall.DoneButton); yield return Wait(1f);
            capturing = false; yield return Wait(.3f);
            report.frames = frame; report.pass = report.steps.All(x => x.pass);
            File.WriteAllText(Path.Combine(outDir, "harvest-playtest.json"), JsonUtility.ToJson(report, true));
            Debug.Log("HARVEST_PLAYTEST_DONE pass=" + report.pass + " frames=" + frame);
            Application.Quit(report.pass ? 0 : 1);
        }
    }
}
