// 青溪水工 B：古水路修復規則核心的 C# 版，逐行對照 tools/qingxi-waterworks-b/src/waterworks-core.mjs。
// 純計算：不讀時鐘、不用亂數、不碰 Unity 物件。同樣的版面、線索與淤積狀態一定得到同樣結果；
// 編輯器的 WaterworksPuzzleBuild.TestRules 會拿 data/scenarios.json（JS 參考結果）逐案比對。
// 文字訊息必須和 JS 一字不差，修改時兩邊一起改。
using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;

namespace QingxiWaterworksB
{
    // 保留插入順序的字典（對應 JS 物件的鍵順序）。
    public class OMap<T> : IEnumerable<KeyValuePair<string, T>>
    {
        public readonly List<string> Keys = new List<string>();
        readonly Dictionary<string, T> m = new Dictionary<string, T>();
        public int Count => Keys.Count;
        public bool Has(string k) => k != null && m.ContainsKey(k);
        public T Get(string k, T def = default) => k != null && m.TryGetValue(k, out var v) ? v : def;
        public T this[string k]
        {
            get => m[k];
            set { if (!m.ContainsKey(k)) Keys.Add(k); m[k] = value; }
        }
        public void Remove(string k) { if (k != null && m.Remove(k)) Keys.Remove(k); }
        public IEnumerable<T> Values => Keys.Select(k => m[k]);
        public OMap<T> Clone() { var c = new OMap<T>(); foreach (var k in Keys) c[k] = m[k]; return c; }
        public IEnumerator<KeyValuePair<string, T>> GetEnumerator() { foreach (var k in Keys.ToList()) yield return new KeyValuePair<string, T>(k, m[k]); }
        IEnumerator IEnumerable.GetEnumerator() => GetEnumerator();
    }

    public class WwPort { public string name, kind; public double[] pos, dir; }
    public class WwPiece
    {
        public string id, name, kind, crack, side, author, status;
        public double? eff;
        public OMap<int> cost = new OMap<int>();
        public List<WwPort> ports = new List<WwPort>();
        public List<int[]> cells = new List<int[]>();
    }
    public class WwSlot { public string id, label, fixedPiece; public double[] pos, dir; public bool old; }
    public class WwTerminal { public string id, kind; public double[] pos, dir; }
    public class WwExample { public string title; public List<WwAction> steps = new List<WwAction>(); }

    public class WwBoard
    {
        public string id, title;
        public double[] sourcePos, sourceDir;
        public List<WwSlot> slots = new List<WwSlot>();
        public List<WwTerminal> terminals = new List<WwTerminal>();
        public double[] fieldRect, nurseryRect, drainRect;
        public string siltSlot, siltObs, crackSlot, crackType, crackObs, nurseryObs;
        public double siltFactor, crackFactor, safeGap;
        public OMap<int> pieceStock = new OMap<int>(), materialStock = new OMap<int>();
        public OMap<string> materialNames = new OMap<string>();
        public double[] crackMarkPos; public double crackMarkZ;
        public OMap<WwExample> examples = new OMap<WwExample>();
    }

    public class WwCtx
    {
        public WwBoard board;
        public OMap<WwPiece> pieces = new OMap<WwPiece>();
        public OMap<List<string>> observationSets = new OMap<List<string>>();
        public OMap<string> observationLabels = new OMap<string>(), observationTexts = new OMap<string>();

        static double[] V(object o) { var l = (List<object>)o; return l.Select(x => (double)x).ToArray(); }

        public static WwCtx Load(string boardJson, string catalogJson, string fixtureJson)
        {
            var ctx = new WwCtx();
            var b = (JObj)MiniJson.Parse(boardJson);
            var B = new WwBoard { id = b.S("id"), title = b.S("title") };
            B.sourcePos = V(b.O("source")["pos"]); B.sourceDir = V(b.O("source")["dir"]);
            foreach (JObj s in b.A("slots"))
                B.slots.Add(new WwSlot { id = s.S("id"), label = s.S("label"), fixedPiece = s.S("fixed"), pos = V(s["pos"]), dir = V(s["dir"]), old = s["old"] is bool ob && ob });
            foreach (JObj t in b.A("terminals"))
                B.terminals.Add(new WwTerminal { id = t.S("id"), kind = t.S("kind"), pos = V(t["pos"]), dir = V(t["dir"]) });
            var z = b.O("zones");
            B.fieldRect = V(z.O("field")["rect"]); B.nurseryRect = V(z.O("nursery")["rect"]); B.drainRect = V(z.O("drain")["rect"]);
            var T = b.O("truth");
            B.siltSlot = T.O("silt").S("slot"); B.siltFactor = T.O("silt").D("factor"); B.siltObs = T.O("silt").S("observation");
            B.crackSlot = T.O("crack").S("slot"); B.crackType = T.O("crack").S("type"); B.crackFactor = T.O("crack").D("factor"); B.crackObs = T.O("crack").S("observation");
            B.nurseryObs = T.O("nursery").S("observation"); B.safeGap = T.O("nursery").D("safeGap");
            foreach (var k in b.O("pieceStock").Keys) B.pieceStock[k] = (int)b.O("pieceStock").D(k);
            foreach (var k in b.O("materialStock").Keys) B.materialStock[k] = (int)b.O("materialStock").D(k);
            foreach (var k in b.O("materialNames").Keys) B.materialNames[k] = b.O("materialNames").S(k);
            if (b.O("crackMark") != null) { B.crackMarkPos = V(b.O("crackMark")["pos"]); B.crackMarkZ = b.O("crackMark").D("z"); }
            var ex = b.O("examples");
            foreach (var choice in ex.Keys)
            {
                if (!(ex[choice] is JObj e)) continue;
                var we = new WwExample { title = e.S("title") };
                foreach (List<object> st in e.A("steps"))
                {
                    var type = (string)st[0];
                    we.steps.Add(type == "gate" ? new WwAction { type = type, slot = (string)st[1], open = (bool)st[2] }
                                                : new WwAction { type = type, slot = (string)st[1], piece = (string)st[2] });
                }
                B.examples[choice] = we;
            }
            ctx.board = B;

            var c = (JObj)MiniJson.Parse(catalogJson);
            var ps = c.O("pieces");
            foreach (var id in ps.Keys)
            {
                var p = ps.O(id);
                var wp = new WwPiece { id = p.S("id"), name = p.S("name"), kind = p.S("kind"), crack = p.S("crack"), side = p.S("side"), author = p.S("author"), status = p.S("status") };
                if (p["eff"] is double ef) wp.eff = ef;
                if (p.O("cost") != null) foreach (var k in p.O("cost").Keys) wp.cost[k] = (int)p.O("cost").D(k);
                if (p.A("ports") != null) foreach (JObj q in p.A("ports")) wp.ports.Add(new WwPort { name = q.S("name"), kind = q.S("kind"), pos = V(q["pos"]), dir = V(q["dir"]) });
                if (p.A("cells") != null) foreach (List<object> cc in p.A("cells")) wp.cells.Add(new[] { (int)(double)cc[0], (int)(double)cc[1] });
                ctx.pieces[id] = wp;
            }

            if (fixtureJson != null)
            {
                var f = (JObj)MiniJson.Parse(fixtureJson);
                foreach (var k in f.O("sets").Keys)
                    ctx.observationSets[k] = f.O("sets").O(k).A("observationIds").Select(x => (string)x).ToList();
                foreach (var k in f.O("observations").Keys)
                {
                    ctx.observationLabels[k] = f.O("observations").O(k).S("label");
                    ctx.observationTexts[k] = f.O("observations").O(k).S("text");
                }
            }
            return ctx;
        }
    }

