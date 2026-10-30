// 青溪水工 B：溪流取水 demo 場景（批次模式）。
//
//   Unity.exe -batchmode -projectPath tools/qingxi-waterworks-b/unity -executeMethod WaterworksDemo.Run -quit -logFile <log> [-qxBuild <exe 路徑>]
//
// 1. 依 art/source/qingxi-waterworks-b/routes.json 的 stream_test 擺放矩陣（Blender 座標）擺出 S01、S02、B01…F01、B02-V05，
//    各件掛上水面子物件（Qingxi/WaterFlow）。Blender (x, y, z) → Unity (x, z, y)：矩陣換成 P·M·P（P 對調 y、z）。
// 2. F01 掛 FieldWeirController，逐一套用 raised／hold／half／drain，量堰板位移、手輪角度、田面水高度與顯示切換，
//    結果寫進 art/source/qingxi-waterworks-b/unity_demo_report.json；四個狀態各渲染一張特寫。
// 3. 場景存成 Scenes/StreamDemo.unity（含 WaterDemoRecorder）；有 -qxBuild 參數時輸出 Windows 播放器。
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

public static class WaterworksDemo
{
    const string ScenePath = "Assets/QingxiWaterworksB/Scenes/StreamDemo.unity";
    const string ModelDir = "Assets/QingxiWaterworksB/Models";

    static string RepoRoot => Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", "..", ".."));

