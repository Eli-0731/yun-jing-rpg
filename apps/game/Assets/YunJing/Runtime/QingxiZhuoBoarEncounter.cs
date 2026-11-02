using System;
using System.Collections.Generic;
using QingxiWorld;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.LowLevel;
using Rules = YunJing.QingxiZhuoBoarRules;

namespace YunJing
{
    // Day 3: the sick boar at the creek. Rules and numbers are QingxiZhuoBoarRules and packages/content/zhuo-boar-encounter-v1.json;
    // this drives the model and animations, reads keyboard and touch, moves the player for dodges and knockback, and draws the HUD.
    // Sits on the D3_BoarEncounter slot. The core team plays its scene, then calls BeginFromScript(); startOnNotice is for the
    // test scene. Nothing is sent to a server and nothing is granted here: Cleansed and Escaped are for the core team to act on.
    public sealed class QingxiZhuoBoarEncounter : MonoBehaviour
    {
        const string ContentPath = "QingxiZhuoBoar/zhuo-boar-encounter-v1";
        static readonly int ZhuoId = Shader.PropertyToID("_Zhuo");

        public static event Action<double, int> Cleansed;   // zhuoBoar.cleansed { durationSeconds, hitsTaken }
        public static event Action<int> Escaped;            // zhuoBoar.escaped { hitsTaken }
        public static event Action<double, double> StaminaLost;  // lost, left (never below the content's floor)

        public bool startOnNotice;
        public float staminaStart = 100;
        public Transform boarModel;    // from BR01; left empty, a 1.5 x 0.9 m capsule stands in
        public Animation clips;        // Idle, Paw, Charge, Daze, Cleanse, Flee
        public bool useBounds;
        public Vector2 boundsMin, boundsMax;

        public Rules.Encounter Rule { get; private set; }
        public Rules.Content Content { get; private set; }

        Transform body;
        Renderer[] renderers;
        MaterialPropertyBlock block;
        QingxiZhuoBoarFx fx;
        readonly List<Rules.Obstacle> obstacles = new List<Rules.Obstacle>();
        readonly Dictionary<string, BoarObstacle> byId = new Dictionary<string, BoarObstacle>();
        readonly Rules.Input input = new Rules.Input();
        double clock;
        float zhuoShown = 1, groundY, hitFlash;
        string clipNow, tipOverride;
        float tipUntil, bannerAt = -100;
        string bannerTop, bannerSub;

        // Player motion the rules asked for (dodge, knockback), spread over a moment.
        Vector3 pushLeft;
        float pushRate, savedWalk, savedRun, savedJump;
        bool pushing, holdingJump;

        public void BeginFromScript()
        {
            Prepare();
            if (Rule != null) Rule.Begin();
        }

        void Awake()
        {
            var text = Resources.Load<TextAsset>(ContentPath);
            if (text == null) { Debug.LogError(ContentPath + " missing"); enabled = false; return; }
            Content = JsonUtility.FromJson<Rules.Content>(text.text);
            fx = gameObject.AddComponent<QingxiZhuoBoarFx>();
            block = new MaterialPropertyBlock();
        }

        void Start()
        {
            Prepare();
            StartReviewHooks();
        }

        void Prepare()
        {
            if (Rule != null || Content == null) return;
            var p = transform.position;
            Rule = new Rules.Encounter(Content, p.x, p.z, transform.eulerAngles.y * Mathf.Deg2Rad, staminaStart, startOnNotice);
            body = boarModel != null ? boarModel : Capsule();
            renderers = body.GetComponentsInChildren<Renderer>();
            if (clips != null) foreach (AnimationState s in clips) s.wrapMode = s.name == "Cleanse" ? WrapMode.ClampForever : WrapMode.Loop;
            foreach (var slot in new[] { "D3_BoarTree_01", "D3_BoarTree_02", "D3_BoarTree_03" })
            {
                var tree = GameObject.Find(slot);
                if (tree != null && tree.GetComponent<BoarObstacle>() == null) tree.AddComponent<BoarObstacle>().leanDegrees = 8;
            }
            CollectObstacles();
            if (useBounds) input.bounds = new Rules.Bounds { minX = boundsMin.x, maxX = boundsMax.x, minZ = boundsMin.y, maxZ = boundsMax.y };
            input.obstacles = obstacles;
            groundY = Ground(p);
        }

