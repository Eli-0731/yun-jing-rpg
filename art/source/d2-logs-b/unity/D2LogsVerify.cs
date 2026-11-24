using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

namespace YunJing.Editor
{
    // Unity check of B's D2 fallen logs and stumps (art/exports/d2-logs-b, joshsu54: DR06 fallen trunk, DR05 hollow log, DR07 giant stumps), the same way as D2RootsVerify (d2-roots-b). It does
    // not change apps/game: run_unity_check.sh copies this file in for one batch run and removes it together with the temporary model copies.
    // Imports the delivered FBX and textures, builds one URP Lit for the body (Albedo, Normal, MaskURP, shared bark detail on UV0) and one
    // two-sided for the plants, compares with model_info.json (size within 2 cm, triangles per LOD, objects, materials, 2048 textures,
    // minTier, detailObjects, origin at the bottom centre), switches Detail_* off the way the standard tier will, gives the collision shell a
    // MeshCollider and checks that a 1.75 m walker cannot cross the trunk or the root plate, then renders the review shots listed in
    // model_info.json (review_cams_build_xyz: Blender build coordinates, root plate at x = 0, snapped end at x = L).
    //   Unity -batchmode -quit -projectPath apps/game -executeMethod YunJing.Editor.D2LogsVerify.Run -logFile <log>
    // Output: art/previews/d2-logs-b/<asset>/unity/*.png and report.txt; the run fails when a check fails.
    public static class D2LogsVerify
    {
        const string BudgetModels = "Assets/YunJing/Models/D2LogsB", RawModels = "Assets/D2LogsBRawCheck";
        static string Models = BudgetModels;
        static bool Raw => Models == RawModels;
        static string Version(string id) => "v001";
        static readonly string[] AllIds = { "DR06_FallenTrunk_B", "DR06_FallenTrunk_A", "DR05_HollowLog", "DR07_GiantStump_A", "DR07_GiantStump_B", "DR08_RottenLog_A", "DR08_RottenLog_B", "DR08_RottenLog_C" };
        static string[] Ids => string.IsNullOrEmpty(Environment.GetEnvironmentVariable("D2_IDS")) ? AllIds
            : Environment.GetEnvironmentVariable("D2_IDS").Split(',').Select(s => s.Trim()).Where(AllIds.Contains).ToArray();
        static string Repo => Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", ".."));
        static string Exports => Path.Combine(Repo, "art/exports/d2-logs-b");
        static string Out(string id) => Path.Combine(Repo, "art/previews/d2-logs-b", id, "unity");
        static readonly List<string> Report = new List<string>();
        static int failures;

        [Serializable] class Lod { public int triangles, objects, materials; }
        [Serializable] class Lods { public Lod LOD0, LOD1, LOD2; public Lod[] All => new[] { LOD0, LOD1, LOD2 }; }
        [Serializable] class UnityInfo { public float detail_tiling_on_uv0; }
        [Serializable] class Cam { public string name; public float[] from; public float[] at; public float lens_mm; }
        [Serializable] class Tunnel { public float axis_y, floor_z, x0, x1; }
        [Serializable] class Stump { public float axis_x, axis_y, rim_low, pool_z, radius; }
        [Serializable] class Info
        {
            public float[] dimensions_m; public string minTier; public string[] detailObjects; public Lods budget_per_lod; public UnityInfo unity;
            public float[] build_origin_m; public float length_build_m, plate_x_build_m; public Cam[] review_cams_build_xyz; public Tunnel tunnel_build;
            public Stump stump_build; public float[] ruler_build_xy; public WaterInfo water;
        }
        // DR07: the standing water is its own FBX (<id>_water_v001.fbx, like CR06 / F01 in the creek repair pack): wet = body + water, dry = body only
        [Serializable] class WaterInfo { public string file; public string[] objects; public float z_m; public float[] centre_xy_m; }
        static bool HasWater(Info info) => info.water != null && !string.IsNullOrEmpty(info.water.file);

        public static void Run()
        {
            Report.Clear(); failures = 0;
            Import();
            QingxiUrpUpgrade.EnsurePipeline();
            Report.Add($"Unity {Application.unityVersion}, pipeline {GraphicsSettings.currentRenderPipeline?.name ?? "built-in"}");
            var own = new Dictionary<string, List<string>>();
            foreach (var id in Ids)
            {
                Directory.CreateDirectory(Out(id));
                EditorSceneManager.NewScene(NewSceneSetup.EmptyScene);
                var info = InfoOf(id);
                int start = Report.Count;
                Inspect(id, info);
                Shots(id, info);
                own[id] = Report.Skip(start).ToList();
                File.WriteAllLines(Path.Combine(Out(id), "report.txt"), new[] { Report[0] }.Concat(own[id]));
            }
            Models = RawModels; Mats.Clear();
            Import();
            foreach (var id in Ids)
            {
                var info = InfoOf(id);
                var before = Report.Count; int f0 = failures;
                Shots(id, info);
                Report.RemoveRange(before, Report.Count - before); failures = f0;
                var note = $"INFO {id}: *-rawimport.png show the delivered files without the project's import budget (2048 textures, no crunch, no mesh compression)";
                Report.Add(note); own[id].Add(note);
                File.WriteAllLines(Path.Combine(Out(id), "report.txt"), new[] { Report[0] }.Concat(own[id]));
            }
            Models = BudgetModels; Mats.Clear();
            foreach (var line in Report) Debug.Log("DR " + line);
            if (failures > 0) throw new Exception($"DR_VERIFY {failures} check(s) failed, see report.txt");
            Debug.Log("DR_VERIFY_DONE all checks passed");
        }

