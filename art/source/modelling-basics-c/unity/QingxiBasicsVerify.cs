using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

namespace YunJing.Editor
{
    // Unity check of C's modelling-basics models (art/exports/modelling-basics-c, Eli-0731). The work pack says not to change apps/game,
    // so this file lives in art/source/modelling-basics-c/unity and run_unity_check.sh copies it in for the run and removes it after.
    // Imports the delivered FBX and textures, builds URP materials, LODGroup and colliders from the node names, compares them with
    // model_info.json (size, width, triangles, minTier, detailObjects), switches the Detail_* meshes off the way the standard tier
    // will, walks a player capsule into each crate and renders review shots.
    //   Unity -batchmode -quit -projectPath apps/game -executeMethod YunJing.Editor.QingxiBasicsVerify.Run -logFile <log>
    // Output: art/previews/modelling-basics-c/unity/*.png and report.txt; the run fails when a check fails.
    public static class QingxiBasicsVerify
    {
        const string Models = "Assets/YunJing/Models/BasicsC";   // temporary copy of art/exports, removed by the run script
        static readonly string[] Ids = { "BM01_01", "BM01_02", "BM01_03", "BM02_01", "BM02_02", "BM03_01", "BM03_02", "BM03_03", "BM04_01", "BM04_02", "BM04_03", "BM04_04", "BM05_01", "BM05_02", "BM05_03", "BM06_01", "BM06_02", "BM06_03", "BM06_04", "BM07_01",
                                                    "BM08_01", "BM08_02", "BM09_01", "BM09_02", "BM10_01", "BM10_02", "BM10_03" };
        // work pack §2: crates block the way (standard); the hitching posts are dressing (high), so they carry no collision
        static readonly Dictionary<string, string> Tier = new Dictionary<string, string> { { "BM01", "standard" }, { "BM02", "high" }, { "BM03", "high" }, { "BM04", "standard" }, { "BM05", "standard" }, { "BM06", "standard" }, { "BM07", "standard" },
            { "BM08_01", "standard" }, { "BM08_02", "high" }, { "BM09_01", "standard" }, { "BM09_02", "high" }, { "BM10", "ultra" } };   // an id overrides its item (BM08, BM09: one standard, one high)
        // ground decals: a flat patch has nothing to take away on a lower tier
        static readonly HashSet<string> NoDetail = new HashSet<string> { "BM10_01", "BM10_02", "BM10_03" };
        // standard-tier items the work pack gives no _Collision (BM04: only the largest stone has one)
        static readonly HashSet<string> NoCollision = new HashSet<string> { "BM04_02", "BM04_03", "BM04_04", "BM08_01", "BM09_01" };   // BM08_01 a shrub to brush past, BM09_01 a fern: nothing to stop on
        // foliage drawn on alpha-cut cards (leaves, fronds, fallen leaves, the leaf-litter ground patches): alpha clip and both faces
        static bool Cutout(string group) => Regex.IsMatch(group, @"^BM08_0\d_(Leaves|Detail_Litter)$|^BM09_0\d_(Fronds|Detail_DryFronds)$|^BM10_0[123]_Ground$");
        static string Repo => Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", ".."));
        static string Out => Path.Combine(Repo, "art/previews/modelling-basics-c/unity");
        static readonly List<string> Report = new List<string>();
        static int failures;
        static readonly HashSet<string> Checked = new HashSet<string>();
        static string json;

        [Serializable] class Info { public float[] dimensions_xyz_m, body_dimensions_xyz_m; public string target_axis; public float target_m; public int[] triangles_total; public string minTier; public string[] detailObjects, detailMeshes; }

        public static void Run()
        {
            Report.Clear(); Checked.Clear(); failures = 0;
            Directory.CreateDirectory(Out);
            Import();
            QingxiUrpUpgrade.EnsurePipeline();
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene);
            json = File.ReadAllText(Path.Combine(Repo, "art/exports/modelling-basics-c/model_info.json"));
            Report.Add($"Unity {Application.unityVersion}, pipeline {GraphicsSettings.currentRenderPipeline?.name ?? "built-in"}");
            foreach (var id in Ids) Inspect(id, JsonUtility.FromJson<Info>(Block(json, id)));
            Shots();
            File.WriteAllLines(Path.Combine(Out, "report.txt"), Report);
            foreach (var line in Report) Debug.Log("BASICS " + line);
            if (failures > 0) throw new Exception($"BASICS_VERIFY {failures} check(s) failed, see {Out}/report.txt");
            Debug.Log($"BASICS_VERIFY_DONE all checks passed, output {Out}");
        }

