using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

namespace YunJing.CreekRepair
{
    // C# port of tools/creek-repair/rules.ts, data from packages/content/creek-repair-v1.json. Checked against
    // tests/fixtures/creek-repair-trace.json by the scene builder. Nothing can fail; a wrong piece only explains itself.
    [Serializable] public class CreekOption { public string piece, message; public int gapCm; public float[] from, to; }
    [Serializable] public class CreekWork { public string slot, piece, name; public CreekOption[] options; }
    [Serializable] public class CreekPatch { public string slot, piece, name, wrong, wrongMessage; }
    [Serializable] public class CreekPair { public string slot, piece; }
    [Serializable] public class CreekAqueduct { public string name, piece; public CreekPair[] slots; }
    [Serializable] public class CreekSpot { public string id, reveal; public float[] pos; public int slump; }
    [Serializable] public class CreekPile { public float plugLength; public string id, kind; public float[] pos, pull, stand; public int mass, stones; public float scale, channelWidth; public CreekSpot[] spots; }
    [Serializable] public class CreekNode { public string id, kind; public float[] pos; public float lengthM; }
    [Serializable] public class CreekMethod
    {
        public string label; public float waterWidthM; public int stone, channel;
        public CreekPair[] given; public CreekPile[] piles; public CreekWork[] work; public CreekPatch[] patches; public CreekAqueduct aqueduct; public CreekNode[] route;
        public bool HasAqueduct => aqueduct != null && !string.IsNullOrEmpty(aqueduct.name);
    }
    [Serializable] public class CreekMethods { public CreekMethod clear_silt, restore_channel, protect_nursery; }
    [Serializable] public class CreekSpade { public float minDragM, fullDragM, scoopMass, hurriedSeconds, hurriedKeep, slumpRadiusM, beatKeep; }
    [Serializable] public class CreekMudKind { public float minDragM, fullDragM, hurriedSeconds, followRate, wrongWayKeep, bladeSpeedMps, biteM, loadDrag; }
    [Serializable] public class CreekMud { public CreekMudKind soft, hard, weed; }
    [Serializable] public class CreekChant { public float cycleSeconds, yoAtSeconds, windowSeconds; }
    [Serializable] public class CreekFlow { public float wheelDegrees, speedMps; }
    [Serializable] public class CreekParty { public int minSize, maxSize; }
    [Serializable] public class CreekGate { public string id, field, label; public float[] pos; public float fieldM, planLevel; }
    [Serializable] public class CreekDistribution { public float villagerDelaySeconds, togetherWithin; public float[] levels; public CreekGate[] gates; }
    [Serializable] public class CreekContent
    {
        public string version; public CreekParty party; public CreekSpade spade; public CreekMud mud; public CreekChant chant; public CreekFlow flow; public CreekDistribution distribution; public CreekMethods methods;
        public CreekMethod Method(string id) => id == "clear_silt" ? methods.clear_silt : id == "restore_channel" ? methods.restore_channel : id == "protect_nursery" ? methods.protect_nursery : throw new ArgumentException(id);
    }

    [Serializable] public class CreekEntry { public string slot, piece; }
    [Serializable] public class CreekSilt { public string id; public double left; }
    [Serializable] public class CreekGateState { public string id; public double level, fill; }
    /// `by` is "villager" or a player's id, so a server can name real players later without new rules.
    [Serializable] public class CreekGateMove { public string gate, by; public double level; }
    [Serializable] public class CreekState
    {
        public string version, method; public int partySize;
        public List<CreekSilt> silt = new List<CreekSilt>(); public List<string> slumped = new List<string>(); public List<CreekEntry> placed = new List<CreekEntry>(), patches = new List<CreekEntry>();
        public bool aqueduct, done, together; public double wheelDegrees, flowM, idleSeconds; public string lastClosed = ""; public List<CreekGateState> gates = new List<CreekGateState>(); public List<CreekGateMove> gateLog = new List<CreekGateMove>();
        public List<string> reached = new List<string>(), fired = new List<string>(), events = new List<string>();
    }
    public struct CreekStep { public bool ok, onBeat; public string code, message; public int gapCm; public double moved; }