        static void Check(bool ok, string line) { Report.Add((ok ? "PASS " : "FAIL ") + line); if (!ok) failures++; }
        static Info InfoOf(string id) => JsonUtility.FromJson<Info>(File.ReadAllText(Path.Combine(Exports, id, "model_info.json")));

        // ------------------------------------------------------------------ import
        static void Import()
        {
            foreach (var id in Ids)
            {
                Copy(Path.Combine(Exports, id), Path.Combine(Repo, "apps/game", Models, id), $"{id}_{Version(id)}.fbx");
                if (File.Exists(Path.Combine(Exports, id, $"{id}_water_{Version(id)}.fbx")))
                    Copy(Path.Combine(Exports, id), Path.Combine(Repo, "apps/game", Models, id), $"{id}_water_{Version(id)}.fbx");
                if (!IsLayered(id)) Copy(Path.Combine(Exports, id, "Textures"), Path.Combine(Repo, "apps/game", Models, id, "Textures"), id + "_*.png");
            }
            // DR08: A / B / C share six hand-painted tiling layers (1024) and the plant atlas (2048) in DR08_Shared
            if (Ids.Any(IsLayered)) Copy(Path.Combine(Exports, "DR08_Shared", "Textures"), Path.Combine(Repo, "apps/game", Models, "DR08_Shared", "Textures"), "*.png");
            Copy(Path.Combine(Repo, "art/exports/d2-roots-b/Shared"), Path.Combine(Repo, "apps/game", Models, "Shared"), "*.png");
            AssetDatabase.Refresh();
            foreach (var guid in AssetDatabase.FindAssets("t:Model", new[] { Models }))
            {
                var importer = (ModelImporter)AssetImporter.GetAtPath(AssetDatabase.GUIDToAssetPath(guid));
                if (importer.bakeAxisConversion && importer.materialImportMode == ModelImporterMaterialImportMode.ImportViaMaterialDescription) continue;
                importer.bakeAxisConversion = true; importer.importCameras = false; importer.importLights = false; importer.addCollider = false;
                importer.importAnimation = false; importer.materialImportMode = ModelImporterMaterialImportMode.ImportViaMaterialDescription;
                importer.SaveAndReimport();
            }
            foreach (var guid in AssetDatabase.FindAssets("t:Texture2D", new[] { Models }))
            {
                var path = AssetDatabase.GUIDToAssetPath(guid);
                var ti = (TextureImporter)AssetImporter.GetAtPath(path);
                bool normal = path.EndsWith("_Normal.png"), linear = normal || path.EndsWith("_MaskURP.png") || path.EndsWith("_ORM.png");
                var type = normal ? TextureImporterType.NormalMap : TextureImporterType.Default;
                if (ti.textureType == type && ti.sRGBTexture == !linear && ti.maxTextureSize == 2048) continue;
                ti.textureType = type; ti.sRGBTexture = !linear; ti.mipmapEnabled = true; ti.maxTextureSize = 2048;
                ti.SaveAndReimport();
            }
        }

        static void Copy(string sourceDir, string targetDir, string pattern)
        {
            Directory.CreateDirectory(targetDir);
            var files = Directory.GetFiles(sourceDir, pattern);
            if (files.Length == 0) throw new FileNotFoundException($"{sourceDir}/{pattern}");
            foreach (var file in files)
            {
                if (new FileInfo(file).Length < 1024 && File.ReadAllText(file).StartsWith("version https://git-lfs"))
                    throw new InvalidOperationException("Git LFS pointer instead of asset; run git lfs pull: " + file);
                var target = Path.Combine(targetDir, Path.GetFileName(file));
                if (!File.Exists(target) || new FileInfo(target).Length != new FileInfo(file).Length) File.Copy(file, target, true);
            }
        }

