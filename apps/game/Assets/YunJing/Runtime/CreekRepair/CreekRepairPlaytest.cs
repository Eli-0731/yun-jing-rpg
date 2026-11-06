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

namespace YunJing.CreekRepair
{
    // Scripted player for the creek test scene (-creekPlaytest -creekMethod clear_silt -creekParty 1 -creekOut dir). Drives a virtual
    // touchscreen, so each dig, tap and wheel turn goes through the same input path a thumb does. Frames for the recording are JPGs.
    public sealed class CreekRepairPlaytest : MonoBehaviour
    {
        [Serializable] class Step { public int index; public string name; public bool pass; public string note; public float seconds; public string shot; }
        [Serializable] class Report { public string started, method, resolution, input; public int party, frames; public bool pass; public float frameEvery, totalSeconds, frameMsMedian, frameMsP95; public List<Step> steps = new List<Step>(); public List<string> events = new List<string>(); }

        public CreekRepairDirector director;
        string outDir; readonly Report report = new Report(); float t0, nextFrame; int index, frame; bool capturing; Touchscreen finger;

        static string Arg(string name)
        {
            var args = Environment.GetCommandLineArgs(); int i = Array.IndexOf(args, name);
            return i >= 0 && i + 1 < args.Length ? args[i + 1] : null;
        }

        void Start()
        {
            if (!Environment.GetCommandLineArgs().Contains("-creekPlaytest")) { enabled = false; return; }
            Application.runInBackground = true; InputSystem.settings.backgroundBehavior = InputSettings.BackgroundBehavior.IgnoreFocus; QualitySettings.vSyncCount = 0; Application.targetFrameRate = 60;
            report.method = Arg("-creekMethod") ?? "clear_silt"; report.party = int.TryParse(Arg("-creekParty"), out var p) ? p : 1;
            outDir = Arg("-creekOut") ?? Path.Combine(Application.persistentDataPath, "creek-playtest");
            Directory.CreateDirectory(Path.Combine(outDir, "frames"));
            report.frameEvery = float.TryParse(Arg("-creekFrameEvery"), out var every) ? every : .1f;
            report.started = DateTime.Now.ToString("s"); report.resolution = Screen.width + "x" + Screen.height; report.input = "virtual Input System Touchscreen (one finger)";
            CreekRepairEvents.Emitted += (n, j) => report.events.Add(n + " " + j);
            finger = InputSystem.AddDevice<Touchscreen>("PlaytestFinger");
            if (File.Exists(CreekRepairDirector.SavePath)) File.Delete(CreekRepairDirector.SavePath);
            StartCoroutine(Run());
        }

        void LateUpdate() { if (capturing && Time.realtimeSinceStartup >= nextFrame) { nextFrame += report.frameEvery; StartCoroutine(Save(Path.Combine("frames", $"f{frame++:00000}.jpg"))); } }

        IEnumerator Save(string file)
        {
            yield return new WaitForEndOfFrame();
            var tex = new Texture2D(Screen.width, Screen.height, TextureFormat.RGB24, false);
            tex.ReadPixels(new Rect(0, 0, Screen.width, Screen.height), 0, 0); tex.Apply();
            File.WriteAllBytes(Path.Combine(outDir, file), tex.EncodeToJPG(88)); Destroy(tex);
        }

        IEnumerator Shot(string name) { var file = $"{index:00}_{name}.jpg"; report.steps[report.steps.Count - 1].shot = file; yield return Save(file); }

        void OnEnable() => Application.logMessageReceived += OnLog;
        void OnDisable() => Application.logMessageReceived -= OnLog;
        void OnLog(string message, string stack, LogType type)
        {
            if (type != LogType.Exception) return;
            Debug.Log("CREEK_PLAYTEST ABORT " + message);
            Application.Quit(3);
        }

        readonly List<float> frameMs = new List<float>();
        void Update() => frameMs.Add(Time.unscaledDeltaTime * 1000);

        void Mark(string name, bool pass, string note = "")
        {
            report.steps.Add(new Step { index = ++index, name = name, pass = pass, note = note, seconds = Time.realtimeSinceStartup - t0 });
            Debug.Log($"CREEK_PLAYTEST {(pass ? "PASS" : "FAIL")} {index:00} {name} {note}");
        }

        IEnumerator Wait(float seconds) { yield return new WaitForSeconds(seconds); }

        void Touch(TouchPhase phase, Vector2 at) => InputSystem.QueueStateEvent(finger, new TouchState { touchId = 1, phase = phase, position = at, pressure = 1 });
        IEnumerator Tap(Vector2 at) { Touch(TouchPhase.Began, at); yield return null; yield return null; Touch(TouchPhase.Stationary, at); yield return null; Touch(TouchPhase.Ended, at); yield return null; yield return null; }
        static Vector2 ScreenOf(Component ui) => RectTransformUtility.WorldToScreenPoint(null, ((RectTransform)ui.transform).TransformPoint(((RectTransform)ui.transform).rect.center));