    public class WwAction
    {
        public string type, slot, piece, choice;
        public bool? open;
        public override string ToString() => $"{type} {slot} {piece}{(open.HasValue ? " " + open : "")}{choice}";
    }

    public class WwDesign
    {
        public OMap<string> placed = new OMap<string>(), patches = new OMap<string>();
        public OMap<bool> gates = new OMap<bool>();
        public string choice;
        public WwDesign Clone() => new WwDesign { placed = placed.Clone(), patches = patches.Clone(), gates = gates.Clone(), choice = choice };
    }

    public class WwOutcome
    {
        public string outcomeId, choice, villageText, nursery, nurseryText, silt, crack;
        public int villageSupply;
        public List<string> discovered = new List<string>();
    }

    public class WwReceipt
    {
        public string requestId, fingerprint, projectId;
        public int seq, contribution;
        public OMap<int> consumed;
        public WwOutcome outcome;
    }

    public class WwLedger
    {
        public OMap<int> stock = new OMap<int>();
        public Dictionary<string, WwReceipt> receipts = new Dictionary<string, WwReceipt>();
        public List<(int seq, string requestId, string outcomeId)> completed = new List<(int, string, string)>();
        public int contribution, seq;
        public bool siltCleared;
        public WwLedger Clone() => new WwLedger { stock = stock.Clone(), receipts = new Dictionary<string, WwReceipt>(receipts), completed = completed.ToList(), contribution = contribution, seq = seq, siltCleared = siltCleared };
    }

    public class WwSession
    {
        public WwDesign design = new WwDesign();
        public List<WwDesign> past = new List<WwDesign>(), future = new List<WwDesign>();
        public List<string> obs = new List<string>();
        public WwLedger ledger = new WwLedger();
        public WwSession With(WwDesign d, List<WwDesign> p, List<WwDesign> f) => new WwSession { design = d, past = p, future = f, obs = obs, ledger = ledger };
    }

    public class WwResult
    {
        public bool ok, replayed;
        public string code, message;
        public WwSession session;
        public WwDesign design;
        public List<WwProblem> problems;
        public WwReceipt receipt;   // 完工成功或重送時
    }

    public class WwPlacedPort { public string name, kind; public double[] pos, dir; }
    public class WwPlacement { public List<WwPlacedPort> ports; public List<string> cells; public double yaw; }

    public class WwInst
    {
        public WwSlot slot; public string id; public WwPiece piece;
        public List<WwPlacedPort> ports; public List<string> cells; public double yaw; public bool gateOpen;
    }
    public class WwEdge { public WwPlacedPort port; public string to, emptySlot; public bool bad; }
    public class WwIssue
    {
        public string code, slot, port, next, message, fix;
        public bool blocking, deadEnd;
    }
    public class WwProblem { public string code, message, fix; }
    public class WwMetrics
    {
        public int villageSupply, drainFlow, spill, pieces, bends;
        public string nurseryLevel, silt, crack;
        public double? nurseryGap;
        public List<(string slot, bool open)> gatesOnPath = new List<(string, bool)>();
    }
    public class WwEval
    {
        public OMap<WwInst> inst = new OMap<WwInst>();
        public OMap<List<WwEdge>> edges = new OMap<List<WwEdge>>();
        public List<string> reached = new List<string>();
        public OMap<string> wet = new OMap<string>();
        public OMap<double> flow = new OMap<double>();
        public List<WwIssue> issues = new List<WwIssue>();
        public List<(string id, string text)> unknowns = new List<(string, string)>();
        public WwMetrics metrics;
        public List<WwIssue> blocking;
    }
    public class WwPreview { public WwEval ev; public List<WwProblem> problems; public OMap<int> cost; public bool ready; }
    public class WwCompare
    {
        public string choice, title, outcomeId, villageText, nursery, nurseryText, silt;
        public int villageSupply, pieces;
        public OMap<int> cost;
    }

    public static class WaterworksRules
    {
        public static readonly OMap<(string label, string shortLabel, string outcomeId)> CHOICES = MakeChoices();
        static OMap<(string, string, string)> MakeChoices()
        {
            var c = new OMap<(string, string, string)>();
            c["clear_silt"] = ("先清淤", "清淤", "wwb.clear_silt.diverted");
            c["restore_channel"] = ("修回舊渠", "修舊渠", "wwb.restore_channel.direct");
            c["protect_nursery"] = ("保護育幼區", "護育幼", "wwb.protect_nursery.bypass");
            return c;
        }
        public static readonly Dictionary<string, string> KIND_LABEL = new Dictionary<string, string>
        { { "straight", "直槽" }, { "discharge", "放流坡" }, { "bend", "彎槽" }, { "tee", "三通" }, { "gate", "閘板" }, { "patch", "補石" } };

