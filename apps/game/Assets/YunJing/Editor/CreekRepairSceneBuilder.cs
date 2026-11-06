using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using YunJing.CreekRepair;

namespace YunJing.Editor
{
    // Work pack B-56h section 1 test scene: the waterworks board at 1:1 from the qingxi-waterworks-b exports, CR05 shelter and CR09 gate,
    // three F01 fields. Ground and anything not yet modelled is named Placeholder_*. Everything lands in gitignored folders.
    // Run: -executeMethod YunJing.Editor.CreekRepairSceneBuilder.Build
    public static class CreekRepairSceneBuilder
    {
        const string Scene = "Assets/YunJing/Generated/CreekRepair.unity";
        const string Root = "Assets/YunJing/Generated/CreekRepairScene";
        const string Own = "Assets/YunJing/Generated/CreekRepairB";
        static string Repo => Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", ".."));
        static string Ww => Path.Combine(Repo, "art", "exports", "qingxi-waterworks-b");
        static string Cr => Path.Combine(Repo, "art", "exports", "creek-repair-b");
        static readonly string[] Pieces = { "B01", "B02", "B02-V02", "B02-V03", "B02-V04", "B02-V05", "B03", "B03-V02", "B03-V03", "B03-V04", "B04-V02", "B05", "B06", "B07", "B07-V02", "B11", "B12", "F01" };

        static readonly string[] FieldGaps = { "F01_Field" };

        static readonly string[] Props = { "C03", "C04", "C06", "C07", "A04_SiltBar" };

        /// One group of a B-pack FBX as its own prefab, LOD0 only, moved to the prefab's origin when asked.
        static GameObject Extract(string id, Func<string, bool> keep, string file, Material material = null, bool toOrigin = false, Action<Transform> pose = null)
        {
            var go = PutOwn(null, id, Vector3.zero);
            var lod = go.GetComponent<LODGroup>(); if (lod != null) UnityEngine.Object.DestroyImmediate(lod);
            foreach (var t in go.GetComponentsInChildren<Transform>(true).Where(t => t != go.transform).ToArray())
            {
                if (t == null) continue;
                if (t.name.StartsWith("Socket_")) { UnityEngine.Object.DestroyImmediate(t.gameObject); continue; }
                bool wanted = t.name.EndsWith("_LOD0") && t.name != id + "_Collision" && keep(t.name.Substring(id.Length + 1));
                if (!wanted) { UnityEngine.Object.DestroyImmediate(t.gameObject); continue; }
                if (toOrigin) t.localPosition = Vector3.zero;
                pose?.Invoke(t);
                if (material != null) foreach (var r in t.GetComponents<Renderer>()) r.sharedMaterial = material;
            }
            var path = $"{Root}/{file}.prefab";
            var prefab = PrefabUtility.SaveAsPrefabAsset(go, path); UnityEngine.Object.DestroyImmediate(go); return prefab;
        }

        /// A channel's water model (its own FBX, same origin as the body) as a prefab, LOD0 only.
        static GameObject OwnWater(string id, string file, Material material)
        {
            var go = Put(null, AssetDatabase.LoadAssetAtPath<GameObject>($"{Own}/{id}/{id}_water_v001.fbx"), Vector3.zero);
            var lod = go.GetComponent<LODGroup>(); if (lod != null) UnityEngine.Object.DestroyImmediate(lod);
            foreach (var t in go.GetComponentsInChildren<Transform>(true).Where(t => t != go.transform).ToArray())
            {
                if (t == null) continue;
                if (!t.name.EndsWith("_LOD0")) { UnityEngine.Object.DestroyImmediate(t.gameObject); continue; }
                foreach (var r in t.GetComponents<Renderer>()) r.sharedMaterial = material;
            }
            var prefab = PrefabUtility.SaveAsPrefabAsset(go, $"{Root}/{file}.prefab"); UnityEngine.Object.DestroyImmediate(go); return prefab;
        }

        static GameObject Prop(Transform parent, string id, Vector3 at, float yaw = 0)
        {
            var asset = AssetDatabase.LoadAssetAtPath<GameObject>($"{Root}/{id}/{id}.fbx");
            if (asset == null) throw new FileNotFoundException(id);
            var go = Put(parent, asset, at, yaw); go.name = id; return go;
        }

        static void UsePipeline()
        {
            var pipeline = AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>("Assets/YunJing/Generated/URP.asset");
            if (pipeline == null) { ProjectBuilder.Generate(); pipeline = AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>("Assets/YunJing/Generated/URP.asset"); }
            if (GraphicsSettings.defaultRenderPipeline != pipeline) GraphicsSettings.defaultRenderPipeline = pipeline;
            if (QualitySettings.renderPipeline != pipeline) QualitySettings.renderPipeline = pipeline;
            pipeline.shadowDistance = 34; pipeline.shadowDepthBias = 1.6f; pipeline.shadowNormalBias = 1.6f;
            var settings = new SerializedObject(pipeline);
            settings.FindProperty("m_MainLightShadowmapResolution").intValue = 4096; settings.FindProperty("m_ShadowCascadeCount").intValue = 4; settings.FindProperty("m_SoftShadowsSupported").boolValue = true;
            settings.FindProperty("m_SupportsHDR").boolValue = true; settings.FindProperty("m_MSAA").intValue = 4; settings.ApplyModifiedPropertiesWithoutUndo();
            var renderer = AssetDatabase.LoadAssetAtPath<UniversalRendererData>("Assets/YunJing/Generated/Renderer.asset");
            if (renderer != null && renderer.postProcessData == null) { renderer.postProcessData = AssetDatabase.LoadAssetAtPath<PostProcessData>("Packages/com.unity.render-pipelines.universal/Runtime/Data/PostProcessData.asset"); EditorUtility.SetDirty(renderer); }
        }