    public static void Run()
    {
        var pieces = ReadRoute("stream_test");
        EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        RenderSettings.ambientMode = AmbientMode.Trilight;
        RenderSettings.ambientSkyColor = new Color(0.50f, 0.53f, 0.55f);
        RenderSettings.ambientEquatorColor = new Color(0.38f, 0.38f, 0.35f);
        RenderSettings.ambientGroundColor = new Color(0.20f, 0.19f, 0.17f);
        var sun = new GameObject("Sun").AddComponent<Light>();
        sun.type = LightType.Directional;
        sun.color = new Color(1f, 0.95f, 0.86f);
        sun.intensity = 1.25f;
        sun.shadows = LightShadows.Soft;
        sun.shadowStrength = 0.75f;
        sun.transform.rotation = Quaternion.Euler(48f, -35f, 0f);
        QualitySettings.shadowDistance = 40f;

        var ground = GameObject.CreatePrimitive(PrimitiveType.Plane);
        ground.name = "Ground";
        ground.transform.localScale = new Vector3(6f, 1f, 6f);
        ground.transform.position = new Vector3(4f, -0.02f, 6f);
        var gm = new Material(Shader.Find("Standard")) { color = new Color(0.30f, 0.30f, 0.27f) };
        gm.SetFloat("_Glossiness", 0.05f);
        AssetDatabase.CreateAsset(gm, "Assets/QingxiWaterworksB/Materials/demo_ground.mat");
        ground.GetComponent<Renderer>().sharedMaterial = gm;

        var root = new GameObject("stream_test");
        GameObject f01 = null, b05 = null;
        var placedPieces = new List<(string id, GameObject go)>();
        foreach (var (id, m) in pieces)
        {
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>($"{ModelDir}/{id}.fbx");
            var go = (GameObject)PrefabUtility.InstantiatePrefab(prefab, root.transform);
            // 匯入的根物件可能自帶姿態（例如 x 軸 −90°）：路線矩陣要乘在它外面，不能直接覆蓋
            var u = ToUnity(m);
            var r = u.rotation;
            go.transform.SetPositionAndRotation((Vector3)u.GetColumn(3) + r * prefab.transform.localPosition,
                                                r * prefab.transform.localRotation);
            WaterworksImportCheck.AttachWater(id, go);
            if (id == "F01") f01 = go;
            if (id == "B05") b05 = go;
            placedPieces.Add((id, go));
        }

        var weir = f01.AddComponent<FieldWeirController>();
        weir.Recapture();
        var gate = b05.AddComponent<GateController>();               // 模型預設閘板在槽底＝關
        var network = root.AddComponent<WaterNetwork>();
        foreach (var (id, go) in placedPieces) network.nodes.Add(BuildNode(id, go, gate, weir));

        var cam = new GameObject("Camera").AddComponent<Camera>();
        cam.clearFlags = CameraClearFlags.SolidColor;
        cam.backgroundColor = new Color(0.62f, 0.68f, 0.72f);
        cam.fieldOfView = 40f;
        cam.nearClipPlane = 0.05f;
        cam.farClipPlane = 200f;
        cam.depthTextureMode |= DepthTextureMode.Depth;
        cam.gameObject.AddComponent<WaterDepthCamera>();
        cam.tag = "MainCamera";

        // F01 局部（Blender 座標）→ 世界：先扣掉根物件的匯入姿態，再把 (x, y, z) 換成 Unity 局部 (x, z, y)
        var f01Src = PrefabUtility.GetCorrespondingObjectFromSource(f01).transform;
        var f01Rot = f01.transform.rotation * Quaternion.Inverse(f01Src.localRotation);
        var f01Pos = f01.transform.position - f01Rot * f01Src.localPosition;
        Vector3 F(float x, float y, float z) => f01Pos + f01Rot * new Vector3(x, z, y);
        var weirCam = F(-0.55f, 2.75f, 0.95f);
        var weirTarget = F(0f, 3.62f, 0.24f);
        var b01 = root.transform.Cast<Transform>().First(t => t.name.StartsWith("B01")).position;

        var rec = new GameObject("DemoRecorder").AddComponent<WaterDemoRecorder>();
        var controls = rec.gameObject.AddComponent<WaterDemoControls>();
        controls.gate = gate;
        controls.weir = weir;
        controls.network = network;
        rec.cam = cam;
        rec.weir = weir;
        rec.gate = gate;
        rec.network = network;
        rec.controls = controls;
        rec.overviewPosition = new Vector3(4.6f, 7.8f, -2.8f);
        rec.overviewTarget = new Vector3(4.6f, 0f, 5.6f);
        var chainCam = new Vector3(4.2f, 4.2f, 1.2f);                 // 從取水口斜看到田地，整條水路入鏡
        var chainTarget = new Vector3(5.6f, 0.1f, 6.2f);
        controls.cam = cam;
        controls.cameraPositions = new[] { chainCam, weirCam, b01 + new Vector3(-1.7f, 1.5f, -1.9f) };
        controls.cameraTargets = new[] { chainTarget, weirTarget, b01 + new Vector3(0.3f, 0.2f, 0f) };
        rec.shots = new[]
        {
            new WaterDemoRecorder.Shot { name = "stream", position = new Vector3(-2.0f, 1.7f, 2.2f),
                target = new Vector3(0.4f, 0.15f, 5.2f), seconds = 3f, fps = 12f },
            new WaterDemoRecorder.Shot { name = "intake", position = b01 + new Vector3(-1.7f, 1.5f, -1.9f),
                target = b01 + new Vector3(0.3f, 0.2f, 0f), seconds = 3f, fps = 12f },
            new WaterDemoRecorder.Shot { name = "network", position = chainCam, target = chainTarget,
                seconds = 22f, fps = 6f, gateSequence = true },
            new WaterDemoRecorder.Shot { name = "weir", position = weirCam, target = weirTarget,
                seconds = 8f, fps = 8f, weirSweep = true, prefill = true },
        };

        // 堰板連動檢查＋特寫
        var shots = Path.Combine(RepoRoot, "art", "previews", "qingxi-waterworks-b");
        var tests = new List<string>();
        bool allOk = true;
        weir.SetCrest(FieldWeirController.WaterZ);                // 位移以建模位置（堰頂 0.28）為基準
        var w0 = weir.Weir.position;
        var wheelR0 = weir.Wheel.rotation;
        var f0 = weir.FieldWater.position;
        cam.transform.position = weirCam;
        cam.transform.LookAt(weirTarget);
        foreach (var (name, crest) in FieldWeirController.Presets)
        {
            weir.SetCrest(crest);
            float dy = weir.Weir.position.y - w0.y;
            float fy = weir.FieldWater.position.y - f0.y;
            float ang = Quaternion.Angle(wheelR0, weir.Wheel.rotation);
            float expectAng = Mathf.Abs(Mathf.DeltaAngle(0f, weir.WheelTurns * 360f));
            bool fieldOn = weir.FieldWater.gameObject.activeSelf;
            bool lowOn = weir.FieldLowWater != null && weir.FieldLowWater.gameObject.activeSelf;
            bool ok = Mathf.Abs(dy - (crest - 0.28f)) < 1e-4f && Mathf.Abs(fy - (crest - 0.28f)) < 1e-4f &&
                      Mathf.Abs(ang - expectAng) < 0.05f && fieldOn == (crest >= 0.125f) && lowOn == (crest < 0.125f);
            allOk &= ok;
            tests.Add($"{{\"state\":\"{name}\",\"crest_z\":{G(crest)},\"weir_dy_m\":{G(dy)},\"field_dy_m\":{G(fy)}," +
                      $"\"wheel_deg\":{G(ang)},\"wheel_deg_expected\":{G(expectAng)},\"field_visible\":{B(fieldOn)}," +
                      $"\"field_low_visible\":{B(lowOn)},\"ok\":{B(ok)}}}");
            WaterworksImportCheck.Shoot(cam, Path.Combine(shots, $"unity_weir_{name}.png"), 1100, 820);
        }
        weir.SetCrest(FieldWeirController.MaxCrest);

        // 水路檢查：關閘 → 開閘（疊板卡滿）→ 疊板降下 → 關閘 → 疊板升回，每段 20 秒（模擬時間，每步 0.05 秒）
        var netTests = new List<string>();
        bool netOk = true;
        string Wet() => string.Join(",", network.nodes.Where(n => !n.source).SelectMany(n =>
            n.segments.Select(s => $"\"{n.id}.{s.name}\":{G(Mathf.Round(s.level * 1000f) / 1000f)}")));
        bool Full(string id, int occ, string seg) => network.Find(id, occ).segments.First(s => s.name == seg).level >= 0.999f;
        bool Dry(string id, int occ, string seg) => network.Find(id, occ).segments.First(s => s.name == seg).level <= 0.001f;
        void Run20() { for (int k = 0; k < 400; k++) network.Step(0.05f); }
        void Check(string phase, bool ok)
        {
            netOk &= ok;
            netTests.Add($"{{\"phase\":\"{phase}\",\"ok\":{B(ok)},\"levels\":{{{Wet()}}}}}");
        }
        gate.SetOpen(false, true);
        network.ResetDry();
        Run20();
        Check("gate_closed_start", Full("B01", 0, "outlet") && Full("B02", 0, "water") && Full("B05", 0, "upstream") &&
                                   Dry("B05", 0, "downstream") && Dry("B02", 1, "water") && Dry("F01", 0, "inlet") &&
                                   Dry("F01", 0, "field") && Dry("B02-V05", 0, "water") && !weir.FieldWaterVisible);
        ShootTopAndChain(cam, shots, "closed", chainCam, chainTarget);
        gate.open = true;
        Run20();
        Check("gate_opened_planks_full", Full("B05", 0, "downstream") && Full("B02", 1, "water") &&
                                         Full("F01", 0, "field") && Dry("F01", 0, "outlet") &&
                                         Dry("B02-V05", 0, "water") && weir.FieldWaterVisible && weir.Holding);
        ShootTopAndChain(cam, shots, "open", chainCam, chainTarget);
        weir.SetCrest(FieldWeirController.MinCrest);
        Run20();
        Check("planks_lowered", Full("F01", 0, "outlet") && Full("B02-V05", 0, "water") && weir.FieldLowVisible &&
                                !weir.Holding);
        ShootTopAndChain(cam, shots, "release", chainCam, chainTarget);
        gate.open = false;
        Run20();
        Check("gate_closed_drained", Full("B05", 0, "upstream") && Dry("B05", 0, "downstream") && Dry("B02", 1, "water") &&
                                     Dry("F01", 0, "inlet") && Dry("F01", 0, "field") && Dry("F01", 0, "outlet") &&
                                     Dry("B02-V05", 0, "water"));
        weir.SetCrest(FieldWeirController.MaxCrest);
        gate.open = true;
        Run20();
        Check("planks_raised_refill", Full("F01", 0, "field") && Dry("F01", 0, "outlet") && Dry("B02-V05", 0, "water"));
        gate.SetOpen(false, true);
        weir.SetCrest(FieldWeirController.MaxCrest);
        network.ResetDry();
        Run20();                                                  // 存檔與其餘截圖用「閘門關、疊板卡滿」的狀態
        cam.orthographic = false;
        cam.transform.position = rec.overviewPosition;
        cam.transform.LookAt(rec.overviewTarget);
        WaterworksImportCheck.Shoot(cam, Path.Combine(shots, "unity_demo_overview.png"), 1600, 900);
        cam.transform.position = rec.shots[0].position;
        cam.transform.LookAt(rec.shots[0].target);
        WaterworksImportCheck.Shoot(cam, Path.Combine(shots, "unity_demo_stream.png"), 1600, 900);

        Directory.CreateDirectory(Path.GetDirectoryName(Path.Combine(RepoRoot, "tools", "qingxi-waterworks-b", "unity", ScenePath)));
        EditorSceneManager.SaveScene(EditorSceneManager.GetActiveScene(), ScenePath);

        var json = new StringBuilder("{\n");
        json.Append($"  \"route\": \"stream_test\",\n  \"pieces\": {pieces.Count},\n");
        json.Append($"  \"scene\": \"tools/qingxi-waterworks-b/unity/{ScenePath}\",\n");
        json.Append($"  \"weir_tests_ok\": {B(allOk)},\n");
        json.Append("  \"weir_tests\": [\n    ").Append(string.Join(",\n    ", tests)).Append("\n  ],\n");
        json.Append($"  \"network_tests_ok\": {B(netOk)},\n");
        json.Append("  \"network_tests\": [\n    ").Append(string.Join(",\n    ", netTests)).Append("\n  ]");

        var args = System.Environment.GetCommandLineArgs();
        var bi = System.Array.IndexOf(args, "-qxBuild");
        if (bi >= 0 && bi + 1 < args.Length)
        {
            PlayerSettings.productName = "QingxiStreamDemo";
            PlayerSettings.fullScreenMode = FullScreenMode.Windowed;
            PlayerSettings.defaultScreenWidth = 1280;
            PlayerSettings.defaultScreenHeight = 720;
            PlayerSettings.runInBackground = true;
            var report = BuildPipeline.BuildPlayer(new BuildPlayerOptions
            {
                scenes = new[] { ScenePath },
                locationPathName = args[bi + 1],
                target = BuildTarget.StandaloneWindows64,
                options = BuildOptions.None,
            });
            json.Append($",\n  \"player_build\": \"{report.summary.result}\"");
            Debug.Log($"[WaterworksDemo] build {report.summary.result} → {args[bi + 1]}");
        }
        json.Append("\n}\n");
        var outPath = Path.Combine(RepoRoot, "art", "source", "qingxi-waterworks-b", "unity_demo_report.json");
        File.WriteAllText(outPath, json.ToString(), new UTF8Encoding(false));
        Debug.Log($"[WaterworksDemo] weir tests ok={allOk}; network tests ok={netOk}; wrote {outPath}");
    }