        /// Press on a pile, `offset` from its middle, and push the mud `meters` along `way` over `seconds`; the camera may be moving, so the world target is reprojected.
        IEnumerator Dig(string pile, float meters, float seconds, Vector2 offset = default, Vector2 way = default)
        {
            if (way == default) way = new Vector2(.92f, .38f);
            yield return StepUp(pile);
            if (offset == default) offset = director.PileStand(pile) * -.15f;   // the thumb lands short of where it aims, seen from the near side: aim past the middle, clear of the near cracks
            var from = director.PileWorld(pile) + new Vector3(offset.x, .2f, offset.y); from.y = Mathf.Max(director.PileSurface(pile, from), .1f); var to = from + new Vector3(meters * way.x, 0, meters * way.y);
            Touch(TouchPhase.Began, director.WorldScreen(from)); yield return null; yield return null;
            float t = 0;
            while (t < seconds) { t += Time.deltaTime; Touch(TouchPhase.Moved, director.WorldScreen(Vector3.Lerp(from, to, Mathf.Clamp01(t / seconds)))); yield return null; }
            Touch(TouchPhase.Moved, director.WorldScreen(to)); yield return null;
            Touch(TouchPhase.Ended, director.WorldScreen(to)); yield return null; yield return null;
        }

        /// A tap on the pile steps up to it, first person; a tap on 起身 steps back.
        IEnumerator StepUp(string pile)
        {
            if (director.DiggingPile(pile)) yield break;
            yield return StepBack();
            yield return Tap(director.PileScreen(pile)); yield return Wait(.95f);
            if (!firstPersonChecked) { firstPersonChecked = true; Mark("first_person_in", director.FirstPersonNow && director.DiggingPile(pile), "點泥堆，鏡頭切到第一視角"); yield return Shot("first_person_" + pile); }
        }

        IEnumerator StepBack()
        {
            if (!director.Digging) yield break;
            yield return Tap(ScreenOf(director.LeaveButton)); yield return Wait(.9f);
            if (!stepBackChecked) { stepBackChecked = true; Mark("first_person_out", !director.Digging, "按起身，鏡頭拉回"); }
        }

        bool firstPersonChecked, stepBackChecked;

        /// One real stroke: the thumb goes down at `from` and drags to `to` over `seconds`, then waits for the blade to come up behind it, or for the blade to be full. `lift` runs just before letting go.
        IEnumerator Stroke(string pile, Vector3 from, Vector3 to, float seconds, float fullAt = .92f, Func<IEnumerator> lift = null)
        {
            yield return StepUp(pile);
            Touch(TouchPhase.Began, director.WorldScreen(from)); yield return null;
            float wait = 0; while (!director.BladeIn && wait < .7f) { wait += Time.deltaTime; Touch(TouchPhase.Stationary, director.WorldScreen(from)); yield return null; }
            float t = 0; var at = from; float stuck = 0;
            while (stuck < 2.2f)
            {
                t += Time.deltaTime; at = Vector3.Lerp(from, to, Mathf.Clamp01(t / seconds)); Touch(TouchPhase.Moved, director.WorldScreen(at)); yield return null;
                if (t >= seconds) stuck += Time.deltaTime;
                if (director.BladeLoad >= fullAt || (t >= seconds && director.BladeLag < .03f)) break;
            }
            if (lift != null) { var inner = lift(); while (inner.MoveNext()) { Touch(TouchPhase.Moved, director.WorldScreen(at)); yield return inner.Current; } }
            Touch(TouchPhase.Ended, director.WorldScreen(at)); yield return null; yield return null;
        }

        /// A player's next stroke: into the deepest mud left, along the channel or outward off the heap.
        void NextStroke(CreekPile p, out Vector3 from, out Vector3 to)
        {
            var bed = director.Bed(p.id); var zone = director.BedZone(p.id); from = bed.Deepest(zone); var mid = new Vector3(zone.center.x, from.y, zone.center.y);
            var back = new Vector3(p.stand[0], 0, p.stand[1]).normalized;
            var flat = from - mid; flat.y = 0;
            var way = p.channelWidth > 0 ? back * (Vector3.Dot(flat, back) > 0 ? -1 : 1) : (flat.magnitude > .5f * zone.width / 2 ? -flat.normalized : flat.sqrMagnitude > .002f ? flat.normalized : back);   // near the rim: back across, there is no room to push on
            to = from + way * .85f;
        }

        /// The same drag, begun so the release lands on the 喲.
        IEnumerator DigOnBeat(string pile, float meters, float seconds, Vector2 offset = default, Vector2 way = default)
        {
            yield return StepUp(pile);
            while (director.NextYoIn < seconds + .06f || director.NextYoIn > seconds + .3f) yield return null;
            yield return Dig(pile, meters, seconds, offset, way);
        }

