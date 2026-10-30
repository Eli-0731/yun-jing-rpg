// 青溪水工 B：古水路修復可玩場景（批次模式產生）。
//
//   Unity.exe -batchmode -quit -projectPath tools/qingxi-waterworks-b/unity -executeMethod WaterworksPuzzleBuild.Build
//             -logFile <log> [-qxBuild <exe 路徑>]
//
// 1. 把 tools/qingxi-waterworks-b/data 的 board／catalog／fixture-observations 複製到 Assets/QingxiWaterworksB/Data（播放器讀這份；來源以 data/ 為準）。
// 2. 擺 B01 取水基座（原點）、S01／S02 溪流（沿用 routes.json stream_test 中與 B01 的相對位置）、F01 村田（田區端點 (0, 6)）、
//    B11 手推車、B12 完工碑，座標與網頁版 main.js 相同（Blender 平面 → Unity (x, z, y)）。
// 3. 每種段件做一個隱藏的範本（本體＋水面；B05 加 B06 閘輪與 GateController），執行時依版面複製到槽位。
// 4. 存成 Scenes/WaterworksPuzzle.unity；有 -qxBuild 時輸出 Windows 播放器。
using System.Collections.Generic;
using System.IO;
using System.Linq;
using QingxiWaterworksB;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

public static class WaterworksPuzzleBuild
{
    const string ScenePath = "Assets/QingxiWaterworksB/Scenes/WaterworksPuzzle.unity";
    const string ModelDir = "Assets/QingxiWaterworksB/Models";
    const string MatDir = "Assets/QingxiWaterworksB/Materials";
    const string DataDir = "Assets/QingxiWaterworksB/Data";

    static string ToolRoot => Path.GetFullPath(Path.Combine(Application.dataPath, "..", ".."));
    static string RepoRoot => Path.GetFullPath(Path.Combine(ToolRoot, "..", ".."));