    public static class CreekRepairEvents
    {
        public const string WorkCompleted = "creek.workCompleted", FlowReached = "creek.flowReached", FlowCompleted = "creek.flowCompleted";
        public static event Action<string, string> Emitted;
        public static void Emit(string name, string json) => Emitted?.Invoke(name, json);
    }

    public sealed class CreekRepairSim
    {
        public readonly CreekContent content; public CreekState s;
        public CreekMethod M => content.Method(s.method);

        public CreekRepairSim(CreekContent content, string method, int partySize = 1)
        {
            if (partySize < content.party.minSize || partySize > content.party.maxSize) throw new ArgumentException("partySize " + partySize);
            this.content = content;
            s = new CreekState { version = content.version, method = method, partySize = partySize };
            foreach (var p in content.Method(method).piles) s.silt.Add(new CreekSilt { id = p.id, left = PileMass(p.mass) });
            foreach (var g in content.distribution.gates) s.gates.Add(new CreekGateState { id = g.id });
        }

        public CreekRepairSim(CreekContent content, string saved)
        {
            this.content = content; s = JsonUtility.FromJson<CreekState>(saved);
            if (s.version != content.version) throw new InvalidOperationException($"save is {s.version}, content is {content.version}");
            content.Method(s.method);
        }

        public string Save() => JsonUtility.ToJson(s);
        static CreekStep Fail(string code, string message, int gap = 0) => new CreekStep { ok = false, code = code, message = message, gapCm = gap };
        static CreekStep Okay(string code, string message, double moved = 0) => new CreekStep { ok = true, code = code, message = message, moved = moved };
        static string Of(List<CreekEntry> list, string slot) => list.FirstOrDefault(e => e.slot == slot)?.piece;

        public int PileMass(int mass) => mass * s.partySize;
        public double SiltLeft => s.silt.Sum(p => p.left);
        public double Left(string pile) => s.silt.First(p => p.id == pile).left;
        public string Placed(string slot) => Of(s.placed, slot);
        public string Patched(string slot) => Of(s.patches, slot);

        void Fire(string key, string name, string json)
        {
            if (s.fired.Contains(key)) return;
            s.fired.Add(key); s.events.Add(name + " " + json); CreekRepairEvents.Emit(name, json);
        }

        // ---- clear
        static double D(float v) => (double)(decimal)v;
        public CreekMudKind Mud(string kind) => kind == "hard" ? content.mud.hard : kind == "weed" ? content.mud.weed : content.mud.soft;
        public CreekPile Pile(string id) => M.piles.First(p => p.id == id);

        /// The chant keeps its own clock: true when `clock` falls near the 喲. Only ever a bonus.
        public bool IsOnBeat(double clock)
        {
            double cycle = D(content.chant.cycleSeconds), phase = ((clock % cycle) + cycle) % cycle, d = Math.Abs(phase - D(content.chant.yoAtSeconds));
            return Math.Min(d, cycle - d) <= D(content.chant.windowSeconds) + 1e-9;
        }

        /// The unspent weak spot under the spade, if there is one.
        public CreekSpot SpotAt(string pile, double[] at)
        {
            var p = M.piles.FirstOrDefault(x => x.id == pile);
            if (p == null || at == null) return null;
            return p.spots.FirstOrDefault(o => !Spent(pile, o) && Math.Sqrt(Math.Pow(D(o.pos[0]) - at[0], 2) + Math.Pow(D(o.pos[1]) - at[1], 2)) <= D(content.spade.slumpRadiusM));
        }
        public bool Spent(string pile, CreekSpot spot) => s.slumped.Contains(pile + ":" + spot.id);