    // 一件的水面分段（依水流先後）。名稱來自 Blender 的 flows／water_polys：WATER_<件號>_<名稱>
    static WaterNetwork.Node BuildNode(string id, GameObject go, GateController gate, FieldWeirController weir)
    {
        var node = new WaterNetwork.Node { id = id, source = id == "S01" };
        // 只有一個水面的 FBX，Unity 會把那個網格當根物件並改用檔名（<件號>_water）
        var waters = go.GetComponentsInChildren<Transform>(true).Where(t => t.name.StartsWith("WATER_") ||
            (t.name == id + "_water" && t.GetComponent<MeshRenderer>() != null)).ToList();
        if (waters.Count == 0) return node;                      // S01 自身就是水；S02、B06 沒有水面
        Transform W(string suffix) => waters.First(t => t.name.EndsWith("_" + suffix));
        WaterNetwork.Segment Seg(string name, float sec, params Transform[] ts) =>
            new WaterNetwork.Segment { name = name, fillSeconds = sec, waters = ts };
        switch (id)
        {
            case "B01":
                node.segments.Add(Seg("intake", 0.4f, W("intake")));
                node.segments.Add(Seg("basin", 1.0f, W("basin")));
                node.segments.Add(Seg("outlet", 0.4f, W("outlet")));
                break;
            case "B05":
                node.gate = gate;
                node.gateBefore = 1;
                node.segments.Add(Seg("upstream", 0.5f, W("upstream")));
                node.segments.Add(Seg("downstream", 0.5f, W("downstream")));
                break;
            case "F01":
                node.field = weir;
                node.segments.Add(Seg("inlet", 0.6f, W("inlet")));
                var field = Seg("field", 6f);
                field.waters = new Transform[0];
                field.fieldWater = true;
                field.holds = true;
                node.segments.Add(field);
                var outlet = Seg("outlet", 0.6f, W("outlet"));
                outlet.needsRelease = true;
                node.segments.Add(outlet);
                break;
            default:
                node.segments.Add(Seg("water", 0.6f, waters.ToArray()));
                break;
        }
        return node;
    }