        static readonly Dictionary<string, Material> Mats = new Dictionary<string, Material>();
        static bool IsLayered(string id) => id.StartsWith("DR08");
        static readonly string[] Layers = { "Bark", "Moss", "Rot", "Fibre", "Inner", "Soil" };
        static Texture2D SharedTex(string name) => AssetDatabase.LoadAssetAtPath<Texture2D>($"{Models}/DR08_Shared/Textures/{name}.png");
        // DR08: the body slot gets YunJing/D2LayeredWood (six layers mixed by vertex colour + UV1), the bracket fungus slot and Detail_ the plant atlas
        static Material MatFor(string id, Renderer r, Material imported, Info info)
        {
            if (!IsLayered(id)) return Mat(id, IsDetail(r), info);
            bool plants = IsDetail(r) || (imported != null && imported.name.Contains("Plants"));
            string key = "DR08" + (plants ? "Plants" : "Layered");
            if (Mats.TryGetValue(key, out var cached) && cached) return cached;
            var dir = $"{Models}/DR08_Shared/Materials"; Directory.CreateDirectory(Path.Combine(Repo, "apps/game", dir));
            var path = $"{dir}/M_DR08_{(plants ? "Plants" : "Layered")}.mat";
            var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
            var shader = Shader.Find(plants ? "Universal Render Pipeline/Lit" : "YunJing/D2LayeredWood");
            Check(shader != null, $"{id}: shader {(plants ? "URP Lit" : "YunJing/D2LayeredWood")} found");
            if (mat == null) { mat = new Material(shader); AssetDatabase.CreateAsset(mat, path); } else mat.shader = shader;
            if (plants)
            {
                var a = SharedTex("DR08_Plants_Albedo");
                Check(a != null, $"{id}: DR08_Plants_Albedo.png found");
                mat.SetTexture("_BaseMap", a); mat.SetColor("_BaseColor", Color.white); mat.SetFloat("_Smoothness", .15f);
                mat.SetFloat("_AlphaClip", 1); mat.SetFloat("_Cutoff", .5f); mat.EnableKeyword("_ALPHATEST_ON");
                mat.SetFloat("_Cull", (float)CullMode.Off); mat.doubleSidedGI = true;
                mat.renderQueue = (int)UnityEngine.Rendering.RenderQueue.AlphaTest; mat.SetOverrideTag("RenderType", "TransparentCutout");
            }
            else
            {
                var sizes = new List<string>();
                foreach (var l in Layers)
                {
                    var al = SharedTex($"DR08_{l}_Albedo"); var nm = SharedTex($"DR08_{l}_Normal");
                    Check(al != null && nm != null, $"{id}: DR08_{l}_Albedo / Normal found");
                    mat.SetTexture($"_{l}Map", al); mat.SetTexture($"_{l}Nrm", nm);
                    foreach (var t in new[] { al, nm }.Where(t => t))
                    {
                        ((TextureImporter)AssetImporter.GetAtPath(AssetDatabase.GetAssetPath(t))).GetSourceTextureWidthAndHeight(out int w, out int h);
                        sizes.Add($"{w}x{h}");
                    }
                }
                var src = sizes.Distinct().ToArray();
                Check(src.Length == 1 && src[0] == "1024x1024", $"{id}: shared tiling layers delivered at {string.Join(", ", src)} (1024, tiled 1–2 times per metre)");
            }
            EditorUtility.SetDirty(mat); Mats[key] = mat;
            return mat;
        }
        static Material Mat(string id, bool leaf, Info info)
        {
            string key = id + (leaf ? "Leaf" : "A");
            if (Mats.TryGetValue(key, out var cached) && cached) return cached;
            var dir = $"{Models}/{id}/Materials"; Directory.CreateDirectory(Path.Combine(Repo, "apps/game", dir));
            var path = $"{dir}/M_{id}_{(leaf ? "Leaf" : "A")}.mat";
            var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (mat == null) { mat = new Material(Shader.Find("Universal Render Pipeline/Lit")); AssetDatabase.CreateAsset(mat, path); }
            var albedo = Tex(id, "Albedo"); var mask = Tex(id, "MaskURP"); var normal = Tex(id, "Normal"); var orm = Tex(id, "ORM");
            var detail = AssetDatabase.LoadAssetAtPath<Texture2D>($"{Models}/Shared/D2Bark_Detail_Normal.png");
            if (leaf) { Setup(mat, albedo, normal, mask, null, info); mat.SetFloat("_Cull", (float)CullMode.Off); mat.doubleSidedGI = true; EditorUtility.SetDirty(mat); Mats[key] = mat; return mat; }
            Check(albedo != null && mask != null && normal != null && orm != null, $"{id}: Albedo / Normal / ORM / MaskURP textures found");
            var all = new[] { albedo, normal, orm, mask };
            var src = all.Where(t => t).Select(t => { ((TextureImporter)AssetImporter.GetAtPath(AssetDatabase.GetAssetPath(t))).GetSourceTextureWidthAndHeight(out int w, out int h); return $"{w}x{h}"; }).Distinct().ToArray();
            Check(src.Length == 1 && src[0] == "2048x2048", $"{id}: delivered textures {string.Join(", ", src)} (larger than a person: 2048)");
            var tiA = (TextureImporter)AssetImporter.GetAtPath(AssetDatabase.GetAssetPath(albedo));
            Report.Add($"INFO {id}: imported at {string.Join(", ", all.Where(t => t).Select(t => $"{t.width}x{t.height}").Distinct())} on {EditorUserBuildSettings.activeBuildTarget} (importer max {tiA.maxTextureSize})");
            Setup(mat, albedo, normal, mask, detail, info);
            if (detail != null) Report.Add($"INFO {id}: bark detail on UV0, tiling {info.unity.detail_tiling_on_uv0:0.00}");
            EditorUtility.SetDirty(mat); Mats[key] = mat;
            return mat;
        }

