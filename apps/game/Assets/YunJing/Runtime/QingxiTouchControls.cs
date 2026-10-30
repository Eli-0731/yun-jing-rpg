using QingxiWorld;
using UnityEngine;
using UnityEngine.InputSystem;

namespace YunJing
{
    // On-screen controls for phones and the browser (PWA), laid out per docs/art/ui-ux-direction-v1.md §3:
    // a floating jade joystick on the lower left (pushed to the rim = run), drag on the right half to look,
    // and an arc of round jade buttons on the lower right: the large main button interacts (what it does is
    // written on a label beside it), then jump, use (E) and hold-to-run. Inside Johnnnny0823's forest encounter
    // the arc becomes attack, dodge, technique and hold-to-block, with small interact and return buttons.
    // Multi-touch through the Input System touchscreen; with a mouse it can be forced on with ?touch or T.
    public sealed class QingxiTouchControls : MonoBehaviour
    {
        public static bool Active { get; private set; }
        public QingxiForestEncounter forest;
        public QingxiTrainingPractice training;
        public QingxiLocalForaging foraging;   // for the label beside the main button
        public float lookSensitivity = .18f;

        const float StickRadius = 74f;
        int stickTouch = -1, lookTouch = -1;
        Vector2 stickOrigin, stickNow, lookLast;
        bool forcedOn, mouseDown;
        Vector2 mouseLast;

        struct Button
        {
            public string label, key; public Vector2 centre; public float size; public System.Action press; public bool hold, main;
            public bool Hit(Vector2 p) => Vector2.Distance(p, centre) <= size * .5f + 6;   // round, with a little slack
        }

        System.Collections.IEnumerator Start()
        {
            string args = string.Join(" ", System.Environment.GetCommandLineArgs());
            forcedOn = Application.absoluteURL.Contains("touch") || Application.isMobilePlatform || args.Contains("--touch");
            if (!args.Contains("--ui-shot")) yield break;
            // Review hook: stand by the first hidden find (label and glint showing), save ui-shot.png, quit.
            yield return new WaitForSeconds(2f);
            var walker = QingxiFirstPerson.Current;
            var fortunes = QingxiFortunes.Current;
            if (walker != null && fortunes != null && fortunes.fortunes.Length > 0)
            {
                var cc = walker.GetComponent<CharacterController>();
                cc.enabled = false; walker.transform.position = fortunes.fortunes[0].position + Vector3.back * 1.2f + Vector3.up * .1f; cc.enabled = true;
            }
            yield return new WaitForSeconds(2.5f);
            yield return new WaitForEndOfFrame();
            var tex = new Texture2D(Screen.width, Screen.height, TextureFormat.RGB24, false);
            tex.ReadPixels(new Rect(0, 0, Screen.width, Screen.height), 0, 0); tex.Apply();
            System.IO.File.WriteAllBytes(System.IO.Path.Combine(System.IO.Path.GetDirectoryName(Application.dataPath), "ui-shot.png"), tex.EncodeToPNG());
            Application.Quit();
        }

        bool sawTouch;

        bool ShouldShow()
        {
            if (Keyboard.current != null && Keyboard.current.tKey.wasPressedThisFrame) forcedOn = !forcedOn;
            if (Touchscreen.current != null && Touchscreen.current.primaryTouch.press.isPressed) sawTouch = true;
            return forcedOn || sawTouch;
        }

        // GUI is drawn in a 720-high virtual space; convert a screen position (origin bottom-left) into it.
        float Scale => Mathf.Clamp(Screen.height / 720f, .7f, 2f);
        Vector2 ToGui(Vector2 screen) => new Vector2(screen.x / Scale, (Screen.height - screen.y) / Scale);
        float GuiW => Screen.width / Scale;
        float GuiH => Screen.height / Scale;

        bool InForest => forest != null && forest.PlayerInside && !forest.Climbed;