    public static void Build()
    {
        // data
        Directory.CreateDirectory(Path.Combine(Application.dataPath, "QingxiWaterworksB", "Data"));
        foreach (var f in new[] { "board.json", "catalog.json", "fixture-observations.json" })
            File.Copy(Path.Combine(ToolRoot, "data", f), Path.Combine(Application.dataPath, "QingxiWaterworksB", "Data", f), true);
        AssetDatabase.Refresh();
        var ctx = WwCtx.Load(File.ReadAllText(Path.Combine(ToolRoot, "data", "board.json")), File.ReadAllText(Path.Combine(ToolRoot, "data", "catalog.json")), null);

        // materials
        var overlay = SaveMat("ww_ui_overlay", new Material(Shader.Find("Qingxi/OverlayColor")) { color = Color.white });
        var standard = SaveMat("ww_ui_standard", new Material(Shader.Find("Standard")) { color = Color.white });
        var fadeM = new Material(Shader.Find("Standard")) { color = new Color(1, 1, 1, 0.5f) };
        fadeM.SetFloat("_Mode", 2f);
        fadeM.SetOverrideTag("RenderType", "Transparent");
        fadeM.SetInt("_SrcBlend", (int)BlendMode.SrcAlpha);
        fadeM.SetInt("_DstBlend", (int)BlendMode.OneMinusSrcAlpha);
        fadeM.SetInt("_ZWrite", 0);
        fadeM.DisableKeyword("_ALPHATEST_ON");
        fadeM.EnableKeyword("_ALPHABLEND_ON");
        fadeM.DisableKeyword("_ALPHAPREMULTIPLY_ON");
        fadeM.renderQueue = (int)RenderQueue.Transparent;
        fadeM.SetFloat("_Glossiness", 0.3f);
        var fade = SaveMat("ww_ui_fade", fadeM);
        var groundM = new Material(Shader.Find("Standard")) { color = new Color32(0x66, 0x73, 0x4f, 255) };
        groundM.SetFloat("_Glossiness", 0.05f);
        var ground = SaveMat("ww_puzzle_ground", groundM);
        var waterFlow = AssetDatabase.LoadAssetAtPath<Material>($"{MatDir}/ww_water.mat");
        var waterStill = AssetDatabase.LoadAssetAtPath<Material>($"{MatDir}/ww_water_still.mat");

        // scene
        EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        RenderSettings.ambientMode = AmbientMode.Trilight;
        RenderSettings.ambientSkyColor = new Color(0.62f, 0.66f, 0.64f);
        RenderSettings.ambientEquatorColor = new Color(0.45f, 0.45f, 0.40f);
        RenderSettings.ambientGroundColor = new Color(0.24f, 0.22f, 0.19f);
        RenderSettings.fog = true;
        RenderSettings.fogMode = FogMode.Linear;
        RenderSettings.fogColor = new Color32(0xa9, 0xbc, 0xb3, 255);
        RenderSettings.fogStartDistance = 16f;
        RenderSettings.fogEndDistance = 34f;
        var sun = new GameObject("Sun").AddComponent<Light>();
        sun.type = LightType.Directional;
        sun.color = new Color(1f, 0.93f, 0.82f);
        sun.intensity = 1.3f;
        sun.shadows = LightShadows.Soft;
        sun.shadowStrength = 0.7f;
        sun.transform.rotation = Quaternion.LookRotation(B(-0.6, -3, 0) - B(-4, 2, 9));   // 對照網頁版太陽方向
        QualitySettings.shadowDistance = 30f;

        var plane = GameObject.CreatePrimitive(PrimitiveType.Plane);
        plane.name = "Ground";
        plane.transform.localScale = new Vector3(1.8f, 1f, 1.8f);
        plane.transform.position = B(-1, 3, -0.02);
        plane.GetComponent<Renderer>().sharedMaterial = ground;
        Object.DestroyImmediate(plane.GetComponent<Collider>());

        var scenery = new GameObject("Scenery").transform;
        var b01 = Place("B01", Matrix4x4.identity, scenery);
        WaterworksImportCheck.AttachWater("B01", b01);
        var routes = ReadRoute("stream_test");
        var mB01 = routes.First(r => r.id == "B01").m;
        foreach (var id in new[] { "S01", "S02" })
        {
            var rel = mB01.inverse * routes.First(r => r.id == id).m;   // 與取水基座的相對位置（stream_test 已驗證接口）
            Place(id, rel, scenery);
        }
        var field = ctx.board.terminals.First(t => t.kind == "field");
        var f01 = Place("F01", Matrix4x4.TRS(new Vector3((float)field.pos[0], (float)field.pos[1], 0), Quaternion.Euler(0, 0, (float)(WaterworksRules.YawOf(field.dir) * Mathf.Rad2Deg)), Vector3.one), scenery);
        WaterworksImportCheck.AttachWater("F01", f01);
        var weir = f01.AddComponent<FieldWeirController>();
        weir.Recapture();
        Place("B11", Matrix4x4.TRS(new Vector3(1.7f, -0.9f, 0), Quaternion.Euler(0, 0, -2.2f * Mathf.Rad2Deg), Vector3.one), scenery);
        var b12 = Place("B12", Matrix4x4.TRS(new Vector3(3.7f, 6.4f, 0), Quaternion.Euler(0, 0, 0.15f * 180f), Vector3.one), scenery);

        // piece templates
        var lib = new GameObject("Library").transform;
        var ids = new List<string>(); var templates = new List<GameObject>();
        foreach (var id in ctx.pieces.Keys)
        {
            var wrap = new GameObject("LIB_" + id);
            wrap.transform.SetParent(lib, false);
            var inst = Place(id, Matrix4x4.identity, wrap.transform);
            WaterworksImportCheck.AttachWater(id, inst);
            if (ctx.pieces[id].kind == "gate")
            {
                Place("B06", Matrix4x4.Translate(new Vector3(0.392f, 0.5f, 0.9f)), wrap.transform);   // 與網頁版相同的閘輪位置
                wrap.AddComponent<GateController>();
            }
            wrap.SetActive(false);
            ids.Add(id); templates.Add(wrap);
        }

        var cam = new GameObject("Camera").AddComponent<Camera>();
        cam.clearFlags = CameraClearFlags.SolidColor;
        cam.backgroundColor = new Color32(0xa9, 0xbc, 0xb3, 255);
        cam.fieldOfView = 38f;
        cam.nearClipPlane = 0.05f;
        cam.farClipPlane = 80f;
        cam.depthTextureMode |= DepthTextureMode.Depth;
        cam.gameObject.AddComponent<WaterDepthCamera>();
        cam.tag = "MainCamera";
        cam.transform.position = B(1.8, -4.4, 11.6);
        cam.transform.LookAt(B(-0.5, 4.0));

        var puzzle = new GameObject("WaterworksPuzzle").AddComponent<WaterworksPuzzle>();
        puzzle.boardJson = AssetDatabase.LoadAssetAtPath<TextAsset>($"{DataDir}/board.json");
        puzzle.catalogJson = AssetDatabase.LoadAssetAtPath<TextAsset>($"{DataDir}/catalog.json");
        puzzle.fixtureJson = AssetDatabase.LoadAssetAtPath<TextAsset>($"{DataDir}/fixture-observations.json");
        puzzle.libraryIds = ids; puzzle.libraryTemplates = templates;
        puzzle.cam = cam; puzzle.weir = weir;
        var f01Parts = f01.GetComponentsInChildren<Transform>(true);
        puzzle.fieldInlet = f01Parts.FirstOrDefault(t => t.name.EndsWith("_inlet") && t.name.StartsWith("WATER_"));
        puzzle.fieldOutlet = f01Parts.FirstOrDefault(t => t.name.EndsWith("_outlet") && t.name.StartsWith("WATER_"));
        var b12Parts = b12.GetComponentsInChildren<Transform>(true);
        puzzle.pegs = new[] { "peg_1", "peg_2", "peg_3" }.Select(p => b12Parts.FirstOrDefault(t => t.name.EndsWith(p))?.gameObject).ToArray();
        puzzle.waterFlow = waterFlow; puzzle.waterStill = waterStill; puzzle.overlay = overlay; puzzle.fade = fade; puzzle.standard = standard;

        var missing = new List<string>();
        if (puzzle.fieldInlet == null) missing.Add("F01 inlet");
        if (puzzle.fieldOutlet == null) missing.Add("F01 outlet");
        for (int k = 0; k < 3; k++) if (puzzle.pegs[k] == null) missing.Add($"B12 peg_{k + 1}");
        if (waterFlow == null || waterStill == null) missing.Add("water materials");
        foreach (var t in templates.Where(t => t.GetComponentsInChildren<Transform>(true).All(x => !x.name.EndsWith("_water")) && ctx.pieces[t.name.Substring(4)].kind != "patch"))
            missing.Add($"{t.name} water");
        Debug.Log($"[WaterworksPuzzleBuild] templates {templates.Count}; missing: {(missing.Count == 0 ? "none" : string.Join(", ", missing))}");

        EditorSceneManager.SaveScene(EditorSceneManager.GetActiveScene(), ScenePath);
        var scenes = EditorBuildSettings.scenes.Where(s => s.path != ScenePath).ToList();
        scenes.Insert(0, new EditorBuildSettingsScene(ScenePath, true));
        EditorBuildSettings.scenes = scenes.ToArray();

        var args = System.Environment.GetCommandLineArgs();
        var bi = System.Array.IndexOf(args, "-qxBuild");
        if (bi >= 0 && bi + 1 < args.Length)
        {
            PlayerSettings.productName = "QingxiWaterworks";
            PlayerSettings.fullScreenMode = FullScreenMode.Windowed;
            PlayerSettings.defaultScreenWidth = 1280;
            PlayerSettings.defaultScreenHeight = 720;
            PlayerSettings.resizableWindow = false;
            PlayerSettings.runInBackground = true;
            var report = BuildPipeline.BuildPlayer(new BuildPlayerOptions
            {
                scenes = new[] { ScenePath },
                locationPathName = args[bi + 1],
                target = BuildTarget.StandaloneWindows64,
                options = BuildOptions.None,
            });
            Debug.Log($"[WaterworksPuzzleBuild] build {report.summary.result} errors={report.summary.totalErrors} → {args[bi + 1]}");
            if (Application.isBatchMode) EditorApplication.Exit(report.summary.result == UnityEditor.Build.Reporting.BuildResult.Succeeded && missing.Count == 0 ? 0 : 1);
        }
    }

