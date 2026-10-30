using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace YunJing
{
    // K9: keeps phones smooth without punishing computers. Every 4 s it looks at the average frame rate; below 40 fps
    // it steps down (render scale and shadow distance), above 57 fps it steps back up, never past the authored
    // settings. ?quality=high (or --quality-high) pins the top step for comparisons. Changes are logged as
    // QINGXI_QUALITY so a perf run (QingxiPerfProbe) shows what the device settled on.
    public sealed class QingxiAdaptiveQuality : MonoBehaviour
    {
        static readonly (float scale, float shadows)[] Steps = { (1f, 35f), (.85f, 28f), (.72f, 20f), (.6f, 14f) };
        int step;
        float windowStart, sum; int frames;
        UniversalRenderPipelineAsset pipeline;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        static void Install()
        {
            if (FindAnyObjectByType<QingxiAdaptiveQuality>() != null) return;
            var go = new GameObject("Qingxi Adaptive Quality (K9)");
            DontDestroyOnLoad(go);
            go.AddComponent<QingxiAdaptiveQuality>();
        }

        void Start()
        {
            pipeline = GraphicsSettings.currentRenderPipeline as UniversalRenderPipelineAsset;
            string args = string.Join(" ", System.Environment.GetCommandLineArgs()) + " " + Application.absoluteURL;
            if (pipeline == null || args.Contains("quality=high") || args.Contains("--quality-high")) { enabled = false; return; }
            Apply(0);
            windowStart = Time.realtimeSinceStartup + 3;   // let the first scene settle before judging
        }

        void Apply(int s)
        {
            step = s;
            pipeline.renderScale = Steps[s].scale;
            pipeline.shadowDistance = Steps[s].shadows;
        }

        void Update()
        {
            if (Time.realtimeSinceStartup < windowStart) return;
            sum += Time.unscaledDeltaTime; frames++;
            if (Time.realtimeSinceStartup - windowStart < 4) return;
            float fps = frames / Mathf.Max(.001f, sum);
            int next = fps < 40 ? Mathf.Min(step + 1, Steps.Length - 1) : fps > 57 ? Mathf.Max(step - 1, 0) : step;
            if (next != step)
            {
                Apply(next);
                Debug.Log($"QINGXI_QUALITY {fps:0} fps -> step {step}: render scale {Steps[step].scale:0.00}, shadows {Steps[step].shadows:0} m");
            }
            windowStart = Time.realtimeSinceStartup; sum = 0; frames = 0;
        }

        // The pipeline asset is shared with the editor: put the authored values back when the player stops.
        void OnDestroy() { if (pipeline != null) Apply(0); }
    }
}