        static void CopyImport()
        {
            var abs = Path.Combine(Repo, "apps", "game", Root); Directory.CreateDirectory(abs);
            foreach (var id in Pieces)
            {
                var dst = Path.Combine(abs, id); Directory.CreateDirectory(dst);
                foreach (var f in Directory.GetFiles(Path.Combine(Ww, id), "*.fbx")) File.Copy(f, Path.Combine(dst, Path.GetFileName(f)), true);
            }
            foreach (var id in FieldGaps)
            {
                var dst = Path.Combine(abs, id); Directory.CreateDirectory(dst);
                File.Copy(Path.Combine(Cr, id, id + ".fbx"), Path.Combine(dst, id + ".fbx"), true);
            }
            File.Copy(Path.Combine(Repo, "packages", "content", "creek-repair-v1.json"), Path.Combine(abs, "creek-repair-v1.json"), true);
            File.Copy(Path.Combine(Repo, "tools", "qingxi-waterworks-b", "data", "board.json"), Path.Combine(abs, "board.json"), true);
            foreach (var id in Props)
            {
                var dst = Path.Combine(abs, id); Directory.CreateDirectory(dst);
                foreach (var f in Directory.GetFiles(Path.Combine(Repo, "art", "exports", "creek-repair-b-props", id))) File.Copy(f, Path.Combine(dst, Path.GetFileName(f)), true);
            }
            AssetDatabase.Refresh();
            foreach (var id in Pieces.Concat(FieldGaps).Concat(Props))
                foreach (var f in Directory.GetFiles(Path.Combine(abs, id), "*.fbx"))
                {
                    var importer = AssetImporter.GetAtPath($"{Root}/{id}/{Path.GetFileName(f)}") as ModelImporter; if (importer == null) continue;
                    importer.bakeAxisConversion = true; importer.importAnimation = false; importer.importCameras = false; importer.importLights = false; importer.addCollider = false;
                    importer.materialImportMode = ModelImporterMaterialImportMode.ImportViaMaterialDescription; importer.SaveAndReimport();
                }
            var kit = WaterworksMaterials(); var water = FlowWater("Creek_FlowWater");
            foreach (var id in Pieces.Concat(FieldGaps))
                foreach (var f in Directory.GetFiles(Path.Combine(abs, id), "*.fbx")) Remap($"{Root}/{id}/{Path.GetFileName(f)}", n => kit.TryGetValue(n, out var m) ? m : null);
            foreach (var id in Props)
            {
                var own = PropMaterials(id, water);
                Remap($"{Root}/{id}/{id}.fbx", n => own.TryGetValue(n, out var m) ? m : null);
            }
        }

        static void Remap(string fbx, Func<string, Material> pick)
        {
            var importer = (ModelImporter)AssetImporter.GetAtPath(fbx); bool any = false;
            foreach (var old in AssetDatabase.LoadAllAssetsAtPath(fbx).OfType<Material>())
            {
                var m = pick(old.name.Split('.')[0]); if (m == null) continue;
                importer.AddRemap(new AssetImporter.SourceAssetIdentifier(typeof(Material), old.name), m); any = true;
            }
            if (any) importer.SaveAndReimport();
        }

        static Material LitMaterial(string path, Texture2D baseMap, Texture2D normal, Color color, float rough, bool vertexColor)
        {
            var m = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (m == null) { m = new Material(Shader.Find("YunJing/CreekFreshLit")); AssetDatabase.CreateAsset(m, path); }
            m.SetTexture("_BaseMap", baseMap); m.SetTexture("_BumpMap", normal); m.SetColor("_BaseColor", color); m.SetFloat("_Smoothness", 1 - rough); m.SetFloat("_UseVC", vertexColor ? 1 : 0);
            EditorUtility.SetDirty(m); return m;
        }

        static Texture2D ImportTexture(string path, bool normal)
        {
            var importer = (TextureImporter)AssetImporter.GetAtPath(path);
            var kind = normal ? TextureImporterType.NormalMap : TextureImporterType.Default;
            if (importer.textureType != kind) { importer.textureType = kind; importer.SaveAndReimport(); }
            return AssetDatabase.LoadAssetAtPath<Texture2D>(path);
        }

        // The waterworks kit's material table (tools/qingxi-waterworks-b WaterworksImportCheck), under URP.
        static Dictionary<string, Material> WaterworksMaterials()
        {
            var src = Path.Combine(Repo, "tools", "qingxi-waterworks-b", "unity", "Assets", "QingxiWaterworksB", "Textures");
            var dir = $"{Root}/ww"; Directory.CreateDirectory(dir);
            foreach (var f in Directory.GetFiles(src, "*.png")) File.Copy(f, Path.Combine(dir, Path.GetFileName(f)), true);
            AssetDatabase.Refresh();
            var specs = new (string name, string tex, Color color, float rough, string normal)[]
            {
                ("ww_stone", "ww_stone", Color.white, .84f, "ww_stone_n"), ("ww_stone_moss", "ww_stone_moss", Color.white, .92f, "ww_stone_n"),
                ("ww_wood", "ww_wood", Color.white, .8f, null), ("ww_bronze", "ww_bronze", Color.white, .72f, null), ("ww_soil", "ww_soil", Color.white, .95f, null),
                ("ww_gasket", null, new Color(.1f, .085f, .07f), .9f, null), ("ww_seal", null, new Color(.4f, .2f, .12f), .95f, null), ("ww_cloth", null, new Color(.56f, .12f, .07f), .85f, null),
                ("ww_rope", null, new Color(.2f, .14f, .075f), .95f, null), ("ww_iron", null, new Color(.3f, .3f, .29f), .55f, null), ("ww_field_soil", "ww_field_soil", Color.white, .95f, "ww_field_soil_n"),
                ("ww_grass", null, Color.white, .9f, null), ("ww_riverbed", "ww_riverbed", Color.white, .92f, "ww_riverbed_n"),
            };
            var made = specs.ToDictionary(k => k.name, k => LitMaterial($"{dir}/{k.name}.mat", k.tex == null ? null : ImportTexture($"{dir}/{k.tex}.png", false), k.normal == null ? null : ImportTexture($"{dir}/{k.normal}.png", true), k.color, k.rough, true));
            foreach (var key in new[] { "ww_stone", "ww_stone_moss" }) { made[key].SetFloat("_VCAmount", .45f); made[key].SetColor("_BaseColor", new Color(.82f, .8f, .74f)); EditorUtility.SetDirty(made[key]); }
            return made;
        }