        public CreekStep Scoop(string pile, double dragM, double seconds, double[] at = null, double[] dir = null, bool onBeat = false)
        {
            var sp = content.spade; var entry = s.silt.FirstOrDefault(p => p.id == pile); var data = M.piles.FirstOrDefault(p => p.id == pile);
            if (entry == null || data == null) return Fail("NO_PILE", $"這裡沒有 {pile} 這堆泥");
            if (entry.left <= 0) return Fail("PILE_CLEAR", "這堆泥已經清完了");
            var mud = Mud(data.kind);
            if (dragM < D(mud.minDragM)) return Fail("TOO_SHORT", data.kind == "hard" ? "這塊泥結硬了，要拖得更長更慢" : "泥很重，鏟子要拖長一點才撥得動");
            double moved = Math.Min(1, dragM / D(mud.fullDragM)) * D(sp.scoopMass);
            bool hurried = seconds < D(mud.hurriedSeconds);
            if (hurried) moved *= D(sp.hurriedKeep);
            var spot = SpotAt(pile, at);
            bool beat = onBeat && !hurried;
            bool tangled = spot == null && dir != null && data.kind == "weed" && dir[0] * D(data.pull[0]) + dir[1] * D(data.pull[1]) < 0;
            if (tangled) moved *= D(mud.wrongWayKeep);
            if (beat) moved *= D(sp.beatKeep);
            if (spot != null) { s.slumped.Add(pile + ":" + spot.id); moved += spot.slump * s.partySize; }
            moved = Math.Min(moved, entry.left);
            entry.left = Math.Max(0, Math.Round(entry.left - moved, 3, MidpointRounding.AwayFromZero));
            CheckWork();
            var step = spot != null ? Okay("SLUMPED", "整片泥塌下來了", moved) : tangled ? Okay("TANGLED", "水草纏住了，要往渠外拉", moved) : Okay(hurried ? "HURRIED" : "MOVED", hurried ? "撥太急，泥滑回一半" : "泥被撥開了", moved);
            step.onBeat = beat; return step;
        }

        /// Soft or hard mud is scraped: the game measures what the blade carried off and says so here (see rules.ts).
        public CreekStep Scrape(string pile, double mass, double[] at = null, bool onBeat = false)
        {
            var entry = s.silt.FirstOrDefault(p => p.id == pile); var data = M.piles.FirstOrDefault(p => p.id == pile);
            if (entry == null || data == null) return Fail("NO_PILE", $"這裡沒有 {pile} 這堆泥");
            if (entry.left <= 0) return Fail("PILE_CLEAR", "這堆泥已經清完了");
            if (data.kind == "weed") return Fail("USE_DRAG", "水草要順著拉出來");
            var spot = SpotAt(pile, at);
            if (mass <= 0 && spot == null) return Fail("NOTHING_MOVED", "");
            double moved = Math.Max(0, mass);
            if (spot != null) { s.slumped.Add(pile + ":" + spot.id); moved += spot.slump * s.partySize; }
            moved = Math.Min(moved, entry.left);
            entry.left = Math.Max(0, Math.Round(entry.left - moved, 3, MidpointRounding.AwayFromZero));
            CheckWork();
            var step = spot != null ? Okay("SLUMPED", "整片泥塌下來了", moved) : Okay("MOVED", "泥被鏟開了", moved);
            step.onBeat = onBeat; return step;
        }

        public int StonesShowing(string pile)
        {
            var p = M.piles.First(x => x.id == pile);
            return (int)Math.Floor(p.stones * (1 - Left(pile) / PileMass(p.mass)) + 1e-6);
        }

        // ---- join
        public CreekStep Place(string slot, string piece)
        {
            var w = M.work.FirstOrDefault(x => x.slot == slot);
            if (w == null) return Fail("NOT_WORK_SLOT", $"{slot} 這一段不用你接");
            if (Placed(slot) != null) return Fail("ALREADY_PLACED", $"{slot} 已經接好了");
            var option = w.options.FirstOrDefault(o => o.piece == piece);
            if (option == null) return Fail("NOT_ON_CART", $"{piece} 不在這一段的料裡");
            if (piece != w.piece) return Fail("MISALIGNED", option.message, option.gapCm);
            s.placed.Add(new CreekEntry { slot = slot, piece = piece }); CheckWork();
            return Okay("PLACED", $"{slot} 接上了");
        }

