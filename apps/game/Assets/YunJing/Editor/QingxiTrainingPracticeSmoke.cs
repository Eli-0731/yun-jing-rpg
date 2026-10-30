using System;
using System.IO;
using System.Linq;
using UnityEngine;
using Rules = YunJing.QingxiTrainingPracticeRules;

namespace YunJing.Editor
{
    // Replays the runs recorded from Johnnnny0823's practice.mjs (tools/qingxi-main-scene/training-parity.mjs)
    // on the C# port and requires the same patterns, breath scores and block judgements.
    public static class QingxiTrainingPracticeSmoke
    {
        [Serializable] class StrikeData { public double at; public string side; public int phrase; }
        [Serializable] class PatternData { public uint seed; public StrikeData[] strikes; }
        [Serializable] class BreathData { public string name; public double step; public int frames; public int[] toggles; public bool done; public double qi; public int harmonised; public double[] scores; public string[] grades; }
        [Serializable] class InputData { public double t; public string side; public bool repeat; }
        [Serializable] class BlockData { public string name; public uint seed; public InputData[] inputs; public string[] judged; public bool done; public int blocked, perfect, bestCombo, flinches; public string grade; }
        [Serializable] class Parity { public PatternData[] patterns; public BreathData[] breath; public BlockData[] block; }

        public static string Verify()
        {
            var path = Path.Combine(Application.dataPath, "YunJing/Data/QingxiTrainingParity.json");
            var data = JsonUtility.FromJson<Parity>(File.ReadAllText(path));
            if (data?.patterns == null || data.breath == null || data.block == null) throw new InvalidDataException("Training parity data missing");

            foreach (var p in data.patterns)
            {
                var strikes = Rules.BlockPattern(p.seed);
                if (strikes.Count != p.strikes.Length) throw new InvalidOperationException($"seed {p.seed}: {strikes.Count} strikes, JS {p.strikes.Length}");
                for (int i = 0; i < strikes.Count; i++)
                    if (Math.Abs(strikes[i].at - p.strikes[i].at) > 1e-5 || strikes[i].side != p.strikes[i].side || strikes[i].phrase != p.strikes[i].phrase)
                        throw new InvalidOperationException($"seed {p.seed} strike {i}: C# {strikes[i].side}@{strikes[i].at}, JS {p.strikes[i].side}@{p.strikes[i].at}");
            }

            foreach (var b in data.breath)
            {
                var s = new Rules.BreathSession();
                bool held = false; double t = 0; int toggle = 0;
                for (int frame = 1; frame <= b.frames && !s.done; frame++)
                {
                    t += b.step;
                    if (toggle < b.toggles.Length && b.toggles[toggle] == frame) { held = !held; toggle++; }
                    s.SetHeld(held);
                    s.Update(t);
                }
                var scores = s.FinishedScores;
                if (s.done != b.done || s.Harmonised != b.harmonised || scores.Length != b.scores.Length || Math.Abs(s.qi - b.qi) > 1e-5)
                    throw new InvalidOperationException($"breath {b.name}: C# done={s.done} harmonised={s.Harmonised} qi={s.qi:0.######}, JS done={b.done} harmonised={b.harmonised} qi={b.qi}");
                for (int i = 0; i < scores.Length; i++)
                    if (Math.Abs(scores[i] - b.scores[i]) > 1e-5 || Rules.GradeBreath(scores[i]) != b.grades[i])
                        throw new InvalidOperationException($"breath {b.name} cycle {i}: C# {scores[i]:0.######}, JS {b.scores[i]}");
            }

            foreach (var b in data.block)
            {
                var s = new Rules.BlockSession(b.seed);
                var judged = b.inputs.Where(i => !string.IsNullOrEmpty(i.side)).Select(i => i).ToList();
                int j = 0;
                foreach (var i in b.inputs)
                {
                    if (string.IsNullOrEmpty(i.side)) { s.Update(i.t); continue; }
                    var r = s.Input(i.side, i.t, i.repeat);
                    string got = r.HasValue ? r.Value.result : "ignored";
                    if (got != b.judged[j]) throw new InvalidOperationException($"block {b.name} input {j}: C# {got}, JS {b.judged[j]}");
                    j++;
                }
                if (s.done != b.done || s.Blocked != b.blocked || s.Perfect != b.perfect || s.bestCombo != b.bestCombo || s.flinches != b.flinches || (s.Grade ?? "") != b.grade)
                    throw new InvalidOperationException($"block {b.name}: C# {s.Blocked}/{s.Perfect}/{s.bestCombo}/{s.flinches}/{s.Grade}, JS {b.blocked}/{b.perfect}/{b.bestCombo}/{b.flinches}/{b.grade}");
            }
            var summary = $"training parity: {data.patterns.Length} patterns, breath {string.Join("/", data.breath.Select(b => b.harmonised))}, block {string.Join("/", data.block.Select(b => b.blocked))}";
            Debug.Log("QINGXI_TRAINING_PARITY PASS " + summary);
            return summary;
        }
    }
}
