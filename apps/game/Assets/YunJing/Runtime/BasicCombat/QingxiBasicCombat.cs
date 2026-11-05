using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using UnityEngine.InputSystem;
using Rules = YunJing.BasicCombat.QingxiBasicCombatRules;

namespace YunJing.BasicCombat
{
    /// <summary>
    /// Novice bare-hand combat on the player: three-hit palm chain, one charged heavy strike with knockback and cooldown, a dodge with
    /// i-frames that cancels recovery, and hit feedback (hit-stop, light camera shake, target flash, debris, placeholder sound).
    /// Rules live in QingxiBasicCombatRules (port of tools/basic-combat); numbers in Resources/BasicCombat/basic-combat-v1.
    /// Keys: J / left mouse = palm, Q / right mouse (hold) = heavy, C / Left Ctrl = dodge. Touch: QingxiTouchControls draws 攻 招 閃.
    /// Settlement is not done here: every hit raises <see cref="Hit"/> (combat.hit { targetId, attackId, damage }) for the core group.
    /// </summary>
    [DefaultExecutionOrder(50)]
    public sealed class QingxiBasicCombat : MonoBehaviour
    {
        public static bool VirtualAttack, VirtualHeavyHeld, VirtualDodge;
        /// <summary>Scripted runs (demo capture, smoke) can supply input instead of the devices.</summary>
        public static Func<Rules.Input?> ScriptedInput;
        /// <summary>combat.hit { targetId, attackId, damage } — the core group settles from this.</summary>
        public static event Action<string, string, float> Hit;
        public static QingxiBasicCombat Current { get; private set; }

        public Transform body;            // avatar to turn and animate (Body_NoviceCultivatorV1)
        public Camera cam;
        public ParticleSystem debris;
        public float targetSearchRadius = 15;

        CharacterController cc;
        Rules rules;
        readonly List<Rules.Target> targets = new List<Rules.Target>();
        readonly List<ICombatTarget> targetObjects = new List<ICombatTarget>();
        // study avatar arm parts are separate, unparented meshes (upper arm, sleeve, hand); each side swings as one around its shoulder
        readonly List<Transform> rightArm = new List<Transform>(), leftArm = new List<Transform>();
        Transform rightShoulder, leftShoulder;
        // QingxiNoviceMotion re-sets the arm rotations each frame but never positions, and never touches the hands: keep both rests
        readonly Dictionary<Transform, (Vector3 pos, Quaternion rot)> armRest = new Dictionary<Transform, (Vector3, Quaternion)>();
        float shake, shakeSeed, hurtFlash, dodgedFlash, bodyYaw;
        Coroutine stopRoutine;
        AudioSource audioSource;
        AudioClip thump, heavyThump, whoosh;
        string lastNotice; float noticeUntil;

        public Rules Rules => rules;
        public Vector3 ShakeOffset { get; private set; }
        public bool Busy => rules != null && rules.Busy;

        void Awake()
        {
            Current = this;
            cc = GetComponent<CharacterController>();
            var text = Resources.Load<TextAsset>("BasicCombat/basic-combat-v1");
            if (text == null) throw new InvalidOperationException("Resources/BasicCombat/basic-combat-v1 missing");
            var content = JsonUtility.FromJson<Rules.Content>(text.text);
            rules = new Rules(content, transform.position.x, transform.position.z, transform.eulerAngles.y * Mathf.Deg2Rad);
            if (body != null)
                foreach (var t in body.GetComponentsInChildren<Transform>(true))
                {
                    if (!t.name.Contains("SK_QX13_UpperArm_") && !t.name.Contains("SK_QX13_Sleeve_") && !t.name.Contains("SK_QX13_Hand_")) continue;
                    var upper = body.GetComponentsInChildren<Transform>(true).FirstOrDefault(u => u.name == "SK_QX13_UpperArm_" + (t.name.EndsWith("_-1") ? "-1" : "1"));
                    if (upper == null) continue;
                    bool right = Vector3.Dot(upper.position - body.position, body.right) > 0;
                    (right ? rightArm : leftArm).Add(t);
                    armRest[t] = (t.localPosition, t.localRotation);
                    if (t == upper) { if (right) rightShoulder = t; else leftShoulder = t; }
                }
            audioSource = gameObject.AddComponent<AudioSource>();
            audioSource.playOnAwake = false; audioSource.spatialBlend = 0;
            thump = Tone("thump", 90, .09f, .9f); heavyThump = Tone("heavy", 60, .18f, 1f); whoosh = Tone("whoosh", 0, .12f, .35f);
        }

