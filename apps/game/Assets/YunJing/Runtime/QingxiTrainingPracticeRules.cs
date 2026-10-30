using System;
using System.Collections.Generic;
using System.Linq;

namespace YunJing
{
    // C# port of Johnnnny0823's tools/training-yard-demo/practice.mjs: 引氣呼吸 (qi breathing) on the
    // qi striking post and 武技格擋 (block rhythm) on the agility post. Pure and time-driven (seconds),
    // double precision like the JS original; QingxiTrainingPracticeSmoke checks parity against recorded runs.
    // Results are UI feedback only and never become cultivation (server practice-basic decides that).
    public static class QingxiTrainingPracticeRules
    {
        public const string Notice = "本機演示・刷新重置・不產生正式修為";
        public const string NoRootMessage = "目前未感應靈氣，可先練基礎武技、藥浴淬體或探索後天開靈";

        public struct Phase { public string key, label; public double seconds; }
        public static readonly Phase[] BreathPhases = {
            new Phase { key = "inhale", label = "吸", seconds = 3.2 },
            new Phase { key = "hold", label = "停", seconds = 1.0 },
            new Phase { key = "exhale", label = "呼", seconds = 3.2 },
            new Phase { key = "rest", label = "歇", seconds = 0.8 },
        };
        public static readonly double BreathLength = BreathPhases.Sum(p => p.seconds);
        public const double LeadIn = 1.5;

        public struct Guide { public string phase, label; public double value; public int cycle; }

        public static Guide GuideAt(double t)
        {
            if (t < 0) return new Guide { phase = "ready", label = "凝神", value = 0, cycle = 0 };
            int cycle = (int)Math.Floor(t / BreathLength);
            double u = t - cycle * BreathLength;
            foreach (var p in BreathPhases)
            {
                if (u < p.seconds)
                {
                    double k = u / p.seconds;
                    double value = p.key == "inhale" ? k : p.key == "hold" ? 1 : p.key == "exhale" ? 1 - k : 0;
                    return new Guide { phase = p.key, label = p.label, value = value, cycle = cycle };
                }
                u -= p.seconds;
            }
            return new Guide { phase = "rest", label = "歇", value = 0, cycle = cycle };
        }

        public static string GradeBreath(double score) => score >= 0.85 ? "圓融" : score >= 0.7 ? "平穩" : "散亂";

        static double Clamp01(double v) => Math.Min(1, Math.Max(0, v));

        public sealed class BreathSession
        {
            public readonly int cycles;
            readonly double start;
            double last;
            public bool held, done;
            public double qi;
            readonly List<double[]> acc = new List<double[]>();   // per cycle: weighted match, weight

            public BreathSession(bool hasRoots = true, int cycles = 3, double start = 0)
            {
                if (!hasRoots) throw new InvalidOperationException(NoRootMessage);
                this.cycles = cycles; this.start = start; last = start;
            }

            public void SetHeld(bool value) { if (!done) held = value; }

            // Integrates in steps of at most 1/120 s so the score does not depend on frame rate.
            public void Update(double now)
            {
                if (double.IsNaN(now) || double.IsInfinity(now) || now < last) throw new ArgumentException("time must be finite and monotonic");
                double t0 = last - start - LeadIn, t1 = now - start - LeadIn;
                while (!done && t0 < t1)
                {
                    double dt = Math.Min(1.0 / 120, t1 - t0);
                    t0 += dt;
                    double rate = (held ? 1 : -1) / BreathPhases[0].seconds;
                    qi = Clamp01(qi + rate * dt);
                    if (t0 >= 0)
                    {
                        var g = GuideAt(t0);
                        if (g.cycle >= cycles) { done = true; break; }
                        double weight = g.phase == "rest" ? 0.3 : 1;
                        double match = 1 - Math.Min(1, Math.Abs(qi - g.value) / 0.45);
                        while (acc.Count <= g.cycle) acc.Add(new double[2]);
                        acc[g.cycle][0] += match * weight * dt;
                        acc[g.cycle][1] += weight * dt;
                    }
                }
                last = now;
            }

