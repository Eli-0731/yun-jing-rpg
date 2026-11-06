using System;
using System.Collections;
using System.IO;
using UnityEngine;

namespace YunJing
{
    // Opt-in local build check. Never attached to network/account scenes.
    public sealed class QingxiWalkthroughSmoke : MonoBehaviour
    {
        IEnumerator Start()
        {
            if (Array.IndexOf(Environment.GetCommandLineArgs(), "--walkthrough-smoke") < 0) yield break;
            var player = GetComponent<QingxiWalkthroughController>();
            player.ScriptedWalkthrough = true;
            for (int i = 0; i < 90; i++) { player.Step(Vector2.zero, false, false, 1f / 60); yield return new WaitForSecondsRealtime(1f / 60); }
            var start = transform.position;
            var cameraStart = Camera.main.transform.position;
            for (int i = 0; i < 60; i++) { player.Step(Vector2.up, false, false, 1f / 60); yield return new WaitForSecondsRealtime(1f / 60); }
            float moved = Vector3.Distance(start, transform.position);
            float cameraMoved = Vector3.Distance(cameraStart, Camera.main.transform.position);
            float ground = transform.position.y, peak = ground;
            for (int i = 0; i < 100; i++) {
                player.Step(Vector2.zero, false, i == 0, 1f / 60);
                peak = Mathf.Max(peak, transform.position.y);
                yield return new WaitForSecondsRealtime(1f / 60);
            }
            bool landed = Mathf.Abs(transform.position.y - ground) < .15f;
            bool passed = moved > 3.5f && moved < 4.5f && cameraMoved > 2f && peak - ground > .8f && landed;
            player.ReturnToEntrance();
            for (int i = 0; i < 60; i++) { player.Step(Vector2.zero, false, false, 1f / 60); yield return new WaitForSecondsRealtime(1f / 60); }
            passed &= Vector3.Distance(start, transform.position) < .2f;
            string report = $"QINGXI_WALKTHROUGH_SMOKE {(passed ? "PASS" : "FAIL")}: walk={moved:F3}m camera={cameraMoved:F3}m jump={peak-ground:F3}m landed={landed}; return={Vector3.Distance(start, transform.position):F3}m";
            Debug.Log(report);
            File.WriteAllText(Path.Combine(Application.persistentDataPath, "walkthrough-smoke.txt"), report);
            Application.Quit(passed ? 0 : 1);
        }
    }
}
