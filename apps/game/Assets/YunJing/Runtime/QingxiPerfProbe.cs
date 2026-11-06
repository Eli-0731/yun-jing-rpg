using System.Collections.Generic;
using UnityEngine;

namespace YunJing
{
    // K9: frame-rate probe. With ?perf in the URL (browser) or --perf on the command line it shows the frame rate
    // and frame time in a corner, and every 20 s logs QINGXI_PERF with the average and the slowest 1 % of frames,
    // so a phone test gives numbers instead of impressions. Off otherwise (no cost).
    public sealed class QingxiPerfProbe : MonoBehaviour
    {
        readonly List<float> frames = new List<float>(2048);
        float windowStart, shownFps, shownMs, lastShown;
        GUIStyle style;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        static void Install()
        {
            string args = string.Join(" ", System.Environment.GetCommandLineArgs()) + " " + Application.absoluteURL;
            if (!args.Contains("perf") || FindAnyObjectByType<QingxiPerfProbe>() != null) return;
            var go = new GameObject("Qingxi Perf Probe (K9)");
            DontDestroyOnLoad(go);
            go.AddComponent<QingxiPerfProbe>();
        }

        void Start() { windowStart = Time.realtimeSinceStartup; }

        void Update()
        {
            frames.Add(Time.unscaledDeltaTime);
            float now = Time.realtimeSinceStartup;
            if (now - lastShown > .5f)
            {
                lastShown = now;
                float sum = 0; int n = Mathf.Min(30, frames.Count);
                for (int i = frames.Count - n; i < frames.Count; i++) sum += frames[i];
                shownMs = sum / Mathf.Max(1, n) * 1000; shownFps = 1000 / Mathf.Max(.01f, shownMs);
            }
            if (now - windowStart >= 20 && frames.Count > 30)
            {
                var sorted = new List<float>(frames); sorted.Sort();
                float avg = 0; foreach (var f in frames) avg += f; avg /= frames.Count;
                float low = sorted[Mathf.Clamp(Mathf.FloorToInt(sorted.Count * .99f), 0, sorted.Count - 1)];
                Debug.Log($"QINGXI_PERF {frames.Count} frames: avg {1 / avg:0.0} fps ({avg * 1000:0.0} ms), slowest 1% {low * 1000:0.0} ms ({1 / low:0.0} fps), " +
                          $"{Screen.width}x{Screen.height}, {SystemInfo.graphicsDeviceName}, {SystemInfo.operatingSystem}");
                frames.Clear(); windowStart = now;
            }
        }

        void OnGUI()
        {
            if (style == null) style = new GUIStyle { fontSize = 14, normal = { textColor = Color.white }, alignment = TextAnchor.UpperCenter };
            var colour = shownFps >= 50 ? new Color(.6f, 1, .7f) : shownFps >= 30 ? new Color(1, .9f, .5f) : new Color(1, .5f, .45f);
            style.normal.textColor = colour;
            GUI.Label(new Rect(Screen.width / 2f - 100, 4, 200, 20), $"{shownFps:0} fps · {shownMs:0.0} ms", style);
        }
    }
}