        // Disabling stops this component's coroutines, so the hit-stop timer would never end: both paths run the same cleanup.
        void OnDisable() => EndHitStop();
        void OnDestroy() { EndHitStop(); if (Current == this) Current = null; }

        // Placeholder sounds (the package asks for placeholders): a low thump for hits, noise for swings.
        static AudioClip Tone(string name, float hz, float seconds, float gain)
        {
            int rate = 22050, n = Mathf.CeilToInt(rate * seconds);
            var data = new float[n];
            var rnd = new System.Random(name.GetHashCode());
            for (int i = 0; i < n; i++)
            {
                float t = i / (float)rate, env = Mathf.Exp(-t * (hz > 0 ? 28 : 18)) * Mathf.Clamp01(t * 400);
                float noise = (float)(rnd.NextDouble() * 2 - 1);
                data[i] = gain * env * (hz > 0 ? .75f * Mathf.Sin(2 * Mathf.PI * hz * t * (1 - t * 2)) + .25f * noise : noise * .6f);
            }
            var clip = AudioClip.Create("BasicCombat_" + name, n, 1, rate, false);
            clip.SetData(data, 0);
            return clip;
        }

        Rules.Input ReadDevices(out Vector3 move)
        {
            var kb = Keyboard.current; var mouse = Mouse.current;
            bool locked = Cursor.lockState == CursorLockMode.Locked;
            var input = new Rules.Input
            {
                attack = VirtualAttack || (kb != null && kb.jKey.wasPressedThisFrame) || (locked && mouse != null && mouse.leftButton.wasPressedThisFrame),
                heavyHeld = VirtualHeavyHeld || (kb != null && kb.qKey.isPressed) || (locked && mouse != null && mouse.rightButton.isPressed),
                dodge = VirtualDodge || (kb != null && (kb.cKey.wasPressedThisFrame || kb.leftCtrlKey.wasPressedThisFrame)),
            };
            VirtualAttack = VirtualDodge = false;
            var stick = global::QingxiWorld.QingxiFirstPerson.VirtualMove;
            float mx = stick.x, mz = stick.y;
            if (kb != null) { mx += (kb.dKey.isPressed ? 1 : 0) - (kb.aKey.isPressed ? 1 : 0); mz += (kb.wKey.isPressed ? 1 : 0) - (kb.sKey.isPressed ? 1 : 0); }
            move = transform.right * mx + transform.forward * mz;   // the player root turns with the camera
            move.y = 0;
            if (move.sqrMagnitude > 1) move.Normalize();
            input.moveX = move.x; input.moveZ = move.z;
            return input;
        }

        void Update()
        {
            Vector3 move;
            var input = ReadDevices(out move);
            var scripted = ScriptedInput?.Invoke();
            if (scripted.HasValue) input = scripted.Value;

            rules.Sync(transform.position.x, transform.position.z, (body != null ? body.eulerAngles.y : transform.eulerAngles.y) * Mathf.Deg2Rad);
            targets.Clear(); targetObjects.Clear();
            foreach (var t in CombatTargets.All)
            {
                var p = t.CombatPosition;
                if ((p - transform.position).sqrMagnitude > targetSearchRadius * targetSearchRadius) continue;
                targets.Add(new Rules.Target { id = t.CombatId, x = p.x, z = p.z, radius = t.CombatRadius, alive = t.CombatAlive });
                targetObjects.Add(t);
            }
            foreach (var e in rules.Update(Time.time, input, targets)) Handle(e);

            rules.Velocity(out double vx, out double vz);
            if ((vx != 0 || vz != 0) && cc != null && cc.enabled) cc.Move(new Vector3((float)vx, 0, (float)vz) * Time.deltaTime);
        }

