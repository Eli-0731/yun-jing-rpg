using System;
using System.Collections.Generic;
using System.Linq;

namespace YunJing
{
    // C# port of tools/qingxi-encounter-a/encounter.mjs (Johnnnny0823's forest rabbit encounter rules).
    // Pure and fixed-step: no Unity objects, no network, no storage. Ground plane is (x, z) in metres,
    // heading 0 = +z and positive towards +x. Results are local rehearsal feedback only; real drops still
    // come from the region process and POST /v1/internal/hunt/death (tools/qingxi-encounter-a/CONTRACT.md).
    // Keep this file in step with encounter.mjs; QingxiForestEncounterSmoke replays the JS event log.
    public sealed class QingxiForestEncounterRules
    {
        public const string Notice = "本機展示・不發正式掉落或靈石";

        public sealed class Params
        {
            public double dt = 1.0 / 60;
            public double playerRadius = .35, playerSpeed = 3.2; public int playerHp = 3;
            public double dodgeDistance = 2.6, dodgeTime = .32, dodgeIframes = .26, dodgeCooldown = .75;
            public double attackRange = 1.55, attackArc = Math.PI * .45, attackWindup = .18, attackRecover = .32;
            public double blockArc = Math.PI * .6, blockPerfect = .18, blockSpamWindow = 1.5, blockBreakTime = 1.2; public int blockSpamLimit = 4;
            public double rabbitRadius = .38; public int rabbitHp = 3;
            public double alertRadius = 7.5, engageRadius = 5, leashRadius = 13, alertTime = 1.1, windup = .85,
                chargeSpeed = 9.5, chargeMax = 5, staggerTime = 1.3, blockedStagger = 1.9, parryStagger = 2.6,
                wallStagger = 2.2, retreatSpeed = 5.5, cooldownAfterRetreat = 2.5;
            public double safeRadius = 1.4;
        }

        [Serializable] public struct Circle { public double x, z, r; public int wearAt; public Circle(double x, double z, double r, int wearAt = 0) { this.x = x; this.z = z; this.r = r; this.wearAt = wearAt; } }

        public sealed class World
        {
            public Circle burrow, safe, start; public Circle? respawn;
            public List<Circle> cover = new List<Circle>(), walls = new List<Circle>(), safeZones = new List<Circle>(), dummies = new List<Circle>();
        }

        public sealed class Event
        {
            public double t; public string type, reason, kind, state, cause; public int hp = -1, dmg, index = -1, total; public double seconds, windup; public bool worn;
            public override string ToString() => type + (state != null ? ":" + state : "") + (reason != null ? ":" + reason : "") + (kind != null ? ":" + kind : "") + (hp >= 0 ? ":hp" + hp : "");
        }

        public sealed class PlayerState
        {
            public double x, z, heading, moveX, moveZ, dodgeT, dodgeCd, blockSince = -1, guardBroken, attackT, dodgeDirX, dodgeDirZ;
            public int hp; public bool blocking, attackHit, downed; public string attackKind; public List<double> blockPresses = new List<double>();
        }

        public sealed class RabbitState
        {
            public double x, z, heading, t, seen, dir, travelled, cooldown, stagger, windupTime; public int hp; public string state = "idle"; public bool hitThisCharge;
        }

        public sealed class Stats { public int dodged, blocked, parried, hitsTaken, hitsLanded, whiffs, retreats; }

        public readonly Params P; public World world; public string Style { get; private set; }
        public double time; public PlayerState player; public RabbitState rabbit; public Stats stats;
        public string outcome;   // "won" | "downed" | null
        public List<int> dummyHits = new List<int>();
        List<Event> events = new List<Event>();

        public QingxiForestEncounterRules(World world, string style = "sword", Params parameters = null)
        {
            if (style != "sword" && style != "body") throw new ArgumentException("style must be sword or body (qi is next version)");
            P = parameters ?? new Params(); this.world = world; Style = style; Init(world.start);
        }

        void Init(Circle start)
        {
            time = 0; events = new List<Event>(); outcome = null; dummyHits = new List<int>(); stats = new Stats();
            player = new PlayerState { x = start.x, z = start.z, heading = 0, hp = P.playerHp };
            rabbit = new RabbitState { x = world.burrow.x, z = world.burrow.z, heading = Math.PI, hp = P.rabbitHp, state = "idle" };
        }

        static double Len(double x, double z) => Math.Sqrt(x * x + z * z);
        static double AngleDiff(double a, double b) => Math.Atan2(Math.Sin(a - b), Math.Cos(a - b));
        static double HeadingTo(double fx, double fz, double tx, double tz) => Math.Atan2(tx - fx, tz - fz);

