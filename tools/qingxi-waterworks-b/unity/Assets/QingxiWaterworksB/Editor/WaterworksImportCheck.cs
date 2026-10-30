// 青溪水工 B：Unity 匯入檢查（批次模式）。
//
//   Unity.exe -batchmode -projectPath tools/qingxi-waterworks-b/unity -executeMethod WaterworksImportCheck.Run -quit -logFile <log>
//
// 1. 依 Blender 的材質規格建立共用材質（名稱與 FBX 內材質相同，Qingxi/StandardVC 著色器）。
// 2. 每個 FBX 依材質名稱重新對應到這些材質後重新匯入。
// 3. 量測每件的尺寸、三角面、材質、子物件（gate、wheel、SOCKET_*），寫入 unity_import_report.json。
// 4. 擺出 13 件與一段直線拼接，存場景並渲染兩張截圖到 art/previews/qingxi-waterworks-b/。
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

public static class WaterworksImportCheck
{
    const string Root = "Assets/QingxiWaterworksB";
    const string ModelDir = Root + "/Models";
    const string TexDir = Root + "/Textures";
    const string MatDir = Root + "/Materials";
    const string ScenePath = Root + "/Scenes/ImportCheck.unity";

    // 與 kit_lib.MAT_SPECS 對應：roughness → smoothness = 1 - roughness
    static readonly (string name, string tex, Color color, float metal, float rough, float normal)[] Specs =
    {
        ("ww_stone", "ww_stone", Color.white, 0f, 0.84f, 0.6f),
        ("ww_stone_moss", "ww_stone_moss", Color.white, 0f, 0.92f, 0.6f),
        ("ww_wood", "ww_wood", Color.white, 0f, 0.80f, 0f),
        ("ww_bronze", "ww_bronze", Color.white, 0.9f, 0.30f, 0f),
        ("ww_soil", "ww_soil", Color.white, 0f, 0.95f, 0f),
        ("ww_gasket", null, new Color(0.10f, 0.085f, 0.07f), 0f, 0.9f, 0f),
        ("ww_seal", null, new Color(0.40f, 0.20f, 0.12f), 0f, 0.95f, 0f),
        ("ww_cloth", null, new Color(0.56f, 0.12f, 0.07f), 0f, 0.85f, 0f),
        ("ww_rope", null, new Color(0.20f, 0.14f, 0.075f), 0f, 0.95f, 0f),
        ("ww_iron", null, new Color(0.30f, 0.30f, 0.29f), 0.7f, 0.55f, 0f),
        ("ww_field_soil", "ww_field_soil", Color.white, 0f, 0.95f, 0.6f),
        ("ww_grass", null, new Color(0.15f, 0.25f, 0.07f), 0f, 0.9f, 0f),
        ("ww_riverbed", "ww_riverbed", Color.white, 0f, 0.92f, 0.6f),
    };

    // 水面材質（Qingxi/WaterFlow）：色調 A＝透明度；tiling 依 UV 尺度換成約 0.8–1.8 m 一格；速度單位 UV/秒
    //   ww_stream：S01 溪流（U 橫跨 1.8 m、V＝沿流 m×0.6）；ww_water：石槽／田溝帶狀水面（U 橫跨 0.39 m、V＝沿流 m）
    //   ww_water_still：田面積水（UV＝平面 m），慢速、斜向微動
    static readonly (string name, Color tint, Vector2 tiling, Vector2 dir, float s1, float s2, float vc, float bump)[]
        WaterSpecs =
    {
        ("ww_stream", new Color(1f, 1f, 1f, 0.72f), new Vector2(1f, 1f), new Vector2(0f, 1f), 0.30f, 0.17f, 1f, 0.5f),
        ("ww_water", new Color(0.62f, 0.86f, 0.86f, 0.42f), new Vector2(0.5f, 1.25f), new Vector2(0f, 1f), 0.40f, 0.23f,
            0f, 0.7f),
        ("ww_water_still", new Color(0.55f, 0.78f, 0.74f, 0.62f), new Vector2(0.6f, 0.6f), new Vector2(0.6f, 0.8f),
            0.03f, 0.018f, 0f, 0.25f),
    };

