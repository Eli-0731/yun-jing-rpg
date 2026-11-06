using System;
using System.Collections.Generic;

namespace YunJing.BasicCombat
{
    // C# port of tools/basic-combat/basic-combat-rules.mjs (Johnnnny0823). Pure logic with the same fixed step, same order and the
    // same numbers from packages/content/basic-combat-v1.json; QingxiBasicCombatSmoke replays the runs parity.mjs records.
    public sealed class QingxiBasicCombatRules
    {
        public const double Step = 1.0 / 120;
        public const string HitEvent = "combat.hit";

        [Serializable] public sealed class Attack { public string id; public double windup, active, recovery, chainFrom, damage, range, arc, lunge, hitStop, shake, knockback; }
        [Serializable] public sealed class Heavy { public string id; public double chargeMin, chargeMax, windup, active, recovery, damageMin, damageMax, knockbackMin, knockbackMax, range, arc, lunge, cooldown, hitStop, shake; }
        [Serializable] public sealed class Dodge { public double distance, duration, iframes, cooldown; public bool cancelsRecovery; }
        [Serializable] public sealed class Facing { public double autoFaceRadius; }
        [Serializable] public sealed class Feedback { public double flashSeconds; public int debris, debrisHeavy; }
        [Serializable] public sealed class Touch { public float minButtonPx; }
        [Serializable]
        public sealed class Content
        {
            public int version;
            public Attack[] light;
            public Heavy heavy;
            public Dodge dodge;
            public Facing facing;
            public Feedback feedback;
            public Touch touch;
        }

        public struct Target { public string id; public double x, z, radius; public bool alive; }
        public struct Input { public bool attack, dodge, heavyHeld; public double moveX, moveZ; }

        public sealed class Event
        {
            public string type, attackId, targetId, kind, input, result;
            public double t, damage, knockback, dirX, dirZ, hitStop, shake, power;
            public int swing;
            public bool heavy, cancelled;
        }

        readonly Content c;
        public double x, z, yaw, time;
        double accumulator, lastNow = double.NaN, stateAt, chargeFrom = -1, heavyReadyAt, dodgeReadyAt, iFrameUntil = -1, dodgeDirX, dodgeDirZ = 1;
        public string state = "idle";
        public string phase;          // windup | active | recovery | null
        public int combo, swing;
        public double heavyPower;
        Attack light;                 // current light spec, or null during heavy
        readonly HashSet<string> hitSet = new HashSet<string>();
        public readonly List<Event> events = new List<Event>();

        public QingxiBasicCombatRules(Content content, double x = 0, double z = 0, double yaw = 0)
        {
            c = content;
            this.x = x; this.z = z; this.yaw = yaw;
        }

        public double Elapsed => time - stateAt;
        public bool Invulnerable => time < iFrameUntil;
        public double HeavyCooldown => Math.Max(0, heavyReadyAt - time);
        public double DodgeCooldown => Math.Max(0, dodgeReadyAt - time);
        public double Charge => state == "charging" ? Math.Min(1, (time - chargeFrom) / c.heavy.chargeMax) : 0;
        public bool Busy => state == "light" || state == "heavy" || state == "dodge";
        public string AttackId => state == "heavy" ? c.heavy.id : light?.id;
        public Content Data => c;

        double Windup => state == "heavy" ? c.heavy.windup : light.windup;
        double Active => state == "heavy" ? c.heavy.active : light.active;
        double Recovery => state == "heavy" ? c.heavy.recovery : light.recovery;
        double Lunge => state == "heavy" ? c.heavy.lunge : light.lunge;

        void Enter(string s) { state = s; stateAt = time; }
        Event Emit(string type) { var e = new Event { type = type, t = Math.Round(time * 1e4) / 1e4 }; events.Add(e); return e; }

        static double Wrap(double a) { while (a > Math.PI) a -= 2 * Math.PI; while (a < -Math.PI) a += 2 * Math.PI; return a; }