        // The stand-in until BR01 is on the slot.
        Transform Capsule()
        {
            var go = GameObject.CreatePrimitive(PrimitiveType.Capsule);
            go.name = "BoarCapsule_1.5x0.9";
            Destroy(go.GetComponent<Collider>());
            go.transform.SetParent(transform, false);
            go.transform.localRotation = Quaternion.Euler(90, 0, 0);
            go.transform.localScale = new Vector3(.9f, .75f, .9f);
            var root = new GameObject("BoarStandIn").transform;
            root.SetParent(transform, false);
            go.transform.SetParent(root, false);
            go.transform.localPosition = Vector3.up * .45f;
            return root;
        }

        void CollectObstacles()
        {
            obstacles.Clear(); byId.Clear();
            int n = 0;
            foreach (var o in BoarObstacle.All)
            {
                var id = o.name + (byId.ContainsKey(o.name) ? "#" + ++n : "");
                byId[id] = o;
                obstacles.Add(new Rules.Obstacle { id = id, x = o.Centre.x, z = o.Centre.z, r = o.Radius });
            }
        }

        float Ground(Vector3 at)
        {
            var player = QingxiFirstPerson.Current;
            float best = float.NegativeInfinity;
            int count = Physics.RaycastNonAlloc(new Vector3(at.x, at.y + 3, at.z), Vector3.down, hitsBuffer, 12, ~0, QueryTriggerInteraction.Ignore);
            for (int i = 0; i < count; i++)
            {
                var h = hitsBuffer[i];
                if (player != null && h.collider.transform.IsChildOf(player.transform)) continue;
                if (h.collider.GetComponentInParent<BoarObstacle>() != null) continue;
                if (h.point.y > best) best = h.point.y;
            }
            return float.IsNegativeInfinity(best) ? at.y : best;
        }
        readonly RaycastHit[] hitsBuffer = new RaycastHit[8];

        void Update()
        {
            if (Rule == null) return;
            var walker = QingxiFirstPerson.Current;
            float dt = Mathf.Min(Time.deltaTime, .1f);
            if (walker == null) { Present(dt); return; }
            clock += dt;
            hitFlash = Mathf.Max(0, hitFlash - dt * 3);
            if (BoarObstacle.All.Count != obstacles.Count) CollectObstacles();

            var at = walker.transform.position;
            input.player = new Rules.P(at.x, at.z);
            ReadInput(walker);
            input.dodge = dodgeWanted;
            input.cleanseHeld = cleanseKey;
            var events = Rule.Update(clock, input);
            dodgeWanted = null;
            foreach (var e in events) React(e, walker);
            MovePlayer(walker, dt);
            if (auto) AutoEnd();
            Present(dt);
            SetJumpHeld(walker, Rule.Engaged);
        }

        // Space dodges during the fight, so it must not also jump. Restored as soon as the fight is over.
        void SetJumpHeld(QingxiFirstPerson walker, bool hold)
        {
            if (hold == holdingJump) return;
            holdingJump = hold;
            if (hold) { savedJump = walker.jumpSpeed; walker.jumpSpeed = 0; }
            else walker.jumpSpeed = savedJump;
        }

        void OnDisable()
        {
            var walker = QingxiFirstPerson.Current;
            if (walker == null) return;
            if (holdingJump) SetJumpHeld(walker, false);
            if (pushing) { walker.walkSpeed = savedWalk; walker.runSpeed = savedRun; pushing = false; }
        }

        void React(in Rules.Event e, QingxiFirstPerson walker)
        {
            if (auto) Debug.Log($"QINGXI_ZHUO_BOAR_EVENT {Rule.time:0.00} {e.type} {e.obstacle} boar=({Rule.x:0.0},{Rule.z:0.0}) player=({walker.transform.position.x:0.0},{walker.transform.position.z:0.0}) walk={walker.walkSpeed} keys={autoKeys.Count} kb={Keyboard.current?.name}");
            var tip = Content.texts.tip;
            switch (e.type)
            {
                case "dodge":
                    Push(walker, new Vector3((float)e.x, 0, (float)e.z), (float)Content.dodgeIFrameSeconds);
                    break;
                case "hit":
                    hitFlash = 1;
                    Push(walker, new Vector3((float)e.x, 0, (float)e.z), .22f);
                    fx.Thud(); fx.Shake(.2f, .1f);
                    Tip(tip.hit, 1.2f);
                    StaminaLost?.Invoke(e.staminaLost, e.stamina);
                    break;
                case "daze":
                    fx.Shake((float)Content.dazeShakeSeconds, .14f); fx.Clack(); fx.Thud();
                    if (byId.TryGetValue(e.obstacle, out var struck)) struck.Strike(body.position, fx);
                    break;
                case "cleanse":
                    fx.MistBurst(40); fx.Breath();
                    if (Rule.cleanses < Content.cleanseNeeded) Tip(tip.firstCleanse, 1.6f);
                    break;
                case Rules.CleansedEvent:
                    fx.MistBurst(90);
                    Banner(Content.texts.cleansed, Content.texts.cleansedHint);
                    Cleansed?.Invoke(e.durationSeconds, e.hitsTaken);
                    result = $"cleansed duration={e.durationSeconds:0.0} hits={e.hitsTaken}";
                    break;
                case Rules.EscapedEvent:
                    Banner(Content.texts.escaped, Content.texts.escapedHint);
                    Escaped?.Invoke(e.hitsTaken);
                    result = $"escaped hits={e.hitsTaken}";
                    break;
                case "returned":
                    zhuoShown = 1;
                    returned = true;
                    break;
            }
        }