        public CreekStep Patch(string slot, string piece)
        {
            var w = M.patches.FirstOrDefault(x => x.slot == slot);
            if (w == null) return Fail("NOT_PATCH_SLOT", $"{slot} 沒有要補的裂口");
            if (Patched(slot) != null) return Fail("ALREADY_PLACED", $"{slot} 已經補好了");
            if (piece != w.piece) return Fail("WRONG_PATCH", w.wrongMessage);
            s.patches.Add(new CreekEntry { slot = slot, piece = piece }); CheckWork();
            return Okay("PATCHED", $"{slot} 的裂口補好了");
        }

        public CreekStep BuildAqueduct()
        {
            if (!M.HasAqueduct) return Fail("NO_AQUEDUCT", "這個修法不用渡槽");
            if (s.aqueduct) return Fail("ALREADY_PLACED", "渡槽已經架好了");
            s.aqueduct = true; CheckWork();
            return Okay("AQUEDUCT", "渡槽架好了");
        }

        public int WorkLeft => M.work.Count(w => Placed(w.slot) == null) + M.patches.Count(p => Patched(p.slot) == null) + (M.HasAqueduct && !s.aqueduct ? 1 : 0);
        public bool WorkDone => SiltLeft <= 0 && WorkLeft == 0;

        public SortedDictionary<string, string> Layout()
        {
            var o = new SortedDictionary<string, string>(StringComparer.Ordinal);
            foreach (var g in M.given) o[g.slot] = g.piece;
            foreach (var e in s.placed) o[e.slot] = e.piece;
            if (s.aqueduct && M.HasAqueduct) foreach (var g in M.aqueduct.slots) o[g.slot] = g.piece;
            return o;
        }

        void CheckWork()
        {
            if (!WorkDone) return;
            string layout = string.Join(",", Layout().Select(k => $"\"{k.Key}\":\"{k.Value}\"")), patches = string.Join(",", s.patches.Select(k => $"\"{k.slot}\":\"{k.piece}\""));
            Fire("work", CreekRepairEvents.WorkCompleted, $"{{\"method\":\"{s.method}\",\"layout\":{{{layout}}},\"patches\":{{{patches}}}}}");
        }

        // ---- flow
        public CreekStep TurnWheel(double degrees)
        {
            if (!WorkDone) return Fail("WORK_PENDING", SiltLeft > 0 ? "還有淤泥沒清完，水過不去" : "還有段落沒接好，現在放水會漫出來");
            if (degrees <= 0) return Fail("WRONG_WAY", "閘輪要往開的方向轉");
            s.wheelDegrees = Math.Min(content.flow.wheelDegrees, s.wheelDegrees + degrees);
            return Okay("TURNED", GateOpen ? "閘開了，水來了" : "閘板慢慢升起");
        }

        public bool GateOpen => s.wheelDegrees >= content.flow.wheelDegrees;
        public double RouteLength => M.route.Sum(n => (double)(decimal)n.lengthM);

        // ---- share the water
        public CreekGateState Gate(string id) => s.gates.First(g => g.id == id);
        public CreekGate GateData(string id) => content.distribution.gates.First(g => g.id == id);
        public bool FieldFull(string id) => Gate(id).fill >= D(GateData(id).fieldM) - 1e-9;
        public static string LevelName(double level) => level == 0 ? "關上了" : level < 1 ? "半開" : "全開";

        void MoveGate(string id, double level, string by)
        {
            Gate(id).level = level; s.gateLog.Add(new CreekGateMove { gate = id, level = level, by = by });
            if (by == "villager") return;
            s.idleSeconds = 0;
            s.lastClosed = level == 0 ? id : s.lastClosed == id ? "" : s.lastClosed;
        }