        /// <summary>Advance to now in fixed steps, then apply this frame's presses. Returns the events raised by this call.</summary>
        public List<Event> Update(double now, Input input, IList<Target> targets)
        {
            if (double.IsNaN(lastNow)) lastNow = now;
            accumulator += Math.Max(0, now - lastNow);
            lastNow = now;
            int start = events.Count;
            var held = input; held.attack = false; held.dodge = false;
            while (accumulator >= Step - 1e-9)
            {
                accumulator -= Step;
                StepOnce(Step, held, targets);
            }
            if (input.dodge) TryDodge(input.moveX, input.moveZ);
            if (input.attack) TryLight(targets, input.moveX, input.moveZ);
            if (input.heavyHeld && state == "idle") TryCharge();
            if (!input.heavyHeld && state == "charging") ReleaseCharge(targets, input.moveX, input.moveZ);
            return events.GetRange(start, events.Count - start);
        }

        /// <summary>The engine owns walking; it hands combat the fighter's position and facing when not mid-move.</summary>
        public void Sync(double px, double pz, double pyaw)
        {
            x = px; z = pz;
            if (!Busy) yaw = pyaw;
        }

        bool TryLight(IList<Target> targets, double mx, double mz)
        {
            if (state == "idle") return StartLight(0, targets, mx, mz);
            if (state == "light" && phase == "recovery")
            {
                double since = Elapsed - light.windup - light.active;
                if (since >= light.chainFrom && combo < c.light.Length - 1) return StartLight(combo + 1, targets, mx, mz);
            }
            var e = Emit("input.ignored"); e.input = "attack";
            return false;
        }

        bool StartLight(int index, IList<Target> targets, double mx, double mz)
        {
            combo = index;
            light = c.light[index];
            BeginSwing("light", targets, mx, mz);
            return true;
        }

        bool TryCharge()
        {
            if (time < heavyReadyAt) { Emit("heavy.cooldown"); return false; }
            chargeFrom = time;
            Enter("charging");
            Emit("heavy.charge");
            return true;
        }

        bool ReleaseCharge(IList<Target> targets, double mx, double mz)
        {
            double held = time - chargeFrom;
            if (held < c.heavy.chargeMin) { Enter("idle"); Emit("heavy.cancelled"); return false; }
            heavyPower = Math.Min(1, (held - c.heavy.chargeMin) / (c.heavy.chargeMax - c.heavy.chargeMin));
            light = null;
            heavyReadyAt = time + c.heavy.cooldown;
            BeginSwing("heavy", targets, mx, mz);
            return true;
        }

        void BeginSwing(string kind, IList<Target> targets, double mx, double mz)
        {
            swing++;
            hitSet.Clear();
            phase = "windup";
            Enter(kind);
            int best = Nearest(targets);
            if (best >= 0) yaw = Math.Atan2(targets[best].x - x, targets[best].z - z);
            else if (Math.Sqrt(mx * mx + mz * mz) > .1) yaw = Math.Atan2(mx, mz);
            var e = Emit("attack.start");
            e.attackId = AttackId; e.kind = kind; e.swing = swing; e.targetId = null; e.power = kind == "heavy" ? heavyPower : 0;
        }

        int Nearest(IList<Target> targets)
        {
            int best = -1;
            double bestD = c.facing.autoFaceRadius + 1e-9;
            for (int i = 0; i < targets.Count; i++)
            {
                if (!targets[i].alive) continue;
                double d = Math.Sqrt((targets[i].x - x) * (targets[i].x - x) + (targets[i].z - z) * (targets[i].z - z));
                if (d < bestD) { best = i; bestD = d; }   // ties keep the first listed
            }
            return best;
        }

