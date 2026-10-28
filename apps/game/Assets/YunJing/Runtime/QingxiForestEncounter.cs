using System;
using System.Linq;
using QingxiWorld;
using UnityEngine;
using UnityEngine.InputSystem;

namespace YunJing
{
    // Plays Johnnnny0823's forest rabbit encounter (A01-A12) inside the Qingxi novice village.
    // This transform is the zone origin: rule coordinates (x, z) are its local ground plane.
    // The CharacterController walks the player; the rules only add dodge and knockback displacement,
    // judge every hit and drive the rabbit. Nothing here writes inventory or calls the API.
    public sealed class QingxiForestEncounter : MonoBehaviour
    {
        public TextAsset zoneData;
        public QingxiFirstPerson walker;
        public Transform rabbit;
        public Animation rabbitAnimation;
        public LineRenderer chargeLane;
        public GameObject dummyIntact, dummyWorn;
        public string style = "sword";
        public float activeRadius = 15f;

        QingxiForestEncounterRules rules;
        QingxiAbcZoneData.Platform platform;
        CharacterController body;
        double accumulator;
        float messageUntil;
        bool climbed;

        public bool PlayerInside { get; private set; }
        public bool Climbed => climbed;
        public string Message { get; private set; } = "";
        public QingxiForestEncounterRules Rules => rules;
        public event Action Changed;

        static readonly string[] StateText = { "idle", "洞裡安靜", "alert", "警戒：豎耳、踏地。躲到石後擋住視線，或站穩準備",
            "windup", "預備：壓低後蹬。往側面閃避（C），或面向牠按住格擋（K／右鍵）", "charge", "衝刺！方向已鎖定",
            "stagger", "硬直：破綻！靠近出手（J／左鍵），Q 試招", "retreat", "撤退回洞" };
        static readonly (string type, string text)[] RetreatText = { ("safe-point", "你回到安全點，山兔退回洞裡"), ("left-area", "你離開了遭遇範圍，山兔回洞"),
            ("lost-sight", "山兔看不見你了，回洞去"), ("disconnect", "畫面中斷：山兔脫離遭遇，沒有扣血"), ("defeated", "山兔被驅離"), ("player-down", "山兔退開了") };

        public string StateLabel => rules == null ? "" : Lookup(StateText, rules.rabbit.state);
        static string Lookup(string[] pairs, string key) { for (int i = 0; i + 1 < pairs.Length; i += 2) if (pairs[i] == key) return pairs[i + 1]; return key; }

        void Start()
        {
            var data = QingxiAbcZoneData.Parse(zoneData.text);
            platform = data.forest.platform;
            rules = new QingxiForestEncounterRules(data.ToRulesWorld(), style);
            if (walker == null) walker = QingxiFirstPerson.Current;
            if (walker != null) body = walker.GetComponent<CharacterController>();
            if (chargeLane != null) chargeLane.enabled = false;
            SetDummyWorn(false);
        }

        Vector2 Local(Vector3 world) { var l = transform.InverseTransformPoint(world); return new Vector2(l.x, l.z); }

        void Update()
        {
            if (rules == null || walker == null) return;
            var local = Local(walker.transform.position);
            var burrow = new Vector2((float)rules.world.burrow.x, (float)rules.world.burrow.z);
            var safe = new Vector2((float)rules.world.safe.x, (float)rules.world.safe.z);
            bool inside = Vector2.Distance(local, burrow) < activeRadius || Vector2.Distance(local, safe) < 4f;
            if (inside != PlayerInside) { PlayerInside = inside; Say(inside ? "進入林地：沿兔徑往凹地走，留意動靜" : "離開林地遭遇範圍"); }
            if (inside && !climbed) ReadInput();

            accumulator += Mathf.Min(Time.deltaTime, .1f);
            while (accumulator >= rules.P.dt)
            {
                accumulator -= rules.P.dt;
                var before = Local(walker.transform.position);
                if (!climbed) { rules.player.x = before.x; rules.player.z = before.y; }
                rules.Face((walker.transform.eulerAngles.y - transform.eulerAngles.y) * Mathf.Deg2Rad);
                rules.Step(rules.P.dt);
                // Dodge dashes and charge knockback are the only displacement the rules add.
                var moved = new Vector3((float)rules.player.x - before.x, 0, (float)rules.player.z - before.y);
                if (!climbed && moved.sqrMagnitude > 1e-8f && body != null && body.enabled) body.Move(transform.TransformVector(moved));
            }
            foreach (var e in rules.DrainEvents()) OnEvent(e);
            UpdateRabbit();
        }

        void ReadInput()
        {
            var kb = Keyboard.current; var mouse = Mouse.current; if (kb == null) return;
            bool locked = Cursor.lockState == CursorLockMode.Locked;
            if (kb.rKey.wasPressedThisFrame) { ReturnToSafePoint(); return; }
            bool blockHeld = kb.kKey.isPressed || (locked && mouse != null && mouse.rightButton.isPressed);
            if (blockHeld != rules.player.blocking) rules.SetBlock(blockHeld);
            if (kb.jKey.wasPressedThisFrame || (locked && mouse != null && mouse.leftButton.wasPressedThisFrame)) rules.Attack("basic");
            if (kb.qKey.wasPressedThisFrame) rules.Attack("technique");
            if (kb.cKey.wasPressedThisFrame || kb.leftCtrlKey.wasPressedThisFrame)
            {
                var input = new Vector3((kb.dKey.isPressed ? 1 : 0) - (kb.aKey.isPressed ? 1 : 0), 0, (kb.wKey.isPressed ? 1 : 0) - (kb.sKey.isPressed ? 1 : 0));
                var dir = transform.InverseTransformDirection(walker.transform.TransformDirection(input));
                rules.Move(dir.x, dir.z);
                rules.Dodge();
                rules.Move(0, 0);
            }
        }