        void Tip(string text, float seconds) { tipOverride = text; tipUntil = Time.time + seconds; }
        void Banner(string top, string sub) { bannerTop = top; bannerSub = sub; bannerAt = Time.time; }

        void Push(QingxiFirstPerson walker, Vector3 by, float seconds)
        {
            pushLeft = by; pushRate = by.magnitude / Mathf.Max(seconds, .01f);
            if (!pushing) { savedWalk = walker.walkSpeed; savedRun = walker.runSpeed; walker.walkSpeed = walker.runSpeed = 0; pushing = true; }
        }

        void MovePlayer(QingxiFirstPerson walker, float dt)
        {
            if (!pushing) return;
            var step = Vector3.MoveTowards(Vector3.zero, pushLeft, pushRate * dt);
            pushLeft -= step;
            var cc = walker.GetComponent<CharacterController>();
            if (cc != null && cc.enabled) cc.Move(step);
            if (pushLeft.sqrMagnitude < 1e-5f) { walker.walkSpeed = savedWalk; walker.runSpeed = savedRun; pushing = false; }
        }

        void Present(float dt)
        {
            bool shown = Rule.visible;
            foreach (var r in renderers) if (r != null) r.enabled = shown;

            var pos = new Vector3((float)Rule.x, 0, (float)Rule.z);
            groundY = Mathf.Lerp(groundY, Ground(new Vector3(pos.x, groundY, pos.z)), 1 - Mathf.Exp(-14 * dt));
            pos.y = groundY;
            var rot = Quaternion.Euler(0, (float)Rule.yaw * Mathf.Rad2Deg, 0);
            body.SetPositionAndRotation(pos, rot);

            zhuoShown = shotZhuo >= 0 ? shotZhuo : Mathf.MoveTowards(zhuoShown, (float)Rule.Zhuo, dt * .7f);
            foreach (var r in renderers)
            {
                if (r == null) continue;
                r.GetPropertyBlock(block);
                block.SetFloat(ZhuoId, zhuoShown);
                r.SetPropertyBlock(block);
            }

            PlayClip(ClipFor());
            if (clips != null && clips["Flee"] != null) clips["Flee"].speed = Rule.state == "reposition" ? .7f : 1;   // a trot, not a bolt

            var line = Rule.line;
            if (line != null && (Rule.state == "telegraph" || Rule.state == "charge"))
            {
                var dir = new Vector3(Mathf.Sin((float)line.yaw), 0, Mathf.Cos((float)line.yaw));
                fx.ShowLine(new Vector3((float)line.x, groundY, (float)line.z), dir, (float)line.length + .3f, (float)line.width, line.isFixed, Ground);
            }
            else fx.HideLine();

            bool cleansing = Rule.state == "daze" && Rule.CleanseProgress > 0;
            float rate = !shown || Rule.state == "cleansed" ? 0 : cleansing ? 46 : 4.5f * (float)Rule.Zhuo;
            fx.MistAt(pos + Vector3.up * .72f, rot, rate);
        }

        string ClipFor()
        {
            switch (Rule.state)
            {
                case "telegraph": return "Paw";
                case "charge": return "Charge";
                case "daze": return "Daze";
                case "cleansed": return Rule.Elapsed < Content.tuning.cleansedStandSeconds ? "Cleanse" : "Flee";
                case "escaped": return "Flee";
                case "reposition": return "Flee";
                default: return "Idle";
            }
        }

        void PlayClip(string name)
        {
            if (clips == null || name == clipNow || clips[name] == null) return;
            clipNow = name;
            if (name == "Paw") clips[name].speed = clips[name].length / (float)Content.pawTelegraphSeconds;
            clips.CrossFade(name, name == "Charge" ? .1f : .2f);
        }