        static void Setup(Material mat, Texture2D albedo, Texture2D normal, Texture2D mask, Texture2D detail, Info info)
        {
            mat.SetTexture("_BaseMap", albedo); mat.SetColor("_BaseColor", Color.white);
            mat.SetTexture("_BumpMap", normal); mat.EnableKeyword("_NORMALMAP");
            mat.SetTexture("_MetallicGlossMap", mask); mat.EnableKeyword("_METALLICSPECGLOSSMAP"); mat.SetFloat("_Smoothness", 1);
            mat.SetTexture("_OcclusionMap", mask); mat.EnableKeyword("_OCCLUSIONMAP");
            if (detail != null && info.unity != null && info.unity.detail_tiling_on_uv0 > 0)
            {
                var ti = (TextureImporter)AssetImporter.GetAtPath(AssetDatabase.GetAssetPath(detail));
                if (ti.textureType != TextureImporterType.NormalMap) { ti.textureType = TextureImporterType.NormalMap; ti.SaveAndReimport(); }
                var detailAlbedo = AssetDatabase.LoadAssetAtPath<Texture2D>($"{Models}/Shared/D2Bark_Detail_Albedo.png");
                mat.SetTexture("_DetailNormalMap", detail); mat.SetFloat("_DetailNormalMapScale", 1);
                mat.SetTexture("_DetailAlbedoMap", detailAlbedo); mat.SetFloat("_DetailAlbedoMapScale", 1);
                mat.SetTexture("_DetailMask", albedo);
                float t = info.unity.detail_tiling_on_uv0;
                mat.SetTextureScale("_DetailAlbedoMap", new Vector2(t, t));
                mat.EnableKeyword("_DETAIL_MULX2");
            }
        }
        static Texture2D Tex(string id, string kind) => AssetDatabase.LoadAssetAtPath<Texture2D>($"{Models}/{id}/Textures/{id}_A_{kind}.png");

        static bool IsDetail(Renderer r) => r.name.StartsWith("Detail_");
        static bool IsCollision(Component r) => r.name.EndsWith("_Collision");

        // The origin is at the bottom centre. The checks and shots use the build coordinates (root plate at x = 0, trunk along +x, snapped end
        // at x = L): put the build origin on the world origin. Blender (x, y, z) comes in as Unity (x, z, y).
        static GameObject Place(string id, Info info, bool atBuild = true)
        {
            var go = (GameObject)PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>($"{Models}/{id}/{id}_{Version(id)}.fbx"));
            foreach (var r in go.GetComponentsInChildren<Renderer>(true))
            {
                r.sharedMaterials = r.sharedMaterials.Select(sm => MatFor(id, r, sm, info)).ToArray();
                if (IsCollision(r)) { r.enabled = false; r.gameObject.AddComponent<MeshCollider>().sharedMesh = r.GetComponent<MeshFilter>().sharedMesh; }
            }
            float[] cut = { .25f, .08f, .015f };
            var kids = go.GetComponentsInChildren<Renderer>(true).Where(r => !IsCollision(r)).ToArray();
            var lg = go.GetComponent<LODGroup>(); if (lg == null) lg = go.AddComponent<LODGroup>();
            lg.SetLODs(Enumerable.Range(0, 3).Select(i => new LOD(cut[i], kids.Where(r => r.name.EndsWith("_LOD" + i)).ToArray())).ToArray());
            var p = info.build_origin_m;
            if (atBuild && p != null && p.Length == 3) go.transform.position = new Vector3(-p[0], -p[2], -p[1]);
            return go;
        }

        // the user's water from the creek repair pack: YunJing/CreekFlowWater in still mode (as Field_StillWater), tinted tea brown
        static Material WaterMat(string id)
        {
            var shader = Shader.Find("YunJing/CreekFlowWater"); if (shader == null || ShaderUtil.ShaderHasError(shader)) throw new InvalidOperationException("CreekFlowWater did not compile");
            var dir = $"{Models}/{id}/Materials"; Directory.CreateDirectory(Path.Combine(Repo, "apps/game", dir));
            var path = $"{dir}/M_{id}_Water.mat";
            var m = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (m == null) { m = new Material(shader); AssetDatabase.CreateAsset(m, path); }
            m.shader = shader; m.SetColor("_Shallow", new Color(.18f, .255f, .21f)); m.SetColor("_Deep", new Color(.085f, .16f, .135f));
            // a stump pool: rain water steeped in rotten wood is tea brown and clear, so the mud and leaves 14 cm down show through
            m.SetFloat("_Still", 1); m.SetFloat("_Speed", .03f); m.SetFloat("_AlphaMid", .6f); m.SetFloat("_AlphaBank", .6f);
            m.SetVector("_StillColour", new Vector4(.05f, .036f, .02f, 1));
            m.SetFloat("_Ripple", .012f); m.SetFloat("_Gloss", 512);      // a pool in a stump barely moves: at 0.06 / 220 the sun glints read as white streaks
            EditorUtility.SetDirty(m); return m;
        }

        static GameObject PlaceWater(string id, Info info, bool atBuild = true)
        {
            var asset = AssetDatabase.LoadAssetAtPath<GameObject>($"{Models}/{id}/{id}_water_{Version(id)}.fbx");
            if (asset == null) return null;
            var go = (GameObject)PrefabUtility.InstantiatePrefab(asset);
            var mat = WaterMat(id);
            var rs = go.GetComponentsInChildren<Renderer>(true);
            // slot 0 is the water; slot 1 (LOD0 / LOD1) the leaves floating on it, on the stump atlas like the Detail_ plants
            foreach (var r in rs)
            {
                r.sharedMaterials = r.sharedMaterials.Select((sm, k) => k == 0 ? mat : Mat(id, true, info)).ToArray();
                r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            }
            float[] cut = { .25f, .08f, .015f };
            var lg = go.GetComponent<LODGroup>(); if (lg == null) lg = go.AddComponent<LODGroup>();
            lg.SetLODs(Enumerable.Range(0, 3).Select(i => new LOD(cut[i], rs.Where(r => r.name.EndsWith("_LOD" + i)).ToArray())).ToArray());
            var p = info.build_origin_m;
            if (atBuild && p != null && p.Length == 3) go.transform.position = new Vector3(-p[0], -p[2], -p[1]);
            return go;
        }