    const string WaterDir = ModelDir + "/Water";        // <件號>_water.fbx：與本體同原點，掛成子物件

    static string RepoRoot => Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", "..", ".."));

    public static void Run()
    {
        var log = new StringBuilder();
        PlayerSettings.colorSpace = ColorSpace.Linear;
        SetupTextures();
        var mats = BuildMaterials();
        var allModels = AssetDatabase.FindAssets("t:Model", new[] { ModelDir })
            .Select(AssetDatabase.GUIDToAssetPath).OrderBy(p => p).ToList();
        var models = allModels.Where(p => !p.StartsWith(WaterDir + "/")).ToList();
        foreach (var path in allModels)
        {
            var imp = (ModelImporter)AssetImporter.GetAtPath(path);
            imp.globalScale = 1f;
            imp.useFileScale = true;
            imp.bakeAxisConversion = true;
            imp.materialImportMode = ModelImporterMaterialImportMode.ImportStandard;
            imp.materialLocation = ModelImporterMaterialLocation.InPrefab;
            imp.importAnimation = false;
            imp.addCollider = false;
            imp.SaveAndReimport();
            foreach (var src in AssetDatabase.LoadAllAssetsAtPath(path).OfType<Material>().ToList())
            {
                if (mats.TryGetValue(src.name, out var pm))
                    imp.AddRemap(new AssetImporter.SourceAssetIdentifier(typeof(Material), src.name), pm);
                else
                    log.AppendLine($"{path}: 材質 {src.name} 沒有對應的專案材質");
            }
            imp.SaveAndReimport();
        }

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
        QualitySettings.shadowResolution = ShadowResolution.VeryHigh;
        QualitySettings.antiAliasing = 8;

        var ground = GameObject.CreatePrimitive(PrimitiveType.Plane);
        ground.name = "Ground";
        ground.transform.localScale = new Vector3(4f, 1f, 4f);
        var gm = new Material(Shader.Find("Standard")) { color = new Color(0.30f, 0.30f, 0.27f) };
        gm.SetFloat("_Glossiness", 0.05f);
        ground.GetComponent<Renderer>().sharedMaterial = gm;

        var reports = new List<string>();
        var placed = new Dictionary<string, GameObject>();
        int col = 0, row = 0;
        var large = new List<GameObject>();
        foreach (var path in models)
        {
            var id = Path.GetFileNameWithoutExtension(path);
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(path);
            var go = (GameObject)PrefabUtility.InstantiatePrefab(prefab);
            var b0 = Bounds(go);
            placed[id] = go;
            reports.Add(Measure(id, path, go, mats));
            AttachWater(id, go);
            if (b0.size.x > 2.2f || b0.size.z > 2.2f) { large.Add(go); continue; }   // 田地等大件另排一列
            var cell = new Vector3(col * 2.3f - 5.75f, 0f, -row * 2.4f + 4.2f);
            go.transform.position = cell - new Vector3(b0.center.x, 0f, b0.center.z);
            if (++col == 6) { col = 0; row++; }
        }
        float lz = 3.0f;                                  // 大件排在網格右側，由上往下
        foreach (var go in large)
        {
            // S02 河床河岸與 S01 溪流同原點：直接疊在 S01 的位置
            if (go.name == "S02" && placed.TryGetValue("S01", out var s01))
            {
                go.transform.position = s01.transform.position;
                continue;
            }
            var b0 = Bounds(go);
            // S 開頭（溪流）原點在水面、下半埋在地面以下：抬到底面貼地，避免與地面平面穿插
            var lift = go.name.StartsWith("S") ? -b0.min.y + 0.005f : 0f;
            go.transform.position = new Vector3(7.6f + b0.size.x / 2f, lift, lz - b0.size.z / 2f)
                                    - new Vector3(b0.center.x, 0f, b0.center.z);
            lz -= b0.size.z + 0.6f;
        }
        Directory.CreateDirectory(Path.Combine(Application.dataPath, "QingxiWaterworksB", "Scenes"));
        var shots = Path.Combine(RepoRoot, "art", "previews", "qingxi-waterworks-b");
        Directory.CreateDirectory(shots);
        var cam = new GameObject("Camera").AddComponent<Camera>();
        cam.clearFlags = CameraClearFlags.SolidColor;
        cam.backgroundColor = new Color(0.45f, 0.46f, 0.44f);
        cam.fieldOfView = 30f;
        cam.nearClipPlane = 0.05f;
        cam.depthTextureMode |= DepthTextureMode.Depth;     // 水面著色器要深度貼圖（淺處淡出、岸邊泡沫）
        cam.transform.position = new Vector3(2.6f, 15.5f, -15.0f);
        cam.transform.LookAt(new Vector3(2.6f, 0.2f, -0.2f));
        Shoot(cam, Path.Combine(shots, "unity_import_all.png"), 2200, 1240);

        // 直線拼接：依 B02 的長邊方向與入口所在一端決定流向，逐件首尾相接
        foreach (var go in placed.Values) go.SetActive(false);
        var chainIds = new[] { "B02", "B02-V02", "B05", "B02-V04", "B02" };
        var flow = FlowDirection(placed["B02"]);
        var origin = new Vector3(-2.5f, 0f, 0f);
        var cursor = origin;
        var chain = new GameObject("Chain");
        var chainLen = new List<string>();
        foreach (var id in chainIds)
        {
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>($"{ModelDir}/{id}.fbx");
            var go = (GameObject)PrefabUtility.InstantiatePrefab(prefab, chain.transform);
            go.transform.position = cursor;
            AttachWater(id, go);
            var len = Vector3.Dot(Bounds(go).size, Abs(flow));
            var nominal = id == "B02-V04" ? 0.5f : 1.0f;
            chainLen.Add($"{{\"id\":\"{id}\",\"bounds_len_m\":{F(len)},\"nominal_m\":{F(nominal)}}}");
            cursor += flow * nominal;
        }
        var mid = (origin + cursor) * 0.5f;
        var side = Vector3.Cross(Vector3.up, flow).normalized;
        cam.fieldOfView = 34f;
        cam.transform.position = mid - side * 5.2f + Vector3.up * 3.0f - flow * 1.6f;
        cam.transform.LookAt(mid + Vector3.up * 0.25f);
        Shoot(cam, Path.Combine(shots, "unity_import_chain.png"), 2200, 1240);
        var frames = Path.Combine(shots, "unity_water_frames");
        Directory.CreateDirectory(frames);
        cam.transform.position = mid - side * 1.3f + Vector3.up * 1.2f - flow * 0.9f;   // 石槽特寫，看得到水面捲動
        cam.transform.LookAt(mid + Vector3.up * 0.2f);
        ShootFlowFrames(cam, Path.Combine(frames, "chain"));
        foreach (var go in placed.Values) go.SetActive(true);
        chain.SetActive(false);

        // 溪流特寫：S01＋S02，從下游斜上方看
        if (placed.TryGetValue("S01", out var st))
        {
            var sb = Bounds(st);
            cam.fieldOfView = 40f;
            cam.transform.position = sb.center + new Vector3(-2.6f, 2.4f, -3.2f);
            cam.transform.LookAt(sb.center + new Vector3(0f, -0.1f, 0.6f));
            Shoot(cam, Path.Combine(shots, "unity_water_stream.png"), 1600, 1000);
            ShootFlowFrames(cam, Path.Combine(frames, "stream"));
        }
        EditorSceneManager.SaveScene(EditorSceneManager.GetActiveScene(), ScenePath);

        var json = new StringBuilder();
        json.Append("{\n  \"unity_version\": \"").Append(Application.unityVersion).Append("\",\n");
        json.Append("  \"color_space\": \"").Append(PlayerSettings.colorSpace).Append("\",\n");
        json.Append("  \"render_pipeline\": \"Built-in\",\n");
        json.Append("  \"graphics_device\": \"").Append(SystemInfo.graphicsDeviceType).Append("\",\n");
        json.Append("  \"flow_axis_unity\": [").Append(F(flow.x)).Append(", ").Append(F(flow.y)).Append(", ")
            .Append(F(flow.z)).Append("],\n");
        json.Append("  \"pieces\": [\n    ").Append(string.Join(",\n    ", reports)).Append("\n  ],\n");
        json.Append("  \"water_shader\": \"Qingxi/WaterFlow (alpha:premul, ZWrite Off, 2-layer UV scroll)\",\n");
        json.Append("  \"water\": [").Append(string.Join(", ", WaterReports)).Append("],\n");
        json.Append("  \"chain\": [").Append(string.Join(", ", chainLen)).Append("],\n");
        json.Append("  \"screenshots\": [\"art/previews/qingxi-waterworks-b/unity_import_all.png\", ")
            .Append("\"art/previews/qingxi-waterworks-b/unity_import_chain.png\", ")
            .Append("\"art/previews/qingxi-waterworks-b/unity_water_stream.png\"],\n");
        json.Append("  \"import_warnings\": \"").Append(log.ToString().Replace("\\", "/").Replace("\"", "'")
            .Replace("\r", "").Replace("\n", " | ")).Append("\",\n");
        json.Append("  \"scene\":\"tools/qingxi-waterworks-b/unity/").Append(ScenePath).Append("\"\n}\n");
        var outPath = Path.Combine(RepoRoot, "art", "source", "qingxi-waterworks-b", "unity_import_report.json");
        File.WriteAllText(outPath, json.ToString(), new UTF8Encoding(false));
        Debug.Log("[WaterworksImportCheck] wrote " + outPath);
    }