        // ------------------------------------------------------------------ input
        Rules.P? dodgeWanted;
        bool cleanseKey, touchDodge, touchCleanse;

        void ReadInput(QingxiFirstPerson walker)
        {
            var kb = Keyboard.current;
            ReadTouchButtons();
            cleanseKey = touchCleanse || (kb != null && kb.fKey.isPressed);
            bool pressed = touchDodge || (kb != null && (kb.leftShiftKey.wasPressedThisFrame || kb.rightShiftKey.wasPressedThisFrame || kb.spaceKey.wasPressedThisFrame));
            touchDodge = false;
            if (auto) { pressed = false; AutoPlay(walker, ref pressed); }
            if (pressed && Rule.CanDodge) dodgeWanted = DodgeDirection(walker, kb);
        }

        // Keys or the left stick, relative to the view. With no direction: out of the charge line if it is showing, otherwise back.
        Rules.P DodgeDirection(QingxiFirstPerson walker, Keyboard kb)
        {
            var stick = QingxiFirstPerson.VirtualMove;
            if (kb != null) stick += new Vector2((kb.dKey.isPressed ? 1 : 0) - (kb.aKey.isPressed ? 1 : 0), (kb.wKey.isPressed ? 1 : 0) - (kb.sKey.isPressed ? 1 : 0));
            if (autoDodgeSide != 0) stick = Vector2.zero;
            if (stick.sqrMagnitude > .01f)
            {
                var d = walker.transform.TransformDirection(new Vector3(stick.x, 0, stick.y));
                return new Rules.P(d.x, d.z);
            }
            var line = Rule.line;
            if (line != null)
            {
                double sx = Math.Cos(line.yaw), sz = -Math.Sin(line.yaw);
                double side = autoDodgeSide != 0 ? autoDodgeSide : ((walker.transform.position.x - line.x) * sx + (walker.transform.position.z - line.z) * sz >= 0 ? 1 : -1);
                return new Rules.P(sx * side, sz * side);
            }
            var back = -walker.transform.forward;
            return new Rules.P(back.x, back.z);
        }

        // On-screen buttons sit over QingxiTouchControls' arc, which keeps doing the stick and the look.
        void ReadTouchButtons()
        {
            if (!QingxiTouchControls.Active || !Rule.Engaged) { touchCleanse = false; return; }
            bool held = false;
            if (Touchscreen.current != null)
                foreach (var t in Touchscreen.current.touches)
                {
                    var phase = t.phase.ReadValue();
                    if (phase == UnityEngine.InputSystem.TouchPhase.None || phase == UnityEngine.InputSystem.TouchPhase.Ended || phase == UnityEngine.InputSystem.TouchPhase.Canceled) continue;
                    Pointer(t.position.ReadValue(), phase == UnityEngine.InputSystem.TouchPhase.Began, ref held);
                }
            var mouse = Mouse.current;
            if (mouse != null && mouse.leftButton.isPressed) Pointer(mouse.position.ReadValue(), mouse.leftButton.wasPressedThisFrame, ref held);
            touchCleanse = held;
        }

        void Pointer(Vector2 screen, bool began, ref bool held)
        {
            float s = Scale;
            var gui = new Vector2(screen.x / s, (Screen.height - screen.y) / s);
            if (began && Vector2.Distance(gui, DodgeCentre) <= ButtonSize * .5f + 6) touchDodge = true;
            if (ShowCleanse && Vector2.Distance(gui, CleanseCentre) <= ButtonSize * .5f + 6) held = true;
        }

        bool ShowCleanse => Rule != null && QingxiFirstPerson.Current != null && Rule.CanCleanse(new Rules.P(QingxiFirstPerson.Current.transform.position.x, QingxiFirstPerson.Current.transform.position.z));

        // ------------------------------------------------------------------ HUD (720-high GUI space; 104 is 156 px on a 1080p screen)
        const float ButtonSize = 104;
        static float Scale => Mathf.Clamp(Screen.height / 720f, .7f, 2f);
        static Vector2 DodgeCentre => new Vector2(Screen.width / Scale - 96, Screen.height / Scale - 96);
        static Vector2 CleanseCentre => DodgeCentre + new Vector2(-124, -18);

        GUIStyle title, label, tipStyle, buttonStyle, keyStyle, bannerStyle, bannerSubStyle;