        // Sizes are in the 720-high GUI space: main 104, arc 76, small 56 (the 1080p spec x 2/3).
        Button[] Buttons()
        {
            float w = GuiW, h = GuiH;
            var main = new Vector2(w - 96, h - 96);
            var list = new System.Collections.Generic.List<Button>();
            if (InForest)
            {
                list.Add(new Button { label = "攻擊", key = "", centre = main, size = 104, main = true, press = () => QingxiForestEncounter.VirtualAttack = true });
                list.Add(new Button { label = "閃避", key = "", centre = main + new Vector2(-127, 6), size = 76, press = () => QingxiForestEncounter.VirtualDodge = true });
                list.Add(new Button { label = "試招", key = "", centre = main + new Vector2(-90, -90), size = 76, press = () => QingxiForestEncounter.VirtualTechnique = true });
                list.Add(new Button { label = "格擋", key = "按住", centre = main + new Vector2(0, -127), size = 76, hold = true });
                list.Add(new Button { label = "互動", key = "F", centre = new Vector2(w - 46, h - 262), size = 56, press = () => QingxiFirstPerson.VirtualInteract = true });
                list.Add(new Button { label = "回", key = "安全點", centre = new Vector2(w - 46, h - 330), size = 56, press = () => QingxiForestEncounter.VirtualReturn = true });
            }
            else
            {
                list.Add(new Button { label = "互動", key = "F", centre = main, size = 104, main = true, press = () => QingxiFirstPerson.VirtualInteract = true });
                list.Add(new Button { label = "跳", key = "", centre = main + new Vector2(-127, 6), size = 76, press = () => QingxiFirstPerson.VirtualJump = true });
                list.Add(new Button { label = "運用", key = "E", centre = main + new Vector2(-90, -90), size = 76, press = () => QingxiFirstPerson.VirtualSecondary = true });
                list.Add(new Button { label = "疾行", key = "按住", centre = main + new Vector2(0, -127), size = 76, hold = true });
            }
            return list.ToArray();
        }

        void Update()
        {
            bool practising = training != null && training.Active;
            Active = ShouldShow() && !practising;
            if (!Active) { Release(); return; }

            var buttons = Buttons();
            bool run = false, block = false;
            var pointers = new System.Collections.Generic.List<(int id, Vector2 pos, bool began, bool ended)>();
            if (Touchscreen.current != null)
                foreach (var t in Touchscreen.current.touches)
                {
                    var phase = t.phase.ReadValue();
                    if (phase == UnityEngine.InputSystem.TouchPhase.None) continue;
                    pointers.Add((t.touchId.ReadValue(), t.position.ReadValue(),
                        phase == UnityEngine.InputSystem.TouchPhase.Began,
                        phase == UnityEngine.InputSystem.TouchPhase.Ended || phase == UnityEngine.InputSystem.TouchPhase.Canceled));
                }
            // Mouse stands in for one finger when the controls were forced on in a desktop browser.
            if (pointers.Count == 0 && Mouse.current != null && (Mouse.current.leftButton.isPressed || mouseDown))
            {
                bool pressed = Mouse.current.leftButton.isPressed;
                pointers.Add((-99, Mouse.current.position.ReadValue(), pressed && !mouseDown, !pressed));
                mouseDown = pressed;
            }

            foreach (var (id, pos, began, ended) in pointers)
            {
                var gui = ToGui(pos);
                if (began)
                {
                    bool onButton = false;
                    foreach (var b in buttons)
                        if (b.Hit(gui)) { onButton = true; b.press?.Invoke(); pressed[b.label] = Time.time; }
                    if (onButton) continue;
                    if (gui.x < GuiW * .45f && gui.y > GuiH * .35f && stickTouch == -1) { stickTouch = id; stickOrigin = gui; stickNow = gui; }
                    else if (lookTouch == -1) { lookTouch = id; lookLast = gui; }
                    continue;
                }
                foreach (var b in buttons)
                    if (b.hold && b.Hit(gui) && !ended) { if (b.label == "疾行") run = true; else block = true; held[b.label] = Time.time; }
                if (id == stickTouch) { stickNow = gui; if (ended) stickTouch = -1; }
                if (id == lookTouch)
                {
                    var delta = gui - lookLast; lookLast = gui;
                    QingxiFirstPerson.VirtualLook += new Vector2(delta.x, delta.y) * lookSensitivity;
                    if (ended) lookTouch = -1;
                }
            }
            if (stickTouch != -1 && !pointers.Exists(p => p.id == stickTouch)) stickTouch = -1;
            if (lookTouch != -1 && !pointers.Exists(p => p.id == lookTouch)) lookTouch = -1;

            var offset = stickTouch == -1 ? Vector2.zero : Vector2.ClampMagnitude(stickNow - stickOrigin, StickRadius) / StickRadius;
            QingxiFirstPerson.VirtualMove = new Vector2(offset.x, -offset.y);   // GUI y grows downward
            QingxiFirstPerson.VirtualRun = run || offset.magnitude > .95f;
            QingxiForestEncounter.VirtualBlockHeld = block;
        }

        void Release()
        {
            stickTouch = lookTouch = -1;
            QingxiFirstPerson.VirtualMove = Vector2.zero;
            QingxiFirstPerson.VirtualRun = false;
            QingxiForestEncounter.VirtualBlockHeld = false;
        }

        void OnDisable() { Active = false; Release(); }

        readonly System.Collections.Generic.Dictionary<string, float> pressed = new System.Collections.Generic.Dictionary<string, float>(),
            held = new System.Collections.Generic.Dictionary<string, float>();
        GUIStyle labelStyle, keyStyle, tagStyle;