        // ------------------------------------------------------------ inputs (all validated by state)
        public void Move(double x, double z) { var l = Len(x, z); player.moveX = l > 1 ? x / l : x; player.moveZ = l > 1 ? z / l : z; }
        public void Face(double heading) { if (!double.IsNaN(heading) && !double.IsInfinity(heading)) player.heading = heading; }

        public bool Dodge()
        {
            var p = player;
            if (outcome != null || p.dodgeT > 0 || p.dodgeCd > 0 || p.attackT > 0) return false;
            double dx = p.moveX, dz = p.moveZ;
            if (dx == 0 && dz == 0) { dx = -Math.Sin(p.heading); dz = -Math.Cos(p.heading); } // backstep when standing still
            var l = Len(dx, dz);
            p.dodgeDirX = dx / l; p.dodgeDirZ = dz / l;
            p.dodgeT = P.dodgeTime;
            p.dodgeCd = P.dodgeCooldown + p.dodgeT;
            p.blocking = false;
            Emit("dodge");
            return true;
        }

        public bool SetBlock(bool on)
        {
            var p = player;
            if (outcome != null) return false;
            if (on && !p.blocking)
            {
                p.blockPresses = p.blockPresses.Where(t => time - t < P.blockSpamWindow).ToList();
                p.blockPresses.Add(time);
                if (p.blockPresses.Count > P.blockSpamLimit)   // mashing block breaks the stance for a moment
                {
                    p.guardBroken = P.blockBreakTime; p.blockPresses.Clear(); p.blocking = false;
                    Emit("guard-broken");
                    return false;
                }
                if (p.guardBroken > 0 || p.dodgeT > 0 || p.attackT > 0) return false;
                p.blocking = true; p.blockSince = time;
                return true;
            }
            if (!on) p.blocking = false;
            return false;
        }

        public bool Attack(string kind = "basic")
        {
            var p = player;
            if (outcome != null || p.attackT > 0 || p.dodgeT > 0) return false;
            if (kind == "technique" && Style != "sword") kind = "basic"; // body style's technique is the parry
            p.attackT = P.attackWindup + P.attackRecover; p.attackKind = kind; p.attackHit = false; p.blocking = false;
            Emit("attack", e => e.kind = kind);
            return true;
        }

        /** Player paused or the window lost focus: the encounter cannot continue fairly, so the rabbit disengages. */
        public void Disconnect()
        {
            var s = rabbit.state;
            if (s == "alert" || s == "windup" || s == "charge" || s == "stagger") Retreat("disconnect");
            player.moveX = player.moveZ = 0; player.blocking = false;
        }

        // ------------------------------------------------------------ simulation
        public void Step(double seconds)
        {
            var n = Math.Max(0, (int)Math.Round(seconds / P.dt));
            for (int i = 0; i < n; i++) Tick(P.dt);
        }

        void Tick(double dt) { time += dt; TickPlayer(dt); TickRabbit(dt); }

        void TickPlayer(double dt)
        {
            var p = player;
            p.dodgeCd = Math.Max(0, p.dodgeCd - dt);
            p.guardBroken = Math.Max(0, p.guardBroken - dt);
            if (outcome == "downed") return;
            double vx = p.moveX * P.playerSpeed, vz = p.moveZ * P.playerSpeed;
            if (p.blocking || p.attackT > 0) { vx *= .35; vz *= .35; }
            if (p.dodgeT > 0)
            {
                p.dodgeT = Math.Max(0, p.dodgeT - dt);
                var s = P.dodgeDistance / P.dodgeTime;
                vx = p.dodgeDirX * s; vz = p.dodgeDirZ * s;
            }
            Walk(ref p.x, ref p.z, vx * dt, vz * dt, P.playerRadius);
            if (p.attackT > 0)
            {
                var before = p.attackT;
                p.attackT = Math.Max(0, p.attackT - dt);
                if (before > P.attackRecover && p.attackT <= P.attackRecover) ResolveAttack();   // the swing lands after windup
            }
        }

        void Walk(ref double x, ref double z, double dx, double dz, double r)
        {
            double ox = x, oz = z, nx = x + dx, nz = z + dz;
            if (!world.walls.Any(w => Len(nx - w.x, oz - w.z) < w.r + r)) ox = nx;
            if (!world.walls.Any(w => Len(ox - w.x, nz - w.z) < w.r + r)) oz = nz;
            x = ox; z = oz;
        }