        void Styles()
        {
            if (title != null) return;
            title = new GUIStyle { font = QingxiFonts.Title, fontSize = 22, alignment = TextAnchor.MiddleCenter, normal = { textColor = QingxiUiArt.Mist } };
            label = new GUIStyle { font = QingxiFonts.Ui, fontSize = 14, alignment = TextAnchor.MiddleLeft, normal = { textColor = QingxiUiArt.Mist } };
            tipStyle = new GUIStyle { font = QingxiFonts.Ui, fontSize = 18, alignment = TextAnchor.MiddleCenter, normal = { textColor = QingxiUiArt.Mist } };
            buttonStyle = new GUIStyle { font = QingxiFonts.Title, fontStyle = FontStyle.Bold, fontSize = 34, alignment = TextAnchor.MiddleCenter, normal = { textColor = new Color(.06f, .15f, .13f) } };
            keyStyle = new GUIStyle { font = QingxiFonts.Ui, fontSize = 11, alignment = TextAnchor.MiddleCenter, normal = { textColor = new Color(.1f, .22f, .19f, .85f) } };
            bannerStyle = new GUIStyle { font = QingxiFonts.Title, fontSize = 46, alignment = TextAnchor.MiddleCenter, normal = { textColor = QingxiUiArt.Mist } };
            bannerSubStyle = new GUIStyle { font = QingxiFonts.Ui, fontSize = 20, alignment = TextAnchor.MiddleCenter, normal = { textColor = QingxiUiArt.Mist } };
        }

        void OnGUI()
        {
            if (Rule == null || Rule.state == "idle" && Time.time - bannerAt > 5) return;
            QingxiFonts.ApplyImgui();
            Styles();
            GUI.depth = -10;
            var previous = GUI.matrix;
            float s = Scale;
            GUI.matrix = Matrix4x4.Scale(Vector3.one * s);
            float w = Screen.width / s, h = Screen.height / s;

            if (hitFlash > 0) QingxiUiArt.Draw(new Rect(-w * .25f, -h * .25f, w * 1.5f, h * 1.5f), QingxiUiArt.Soft, new Color(.6f, .08f, .06f, .0f + .22f * hitFlash));
            if (Rule.Engaged) DrawFight(w, h);
            if (Rule.state == "escaped" && Rule.RetryIn > 0 && Time.time - bannerAt > 3)
                Strip(w, h, $"{Math.Ceiling(Rule.RetryIn):0} {Content.texts.cooldown}");
            float age = Time.time - bannerAt;
            if (age < 4.5f && bannerTop != null)
            {
                float a = Mathf.Clamp01(age / .4f) * Mathf.Clamp01((4.5f - age) / .8f);
                var keep = GUI.color; GUI.color = new Color(1, 1, 1, a);
                GUI.Label(new Rect(0, h * .3f, w, 70), bannerTop, bannerStyle);
                GUI.Label(new Rect(0, h * .3f + 66, w, 34), bannerSub, bannerSubStyle);
                GUI.color = keep;
            }
            GUI.matrix = previous;
        }

        void DrawFight(float w, float h)
        {
            var hud = Content.texts.hud;
            float x = w / 2 - 150, y = 16;
            QingxiUiArt.Sliced(new Rect(x - 16, y - 8, 332, 80), QingxiUiArt.Ink);
            Bar(new Rect(x + 52, y + 6, 248, 14), (float)Rule.Zhuo, new Color(.36f, .18f, .5f));
            GUI.Label(new Rect(x, y, 50, 26), hud.zhuo, label);
            Bar(new Rect(x + 52, y + 34, 158, 10), (float)(Rule.stamina / staminaStart), new Color(.42f, .72f, .5f));
            GUI.Label(new Rect(x, y + 26, 50, 26), hud.stamina, label);
            GUI.Label(new Rect(x + 218, y + 26, 40, 26), hud.hits, label);
            for (int i = 0; i < Content.hitsBeforeEscape; i++)
                QingxiUiArt.Draw(QingxiUiArt.Circle(new Vector2(x + 262 + i * 15, y + 39), 12), QingxiUiArt.Soft, i < Rule.hits ? new Color(.86f, .3f, .22f) : new Color(1, 1, 1, .3f));

            var player = QingxiFirstPerson.Current.transform.position;
            bool near = Rule.CanCleanse(new Rules.P(player.x, player.z));
            var tip = Content.texts.tip;
            string line = Time.time < tipUntil ? tipOverride
                : Rule.state == "alert" ? tip.alert : Rule.state == "telegraph" ? tip.telegraph : Rule.state == "charge" ? tip.charge
                : Rule.state == "brake" ? tip.brake : Rule.state == "reposition" ? tip.reposition : near ? tip.dazeNear : tip.dazeFar;
            Strip(w, h, line);

            // Hold progress also shows at the centre for keyboard players, who have no button.
            if (near && Rule.CleanseProgress > 0 && !QingxiTouchControls.Active)
            {
                var c = new Vector2(w / 2, h * .62f);
                Ring(c, 70, (float)Rule.CleanseProgress);
                GUI.Label(new Rect(c.x - 35, c.y - 35, 70, 70), Content.texts.button.cleanse, new GUIStyle(title) { fontSize = 26 });
            }
            else if (near && !QingxiTouchControls.Active) GUI.Label(new Rect(0, h * .62f - 16, w, 32), Content.texts.button.cleanseKey, tipStyle);

            if (!QingxiTouchControls.Active) return;
            RoundButton(DodgeCentre, Content.texts.button.dodge, Content.texts.button.dodgeKey, Rule.CanDodge ? 1 : .55f, -1);
            if (near) RoundButton(CleanseCentre, Content.texts.button.cleanse, Content.texts.button.cleanseKey, 1, (float)Rule.CleanseProgress);
        }

