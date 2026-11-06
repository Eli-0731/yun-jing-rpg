// 青溪水工 B：C# 規則（Runtime/WaterworksRules.cs）與 JS 規則核心逐案比對。
// 讀 tools/qingxi-waterworks-b/data/scenarios.json（scripts/export-scenarios.mjs 產生），照同樣步驟在 C# 重跑，
// 比較水流、指標、接口問題與文字、方向條件、花費、請求編號、完工與重送結果，寫出報告。
//   Unity.exe -batchmode -quit -projectPath tools/qingxi-waterworks-b/unity
//     -executeMethod WaterworksRulesParity.Run -logFile <log>
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using QingxiWaterworksB;
using UnityEngine;

public static class WaterworksRulesParity
{
    static string ToolRoot => Path.GetFullPath(Path.Combine(Application.dataPath, "..", ".."));

    public static WwCtx LoadCtx()
    {
        var d = Path.Combine(ToolRoot, "data");
        return WwCtx.Load(File.ReadAllText(Path.Combine(d, "board.json")), File.ReadAllText(Path.Combine(d, "catalog.json")), File.ReadAllText(Path.Combine(d, "fixture-observations.json")));
    }

    public static void Run()
    {
        var ctx = LoadCtx();
        var root = (JObj)MiniJson.Parse(File.ReadAllText(Path.Combine(ToolRoot, "data", "scenarios.json")));
        var report = new StringBuilder("{\n \"note\": \"Unity C# 規則與 JS 規則核心逐案比對（data/scenarios.json）。由 WaterworksRulesParity.Run 在 Unity 批次模式產生。\",\n");
        report.Append($" \"unity\": {MiniJson.Quote(Application.unityVersion)},\n \"scenarios\": [\n");
        int pass = 0, total = 0, checks = 0;
        var lines = new List<string>();
        foreach (JObj sc in root.A("scenarios"))
        {
            total++;
            var diffs = new List<string>();
            int n = 0;
            void Eq(string what, object js, object cs)
            {
                n++;
                var a = Norm(js); var b = Norm(cs);
                if (a != b) diffs.Add($"{what}: JS={a} C#={b}");
            }
            void Near(string what, double js, double cs) { n++; if (Math.Abs(js - cs) > 1.5e-4) diffs.Add($"{what}: JS={js} C#={cs}"); }

            var s = WaterworksRules.NewSession(ctx, ctx.observationSets[sc.S("obs")]);
            var refusals = new List<WwResult>();
            foreach (JObj st in sc.A("steps"))
            {
                var type = st.S("type");
                if (type == "undo") { s = WaterworksRules.Undo(s).session; continue; }
                if (type == "redo") { s = WaterworksRules.Redo(s).session; continue; }
                if (type == "complete") { s = WaterworksRules.Complete(ctx, s, WaterworksRules.RequestIdFor(s)).session; continue; }
                var a = new WwAction { type = type, slot = st.S("slot"), piece = st.S("piece"), choice = st.S("choice"), open = st["open"] is bool o ? o : (bool?)null };
                var r = WaterworksRules.Act(ctx, s, a);
                if (!r.ok) refusals.Add(r);
                s = r.session;
            }
            var jr = sc.A("refusals");
            Eq("refusals.count", jr.Count, refusals.Count);
            for (int i = 0; i < Math.Min(jr.Count, refusals.Count); i++)
            {
                Eq($"refusals[{i}].code", ((JObj)jr[i]).S("code"), refusals[i].code);
                Eq($"refusals[{i}].message", ((JObj)jr[i]).S("message"), refusals[i].message);
            }
            var jd = sc.O("design");
            Eq("design.placed", Ordered(jd.O("placed")), string.Join(",", s.design.placed.Select(kv => kv.Key + "=" + kv.Value)));
            Eq("design.patches", Ordered(jd.O("patches")), string.Join(",", s.design.patches.Select(kv => kv.Key + "=" + kv.Value)));
            Eq("design.gates", Ordered(jd.O("gates")), string.Join(",", s.design.gates.Select(kv => kv.Key + "=" + (kv.Value ? "true" : "false"))));
            Eq("design.choice", jd.S("choice"), s.design.choice);

            var pv = WaterworksRules.Preview(ctx, s);
            var ev = pv.ev;
            Eq("wet", Sorted(sc.O("wet")), string.Join(",", ev.wet.Keys.OrderBy(k => k, StringComparer.Ordinal).Select(k => k + "=" + ev.wet[k])));
            var jf = sc.O("flow");
            Eq("flow.keys", string.Join(",", jf.Keys.OrderBy(k => k, StringComparer.Ordinal)), string.Join(",", ev.flow.Keys.OrderBy(k => k, StringComparer.Ordinal)));
            foreach (var k in jf.Keys) if (ev.flow.Has(k)) Near($"flow.{k}", jf.D(k), ev.flow[k]);

            var jm = sc.O("metrics"); var m = ev.metrics;
            Eq("metrics.villageSupply", jm.D("villageSupply"), m.villageSupply);
            Eq("metrics.drainFlow", jm.D("drainFlow"), m.drainFlow);
            Eq("metrics.spill", jm.D("spill"), m.spill);
            Eq("metrics.nursery.level", jm.O("nursery").S("level"), m.nurseryLevel);
            Eq("metrics.nursery.gap", jm.O("nursery")["gap"], m.nurseryGap);
            Eq("metrics.silt", jm.S("silt"), m.silt);
            Eq("metrics.crack", jm.S("crack"), m.crack);
            Eq("metrics.pieces", jm.D("pieces"), m.pieces);
            Eq("metrics.bends", jm.D("bends"), m.bends);
            Eq("metrics.gatesOnPath", string.Join(",", jm.A("gatesOnPath").Cast<JObj>().Select(g => g.S("slot") + "=" + ((bool)g["open"] ? "true" : "false"))),
                string.Join(",", m.gatesOnPath.Select(g => g.slot + "=" + (g.open ? "true" : "false"))));

            var ji = sc.A("issues");
            Eq("issues.count", ji.Count, ev.issues.Count);
            for (int i = 0; i < Math.Min(ji.Count, ev.issues.Count); i++)
            {
                var a = (JObj)ji[i]; var b = ev.issues[i];
                Eq($"issues[{i}].code", a.S("code"), b.code);
                Eq($"issues[{i}].slot", a.S("slot"), b.slot);
                Eq($"issues[{i}].port", a.S("port"), b.port);
                Eq($"issues[{i}].blocking", a["blocking"], b.blocking);
                Eq($"issues[{i}].message", a.S("message"), b.message);
                Eq($"issues[{i}].fix", a.S("fix"), b.fix);
            }
            Eq("unknowns", string.Join(",", sc.A("unknowns").Cast<string>()), string.Join(",", ev.unknowns.Select(u => u.id)));
            var jp = sc.A("problems");
            Eq("problems.count", jp.Count, pv.problems.Count);
            for (int i = 0; i < Math.Min(jp.Count, pv.problems.Count); i++)
            {
                Eq($"problems[{i}].code", ((JObj)jp[i]).S("code"), pv.problems[i].code);
                Eq($"problems[{i}].message", ((JObj)jp[i]).S("message"), pv.problems[i].message);
            }
            Eq("cost", Sorted(sc.O("cost")), string.Join(",", pv.cost.Keys.OrderBy(k => k, StringComparer.Ordinal).Select(k => k + "=" + pv.cost[k])));
            Eq("ready", sc["ready"], pv.ready);
            Eq("requestId", sc.S("requestId"), WaterworksRules.RequestIdFor(s));

            var jc = sc.A("completes");
            for (int i = 0; i < jc.Count; i++)
            {
                var a = (JObj)jc[i];
                var c = WaterworksRules.Complete(ctx, s, WaterworksRules.RequestIdFor(s));
                var p = $"completes[{i}]";
                Eq(p + ".ok", a["ok"], c.ok);
                Eq(p + ".code", a.S("code"), c.code);
                Eq(p + ".replayed", a["replayed"], c.ok ? (object)c.replayed : null);
                var o = a.O("outcome"); var co = c.receipt?.outcome;
                Eq(p + ".outcome?", o != null, co != null);
                if (o != null && co != null)
                {
                    Eq(p + ".outcomeId", o.S("outcomeId"), co.outcomeId);
                    Eq(p + ".villageSupply", o.D("villageSupply"), co.villageSupply);
                    Eq(p + ".villageText", o.S("villageText"), co.villageText);
                    Eq(p + ".nursery", o.S("nursery"), co.nursery);
                    Eq(p + ".nurseryText", o.S("nurseryText"), co.nurseryText);
                    Eq(p + ".silt", o.S("silt"), co.silt);
                    Eq(p + ".crack", o.S("crack"), co.crack);
                    Eq(p + ".discovered", string.Join("|", o.A("discovered").Cast<string>()), string.Join("|", co.discovered));
                }
                if (a.O("consumed") != null) Eq(p + ".consumed", Sorted(a.O("consumed")), c.receipt == null ? "" : string.Join(",", c.receipt.consumed.Keys.OrderBy(k => k, StringComparer.Ordinal).Select(k => k + "=" + c.receipt.consumed[k])));
                Eq(p + ".stock", Sorted(a.O("stock")), string.Join(",", c.session.ledger.stock.Keys.OrderBy(k => k, StringComparer.Ordinal).Select(k => k + "=" + c.session.ledger.stock[k])));
                Eq(p + ".completed", a.D("completed"), c.session.ledger.completed.Count);
                s = c.session;
            }

            checks += n;
            var ok = diffs.Count == 0;
            if (ok) pass++;
            lines.Add($"  {{ \"name\": {MiniJson.Quote(sc.S("name"))}, \"pass\": {(ok ? "true" : "false")}, \"checks\": {n}, \"diffs\": [{string.Join(", ", diffs.Select(MiniJson.Quote))}] }}");
            Debug.Log($"[WWB-PARITY] {sc.S("name")}: {(ok ? "PASS" : "FAIL")} ({n} checks){(ok ? "" : "\n  " + string.Join("\n  ", diffs))}");
        }
        report.Append(string.Join(",\n", lines));
        report.Append($"\n ],\n \"passed\": {pass},\n \"total\": {total},\n \"checks\": {checks}\n}}\n");
        var outDir = Path.Combine(ToolRoot, "reports");
        Directory.CreateDirectory(outDir);
        File.WriteAllText(Path.Combine(outDir, "unity_rules_parity.json"), report.ToString(), new UTF8Encoding(false));
        Debug.Log($"[WWB-PARITY] {pass}/{total} scenarios, {checks} checks");
        if (Application.isBatchMode) EditorApplicationExit(pass == total ? 0 : 1);
    }

    static void EditorApplicationExit(int code) => UnityEditor.EditorApplication.Exit(code);

    static string Norm(object v)
    {
        switch (v)
        {
            case null: return "null";
            case bool b: return b ? "true" : "false";
            case double d: return WaterworksRules.Num(d);
            case int i: return i.ToString();
            case float f: return WaterworksRules.Num(f);
            default: return v.ToString();
        }
    }
    static string Ordered(JObj o) => o == null ? "" : string.Join(",", o.Keys.Select(k => k + "=" + Norm(o[k])));
    static string Sorted(JObj o) => o == null ? "" : string.Join(",", o.Keys.OrderBy(k => k, StringComparer.Ordinal).Select(k => k + "=" + Norm(o[k])));
}