        /// Set a gate, before the water comes or while it runs. A full field needs no more, and nothing else is refused.
        public CreekStep SetGate(string id, double level, string by = "player")
        {
            var g = content.distribution.gates.FirstOrDefault(x => x.id == id);
            if (g == null) return Fail("NO_GATE", $"這裡沒有 {id} 這個閘門");
            if (!content.distribution.levels.Any(l => D(l) == level)) return Fail("BAD_LEVEL", "閘門只有關、半開、全開");
            if (level > 0 && FieldFull(id)) return Fail("FIELD_FULL", $"{g.label}已經滿了");
            if (Gate(id).level == level) return Okay("SAME_LEVEL", $"{g.label}的閘門已經是這樣了");
            MoveGate(id, level, by);
            return Okay("GATE_SET", $"{g.label}的閘門{LevelName(level)}");
        }

        /// One press on a gate: shut, half, full, shut.
        public CreekStep CycleGate(string id, string by = "player")
        {
            var levels = content.distribution.levels.Select(D).ToArray(); int at = Array.IndexOf(levels, Gate(id).level);
            double next = levels[(at + 1) % levels.Length];
            return SetGate(id, next > 0 && FieldFull(id) ? 0 : next, by);
        }

        /// With the water going nowhere, another gate is lifted to what the sign shows; never the one a player just shut, unless it is the last.
        void VillagerOpens()
        {
            var dry = content.distribution.gates.Where(g => !FieldFull(g.id)).ToArray(); var pick = dry.FirstOrDefault(g => g.id != s.lastClosed) ?? dry.FirstOrDefault();
            if (pick != null) MoveGate(pick.id, D(pick.planLevel), "villager");
        }

        void Distribute(double seconds)
        {
            var d = content.distribution; var gates = d.gates;
            var active = gates.Where(g => Gate(g.id).level > 0 && !FieldFull(g.id)).ToArray();
            if (active.Length == 0)
            {
                s.idleSeconds += seconds;
                if (s.idleSeconds >= D(d.villagerDelaySeconds) - 1e-9) { s.idleSeconds = 0; VillagerOpens(); }
                return;
            }
            s.idleSeconds = 0;
            double open = active.Aggregate(0.0, (a, g) => a + Gate(g.id).level); bool anyFull = gates.Any(g => FieldFull(g.id));
            foreach (var g in active)
            {
                var st = Gate(g.id);
                st.fill = Math.Min(D(g.fieldM), st.fill + D(content.flow.speedMps) * seconds * st.level / open);
                if (st.fill >= D(g.fieldM) - 1e-9) st.fill = D(g.fieldM);
                if (!s.reached.Contains(g.field)) { s.reached.Add(g.field); Fire("flow:" + g.field, CreekRepairEvents.FlowReached, $"{{\"nodeId\":\"{g.field}\"}}"); }
            }
            if (!anyFull && gates.Any(g => FieldFull(g.id))) s.together = gates.All(g => (D(g.fieldM) - Gate(g.id).fill) / D(g.fieldM) <= D(d.togetherWithin));
            foreach (var g in active) if (FieldFull(g.id)) MoveGate(g.id, 0, "villager");
            if (gates.All(g => FieldFull(g.id))) { s.done = true; Fire("flowDone", CreekRepairEvents.FlowCompleted, $"{{\"method\":\"{s.method}\"}}"); }
        }

        public bool CanalFull => s.flowM >= RouteLength - 1e-6;

        /// The water head runs along the route to the crossing, each node reported once; from there what is open shares the water.
        public void AdvanceFlow(double seconds)
        {
            if (!GateOpen || s.done || seconds <= 0) return;
            s.flowM = Math.Min(RouteLength, s.flowM + D(content.flow.speedMps) * seconds);
            double at = 0;
            foreach (var n in M.route)
            {
                if (s.flowM + 1e-6 < at) break;
                if (!s.reached.Contains(n.id)) { s.reached.Add(n.id); Fire("flow:" + n.id, CreekRepairEvents.FlowReached, $"{{\"nodeId\":\"{n.id}\"}}"); }
                at += D(n.lengthM);
            }
            if (CanalFull) Distribute(seconds);
        }
    }
}
