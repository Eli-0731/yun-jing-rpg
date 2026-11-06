using System;
using System.Collections.Generic;
using System.IO;
using UnityEngine;
using Rules = YunJing.BasicCombat.QingxiBasicCombatRules;

namespace YunJing.Editor
{
    // Replays the runs recorded from tools/basic-combat/basic-combat-rules.mjs (parity.mjs) on the C# port and requires the same
    // events, positions and facing.
    //   Unity -batchmode -nographics -quit -projectPath apps/game -executeMethod YunJing.Editor.QingxiBasicCombatSmoke.Run
    public static class QingxiBasicCombatSmoke
    {
        [Serializable] class TargetData { public string id; public double x, z, radius; }
        [Serializable] class FrameData { public int frame; public bool attack, dodge, held; public double mx, mz; }
        [Serializable] class RunData { public string name; public double step, seconds, x, z, yaw, heavyCooldown; public string state; public TargetData[] targets; public FrameData[] frames; public string[] log; }
        [Serializable] class Parity { public RunData[] runs; }

        public static void Run() => Debug.Log(Verify());

        public static Rules.Content Load()
        {
            var text = Resources.Load<TextAsset>("BasicCombat/basic-combat-v1");
            if (text == null) throw new InvalidDataException("Resources/BasicCombat/basic-combat-v1 missing");
            var content = JsonUtility.FromJson<Rules.Content>(text.text);
            if (content.light == null || content.light.Length != 3 || content.heavy == null || content.dodge == null) throw new InvalidDataException("Basic combat content did not parse");
            return content;
        }

        static double R6(double v) => Math.Round(v * 1e6) / 1e6;

        static string Format(Rules.Event e)
        {
            string s = $"{R6(e.t)}:{e.type}";
            if (!string.IsNullOrEmpty(e.attackId) && e.type != "input.ignored") s += ":" + e.attackId;
            if (!string.IsNullOrEmpty(e.targetId)) s += ":" + e.targetId;
            if (e.type == Rules.HitEvent) s += ":" + e.damage;
            return s;
        }

        public static string Verify()
        {
            var content = Load();
            var data = JsonUtility.FromJson<Parity>(File.ReadAllText(Path.Combine(Application.dataPath, "YunJing/Data/QingxiBasicCombatParity.json")));
            if (data?.runs == null || data.runs.Length == 0) throw new InvalidDataException("Basic combat parity data missing");
            int events = 0;
            foreach (var r in data.runs)
            {
                var f = new Rules(content);
                var targets = new List<Rules.Target>();
                foreach (var t in r.targets) targets.Add(new Rules.Target { id = t.id, x = t.x, z = t.z, radius = t.radius, alive = true });
                var log = new List<string>();
                bool held = false; double mx = 0, mz = 0; int k = 0;
                for (int frame = 1; ; frame++)
                {
                    double now = R6(frame * r.step);
                    if (now >= r.seconds + 1e-9) break;
                    bool attack = false, dodge = false;
                    if (k < r.frames.Length && r.frames[k].frame == frame)
                    {
                        var fr = r.frames[k++];
                        attack = fr.attack; dodge = fr.dodge; held = fr.held; mx = fr.mx; mz = fr.mz;
                    }
                    foreach (var e in f.Update(now, new Rules.Input { attack = attack, dodge = dodge, heavyHeld = held, moveX = mx, moveZ = mz }, targets))
                        log.Add(Format(e));
                    if (frame > 100000) throw new InvalidOperationException("runaway replay " + r.name);
                }
                if (log.Count != r.log.Length) throw new InvalidDataException($"{r.name}: {log.Count} events, JS had {r.log.Length}\nC#: {string.Join(" | ", log)}\nJS: {string.Join(" | ", r.log)}");
                for (int i = 0; i < log.Count; i++)
                    if (log[i] != r.log[i]) throw new InvalidDataException($"{r.name} event {i}: C# '{log[i]}' vs JS '{r.log[i]}'");
                if (f.state != r.state || Math.Abs(f.x - r.x) > 1e-4 || Math.Abs(f.z - r.z) > 1e-4 || Math.Abs(f.yaw - r.yaw) > 1e-4 || Math.Abs(f.HeavyCooldown - r.heavyCooldown) > 1e-4)
                    throw new InvalidDataException($"{r.name}: end state C# {f.state} {f.x:F4},{f.z:F4} yaw {f.yaw:F4} cd {f.HeavyCooldown:F4} vs JS {r.state} {r.x},{r.z} yaw {r.yaw} cd {r.heavyCooldown}");
                events += log.Count;
            }
            return $"QINGXI_BASIC_COMBAT_PARITY_OK runs={data.runs.Length} events={events}";
        }
    }
}
