// 青溪水工 B：溪流取水 demo 的實機錄影與效能量測（放在 StreamDemo 場景，於 Windows 播放器執行）。
//
//   StreamDemo.exe -screen-width 1280 -screen-height 720 -screen-fullscreen 0 -qxOut <輸出資料夾>
//
// 1. 效能：總覽鏡頭各量 8 秒（水面開／水面全關），記錄每格 unscaledDeltaTime，輸出平均、P95、最大值。
// 2. 錄影：依 shots 逐段擷取畫面（實際經過的時間，水面用 _Time 自己流動，不推進任何時間位移）；
//    堰板段同時把 F01 堰頂從 0.28 → 0.30 → 0.10 → 0.28 移動，檢查水位連動。
// 3. 寫 demo_report.json 後結束程式。沒有 -qxOut 參數時只顯示場景、不錄影。
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using UnityEngine;

public class WaterDemoRecorder : MonoBehaviour
{
    [System.Serializable]
    public class Shot
    {
        public string name;
        public Vector3 position;
        public Vector3 target;
        public float seconds = 3f;
        public float fps = 12f;
        public bool weirSweep;
        public bool gateSequence;                   // 時間表：閘門關 → 開（灌田）→ 疊板降下（放水）→ 閘門關（退乾）
        public bool prefill;                        // 開拍前先開閘灌滿
    }

    public Camera cam;
    public FieldWeirController weir;
    public GateController gate;
    public WaterNetwork network;
    public WaterDemoControls controls;
    public Vector3 overviewPosition;
    public Vector3 overviewTarget;
    public Shot[] shots;
    public float perfSeconds = 8f;

    string outDir;
    readonly StringBuilder json = new StringBuilder();

    void Start()
    {
        var args = System.Environment.GetCommandLineArgs();
        var i = System.Array.IndexOf(args, "-qxOut");
        Aim(overviewPosition, overviewTarget);
        if (controls != null) controls.SelectCamera(0);
        if (i < 0 || i + 1 >= args.Length) return;
        outDir = args[i + 1];
        Directory.CreateDirectory(outDir);
        var f = System.Array.IndexOf(args, "-qxFree");
        if (f >= 0 && f + 1 < args.Length)
        {
            // 自由錄影：不跑劇本，只依實際按鍵操作錄畫面（8 fps），每格記錄閘門、疊板與鏡頭狀態
            StartCoroutine(Free(float.Parse(args[f + 1], System.Globalization.CultureInfo.InvariantCulture)));
            return;
        }
        QualitySettings.vSyncCount = 0;
        Application.targetFrameRate = -1;
        StartCoroutine(Run());
    }

    IEnumerator Free(float seconds)
    {
        Application.targetFrameRate = 60;
        var rows = new List<string>();
        float t0 = Time.realtimeSinceStartup, next = 0f;
        int n = 0;
        while (true)
        {
            float t = Time.realtimeSinceStartup - t0;
            if (t > seconds) break;
            if (t >= next)
            {
                yield return new WaitForEndOfFrame();
                var tex = new Texture2D(Screen.width, Screen.height, TextureFormat.RGB24, false);
                tex.ReadPixels(new Rect(0, 0, Screen.width, Screen.height), 0, 0);
                tex.Apply();
                File.WriteAllBytes(Path.Combine(outDir, $"free_{n:000}.png"), tex.EncodeToPNG());
                Destroy(tex);
                rows.Add($"{{\"t\":{F(t)},\"gate_open\":{(gate != null && gate.open ? 1 : 0)}," +
                         $"\"gate_offset\":{F(gate != null ? gate.Offset : 0f)},\"crest_z\":{F(weir != null ? weir.crestZ : 0f)}," +
                         $"\"field_fill\":{F(weir != null ? weir.fill : 0f)},\"camera\":{(controls != null ? controls.CameraIndex : 0)}}}");
                n++;
                next += 1f / 8f;
            }
            yield return null;
        }
        File.WriteAllText(Path.Combine(outDir, "free_report.json"),
            "{\n  \"frames\": [\n    " + string.Join(",\n    ", rows) + "\n  ]\n}\n", new UTF8Encoding(false));
        Application.Quit();
    }

    void Aim(Vector3 p, Vector3 t)
    {
        cam.transform.position = p;
        cam.transform.LookAt(t);
    }