        const double EPS = 1e-6;

        // JS 的 Math.round（.5 往正無限大）與數字轉字串
        public static double JsRound(double x) => Math.Floor(x + 0.5);
        public static string Num(double x)
        {
            if (Math.Abs(x - Math.Round(x)) < 1e-12 && Math.Abs(x) < 1e15) return ((long)Math.Round(x)).ToString(CultureInfo.InvariantCulture);
            return x.ToString("R", CultureInfo.InvariantCulture);
        }

        public static string DirName(double[] d)
        {
            var k = $"{Num(JsRound(d[0]))},{Num(JsRound(d[1]))}";
            switch (k) { case "0,1": return "北"; case "0,-1": return "南"; case "1,0": return "東"; case "-1,0": return "西"; default: return "?"; }
        }
        static double Fmt(double v) => Math.Abs(v) < EPS ? 0 : JsRound(v * 100) / 100;
        public static string FmtPos(double[] p) => $"({Num(Fmt(p[0]))}, {Num(Fmt(p[1]))})";
        static bool Same(double[] a, double[] b) => Math.Abs(a[0] - b[0]) < 0.01 && Math.Abs(a[1] - b[1]) < 0.01;

        // 把局部 +Y 轉到 d（d 為單位軸向量）
        static double[] Apply(double[] d, double[] v) { double c = d[1], s = -d[0]; return new[] { c * v[0] - s * v[1], s * v[0] + c * v[1] }; }
        public static double YawOf(double[] d) => Math.Atan2(-d[0], d[1]);

        // ------------------------------------------------------------ placement geometry
        public static WwPlacement PlacePiece(WwPiece piece, WwSlot slot)
        {
            var ports = piece.ports.Select(p =>
            {
                var w = Apply(slot.dir, p.pos);
                return new WwPlacedPort { name = p.name, kind = p.kind, pos = new[] { slot.pos[0] + w[0], slot.pos[1] + w[1] }, dir = Apply(slot.dir, p.dir) };
            }).ToList();
            var cells = piece.cells.Select(c =>
            {
                var w = Apply(slot.dir, new[] { (c[0] + 0.5) * 0.25, (c[1] + 0.5) * 0.25 });
                return $"{Num(Math.Floor((slot.pos[0] + w[0]) / 0.25 + EPS))},{Num(Math.Floor((slot.pos[1] + w[1]) / 0.25 + EPS))}";
            }).ToList();
            return new WwPlacement { ports = ports, cells = cells, yaw = YawOf(slot.dir) };
        }

        static double RectGap(IEnumerable<string> cellKeys, double[] rect)
        {
            double best = double.PositiveInfinity;
            foreach (var k in cellKeys)
            {
                var parts = k.Split(',');
                double cx = double.Parse(parts[0], CultureInfo.InvariantCulture), cy = double.Parse(parts[1], CultureInfo.InvariantCulture);
                double x0 = cx * 0.25, y0 = cy * 0.25, x1 = x0 + 0.25, y1 = y0 + 0.25;
                double dx = Math.Max(Math.Max(rect[0] - x1, x0 - rect[2]), 0), dy = Math.Max(Math.Max(rect[1] - y1, y0 - rect[3]), 0);
                best = Math.Min(best, Math.Sqrt(dx * dx + dy * dy));
            }
            return best;
        }
        static bool InRect(double[] p, double[] r) => p[0] >= r[0] - EPS && p[0] <= r[2] + EPS && p[1] >= r[1] - EPS && p[1] <= r[3] + EPS;

        // ------------------------------------------------------------ design (undoable) and session
        public static WwDesign NewDesign() => new WwDesign();

        public static WwSession NewSession(WwCtx ctx, IEnumerable<string> observationIds)
        {
            return new WwSession { obs = observationIds.ToList(), ledger = new WwLedger { stock = ctx.board.materialStock.Clone() } };
        }

        static int Used(WwDesign d, string id) => d.placed.Values.Count(p => p == id) + d.patches.Values.Count(p => p == id);
        static WwResult Fail(string code, string message) => new WwResult { ok = false, code = code, message = message };

        public static WwResult Edit(WwCtx ctx, WwDesign design, WwAction action)
        {
            var board = ctx.board;
            var slot = action.slot != null ? board.slots.FirstOrDefault(s => s.id == action.slot) : null;
            if (action.slot != null && slot == null) return Fail("NO_SLOT", $"沒有 {action.slot} 這個槽位");
            var d = design.Clone();
            switch (action.type)
            {
                case "place":
                {
                    var piece = ctx.pieces.Get(action.piece);
                    if (piece == null || piece.kind == "patch") return Fail("NOT_A_TROUGH", $"{action.piece} 不是可放進槽位的段件");
                    if (slot.fixedPiece != null) return Fail("FIXED_SLOT", $"{slot.id} 是舊渠原有的石槽，不能拆換{(slot.id == board.crackSlot ? "；可以用補石修" : "")}");
                    var left = board.pieceStock.Get(piece.id, 0) - Used(design, piece.id) + (design.placed.Get(slot.id) == piece.id ? 1 : 0);
                    if (left <= 0) return Fail("NO_PIECE", $"{piece.id} {piece.name}已經用完（材料車上共 {board.pieceStock.Get(piece.id, 0)} 件）；先拆下別處的同款或換一款");
                    d.placed[slot.id] = piece.id;
                    if (piece.kind == "gate" && !d.gates.Has(slot.id)) d.gates[slot.id] = false;
                    if (piece.kind != "gate") d.gates.Remove(slot.id);
                    return new WwResult { ok = true, design = d };
                }
                case "remove":
                {
                    if (slot.fixedPiece != null) return Fail("FIXED_SLOT", $"{slot.id} 是舊渠原有的石槽，不能拆");
                    if (!d.placed.Has(slot.id)) return Fail("EMPTY_SLOT", $"{slot.id} 本來就是空的");
                    d.placed.Remove(slot.id); d.gates.Remove(slot.id);
                    return new WwResult { ok = true, design = d };
                }
                case "patch":
                {
                    var piece = ctx.pieces.Get(action.piece);
                    if (piece == null || piece.kind != "patch") return Fail("NOT_A_PATCH", $"{action.piece} 不是補石");
                    if (!slot.old) return Fail("NOT_OLD", $"{slot.id} 是新放的段件，不需要補石；補石用在舊槽（{string.Join("、", board.slots.Where(s => s.old).Select(s => s.id))}）");
                    var left = board.pieceStock.Get(piece.id, 0) - Used(design, piece.id) + (design.patches.Get(slot.id) == piece.id ? 1 : 0);
                    if (left <= 0) return Fail("NO_PIECE", $"{piece.id} {piece.name}已經用完");
                    d.patches[slot.id] = piece.id;
                    return new WwResult { ok = true, design = d };
                }
                case "unpatch":
                {
                    if (!d.patches.Has(slot.id)) return Fail("EMPTY_SLOT", $"{slot.id} 沒有補石");
                    d.patches.Remove(slot.id);
                    return new WwResult { ok = true, design = d };
                }
                case "gate":
                {
                    var id = d.placed.Get(slot.id);
                    if (id == null || ctx.pieces[id].kind != "gate") return Fail("NO_GATE", $"{slot.id} 沒有閘板");
                    d.gates[slot.id] = action.open ?? !d.gates.Get(slot.id, false);
                    return new WwResult { ok = true, design = d };
                }
                case "choose":
                {
                    if (action.choice != null && !CHOICES.Has(action.choice)) return Fail("NO_CHOICE", $"沒有 {action.choice} 這個處理方向");
                    d.choice = action.choice;
                    return new WwResult { ok = true, design = d };
                }
                case "clear": return new WwResult { ok = true, design = NewDesign() };
                default: return Fail("NO_ACTION", $"不認得的操作 {action.type}");
            }
        }