        bool TryDodge(double mx, double mz)
        {
            bool recovering = (state == "light" || state == "heavy") && phase == "recovery" && c.dodge.cancelsRecovery;
            bool free = state == "idle" || state == "charging" || recovering;
            if (!free || time < dodgeReadyAt) { var e = Emit("input.ignored"); e.input = "dodge"; return false; }
            double l = Math.Sqrt(mx * mx + mz * mz);
            if (l > .1) { dodgeDirX = mx / l; dodgeDirZ = mz / l; }
            else { dodgeDirX = -Math.Sin(yaw); dodgeDirZ = -Math.Cos(yaw); }   // standing still: step back
            if (state == "charging") Emit("heavy.cancelled");
            light = null;
            phase = null;
            Enter("dodge");
            iFrameUntil = time + c.dodge.iframes;
            dodgeReadyAt = time + c.dodge.duration + c.dodge.cooldown;
            Emit("dodge.start").cancelled = recovering;
            return true;
        }

        /// <summary>Something tries to hurt the fighter; "dodged" while i-frames last, otherwise "hit".</summary>
        public string Receive(string source = "enemy")
        {
            var e = Emit("defend");
            e.result = Invulnerable ? "dodged" : "hit";
            e.input = source;
            return e.result;
        }

        /// <summary>World-space velocity the engine should add this frame (lunge in windup/active, dodge displacement).</summary>
        public void Velocity(out double vx, out double vz)
        {
            vx = vz = 0;
            if (state == "dodge")
            {
                double s = c.dodge.distance / c.dodge.duration;
                vx = dodgeDirX * s; vz = dodgeDirZ * s;
            }
            else if ((state == "light" || state == "heavy") && phase != "recovery" && Lunge > 0)
            {
                double s = Lunge / (Windup + Active);
                vx = Math.Sin(yaw) * s; vz = Math.Cos(yaw) * s;
            }
        }

        void StepOnce(double dt, Input input, IList<Target> targets)
        {
            time += dt;
            Velocity(out double vx, out double vz);
            x += vx * dt; z += vz * dt;
            if (state == "dodge" && Elapsed >= c.dodge.duration) { Enter("idle"); Emit("dodge.end"); }
            if (state == "charging" && time - chargeFrom >= c.heavy.chargeMax) ReleaseCharge(targets, input.moveX, input.moveZ);
            if (state != "light" && state != "heavy") return;
            double e = Elapsed;
            string p = e < Windup ? "windup" : e < Windup + Active ? "active" : e < Windup + Active + Recovery ? "recovery" : "done";
            if (p != phase)
            {
                phase = p;
                if (p == "done") { var id = AttackId; Enter("idle"); phase = null; Emit("attack.end").attackId = id; return; }
            }
            if (phase == "active") ResolveHits(targets);
        }

        void ResolveHits(IList<Target> targets)
        {
            bool heavy = state == "heavy";
            double range = heavy ? c.heavy.range : light.range, arc = heavy ? c.heavy.arc : light.arc;
            double fx = Math.Sin(yaw), fz = Math.Cos(yaw);
            foreach (var t in targets)
            {
                if (!t.alive || hitSet.Contains(t.id)) continue;
                double dx = t.x - x, dz = t.z - z, d = Math.Sqrt(dx * dx + dz * dz);
                if (d > range + t.radius) continue;
                double angle = d < 1e-6 ? 0 : Math.Abs(Wrap(Math.Atan2(dx, dz) - yaw)) * 180 / Math.PI;
                if (angle > arc / 2) continue;
                hitSet.Add(t.id);
                var e = Emit(HitEvent);
                e.targetId = t.id; e.attackId = AttackId; e.heavy = heavy; e.swing = swing;
                e.damage = heavy ? Math.Round(c.heavy.damageMin + (c.heavy.damageMax - c.heavy.damageMin) * heavyPower, MidpointRounding.AwayFromZero) : light.damage;
                e.knockback = heavy ? Math.Round((c.heavy.knockbackMin + (c.heavy.knockbackMax - c.heavy.knockbackMin) * heavyPower) * 1000) / 1000 : light.knockback;
                e.dirX = fx; e.dirZ = fz;
                e.hitStop = heavy ? c.heavy.hitStop : light.hitStop;
                e.shake = heavy ? c.heavy.shake : light.shake;
            }
        }
    }
}