        static Dictionary<string, Material> PropMaterials(string id, Material water)
        {
            var result = new Dictionary<string, Material>(); var dir = $"{Root}/{id}";
            foreach (var line in File.ReadAllLines(Path.Combine(Repo, "apps", "game", dir, "materials.txt")))
            {
                var f = line.Split('|'); if (f.Length < 7) continue;
                var key = f[0].Split('.')[0];
                if (key.Contains("Water") || key.Contains("water")) { result[key] = water; continue; }
                float N(int i) => float.Parse(f[i], System.Globalization.CultureInfo.InvariantCulture);
                result[key] = LitMaterial($"{dir}/M_{key}.mat", f[1] == "" ? null : ImportTexture($"{dir}/{f[1]}", false), f[2] == "" ? null : ImportTexture($"{dir}/{f[2]}", true), f[1] == "" ? new Color(N(3), N(4), N(5)) : Color.white, N(6), false);
            }
            return result;
        }

        // uGUI shaders are not referenced by any material asset, so player builds strip them.
        static void IncludeUiShaders()
        {
            var settings = new SerializedObject(AssetDatabase.LoadAllAssetsAtPath("ProjectSettings/GraphicsSettings.asset")[0]);
            var list = settings.FindProperty("m_AlwaysIncludedShaders");
            foreach (var name in new[] { "UI/Default", "Sprites/Default" })
            {
                var shader = Shader.Find(name); if (shader == null) continue;
                bool present = false; for (int i = 0; i < list.arraySize; i++) if (list.GetArrayElementAtIndex(i).objectReferenceValue == shader) present = true;
                if (!present) { list.InsertArrayElementAtIndex(list.arraySize); list.GetArrayElementAtIndex(list.arraySize - 1).objectReferenceValue = shader; }
            }
            settings.ApplyModifiedPropertiesWithoutUndo(); AssetDatabase.SaveAssets();
        }

        static GameObject Fbx(string id, string suffix = "") => AssetDatabase.LoadAssetAtPath<GameObject>($"{Root}/{id}/{id}{suffix}.fbx");

        /// Water that moves by itself (YunJing/CreekFlowWater). Still: standing field water, uv in metres on both axes.
        static Material FlowWater(string name, bool still = false)
        {
            var shader = Shader.Find("YunJing/CreekFlowWater"); if (shader == null || ShaderUtil.ShaderHasError(shader)) throw new InvalidOperationException("CreekFlowWater did not compile");
            var path = $"{Root}/{name}.mat";
            var m = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (m == null) { m = new Material(shader); AssetDatabase.CreateAsset(m, path); }
            m.shader = shader; m.SetColor("_Shallow", new Color(.18f, .255f, .21f)); m.SetColor("_Deep", new Color(.085f, .16f, .135f)); m.SetFloat("_Still", still ? 1 : 0); m.SetFloat("_Speed", still ? .03f : .45f); m.SetFloat("_AlphaMid", still ? .74f : .8f);
            EditorUtility.SetDirty(m); return m;
        }

        static Material Mat(string name, Color color, float smooth = .15f, bool transparent = false)
        {
            var path = $"{Root}/{name}.mat";
            var m = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (m == null) { m = new Material(Shader.Find("Universal Render Pipeline/Lit")); AssetDatabase.CreateAsset(m, path); }
            m.SetColor("_BaseColor", color); m.SetFloat("_Smoothness", smooth);
            if (transparent)
            {
                m.SetFloat("_Surface", 1); m.SetFloat("_Blend", 0); m.SetFloat("_ZWrite", 0); m.SetFloat("_SrcBlend", (float)BlendMode.SrcAlpha); m.SetFloat("_DstBlend", (float)BlendMode.OneMinusSrcAlpha);
                m.renderQueue = (int)RenderQueue.Transparent; m.SetOverrideTag("RenderType", "Transparent"); m.EnableKeyword("_SURFACE_TYPE_TRANSPARENT");
            }
            EditorUtility.SetDirty(m); return m;
        }

        static GameObject Box(Transform parent, string name, Vector3 at, Vector3 size, Material mat)
        {
            var b = GameObject.CreatePrimitive(PrimitiveType.Cube); b.name = name; b.transform.SetParent(parent); b.transform.position = at; b.transform.localScale = size;
            UnityEngine.Object.DestroyImmediate(b.GetComponent<Collider>()); b.GetComponent<Renderer>().sharedMaterial = mat; return b;
        }

        /// A flat slab with a rectangular hole, as four boxes.
        static void Sheet(Transform parent, string name, float y, float h, float x0, float x1, float z0, float z1, float hx0, float hx1, float hz0, float hz1, Material mat)
        {
            void Part(float a0, float a1, float b0, float b1) => Box(parent, name, new Vector3((a0 + a1) / 2, y, (b0 + b1) / 2), new Vector3(a1 - a0, h, b1 - b0), mat);
            Part(x0, hx0, z0, z1); Part(hx1, x1, z0, z1); Part(hx0, hx1, z0, hz0); Part(hx0, hx1, hz1, z1);
        }

        static GameObject Put(Transform parent, GameObject prefab, Vector3 at, float yaw = 0)
        {
            var go = (GameObject)PrefabUtility.InstantiatePrefab(prefab); PrefabUtility.UnpackPrefabInstance(go, PrefabUnpackMode.Completely, InteractionMode.AutomatedAction);
            go.transform.SetParent(parent); go.transform.SetPositionAndRotation(at, Quaternion.Euler(0, yaw, 0) * prefab.transform.localRotation);   // a one-mesh FBX keeps its axis conversion on the root
            if (prefab.name.StartsWith("B") || prefab.name.StartsWith("F")) CreekRepairDirector.KeepLod0(go);   // the waterworks FBX keeps its LODs as siblings; they would all draw
            return go;
        }

        static GameObject PutOwn(Transform parent, string id, Vector3 at, float yaw = 0)
        {
            var go = Put(parent, AssetDatabase.LoadAssetAtPath<GameObject>($"{Own}/{id}/{id}_v001.fbx"), at, yaw);
            var mat = AssetDatabase.LoadAssetAtPath<Material>($"{Own}/{id}.mat");
            foreach (var r in go.GetComponentsInChildren<Renderer>(true))
            {
                if (r.name == id + "_Collision") { r.enabled = false; continue; }
                r.sharedMaterials = Enumerable.Repeat(mat, r.sharedMaterials.Length).ToArray();
            }
            float[] cut = { .25f, .08f, .015f };
            if (go.GetComponent<LODGroup>() == null) go.AddComponent<LODGroup>().SetLODs(Enumerable.Range(0, 3).Select(i => new LOD(cut[i], go.GetComponentsInChildren<Renderer>(true).Where(r => r.name.EndsWith("_LOD" + i)).ToArray())).ToArray());
            return go;
        }

