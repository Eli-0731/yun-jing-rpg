using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEngine;
using Rules = YunJing.QingxiZhuoBoarRules;

namespace YunJing.Editor
{
    // Replays the runs recorded from tools/zhuo-boar/zhuo-boar-rules.mjs (parity.mjs) on the C# port and requires the same
    // events, positions and outcomes.
    //   Unity -batchmode -nographics -quit -projectPath apps/game -executeMethod YunJing.Editor.QingxiZhuoBoarSmoke.Run
    public static class QingxiZhuoBoarSmoke
    {
        [Serializable] class InputData { public int frame; public double px, pz, dx, dz; public bool held, hasDodge; }
        [Serializable] class RunData { public string name; public double step; public int frames; public InputData[] inputs; public string[] log; public string state; public double x, z, yaw, stamina; public int hits, cleanses; }
        [Serializable] class Parity { public RunData[] runs; }

        static readonly Rules.Obstacle[] Obstacles = {
            new Rules.Obstacle { id = "D3_BoarTree_01", x = -4, z = 2, r = .175 },
            new Rules.Obstacle { id = "D3_BoarTree_02", x = 4, z = 3, r = .175 },
            new Rules.Obstacle { id = "D3_BoarTree_03", x = 0, z = -4, r = .175 },
            new Rules.Obstacle { id = "Stone_01", x = 5, z = -5, r = .8 },
            new Rules.Obstacle { id = "Stone_02", x = -6, z = -3, r = .7 },
        };

        public static void Run() => Debug.Log(Verify());

        public static string Verify()
        {
            var text = Resources.Load<TextAsset>("QingxiZhuoBoar/zhuo-boar-encounter-v1");
            if (text == null) throw new InvalidDataException("Resources/QingxiZhuoBoar/zhuo-boar-encounter-v1 missing");
            var content = JsonUtility.FromJson<Rules.Content>(text.text);
            if (content.tuning == null || content.texts?.button == null) throw new InvalidDataException("Zhuo boar content did not parse");
            var path = Path.Combine(Application.dataPath, "YunJing/Data/QingxiZhuoBoarParity.json");
            var data = JsonUtility.FromJson<Parity>(File.ReadAllText(path));
            if (data?.runs == null) throw new InvalidDataException("Zhuo boar parity data missing");

            var bounds = new Rules.Bounds { minX = -10, maxX = 10, minZ = -10, maxZ = 10 };
            foreach (var r in data.runs)
            {
                var boar = new Rules.Encounter(content, 0, 7, Math.PI, 40, false);
                boar.Begin();
                var input = new Rules.Input { obstacles = Obstacles, bounds = bounds };
                var log = new List<string>();
                int next = 0;
                double now = 0;
                bool dodge = false; Rules.P wanted = default;
                for (int frame = 1; frame <= r.frames; frame++)
                {
                    now += r.step;
                    if (next < r.inputs.Length && r.inputs[next].frame == frame)
                    {
                        var i = r.inputs[next++];
                        input.player = new Rules.P(i.px, i.pz);
                        input.cleanseHeld = i.held;
                        dodge = i.hasDodge; wanted = new Rules.P(i.dx, i.dz);
                    }
                    input.dodge = dodge ? wanted : (Rules.P?)null;
                    foreach (var e in boar.Update(now, input))
                        log.Add($"{Math.Round(boar.time, 6).ToString(System.Globalization.CultureInfo.InvariantCulture)}:{e.type}{(e.obstacle != null ? ":" + e.obstacle : "")}{(e.hits != 0 ? ":" + e.hits : "")}{(e.count != 0 ? ":" + e.count : "")}");
                }
                if (log.Count != r.log.Length) throw new InvalidOperationException($"run {r.name}: C# {log.Count} events, JS {r.log.Length}\nC#: {string.Join(" ", log)}\nJS: {string.Join(" ", r.log)}");
                for (int i = 0; i < log.Count; i++)
                    if (!SameEvent(log[i], r.log[i])) throw new InvalidOperationException($"run {r.name} event {i}: C# {log[i]}, JS {r.log[i]}");
                if (boar.state != r.state || boar.hits != r.hits || boar.cleanses != r.cleanses || Math.Abs(boar.stamina - r.stamina) > 1e-6)
                    throw new InvalidOperationException($"run {r.name}: C# {boar.state}/{boar.hits}/{boar.cleanses}/{boar.stamina}, JS {r.state}/{r.hits}/{r.cleanses}/{r.stamina}");
                if (Math.Abs(boar.x - r.x) > 1e-4 || Math.Abs(boar.z - r.z) > 1e-4 || Math.Abs(boar.yaw - r.yaw) > 1e-4)
                    throw new InvalidOperationException($"run {r.name}: C# at {boar.x},{boar.z},{boar.yaw}, JS at {r.x},{r.z},{r.yaw}");
            }
            return $"QINGXI_ZHUO_BOAR_PARITY PASS runs {string.Join(" ", data.runs.Select(r => $"{r.name}:{r.state}/hits{r.hits}/cleanses{r.cleanses}/events{r.log.Length}"))}";
        }

        static bool SameEvent(string a, string b)
        {
            int ai = a.IndexOf(':'), bi = b.IndexOf(':');
            return a.Substring(ai) == b.Substring(bi)
                && Math.Abs(double.Parse(a.Substring(0, ai), System.Globalization.CultureInfo.InvariantCulture) - double.Parse(b.Substring(0, bi), System.Globalization.CultureInfo.InvariantCulture)) < 1e-4;
        }
    }
}