        // 有撤回／重做的包裝。完工不進撤回歷史（帳本不會撤回）。
        public static WwResult Act(WwCtx ctx, WwSession session, WwAction action)
        {
            var r = Edit(ctx, session.design, action);
            if (!r.ok) { r.session = session; return r; }
            var past = session.past.ToList(); past.Add(session.design);
            return new WwResult { ok = true, session = session.With(r.design, past, new List<WwDesign>()) };
        }
        public static WwResult Undo(WwSession session)
        {
            if (session.past.Count == 0) return new WwResult { ok = false, code = "NOTHING_TO_UNDO", message = "沒有可以撤回的步驟", session = session };
            var future = new List<WwDesign> { session.design }; future.AddRange(session.future);
            return new WwResult { ok = true, session = session.With(session.past[session.past.Count - 1], session.past.Take(session.past.Count - 1).ToList(), future) };
        }
        public static WwResult Redo(WwSession session)
        {
            if (session.future.Count == 0) return new WwResult { ok = false, code = "NOTHING_TO_REDO", message = "沒有可以重做的步驟", session = session };
            var past = session.past.ToList(); past.Add(session.design);
            return new WwResult { ok = true, session = session.With(session.future[0], past, session.future.Skip(1).ToList()) };
        }

        // ------------------------------------------------------------ evaluation
        static bool OutsLand(WwCtx ctx, WwPiece piece, WwSlot slot, bool deep)
        {
            var board = ctx.board;
            var g = PlacePiece(piece, slot);
            var outs = g.ports.Where(p => p.kind != "in").ToList();
            return outs.Count > 0 && outs.All(p =>
            {
                if (p.kind == "discharge") return InRect(p.pos, board.drainRect);
                if (board.terminals.Any(t => Same(t.pos, p.pos) && Same(t.dir, p.dir))) return true;
                var next = board.slots.FirstOrDefault(x => x.id != slot.id && Same(x.pos, p.pos) && Same(x.dir, p.dir));
                return next != null && (!deep || piece.kind == "tee" || !DeadEnd(ctx, next));   // 三通可以用關著的閘板擋一側
            });
        }
        // 死路：這裡只能放關著的閘板（水接不下去）
        public static bool DeadEnd(WwCtx ctx, WwSlot slot) => !ctx.pieces.Values.Any(p => p.kind != "patch" && p.kind != "gate" && OutsLand(ctx, p, slot, false));
        public static List<string> FitsFor(WwCtx ctx, WwSlot slot, string kind = null, string exclude = null)
        {
            var all = ctx.pieces.Values.Where(p => p.kind != "patch" && p.id != exclude && ctx.board.pieceStock.Get(p.id, 0) > 0 && OutsLand(ctx, p, slot, true)).ToList();
            var sameKind = all.Where(p => p.kind == kind).ToList();
            return (sameKind.Count > 0 ? sameKind : all).Select(p => p.id).ToList();
        }

        static string PieceLabel(WwCtx ctx, string id) => $"{id} {ctx.pieces[id].name}";