        void Handle(Rules.Event e)
        {
            switch (e.type)
            {
                case "attack.start":
                    audioSource.pitch = e.kind == "heavy" ? .7f : UnityEngine.Random.Range(1.05f, 1.25f);
                    audioSource.PlayOneShot(whoosh, e.kind == "heavy" ? .9f : .6f);
                    break;
                case Rules.HitEvent:
                    var target = targetObjects.Find(t => t.CombatId == e.targetId);
                    var dir = new Vector3((float)e.dirX, 0, (float)e.dirZ);
                    var hit = new CombatHit { targetId = e.targetId, attackId = e.attackId, damage = (float)e.damage, knockback = (float)e.knockback, hitStop = (float)e.hitStop, direction = dir, heavy = e.heavy };
                    if (target != null)
                    {
                        target.TakeCombatHit(hit);
                        var at = target.CombatPosition + Vector3.up * 1.0f - dir * target.CombatRadius;
                        if (debris != null)
                        {
                            debris.transform.position = at;
                            debris.Emit(e.heavy ? rules.Data.feedback.debrisHeavy : rules.Data.feedback.debris);
                        }
                    }
                    audioSource.pitch = UnityEngine.Random.Range(.92f, 1.08f);
                    audioSource.PlayOneShot(e.heavy ? heavyThump : thump);
                    HitStop((float)e.hitStop);
                    shake = Mathf.Max(shake, (float)e.shake);
                    Hit?.Invoke(e.targetId, e.attackId, (float)e.damage);
                    break;
                case "heavy.cooldown":
                    Notice($"重擊冷卻 {rules.HeavyCooldown:0.0} 秒");
                    break;
                case "defend":
                    if (e.result == "dodged") { dodgedFlash = 1; Notice("閃過"); }
                    else { hurtFlash = 1; shake = Mathf.Max(shake, .08f); }
                    break;
            }
        }

        void Notice(string text) { lastNotice = text; noticeUntil = Time.unscaledTime + .9f; }

        /// <summary>An enemy strike reaches the player: returns true if it lands (false while dodge i-frames last).</summary>
        public bool ReceiveStrike(string source, Vector3 push)
        {
            bool landed = rules.Receive(source) == "hit";
            Handle(rules.events[rules.events.Count - 1]);
            if (landed && cc != null && cc.enabled) cc.Move(push);
            return landed;
        }

        /// <summary>Slows time to <see cref="HitStopScale"/> for <paramref name="seconds"/> of real time. A second call while one is running
        /// takes over the same restore duty (the value from before the first call), so the older timer cannot end the new stop early.</summary>
        public void HitStop(float seconds)
        {
            if (seconds <= 0 || !isActiveAndEnabled) return;
            if (stopRoutine != null) { StopCoroutine(stopRoutine); stopRoutine = null; }
            if (!stopClock.Begin()) return;   // someone else has time stopped (pause menu at 0): leave it alone
            stopRoutine = StartCoroutine(StopFor(seconds));
        }

        IEnumerator StopFor(float seconds)
        {
            float t = 0;
            while (t < seconds) { t += Time.unscaledDeltaTime; yield return null; }
            stopRoutine = null;
            EndHitStop();
        }

        /// <summary>Ends a running hit-stop. Safe to call any number of times; shared by the timer, OnDisable and OnDestroy.</summary>
        void EndHitStop()
        {
            if (stopRoutine != null) { StopCoroutine(stopRoutine); stopRoutine = null; }
            stopClock.Release();
        }