        void Strip(float w, float h, string text)
        {
            if (string.IsNullOrEmpty(text)) return;
            float width = Mathf.Min(w - 40, 60 + text.Length * 19);
            var r = new Rect(w / 2 - width / 2, h - 64, width, 40);
            QingxiUiArt.Sliced(r, QingxiUiArt.Ink);
            GUI.Label(r, text, tipStyle);
        }

        static void Bar(Rect r, float k, Color c)
        {
            QingxiUiArt.Draw(r, Texture2D.whiteTexture, new Color(0, 0, 0, .45f));
            QingxiUiArt.Draw(new Rect(r.x + 1, r.y + 1, Mathf.Max(0, (r.width - 2) * Mathf.Clamp01(k)), r.height - 2), Texture2D.whiteTexture, c);
        }

        // The fill is a ring that closes on the button: outer ring of dots, one per step.
        static void Ring(Vector2 centre, float size, float k)
        {
            QingxiUiArt.Draw(QingxiUiArt.Circle(centre, size), QingxiUiArt.Ring, new Color(1, 1, 1, .35f));
            const int Dots = 36;
            int on = Mathf.RoundToInt(Dots * Mathf.Clamp01(k));
            for (int i = 0; i < on; i++)
            {
                float a = i / (float)Dots * Mathf.PI * 2;
                QingxiUiArt.Draw(QingxiUiArt.Circle(centre + new Vector2(Mathf.Sin(a), -Mathf.Cos(a)) * (size * .5f), 9), QingxiUiArt.Soft, QingxiUiArt.Gold);
            }
        }

        void RoundButton(Vector2 centre, string text, string key, float alpha, float fill)
        {
            QingxiUiArt.Draw(QingxiUiArt.Circle(centre + new Vector2(0, 3), ButtonSize + 8), QingxiUiArt.Soft, new Color(0, 0, 0, .35f));
            QingxiUiArt.Draw(QingxiUiArt.Circle(centre, ButtonSize), QingxiUiArt.Jade, new Color(1, 1, 1, alpha));
            GUI.Label(new Rect(centre.x - ButtonSize / 2, centre.y - ButtonSize / 2 - 6, ButtonSize, ButtonSize), text, buttonStyle);
            GUI.Label(new Rect(centre.x - ButtonSize / 2, centre.y + 22, ButtonSize, 16), key, keyStyle);
            if (fill >= 0) Ring(centre, ButtonSize + 10, fill);
        }

        // ------------------------------------------------------------------ review hooks: --boar-auto-clean and --boar-auto-hits play with the
        // same paths the buttons use (scripted, not a person), --boar-capture saves 30 fps frames beside the player (for the
        // video) and quits at the end, --touch shows the phone buttons.
        bool auto, autoHits, capture;
        Keyboard autoKeyboard;
        readonly List<Key> autoKeys = new List<Key>();
        string result;
        int autoCharges, frameIndex, autoDodgeSide;
        float endTimer;
        Vector3 autoSpot;
        bool autoHoldSpot, returned;
        float shotZhuo = -1;