        public static WwEval Evaluate(WwCtx ctx, WwDesign design, IList<string> obs = null, bool siltCleared = false, bool truth = false)
        {
            var board = ctx.board;
            obs = obs ?? new List<string>();
            bool Knows(string id) => truth || obs.Contains(id);
            var ev = new WwEval();
            var inst = ev.inst;
            foreach (var slot in board.slots)
            {
                var id = slot.fixedPiece ?? design.placed.Get(slot.id);
                if (id == null) continue;
                var pl = PlacePiece(ctx.pieces[id], slot);
                inst[slot.id] = new WwInst { slot = slot, id = id, piece = ctx.pieces[id], ports = pl.ports, cells = pl.cells, yaw = pl.yaw, gateOpen = design.gates.Get(slot.id, false) };
            }
            var issues = ev.issues;

            // 從水源出發的連接圖
            WwSlot EntryAt(double[] pos, double[] dir) => board.slots.FirstOrDefault(s => Same(s.pos, pos) && Same(s.dir, dir));
            WwTerminal TerminalAt(double[] pos, double[] dir) => board.terminals.FirstOrDefault(t => Same(t.pos, pos) && Same(t.dir, dir));
            var edges = ev.edges;
            var reached = new HashSet<string>();
            var reachedOrder = ev.reached;
            void Visit(string slotId)
            {
                if (reached.Contains(slotId)) return;
                reached.Add(slotId); reachedOrder.Add(slotId);
                var s = inst[slotId];
                var list = new List<WwEdge>();
                edges[slotId] = list;
                foreach (var p in s.ports)
                {
                    if (p.kind == "in") continue;
                    if (p.kind == "discharge")
                    {
                        var ok = InRect(p.pos, board.drainRect);
                        list.Add(new WwEdge { port = p, to = ok ? "drain" : null, bad = !ok });
                        continue;
                    }
                    var term = TerminalAt(p.pos, p.dir);
                    if (term != null) { list.Add(new WwEdge { port = p, to = term.id }); continue; }
                    var next = EntryAt(p.pos, p.dir);
                    if (next != null && inst.Has(next.id)) { list.Add(new WwEdge { port = p, to = next.id }); Visit(next.id); continue; }
                    list.Add(new WwEdge { port = p, to = null, emptySlot = next?.id });
                }
            }
            var first = EntryAt(board.sourcePos, board.sourceDir);
            Visit(first.id);

            // 疊件
            var owner = new OMap<List<string>>();
            foreach (var s in inst.Values) foreach (var c in s.cells) { if (!owner.Has(c)) owner[c] = new List<string>(); owner[c].Add(s.slot.id); }
            var pairs = new List<string>();
            foreach (var ids in owner.Values)
                if (ids.Count > 1)
                {
                    var key = string.Join("|", ids.Distinct().OrderBy(x => x, StringComparer.Ordinal));
                    if (!pairs.Contains(key)) pairs.Add(key);
                }
            foreach (var pr in pairs)
            {
                var ab = pr.Split('|');
                if (ab.Length < 2) continue;
                string a = ab[0], b = ab[1];
                var movable = inst[a].slot.fixedPiece != null ? b : inst[b].slot.fixedPiece != null ? a : !reached.Contains(b) ? b : !reached.Contains(a) ? a : b;
                issues.Add(new WwIssue
                {
                    code = "OVERLAP", slot = movable, blocking = true,
                    message = $"{a} 的 {PieceLabel(ctx, inst[a].id)}和 {b} 的 {PieceLabel(ctx, inst[b].id)}疊在一起",
                    fix = $"拆掉 {movable}；{a} 和 {b} 不能同時放（{(inst[a].piece.kind == "tee" || inst[b].piece.kind == "tee" ? "三通的分流缽會佔到下一格" : "形體會互相穿插")}）"
                });
            }

            // 水流：分支通到出口（村田、回流溝）或漫出才算有流；關著的閘板讓水靜止
            var carries = new Dictionary<string, bool>();
            bool Branch(string slotId)
            {
                if (carries.TryGetValue(slotId, out var cv)) return cv;
                carries[slotId] = false;   // 防環
                var s = inst[slotId];
                if (s.piece.kind == "gate" && !s.gateOpen) return carries[slotId] = false;
                bool any = false;
                foreach (var e in edges[slotId]) any = (e.to == null || e.to == "drain" || e.to == "field" || Branch(e.to)) || any;
                return carries[slotId] = any;
            }
            Branch(first.id);

            var flow = ev.flow; var wet = ev.wet;
            double fieldFlow = 0, drainFlow = 0, spillFlow = 0;
            bool Silted(string slotId) => slotId == board.siltSlot && !siltCleared;
            bool CrackLeak(string slotId) => slotId == board.crackSlot && ctx.pieces.Get(design.patches.Get(slotId))?.crack != board.crackType;
            void Still(string slotId)
            {
                if (wet.Has(slotId)) return;
                wet[slotId] = "still"; flow[slotId] = 0;
                if (inst[slotId].piece.kind == "gate" && !inst[slotId].gateOpen) return;   // 水停在關著的閘板
                foreach (var e in edges[slotId]) if (e.to != null && inst.Has(e.to)) Still(e.to);
            }
            void Push(string slotId, double q)
            {
                var s = inst[slotId];
                wet[slotId] = q > EPS ? "flow" : "still";
                flow[slotId] = flow.Get(slotId, 0) + q;
                var o = q * (s.piece.eff ?? 1);
                if (Silted(slotId) && Knows(board.siltObs)) o *= board.siltFactor;
                if (CrackLeak(slotId) && Knows(board.crackObs)) o *= board.crackFactor;
                if (s.piece.kind == "gate" && !s.gateOpen) { wet[slotId] = "still"; return; }
                var live = edges[slotId].Where(e => e.to == null || e.to == "drain" || e.to == "field" || Branch(e.to)).ToList();
                foreach (var e in edges[slotId])
                {
                    var share = live.Contains(e) ? o / live.Count : 0;
                    if (e.to == "field") fieldFlow += share;
                    else if (e.to == "drain") drainFlow += share;
                    else if (e.to == null) spillFlow += share;
                    else if (share > EPS) Push(e.to, share);
                    else Still(e.to);
                }
            }
            Push(first.id, 1);

            // 斷開／空著的接口，指名說明
            foreach (var kv in edges)
            {
                var slotId = kv.Key;
                var s = inst[slotId];
                foreach (var e in kv.Value)
                {
                    if (e.to != null) continue;
                    var where = $"{slotId} 的 {PieceLabel(ctx, s.id)}「{e.port.name}」接口";
                    var flowing = flow.Get(slotId, 0) > EPS;
                    if (e.bad)
                    {
                        issues.Add(new WwIssue
                        {
                            code = "BAD_DISCHARGE", slot = slotId, port = e.port.name, blocking = flowing,
                            message = $"{where}把水倒在 {FmtPos(e.port.pos)}，那裡不是回流溝",
                            fix = "放流坡只能接在 L2，讓水倒回西邊的回流溝；這一格請改放直槽或彎槽"
                        });
                    }
                    else if (e.emptySlot != null)
                    {
                        var nextSlot = board.slots.First(x => x.id == e.emptySlot);
                        var dead = DeadEnd(ctx, nextSlot);
                        var fits = dead ? new List<string>() : FitsFor(ctx, nextSlot);
                        var alt = s.slot.fixedPiece != null ? new List<string>() : FitsFor(ctx, s.slot, exclude: s.id);
                        issues.Add(new WwIssue
                        {
                            code = "EMPTY_NEXT", slot = slotId, port = e.port.name, next = e.emptySlot, blocking = flowing, deadEnd = dead,
                            message = $"{where}朝{DirName(e.port.dir)}接到 {e.emptySlot}，但 {e.emptySlot} 還空著{(dead ? $"；{e.emptySlot} 再往前沒有槽位，只能放關著的閘板擋水" : "")}{(flowing ? "，水會從這裡漫出" : "")}",
                            fix = dead && s.piece.kind == "tee"
                                ? $"在 {e.emptySlot} 放一座 B05 閘板並保持關閉，把這一側的水擋住"
                                : dead
                                ? $"把 {slotId} 換成不往 {e.emptySlot} 出水的段件{(alt.Count > 0 ? $"（例如 {string.Join("、", alt.Take(4))}）" : "")}"
                                : $"在 {e.emptySlot} 放一段能接下去的段件{(fits.Count > 0 ? $"（例如 {string.Join("、", fits.Take(4))}）" : "")}"
                        });
                    }
                    else
                    {
                        var near = board.slots.Where(x => !inst.Has(x.id) || x.id != slotId)
                            .Select(x => (x, d: Hypot(x.pos[0] - e.port.pos[0], x.pos[1] - e.port.pos[1]))).OrderBy(t => t.d).FirstOrDefault();
                        var fits = FitsFor(ctx, s.slot, s.piece.kind, s.id);
                        if (s.piece.kind == "gate" && !s.gateOpen && !flowing)
                        {
                            issues.Add(new WwIssue
                            {
                                code = "GATE_END", slot = slotId, port = e.port.name, blocking = false,
                                message = $"{slotId} 閘板外側（{DirName(e.port.dir)}）還沒接槽；閘板關著，水擋在這裡不會漏",
                                fix = "要送水時先在外側接好段件再開閘；只當擋水閘用就保持關閉"
                            });
                            continue;
                        }
                        var hint = near.x != null && near.d < 0.6
                            ? $"最近的槽位 {near.x.id} 入口在 {FmtPos(near.x.pos)} 朝{DirName(near.x.dir)}，差 {Num(JsRound(near.d * 100))} cm"
                            : "這個方向沒有槽位";
                        issues.Add(new WwIssue
                        {
                            code = "OPEN_PORT", slot = slotId, port = e.port.name, blocking = flowing || s.piece.kind != "gate",
                            message = $"{where}落在 {FmtPos(e.port.pos)} 朝{DirName(e.port.dir)}，沒有接上任何槽位（{hint}）{(flowing ? "，水會從這裡漫出" : "")}",
                            fix = s.slot.fixedPiece != null ? $"{slotId} 是舊槽，請調整下游段件" : (fits.Count > 0 ? $"把 {slotId} 換成 {string.Join("、", fits)}，接口才會對上" : $"拆掉 {slotId}，換一款出水口對得上的段件")
                        });
                    }
                }
            }
            // 水到不了的段件
            foreach (var slotId in design.placed.Keys)
            {
                if (reached.Contains(slotId)) continue;
                var s = inst[slotId];
                var feeders = inst.Values.Where(o => o.slot.id != slotId && o.ports.Any(p => p.kind == "out" && Same(p.pos, s.slot.pos) && Same(p.dir, s.slot.dir))).ToList();
                var why = feeders.Count > 0 ? $"上游 {string.Join("、", feeders.Select(f => f.slot.id))} 也還沒接上水路" : "上游沒有段件的出水口通到這裡";
                issues.Add(new WwIssue
                {
                    code = "NOT_CONNECTED", slot = slotId, blocking = true,
                    message = $"{slotId} 的 {PieceLabel(ctx, s.id)}沒接上水路：{why}",
                    fix = $"拆掉 {slotId}，或在上游放能通到 {slotId} 入口 {FmtPos(s.slot.pos)} 的段件"
                });
            }
            foreach (var kv in design.patches)
            {
                string slotId = kv.Key, pid = kv.Value;
                if (ctx.pieces[pid].crack == board.crackType && slotId == board.crackSlot) continue;
                if (slotId != board.crackSlot)
                    issues.Add(new WwIssue { code = "PATCH_UNNEEDED", slot = slotId, blocking = false, message = $"{slotId} 沒有{(Knows(board.crackObs) ? "" : "已知的")}裂口，補石用不上", fix = $"撤回 {slotId} 的補石" });
                else if (Knows(board.crackObs))
                    issues.Add(new WwIssue
                    {
                        code = "PATCH_WRONG", slot = slotId, blocking = false,
                        message = $"{PieceLabel(ctx, pid)}貼不上 {slotId} 的裂口：這道是槽壁外側的直裂縫", fix = "改用 B07 修補石鞍（鞍形貼牆頂）"
                    });
            }

            // 供水、育幼區與淤積
            var flowingKeys = flow.Keys.Where(k => flow[k] > EPS).ToList();
            var gap = flowingKeys.Count > 0 ? RectGap(flowingKeys.SelectMany(k => inst[k].cells), board.nurseryRect) : double.PositiveInfinity;
            var nurseryLevel = flowingKeys.Count == 0 ? "dry" : gap < board.safeGap ? "risk" : "safe";
            var crackOnPath = inst.Has(board.crackSlot) && flow.Get(board.crackSlot, 0) > EPS;
            var siltOnPath = flow.Get(board.siltSlot, 0) > EPS;
            if (!Knows(board.siltObs)) ev.unknowns.Add(("silt", "沒有「淤積」線索：取水口後的舊槽 P1 淤到什麼程度不知道，實際水量可能比預估少。"));
            if (!Knows(board.crackObs) && crackOnPath) ev.unknowns.Add(("crack", "沒有「破槽」線索：舊槽 P4 有沒有裂縫沒人查過，水走這裡可能漏掉一部分。"));
            if (!Knows(board.nurseryObs)) ev.unknowns.Add(("nursery", "沒有「育幼區足跡」線索：不知道渠邊平常有沒有孩子走動，靠近育幼區的路線風險未知。"));

            var gates = inst.Values.Where(s => s.piece.kind == "gate").ToList();
            var m = new WwMetrics
            {
                villageSupply = (int)JsRound(fieldFlow * 100),
                drainFlow = (int)JsRound(drainFlow * 100),
                spill = (int)JsRound(spillFlow * 100),
                nurseryLevel = Knows(board.nurseryObs) ? nurseryLevel : (nurseryLevel == "dry" ? "dry" : "unknown"),
                nurseryGap = double.IsInfinity(gap) ? (double?)null : JsRound(gap * 100) / 100,
                silt = siltCleared ? "cleared" : Knows(board.siltObs) ? (siltOnPath ? "slowing" : "remaining") : "unknown",
                crack = !crackOnPath ? "bypassed" : !Knows(board.crackObs) ? "unknown" : CrackLeak(board.crackSlot) ? "leaking" : "patched",
                pieces = design.placed.Count,
                bends = inst.Values.Count(s => reached.Contains(s.slot.id) && s.piece.kind == "bend"),
                gatesOnPath = gates.Where(g => reached.Contains(g.slot.id)).Select(g => (g.slot.id, g.gateOpen)).ToList(),
            };
            ev.metrics = m;
            ev.blocking = issues.Where(i => i.blocking).ToList();
            return ev;
        }
        static double Hypot(double x, double y) => Math.Sqrt(x * x + y * y);