        bool Sees()
        {
            var p = player; var r = rabbit;
            var d = Len(p.x - r.x, p.z - r.z);
            if (d > P.alertRadius) return false;
            // sight line blocked by any cover circle between rabbit and player
            foreach (var c in world.cover)
            {
                double ax = p.x - r.x, az = p.z - r.z, dd = d * d;
                var t = Math.Max(0, Math.Min(1, ((c.x - r.x) * ax + (c.z - r.z) * az) / (dd == 0 ? 1 : dd)));
                if (Len(r.x + ax * t - c.x, r.z + az * t - c.z) < c.r) return false;
            }
            return true;
        }

        void TickRabbit(double dt)
        {
            var r = rabbit; var p = player;
            if (outcome == "won" && r.state != "retreat") return;
            r.t += dt;
            var dPlayer = Len(p.x - r.x, p.z - r.z);
            var atSafe = InSafeZone();
            var leashed = Len(p.x - world.burrow.x, p.z - world.burrow.z) > P.leashRadius;
            switch (r.state)
            {
                case "idle":
                    r.cooldown = Math.Max(0, r.cooldown - dt);
                    if (r.cooldown == 0 && !atSafe && Sees() && outcome == null) Enter("alert");
                    break;
                case "alert":   // ears up, faces the player, thumps the ground: the first tell
                    r.heading = HeadingTo(r.x, r.z, p.x, p.z);
                    if (atSafe || leashed) { Retreat(atSafe ? "safe-point" : "left-area"); break; }
                    if (!Sees()) { r.seen = Math.Max(0, r.seen - dt * 2); if (r.t > 3 && r.seen == 0) Retreat("lost-sight"); break; }
                    r.seen += dt;
                    if (dPlayer < P.engageRadius && r.seen >= P.alertTime) Enter("windup");
                    break;
                case "windup":  // crouch + scrape: the readable warning before any hit can happen
                    r.heading = HeadingTo(r.x, r.z, p.x, p.z);
                    if (atSafe || leashed) { Retreat(atSafe ? "safe-point" : "left-area"); break; }
                    if (r.t >= r.windupTime)
                    {
                        r.dir = r.heading;  // direction locks at the end of windup: side-steps after this make it miss
                        r.travelled = 0; r.hitThisCharge = false;
                        Enter("charge");
                    }
                    break;
                case "charge":
                {
                    var step = P.chargeSpeed * dt;
                    double nx = r.x + Math.Sin(r.dir) * step, nz = r.z + Math.Cos(r.dir) * step;
                    if (world.walls.Any(w => Len(nx - w.x, nz - w.z) < w.r + P.rabbitRadius)) { Stagger(P.wallStagger, "wall"); break; }
                    r.x = nx; r.z = nz; r.travelled += step;
                    if (!r.hitThisCharge && Len(p.x - r.x, p.z - r.z) < P.rabbitRadius + P.playerRadius) ResolveImpact();
                    if (r.state == "charge" && r.travelled >= P.chargeMax) Stagger(P.staggerTime, "overrun");
                    break;
                }
                case "stagger": // the opening: attacks here land
                    if (r.t >= r.stagger)
                    {
                        if (atSafe || leashed) Retreat(atSafe ? "safe-point" : "left-area");
                        else Enter("alert");
                    }
                    break;
                case "retreat":
                {
                    double bx = world.burrow.x - r.x, bz = world.burrow.z - r.z, d = Len(bx, bz);
                    if (d < .2)
                    {
                        r.x = world.burrow.x; r.z = world.burrow.z; r.cooldown = P.cooldownAfterRetreat;
                        if (r.hp > 0) r.hp = Math.Max(r.hp, 1);
                        Enter("idle");
                    }
                    else
                    {
                        r.heading = Math.Atan2(bx, bz);
                        var s = Math.Min(d, P.retreatSpeed * dt);
                        r.x += bx / d * s; r.z += bz / d * s;
                    }
                    break;
                }
            }
        }

        void ResolveImpact()
        {
            var r = rabbit; var p = player;
            r.hitThisCharge = true;
            if (p.dodgeT > 0 && p.dodgeT > P.dodgeTime - P.dodgeIframes)
            {
                stats.dodged++; Emit("dodged"); return;           // passes through during i-frames
            }
            var facing = Math.Abs(AngleDiff(p.heading, HeadingTo(p.x, p.z, r.x, r.z))) < P.blockArc / 2;
            if (p.blocking && facing)
            {
                var perfect = time - p.blockSince <= P.blockPerfect;
                if (perfect) { stats.parried++; Emit("parry"); Stagger(Style == "body" ? P.parryStagger : P.blockedStagger, "parry"); }
                else { stats.blocked++; Emit("blocked"); Stagger(P.blockedStagger * (Style == "body" ? 1 : .75), "blocked"); }
                return;
            }
            p.hp -= 1; stats.hitsTaken++;
            var why = p.blocking ? "防禦方向不對" : p.dodgeT > 0 ? "閃得太晚" : "正面被撞";
            Emit("player-hit", e => { e.hp = p.hp; e.reason = why; });
            // knockback along the charge direction
            Walk(ref p.x, ref p.z, Math.Sin(r.dir) * .8, Math.Cos(r.dir) * .8, P.playerRadius);
            if (p.hp <= 0) { p.downed = true; outcome = "downed"; Emit("downed"); Retreat("player-down"); }
        }