        /// Pulls the way this mud wants, at the speed it wants.
        IEnumerator DigProperly(CreekPile p, bool onBeat, Vector2 offset = default)
        {
            if (p.kind != "weed")
            {
                yield return StepUp(p.id);
                NextStroke(p, out var from, out var to);
                if (offset != default) { var hit = director.PileWorld(p.id) + new Vector3(offset.x, 0, offset.y); var through = (to - from).normalized; from = hit - through * .16f; from.y = director.PileSurface(p.id, from); to = hit + through * .5f; to.y = from.y; }
                yield return Stroke(p.id, from, to, .9f);
                yield break;
            }
            float meters = 1.05f, seconds = .8f;
            var way = new Vector2(p.pull[0], p.pull[1]);
            if (onBeat) yield return DigOnBeat(p.id, meters, seconds, offset, way); else yield return Dig(p.id, meters, seconds, offset, way);
        }

        /// Circles the wheel clockwise on screen.
        IEnumerator Spin(float degrees, float seconds)
        {
            float radius = 50 * Screen.height / 1080f, a = 90;
            Vector2 At() => director.WheelScreen + new Vector2(Mathf.Cos(a * Mathf.Deg2Rad), Mathf.Sin(a * Mathf.Deg2Rad)) * radius;
            Touch(TouchPhase.Began, At()); yield return null; yield return null;
            float t = 0, step = degrees / seconds;
            while (t < seconds) { t += Time.deltaTime; a -= step * Time.deltaTime; Touch(TouchPhase.Moved, At()); yield return null; }
            Touch(TouchPhase.Ended, At()); yield return null; yield return null;
        }

        static CreekContent content(CreekRepairSim sim) => sim.content;

        /// -creekLook: starts the method, finishes the work, and photographs named places from close, then quits. For checking joins by eye.
        IEnumerator Look()
        {
            director.Begin(report.method, report.party); var sim = director.Sim; yield return null;
            var m = sim.M;
            director.closeUp = true; yield return Wait(.5f);
            foreach (var p in m.piles)
            {
                var at = director.PileWorld(p.id) + Vector3.up * .25f; director.closeUpAt = at; director.closeUpFrom = at + new Vector3(.7f, 1.7f, -1.6f); yield return Wait(.25f);
                yield return Save("before_" + p.id + ".jpg"); yield return null;
            }
            director.closeUp = false;
            foreach (var j in m.piles)
            {
                director.EnterDig(j.id); yield return Wait(1f);
                yield return Save("fp_" + j.id + ".jpg"); yield return null;
                director.LeaveDig(); yield return Wait(.8f);
            }
            director.closeUp = true;
            foreach (var w in m.work) sim.Place(w.slot, w.piece);
            foreach (var p in m.patches) sim.Patch(p.slot, p.piece);
            if (m.HasAqueduct) sim.BuildAqueduct();
            foreach (var p in m.piles) while (sim.Left(p.id) > 0) sim.Scoop(p.id, 2, 1);
            director.SaveNow(); director.RestoreSaved(); sim = director.Sim; yield return Wait(.5f);
            director.closeUp = true;
            for (int wet = 0; wet < 2; wet++)
            {
                if (wet == 1)
                {
                    sim.TurnWheel(99999);
                    // the front part way round each bend, from straight above
                    for (int i = 0; i < 6 && !sim.CanalFull; i++)
                    {
                        sim.AdvanceFlow(i == 0 ? 42 : 11); yield return Wait(.3f);
                        var above = director.WaterHead; director.closeUpAt = above; director.closeUpFrom = above + new Vector3(.01f, 4.5f, -1.5f); yield return Wait(.25f);
                        yield return Save($"front_{i}.jpg"); yield return null;
                    }
                    while (!sim.CanalFull) sim.AdvanceFlow(1);
                    sim.SetGate("gate_a", 1); sim.SetGate("gate_c", .5); yield return Wait(2.6f);
                    for (int i = 0; i < 5; i++) { sim.AdvanceFlow(4); yield return Wait(.3f); director.closeUpAt = new Vector3(0, .2f, 11); director.closeUpFrom = director.closeUpAt + new Vector3(1.2f, 4.2f, -3.6f); yield return Wait(.25f); yield return Save($"fill_{i}.jpg"); yield return null; }
                }
                foreach (var (name, at, from) in new[] {
                    ("overview", new Vector3(0, .2f, 8), new Vector3(.01f, 11, -9)),
                    ("cross", new Vector3(0, .2f, 6.4f), new Vector3(.9f, 2, -2.1f)),
                    ("cross_top", new Vector3(0, .2f, 6.2f), new Vector3(.01f, 3.2f, -.01f)),
                    ("gate_middle", new Vector3(0, .3f, 8.25f), new Vector3(.9f, 1.3f, -1.9f)),
                    ("gate_west", new Vector3(-6, .3f, 8.25f), new Vector3(.9f, 1.3f, -1.9f)),
                    ("gate_east", new Vector3(6, .3f, 8.25f), new Vector3(-.9f, 1.3f, -1.9f)),
                    ("west_bend", new Vector3(-5.2f, .2f, 7.2f), new Vector3(1.2f, 1.9f, -2.2f)),
                    ("field_inlet", new Vector3(0, .2f, 9), new Vector3(.8f, 2, -2)),
                    ("ditch_top", new Vector3(1.9f, 0, 3.8f), new Vector3(.01f, 8f, -.01f)),
                    ("ditch_start", new Vector3(1.75f, .2f, 2f), new Vector3(1.2f, 1.8f, -2f)),
                    ("ditch_start_back", new Vector3(1.75f, .2f, 2f), new Vector3(-1.2f, 1.6f, 2f)),
                    ("ditch_end", new Vector3(1f, .2f, 5.6f), new Vector3(1.4f, 1.9f, -2f)) })
                {
                    director.closeUpAt = at; director.closeUpFrom = at + from; yield return Wait(.25f);
                    yield return Save((wet == 1 ? "wet_" : "dry_") + name + ".jpg"); yield return null;
                }
            }
            Application.Quit(0);
        }