            public double Elapsed => last - start - LeadIn;
            public Guide CurrentGuide => GuideAt(Math.Min(Elapsed, cycles * BreathLength - 1e-6));
            public double GuideValue => Elapsed < 0 ? 0 : CurrentGuide.value;
            public double Sync => 1 - Math.Min(1, Math.Abs(qi - GuideValue) / 0.45);

            public double[] FinishedScores
            {
                get
                {
                    var scores = acc.Select(a => a[1] != 0 ? a[0] / a[1] : 0).ToArray();
                    return scores.Take(done ? cycles : CurrentGuide.cycle).ToArray();
                }
            }

            public int Harmonised => FinishedScores.Count(s => s >= 0.7);
        }

        public static readonly string[] Sides = { "left", "right", "low" };
        public static string SideLabel(string side) => side == "left" ? "左臂" : side == "right" ? "右臂" : "下樁";
        public const double PerfectWindow = 0.09, GoodWindow = 0.18;

        public struct Strike { public double at; public string side; public int phrase; }

        // Three phrases that speed up; fixed per seed so a retry can be the same drill.
        public static List<Strike> BlockPattern(uint seed = 7)
        {
            uint s = seed;
            double Rnd() { s = unchecked(1664525u * s + 1013904223u); return s / 4294967296.0; }
            var phrases = new[] { (n: 4, gap: 1.25), (n: 4, gap: 1.0), (n: 4, gap: 0.8) };
            var strikes = new List<Strike>();
            double at = 2.0; string prev = null;
            for (int pi = 0; pi < phrases.Length; pi++)
            {
                for (int i = 0; i < phrases[pi].n; i++)
                {
                    string side = Sides[(int)Math.Floor(Rnd() * 3)];
                    if (side == prev && Rnd() < 0.6) side = Sides[(Array.IndexOf(Sides, side) + 1) % 3];
                    strikes.Add(new Strike { at = at, side = side, phrase = pi });
                    prev = side;
                    at += phrases[pi].gap;
                }
                at += 0.9;   // breath between phrases
            }
            return strikes;
        }

        public struct Judged { public string result, reason; public string side; }

        public sealed class BlockSession
        {
            public readonly List<Strike> strikes;
            readonly double start;
            double last;
            public int index, combo, bestCombo, flinches;
            public bool done;
            public readonly List<Judged> results = new List<Judged>();

            public BlockSession(uint seed = 7, double start = 0) { strikes = BlockPattern(seed); this.start = start; last = start; }

            public double Elapsed => last - start;

            public void Update(double now)
            {
                if (double.IsNaN(now) || double.IsInfinity(now) || now < last) throw new ArgumentException("time must be finite and monotonic");
                last = now;
                double t = now - start;
                while (!done && t > strikes[index].at + GoodWindow) Record(new Judged { result = "hit", reason = "來不及格擋" });
            }

            // Returns null when ignored (key repeat, finished, unknown side). Callers filter key repeat.
            public Judged? Input(string side, double now, bool repeat = false)
            {
                Update(now);
                if (repeat || done || Array.IndexOf(Sides, side) < 0) return null;
                var strike = strikes[index];
                double offset = now - start - strike.at;
                if (Math.Abs(offset) > GoodWindow)
                {
                    // Pressing with nothing arriving breaks the stance: mashing cannot farm combos.
                    flinches++; combo = 0;
                    return new Judged { result = "flinch", reason = "架勢鬆了" };
                }
                var judged = side != strike.side
                    ? new Judged { result = "hit", reason = $"擋錯方向，{SideLabel(strike.side)}打到" }
                    : new Judged { result = Math.Abs(offset) <= PerfectWindow ? "perfect" : "good" };
                Record(judged);
                return judged;
            }

            void Record(Judged r)
            {
                r.side = strikes[index].side;
                results.Add(r);
                combo = r.result == "perfect" || r.result == "good" ? combo + 1 : 0;
                bestCombo = Math.Max(bestCombo, combo);
                index++;
                done = index >= strikes.Count;
            }

            public int Blocked => results.Count(r => r.result == "perfect" || r.result == "good");
            public int Perfect => results.Count(r => r.result == "perfect");
            public string Grade => !done ? null : Blocked >= 11 ? "身法如風" : Blocked >= 8 ? "架勢已成" : "再練一輪";
            public Strike? Next => done ? (Strike?)null : strikes[index];
        }
    }
}