        // ------------------------------------------------------------ direction (choice) requirements
        public static List<WwProblem> CheckChoice(WwCtx ctx, WwDesign design, WwEval ev)
        {
            var board = ctx.board;
            var problems = new List<WwProblem>();
            var c = design.choice;
            if (c == null) return new List<WwProblem> { new WwProblem { code = "NO_CHOICE", message = "還沒選處理方向（清淤／修回舊渠／保護育幼區）" } };
            var m = ev.metrics;
            if (c == "restore_channel" || c == "protect_nursery")
            {
                if (m.villageSupply <= 0) problems.Add(new WwProblem { code = "NO_FIELD_WATER", message = "水還沒流到村田進水口" + (m.gatesOnPath.Any(g => !g.open) ? "：路上的閘板關著，按「開閘」" : "：從 B01 一路接到北邊的村田") });
                if (m.gatesOnPath.Count == 0) problems.Add(new WwProblem { code = "NO_GATE", message = "水路上要有一座 B05 閘板，村裡才能控制放水；把其中一段直槽換成閘板" });
            }
            if (c == "restore_channel" && !(ev.flow.Get(board.crackSlot, 0) > 0))
                problems.Add(new WwProblem { code = "NOT_OLD_LINE", message = $"「修回舊渠」要讓水走原本的舊渠（經過舊槽 {board.crackSlot}）；現在的路線繞開了它" });
            if (c == "protect_nursery" && m.villageSupply > 0)
            {
                var gap = m.nurseryGap ?? double.PositiveInfinity;
                if (gap < board.safeGap) problems.Add(new WwProblem { code = "TOO_CLOSE", message = $"流水離育幼區只有 {Num(JsRound(gap * 100))} cm（至少要 {Num(board.safeGap * 100)} cm）；改走西側 L 槽位繞過去" });
            }
            if (c == "clear_silt")
            {
                var tee = ev.reached.Select(id => ev.inst[id]).FirstOrDefault(s => s.piece.kind == "tee");
                if (tee == null) problems.Add(new WwProblem { code = "NO_TEE", message = "清淤時要先把泥水導開：在 P2 放三通，一邊接去回流溝" });
                if (m.drainFlow <= 0) problems.Add(new WwProblem { code = "NO_DRAIN", message = "泥水沒有導進回流溝：三通西側接 L1 直槽、L2 放流坡 B02-V05" });
                if (m.villageSupply > 0) problems.Add(new WwProblem { code = "MUD_TO_FIELD", message = "清淤時泥水會沖進村田：把往村田那一側的閘板關上" });
                if (tee != null && !ev.edges[tee.slot.id].Any(e => e.to != null && ev.inst.Has(e.to) && ev.inst[e.to].piece.kind == "gate"))
                    problems.Add(new WwProblem { code = "NO_HOLD_GATE", message = "三通另一側要接一座閘板（關著），清完淤再開閘送水" });
            }
            return problems;
        }