        void StartReviewHooks()
        {
            string args = string.Join(" ", Environment.GetCommandLineArgs()) + " " + Application.absoluteURL;
            autoHits = args.Contains("boar-auto-hits");
            auto = autoHits || args.Contains("boar-auto-clean");
            capture = args.Contains("boar-capture");
            if (auto) autoKeyboard = InputSystem.AddDevice<Keyboard>("BoarAutoKeyboard");
            if (args.Contains("boar-shot")) StartCoroutine(Shots());
            if (auto) foreach (var o in obstacles) Debug.Log($"QINGXI_ZHUO_BOAR_OBSTACLE {o.id} ({o.x:0.00},{o.z:0.00}) r={o.r:0.00}");
            if (capture) { Time.captureFramerate = 30; StartCoroutine(Capture()); }
        }

        void AutoPlay(QingxiFirstPerson walker, ref bool dodge)
        {
            var at = walker.transform.position;
            var boar = new Vector3((float)Rule.x, at.y, (float)Rule.z);
            autoDodgeSide = 0;
            cleanseKey = false;
            string state = Rule.state;
            if (state == "charge" && !autoHoldSpot) { autoHoldSpot = true; autoCharges++; }
            if (state != "charge" && state != "telegraph") autoHoldSpot = false;

            Vector3 want = at;
            if (state == "idle") want = boar;
            else if (autoHits)
            {
                // Stay in the open, in the way, and take the hit.
                if (state == "alert" || state == "brake") want = OpenSpot(boar);
            }
            else if (state == "daze")
            {
                float d = Vector3.Distance(at, boar);
                if (d > 1.6f) want = boar;
                if (d <= 1.9f) cleanseKey = true;
            }
            else if (state == "alert" || state == "brake" || state == "telegraph" || state == "reposition")
            {
                // The first charge in the open, to show a clean dodge; after that behind a tree, so it runs into the trunk.
                want = autoCharges == 0 ? OpenSpot(boar) : BehindNearestTree(boar, at);
            }
            else if (state == "charge")
            {
                var line = Rule.line;
                if (line != null)
                {
                    var dir = new Vector3(Mathf.Sin((float)line.yaw), 0, Mathf.Cos((float)line.yaw));
                    if (Vector3.Dot(at - boar, dir) < 4.2f && Rule.CanDodge && Vector3.Dot(at - boar, dir) > 0)
                    {
                        dodge = true;
                        autoDodgeSide = (autoCharges % 2) == 0 ? 1 : -1;
                    }
                }
            }

            var to = want - at; to.y = 0;
            float yaw = walker.transform.eulerAngles.y * Mathf.Deg2Rad;
            var local = new Vector2(to.x * Mathf.Cos(yaw) - to.z * Mathf.Sin(yaw), to.x * Mathf.Sin(yaw) + to.z * Mathf.Cos(yaw));
            // Pressed on a keyboard device of its own: QingxiTouchControls rewrites VirtualMove every frame.
            autoKeys.Clear();
            if (local.magnitude > .25f)
            {
                var k = local.normalized;
                if (k.x > .38f) autoKeys.Add(Key.D); if (k.x < -.38f) autoKeys.Add(Key.A);
                if (k.y > .38f) autoKeys.Add(Key.W); if (k.y < -.38f) autoKeys.Add(Key.S);
                if (local.magnitude > 2) autoKeys.Add(Key.LeftShift);
            }
            autoKeyboard.MakeCurrent();
            InputSystem.QueueStateEvent(autoKeyboard, new KeyboardState(autoKeys.ToArray()));
            // Keep the boar in view, the way a player would.
            var look = boar - at; look.y = 0;
            float diff = Mathf.DeltaAngle(walker.transform.eulerAngles.y, Mathf.Atan2(look.x, look.z) * Mathf.Rad2Deg);
            QingxiFirstPerson.VirtualLook += new Vector2(Mathf.Clamp(diff, -180, 180) * Mathf.Min(1, Time.deltaTime * 2.5f), 0);
        }

        Vector3 OpenSpot(Vector3 boar)
        {
            // Six metres from the boar, towards the middle of the clearing and away from anything it could hit.
            Vector3 best = boar; float bestScore = float.NegativeInfinity;
            for (int i = 0; i < 16; i++)
            {
                float a = i / 16f * Mathf.PI * 2;
                var p = boar + new Vector3(Mathf.Sin(a), 0, Mathf.Cos(a)) * 6;
                float score = -new Vector2(p.x - transform.position.x, p.z - transform.position.z).magnitude * .5f;
                foreach (var o in obstacles) score += Mathf.Min(0, DistanceToSegment(new Vector2((float)o.x, (float)o.z), new Vector2(boar.x, boar.z), new Vector2(p.x, p.z)) - 2.2f) * 4;
                if (score > bestScore) { bestScore = score; best = p; }
            }
            return best;
        }