        public const float HitStopScale = .05f;
        readonly HitStopClock stopClock = new HitStopClock();
        public bool HitStopActive => stopClock.Owned;

        /// <summary>Who owns Time.timeScale during a hit-stop. Begin remembers the scale from before the first stop; Release puts it back
        /// only while the current scale is still the one this clock set. If another system changed it meanwhile (a pause menu setting 0,
        /// a slow-motion effect), that system now owns it and Release only drops the duty.</summary>
        public sealed class HitStopClock
        {
            float restoreTo = 1;
            public bool Owned { get; private set; }

            /// <returns>false when the clock does not take time over (it is already stopped by someone else).</returns>
            public bool Begin()
            {
                if (Owned && !Mathf.Approximately(Time.timeScale, HitStopScale)) Owned = false;   // taken over meanwhile
                if (!Owned)
                {
                    if (Time.timeScale <= 0) return false;
                    restoreTo = Time.timeScale;
                }
                Owned = true;
                Time.timeScale = HitStopScale;
                return true;
            }

            public void Release()
            {
                if (!Owned) return;
                Owned = false;
                if (Mathf.Approximately(Time.timeScale, HitStopScale)) Time.timeScale = restoreTo;
            }
        }

        void LateUpdate()
        {
            float dt = Time.unscaledDeltaTime;
            // turn the avatar toward the swing's facing while busy, ease back to the camera-led root afterwards
            if (body != null)
            {
                float rootYaw = transform.eulerAngles.y;
                float want = rules.Busy || rules.state == "charging" ? (float)(rules.yaw * Mathf.Rad2Deg) - rootYaw : 0;
                bodyYaw = Mathf.LerpAngle(bodyYaw, want, 1 - Mathf.Exp(-18 * dt));
                body.localRotation = Quaternion.Euler(0, bodyYaw, 0);
                Animate();
            }
            if (cam != null && shake > 0)
            {
                shakeSeed += dt * 60;
                var o = new Vector3(Mathf.PerlinNoise(shakeSeed, 0) - .5f, Mathf.PerlinNoise(0, shakeSeed) - .5f, 0) * shake;
                ShakeOffset = cam.transform.rotation * o;
                cam.transform.position += ShakeOffset;
                shake = Mathf.MoveTowards(shake, 0, dt * .6f);
            }
            else ShakeOffset = Vector3.zero;
            hurtFlash = Mathf.MoveTowards(hurtFlash, 0, dt * 3);
            dodgedFlash = Mathf.MoveTowards(dodgedFlash, 0, dt * 3);
        }

        // Placeholder motion on the study avatar's arms (the package says to reuse the current test animations): palms thrust
        // forward on alternating sides, the third with both arms; the heavy draws back while charging and drives both palms out.
        void Animate()
        {
            foreach (var kv in armRest)
            {
                if (kv.Key == null) continue;
                kv.Key.localPosition = kv.Value.pos;
                if (kv.Key.name.Contains("SK_QX13_Hand_")) kv.Key.localRotation = kv.Value.rot;
            }
            float right = 0, left = 0;
            string s = rules.state;
            if (s == "light" || s == "heavy")
            {
                var d = rules.Data;
                double w = s == "heavy" ? d.heavy.windup : d.light[rules.combo].windup, a = s == "heavy" ? d.heavy.active : d.light[rules.combo].active;
                double r = s == "heavy" ? d.heavy.recovery : d.light[rules.combo].recovery, e = rules.Elapsed;
                float k = e < w ? -.35f * (float)(e / w) : e < w + a ? Mathf.Lerp(-.35f, 1.15f, (float)((e - w) / a)) : Mathf.Lerp(1.15f, 0, (float)((e - w - a) / r));
                bool both = s == "heavy" || rules.combo == 2;
                bool useRight = both || rules.combo == 0;
                bool useLeft = both || rules.combo == 1;
                right = useRight ? k : 0; left = useLeft ? k : 0;
            }
            else if (s == "charging") { float c = (float)rules.Charge; right = left = -.5f * Mathf.Clamp01(c * 3) - .08f * Mathf.Sin(Time.time * 40) * c; }
            else if (s == "dodge") { right = left = -.4f; }
            Swing(rightArm, rightShoulder, right, -1);
            Swing(leftArm, leftShoulder, left, 1);
            float lean = Mathf.Max(right, left);
            if (lean > 0) body.localRotation *= Quaternion.Euler(8 * lean, 0, 0);
        }