        void OnApplicationFocus(bool focused) { if (!focused && rules != null) rules.Disconnect(); }

        void OnEvent(QingxiForestEncounterRules.Event e)
        {
            switch (e.type)
            {
                case "state": if (e.state != "idle") Say(StateLabel); break;
                case "dodged": Say("閃過了！"); break;
                case "parry": Say(style == "body" ? "穩架！精準格擋，兔子失衡更久" : "精準格擋！"); break;
                case "blocked": Say("擋下衝撞"); break;
                case "player-hit": Say($"被撞了（{e.reason}）· 氣血 {Mathf.Max(0, e.hp)}/{rules.P.playerHp}"); break;
                case "downed": Say("倒地了。不損失任何東西，回安全點重來"); Invoke(nameof(ReturnToSafePoint), 1.2f); break;
                case "whiff": Say("落空：" + e.reason); break;
                case "rabbit-hit": Say(e.kind == "technique" ? $"看破綻！造成 2 點 · 山兔剩 {e.hp}" : $"命中 · 山兔剩 {e.hp}"); break;
                case "won": Say("山兔被驅離。本機演練不發掉落；正式掉落需區域程序與服務端結算"); break;
                case "guard-broken": Say("連按格擋：架勢散亂 1.2 秒"); break;
                case "dummy-hit": Say($"藤靶 {e.total} 點" + (e.worn ? "，外皮破損" : "")); if (e.worn) SetDummyWorn(true); break;
                case "retreat": var r = RetreatText.FirstOrDefault(x => x.type == e.reason); if (r.text != null && e.reason != "defeated") Say(r.text); break;
            }
        }

        public void ReturnToSafePoint()
        {
            CancelInvoke(nameof(ReturnToSafePoint));
            if (climbed) SetClimbed(false);
            var spot = rules.world.respawn ?? rules.world.safe;
            Place(transform.TransformPoint(new Vector3((float)spot.x, 0, (float)spot.z)));
            rules.ResetAtSafePoint();
            SetDummyWorn(false);
            Say("回到避雨龕（安全點）。山兔不會追到這裡");
        }

        // A10 watch platform: a safe vantage point, no movement until climbing down.
        public bool NearLadder(Vector3 world) => platform != null && Vector2.Distance(Local(world), new Vector2(platform.ladder.x, platform.ladder.z)) < 1.6f || climbed;

        public string ToggleClimb() { SetClimbed(!climbed); return climbed ? "爬上觀察台：俯瞰兔徑與凹地，山兔碰不到你（F 下來）" : "回到地面"; }

        void SetClimbed(bool on)
        {
            climbed = on;
            rules.world.safeZones.Clear();
            if (on)
            {
                rules.world.safeZones.Add(new QingxiForestEncounterRules.Circle(platform.x, platform.z, 1.2f));
                rules.player.x = platform.x; rules.player.z = platform.z;
                Place(transform.TransformPoint(new Vector3(platform.x, platform.deck, platform.z)));
            }
            else Place(transform.TransformPoint(new Vector3(platform.ladder.x + .4f, 0, platform.ladder.z)));
            if (body != null) body.enabled = !on;
            Changed?.Invoke();
        }

        void Place(Vector3 world)
        {
            if (body == null) return;
            bool was = body.enabled; body.enabled = false;
            walker.transform.position = Ground(world) + Vector3.up * .05f;
            body.enabled = was && !climbed;
        }

        Vector3 Ground(Vector3 world)
        {
            var hits = Physics.RaycastAll(world + Vector3.up * 4f, Vector3.down, 12f, ~0, QueryTriggerInteraction.Ignore)
                .Where(h => walker == null || !h.collider.transform.IsChildOf(walker.transform)).OrderBy(h => h.distance).ToArray();
            return hits.Length > 0 ? hits[0].point : world;
        }

        void UpdateRabbit()
        {
            if (rabbit == null) return;
            var r = rules.rabbit;
            var pos = Ground(transform.TransformPoint(new Vector3((float)r.x, 0, (float)r.z)));
            if (r.state == "idle") pos += Vector3.down * .12f;   // tucked into the burrow mouth
            rabbit.position = pos;
            rabbit.rotation = transform.rotation * Quaternion.Euler(0, (float)r.heading * Mathf.Rad2Deg, 0);
            rabbit.localScale = new Vector3(1, r.state == "windup" ? .82f : 1, 1);
            if (chargeLane != null)
            {
                bool show = r.state == "windup" || r.state == "charge";
                chargeLane.enabled = show;
                if (show)
                {
                    var dir = rabbit.forward; var start = pos + Vector3.up * .05f;
                    chargeLane.SetPosition(0, start); chargeLane.SetPosition(1, start + dir * (float)rules.P.chargeMax);
                }
            }
            if (rabbitAnimation != null)
            {
                var clip = r.state == "charge" ? "Rabbit_Hop" : r.state == "stagger" ? "Rabbit_Hit" : r.state == "retreat" ? "Rabbit_Flee" : "Rabbit_Idle";
                if (rabbitAnimation.GetClip(clip) != null && !rabbitAnimation.IsPlaying(clip)) rabbitAnimation.CrossFade(clip, .12f);
            }
        }

        void SetDummyWorn(bool worn)
        {
            if (dummyIntact != null) dummyIntact.SetActive(!worn);
            if (dummyWorn != null) dummyWorn.SetActive(worn);
        }

        void Say(string message) { Message = message; messageUntil = Time.time + 4f; Changed?.Invoke(); }
        public bool MessageFresh => Time.time < messageUntil;
    }
}