        static float DistanceToSegment(Vector2 p, Vector2 a, Vector2 b)
        {
            var ab = b - a;
            float t = Mathf.Clamp01(Vector2.Dot(p - a, ab) / Mathf.Max(ab.sqrMagnitude, 1e-4f));
            return Vector2.Distance(p, a + ab * t);
        }

        Vector3 BehindNearestTree(Vector3 boar, Vector3 at)
        {
            Vector3 best = at; float bestD = float.PositiveInfinity;
            foreach (var o in obstacles)
            {
                var tree = new Vector3((float)o.x, at.y, (float)o.z);
                var away = tree - boar; away.y = 0;
                if (away.magnitude < 3) continue;
                var spot = tree + away.normalized * (1.1f + (float)o.r);
                if (useBounds && (spot.x < boundsMin.x + 1 || spot.x > boundsMax.x - 1 || spot.z < boundsMin.y + 1 || spot.z > boundsMax.y - 1)) continue;
                float d = Vector3.Distance(at, spot);
                if (d < bestD) { bestD = d; best = spot; }
            }
            return best;
        }

        void AutoEnd()
        {
            if (Time.time > 170) { Debug.Log($"QINGXI_ZHUO_BOAR_RUN gave up state={Rule.state} cleanses={Rule.cleanses} hits={Rule.hits}"); auto = capture = false; Application.Quit(); return; }
            bool over = autoHits ? returned : Rule.state == "cleansed" && !Rule.visible;
            if (!over) { endTimer = 0; return; }
            endTimer += Time.deltaTime;
            if (endTimer < 2.5f) return;
            Debug.Log($"QINGXI_ZHUO_BOAR_RUN {result} charges={autoCharges} frames={frameIndex}");
            auto = false;
            capture = false;
            Application.Quit();
        }

        // Review shots of the boar in the game, with _Zhuo at 1, 0.5 and 0, saved beside the player. --boar-shot
        System.Collections.IEnumerator Shots()
        {
            var cam = QingxiFirstPerson.Current.cam;
            QingxiFirstPerson.Current.enabled = false;
            yield return new WaitForSeconds(1f);
            var folder = System.IO.Path.GetDirectoryName(Application.dataPath);
            foreach (var (z, name) in new[] { (1f, "zhuo_1"), (.5f, "zhuo_0.5"), (0f, "zhuo_0") })
            {
                shotZhuo = z;
                var at = body.position; var forward = body.forward; var right = body.right;
                cam.transform.position = at + forward * 1.5f + right * 1.25f + Vector3.up * .85f;
                cam.transform.LookAt(at + Vector3.up * .5f);
                yield return new WaitForSeconds(.4f);
                yield return new WaitForEndOfFrame();
                var tex = new Texture2D(Screen.width, Screen.height, TextureFormat.RGB24, false);
                tex.ReadPixels(new Rect(0, 0, Screen.width, Screen.height), 0, 0); tex.Apply();
                System.IO.File.WriteAllBytes(System.IO.Path.Combine(folder, $"boar_{name}.png"), tex.EncodeToPNG());
            }
            shotZhuo = 1;
            cam.transform.position = body.position + body.forward * 1.15f + body.right * .35f + Vector3.up * .68f;
            cam.transform.LookAt(body.position + body.forward * .6f + Vector3.up * .52f);
            yield return new WaitForSeconds(.4f);
            yield return new WaitForEndOfFrame();
            var close = new Texture2D(Screen.width, Screen.height, TextureFormat.RGB24, false);
            close.ReadPixels(new Rect(0, 0, Screen.width, Screen.height), 0, 0); close.Apply();
            System.IO.File.WriteAllBytes(System.IO.Path.Combine(folder, "boar_head_zhuo_1.png"), close.EncodeToPNG());
            Debug.Log("QINGXI_ZHUO_BOAR_SHOTS saved");
            Application.Quit();
        }

        System.Collections.IEnumerator Capture()
        {
            var folder = System.IO.Path.Combine(System.IO.Path.GetDirectoryName(Application.dataPath), "boar-frames");
            System.IO.Directory.CreateDirectory(folder);
            while (capture)
            {
                yield return new WaitForEndOfFrame();
                var tex = new Texture2D(Screen.width, Screen.height, TextureFormat.RGB24, false);
                tex.ReadPixels(new Rect(0, 0, Screen.width, Screen.height), 0, 0); tex.Apply();
                System.IO.File.WriteAllBytes(System.IO.Path.Combine(folder, $"f{frameIndex++:00000}.jpg"), tex.EncodeToJPG(90));
                Destroy(tex);
            }
        }
    }
}