        void Swing(List<Transform> parts, Transform shoulder, float amount, float inward)
        {
            if (shoulder == null || Mathf.Abs(amount) < 1e-3) return;
            // shoulder joint: top of the upper-arm part; raise the arm forward about the body's right axis, a little across the chest
            var pivot = shoulder.position + body.up * .11f;
            var r = Quaternion.AngleAxis(-amount * 78, body.right) * Quaternion.AngleAxis(inward * amount * 14, body.forward);
            foreach (var t in parts)
            {
                if (t == null) continue;
                t.SetPositionAndRotation(pivot + r * (t.position - pivot), r * t.rotation);
            }
        }

        GUIStyle noticeStyle;
        void OnGUI()
        {
            if (rules == null) return;
            QingxiFonts.ApplyImgui();
            float scale = Mathf.Clamp(Screen.height / 720f, .7f, 2f);
            GUI.matrix = Matrix4x4.Scale(new Vector3(scale, scale, 1));
            float w = Screen.width / scale, h = Screen.height / scale;
            // charge bar and cooldowns, bottom centre
            if (rules.state == "charging")
            {
                float c = (float)rules.Charge, min = (float)(rules.Data.heavy.chargeMin / rules.Data.heavy.chargeMax);
                var bar = new Rect(w / 2 - 110, h - 120, 220, 12);
                GUI.color = new Color(0, 0, 0, .45f); GUI.DrawTexture(bar, Texture2D.whiteTexture);
                GUI.color = c < min ? new Color(.9f, .85f, .7f, .9f) : new Color(1f, .72f, .3f, 1f);
                GUI.DrawTexture(new Rect(bar.x, bar.y, bar.width * c, bar.height), Texture2D.whiteTexture);
                GUI.color = Color.white;
            }
            noticeStyle ??= new GUIStyle(GUI.skin.label) { fontSize = 22, alignment = TextAnchor.MiddleCenter, fontStyle = FontStyle.Bold };
            string cd = rules.HeavyCooldown > 0 ? $"招 {rules.HeavyCooldown:0.0}s" : "招 可用";
            GUI.color = new Color(1, 1, 1, .85f);
            GUI.Label(new Rect(w / 2 - 120, h - 100, 240, 30), cd + (rules.DodgeCooldown > 0 ? $"　閃 {rules.DodgeCooldown:0.0}s" : "　閃 可用"), noticeStyle);
            if (Time.unscaledTime < noticeUntil && lastNotice != null)
            {
                GUI.color = new Color(1f, .93f, .75f, Mathf.Clamp01((noticeUntil - Time.unscaledTime) * 2));
                GUI.Label(new Rect(w / 2 - 160, h * .38f, 320, 40), lastNotice, noticeStyle);
            }
            if (hurtFlash > 0) { GUI.color = new Color(.8f, .1f, .05f, hurtFlash * .28f); GUI.DrawTexture(new Rect(0, 0, w, h), Texture2D.whiteTexture); }
            if (dodgedFlash > 0) { GUI.color = new Color(.6f, .85f, 1f, dodgedFlash * .14f); GUI.DrawTexture(new Rect(0, 0, w, h), Texture2D.whiteTexture); }
            GUI.color = Color.white;
            GUI.matrix = Matrix4x4.identity;
        }
    }
}