    IEnumerator Run()
    {
        yield return null;                                              // 等 WaterNetwork.Start（退乾）跑完再灌
        if (gate != null && network != null)                            // 量效能時整條水路都要有水（疊板降下，出水口也有水）
        {
            if (weir != null) weir.SetCrest(FieldWeirController.MinCrest);
            gate.SetOpen(true, true);
            for (int k = 0; k < 400; k++) network.Step(0.05f);
        }
        yield return new WaitForSecondsRealtime(1.5f);                 // 等著色器編譯、貼圖上傳
        var waters = FindObjectsByType<Renderer>(FindObjectsInactive.Exclude, FindObjectsSortMode.None)
            .Where(r => r.sharedMaterials.Any(m => m != null && m.shader.name == "Qingxi/WaterFlow")).ToList();
        json.Append("{\n");
        json.Append($"  \"unity_version\": \"{Application.unityVersion}\",\n");
        json.Append($"  \"gpu\": \"{SystemInfo.graphicsDeviceName.Replace("\"", "'")}\",\n");
        json.Append($"  \"graphics_api\": \"{SystemInfo.graphicsDeviceType}\",\n");
        json.Append($"  \"cpu\": \"{SystemInfo.processorType.Replace("\"", "'").Trim()}\",\n");
        json.Append($"  \"resolution\": [{Screen.width}, {Screen.height}],\n");
        json.Append($"  \"water_renderers\": {waters.Count},\n");

        Aim(overviewPosition, overviewTarget);
        var on = new List<float>();
        yield return Measure(on);
        foreach (var r in waters) r.enabled = false;
        var off = new List<float>();
        yield return Measure(off);
        foreach (var r in waters) r.enabled = true;
        json.Append("  \"perf_water_on\": ").Append(Stats(on)).Append(",\n");
        json.Append("  \"perf_water_off\": ").Append(Stats(off)).Append(",\n");

        json.Append("  \"shots\": [\n");
        for (int s = 0; s < shots.Length; s++)
        {
            var shot = shots[s];
            Aim(shot.position, shot.target);
            if (weir != null) weir.SetCrest(FieldWeirController.MaxCrest);
            if (gate != null && network != null)
            {
                gate.SetOpen(shot.prefill, true);
                network.ResetDry();
                if (shot.prefill)
                    for (int k = 0; k < 400; k++) network.Step(0.05f);   // 20 秒模擬時間，灌滿整條
            }
            yield return new WaitForSecondsRealtime(0.4f);
            var times = new List<string>();
            var crests = new List<string>();
            var gates = new List<string>();
            float t0 = Time.realtimeSinceStartup, next = 0f;
            int n = 0;
            while (true)
            {
                float t = Time.realtimeSinceStartup - t0;
                if (t > shot.seconds) break;
                if (shot.weirSweep && weir != null) weir.SetCrest(Sweep(t / shot.seconds));
                if (shot.gateSequence && gate != null)
                {
                    gate.open = t >= 1.5f && t < 16f;
                    if (weir != null) weir.SetCrest(Mathf.Lerp(FieldWeirController.MaxCrest, FieldWeirController.MinCrest,
                        Mathf.SmoothStep(0f, 1f, (t - 11f) / 2.5f)));
                }
                if (t >= next)
                {
                    yield return new WaitForEndOfFrame();
                    // 專案未啟用 ScreenCapture 模組：在畫格結束時直接讀回後緩衝
                    var tex = new Texture2D(Screen.width, Screen.height, TextureFormat.RGB24, false);
                    tex.ReadPixels(new Rect(0, 0, Screen.width, Screen.height), 0, 0);
                    tex.Apply();
                    File.WriteAllBytes(Path.Combine(outDir, $"{shot.name}_{n:000}.png"), tex.EncodeToPNG());
                    Destroy(tex);
                    times.Add(F(t));
                    crests.Add(F(weir != null ? weir.crestZ : 0f));
                    gates.Add(gate != null && gate.open ? "1" : "0");
                    n++;
                    next += 1f / shot.fps;
                }
                yield return null;
            }
            json.Append($"    {{\"name\":\"{shot.name}\",\"frames\":{n},\"real_seconds\":[{string.Join(",", times)}]");
            if (shot.weirSweep) json.Append($",\"crest_z\":[{string.Join(",", crests)}]");
            if (shot.gateSequence) json.Append($",\"gate_open\":[{string.Join(",", gates)}],\"crest_z\":[{string.Join(",", crests)}]");
            json.Append(s + 1 < shots.Length ? "},\n" : "}\n");
        }
        json.Append("  ]\n}\n");
        File.WriteAllText(Path.Combine(outDir, "demo_report.json"), json.ToString(), new UTF8Encoding(false));
        Application.Quit();
    }

    // 疊板時間表：卡滿 0.30 →（降）0.10 放水 →（升）回卡滿，各段平滑
    static float Sweep(float u)
    {
        if (u < 0.15f) return 0.30f;
        if (u < 0.55f) return Mathf.Lerp(0.30f, 0.10f, Mathf.SmoothStep(0, 1, (u - 0.15f) / 0.4f));
        if (u < 0.7f) return 0.10f;
        return Mathf.Lerp(0.10f, 0.30f, Mathf.SmoothStep(0, 1, (u - 0.7f) / 0.3f));
    }

    IEnumerator Measure(List<float> dts)
    {
        yield return new WaitForSecondsRealtime(0.5f);
        float t0 = Time.realtimeSinceStartup;
        while (Time.realtimeSinceStartup - t0 < perfSeconds)
        {
            yield return null;
            dts.Add(Time.unscaledDeltaTime * 1000f);
        }
    }

    static string Stats(List<float> ms)
    {
        var s = ms.OrderBy(x => x).ToList();
        float avg = s.Average(), p95 = s[Mathf.Min(s.Count - 1, (int)(s.Count * 0.95f))], max = s[s.Count - 1];
        return $"{{\"frames\":{s.Count},\"avg_ms\":{F(avg)},\"p95_ms\":{F(p95)},\"max_ms\":{F(max)},\"avg_fps\":{F(1000f / avg)}}}";
    }

    static string F(float v) => v.ToString("0.###", System.Globalization.CultureInfo.InvariantCulture);
}