        // ------------------------------------------------------------ outcome
        static OMap<int> Cost(WwCtx ctx, WwDesign design, WwEval ev)
        {
            var total = new OMap<int>();
            var ids = design.placed.Where(kv => ev.reached.Contains(kv.Key)).Select(kv => kv.Value).Concat(design.patches.Values);
            foreach (var id in ids)
                foreach (var kv in ctx.pieces[id].cost) total[kv.Key] = total.Get(kv.Key, 0) + kv.Value;
            return total;
        }

        public static string Fingerprint(WwDesign design, IEnumerable<string> obs)
        {
            string O<T>(OMap<T> x, Func<T, string> f) => string.Join(",", x.Keys.OrderBy(k => k, StringComparer.Ordinal).Select(k => $"{k}={f(x[k])}"));
            return $"p:{O(design.placed, v => v)};x:{O(design.patches, v => v)};g:{O(design.gates, v => v ? "true" : "false")};c:{design.choice ?? "null"};o:{string.Join(",", obs.OrderBy(k => k, StringComparer.Ordinal))}";
        }

        // 現在完工會怎樣（不改變任何東西）
        public static WwPreview Preview(WwCtx ctx, WwSession session)
        {
            var design = session.design; var ledger = session.ledger;
            var ev = Evaluate(ctx, design, session.obs, ledger.siltCleared);
            var problems = ev.blocking.Select(i => new WwProblem { code = i.code, message = i.message, fix = i.fix }).Concat(CheckChoice(ctx, design, ev)).ToList();
            var need = Cost(ctx, design, ev);
            var shortList = need.Where(kv => ledger.stock.Get(kv.Key, 0) < kv.Value).ToList();
            if (shortList.Count > 0)
                problems.Add(new WwProblem { code = "NOT_ENOUGH_MATERIAL", message = $"本機展示材料不夠：{string.Join("；", shortList.Select(kv => $"{ctx.board.materialNames.Get(kv.Key)} 要 {kv.Value}、剩 {ledger.stock.Get(kv.Key, 0)}"))}" });
            return new WwPreview { ev = ev, problems = problems, cost = need, ready = problems.Count == 0 };
        }

