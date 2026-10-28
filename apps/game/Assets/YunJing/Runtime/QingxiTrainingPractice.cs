using QingxiWorld;
using UnityEngine;
using UnityEngine.InputSystem;
using Rules = YunJing.QingxiTrainingPracticeRules;

namespace YunJing
{
    // Johnnnny0823's two training-yard drills (tools/training-yard-demo) on his posts in the novice village:
    // F at the qi striking post starts 引氣呼吸, F at the agility post starts 武技格擋. Rules are the C# port
    // QingxiTrainingPracticeRules. Keyboard, mouse and on-screen (touch) buttons; Esc leaves. Local only:
    // the result card is feedback for this round and never becomes cultivation.
    public sealed class QingxiTrainingPractice : MonoBehaviour
    {
        const float Reach = 1.9f;
        public Transform qiPost, blockPost;
        public string qiLabel = "氣勁木樁";
        public QingxiFirstPerson walker;

        public Rules.BreathSession Breath { get; private set; }
        public Rules.BlockSession Block { get; private set; }
        public bool Active => Breath != null || Block != null;
        public string LastResult { get; private set; }

        double clock;
        bool touchHeld;
        string pendingTouchSide, flash;
        float flashUntil, resultUntil;

        static float Flat(Vector3 a, Vector3 b) => Vector2.Distance(new Vector2(a.x, a.z), new Vector2(b.x, b.z));

        public string Prompt(Vector3 position)
        {
            if (Active) return null;
            if (qiPost != null && Flat(position, qiPost.position) <= Reach) return $"F 引氣呼吸（{qiLabel}，Johnnnny0823 的練法）";
            if (blockPost != null && Flat(position, blockPost.position) <= Reach) return "F 武技格擋（身法木樁，Johnnnny0823）";
            return null;
        }

        public bool TryInteract(Vector3 position, out string message)
        {
            message = null;
            if (Active) return false;
            if (qiPost != null && Flat(position, qiPost.position) <= Reach) { StartQi(); message = "凝神：金圈擴張時按住，收回時放開"; return true; }
            if (blockPost != null && Flat(position, blockPost.position) <= Reach) { StartBlock(); message = "木臂蓄勢：光圈收到時按 A／S／D 格擋"; return true; }
            return false;
        }

        // Local practice has no birth record, so the spirit-root gate stays open here (the PWA shows the NO_ROOT case).
        public void StartQi() { End(); clock = 0; Breath = new Rules.BreathSession(true, 3, 0); Freeze(true); }
        public void StartBlock() { End(); clock = 0; Block = new Rules.BlockSession(7, 0); Freeze(true); }

        public void End()
        {
            Breath = null; Block = null; touchHeld = false; pendingTouchSide = null;
            Freeze(false);
        }

        public bool Frozen { get; private set; }

        // Same pause the travel journal uses: no walking or F/E while drilling, and the cursor is free
        // for the on-screen buttons. The walker stays enabled so QingxiFirstPerson.Current keeps working.
        void Freeze(bool on)
        {
            if (walker == null) walker = QingxiFirstPerson.Current;
            if (walker != null && Frozen != on) walker.SetMenuOpen(on);
            Frozen = on;
        }

        void Update()
        {
            if (!Active) return;
            var kb = Keyboard.current; var mouse = Mouse.current;
            if (kb != null && kb.escapeKey.wasPressedThisFrame) { LastResult = "中途收功"; resultUntil = Time.time + 2.5f; End(); return; }
            clock += Mathf.Min(Time.deltaTime, .1f);
            if (Breath != null)
            {
                bool held = touchHeld || (kb != null && kb.spaceKey.isPressed) || (mouse != null && mouse.leftButton.isPressed);
                Breath.SetHeld(held);
                Breath.Update(clock);
                if (Breath.done) Finish($"三息完成：{string.Join("、", System.Array.ConvertAll(Breath.FinishedScores, Rules.GradeBreath))}（{Breath.Harmonised}／3 調和）");
            }
            else if (Block != null)
            {
                string side = pendingTouchSide;
                pendingTouchSide = null;
                if (kb != null)
                {
                    if (kb.aKey.wasPressedThisFrame || kb.leftArrowKey.wasPressedThisFrame) side = "left";
                    if (kb.sKey.wasPressedThisFrame || kb.downArrowKey.wasPressedThisFrame) side = "low";
                    if (kb.dKey.wasPressedThisFrame || kb.rightArrowKey.wasPressedThisFrame) side = "right";
                }
                if (side != null)
                {
                    var judged = Block.Input(side, clock);
                    if (judged.HasValue) Flash(judged.Value.result == "perfect" ? "精準！" : judged.Value.result == "good" ? "擋住" : judged.Value.reason);
                }
                else
                {
                    int before = Block.results.Count;
                    Block.Update(clock);
                    if (Block.results.Count > before) Flash(Block.results[Block.results.Count - 1].reason);
                }
                if (Block.done) Finish($"{Block.Grade}：擋下 {Block.Blocked}／{Block.strikes.Count}，精準 {Block.Perfect}，最長連擋 {Block.bestCombo}");
            }
        }