        static void Check(bool ok, string line) { Report.Add((ok ? "PASS " : "FAIL ") + line); if (!ok) failures++; }

        // model_info.json is keyed by id; JsonUtility only reads objects, so cut out each item's braces.
        static string Block(string text, string key)
        {
            int at = text.IndexOf($"\"{key}\":", StringComparison.Ordinal);
            if (at < 0) return null;
            int start = text.IndexOf('{', at), depth = 0;
            for (int i = start; i < text.Length; i++)
            {
                if (text[i] == '{') depth++;
                else if (text[i] == '}' && --depth == 0) return text.Substring(start, i - start + 1);
            }
            throw new InvalidDataException("model_info.json: no item " + key);
        }

        // ------------------------------------------------------------------ import
        static void Import()
        {
            foreach (var id in Ids)
            {
                Copy(Path.Combine(Repo, "art/exports/modelling-basics-c"), Path.Combine(Repo, "apps/game", Models, id), id + ".fbx");
                Copy(Path.Combine(Repo, "art/textures/modelling-basics-c"), Path.Combine(Repo, "apps/game", Models, id, "Textures"), id + "_*.png");
            }
            AssetDatabase.Refresh();
            foreach (var guid in AssetDatabase.FindAssets("t:Model", new[] { Models }))
            {
                var importer = (ModelImporter)AssetImporter.GetAtPath(AssetDatabase.GUIDToAssetPath(guid));
                if (importer.bakeAxisConversion && importer.materialImportMode == ModelImporterMaterialImportMode.None) continue;
                importer.bakeAxisConversion = true; importer.importCameras = false; importer.importLights = false; importer.addCollider = false;
                importer.importAnimation = false; importer.materialImportMode = ModelImporterMaterialImportMode.None;
                importer.SaveAndReimport();
            }
            foreach (var guid in AssetDatabase.FindAssets("t:Texture2D", new[] { Models }))
            {
                var path = AssetDatabase.GUIDToAssetPath(guid);
                var ti = (TextureImporter)AssetImporter.GetAtPath(path);
                bool normal = path.EndsWith("_Normal.png"), linear = normal || path.EndsWith("_MaskURP.png") || path.EndsWith("_ORM.png");
                var type = normal ? TextureImporterType.NormalMap : TextureImporterType.Default;
                bool cut = path.EndsWith("_Albedo.png") && Cutout(Path.GetFileNameWithoutExtension(path).Replace("_Albedo", ""));
                if (ti.textureType == type && ti.sRGBTexture == !linear && ti.alphaIsTransparency == cut) continue;
                ti.textureType = type; ti.sRGBTexture = !linear; ti.mipmapEnabled = true;
                ti.alphaIsTransparency = cut; ti.mipMapsPreserveCoverage = cut; ti.alphaTestReferenceValue = .45f;   // keeps the leaves from thinning out in the far mips
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

        // One URP Lit per group: Albedo, Normal, MaskURP (R metal, G AO, A smoothness).
        static Material Mat(string id, string name)
        {
            var dir = $"{Models}/{id}/Materials"; Directory.CreateDirectory(Path.Combine(Repo, "apps/game", dir));
            var path = $"{dir}/{name}.mat";
            var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (mat == null) { mat = new Material(Shader.Find("Universal Render Pipeline/Lit")); AssetDatabase.CreateAsset(mat, path); }
            var albedo = Tex(id, name, "Albedo"); var mask = Tex(id, name, "MaskURP"); var normal = Tex(id, name, "Normal");
            if (Checked.Add(name)) Check(albedo != null && mask != null && normal != null, $"{name}: Albedo / MaskURP / Normal textures found");
            mat.SetTexture("_BaseMap", albedo); mat.SetColor("_BaseColor", Color.white);
            mat.SetTexture("_BumpMap", normal); mat.EnableKeyword("_NORMALMAP");
            mat.SetTexture("_MetallicGlossMap", mask); mat.EnableKeyword("_METALLICSPECGLOSSMAP"); mat.SetFloat("_Smoothness", 1);
            mat.SetTexture("_OcclusionMap", mask); mat.EnableKeyword("_OCCLUSIONMAP");
            if (Cutout(name))
            {
                mat.SetFloat("_AlphaClip", 1); mat.SetFloat("_Cutoff", .45f); mat.EnableKeyword("_ALPHATEST_ON");
                mat.SetFloat("_Cull", (float)UnityEngine.Rendering.CullMode.Off); mat.renderQueue = (int)UnityEngine.Rendering.RenderQueue.AlphaTest;
                if (Checked.Add(name + "#cutout")) Check(albedo != null && albedo.alphaIsTransparency, $"{name}: alpha-cut foliage material (cutoff 0.45, both faces)");
            }
            EditorUtility.SetDirty(mat);
            return mat;
        }
        static Texture2D Tex(string id, string group, string kind) => AssetDatabase.LoadAssetAtPath<Texture2D>($"{Models}/{id}/Textures/{group}_{kind}.png");

        static GameObject Place(string id, Vector3 at, float yaw)
        {
            var go = (GameObject)PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>($"{Models}/{id}/{id}.fbx"));
            go.transform.SetPositionAndRotation(at, Quaternion.Euler(0, yaw, 0));
            foreach (var r in go.GetComponentsInChildren<Renderer>(true))
            {
                if (r.name.StartsWith(id + "_Collision")) { r.enabled = false; continue; }
                var group = Regex.Match(r.name, @"^(.+)_LOD\d$");
                if (group.Success) r.sharedMaterials = Enumerable.Repeat(Mat(id, group.Groups[1].Value), r.sharedMaterials.Length).ToArray();
            }
            // Unity builds LODGroups from _LOD0/_LOD1/_LOD2 siblings on import; build one per parent only if it did not.
            foreach (var parent in go.GetComponentsInChildren<Renderer>(true).Where(r => r.name.EndsWith("_LOD0")).Select(r => r.transform.parent).Distinct().ToArray())
            {
                if (parent.GetComponentsInParent<LODGroup>(true).Any(g => g.GetLODs().Any(l => l.renderers.Any(x => x && x.transform.parent == parent)))) continue;
                float[] cut = { .25f, .08f, .015f };
                var kids = parent.Cast<Transform>().Select(t => t.GetComponent<Renderer>()).Where(r => r).ToArray();
                parent.gameObject.AddComponent<LODGroup>().SetLODs(Enumerable.Range(0, 3).Select(i => new LOD(cut[i], kids.Where(r => r.name.EndsWith("_LOD" + i)).ToArray())).ToArray());
            }
            foreach (var col in go.GetComponentsInChildren<MeshFilter>(true).Where(m => m.name.StartsWith(id + "_Collision")))
                if (col.GetComponent<MeshCollider>() == null) col.gameObject.AddComponent<MeshCollider>().sharedMesh = col.sharedMesh;
            Physics.SyncTransforms();
            return go;
        }

        // the standard tier: every mesh whose name holds "_Detail_" is switched off
        static void Detail(GameObject go, bool on) { foreach (var r in go.GetComponentsInChildren<Renderer>(true).Where(r => r.name.Contains("_Detail_"))) r.enabled = on; }

        static Transform Node(GameObject go, string name) => go.GetComponentsInChildren<Transform>(true).FirstOrDefault(t => t.name == name);
        static Renderer[] Level(GameObject go, int i, bool detail = true) =>
            go.GetComponentsInChildren<Renderer>(true).Where(r => r.name.EndsWith("_LOD" + i) && (detail || !r.name.Contains("_Detail_"))).ToArray();
        static int Tris(IEnumerable<Renderer> rs) => rs.Sum(r => { var m = r.GetComponent<MeshFilter>().sharedMesh; return Enumerable.Range(0, m.subMeshCount).Sum(s => (int)m.GetIndexCount(s)) / 3; });
        static Bounds Box(IEnumerable<Renderer> rs) { var a = rs.ToArray(); var b = a[0].bounds; foreach (var r in a) b.Encapsulate(r.bounds); return b; }

        // ------------------------------------------------------------------ checks
        static void Inspect(string id, Info info)
        {
            var go = Place(id, Vector3.zero, 0);
            var lod0 = Level(go, 0); var b = Box(lod0); var body = Box(Level(go, 0, false));
            bool rooted = Node(go, id + "_GroundOrigin") != null || lod0.All(r => r.transform.IsChildOf(go.transform));
            Check(rooted, $"{id}: {id}_GroundOrigin is the model root (Unity names it {go.name}); all LOD meshes hang under it");
            float[] d = info.dimensions_xyz_m, bd = info.body_dimensions_xyz_m;
            Check(Mathf.Abs(b.size.x - d[0]) < .02f && Mathf.Abs(b.size.z - d[1]) < .02f && Mathf.Abs(b.size.y - d[2]) < .02f,
                $"{id}: imported size {b.size.x:0.000} x {b.size.z:0.000} x {b.size.y:0.000} m matches model_info {d[0]} x {d[1]} x {d[2]}");
            float measured = info.target_axis == "z" ? body.size.y : body.size.x, listed = info.target_axis == "z" ? bd[2] : bd[0];
            Check(Mathf.Abs(measured - info.target_m) < .015f && Mathf.Abs(measured - listed) < .01f,
                $"{id}: body {body.size.x:0.000} x {body.size.z:0.000} x {body.size.y:0.000} m, {(info.target_axis == "z" ? "height" : "width")} within 1.5 cm of the work pack's {info.target_m} m");
            Check(Mathf.Abs(body.min.y) < .005f, $"{id}: base at y = {body.min.y:0.000} (origin on the ground)");
            var tris = Enumerable.Range(0, 3).Select(i => Tris(Level(go, i))).ToArray();
            Check(Enumerable.Range(0, 3).All(i => Mathf.Abs(tris[i] - info.triangles_total[i]) <= info.triangles_total[i] * .01f),
                $"{id}: triangles LOD0/1/2 = {tris[0]} / {tris[1]} / {tris[2]} ({100f * tris[1] / tris[0]:0}% / {100f * tris[2] / tris[0]:0}%), model_info {string.Join(" / ", info.triangles_total)}");
            var groups = go.GetComponentsInChildren<LODGroup>(true);
            int inGroups = groups.Sum(g => g.GetLODs().Length == 3 ? g.GetLODs()[0].renderers.Length : 0);
            Check(groups.Length > 0 && groups.All(g => g.GetLODs().Length == 3) && inGroups == lod0.Length,
                $"{id}: {groups.Length} LODGroup(s) with 3 levels covering all {lod0.Length} LOD0 renderers");
            // quality tiers §4: minTier + detailObjects in model_info, and the named Detail_* meshes exist for every LOD
            var tier = Tier.ContainsKey(id) ? Tier[id] : Tier[id.Substring(0, 4)];
            Check(info.minTier == tier, $"{id}: minTier = {info.minTier} (work pack: {tier})");
            var missing = info.detailMeshes.Where(n => Node(go, n) == null).ToArray();
            Check((info.detailObjects.Length > 0 || NoDetail.Contains(id)) && missing.Length == 0 && info.detailObjects.All(g => g.StartsWith("Detail_")),
                $"{id}: detailObjects {string.Join(", ", info.detailObjects)} → {info.detailMeshes.Length} meshes present{(missing.Length > 0 ? ", missing " + string.Join(", ", missing) : "")}");
            Detail(go, false);
            int shown = Level(go, 0).Count(r => r.enabled);
            Check(shown >= 1 && Level(go, 0).Where(r => r.enabled).All(r => !r.name.Contains("_Detail_")), $"{id}: standard tier (Detail_* off) still shows {shown} body mesh(es) per LOD");
            Detail(go, true);
            var col = Node(go, id + "_Collision")?.GetComponent<MeshCollider>();
            if (tier != "standard" || NoCollision.Contains(id))
            {
                Check(col == null && go.GetComponentsInChildren<Collider>(true).Length == 0, tier != "standard" ? $"{id}: no collider (minTier {tier}: hidden on the standard tier, so it must not block the way there)" : $"{id}: no collider (the work pack gives this one no _Collision)");
                UnityEngine.Object.DestroyImmediate(go); return;
            }
            Check(col != null && col.sharedMesh.triangles.Length > 0, $"{id}: {id}_Collision imported as MeshCollider ({(col ? col.sharedMesh.triangles.Length / 3 : 0)} triangles), render hidden");
            if (col != null)
            {
                var cb = col.bounds;
                Check(Mathf.Abs(cb.size.x - body.size.x) < .03f && Mathf.Abs(cb.size.z - body.size.z) < .03f && Mathf.Abs(cb.size.y - body.size.y) < .03f,
                    $"{id}: collision box {cb.size.x:0.00} x {cb.size.z:0.00} x {cb.size.y:0.00} m fits the body");
                // a 1.75 m player (r 0.3) walking at the crate from the front stops on it
                var from = new Vector3(0, .9f, -2f);
                bool blocked = Physics.CapsuleCast(from + Vector3.down * .6f, from + Vector3.up * .55f, .3f, Vector3.forward, out var h, 4f) && h.collider == col;
                Check(blocked, $"{id}: a player capsule walking in from the front is stopped by it ({(blocked ? $"at {h.distance:0.00} m" : "not blocked")})");
            }
            UnityEngine.Object.DestroyImmediate(go);
        }

        // ------------------------------------------------------------------ renders
        static Camera cam; static RenderTexture target; static Light sun;
        static Material groundMat, rulerMat;

        static void Shots()
        {
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene);
            sun = new GameObject("Sun").AddComponent<Light>(); sun.type = LightType.Directional; sun.shadows = LightShadows.Soft;
            var ground = GameObject.CreatePrimitive(PrimitiveType.Plane); ground.transform.localScale = Vector3.one * 8;
            groundMat = Flat("ground", new Color(.40f, .38f, .33f)); ground.GetComponent<Renderer>().sharedMaterial = groundMat;
            rulerMat = Flat("ruler", new Color(.30f, .42f, .55f));
            cam = new GameObject("Review Camera").AddComponent<Camera>(); cam.nearClipPlane = .02f; cam.farClipPlane = 300;
            UnityEngine.Rendering.Universal.CameraExtensions.GetUniversalAdditionalCameraData(cam).renderPostProcessing = true;
            target = new RenderTexture(1280, 960, 24) { antiAliasing = 4 }; cam.targetTexture = target;
            Day();
            var front = Vector3.back; var side = Vector3.right; var tq = (front - side).normalized + Vector3.up * .55f;
            foreach (var id in Ids)   // four views with the 1.75 m figure, LOD0/1/2, and the standard tier (LOD1, Detail_* off)
            {
                var go = Place(id, Vector3.zero, 0); var b = Box(Level(go, 0));
                var ruler = Ruler(new Vector3(b.max.x + .45f, 0, 0));
                var all = b; all.Encapsulate(ruler.GetComponent<Renderer>().bounds);
                foreach (var (view, dir) in new[] { ("front", front), ("side", side), ("back", -front), ("threequarter", tq) })
                    Frame($"{id}/{id}-{view}", all, dir);
                UnityEngine.Object.DestroyImmediate(ruler);
                for (int i = 0; i < 3; i++) { foreach (var g in go.GetComponentsInChildren<LODGroup>()) g.ForceLOD(i); Frame($"{id}/{id}-lod{i}", b, tq); }
                foreach (var g in go.GetComponentsInChildren<LODGroup>()) g.ForceLOD(1);
                Detail(go, false); Frame($"{id}/{id}-standard-tier-lod1-nodetail", b, tq); Detail(go, true);
                foreach (var g in go.GetComponentsInChildren<LODGroup>()) g.ForceLOD(-1);
                UnityEngine.Object.DestroyImmediate(go);
            }
            // the two posts together
            var posts = new[] { Place("BM02_01", new Vector3(-.3f, 0, 0), 0), Place("BM02_02", new Vector3(.3f, 0, 0), 0) };
            var pb = Box(posts.SelectMany(g => Level(g, 0)));
            Frame("BM02-set-front", pb, front, 1.1f); Frame("BM02-set-threequarter", pb, tq, 1.1f);
            foreach (var g in posts) UnityEngine.Object.DestroyImmediate(g);
            // the three jars together
            var jars = new[] { Place("BM03_01", new Vector3(-.75f, 0, 0), 0), Place("BM03_02", new Vector3(-.2f, 0, 0), 0), Place("BM03_03", new Vector3(.45f, 0, 0), 0) };
            var jb = Box(jars.SelectMany(g => Level(g, 0)));
            Frame("BM03-set-front", jb, front, 1.1f); Frame("BM03-set-threequarter", jb, tq, 1.1f);
            foreach (var g in jars) UnityEngine.Object.DestroyImmediate(g);
            // the four stones together
            var stones = new[] { Place("BM04_01", new Vector3(-.9f, 0, 0), 0), Place("BM04_02", new Vector3(.55f, 0, -.1f), 0), Place("BM04_03", new Vector3(1.55f, 0, .05f), 0), Place("BM04_04", new Vector3(2.25f, 0, -.1f), 0) };
            var rb = Box(stones.SelectMany(g => Level(g, 0)));
            Frame("BM04-set-front", rb, front, 1.1f); Frame("BM04-set-threequarter", rb, tq, 1.1f);
            foreach (var g in stones) UnityEngine.Object.DestroyImmediate(g);
            // the table with its two stools, as in the reference sheet
            var rest = new[] { Place("BM05_02", new Vector3(-.8f, 0, 0), 0), Place("BM05_01", Vector3.zero, 0), Place("BM05_03", new Vector3(.8f, 0, 0), 0) };
            var tb = Box(rest.SelectMany(g => Level(g, 0)));
            Frame("BM05-set-front", tb, front, 1.1f); Frame("BM05-set-threequarter", tb, tq, 1.1f);
            foreach (var g in rest) UnityEngine.Object.DestroyImmediate(g);
            foreach (var (tag, ids, xs, pad) in new[] {
                ("BM06-set", new[] { "BM06_01", "BM06_02", "BM06_03", "BM06_04" }, new[] { -1.9f, -.95f, .25f, 1.6f }, 1.1f),
                ("BM07-set", new[] { "BM07_01", "BM04_03" }, new[] { 0f, 1.2f }, 1.15f),
                ("BM08-set", new[] { "BM08_01", "BM08_02" }, new[] { -.85f, .75f }, 1.15f),
                ("BM09-set", new[] { "BM09_01", "BM09_02" }, new[] { -.4f, .55f }, 1.15f) })
            {
                var gs = ids.Select((k, i) => Place(k, new Vector3(xs[i], 0, 0), 0)).ToArray();
                var bb = Box(gs.SelectMany(g => Level(g, 0)));
                Frame(tag + "-front", bb, front, pad); Frame(tag + "-threequarter", bb, tq, pad);
                foreach (var g in gs) UnityEngine.Object.DestroyImmediate(g);
            }
            // the three crates together, as in the reference sheet
            var set = new[] { Place("BM01_01", new Vector3(-1.35f, 0, 0), 0), Place("BM01_02", new Vector3(-.55f, 0, 0), 0), Place("BM01_03", new Vector3(.55f, 0, 0), 0) };
            var sb = Box(set.SelectMany(g => Level(g, 0)));
            Frame("BM01-set-front", sb, front, 1.05f); Frame("BM01-set-threequarter", sb, tq, 1.05f);
            foreach (var g in set) UnityEngine.Object.DestroyImmediate(g);
            Report.Add("INFO renders written to art/previews/modelling-basics-c/unity");
        }