        /// The recording's sound track, from the same clips the game plays and the times it played them.
        void WriteSound(float end)
        {
            float start = t0; var mix = new float[Mathf.CeilToInt((end - start) * CreekRepairSound.Rate)];
            var content = director.Sim.content; var chant = CreekRepairSound.Chant(content.chant.cycleSeconds, content.chant.yoAtSeconds, report.party);
            var clips = new Dictionary<string, float[]> { { "thud", CreekRepairSound.Thud() }, { "slump", CreekRepairSound.Slump() }, { "tick", CreekRepairSound.Tick() }, { "far_chant", CreekRepairSound.Chant(content.chant.cycleSeconds, content.chant.yoAtSeconds, 1) } };
            foreach (var kind in new[] { "soft", "hard", "weed" }) for (int t = 0; t < 3; t++) clips[$"dig_{kind}{t}"] = CreekRepairSound.Dig(kind, t);
            var press = CreekRepairSound.Press(); float pressAt = -1;
            float on = -1, runAt = -1, runGain = 0; var run = CreekRepairSound.Water();
            foreach (var s in director.Sounds)
            {
                if (s.name == "press_on") pressAt = s.at;
                else if (s.name == "press_off") { if (pressAt >= 0) LoopGain(mix, press, pressAt - start, Mathf.Min(s.at, pressAt + press.Length / (float)CreekRepairSound.Rate) - start, s.gain); pressAt = -1; }
                else if (s.name == "water") { if (runAt >= 0) LoopGain(mix, run, runAt - start, s.at - start, runGain); runAt = s.at; runGain = s.gain; }
                else if (s.name == "chant_on") { if (on >= 0) Loop(mix, chant, on - start, s.at - start, content.chant.cycleSeconds); on = s.at; }
                else if (s.name == "chant_off") { if (on >= 0) Loop(mix, chant, on - start, s.at - start, content.chant.cycleSeconds); on = -1; }
                else CreekRepairSound.Add(mix, clips[s.name], s.at - start, s.gain);
            }
            if (on >= 0) Loop(mix, chant, on - start, end - start, content.chant.cycleSeconds);
            if (runAt >= 0) LoopGain(mix, run, runAt - start, end - start, runGain);
            CreekRepairSound.WriteWav(Path.Combine(outDir, "sound.wav"), mix);
        }

        static void LoopGain(float[] mix, float[] run, double from, double to, float gain)
        {
            int at = (int)(from * CreekRepairSound.Rate), stop = Mathf.Min(mix.Length, (int)(to * CreekRepairSound.Rate));
            for (int i = at; i < stop; i++) mix[i] += run[(i - at) % run.Length] * gain;
        }

        static void Loop(float[] mix, float[] chant, double from, double to, float cycle) { for (double at = from; at < to; at += cycle) CreekRepairSound.Add(mix, chant, at, .68f); }

        IEnumerator PickCard(string slot, string piece)
        {
            yield return StepBack();
            while (!director.CameraSettled) yield return null;
            yield return Wait(.6f);
            yield return Tap(director.JobScreen(slot)); yield return Wait(.5f);
            if (!director.CardsOpen) { Mark("cards_open_" + slot, false, "點了沒開"); yield break; }
            yield return Wait(.7f);
            yield return Tap(ScreenOf(director.CardFor(piece))); yield return Wait(.4f);
        }

        /// A run that has stopped getting anywhere must end, not keep filling the disk with frames.
        IEnumerator Watchdog()
        {
            yield return new WaitForSecondsRealtime(630);
            Debug.Log("CREEK_PLAYTEST ABORT still running after 630 s, last step: " + report.steps.LastOrDefault()?.name);
            Application.Quit(4);
        }