    static void SetupTextures()
    {
        foreach (var guid in AssetDatabase.FindAssets("t:Texture2D", new[] { TexDir }))
        {
            var p = AssetDatabase.GUIDToAssetPath(guid);
            var ti = (TextureImporter)AssetImporter.GetAtPath(p);
            var normal = p.EndsWith("_n.png");
            ti.textureType = normal ? TextureImporterType.NormalMap : TextureImporterType.Default;
            ti.sRGBTexture = !normal;
            ti.wrapMode = TextureWrapMode.Repeat;
            ti.anisoLevel = 4;
            ti.maxTextureSize = 1024;
            ti.SaveAndReimport();
        }
    }

    static Dictionary<string, Material> BuildMaterials()
    {
        Directory.CreateDirectory(Path.Combine(Application.dataPath, "QingxiWaterworksB", "Materials"));
        var shader = Shader.Find("Qingxi/StandardVC");
        if (shader == null) throw new System.Exception("找不到 Qingxi/StandardVC 著色器");
        var result = new Dictionary<string, Material>();
        foreach (var s in Specs)
        {
            var path = $"{MatDir}/{s.name}.mat";
            var m = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (m == null)
            {
                m = new Material(shader);
                AssetDatabase.CreateAsset(m, path);
            }
            m.shader = shader;
            m.name = s.name;
            m.color = s.color;
            m.mainTexture = s.tex == null ? null : AssetDatabase.LoadAssetAtPath<Texture2D>($"{TexDir}/{s.tex}.png");
            if (s.normal > 0f)
            {
                // 有專屬法線圖（<貼圖>_n.png）就用，否則共用石材法線
                var bump = AssetDatabase.LoadAssetAtPath<Texture2D>($"{TexDir}/{s.tex}_n.png")
                           ?? AssetDatabase.LoadAssetAtPath<Texture2D>($"{TexDir}/ww_stone_n.png");
                m.SetTexture("_BumpMap", bump);
                m.SetFloat("_BumpScale", s.normal);
            }
            m.SetFloat("_Metallic", s.metal);
            m.SetFloat("_Glossiness", 1f - s.rough);
            m.SetFloat("_UseVertexColor", 1f);
            EditorUtility.SetDirty(m);
            result[s.name] = m;
        }
        var water = Shader.Find("Qingxi/WaterFlow");
        if (water == null) throw new System.Exception("找不到 Qingxi/WaterFlow 著色器");
        var wtex = AssetDatabase.LoadAssetAtPath<Texture2D>($"{TexDir}/ww_stream.png");
        var wbump = AssetDatabase.LoadAssetAtPath<Texture2D>($"{TexDir}/ww_stream_n.png");
        foreach (var s in WaterSpecs)
        {
            var path = $"{MatDir}/{s.name}.mat";
            var m = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (m == null)
            {
                m = new Material(water);
                AssetDatabase.CreateAsset(m, path);
            }
            m.shader = water;
            m.name = s.name;
            m.color = s.tint;
            m.mainTexture = wtex;
            m.mainTextureScale = s.tiling;
            m.SetTexture("_BumpMap", wbump);
            m.SetFloat("_BumpScale", s.bump);
            m.SetVector("_FlowDir", new Vector4(s.dir.x, s.dir.y, 0f, 0f));
            m.SetFloat("_Speed1", s.s1);
            m.SetFloat("_Speed2", s.s2);
            m.SetFloat("_UseVertexColor", s.vc);
            m.renderQueue = (int)RenderQueue.Transparent;
            EditorUtility.SetDirty(m);
            result[s.name] = m;
        }
        AssetDatabase.SaveAssets();
        return result;
    }