    static void ShootTopAndChain(Camera cam, string dir, string tag, Vector3 chainCam, Vector3 chainTarget)
    {
        cam.orthographic = true;                                  // 正上方正交：對照 Blender 的 stream_test_top
        cam.orthographicSize = 7.5f;
        cam.transform.position = new Vector3(4.5f, 30f, 6f);
        cam.transform.rotation = Quaternion.Euler(90f, 0f, 0f);
        WaterworksImportCheck.Shoot(cam, Path.Combine(dir, $"unity_network_{tag}_top.png"), 1600, 1200);
        cam.orthographic = false;
        cam.transform.position = chainCam;
        cam.transform.LookAt(chainTarget);
        WaterworksImportCheck.Shoot(cam, Path.Combine(dir, $"unity_network_{tag}.png"), 1600, 900);
    }

    // routes.json 裡某條路線的 (件號, Blender 4×4 矩陣)
    static List<(string id, Matrix4x4 m)> ReadRoute(string key)
    {
        var text = File.ReadAllText(Path.Combine(RepoRoot, "art", "source", "qingxi-waterworks-b", "routes.json"));
        var start = Regex.Match(text, $"\"key\":\\s*\"{key}\"").Index;
        var end = text.IndexOf("\"key\":", start + 6, System.StringComparison.Ordinal);
        var section = end < 0 ? text.Substring(start) : text.Substring(start, end - start);
        var list = new List<(string, Matrix4x4)>();
        var rx = new Regex("\"id\":\\s*\"([^\"]+)\",\\s*\"label\":\\s*\"[^\"]*\",\\s*\"matrix\":\\s*\\[\\s*" +
                           "\\[([^\\]]+)\\],\\s*\\[([^\\]]+)\\],\\s*\\[([^\\]]+)\\],\\s*\\[([^\\]]+)\\]\\s*\\]");
        foreach (Match mt in rx.Matches(section))
        {
            var m = new Matrix4x4();
            for (int r = 0; r < 4; r++)
            {
                var v = mt.Groups[r + 2].Value.Split(',').Select(s => float.Parse(s.Trim(), CultureInfo.InvariantCulture)).ToArray();
                m.SetRow(r, new Vector4(v[0], v[1], v[2], v[3]));
            }
            list.Add((mt.Groups[1].Value, m));
        }
        if (list.Count == 0) throw new System.Exception($"routes.json 找不到路線 {key}");
        return list;
    }

    static Matrix4x4 ToUnity(Matrix4x4 m)
    {
        var p = new Matrix4x4();
        p.SetRow(0, new Vector4(1, 0, 0, 0));
        p.SetRow(1, new Vector4(0, 0, 1, 0));
        p.SetRow(2, new Vector4(0, 1, 0, 0));
        p.SetRow(3, new Vector4(0, 0, 0, 1));
        return p * m * p;
    }

    static string G(float v) => v.ToString("0.#####", CultureInfo.InvariantCulture);
    static string B(bool b) => b ? "true" : "false";
}
