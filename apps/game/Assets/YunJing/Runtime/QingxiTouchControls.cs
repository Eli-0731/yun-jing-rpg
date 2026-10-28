using QingxiWorld;
using UnityEngine;
using UnityEngine.InputSystem;

namespace YunJing
{
    // On-screen controls for phones and the browser (PWA): a joystick on the lower left, drag on the right
    // half to look, and buttons for jump, run, F (interact) and E (secondary). Inside Johnnnny0823's forest
    // encounter it also shows attack, technique, block (hold), dodge and return. Multi-touch through the Input
    // System touchscreen; with a mouse it can be forced on with ?touch in the URL or the T key.
    public sealed class QingxiTouchControls : MonoBehaviour
    {
        public static bool Active { get; private set; }
        public QingxiForestEncounter forest;
        public QingxiTrainingPractice training;
        public float lookSensitivity = .18f;

        const float StickRadius = 70f;
        int stickTouch = -1, lookTouch = -1;
        Vector2 stickOrigin, stickNow, lookLast;
        bool forcedOn, mouseDown;
        Vector2 mouseLast;

        struct Button { public string label; public Rect rect; public System.Action press; public bool hold; }

        void Start()
        {
            forcedOn = Application.absoluteURL.Contains("touch") || Application.isMobilePlatform;
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

        Button[] Buttons()
        {
            float w = GuiW, h = GuiH;
            var list = new System.Collections.Generic.List<Button> {
                new Button { label = "互動 F", rect = new Rect(w - 130, h - 250, 110, 70), press = () => QingxiFirstPerson.VirtualInteract = true },
                new Button { label = "跳", rect = new Rect(w - 130, h - 170, 110, 70), press = () => QingxiFirstPerson.VirtualJump = true },
                new Button { label = "跑", rect = new Rect(w - 250, h - 170, 110, 70), hold = true },
                new Button { label = "E", rect = new Rect(w - 250, h - 250, 110, 70), press = () => QingxiFirstPerson.VirtualSecondary = true },
            };
            if (InForest)
            {
                list.Add(new Button { label = "攻擊", rect = new Rect(w - 370, h - 170, 110, 70), press = () => QingxiForestEncounter.VirtualAttack = true });
                list.Add(new Button { label = "試招", rect = new Rect(w - 370, h - 250, 110, 70), press = () => QingxiForestEncounter.VirtualTechnique = true });
                list.Add(new Button { label = "格擋", rect = new Rect(w - 490, h - 170, 110, 70), hold = true });
                list.Add(new Button { label = "閃避", rect = new Rect(w - 490, h - 250, 110, 70), press = () => QingxiForestEncounter.VirtualDodge = true });
                list.Add(new Button { label = "回安全點", rect = new Rect(w - 250, h - 330, 230, 60), press = () => QingxiForestEncounter.VirtualReturn = true });
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
                        if (b.rect.Contains(gui)) { onButton = true; b.press?.Invoke(); }
                    if (onButton) continue;
                    if (gui.x < GuiW * .45f && gui.y > GuiH * .35f && stickTouch == -1) { stickTouch = id; stickOrigin = gui; stickNow = gui; }
                    else if (lookTouch == -1) { lookTouch = id; lookLast = gui; }
                    continue;
                }
                foreach (var b in buttons)
                    if (b.hold && b.rect.Contains(gui) && !ended) { if (b.label == "跑") run = true; else block = true; }
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

        void OnGUI()
        {
            QingxiFonts.ApplyImgui();
            if (!Active) return;
            var previous = GUI.matrix;
            GUI.matrix = Matrix4x4.Scale(Vector3.one * Scale);
            var old = GUI.color;
            GUI.color = new Color(1, 1, 1, .55f);
            var origin = stickTouch == -1 ? new Vector2(140, GuiH - 140) : stickOrigin;
            GUI.Box(new Rect(origin.x - StickRadius, origin.y - StickRadius, StickRadius * 2, StickRadius * 2), "");
            var knob = stickTouch == -1 ? origin : origin + Vector2.ClampMagnitude(stickNow - stickOrigin, StickRadius);
            GUI.Box(new Rect(knob.x - 28, knob.y - 28, 56, 56), "移動");
            foreach (var b in Buttons()) GUI.Box(b.rect, "\n" + b.label);
            GUI.color = old;
            GUI.matrix = previous;
        }
    }
}