        static Material GroundMaterial()
        {
            var shader = Shader.Find("YunJing/CreekGround"); if (shader == null || ShaderUtil.ShaderHasError(shader)) throw new InvalidOperationException("CreekGround did not compile");
            var path = $"{Root}/Ground.mat"; var m = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (m == null) { m = new Material(shader); AssetDatabase.CreateAsset(m, path); }
            m.shader = shader; EditorUtility.SetDirty(m); return m;
        }

        /// Morning light with haze, so far things soften and the colours sit together.
        static void Atmosphere(Transform world)
        {
            var skyPath = $"{Root}/Sky.mat"; var sky = AssetDatabase.LoadAssetAtPath<Material>(skyPath);
            if (sky == null) { sky = new Material(Shader.Find("Skybox/Procedural")); AssetDatabase.CreateAsset(sky, skyPath); }
            sky.SetFloat("_SunSize", .03f); sky.SetFloat("_AtmosphereThickness", .85f); sky.SetColor("_SkyTint", new Color(.52f, .6f, .68f)); sky.SetColor("_GroundColor", new Color(.55f, .58f, .55f)); sky.SetFloat("_Exposure", 1.05f);
            EditorUtility.SetDirty(sky); RenderSettings.skybox = sky;
            RenderSettings.fog = true; RenderSettings.fogMode = FogMode.Linear; RenderSettings.fogColor = new Color(.68f, .75f, .77f); RenderSettings.fogStartDistance = 28; RenderSettings.fogEndDistance = 240;

            var path = $"{Root}/PostVolume.asset"; var profile = AssetDatabase.LoadAssetAtPath<VolumeProfile>(path);
            if (profile == null) { profile = ScriptableObject.CreateInstance<VolumeProfile>(); AssetDatabase.CreateAsset(profile, path); }
            if (!profile.TryGet<Tonemapping>(out var tone)) tone = profile.Add<Tonemapping>(true);
            tone.mode.Override(TonemappingMode.ACES);
            if (!profile.TryGet<ColorAdjustments>(out var color)) color = profile.Add<ColorAdjustments>(true);
            color.postExposure.Override(.12f); color.contrast.Override(6); color.saturation.Override(-4); color.colorFilter.Override(new Color(1, .985f, .95f));
            if (!profile.TryGet<Bloom>(out var bloom)) bloom = profile.Add<Bloom>(true);
            bloom.intensity.Override(.22f); bloom.threshold.Override(1.15f); bloom.scatter.Override(.55f);
            if (!profile.TryGet<Vignette>(out var vignette)) vignette = profile.Add<Vignette>(true);
            vignette.intensity.Override(.16f); vignette.smoothness.Override(.5f);
            EditorUtility.SetDirty(profile);
            var volume = new GameObject("Post volume").AddComponent<Volume>(); volume.isGlobal = true; volume.sharedProfile = profile; volume.transform.SetParent(world);
        }

        /// Placeholder surroundings: grass over the bare ground and low hills on the horizon. All of it one mesh per kind, no collision.
        static void Backdrop(Transform world, float gx0, float gx1, float gz0, float gz1)
        {
            var rand = new System.Random(2601);
            var v = new List<Vector3>(); var n = new List<Vector3>(); var c = new List<Color32>(); var t = new List<int>();
            bool Clear(float x, float z)
            {
                bool site = x > -4.2f && x < 4.2f && z > -1.2f && z < 6.7f, fields = x > -9.7f && x < 9.7f && z > 6 && z < 13.7f, ditch = x > -.4f && x < 8.6f && z > -.6f && z < 6.5f;
                return !(site || fields || ditch || (x > gx0 - .3f && x < gx1 + .3f && z > gz0 - .3f && z < gz1 + .3f) || (x > 5.4f && x < 11 && z > -.6f && z < 3));
            }
            float R(float a, float b) => a + (float)rand.NextDouble() * (b - a);
            for (int patch = 0; patch < 230; patch++)
            {
                float px = R(-24, 24), pz = R(-13, 27); int inPatch = rand.Next(3, 9);
                for (int k = 0; k < inPatch; k++)
                {
                    float x = px + R(-.8f, .8f), z = pz + R(-.8f, .8f); if (!Clear(x, z)) continue;
                    float size = R(.65f, 1.25f); byte tint = (byte)rand.Next(0, 40);
                    for (int b = 0; b < 6; b++)
                    {
                        float a = R(0, Mathf.PI * 2), L = R(.12f, .26f) * size, w = R(.009f, .016f) * size, over = R(.2f, .6f), r = R(0, .04f);
                        var lean = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a)); var side = new Vector3(-lean.z, 0, lean.x); var at = new Vector3(x, -.005f, z) + lean * r;
                        var low = at - side * w / 2; var low2 = at + side * w / 2; var mid = at + lean * L * over * .25f + Vector3.up * L * .62f; var tip = at + lean * L * over + Vector3.up * L * (1 - .3f * over);
                        int first = v.Count;
                        v.AddRange(new[] { low, low2, mid - side * w * .4f, mid + side * w * .4f, tip });
                        for (int q = 0; q < 5; q++) { n.Add((Vector3.up * 2 + lean).normalized); float k2 = q < 2 ? 0 : q < 4 ? .55f : 1; c.Add(new Color32((byte)(62 + 78 * k2 + tint), (byte)(88 + 80 * k2 + tint / 2), (byte)(36 + 34 * k2), 255)); }
                        t.AddRange(new[] { first, first + 1, first + 3, first, first + 3, first + 2, first + 2, first + 3, first + 4, first + 3, first + 1, first, first + 2, first + 3, first, first + 4, first + 3, first + 2 });
                    }
                }
            }
            MeshObject(world, "Placeholder_Grass", "GroundGrass", v, n, c, t, false);