        // ---- run ---------------------------------------------------------------------------------------------------
        IEnumerator Run()
        {
            StartCoroutine(Watchdog());
            yield return Wait(1.2f);
            if (Environment.GetCommandLineArgs().Contains("-creekLook")) { yield return Look(); yield break; }
            t0 = Time.realtimeSinceStartup; nextFrame = t0; capturing = true;
            yield return Wait(1f);
            Mark("picker", director.Picking, "測試入口：三個修法");
            yield return Shot("picker");
            yield return Tap(ScreenOf(director.PickerButtons.First(b => b.name == "Pick_" + report.method)));
            yield return Wait(.5f);
            if (report.party != 1) director.Begin(report.method, report.party);
            var sim = director.Sim; var m = sim.M;
            Mark("begin", sim != null && sim.s.method == report.method && !director.Picking, $"{m.label}，{report.party} 人，淤泥 {sim.SiltLeft}，接渠 {m.work.Length} 段");
            yield return Wait(2.5f);
            yield return Shot("site");

            // 1. The wheel before the work: refused with a reason, never a failure.
            yield return Spin(60, .6f); yield return Wait(.4f);
            Mark("wheel_refused", director.LastCode == "WORK_PENDING" && sim.s.wheelDegrees == 0, director.LastMessage);
            yield return Shot("wheel_refused"); yield return Wait(2.2f);

            // 2. Mud is heavy, and the blade shows it: a touch moves nothing, a long drag slows as the bow grows, and letting go heaves it out.
            var first = m.piles[0].id; var firstPile = m.piles[0]; double left = sim.Left(first);
            yield return Wait(1f); Mark("chant_playing", director.ChantPlaying, "號子開始");
            yield return StepUp(first); var bed1 = director.Bed(first); var spoil1 = director.Spoil(first); float volume0 = bed1.Volume();
            Mark("mud_fills_channel", volume0 > .02f && bed1.StartVolume == volume0, $"整段渠道的淤泥 {volume0 * 1000:0} 公升");
            Mark("mud_on_screen", bed1.go.GetComponent<Renderer>().enabled && bed1.go.activeInHierarchy, $"泥床有畫出來；挖掘時讓開 {director.HiddenWhileDigging} 件高過渠道的東西"); yield return Shot("mud_before");
            NextStroke(firstPile, out var a1, out var a2); var touch = Vector3.Lerp(a1, a2, .04f);
            yield return Stroke(first, a1, touch, .12f); yield return Wait(.5f);
            Mark("light_touch", left - sim.Left(first) < .25, $"輕輕碰一下只動一點點（{left - sim.Left(first):0.00}），也沒有失敗訊息"); left = sim.Left(first); yield return Shot("light_touch"); yield return Wait(.8f);
            NextStroke(firstPile, out a1, out a2);
            float early = 0, lateSum = 0, peak = 0; int lateN = 0; bool shotBow = false, wasIn = false;
            IEnumerator Watch() { while (director.Bed(first) != null) { if (director.BladeIn && wasIn) { float l = director.BladeLoad, v = director.BladeSpeed; peak = Mathf.Max(peak, l); if (l < .3f) early = Mathf.Max(early, v); if (l > .45f && v > .001f) { lateSum += v; lateN++; } if (l > .5f && !shotBow) { shotBow = true; yield return Shot("bow_on_blade"); } } wasIn = director.BladeIn; yield return null; } }
            var watching = StartCoroutine(Watch());
            yield return Stroke(first, a1, a2, .9f); yield return Wait(.05f);
            Mark("heaved_out", sim.Left(first) < left, $"放手甩走 {left - sim.Left(first):0.00}，這堆剩 {sim.Left(first):0.00}"); yield return Shot("heave"); yield return Wait(.8f);
            Mark("spoil_grows", spoil1.Volume() > 0, $"渠外泥堆 {spoil1.Volume() * 1000:0.0} 公升"); yield return Shot("spoil_heap");
            Mark("mud_conserved", Mathf.Abs(bed1.Volume() + bed1.Removed - volume0) < volume0 * .005f, $"床上 {bed1.Volume() * 1000:0.0} ＋搬走 {bed1.Removed * 1000:0.0} ＝原本 {volume0 * 1000:0.0} 公升"); yield return Wait(.8f);

            // 3. A wrong piece: says by how many cm and is not kept.
            var w0 = m.work[0]; var wrong = w0.options.Where(o => o.piece != w0.piece).OrderByDescending(o => o.gapCm).First();
            yield return PickCard(w0.slot, wrong.piece); yield return Wait(.4f);
            Mark("wrong_piece", director.LastCode == "MISALIGNED" && sim.Placed(w0.slot) == null && director.LastMessage.Contains($"差 {wrong.gapCm} cm"), director.LastMessage);
            yield return Shot("wrong_piece"); yield return Wait(3.4f);
            yield return PickCard(w0.slot, w0.piece); yield return Wait(.9f);
            Mark("right_piece", sim.Placed(w0.slot) == w0.piece, director.LastMessage);
            yield return Shot("right_piece");

            // 4. Dig the rest, joining as the player walks along, in an order of their own: work goes between the piles.
            int nextWork = 1, count = 0; bool beatChecked = false, stonesChecked = false;
            for (int i = 0; i < m.piles.Length; i++)
            {
                var id = m.piles[i].id; var pile = m.piles[i];
                if (pile.kind == "hard")
                {
                    yield return StepUp(id); NextStroke(pile, out var h1, out var h2); float fastest = 0;
                    bool hardIn = false; IEnumerator WatchHard() { while (true) { if (director.BladeIn && hardIn) fastest = Mathf.Max(fastest, director.BladeSpeed); hardIn = director.BladeIn; yield return null; } }
                    var w = StartCoroutine(WatchHard()); yield return Stroke(id, h1, h2, .9f); StopCoroutine(w); yield return Wait(.4f);
                    Mark("hard_is_slower", fastest > 0 && fastest <= sim.Mud("hard").bladeSpeedMps * 1.31f && fastest < early, $"硬泥最快 {fastest:0.00} m/s，軟泥 {early:0.00} m/s"); yield return Shot("hard_" + id); yield return Wait(1f);
                }
                if (pile.kind == "weed")
                {
                    yield return Dig(id, 1.05f, .8f, default, new Vector2(-pile.pull[0], -pile.pull[1])); yield return Wait(.4f);
                    Mark("weed_wrong_way", director.LastCode == "TANGLED" && director.LastStep.moved > 0, director.LastMessage); yield return Shot("weed_" + id); yield return Wait(1f);
                }
                if (pile.spots.Length > 0) { yield return Wait(1.6f); yield return Shot("crack_" + id); }
                if (!beatChecked && pile.kind != "weed" && sim.Left(id) > 2)
                {
                    // the full blade waits for the 喲, the way a crew does
                    yield return StepUp(id); NextStroke(pile, out var b1, out var b2);
                    IEnumerator Yo() { while (director.NextYoIn > .06f) yield return null; }
                    yield return Stroke(id, b1, b2, .9f, .6f, Yo); yield return Wait(.2f); beatChecked = true;
                    Mark("on_the_beat", director.LastStep.onBeat, $"喲的時候放手，這一鏟 {director.LastStep.moved:0.##}"); yield return Shot("on_beat"); yield return Wait(6); yield return Shot("cut_seeping");
                }
                foreach (var spot in pile.spots)
                {
                    if (sim.Spent(id, spot)) continue;
                    yield return DigProperly(pile, false, new Vector2(spot.pos[0], spot.pos[1])); yield return Wait(.3f);
                    Mark("slump_" + id + "_" + spot.id, sim.Spent(id, spot), $"鏟子拖過裂縫，{director.LastMessage}"); yield return Shot("slump_" + id + "_" + spot.id); yield return Wait(1.3f);
                    count++;
                }
                while (sim.Left(id) > 0)
                {
                    yield return DigProperly(pile, true); yield return Wait(.12f); count++;
                    if (!stonesChecked && director.Bed(id) != null && director.StonesClear(id) > 0)
                    {
                        // nobody places them: the mud coming off is what shows them, so some are out while the pile is still there
                        stonesChecked = true; Mark("stones_show", sim.Left(id) > 0, $"還剩 {sim.Left(id):0.0} 的泥時，泥退開露出 {director.StonesClear(id)} 塊舊石"); yield return Shot("stones_show");
                    }
                }
                if (i == 0) { StopCoroutine(watching); float late = lateN > 0 ? lateSum / lateN : 0; Mark("spade_probe_live", director.ProbeSees(new Vector3(0, .25f, 1.2f), new Vector3(0, .25f, 0)) && director.ProbeSees(new Vector3(.1f, .6f, 1.2f), new Vector3(.1f, -.5f, 1.2f)), "穿模探針看得到閘板，也看得到接上的渠底"); Mark("spade_clear", director.SpadeGap >= 0 && director.SpadeBuried < .02f && director.SpadeHits.Count == 0, $"鏟子離渠牆最近 {director.SpadeGap * 100:0.0} cm，柄埋進泥最深 {director.SpadeBuried * 100:0.0} cm，穿過：{string.Join(",", director.SpadeHits)}"); Mark("gets_heavy", peak > .45f && late > 0 && late < early * .75f, $"空鏟 {early:0.00} m/s → 堆滿 {late:0.00} m/s（鏟前泥 {peak:0.00}）"); yield return Wait(1f); Mark("pile_cleared", sim.Left(id) <= 0 && director.Bed(id).Volume() < director.Bed(id).StartVolume * .1f, $"床上剩 {director.Bed(id).Volume() * 1000:0.0} 公升"); yield return Shot("pile_clear"); }
                yield return Wait(.9f);
                if (nextWork < m.work.Length)
                {
                    var w = m.work[nextWork++];
                    yield return PickCard(w.slot, w.piece); yield return Wait(1f);
                    Mark("joined_" + w.slot, sim.Placed(w.slot) == w.piece, w.name);
                    yield return Shot("joined_" + w.slot);
                }
                if (i == 0)
                {
                    // Save and reload in the middle of the work.
                    director.SaveNow(); string before = sim.Save();
                    director.RestoreSaved(); sim = director.Sim; yield return Wait(1f);
                    Mark("save_restore", sim.Save() == before, $"存檔重開後淤泥 {sim.SiltLeft}，接渠還有 {sim.WorkLeft} 段");
                    yield return Shot("restored");
                }
            }
            while (nextWork < m.work.Length)
            {
                var w = m.work[nextWork++]; yield return PickCard(w.slot, w.piece); yield return Wait(1f);
                Mark("joined_" + w.slot, sim.Placed(w.slot) == w.piece, w.name); yield return Shot("joined_" + w.slot);
            }
            foreach (var p in m.patches)
            {
                yield return PickCard(p.slot, p.wrong); yield return Wait(.3f);
                Mark("wrong_patch", director.LastCode == "WRONG_PATCH" && sim.Patched(p.slot) == null, director.LastMessage);
                yield return Shot("wrong_patch"); yield return Wait(3f);
                yield return PickCard(p.slot, p.piece); yield return Wait(1f);
                Mark("patched", sim.Patched(p.slot) == p.piece, director.LastMessage); yield return Shot("patched");
            }
            if (m.HasAqueduct)
            {
                yield return StepBack(); yield return Wait(1.6f);
                yield return Tap(director.JobScreen("aqueduct")); yield return Wait(1.6f);
                Mark("aqueduct", sim.s.aqueduct, director.LastMessage); yield return Shot("aqueduct");
            }
            Mark("chant_stops", !director.ChantPlaying && sim.SiltLeft <= 0, "清完淤泥，號子停");
            Mark("work_completed", sim.WorkDone && report.events.Count(e => e.StartsWith(CreekRepairEvents.WorkCompleted)) == 1, report.events.LastOrDefault(e => e.StartsWith(CreekRepairEvents.WorkCompleted)));
            yield return Wait(3f);
            yield return Shot("work_done");

            Mark("dry_before_gate", !sim.GateOpen && director.WaterShowing == 0, $"開閘前水面 {director.WaterShowing} 個");

            // 5. The sign and the gates, before any water.
            yield return StepBack(); yield return Wait(1.5f);
            yield return Tap(ScreenOf(director.PlanChip)); yield return Wait(.5f);
            Mark("plan_sign", director.PlanOpen, "點分水牌，看三塊田各開多少"); yield return Shot("plan_sign"); yield return Wait(3f);
            yield return Tap(ScreenOf(director.PlanClose)); yield return Wait(.6f);
            var gates = content(sim).distribution.gates;
            IEnumerator Press(int i) { yield return Tap(ScreenOf(director.GateChip(i))); yield return Wait(.9f); }
            if (report.method == "clear_silt")
            {
                yield return Press(0); yield return Press(0); yield return Press(1); yield return Press(2);
                Mark("preset_plan", gates.All(g => sim.Gate(g.id).level == g.planLevel), "照牌子預先設好三個閘門");
            }
            else if (report.method == "protect_nursery")
            {
                yield return Press(1); yield return Press(1);
                Mark("preset_one", sim.Gate("gate_b").level == 1 && sim.Gate("gate_a").level == 0, "只先全開西田");
            }
            else Mark("preset_none", gates.All(g => sim.Gate(g.id).level == 0), "什麼都不設就放水");
            yield return Wait(1.5f); yield return Shot("gates_set");
            Mark("no_water_yet", sim.s.flowM == 0 && director.WaterShowing == 0, "設閘門時還沒有水");

            // 6. Open the main gate.
            yield return Tap(ScreenOf(director.ViewButton)); yield return Wait(2.2f);
            Mark("to_the_wheel", director.ViewingWheel, "鏡頭回到主閘輪");
            for (int i = 0; i < 4 && !sim.GateOpen; i++)
            {
                yield return Spin(200, 2.4f); yield return Wait(.25f);
                if (i == 1) { Mark("gate_half", sim.s.wheelDegrees > 0 && !sim.GateOpen, $"閘輪 {sim.s.wheelDegrees:0}°"); yield return Shot("gate_half"); }
            }
            Mark("gate_open", sim.GateOpen, director.LastMessage);
            yield return Wait(.5f); Mark("water_after_gate", director.WaterShowing > 0, $"開閘後水面 {director.WaterShowing} 個"); yield return Shot("gate_open");

            // 7. Follow the water, and change the gates while it runs.
            int shots = 0; bool changed = false, villagerSeen = false, canalShot = false;
            while (!sim.s.done && Time.realtimeSinceStartup - t0 < 720)
            {
                if (!canalShot && sim.CanalFull) { canalShot = true; Mark("canal_full", sim.s.flowM >= sim.RouteLength, "水到配水渠，閘門分水"); yield return Wait(1.5f); yield return Shot("canal_full"); }
                int wet = gates.Count(g => sim.s.reached.Contains(g.field));
                if (wet > shots) { shots = wet; Mark("field_wet_" + wet, true, sim.s.reached.Last()); yield return Wait(2f); yield return Shot("field_" + wet); }
                if (!villagerSeen && sim.s.gateLog.Any(g => g.by == "villager" && g.level > 0)) { villagerSeen = true; Mark("villager_gate", director.LastCode == "VILLAGER_GATE" || sim.s.gateLog.Count > 0, director.LastMessage); yield return Shot("villager_gate"); }
                if (!changed && report.method == "protect_nursery" && sim.Gate("gate_b").fill > .8)
                {
                    changed = true; double was = sim.Gate("gate_c").fill;
                    yield return Press(2); yield return Press(1); yield return Wait(1.5f);
                    Mark("change_mid_flow", sim.Gate("gate_b").level == 0 && sim.Gate("gate_c").level == .5 && sim.Gate("gate_c").fill > was, "放水中關西田、半開東田"); yield return Shot("change_mid_flow");
                }
                if (!changed && report.method == "restore_channel" && sim.Gate("gate_a").fill > .8)
                {
                    changed = true; double a0 = sim.Gate("gate_a").fill;
                    yield return Press(2); yield return Press(2);
                    Mark("share_water", sim.Gate("gate_c").level == 1 && sim.Gate("gate_a").fill > a0, "再開東田，水分成兩路"); yield return Wait(1); yield return Shot("share_water");
                }
                yield return null;
            }
            Mark("flow_completed", sim.s.done && report.events.Count(e => e.StartsWith(CreekRepairEvents.FlowCompleted)) == 1, report.events.LastOrDefault());
            if (report.method == "clear_silt") Mark("filled_together", sim.s.together, director.LastMessage);
            else Mark("filled_anyway", gates.All(g => sim.FieldFull(g.id)), director.LastMessage);
            if (report.method != "clear_silt") Mark("villager_helped", villagerSeen, "沒水可去時閘門自己提起");
            yield return Wait(6f);
            yield return Shot("end");
            var routes = report.events.Count(e => e.StartsWith(CreekRepairEvents.FlowReached));
            Mark("events_once", routes == m.route.Length + gates.Length, $"flowReached {routes} 次（路線 {m.route.Length} 節點＋{gates.Length} 塊田）");

            // 8. Close to the running water, so the recording shows it moving by itself.
            var channel = m.route.Where(n => n.kind != "canal").ToArray();
            var near = new[] { new Vector3(channel[Mathf.Min(2, channel.Length - 1)].pos[0], .28f, channel[Mathf.Min(2, channel.Length - 1)].pos[1]), new Vector3(0, .28f, 6.3f), new Vector3(0, .28f, 8.6f) };
            director.closeUp = true; director.closeUpGlide = true;
            for (int i = 0; i < near.Length; i++)
            {
                director.closeUpAt = near[i]; director.closeUpFrom = near[i] + (i == 2 ? new Vector3(1.2f, 1.7f, -1.6f) : new Vector3(.45f, .85f, -.8f));
                yield return Wait(5f);
                Mark("water_close_" + (i + 1), true); yield return Shot("water_close_" + (i + 1));
            }
            director.closeUp = false; director.closeUpGlide = false;

            capturing = false; yield return null; yield return null;
            WriteSound(Time.realtimeSinceStartup);
            Mark("spade_clear_all", director.SpadeGap >= 0 && director.SpadeBuried < .02f && director.SpadeHits.Count == 0, $"整趟：離渠牆最近 {director.SpadeGap * 100:0.0} cm，柄埋進泥最深 {director.SpadeBuried * 100:0.0} cm，穿過：{string.Join(",", director.SpadeHits)}");
            report.frames = frame; report.totalSeconds = Time.realtimeSinceStartup - t0; frameMs.Sort(); if (frameMs.Count > 0) { report.frameMsMedian = frameMs[frameMs.Count / 2]; report.frameMsP95 = frameMs[frameMs.Count * 95 / 100]; } report.pass = report.steps.All(s => s.pass);
            File.WriteAllText(Path.Combine(outDir, "creek-playtest.json"), JsonUtility.ToJson(report, true));
            Debug.Log($"CREEK_PLAYTEST_{(report.pass ? "PASS" : "FAIL")} {report.totalSeconds:0}s {frame} frames");
            Application.Quit(report.pass ? 0 : 1);
        }
    }
}