        void ResolveAttack()
        {
            var p = player; var r = rabbit;
            // practice dummies (A12) take any strike that is in range and aimed: warm-up before the real thing
            for (int i = 0; i < world.dummies.Count; i++)
            {
                var dm = world.dummies[i];
                var dd = Len(dm.x - p.x, dm.z - p.z);
                if (dd <= P.attackRange + dm.r && Math.Abs(AngleDiff(p.heading, HeadingTo(p.x, p.z, dm.x, dm.z))) < P.attackArc / 2)
                {
                    while (dummyHits.Count <= i) dummyHits.Add(0);
                    dummyHits[i] += p.attackKind == "technique" ? 2 : 1;
                    var total = dummyHits[i]; var kind = p.attackKind; var wearAt = dm.wearAt > 0 ? dm.wearAt : 8;
                    Emit("dummy-hit", e => { e.index = i; e.total = total; e.worn = total >= wearAt; e.kind = kind; });
                    return;
                }
            }
            var d = Len(r.x - p.x, r.z - p.z);
            var inArc = Math.Abs(AngleDiff(p.heading, HeadingTo(p.x, p.z, r.x, r.z))) < P.attackArc / 2;
            if (d > P.attackRange + P.rabbitRadius || !inArc || r.state == "idle" || r.state == "retreat")
            {
                stats.whiffs++;
                var why = d > P.attackRange + P.rabbitRadius ? "距離太遠" : !inArc ? "沒有對準" : "目標已退";
                Emit("whiff", e => e.reason = why); return;
            }
            if (r.state != "stagger")   // outside the opening the rabbit sidesteps: timing matters, not animation
            {
                stats.whiffs++; Emit("whiff", e => e.reason = "還不是破綻，兔子躲開了");
                if (r.state == "alert") Enter("windup");
                return;
            }
            var dmg = p.attackKind == "technique" ? 2 : 1;
            r.hp = Math.Max(0, r.hp - dmg); stats.hitsLanded++;
            var hpLeft = r.hp; var attackKind = p.attackKind;
            Emit("rabbit-hit", e => { e.dmg = dmg; e.hp = hpLeft; e.kind = attackKind; });
            if (r.hp <= 0) { outcome = "won"; Emit("won"); Retreat("defeated"); }
        }

        void Stagger(double seconds, string cause) { rabbit.stagger = seconds; Enter("stagger"); Emit("stagger", e => { e.cause = cause; e.seconds = seconds; }); }

        void Retreat(string reason) { stats.retreats++; Enter("retreat"); Emit("retreat", e => e.reason = reason); }

        void Enter(string state)
        {
            var r = rabbit;
            r.state = state; r.t = 0;
            if (state == "alert") r.seen = 0;
            // a hurt rabbit gets hasty: shorter windup, but never shorter than a fair reaction window
            if (state == "windup") r.windupTime = r.hp <= 1 ? Math.Max(.6, P.windup * .75) : P.windup;
            var w = r.windupTime;
            Emit("state", e => { e.state = state; if (state == "windup") e.windup = w; });
        }

        void Emit(string type, Action<Event> fill = null)
        {
            var e = new Event { t = Math.Round(time * 1000) / 1000, type = type };
            fill?.Invoke(e); events.Add(e);
        }

        /** On the safe point (A09) or any extra safe zone such as the watch platform (A10). */
        public bool InSafeZone()
        {
            var p = player;
            if (Len(p.x - world.safe.x, p.z - world.safe.z) < P.safeRadius) return true;
            return world.safeZones.Any(z => Len(p.x - z.x, p.z - z.z) < z.r);
        }

        public List<Event> DrainEvents() { var e = events; events = new List<Event>(); return e; }

        /** Restart from the safe point (or world.respawn); nothing carries over (no permanent loss in the rehearsal). */
        public void ResetAtSafePoint() { Init(world.respawn ?? world.safe); Emit("reset"); }

        public double WindupLeft => rabbit.state == "windup" ? rabbit.windupTime - rabbit.t : 0;
        public double OpeningLeft => rabbit.state == "stagger" ? rabbit.stagger - rabbit.t : 0;
    }
}
