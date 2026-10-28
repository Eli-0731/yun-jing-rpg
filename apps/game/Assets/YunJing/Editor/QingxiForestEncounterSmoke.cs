using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

namespace YunJing.Editor
{
    // Replays the input streams recorded from tools/qingxi-encounter-a/encounter.mjs (see
    // tools/qingxi-main-scene/build-data.mjs) on the C# port and requires the identical event log.
    public static class QingxiForestEncounterSmoke
    {
        public static void Verify(QingxiAbcZoneData data)
        {
            if (data.forest.parity == null || data.forest.parity.Length == 0) throw new InvalidOperationException("No encounter parity scenarios");
            var summary = new List<string>();
            foreach (var s in data.forest.parity)
            {
                var rules = new QingxiForestEncounterRules(data.ToRulesWorld(), s.style);
                var byTick = s.commands.ToLookup(c => c.tick);
                var events = new List<QingxiForestEncounterRules.Event>();
                for (int tick = 0; tick < s.ticks; tick++)
                {
                    foreach (var c in byTick[tick])
                    {
                        if (c.m != null && c.m.Length == 2) rules.Move(c.m[0], c.m[1]);
                        if (c.f != null && c.f.Length == 1) rules.Face(c.f[0]);
                        if (c.b != null && c.b.Length == 1) rules.SetBlock(c.b[0] == 1);
                        if (!string.IsNullOrEmpty(c.a)) rules.Attack(c.a);
                        if (c.d) rules.Dodge();
                        if (c.r) rules.ResetAtSafePoint();
                    }
                    if (s.faceRabbit) rules.Face(Math.Atan2(rules.rabbit.x - rules.player.x, rules.rabbit.z - rules.player.z));
                    rules.Step(rules.P.dt);
                    events.AddRange(rules.DrainEvents());
                }
                if (events.Count != s.events.Length)
                    throw new InvalidOperationException($"{s.name}: C# emitted {events.Count} events, JS {s.events.Length}: {string.Join(" ", events.Select(e => e.type))}");
                for (int i = 0; i < events.Count; i++)
                {
                    var a = events[i]; var b = s.events[i];
                    if (a.type != b.type || (a.state ?? "") != b.state || (a.reason ?? "") != b.reason || (a.kind ?? "") != b.kind ||
                        a.hp != b.hp || Math.Abs(a.t - b.t) > .002)
                        throw new InvalidOperationException($"{s.name}: event {i} differs: C# {a.t:0.000} {a} vs JS {b.t:0.000} {b.type}:{b.state}:{b.reason}:{b.kind}:hp{b.hp}");
                }
                var f = s.final;
                if ((rules.outcome ?? "") != f.outcome || rules.rabbit.state != f.rabbitState || rules.rabbit.hp != f.rabbitHp || rules.player.hp != f.playerHp ||
                    Math.Abs(rules.player.x - f.playerX) > .002 || Math.Abs(rules.player.z - f.playerZ) > .002)
                    throw new InvalidOperationException($"{s.name}: final state differs from JS");
                summary.Add($"{s.name}={events.Count}");
            }
            Debug.Log("QINGXI_FOREST_ENCOUNTER_PARITY_PASS " + string.Join(", ", summary));
        }
    }

    public static class QingxiReturnSortingSmoke
    {
        // Mirrors the checks in tools/qingxi-return-c/state.test.cjs.
        public static void Verify()
        {
            var s = new QingxiReturnSorting();
            Require(!s.MoveTo("save").changed, "moving without a selection must not change anything");
            Require(s.Select("herb").changed && s.MoveTo("alchemy").changed, "select and move");
            Require(!s.MoveTo("alchemy").changed && s.Revision == 1, "repeating a destination adds nothing");
            Require(s.Undo().changed && s.Placements["herb"] == null, "undo returns the sample to the table");
            Require(!s.Undo().changed, "a second undo does nothing");
            Require(!s.MoveTo("unknown").changed && !s.Select("currency").changed, "unknown destination or sample rejected");
            var u = new QingxiReturnSorting();
            u.Select("ore"); u.MoveTo("save"); u.MoveTo("alchemy"); u.Undo();
            Require(u.Placements["ore"] == "save" && u.LastAction == null, "undo restores only the previous location");
            s.Select("ore"); s.MoveTo("commission"); s.Select("seed"); s.MoveTo("commission");
            Require(s.Count("commission") == 2 && s.Count(null) == 1 && s.Placements.Count == 3, "three fixed samples, free destinations");
            for (int i = 0; i < 40; i++) { s.Select("herb"); s.MoveTo(i % 2 == 0 ? "save" : "alchemy"); }
            Require(s.Journal.Count == 30, "journal keeps the latest 30 entries");
            Debug.Log("QINGXI_RETURN_SORTING_SMOKE_PASS");
        }

        static void Require(bool ok, string what) { if (!ok) throw new InvalidOperationException("Return sorting: " + what); }
    }
}