        static void Day()
        {
            sun.transform.rotation = Quaternion.Euler(38, -40, 0); sun.color = new Color(1, .86f, .66f); sun.intensity = 1.7f;
            RenderSettings.ambientMode = AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = new Color(.52f, .60f, .74f); RenderSettings.ambientEquatorColor = new Color(.50f, .50f, .48f); RenderSettings.ambientGroundColor = new Color(.30f, .27f, .22f);
            cam.clearFlags = CameraClearFlags.SolidColor; cam.backgroundColor = new Color(.62f, .72f, .86f);
        }

        static GameObject Ruler(Vector3 at)   // 1.75 m figure
        {
            var r = GameObject.CreatePrimitive(PrimitiveType.Capsule);
            UnityEngine.Object.DestroyImmediate(r.GetComponent<Collider>());
            r.transform.position = at + Vector3.up * .875f; r.transform.localScale = new Vector3(.42f, .875f, .42f);
            r.GetComponent<Renderer>().sharedMaterial = rulerMat;
            return r;
        }

        static void Frame(string file, Bounds b, Vector3 dir, float pad = 1.25f)
        {
            cam.fieldOfView = 30;
            float radius = b.extents.magnitude * pad;
            float dist = radius / Mathf.Sin(cam.fieldOfView * .5f * Mathf.Deg2Rad);
            Shot(file, b.center + dir.normalized * dist, b.center, 30);
        }

        static void Shot(string file, Vector3 from, Vector3 at, float fov)
        {
            cam.fieldOfView = fov; cam.transform.position = from; cam.transform.LookAt(at); cam.Render();
            RenderTexture.active = target;
            var image = new Texture2D(target.width, target.height, TextureFormat.RGB24, false);
            image.ReadPixels(new Rect(0, 0, target.width, target.height), 0, 0); image.Apply();
            var path = Path.Combine(Out, file + ".png"); Directory.CreateDirectory(Path.GetDirectoryName(path));
            File.WriteAllBytes(path, image.EncodeToPNG());
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