        static WwOutcome OutcomeOf(WwCtx ctx, WwDesign design, WwEval truthEv, IList<string> obs)
        {
            var ch = CHOICES[design.choice];
            var m = truthEv.metrics;
            var gcm = Num(JsRound((m.nurseryGap ?? 0) * 100));
            string nurseryText;
            switch (m.nurseryLevel)
            {
                case "risk": nurseryText = $"流水離育幼區只有 {gcm} cm，孩子常走的渠邊要加圍欄、派人看守"; break;
                case "safe": nurseryText = $"流水離育幼區 {gcm} cm 以上，孩子的路不受影響"; break;
                case "dry": nurseryText = "育幼區附近沒有流水"; break;
                default: nurseryText = null; break;
            }
            var B = ctx.board;
            var discovered = new List<string>();
            if (!obs.Contains(B.siltObs) && m.silt == "slowing") discovered.Add("完工放水才發現 P1 淤了一半，水量少了四成");
            if (!obs.Contains(B.crackObs) && m.crack == "leaking") discovered.Add("放水後 P4 舊槽西牆滲水，漏掉約三成半");
            if (!obs.Contains(B.nurseryObs) && m.nurseryLevel == "risk") discovered.Add("放水後才看到育幼區孩子的腳印橫過渠道");
            var today = design.choice == "clear_silt" ? 0 : m.villageSupply;
            return new WwOutcome
            {
                outcomeId = ch.outcomeId, choice = design.choice,
                villageSupply = today,
                villageText = design.choice == "clear_silt" ? "今天村田沒有新水；淤泥從回流溝排走，下次開閘就是全量" : $"村田進水 {today}%",
                nursery = m.nurseryLevel, nurseryText = nurseryText,
                silt = design.choice == "clear_silt" ? "cleared" : m.silt,
                crack = m.crack,
                discovered = discovered,
            };
        }

        // 本機演示完工。以 requestId 保證冪等：同一請求回傳原收據、不改任何東西；同一 requestId 但方案不同則拒絕。
        // 不是正式發放，見 CONTRACT.md。
        public static WwResult Complete(WwCtx ctx, WwSession session, string requestId)
        {
            if (string.IsNullOrEmpty(requestId)) return new WwResult { ok = false, code = "NO_REQUEST_ID", message = "缺少請求編號", session = session };
            var fp = Fingerprint(session.design, session.obs);
            if (session.ledger.receipts.TryGetValue(requestId, out var prev))
            {
                if (prev.fingerprint != fp) return new WwResult { ok = false, code = "IDEMPOTENCY_CONFLICT", message = "相同請求編號不能用於不同方案", session = session };
                return new WwResult { ok = true, replayed = true, receipt = prev, session = session };
            }
            var pv = Preview(ctx, session);
            if (!pv.ready) return new WwResult { ok = false, code = "NOT_READY", problems = pv.problems, session = session };
            var truthEv = Evaluate(ctx, session.design, null, session.ledger.siltCleared, truth: true);
            var outcome = OutcomeOf(ctx, session.design, truthEv, session.obs);
            var L = session.ledger.Clone();
            foreach (var kv in pv.cost) L.stock[kv.Key] = L.stock.Get(kv.Key, 0) - kv.Value;
            var contribution = pv.cost.Values.Sum();
            L.seq += 1;
            var receipt = new WwReceipt { requestId = requestId, fingerprint = fp, projectId = ctx.board.id, seq = L.seq, consumed = pv.cost, contribution = contribution, outcome = outcome };
            L.contribution += contribution;
            L.receipts[requestId] = receipt;
            L.completed.Add((L.seq, requestId, outcome.outcomeId));
            L.siltCleared = L.siltCleared || session.design.choice == "clear_silt";
            return new WwResult { ok = true, replayed = false, receipt = receipt, session = new WwSession { design = session.design, past = session.past, future = session.future, obs = session.obs, ledger = L } };
        }

        // 版面自上次完工後沒變，再按「完工」就重送同一個請求；之後重排（例如清淤後）是新的請求。
        public static string RequestIdFor(WwSession session)
        {
            var fp = Fingerprint(session.design, session.obs);
            uint h = 2166136261;
            unchecked { foreach (var ch in fp) { h ^= ch; h *= 16777619; } }
            if (session.ledger.completed.Count > 0)
            {
                var last = session.ledger.completed[session.ledger.completed.Count - 1];
                if (session.ledger.receipts[last.requestId].fingerprint == fp) return last.requestId;
            }
            return $"wwb-local-{session.ledger.seq + 1}-{h:x8}";
        }

        // ------------------------------------------------------------ reference layouts
        public static List<WwAction> ExampleActions(WwBoard board, string choice)
        {
            var l = new List<WwAction> { new WwAction { type = "clear" } };
            l.AddRange(board.examples[choice].steps);
            l.Add(new WwAction { type = "choose", choice = choice });
            return l;
        }

        public static List<WwCompare> CompareDirections(WwCtx ctx, WwSession session)
        {
            var allObs = new List<string> { ctx.board.siltObs, ctx.board.crackObs, ctx.board.nurseryObs };
            return CHOICES.Keys.Select(choice =>
            {
                var s = session.With(NewDesign(), new List<WwDesign>(), new List<WwDesign>());
                foreach (var a in ExampleActions(ctx.board, choice)) s = Act(ctx, s, a).session;
                var pv = Preview(ctx, s);
                var truthEv = Evaluate(ctx, s.design, null, session.ledger.siltCleared, truth: true);
                var o = OutcomeOf(ctx, s.design, truthEv, allObs);
                return new WwCompare
                {
                    choice = choice, title = ctx.board.examples[choice].title, outcomeId = CHOICES[choice].outcomeId, villageSupply = o.villageSupply, villageText = o.villageText,
                    nursery = o.nursery, nurseryText = o.nurseryText, silt = o.silt, cost = pv.cost, pieces = s.design.placed.Count
                };
            }).ToList();
        }
    }
}