        static void Detail(GameObject go, bool on) { foreach (var r in go.GetComponentsInChildren<Renderer>(true).Where(IsDetail)) r.enabled = on; }
        static Renderer[] Level(GameObject go, int i, bool detail = true) =>
            go.GetComponentsInChildren<Renderer>(true).Where(r => r.name.EndsWith("_LOD" + i) && (detail || !IsDetail(r))).ToArray();
        static int Tris(IEnumerable<Renderer> rs) => rs.Sum(r => { var m = r.GetComponent<MeshFilter>().sharedMesh; return Enumerable.Range(0, m.subMeshCount).Sum(s => (int)m.GetIndexCount(s)) / 3; });
        static Bounds Box(IEnumerable<Renderer> rs) { var a = rs.ToArray(); var b = a[0].bounds; foreach (var r in a) b.Encapsulate(r.bounds); return b; }

        // ------------------------------------------------------------------ checks
        static void Inspect(string id, Info info)
        {
            var go = Place(id, info, false);
            var body = Box(Level(go, 0, false));
            float[] d = info.dimensions_m;
            if (HasWater(info))
            {
                // the water FBX: three LODs, no collider, flat at the pool height, centred on the hollow, inside the stump's footprint
                var w = PlaceWater(id, info, false);
                Check(w != null, $"{id}: water model {info.water.file} imported");
                if (w != null)
                {
                    var wr = w.GetComponentsInChildren<Renderer>(true);
                    var w0 = wr.Where(r => r.name.EndsWith("_LOD0")).ToArray();
                    Check(Enumerable.Range(0, 3).All(i => wr.Count(r => r.name == $"{id}_water_LOD{i}") == 1), $"{id}: water LOD0 / LOD1 / LOD2 ({string.Join(", ", wr.Select(r => r.name))})");
                    Check(w.GetComponentsInChildren<Collider>(true).Length == 0, $"{id}: the water has no collider (the stump collision closes the hollow)");
                    var wb = Box(w0);
                    Check(Mathf.Abs(wb.min.y - info.water.z_m) <= .01f && wb.size.y < .03f, $"{id}: water flat at y = {wb.min.y:0.000} m, floating leaves at most {wb.size.y * 100:0.0} cm above it (model_info {info.water.z_m:0.000})");
                    var c = info.water.centre_xy_m;
                    Check(c != null && c.Length == 2 && Mathf.Abs(wb.center.x - c[0]) <= .05f && Mathf.Abs(wb.center.z - c[1]) <= .05f,
                        $"{id}: water centred on the hollow ({wb.center.x:0.00}, {wb.center.z:0.00}) (model_info {c?[0]:0.00}, {c?[1]:0.00})");
                    Check(wb.min.x > body.min.x && wb.max.x < body.max.x && wb.min.z > body.min.z && wb.max.z < body.max.z,
                        $"{id}: water {wb.size.x:0.00} x {wb.size.z:0.00} m inside the stump {body.size.x:0.00} x {body.size.z:0.00} m");
                    Check(wr.All(r => r.sharedMaterials[0].shader.name == "YunJing/CreekFlowWater" && r.sharedMaterials[0].GetFloat("_Still") == 1),
                        $"{id}: water uses YunJing/CreekFlowWater, still (_Still 1, _Speed 0.03, _AlphaMid 0.6, _StillColour tea brown)");
                    var mf = w0[0].GetComponent<MeshFilter>().sharedMesh;
                    Check(mf.subMeshCount == 2 && w0[0].sharedMaterials[1].GetFloat("_Cull") == 0, $"{id}: {mf.subMeshCount - 1} submesh of floating leaves on LOD0, two-sided stump-atlas material");
                    Check(mf.uv.Length == mf.vertexCount && mf.uv.Max(u => Mathf.Max(Mathf.Abs(u.x), Mathf.Abs(u.y))) > .3f, $"{id}: water UV in metres from the centre");
                    UnityEngine.Object.DestroyImmediate(w);
                }
            }
            Check(Mathf.Abs(body.size.x - d[0]) <= .02f && Mathf.Abs(body.size.z - d[1]) <= .02f && Mathf.Abs(body.size.y - d[2]) <= .02f,
                $"{id}: imported size {body.size.x:0.000} x {body.size.z:0.000} x {body.size.y:0.000} m matches model_info {d[0]} x {d[1]} x {d[2]} within 2 cm");
            Check(body.min.y < 0 && body.min.y > -1.0f, $"{id}: lowest point y = {body.min.y:0.000} (the trunk sinks into the soil, origin on the ground)");
            Check(Mathf.Abs(body.center.x) <= .02f && Mathf.Abs(body.center.z) <= .02f,
                $"{id}: origin at the bottom centre (LOD0 body footprint centre {body.center.x:0.000}, {body.center.z:0.000} m from the origin; y = 0 is the ground)");
            var levels = info.budget_per_lod.All;
            var tris = Enumerable.Range(0, 3).Select(i => Tris(Level(go, i))).ToArray();
            Check(Enumerable.Range(0, 3).All(i => Mathf.Abs(tris[i] - levels[i].triangles) <= levels[i].triangles * .01f),
                $"{id}: triangles LOD0/1/2 = {tris[0]} / {tris[1]} / {tris[2]} ({100f * tris[1] / tris[0]:0}% / {100f * tris[2] / tris[0]:0}%), model_info {levels[0].triangles} / {levels[1].triangles} / {levels[2].triangles}");
            var objs = Enumerable.Range(0, 3).Select(i => Level(go, i).Length).ToArray();
            Check(Enumerable.Range(0, 3).All(i => objs[i] == levels[i].objects), $"{id}: objects per LOD {string.Join(" / ", objs)} (model_info {string.Join(" / ", levels.Select(l => l.objects))})");
            var mats = go.GetComponentsInChildren<Renderer>(true).Where(r => !IsCollision(r)).SelectMany(r => r.sharedMaterials).Distinct().Count();
            Check(mats == levels[0].materials, $"{id}: {mats} materials over every LOD and Detail_ mesh (model_info {levels[0].materials}: body, two-sided plants)");
            Check(go.GetComponentsInChildren<Renderer>(true).Where(IsDetail).All(r => r.sharedMaterials.All(x => x.GetFloat("_Cull") == 0)), $"{id}: Detail_* plants render both faces");
            Check(info.minTier == "standard", $"{id}: minTier = {info.minTier} (blocks the way: everyone sees it)");
            Check(info.detailObjects.Length > 0 && info.detailObjects.All(g => g.StartsWith("Detail_") && Level(go, 0).Any(r => r.name.StartsWith(g))),
                $"{id}: detailObjects {string.Join(", ", info.detailObjects)} present in the FBX");
            Detail(go, false);
            int shown = Level(go, 0).Count(r => r.enabled);
            Check(shown == 1, $"{id}: Detail_* off still shows the body ({shown} mesh per LOD)");
            Detail(go, true);
            foreach (var mf in Level(go, 0).Select(r => r.GetComponent<MeshFilter>().sharedMesh))
                if (!IsLayered(id)) Check(mf.uv.Length == mf.vertexCount && mf.uv2.Length == mf.vertexCount, $"{id}: {mf.name} has UV0 (atlas) and UV1 (TileUV)");
            if (IsLayered(id))
            {
                var body0 = Level(go, 0, false)[0];
                var m0 = body0.GetComponent<MeshFilter>().sharedMesh;
                Check(m0.uv.Length == m0.vertexCount && m0.uv2.Length == m0.vertexCount && m0.colors.Length == m0.vertexCount,
                    $"{id}: {m0.name} has UV0 (metres), UV1 (soil, AO) and vertex colours (moss, rot, fibre, inner weights)");
                var c = m0.colors; var u2 = m0.uv2;
                Report.Add($"INFO {id}: mean layer weights moss {c.Average(q => q.r):0.00}, rot {c.Average(q => q.g):0.00}, fibre {c.Average(q => q.b):0.00}, inner {c.Average(q => q.a):0.00}, soil {u2.Average(q => q.x):0.00}; AO {u2.Min(q => q.y):0.00}–{u2.Max(q => q.y):0.00}");
                Check(body0.sharedMaterials.Length >= 1 && body0.sharedMaterials[0].shader.name == "YunJing/D2LayeredWood" && body0.sharedMaterials.Skip(1).All(x => x.GetFloat("_Cull") == 0),
                    $"{id}: body slots {string.Join(", ", body0.sharedMaterials.Select(x => x.name + " (" + x.shader.name + ")"))}: layered wood (any extra slot two-sided plant atlas)");
            }
            var col = go.GetComponentsInChildren<MeshCollider>(true);
            Check(col.Length == 1, $"{id}: one collision shell (MeshCollider, renderer off)");
            UnityEngine.Object.DestroyImmediate(go);
            // collision, in build coordinates: a 1.75 m walker (radius 0.35) crossing the trunk (along Unity z) is stopped along the lying
            // part; the root plate stops it too; the top of the trunk is solid underfoot
            go = Place(id, info);
            Physics.SyncTransforms();
            if (info.stump_build != null && info.stump_build.radius > 0)
            {
                // DR07 stump: a 1.75 m walker crossing the stump (along Unity z) is stopped on five lines across the trunk; the hollow is closed
                // on top in the collision (nobody falls into the water); the root collar is a low step (under 0.45 m)
                var s = info.stump_build; int sn = 0, sh = 0;
                foreach (float k in new[] { -.6f, -.3f, 0f, .3f, .6f })
                {
                    sn++;
                    float x = s.axis_x + k * s.radius;
                    if (Physics.CapsuleCast(new Vector3(x, .45f, s.axis_y - 12), new Vector3(x, 1.40f, s.axis_y - 12), .35f, Vector3.forward, 24)) sh++;
                }
                Check(sh == sn, $"{id}: a walker crossing the stump is stopped at {sh} of {sn} lines (-0.6 R to 0.6 R)");
                bool lid = Physics.Raycast(new Vector3(s.axis_x, 10, s.axis_y), Vector3.down, out var hl, 12);
                Check(lid && hl.point.y > s.pool_z + .3f, $"{id}: the hollow is closed on top in the collision (y = {(lid ? hl.point.y : 0):0.00} m, water at {s.pool_z:0.00} m)");
                bool step = Physics.Raycast(new Vector3(s.axis_x + 1.35f * s.radius, 10, s.axis_y), Vector3.down, out var hs, 12);
                Check(step && hs.point.y < .45f, $"{id}: the root collar at 1.35 R is a low step (y = {(step ? hs.point.y : 0):0.00} m)");
                UnityEngine.Object.DestroyImmediate(go);
                return;
            }
            float L = info.length_build_m;
            if (id.StartsWith("DR08"))
            {
                // DR08 rotten logs are low (top 0.6–0.85 m, below hip height): instead of the 1.75 m walker capsule, check that
                // a shin-high sweep (0.08–0.22 m, radius 0.06) is stopped all along, i.e. a walker has to step over or go round, and that the
                // highest point of the top along 0.1–0.9 L is between 0.35 and 1.1 m (the ends and the middle of A are crumbled open)
                int sn = 0, sh = 0;
                for (float x = .12f * L; x <= .90f * L; x += .5f, sn++)
                    if (Physics.CapsuleCast(new Vector3(x, .14f, -12), new Vector3(x, .16f, -12), .06f, Vector3.forward, 24)) sh++;
                Check(sh == sn, $"{id}: a shin-high sweep across the log is stopped at {sh} of {sn} places (every 0.5 m from 0.12 L to 0.90 L)");
                float best = 0;
                for (float x = .1f * L; x <= .9f * L; x += .1f)
                    if (Physics.Raycast(new Vector3(x, 10, 0), Vector3.down, out var hm, 12)) best = Mathf.Max(best, hm.point.y);
                Check(best > .35f && best < 1.1f, $"{id}: the highest point of the log's top (0.1–0.9 L) is a low obstacle below hip height (y = {best:0.00} m)");
                UnityEngine.Object.DestroyImmediate(go);
                return;
            }
            int n = 0, hit = 0;
            bool hollow = info.tunnel_build != null && info.tunnel_build.x1 > info.tunnel_build.x0;
            float lo = hollow ? .15f : .25f, hi = hollow ? .85f : .95f;          // DR05: both ends are ragged and open, check the closed middle
            for (float x = lo * L; x <= hi * L; x += .5f, n++)
                if (Physics.CapsuleCast(new Vector3(x, .45f, -12), new Vector3(x, 1.40f, -12), .35f, Vector3.forward, 24)) hit++;
            Check(hit == n, $"{id}: a walker crossing the trunk is stopped at {hit} of {n} places (every 0.5 m from {lo:0.00} L to {hi:0.00} L)");
            if (info.tunnel_build != null && info.tunnel_build.x1 > info.tunnel_build.x0)
            {
                // DR05 hollow log: a crouching walker (1.1 m capsule, radius 0.3) goes through the tunnel from one end to the other; a standing
                // one (1.75 m) is stopped by the roof
                var t = info.tunnel_build; float f = t.floor_z;
                bool crouch = Physics.CapsuleCast(new Vector3(-4, f + .32f, t.axis_y), new Vector3(-4, f + .80f, t.axis_y), .30f, Vector3.right, L + 8, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore);
                Check(!crouch, $"{id}: a crouching walker (1.1 m, radius 0.3) passes through the tunnel along x at y = {t.axis_y:0.00} (floor {f:0.00} m)");
                bool stand = Physics.CapsuleCast(new Vector3(-4, f + .37f, t.axis_y), new Vector3(-4, f + 1.40f, t.axis_y), .35f, Vector3.right, L + 8);
                Check(stand, $"{id}: a standing 1.75 m walker cannot walk upright through the tunnel (has to crouch)");
            }
            else
            {
                bool plate = Physics.CapsuleCast(new Vector3(info.plate_x_build_m, .45f, -12), new Vector3(info.plate_x_build_m, 1.40f, -12), .35f, Vector3.forward, 24);
                Check(plate, $"{id}: the root plate stops a walker (x = {info.plate_x_build_m:0.00})");
            }
            bool top = Physics.Raycast(new Vector3(.6f * L, 10, 0), Vector3.down, out var ht, 12);
            Check(top && ht.point.y > .8f, $"{id}: the top of the trunk is solid at 0.6 L (y = {(top ? ht.point.y : 0):0.00} m)");
            UnityEngine.Object.DestroyImmediate(go);
        }