            v = new List<Vector3>(); n = new List<Vector3>(); c = new List<Color32>(); t = new List<int>();
            const int Around = 120;
            for (int layer = 0; layer < 2; layer++)
            {
                float radius = layer == 0 ? 95 : 145, tall = layer == 0 ? 13 : 30; int first = v.Count; var tone = layer == 0 ? new Color32(120, 143, 104, 255) : new Color32(146, 165, 158, 255);
                float phase = layer * 3.1f;
                for (int i = 0; i <= Around; i++)
                {
                    float a = i * Mathf.PI * 2 / Around, wave = Mathf.PerlinNoise(Mathf.Cos(a) * 1.7f + 4 + phase, Mathf.Sin(a) * 1.7f + 4) * .75f + Mathf.PerlinNoise(Mathf.Cos(a) * 5 + 9 + phase, Mathf.Sin(a) * 5 + 9) * .25f;
                    var dir = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
                    v.Add(dir * radius * 1.25f + new Vector3(0, -1, 0)); v.Add(dir * radius + Vector3.up * tall * wave);
                    n.Add(Vector3.up); n.Add((Vector3.up - dir * .5f).normalized); c.Add(tone); c.Add(tone);
                    if (i < Around) { int s = first + i * 2; t.AddRange(new[] { s, s + 1, s + 2, s + 2, s + 1, s + 3, s, s + 2, s + 1, s + 2, s + 3, s + 1 }); }
                }
            }
            MeshObject(world, "Placeholder_Hills", "GroundHills", v, n, c, t, false);
        }

        static void MeshObject(Transform parent, string name, string asset, List<Vector3> v, List<Vector3> n, List<Color32> c, List<int> t, bool shadows)
        {
            var path = $"{Root}/{asset}.asset"; AssetDatabase.DeleteAsset(path);
            var mesh = new Mesh { name = asset, indexFormat = UnityEngine.Rendering.IndexFormat.UInt32 }; mesh.SetVertices(v); mesh.SetNormals(n); mesh.SetColors(c); mesh.SetTriangles(t, 0); mesh.RecalculateBounds(); mesh.RecalculateTangents();
            AssetDatabase.CreateAsset(mesh, path);
            var go = new GameObject(name); go.transform.SetParent(parent); go.AddComponent<MeshFilter>().sharedMesh = mesh;
            var r = go.AddComponent<MeshRenderer>(); r.sharedMaterial = LitMaterial($"{Root}/{asset}.mat", null, null, Color.white, .9f, true); r.shadowCastingMode = shadows ? ShadowCastingMode.On : ShadowCastingMode.Off;
        }

        public static void Generate()
        {
            UsePipeline(); CreekRepairModelCheck.ImportForScene(); CopyImport();
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var world = new GameObject("CreekRepair").transform;
            RenderSettings.ambientMode = AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = new Color(.56f, .65f, .74f); RenderSettings.ambientEquatorColor = new Color(.45f, .45f, .39f); RenderSettings.ambientGroundColor = new Color(.2f, .17f, .13f);
            Atmosphere(world);
            var sun = new GameObject("Sun").AddComponent<Light>(); sun.type = LightType.Directional; sun.intensity = 1.75f; sun.color = new Color(1, .92f, .79f); sun.shadows = LightShadows.Soft; sun.transform.SetParent(world); sun.transform.rotation = Quaternion.Euler(36, -48, 0);

            // the ground and bank leave a gully under L3/L4 for the raised flume (1.5 m, work pack CR08)
            float gx0 = -3.65f, gx1 = -1.35f, gz0 = 2.62f, gz1 = 4.38f;
            var grass = GroundMaterial(); var bank = grass; var earth = Mat("Graybox_GullyEarth", new Color(.3f, .24f, .17f), .05f);
            Sheet(world, "Placeholder_Ground", -.05f, .1f, -160, 160, -130, 190, gx0, gx1, gz0, gz1, grass);
            Sheet(world, "Placeholder_Bank", .002f, .006f, -3.7f, 3.7f, -.9f, 6.7f, gx0, gx1, gz0, gz1, bank);
            Box(world, "Placeholder_GullyFloor", new Vector3((gx0 + gx1) / 2, -1.55f, (gz0 + gz1) / 2), new Vector3(gx1 - gx0, .1f, gz1 - gz0), earth);
            foreach (var x in new[] { gx0 - .05f, gx1 + .05f }) Box(world, "Placeholder_GullyWall", new Vector3(x, -.75f, (gz0 + gz1) / 2), new Vector3(.1f, 1.5f, gz1 - gz0 + .2f), earth);
            foreach (var z in new[] { gz0 - .05f, gz1 + .05f }) Box(world, "Placeholder_GullyWall", new Vector3((gx0 + gx1) / 2, -.75f, z), new Vector3(gx1 - gx0, 1.5f, .1f), earth);
            var gullyCover = Box(world, "Placeholder_GullyCover", new Vector3((gx0 + gx1) / 2, .002f, (gz0 + gz1) / 2), new Vector3(gx1 - gx0 + .02f, .006f, gz1 - gz0 + .02f), bank);

            Backdrop(world, gx0, gx1, gz0, gz1);

            Put(world, Fbx("B01"), Vector3.zero);
            var gate = PutOwn(world, "CR09_B_TenonGate", new Vector3(0, 0, .5f));
            // B06's origin is its mounting flange and its shaft runs through the gate's post to the rack on the board
            var wheelAt = new Vector3(.24f, .42f, .407f);   // pinion on the gate's rack (CR09_B x .09, face y -.058)
            var wheelHolder = new GameObject("WheelSpin").transform; wheelHolder.SetParent(world); wheelHolder.position = wheelAt;
            var wheelModel = Put(wheelHolder, Fbx("B06"), wheelAt);
            var shelter = PutOwn(world, "CR05_WorkShelter", new Vector3(7.2f, 0, 1.2f));   // clear of the ditch's first bend
            Put(world, Fbx("B11"), new Vector3(2.2f, 0, -.7f), 70);
            var planSign = Put(world, Fbx("B12"), new Vector3(1.9f, 0, 5.45f), 180);

            // the work site: reused pack props as they are, and this pack's piles and tools
            var site = new GameObject("WorkSite").transform; site.SetParent(world);
            Prop(site, "C03", new Vector3(3.3f, 0, .55f), 30); Prop(site, "C04", new Vector3(3.1f, 0, -.05f), 80); Prop(site, "C06", new Vector3(-1.5f, 0, -1.1f), 15); Prop(site, "C07", new Vector3(2.9f, 0, -1.45f), -20);
            Prop(site, "A04_SiltBar", new Vector3(9.9f, 0, .9f), 90);
            var stonePile = UnityEngine.Object.Instantiate(Extract("CR03_StonePile", n => n.StartsWith("Stage_High"), "Site_StonePile")); stonePile.transform.SetParent(site); stonePile.transform.SetPositionAndRotation(new Vector3(-3.6f, 0, -.9f), Quaternion.Euler(0, 20, 0));
            var timber = UnityEngine.Object.Instantiate(Extract("CR03_TimberRack", n => n.StartsWith("Stage_Mid"), "Site_TimberRack")); timber.transform.SetParent(site); timber.transform.SetPositionAndRotation(new Vector3(-6.2f, 0, -.5f), Quaternion.Euler(0, 10, 0));
            var tools = PutOwn(site, "CR04_Tools", new Vector3(.2f, 0, -1.7f)); tools.name = "CR04_Tools";
            var t080 = PutOwn(site, "CR08_Trestle_080", new Vector3(-4.3f, 0, 3.4f), 90); t080.name = "CR08_Trestle_080";
            var t150 = PutOwn(site, "CR08_Trestle_150", new Vector3(-5.1f, 0, 3.4f), 90); t150.name = "CR08_Trestle_150";
            // two more under the flume's bearers (L3 runs z 2.5..4.5 at x -2.5), seats at ground level
            var trestles = new GameObject("CR08_Trestles_InUse").transform; trestles.SetParent(world);
            foreach (var z in new[] { 2.78f, 4.22f })
            {
                var t = PutOwn(trestles, "CR08_Trestle_150", Vector3.zero);
                var seat = t.GetComponentsInChildren<Transform>(true).First(c => c.name.StartsWith("Socket_TroughSeat")).position;
                t.transform.position = new Vector3(-2.5f, 0, z) - seat;
            }
            var party = PutOwn(world, "CR07_Celebration", new Vector3(0, 0, 14.3f)); party.name = "CR07_Celebration";
            foreach (var t in party.GetComponentsInChildren<Transform>(true)) if (t.name.Contains("_Lit")) t.gameObject.SetActive(false);
            party.SetActive(false);

            var fieldXs = new[] { 0f, -6f, 6f };   // side by side, so neighbours share a bank; each is fed by its own gate from the canal to the south
            const float FieldZ = 9, GateZ = 8.25f;
            var soil = new List<Renderer>(); var fieldWater = new List<Transform>(); var fieldGates = new List<CreekRepairDirector.FieldGate>();
            for (int i = 0; i < 3; i++)
            {
                // F01_Field has its origin at the bottom centre; F01_water keeps F01's, so the field goes back by the offset in its validation.json
                var f = Put(world, Fbx("F01_Field"), new Vector3(fieldXs[i], -.191f, FieldZ + 2)); f.name = "Field_" + i;
                foreach (var r in f.GetComponentsInChildren<MeshRenderer>(true).Where(r => r.name.EndsWith("_Collision"))) { r.enabled = false; r.gameObject.AddComponent<MeshCollider>().sharedMesh = r.GetComponent<MeshFilter>().sharedMesh; }
                soil.AddRange(f.GetComponentsInChildren<Renderer>().Where(r => !r.name.EndsWith("_Collision")).Take(1));
                // the fields' outer edges only just meet: earth in the crack between them, so grass does not show through
                if (i > 0) Box(world, "FieldSeam_" + i, new Vector3(fieldXs[i] / 2, .04f, FieldZ + 2), new Vector3(.6f, .1f, f.GetComponentInChildren<Renderer>().bounds.size.z), Mat("Field_Seam", new Color(.06f, .026f, .012f)));
                var w = Put(world, Fbx("F01", "_water"), new Vector3(fieldXs[i], 0, FieldZ)); w.name = "FieldWater_" + i; fieldWater.Add(w.transform);
                // F01 states: field_low only below crest 0.125, outlet only with the weir lowered; here the weir stays up
                foreach (var t in w.GetComponentsInChildren<Transform>(true).Where(t => t.name.Contains("field_low") || t.name.Contains("outlet")).ToArray()) UnityEngine.Object.DestroyImmediate(t.gameObject);
                foreach (var r in w.GetComponentsInChildren<Renderer>()) r.sharedMaterial = FlowWater("Field_StillWater", true);
                var fg = PutOwn(world, i == 0 ? "CR09_B_TenonGate" : "CR09_A_RopeGate", new Vector3(fieldXs[i], 0, GateZ)); fg.name = "FieldGate_" + i;
                fieldGates.Add(new CreekRepairDirector.FieldGate { at = fg.transform.position, parts = fg.GetComponentsInChildren<Transform>(true).Where(t => t.name.Contains("_Gate_LOD")).ToArray() });
            }

            var rig = new GameObject("Director"); rig.transform.SetParent(world);
            var cam = new GameObject("Main Camera").AddComponent<Camera>(); cam.tag = "MainCamera"; cam.fieldOfView = 42; cam.nearClipPlane = .05f; cam.farClipPlane = 400; cam.clearFlags = CameraClearFlags.Skybox; cam.allowHDR = true; cam.allowMSAA = true; cam.transform.SetParent(world);
            cam.gameObject.AddComponent<UniversalAdditionalCameraData>().renderPostProcessing = true;
            var d = rig.AddComponent<CreekRepairDirector>();
            d.contentJson = AssetDatabase.LoadAssetAtPath<TextAsset>($"{Root}/creek-repair-v1.json"); d.boardJson = AssetDatabase.LoadAssetAtPath<TextAsset>($"{Root}/board.json");
            d.pieces = Pieces.Where(id => id.StartsWith("B0") && id != "B01" && id != "B06").Select(id => new CreekRepairDirector.PieceModel { id = id, model = Fbx(id), water = Fbx(id, "_water") }).ToArray();
            // the crack marks and the weed lie on the mud's surface, so the director reads its vertices
            var mudImporter = (ModelImporter)AssetImporter.GetAtPath($"{Own}/CR03_MudHeap/CR03_MudHeap_v001.fbx");
            if (!mudImporter.isReadable) { mudImporter.isReadable = true; mudImporter.SaveAndReimport(); }
            var toolImporter = (ModelImporter)AssetImporter.GetAtPath($"{Own}/CR04_Tools/CR04_Tools_v001.fbx");   // the spade's shaft is drawn out at run time
            if (!toolImporter.isReadable) { toolImporter.isReadable = true; toolImporter.SaveAndReimport(); }
            foreach (var id in Pieces.Where(id => id.StartsWith("B0") && id != "B01" && id != "B06")) { var pieceImporter = (ModelImporter)AssetImporter.GetAtPath($"{Root}/{id}/{id}.fbx"); if (!pieceImporter.isReadable) { pieceImporter.isReadable = true; pieceImporter.SaveAndReimport(); } }   // what the spade is measured against
            // wet silt, dark and with a little shine; vertex colour marks where a spade has cut it fresh
            var mudMat = AssetDatabase.LoadAssetAtPath<Material>($"{Own}/CR03_MudHeap.mat"); var mudMap = mudMat.GetTexture("_BaseMap"); var mudBump = mudMat.GetTexture("_BumpMap");
            mudMat.shader = Shader.Find("YunJing/CreekFreshLit"); mudMat.SetTexture("_BaseMap", mudMap); mudMat.SetTexture("_BumpMap", mudBump); mudMat.SetColor("_BaseColor", new Color(.5f, .43f, .37f)); mudMat.SetFloat("_Smoothness", .34f); mudMat.SetFloat("_UseVC", 1); mudMat.SetFloat("_VCAmount", 1); EditorUtility.SetDirty(mudMat);
            d.pileStages = new[] { "Stage_High", "Stage_Mid", "Stage_Low" }.Select(st => Extract("CR03_MudHeap", n => n.StartsWith(st), "Pile_" + st)).ToArray();
            // the set lies the spade on the ground; in use it is stood up with the blade tip at the prefab origin
            d.weedClump = Extract("CR14_WeedClump", n => true, "Weed_Clump");
            d.spadeModel = Extract("CR04_Tools", n => n.StartsWith("Spade"), "Tool_Spade", null, true, t =>
            {
                t.rotation = Quaternion.Euler(-90, 0, 0) * Quaternion.AngleAxis(9.17f, Vector3.up) * t.rotation;
                var b = t.GetComponent<Renderer>().bounds; t.position -= new Vector3(b.center.x, b.min.y, b.center.z);
            });
            var creekWater = FlowWater("Creek_FlowWater");
            d.ditchBend = Extract("CR06_Bend", n => true, "Ditch_Bend"); d.ditchBendWater = OwnWater("CR06_Bend", "Ditch_BendWater", creekWater);
            d.ditchShort = Extract("CR06_Short", n => true, "Ditch_Short"); d.ditchShortWater = OwnWater("CR06_Short", "Ditch_ShortWater", creekWater);
            d.ditchStraight = Extract("CR06_Straight", n => true, "Ditch_Straight"); d.ditchStraightWater = OwnWater("CR06_Straight", "Ditch_StraightWater", creekWater);
            d.ditchCross = Extract("CR15_DitchCross", n => true, "Ditch_Cross"); d.ditchCrossWater = OwnWater("CR15_DitchCross", "Ditch_CrossWater", creekWater);
            d.flumeStraight = Extract("CR08_Straight", n => true, "Flume_Body"); d.flumeWater = OwnWater("CR08_Straight", "Flume_Water", creekWater);
            d.oldStones = Extract("CR03_StonePile", n => n.StartsWith("Stage_Low"), "Old_Stones", null, true);
            d.celebration = party; d.aqueductTrestles = trestles.gameObject; d.gullyCover = gullyCover; d.spareTrestle = t150;
            var freshShader = Shader.Find("YunJing/CreekFreshLit"); if (freshShader == null || ShaderUtil.ShaderHasError(freshShader)) throw new InvalidOperationException("CreekFreshLit did not compile");
            var freshPath = $"{Root}/Creek_Fresh.mat"; d.freshMat = AssetDatabase.LoadAssetAtPath<Material>(freshPath);
            if (d.freshMat == null) { d.freshMat = new Material(freshShader); AssetDatabase.CreateAsset(d.freshMat, freshPath); }
            d.freshMat.SetFloat("_UseVC", 1);
            d.wheelParts = wheelModel.GetComponentsInChildren<Transform>(true).Where(t => t.name.Contains("_wheel")).ToArray();
            d.wheel = wheelHolder; d.gateParts = gate.GetComponentsInChildren<Transform>(true).Where(t => t.name.Contains("_Gate_LOD")).ToArray();
            d.fieldWater = fieldWater.ToArray(); d.fieldSoil = soil.ToArray(); d.view = cam; d.fieldGates = fieldGates.ToArray(); d.planSign = planSign.transform;
            d.waterMat = creekWater;
            var linePath = $"{Root}/Creek_Line.mat";
            d.lineMat = AssetDatabase.LoadAssetAtPath<Material>(linePath);
            if (d.lineMat == null) { d.lineMat = new Material(Shader.Find("Universal Render Pipeline/Unlit")); AssetDatabase.CreateAsset(d.lineMat, linePath); }
            d.markMat = Mat("Creek_Mark", new Color(.42f, .86f, .72f, .25f), .1f, true);
            d.wrongMat = Mat("Creek_Wrong", new Color(.8f, .25f, .18f, .55f), .1f, true);
            d.soilMat = Mat("Placeholder_Silt", new Color(.2f, .15f, .1f), .35f);
            d.stoneMat = Mat("Placeholder_Stone", new Color(.42f, .41f, .36f), .1f);
            var pt = rig.AddComponent<CreekRepairPlaytest>(); pt.director = d;
            // what the spade is measured against: not drawn, and on a layer nothing else casts at
            foreach (var f in world.GetComponentsInChildren<MeshFilter>(true))
            {
                if (f.sharedMesh == null || f.name.Contains("LOD1") || f.name.Contains("LOD2") || f.name.StartsWith("Placeholder") || f.name.EndsWith("_Collision") || f.name.ToLowerInvariant().Contains("water")) continue;
                var probe = new GameObject("SpadeProbe") { layer = CreekRepairDirector.ProbeLayer }; probe.transform.SetParent(f.transform, false); probe.AddComponent<MeshCollider>().sharedMesh = f.sharedMesh;
            }
            AssetDatabase.SaveAssets();
            EditorSceneManager.SaveScene(UnityEngine.SceneManagement.SceneManager.GetActiveScene(), Scene);
            Debug.Log("CREEK_SCENE_SAVED wheel children: " + string.Join(",", wheelModel.GetComponentsInChildren<Transform>().Select(t => t.name)) + " | gate parts " + d.gateParts.Length + " | F01 renderers " + soil.Count);
        }

        [Serializable] class Snap { public double silt, wheel, flow, fill; public int work, reached, events, moves; public bool done, together; public string layout, stones, slumped, levels, lastBy; }
        [Serializable] class FixStep { public string op, a, b, code; public double n, m, x, z, dx, dz; public bool hasAt, hasDir, beat; public int gapCm; public Snap after; }
        [Serializable] class FixCase { public string method; public int partySize; public FixStep[] steps; }
        [Serializable] class Fixture { public FixCase[] cases; }

        /// Replays tests/fixtures/creek-repair-trace.json (written by the TS rules) through the C# port.
        public static void VerifySim()
        {
            var content = JsonUtility.FromJson<CreekContent>(File.ReadAllText(Path.Combine(Repo, "packages", "content", "creek-repair-v1.json")));
            var fixture = JsonUtility.FromJson<Fixture>(File.ReadAllText(Path.Combine(Repo, "tests", "fixtures", "creek-repair-trace.json")));
            if (fixture.cases == null || fixture.cases.Length != 12) throw new InvalidDataException("fixture should have 12 cases");
            int steps = 0;
            foreach (var c in fixture.cases)
            {
                var sim = new CreekRepairSim(content, c.method, c.partySize);
                foreach (var s in c.steps)
                {
                    CreekStep r = default;
                    switch (s.op)
                    {
                        case "wheel": r = sim.TurnWheel(s.n); break;
                        case "scoop": r = sim.Scoop(s.a, s.n, s.m); break;
                        case "stroke": r = sim.Scoop(s.a, s.n, s.m, s.hasAt ? new[] { s.x, s.z } : null, s.hasDir ? new[] { s.dx, s.dz } : null, s.beat); break;
                        case "scrape": r = sim.Scrape(s.a, s.n, s.hasAt ? new[] { s.x, s.z } : null, s.beat); break;
                        case "beat": if (sim.IsOnBeat(s.n) != s.beat) throw new InvalidDataException($"beat {s.n}: {sim.IsOnBeat(s.n)} != {s.beat}"); r.code = ""; break;
                        case "place": r = sim.Place(s.a, s.b); break;
                        case "patch": r = sim.Patch(s.a, s.b); break;
                        case "aqueduct": r = sim.BuildAqueduct(); break;
                        case "flow": sim.AdvanceFlow(s.n); r.code = ""; break;
                        case "gate": r = sim.SetGate(s.a, s.n, s.b); break;
                        case "cycle": r = sim.CycleGate(s.a, s.b); break;
                    }
                    var e = s.after; string where = $"{c.method}/{c.partySize} step {steps} {s.op} {s.a} {s.b}";
                    if (r.code != s.code || r.gapCm != s.gapCm) throw new InvalidDataException($"{where}: {r.code}/{r.gapCm} != {s.code}/{s.gapCm}");
                    if (string.Join(",", sim.s.slumped) != e.slumped) throw new InvalidDataException($"{where}: slumped {string.Join(",", sim.s.slumped)} != {e.slumped}");
                    string layout = string.Join(",", sim.Layout().Select(k => k.Key + "=" + k.Value)), stones = string.Join(",", sim.M.piles.Select(p => sim.StonesShowing(p.id)));
                    if (Math.Abs(sim.SiltLeft - e.silt) > 1e-6 || sim.WorkLeft != e.work || Math.Abs(sim.s.wheelDegrees - e.wheel) > 1e-6 || Math.Abs(sim.s.flowM - e.flow) > 1e-3 || sim.s.reached.Count != e.reached || sim.s.done != e.done || sim.s.events.Count != e.events || layout != e.layout || stones != e.stones)
                        throw new InvalidDataException($"{where}: silt {sim.SiltLeft}/{e.silt} work {sim.WorkLeft}/{e.work} flow {sim.s.flowM}/{e.flow} reached {sim.s.reached.Count}/{e.reached} events {sim.s.events.Count}/{e.events} layout {layout}/{e.layout} stones {stones}/{e.stones}");
                    string levels = string.Join(",", content.distribution.gates.Select(g => sim.Gate(g.id).level.ToString(System.Globalization.CultureInfo.InvariantCulture))); double fill = content.distribution.gates.Sum(g => sim.Gate(g.id).fill); string lastBy = sim.s.gateLog.Count > 0 ? sim.s.gateLog[sim.s.gateLog.Count - 1].by : "";
                    if (levels != e.levels || Math.Abs(fill - e.fill) > 1e-3 || sim.s.gateLog.Count != e.moves || lastBy != e.lastBy || sim.s.together != e.together)
                        throw new InvalidDataException($"{where}: gates {levels}/{e.levels} fill {fill}/{e.fill} moves {sim.s.gateLog.Count}/{e.moves} by {lastBy}/{e.lastBy} together {sim.s.together}/{e.together}");
                    steps++;
                }
            }
            Debug.Log($"CREEK_SIM_PARITY_PASS {fixture.cases.Length} cases, {steps} steps");
        }

        public static void Build()
        {
            VerifySim(); Generate(); IncludeUiShaders();
            var dir = Path.Combine(Repo, "artifacts", "creek-repair-build"); Directory.CreateDirectory(dir);
            var path = Path.Combine(dir, "CreekRepair.exe");
            var report = BuildPipeline.BuildPlayer(new BuildPlayerOptions { scenes = new[] { Scene }, target = BuildTarget.StandaloneWindows64, locationPathName = path, options = BuildOptions.Development });
            if (report.summary.result != BuildResult.Succeeded) throw new Exception("Build failed: " + report.summary.result);
            Debug.Log("CREEK_BUILD_PASS " + path);
        }
    }
}
