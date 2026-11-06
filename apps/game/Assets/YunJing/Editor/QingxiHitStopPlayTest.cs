// Play Mode regression for QingxiBasicCombat.HitStop (review on PR #66): the real component on a GameObject in an empty scene,
// driven on real time. Each case logs Time.timeScale at its start and at its end and fails on any wrong value:
//   natural     stop from 0.5 ends by itself and puts 0.5 back (not 1)
//   chained     a second stop inside the first: the first timer must not end it early; the end restores the pre-first value
//   disable     the reviewer's repro: stop, disable the GameObject, 0.5 s later timeScale is back
//   destroy     stop, destroy the GameObject: back on the next frame and still 0.5 s later
//   pause       an outside pause sets 0 during the stop: the stop's end must not overwrite it
//   paused-hit  a hit while the game is paused at 0 does not start a stop at all
//   Unity -batchmode -projectPath apps/game -executeMethod YunJing.Editor.QingxiHitStopPlayTest.Run
// (no -quit: it enters Play Mode and exits by itself). Writes artifacts/basic-combat/hitstop-playmode.txt.
using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using YunJing.BasicCombat;

namespace YunJing.Editor
{
    [InitializeOnLoad]
    public static class QingxiHitStopPlayTest
    {
        const string Key = "QingxiHitStopPlayTest";
        static QingxiHitStopPlayTest() { if (SessionState.GetBool(Key, false)) EditorApplication.update += Tick; }

        public static void Run()
        {
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            SessionState.SetBool(Key, true); EditorApplication.update += Tick; EditorApplication.EnterPlaymode();
        }

        class Step { public float at; public Action act; }
        class Case { public string name; public float startScale; public List<Step> steps = new List<Step>(); }

        static List<Case> cases; static int ci = -1, si; static float t0; static GameObject go; static QingxiBasicCombat combat;
        static readonly List<string> log = new List<string>(); static int failures; static float settle;

        static void Note(string s) { log.Add(s); Debug.Log("HITSTOP_TEST " + s); }
        static void Expect(string what, float want)
        {
            bool ok = Mathf.Abs(Time.timeScale - want) < 1e-4f;
            if (!ok) failures++;
            Note($"  {(ok ? "ok  " : "FAIL")} {what}: timeScale {Time.timeScale:0.###} (want {want:0.###})");
        }

        static Case Make(string name, float start, params (float at, Action act)[] steps)
        {
            var c = new Case { name = name, startScale = start };
            foreach (var s in steps) c.steps.Add(new Step { at = s.at, act = s.act });
            return c;
        }

        static void Build()
        {
            const float S = QingxiBasicCombat.HitStopScale;
            cases = new List<Case>
            {
                Make("natural", .5f,
                    (0, () => combat.HitStop(.1f)), (.03f, () => Expect("during", S)), (.5f, () => Expect("0.5 s after start", .5f))),
                Make("chained", 1,
                    (0, () => combat.HitStop(.2f)), (.15f, () => combat.HitStop(.2f)),
                    (.25f, () => Expect("after the first stop would have ended", S)), (.6f, () => Expect("after the second stop", 1))),
                Make("disable", 1,
                    (0, () => combat.HitStop(.1f)), (.02f, () => { go.SetActive(false); Expect("right after SetActive(false)", 1); }),
                    (.52f, () => Expect("0.5 s after disabling", 1)), (.55f, () => { go.SetActive(true); Expect("re-enabled, no stop resumes", 1); })),
                Make("destroy", 1,
                    (0, () => combat.HitStop(.1f)), (.02f, () => { UnityEngine.Object.Destroy(go); go = null; }),
                    (.06f, () => Expect("frame after Destroy", 1)), (.52f, () => Expect("0.5 s after destroying", 1))),
                Make("pause", 1,
                    (0, () => combat.HitStop(.3f)), (.1f, () => { Time.timeScale = 0; Note("  outside pause sets 0"); }),
                    (.6f, () => Expect("after the stop would have ended", 0)), (.65f, () => { go.SetActive(false); Expect("disable while paused", 0); })),
                Make("paused-hit", 0,
                    (0, () => combat.HitStop(.1f)), (.03f, () => Expect("hit while paused", 0)), (.3f, () => Expect("later", 0))),
            };
        }

        static void Tick()
        {
            if (!EditorApplication.isPlaying) return;
            float now = Time.realtimeSinceStartup;
            if (cases == null) { Build(); settle = now + .5f; Note("Unity " + Application.unityVersion + ", real component QingxiBasicCombat"); }
            if (now < settle) return;
            if (ci < 0 || si >= cases[ci].steps.Count)
            {
                if (ci >= 0) { Note($"  end   timeScale {Time.timeScale:0.###}"); if (go != null) UnityEngine.Object.Destroy(go); go = null; }
                ci++;
                if (ci >= cases.Count) { Finish(); return; }
                Time.timeScale = cases[ci].startScale;
                go = new GameObject("HitStopTest_" + cases[ci].name); combat = go.AddComponent<QingxiBasicCombat>();
                si = 0; t0 = now;
                Note($"{cases[ci].name}: start timeScale {Time.timeScale:0.###}");
                return;
            }
            var step = cases[ci].steps[si];
            if (now - t0 < step.at) return;
            step.act(); si++;
            if (si >= cases[ci].steps.Count) settle = now + .1f;
        }

        static void Finish()
        {
            Time.timeScale = 1;
            Note(failures == 0 ? $"PASS ({cases.Count} cases)" : $"FAIL ({failures} checks)");
            var dir = Path.GetFullPath(Path.Combine(Application.dataPath, "../../../artifacts/basic-combat")); Directory.CreateDirectory(dir);
            File.WriteAllLines(Path.Combine(dir, "hitstop-playmode.txt"), log);
            SessionState.SetBool(Key, false); EditorApplication.update -= Tick;
            EditorApplication.ExitPlaymode();
            if (Application.isBatchMode) EditorApplication.Exit(failures == 0 ? 0 : 1);
        }
    }
}