        void Flash(string text) { flash = text; flashUntil = Time.time + .6f; }

        void Finish(string result) { LastResult = result; resultUntil = Time.time + 5f; End(); }

        void OnGUI()
        {
            QingxiFonts.ApplyImgui();
            float scale = Mathf.Clamp(Screen.height / 720f, .7f, 1.5f);
            var previous = GUI.matrix;
            GUI.matrix = Matrix4x4.Scale(Vector3.one * scale);
            float w = Screen.width / scale, h = Screen.height / scale;
            if (!Active)
            {
                if (LastResult != null && Time.time < resultUntil)
                    GUI.Box(new Rect(w / 2 - 230, h * .22f, 460, 54), LastResult + "\n" + Rules.Notice);
                GUI.matrix = previous;
                return;
            }
            var panel = new Rect(w / 2 - 240, h * .14f, 480, 150);
            GUI.Box(panel, Breath != null ? "引氣呼吸・氣勁木樁（Esc 收功）" : "武技格擋・身法木樁（Esc 收功）");
            if (Breath != null)
            {
                var g = Breath.CurrentGuide;
                string label = Breath.Elapsed < 0 ? "凝神" : g.label;
                GUI.Label(new Rect(panel.x + 16, panel.y + 26, 440, 22), $"第 {Mathf.Min(g.cycle + 1, Breath.cycles)}／{Breath.cycles} 息　{label}　同步 {Breath.Sync:P0}");
                Bar(new Rect(panel.x + 16, panel.y + 52, 448, 16), (float)Breath.GuideValue, new Color(.95f, .78f, .3f), "金圈");
                Bar(new Rect(panel.x + 16, panel.y + 74, 448, 16), (float)Breath.qi, new Color(.45f, .85f, .7f), "玉圈");
                GUI.Label(new Rect(panel.x + 16, panel.y + 96, 440, 22), "各息：" + string.Join("　", System.Array.ConvertAll(Breath.FinishedScores, Rules.GradeBreath)));
                // Touch: hold the button to draw qi in.
                var button = new Rect(w - 210, h - 190, 170, 150);
                var e = Event.current;
                if (e.type == EventType.MouseDown && button.Contains(e.mousePosition)) touchHeld = true;
                if (e.type == EventType.MouseUp) touchHeld = false;
                GUI.Box(button, touchHeld ? "\n\n\n引氣中" : "\n\n\n按住引氣");
            }
            else if (Block != null)
            {
                double t = Block.Elapsed;
                GUI.Label(new Rect(panel.x + 16, panel.y + 26, 440, 22), $"已判 {Block.results.Count}／{Block.strikes.Count}　連擋 {Block.combo}　散架 {Block.flinches}");
                int shown = 0;
                for (int i = Block.index; i < Block.strikes.Count && shown < 3; i++, shown++)
                {
                    var s = Block.strikes[i];
                    double eta = s.at - t;
                    // The ring closes on the key moment: full at 1.5 s out, empty when it arrives.
                    float closing = Mathf.Clamp01((float)(eta / 1.5));
                    Bar(new Rect(panel.x + 16, panel.y + 52 + shown * 22, 448, 16), 1 - closing, i == Block.index ? new Color(.95f, .45f, .3f) : new Color(.6f, .6f, .6f),
                        $"{Rules.SideLabel(s.side)}  {eta:0.0}s");
                }
                if (flash != null && Time.time < flashUntil) GUI.Label(new Rect(panel.x + 16, panel.y + 120, 440, 22), flash);
                // Touch: three block buttons, judged on press (not release) so timing stays fair.
                string[] sides = { "left", "low", "right" };
                for (int i = 0; i < 3; i++)
                {
                    var r = new Rect(w - 420 + i * 130, h - 130, 120, 90);
                    var e = Event.current;
                    if (e.type == EventType.MouseDown && r.Contains(e.mousePosition)) { pendingTouchSide = sides[i]; e.Use(); }
                    GUI.Box(r, "\n\n" + Rules.SideLabel(sides[i]) + "\n" + "ASD"[i]);
                }
            }
            GUI.matrix = previous;
        }

        static void Bar(Rect r, float value, Color color, string label)
        {
            GUI.Box(r, GUIContent.none);
            var old = GUI.color; GUI.color = color;
            GUI.DrawTexture(new Rect(r.x + 1, r.y + 1, (r.width - 2) * Mathf.Clamp01(value), r.height - 2), Texture2D.whiteTexture);
            GUI.color = old;
            GUI.Label(new Rect(r.x + 6, r.y - 2, r.width, r.height + 4), label);
        }
    }
}