        // ------------------------------------------------------------------ shots
        static Camera cam; static RenderTexture target; static Light sun;

        static void Shots(string id, Info info)
        {
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene);
            sun = new GameObject("Sun").AddComponent<Light>(); sun.type = LightType.Directional; sun.shadows = LightShadows.Soft;
            var ground = GameObject.CreatePrimitive(PrimitiveType.Plane); ground.transform.localScale = Vector3.one * 30;
            ground.GetComponent<Renderer>().sharedMaterial = Flat("ground", new Color(.17f, .15f, .12f));
            cam = new GameObject("Review Camera").AddComponent<Camera>(); cam.nearClipPlane = .05f; cam.farClipPlane = 600;
            UnityEngine.Rendering.Universal.CameraExtensions.GetUniversalAdditionalCameraData(cam).renderPostProcessing = true;
            target = new RenderTexture(1536, 864, 24) { antiAliasing = 4 }; cam.targetTexture = target;
            sun.transform.rotation = Quaternion.Euler(50, -35, 0); sun.intensity = 1.25f;
            RenderSettings.ambientMode = AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = new Color(.62f, .7f, .78f); RenderSettings.ambientEquatorColor = new Color(.55f, .58f, .52f); RenderSettings.ambientGroundColor = new Color(.32f, .3f, .26f);
            RenderSettings.fog = true; RenderSettings.fogMode = FogMode.Exponential; RenderSettings.fogDensity = .006f; RenderSettings.fogColor = new Color(.66f, .70f, .74f);
            cam.clearFlags = CameraClearFlags.SolidColor; cam.backgroundColor = new Color(.66f, .70f, .74f);
            var go = Place(id, info);
            var ruler = GameObject.CreatePrimitive(PrimitiveType.Capsule);
            UnityEngine.Object.DestroyImmediate(ruler.GetComponent<Collider>());
            float L = info.length_build_m;
            ruler.transform.position = info.ruler_build_xy != null && info.ruler_build_xy.Length == 2 ? new Vector3(info.ruler_build_xy[0], .875f, info.ruler_build_xy[1])
                : new Vector3(.45f * L, .875f, -2.2f * (info.dimensions_m[1] > 6 ? 1f : .7f)); ruler.transform.localScale = new Vector3(.42f, .875f, .42f);
            ruler.GetComponent<Renderer>().sharedMaterial = Flat("ruler", new Color(.85f, .85f, .85f));
            var water = HasWater(info) ? PlaceWater(id, info) : null;
            var lg = go.GetComponent<LODGroup>();
            lg.ForceLOD(0); if (water) water.GetComponent<LODGroup>().ForceLOD(0);
            var cams = info.review_cams_build_xyz.ToDictionary(c => c.name);
            void S(string file, Cam c) => Shot(id, file, new Vector3(c.from[0], c.from[2], c.from[1]), new Vector3(c.at[0], c.at[2], c.at[1]), c.lens_mm);
            S("side-lod0", cams["side"]);
            if (Raw) { var rk = cams.ContainsKey("snap") ? "snap" : cams.ContainsKey("end") ? "end" : "tq"; S(rk, cams[rk]); if (water) { water.SetActive(false); S(rk + "-dry", cams[rk]); } return; }      // 樹樁拍四分之三      // 空心倒木沒有斷口（snap），改拍洞口（end）
            foreach (var k in new[] { "tq", "plate", "plateq", "snap", "back", "sap", "end", "endA", "inside", "peel", "hinge", "into", "roots", "rim", "hole", "fungi", "brk" }) if (cams.ContainsKey(k)) S(k, cams[k]);
            if (water)
            {
                // dry: the same stump without the water FBX
                water.SetActive(false);
                foreach (var k in new[] { "tq", "into", "rim" }) if (cams.ContainsKey(k)) S(k + "-dry", cams[k]);
                water.SetActive(true);
            }
            for (int i = 1; i < 3; i++) { lg.ForceLOD(i); if (water) water.GetComponent<LODGroup>().ForceLOD(i); S($"side-lod{i}", cams["side"]); }
            if (water) water.GetComponent<LODGroup>().ForceLOD(-1);
            lg.ForceLOD(1); Detail(go, false);
            S("side-standard-tier-lod1-nodetail", cams["side"]);
            Detail(go, true); lg.ForceLOD(-1);
            Report.Add($"INFO renders written to art/previews/d2-logs-b/{id}/unity");
        }

        // vertical field of view of a lens (mm) on a 36 mm wide sensor, 16:9 image
        static void Shot(string id, string file, Vector3 from, Vector3 at, float lens)
        {
            float h = 2 * Mathf.Atan(18f / lens);
            cam.fieldOfView = 2 * Mathf.Atan(Mathf.Tan(h / 2) * 864f / 1536f) * Mathf.Rad2Deg;
            cam.transform.position = from; cam.transform.LookAt(at); cam.Render();
            RenderTexture.active = target;
            var image = new Texture2D(target.width, target.height, TextureFormat.RGB24, false);
            image.ReadPixels(new Rect(0, 0, target.width, target.height), 0, 0); image.Apply();
            File.WriteAllBytes(Path.Combine(Out(id), $"{id}-{file}{(Raw ? "-rawimport" : "")}.png"), image.EncodeToPNG());
            RenderTexture.active = null; UnityEngine.Object.DestroyImmediate(image);
        }

        static Material Flat(string name, Color color)
        {
            var path = $"{Models}/{name}.mat";
            var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (mat == null) { mat = new Material(Shader.Find("Universal Render Pipeline/Lit")); AssetDatabase.CreateAsset(mat, path); }
            mat.SetColor("_BaseColor", color); mat.SetFloat("_Smoothness", .1f);
            return mat;
        }
    }
}