        void OnGUI()
        {
            QingxiFonts.ApplyImgui();
            if (!Active) return;
            if (labelStyle == null)
            {
                labelStyle = new GUIStyle { font = QingxiFonts.Title, fontStyle = FontStyle.Bold, alignment = TextAnchor.MiddleCenter, normal = { textColor = new Color(.06f, .15f, .13f) } };
                keyStyle = new GUIStyle { font = QingxiFonts.Ui, fontSize = 11, alignment = TextAnchor.MiddleCenter, normal = { textColor = new Color(.1f, .22f, .19f, .8f) } };
                tagStyle = new GUIStyle { font = QingxiFonts.Ui, fontSize = 17, alignment = TextAnchor.MiddleCenter, normal = { textColor = QingxiUiArt.Mist } };
            }
            var previous = GUI.matrix;
            GUI.matrix = Matrix4x4.Scale(Vector3.one * Scale);

            // Joystick: rests faintly at its home spot; while held it appears under the thumb, knob glowing at the rim.
            bool holding = stickTouch != -1;
            var origin = holding ? stickOrigin : new Vector2(110, GuiH - 110);
            var offset = holding ? Vector2.ClampMagnitude(stickNow - stickOrigin, StickRadius) : Vector2.zero;
            float alpha = holding ? .95f : .45f;
            QingxiUiArt.Draw(QingxiUiArt.Circle(origin, StickRadius * 2), QingxiUiArt.Soft, new Color(0, 0, 0, .25f * alpha));
            QingxiUiArt.Draw(QingxiUiArt.Circle(origin, StickRadius * 2), QingxiUiArt.Jade, new Color(1, 1, 1, .35f * alpha));
            QingxiUiArt.Draw(QingxiUiArt.Circle(origin, StickRadius * 2), QingxiUiArt.Ring, new Color(QingxiUiArt.Gold.r, QingxiUiArt.Gold.g, QingxiUiArt.Gold.b, .55f * alpha));
            if (offset.magnitude > StickRadius * .95f)
                QingxiUiArt.Draw(QingxiUiArt.Circle(origin + offset, 96), QingxiUiArt.Soft, new Color(QingxiUiArt.JadeGlow.r, QingxiUiArt.JadeGlow.g, QingxiUiArt.JadeGlow.b, .6f));
            QingxiUiArt.Draw(QingxiUiArt.Circle(origin + offset, 62), QingxiUiArt.Jade, new Color(1, 1, 1, alpha));

            // Buttons: jade discs; pressed ones shrink and brighten for 0.12 s, held ones glow.
            foreach (var b in Buttons())
            {
                bool down = (pressed.TryGetValue(b.label, out var at) && Time.time - at < .12f) || (held.TryGetValue(b.label, out var ht) && Time.time - ht < .1f);
                float size = b.size * (down ? .92f : 1);
                QingxiUiArt.Draw(QingxiUiArt.Circle(b.centre + new Vector2(0, 3), size + 8), QingxiUiArt.Soft, new Color(0, 0, 0, .35f));
                QingxiUiArt.Draw(QingxiUiArt.Circle(b.centre, size), QingxiUiArt.Jade, down ? new Color(1.15f, 1.15f, 1.15f, 1) : Color.white);
                if (down) QingxiUiArt.Draw(QingxiUiArt.Circle(b.centre, size * 1.35f), QingxiUiArt.Soft, new Color(QingxiUiArt.JadeGlow.r, QingxiUiArt.JadeGlow.g, QingxiUiArt.JadeGlow.b, .45f));
                labelStyle.fontSize = b.main ? 26 : b.size < 60 ? 15 : 20;
                GUI.Label(new Rect(b.centre.x - size / 2, b.centre.y - size / 2 - (b.key.Length > 0 ? 6 : 0), size, size), b.label, labelStyle);
                if (b.key.Length > 0) GUI.Label(new Rect(b.centre.x - size / 2, b.centre.y + size * .16f, size, 16), b.key, keyStyle);
            }

            // What the main button does right now, on a strip beside the arc (never over a button).
            var prompt = foraging != null && QingxiFirstPerson.Current != null ? foraging.Prompt(QingxiFirstPerson.Current.transform.position) : null;
            if (!string.IsNullOrEmpty(prompt) && prompt.StartsWith("F "))   // actions only, not the general guidance line
            {
                var text = prompt.StartsWith("F ") ? prompt.Substring(2) : prompt;
                float width = Mathf.Min(320, 36 + text.Length * 17);
                var r = new Rect(GuiW - 96 - 127 - 38 - 16 - width, GuiH - 96 - 20, width, 40);
                QingxiUiArt.Sliced(r, QingxiUiArt.Ink);
                GUI.Label(r, text, tagStyle);
            }
            GUI.matrix = previous;
        }
    }
}