    static Vector3 B(double x, double y, double z = 0) => new Vector3((float)x, (float)z, (float)y);

    static Material SaveMat(string name, Material m)
    {
        var path = $"{MatDir}/{name}.mat";
        var old = AssetDatabase.LoadAssetAtPath<Material>(path);
        if (old != null) { old.shader = m.shader; old.CopyPropertiesFromMaterial(m); old.shaderKeywords = m.shaderKeywords; old.renderQueue = m.renderQueue; old.SetOverrideTag("RenderType", m.GetTag("RenderType", false)); EditorUtility.SetDirty(old); return old; }
        AssetDatabase.CreateAsset(m, path);
        return m;
    }

    // 以 Blender 4×4 矩陣擺放：Unity 姿態 = P·M·P，再乘上 FBX 根物件自帶的匯入姿態
    static GameObject Place(string id, Matrix4x4 m, Transform parent)
    {
        var prefab = AssetDatabase.LoadAssetAtPath<GameObject>($"{ModelDir}/{id}.fbx");
        if (prefab == null) throw new System.Exception($"找不到模型 {id}.fbx");
        var go = (GameObject)PrefabUtility.InstantiatePrefab(prefab, parent);
        var p = new Matrix4x4();
        p.SetRow(0, new Vector4(1, 0, 0, 0)); p.SetRow(1, new Vector4(0, 0, 1, 0)); p.SetRow(2, new Vector4(0, 1, 0, 0)); p.SetRow(3, new Vector4(0, 0, 0, 1));
        var u = p * m * p;
        var r = u.rotation;
        go.transform.SetPositionAndRotation((Vector3)u.GetColumn(3) + r * prefab.transform.localPosition, r * prefab.transform.localRotation);
        return go;
    }

    static List<(string id, Matrix4x4 m)> ReadRoute(string key)
    {
        var text = File.ReadAllText(Path.Combine(RepoRoot, "art", "source", "qingxi-waterworks-b", "routes.json"));
        var root = MiniJson.Parse(text);
        var list = root is List<object> l ? l : ((JObj)root).A("routes");
        var route = list.Cast<JObj>().First(r => r.S("key") == key);
        return route.A("pieces").Cast<JObj>().Select(pc =>
        {
            var m = new Matrix4x4();
            var rows = pc.A("matrix");
            for (int i = 0; i < 4; i++) { var v = ((List<object>)rows[i]).Select(x => (float)(double)x).ToArray(); m.SetRow(i, new Vector4(v[0], v[1], v[2], v[3])); }
            return (pc.S("id"), m);
        }).ToList();
    }
}