    static readonly List<string> WaterReports = new List<string>();

    // <件號>_water.fbx 掛在本體下（兩者在 Blender 同原點輸出）。
    // 兩個 FBX 的根物件各自可能帶匯入姿態（x 軸 ±90°），所以先扣掉本體的匯入姿態得到「件的座標系」，再套水面自己的匯入姿態。
    internal static void AttachWater(string id, GameObject go)
    {
        var prefab = AssetDatabase.LoadAssetAtPath<GameObject>($"{WaterDir}/{id}_water.fbx");
        if (prefab == null) return;
        var src = PrefabUtility.GetCorrespondingObjectFromSource(go) ?? go;
        var baseRot = go.transform.rotation * Quaternion.Inverse(src.transform.localRotation);
        var basePos = go.transform.position - baseRot * src.transform.localPosition;
        var w = (GameObject)PrefabUtility.InstantiatePrefab(prefab, go.transform);
        w.transform.SetPositionAndRotation(basePos + baseRot * prefab.transform.localPosition,
                                           baseRot * prefab.transform.localRotation);
        w.transform.localScale = Vector3.one;
        if (WaterReports.Any(r => r.Contains($"\"id\":\"{id}\""))) return;
        int tris = w.GetComponentsInChildren<MeshFilter>(true).Sum(mf => mf.sharedMesh.triangles.Length / 3);
        var names = w.GetComponentsInChildren<Renderer>(true).SelectMany(r => r.sharedMaterials)
            .Select(m => m == null ? "(null)" : $"{m.name}:{m.shader.name}").Distinct().OrderBy(n => n);
        WaterReports.Add($"{{\"id\":\"{id}\",\"tris\":{tris}," +
                         $"\"materials\":[{string.Join(",", names.Select(n => $"\"{n}\""))}]}}");
    }

    // 逐格推進水面時間（全域 _QxWaterTimeOffset），每格 1/8 秒、共 16 格，合成 GIF 檢查流動
    static void ShootFlowFrames(Camera cam, string prefix)
    {
        for (int i = 0; i < 16; i++)
        {
            Shader.SetGlobalFloat("_QxWaterTimeOffset", i / 8f);
            Shoot(cam, $"{prefix}_{i:00}.png", 800, 500);
        }
        Shader.SetGlobalFloat("_QxWaterTimeOffset", 0f);
    }

    static string Measure(string id, string path, GameObject go, Dictionary<string, Material> mats)
    {
        var b = Bounds(go);
        int tris = 0;
        bool vcol = true;
        var matNames = new SortedSet<string>();
        var unmapped = new SortedSet<string>();
        int lod1 = 0, lod2 = 0;
        foreach (var mf in go.GetComponentsInChildren<MeshFilter>(true))
        {
            var mesh = mf.sharedMesh;
            var n = mesh.triangles.Length / 3;
            if (mf.name.EndsWith("_LOD1")) lod1 += n;          // v002：LOD 與 LOD0 同一個 FBX，分開計數
            else if (mf.name.EndsWith("_LOD2")) lod2 += n;
            else tris += n;
            vcol &= mesh.colors32 != null && mesh.colors32.Length == mesh.vertexCount;
        }
        var lodGroup = go.GetComponent<LODGroup>();
        foreach (var r in go.GetComponentsInChildren<Renderer>(true))
            foreach (var m in r.sharedMaterials)
            {
                if (m == null) { unmapped.Add("(null)"); continue; }
                var n = m.name.Split(' ')[0];
                matNames.Add(n);
                if (!mats.TryGetValue(n, out var pm) || pm != m) unmapped.Add(m.name);
            }
        var children = go.GetComponentsInChildren<Transform>(true).Where(t => t != go.transform)
            .Select(t => t.name).Where(n => n == "gate" || n == "wheel" || n.StartsWith("SOCKET_")).Distinct()
            .OrderBy(n => n).ToList();
        var size = b.size;
        var minLocal = b.min - go.transform.position;
        var maxLocal = b.max - go.transform.position;
        return $"{{\"id\":\"{id}\",\"tris\":{tris},\"lod1_tris\":{lod1},\"lod2_tris\":{lod2}," +
               $"\"lod_group_levels\":{(lodGroup != null ? lodGroup.lodCount : 0)},\"size_m\":[{F(size.x)},{F(size.y)},{F(size.z)}]," +
               $"\"min_m\":[{F(minLocal.x)},{F(minLocal.y)},{F(minLocal.z)}]," +
               $"\"max_m\":[{F(maxLocal.x)},{F(maxLocal.y)},{F(maxLocal.z)}]," +
               $"\"vertex_colors\":{(vcol ? "true" : "false")}," +
               $"\"materials\":[{string.Join(",", matNames.Select(n => $"\"{n}\""))}]," +
               $"\"unmapped_materials\":[{string.Join(",", unmapped.Select(n => $"\"{n}\""))}]," +
               $"\"children\":[{string.Join(",", children.Select(n => $"\"{n}\""))}]}}";
    }

    static Vector3 FlowDirection(GameObject b02)
    {
        var b = Bounds(b02);
        var p = b02.transform.position;
        // 長邊（1 m）為流向軸；入口在原點，所以物件延伸到原點的哪一側就是流向
        if (b.size.x > b.size.z)
            return Mathf.Abs(b.min.x - p.x) < Mathf.Abs(b.max.x - p.x) ? Vector3.right : Vector3.left;
        return Mathf.Abs(b.min.z - p.z) < Mathf.Abs(b.max.z - p.z) ? Vector3.forward : Vector3.back;
    }

    static Bounds Bounds(GameObject go)
    {
        var rs = go.GetComponentsInChildren<Renderer>();
        var b = rs[0].bounds;
        foreach (var r in rs) b.Encapsulate(r.bounds);
        return b;
    }

    static Vector3 Abs(Vector3 v) => new Vector3(Mathf.Abs(v.x), Mathf.Abs(v.y), Mathf.Abs(v.z));

    static string F(float v) => v.ToString("0.####", System.Globalization.CultureInfo.InvariantCulture);

    internal static void Shoot(Camera cam, string file, int w, int h)
    {
        var rt = new RenderTexture(w, h, 24, RenderTextureFormat.ARGB32, RenderTextureReadWrite.sRGB)
        { antiAliasing = 8 };
        cam.targetTexture = rt;
        cam.Render();
        RenderTexture.active = rt;
        var tex = new Texture2D(w, h, TextureFormat.RGB24, false);
        tex.ReadPixels(new Rect(0, 0, w, h), 0, 0);
        tex.Apply();
        File.WriteAllBytes(file, tex.EncodeToPNG());
        RenderTexture.active = null;
        cam.targetTexture = null;
        Object.DestroyImmediate(rt);
        Object.DestroyImmediate(tex);
    }
}
