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
    // Unity check of B's D2 fallen logs and stumps (art/exports/d2-logs-b, joshsu54: DR06 fallen trunk, DR05 hollow log), the same way as D2RootsVerify (d2-roots-b). It does
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
        static readonly string[] AllIds = { "DR06_FallenTrunk_B", "DR06_FallenTrunk_A", "DR05_HollowLog" };
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
        [Serializable] class Info
        {
            public float[] dimensions_m; public string minTier; public string[] detailObjects; public Lods budget_per_lod; public UnityInfo unity;
            public float[] build_origin_m; public float length_build_m, plate_x_build_m; public Cam[] review_cams_build_xyz; public Tunnel tunnel_build;
        }

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
                Copy(Path.Combine(Exports, id, "Textures"), Path.Combine(Repo, "apps/game", Models, id, "Textures"), id + "_*.png");
            }
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
                r.sharedMaterials = r.sharedMaterials.Select(sm => Mat(id, IsDetail(r), info)).ToArray();
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
                Check(mf.uv.Length == mf.vertexCount && mf.uv2.Length == mf.vertexCount, $"{id}: {mf.name} has UV0 (atlas) and UV1 (TileUV)");
            var col = go.GetComponentsInChildren<MeshCollider>(true);
            Check(col.Length == 1, $"{id}: one collision shell (MeshCollider, renderer off)");
            UnityEngine.Object.DestroyImmediate(go);
            // collision, in build coordinates: a 1.75 m walker (radius 0.35) crossing the trunk (along Unity z) is stopped along the lying
            // part; the root plate stops it too; the top of the trunk is solid underfoot
            go = Place(id, info);
            Physics.SyncTransforms();
            float L = info.length_build_m;
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
            ruler.transform.position = new Vector3(.45f * L, .875f, -2.2f * (info.dimensions_m[1] > 6 ? 1f : .7f)); ruler.transform.localScale = new Vector3(.42f, .875f, .42f);
            ruler.GetComponent<Renderer>().sharedMaterial = Flat("ruler", new Color(.85f, .85f, .85f));
            var lg = go.GetComponent<LODGroup>();
            lg.ForceLOD(0);
            var cams = info.review_cams_build_xyz.ToDictionary(c => c.name);
            void S(string file, Cam c) => Shot(id, file, new Vector3(c.from[0], c.from[2], c.from[1]), new Vector3(c.at[0], c.at[2], c.at[1]), c.lens_mm);
            S("side-lod0", cams["side"]);
            if (Raw) { var rk = cams.ContainsKey("snap") ? "snap" : "end"; S(rk, cams[rk]); return; }      // 空心倒木沒有斷口（snap），改拍洞口（end）
            foreach (var k in new[] { "tq", "plate", "plateq", "snap", "back", "sap", "end", "endA", "inside", "peel" }) if (cams.ContainsKey(k)) S(k, cams[k]);
            for (int i = 1; i < 3; i++) { lg.ForceLOD(i); S($"side-lod{i}", cams["side"]); }
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
