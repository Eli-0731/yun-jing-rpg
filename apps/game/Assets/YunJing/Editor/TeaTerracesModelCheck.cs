using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace YunJing.Editor
{
    // Work pack B-48h, first batch (TE01 terraces, TE02 tea bushes, TE03 stair / path / stepping stones).
    // Imports art/exports/tea-terraces-b into a gitignored folder, checks every model against its model_info.json, then lays out
    // art/exports/tea-terraces-b/assembly/farm-assembly.json and walks a 1.75 m CharacterController through it (paths, joints,
    // all eight stairs, both ends, the breaches, two bends), measures the joints by ray, and takes URP captures.
    // Writes artifacts/tea-terraces-unity/. Run with -executeMethod YunJing.Editor.TeaTerracesModelCheck.Run
    // Scripted walking is an aid only: it does not replace a person walking it with keyboard and mouse.
    public static class TeaTerracesModelCheck
    {
        const string Root = "Assets/YunJing/Generated/TeaTerracesB";
        const int SeamLayer = 30;
        static string Repo => Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", ".."));
        static string Exports => Path.Combine(Repo, "art", "exports", "tea-terraces-b");
        static string Out => Path.Combine(Repo, "artifacts", "tea-terraces-unity");
        static readonly string[] Ids = { "TE01_StraightA", "TE01_StraightB", "TE01_InnerBend", "TE01_OuterBend", "TE01_End", "TE01_Broken",
            "TE02_Round", "TE02_Wide", "TE02_Tall", "TE03_Stair", "TE03_Path", "TE03_Stepping" };
        static readonly List<string> Report = new List<string>();
        static int failed;
        static CharacterController cc;

        [Serializable] class ModelInfo { public float[] dimensions_m, bounds_min_m, bounds_max_m, size_limit_m; public string minTier; public LodTotals lod_totals; }
        [Serializable] class LodTotals { public int LOD0, LOD1, LOD2; }
        [Serializable] class Placement { public string id; public float[] position_m; public float rotation_z_deg; public bool mirror_x; public int row; }
        [Serializable] class Assembly { public Placement[] pieces; public int rows; }

        static void Check(bool ok, string what) { Report.Add((ok ? "PASS " : "FAIL ") + what); if (!ok) failed++; }
        // Blender (x, y, z) -> Unity (x, z, y)
        static Vector3 U(float x, float y, float z) => new Vector3(x, z, y);
        static float Front(int row) => -18f + 4 * row;

        static void UsePipeline()
        {
            var pipeline = AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>("Assets/YunJing/Generated/URP.asset");
            if (pipeline == null) { ProjectBuilder.Generate(); pipeline = AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>("Assets/YunJing/Generated/URP.asset"); }
            if (GraphicsSettings.defaultRenderPipeline != pipeline) GraphicsSettings.defaultRenderPipeline = pipeline;
            if (QualitySettings.renderPipeline != pipeline) QualitySettings.renderPipeline = pipeline;
            pipeline.shadowDistance = 60;
        }

        public static void Run()
        {
            Report.Clear(); failed = 0;
            UsePipeline();
            if (Directory.Exists(Out)) Directory.Delete(Out, true);
            Directory.CreateDirectory(Out);
            foreach (var id in Ids) Copy(id);
            AssetDatabase.Refresh();
            foreach (var id in Ids) Configure(id);
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            Lighting();
            // each model on its own, far from the assembly
            var single = new Dictionary<string, GameObject>();
            for (int i = 0; i < Ids.Length; i++) { single[Ids[i]] = Place(Ids[i], new Vector3(200 + i % 4 * 16, 0, 200 + i / 4 * 16), 0, false); Verify(Ids[i], single[Ids[i]]); }
            foreach (var id in Ids.Where(i => i.StartsWith("TE02"))) Wind(id, single[id]);
            foreach (var id in Ids) Sockets(id, single[id]);
            // the 40 x 40 m sample
            var asm = JsonUtility.FromJson<Assembly>(File.ReadAllText(Path.Combine(Exports, "assembly", "farm-assembly.json")));
            var placed = new List<(Placement p, GameObject go)>();
            foreach (var p in asm.pieces) placed.Add((p, Place(p.id, U(p.position_m[0], p.position_m[1], p.position_m[2]), p.rotation_z_deg, p.mirror_x)));
            Report.Add($"INFO assembly: {placed.Count} pieces from farm-assembly.json");
            var ground = GameObject.CreatePrimitive(PrimitiveType.Plane); ground.name = "Placeholder_Ground"; ground.transform.localScale = new Vector3(30, 1, 30); ground.transform.position = new Vector3(0, 0, -40);
            ground.GetComponent<Renderer>().sharedMaterial = GroundMat();
            // bends, joined to straights away from the sample
            var bend = new List<GameObject> {
                Place("TE01_StraightA", U(100, 0, 0), 0, false), Place("TE01_OuterBend", U(108, 2, 0), 0, false),
                Place("TE01_StraightB", U(100, -30, 0), 0, false), Place("TE01_InnerBend", U(108, -32, 0), 0, false) };
            Physics.SyncTransforms();
            Seams(placed, asm.rows);
            Walks(asm, placed);
            Capture(placed, single, bend);
            File.WriteAllText(Path.Combine(Out, "unity-verify-report.txt"), string.Join("\n", Report) + $"\n\nUnity {Application.unityVersion}; failed checks: {failed}; walking is a scripted CharacterController, not a person\n");
            Debug.Log("TEA_TERRACES_" + (failed == 0 ? "PASS" : "FAIL") + "\n" + string.Join("\n", Report));
            if (failed > 0 && Application.isBatchMode) EditorApplication.Exit(1);
        }

        static void Copy(string id)
        {
            var src = Path.Combine(Exports, id); var dst = Path.Combine(Repo, "apps", "game", Root, id);
            if (!Directory.Exists(src)) throw new DirectoryNotFoundException(src);
            Directory.CreateDirectory(Path.Combine(dst, "Textures"));
            foreach (var file in Directory.GetFiles(src, "*.fbx").Concat(Directory.GetFiles(Path.Combine(src, "Textures"), "*.png")))
                File.Copy(file, Path.Combine(dst, file.Substring(src.Length + 1)), true);
        }

        static void Configure(string id)
        {
            var importer = AssetImporter.GetAtPath($"{Root}/{id}/{id}_v001.fbx") as ModelImporter;
            if (importer == null) throw new FileNotFoundException("FBX not imported", id);
            importer.bakeAxisConversion = true; importer.materialImportMode = ModelImporterMaterialImportMode.None; importer.isReadable = true;
            importer.importAnimation = false; importer.importCameras = false; importer.importLights = false; importer.addCollider = false;
            importer.importNormals = ModelImporterNormals.Import;
            importer.SaveAndReimport();
            foreach (var tex in Directory.GetFiles(Path.Combine(Repo, "apps", "game", Root, id, "Textures"), "*.png"))
            {
                var path = $"{Root}/{id}/Textures/{Path.GetFileName(tex)}";
                var ti = AssetImporter.GetAtPath(path) as TextureImporter; if (ti == null) continue;
                bool normal = path.EndsWith("_Normal.png");
                bool data = path.EndsWith("_MetallicSmoothness.png") || path.EndsWith("_Roughness.png") || path.EndsWith("_Metallic.png");
                ti.textureType = normal ? TextureImporterType.NormalMap : TextureImporterType.Default;
                ti.sRGBTexture = !normal && !data; ti.maxTextureSize = 4096;
                if (path.EndsWith("TE02_LeafCards_BaseColor.png")) { ti.alphaSource = TextureImporterAlphaSource.FromInput; ti.alphaIsTransparency = true; ti.mipMapsPreserveCoverage = true; ti.alphaTestReferenceValue = .5f; }
                ti.SaveAndReimport();
            }
        }

        static Texture2D Tex(string id, string file) => AssetDatabase.LoadAssetAtPath<Texture2D>($"{Root}/{id}/Textures/{file}");

        static Material Mat(string id)
        {
            var path = $"{Root}/{id}.mat";
            var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (mat == null) { mat = new Material(Shader.Find("Universal Render Pipeline/Lit")); AssetDatabase.CreateAsset(mat, path); }
            mat.SetTexture("_BaseMap", Tex(id, id + "_BaseColor.png")); mat.SetColor("_BaseColor", Color.white);
            mat.SetTexture("_BumpMap", Tex(id, id + "_Normal.png")); mat.EnableKeyword("_NORMALMAP");
            mat.SetTexture("_MetallicGlossMap", Tex(id, id + "_MetallicSmoothness.png")); mat.EnableKeyword("_METALLICSPECGLOSSMAP"); mat.SetFloat("_Smoothness", 1);
            EditorUtility.SetDirty(mat); return mat;
        }

        // TE02 leaf cards: URP Lit, alpha clipped at 0.5, both faces drawn
        static Material LeafMat(string id)
        {
            var path = $"{Root}/{id}_LeafCards.mat";
            var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (mat == null) { mat = new Material(Shader.Find("Universal Render Pipeline/Lit")); AssetDatabase.CreateAsset(mat, path); }
            mat.SetTexture("_BaseMap", Tex(id, "TE02_LeafCards_BaseColor.png")); mat.SetColor("_BaseColor", Color.white);
            mat.SetTexture("_BumpMap", Tex(id, "TE02_LeafCards_Normal.png")); mat.EnableKeyword("_NORMALMAP");
            mat.SetFloat("_AlphaClip", 1); mat.SetFloat("_Cutoff", .5f); mat.EnableKeyword("_ALPHATEST_ON");
            mat.SetFloat("_Cull", (float)CullMode.Off); mat.SetFloat("_Smoothness", .3f); mat.SetFloat("_Metallic", 0);
            mat.SetOverrideTag("RenderType", "TransparentCutout"); mat.renderQueue = (int)RenderQueue.AlphaTest;
            EditorUtility.SetDirty(mat); return mat;
        }

        static Material groundMat;
        static Material GroundMat()
        {
            if (groundMat != null) return groundMat;
            groundMat = new Material(Shader.Find("Universal Render Pipeline/Lit")); groundMat.SetColor("_BaseColor", new Color(.2f, .15f, .1f)); groundMat.SetFloat("_Smoothness", .05f);
            return groundMat;
        }

        static GameObject Place(string id, Vector3 position, float rotZ, bool mirror)
        {
            var go = (GameObject)PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>($"{Root}/{id}/{id}_v001.fbx"));
            PrefabUtility.UnpackPrefabInstance(go, PrefabUnpackMode.Completely, InteractionMode.AutomatedAction);
            go.transform.position = position; go.transform.rotation = Quaternion.Euler(0, -rotZ, 0);
            if (mirror) go.transform.localScale = new Vector3(-1, 1, 1);
            var mat = Mat(id); var leaf = id.StartsWith("TE02") ? LeafMat(id) : null;
            foreach (var r in go.GetComponentsInChildren<Renderer>(true))
            {
                if (r.name == id + "_Collision") { r.enabled = false; continue; }
                var m = r.name.Contains("_Leaves_LOD") ? leaf : mat;
                r.sharedMaterials = Enumerable.Repeat(m, r.sharedMaterials.Length).ToArray();
            }
            if (go.GetComponent<LODGroup>() == null)
            {
                float[] cut = id.StartsWith("TE01") ? new[] { .2f, .06f, .01f } : new[] { .12f, .04f, .008f };
                go.AddComponent<LODGroup>().SetLODs(Enumerable.Range(0, 3).Select(i => new LOD(cut[i], go.GetComponentsInChildren<Renderer>(true).Where(r => r.name.EndsWith("_LOD" + i)).ToArray())).ToArray());
            }
            var col = go.GetComponentsInChildren<MeshFilter>(true).FirstOrDefault(m => m.name == id + "_Collision");
            if (col != null) col.gameObject.AddComponent<MeshCollider>().sharedMesh = col.sharedMesh;
            return go;
        }

        static Bounds LodBounds(GameObject go, string suffix = "_LOD0")
        {
            var rs = go.GetComponentsInChildren<Renderer>(true).Where(r => r.name.EndsWith(suffix)).ToArray();
            var b = rs[0].bounds; foreach (var r in rs) b.Encapsulate(r.bounds); return b;
        }

        static void Verify(string id, GameObject go)
        {
            var info = JsonUtility.FromJson<ModelInfo>(File.ReadAllText(Path.Combine(Exports, id, "model_info.json")));
            var b = LodBounds(go); var o = go.transform.position;
            float[] want = info.dimensions_m; Vector3 size = b.size;
            float dx = Mathf.Abs(size.x - want[0]), dy = Mathf.Abs(size.z - want[1]), dz = Mathf.Abs(size.y - want[2]);
            Check(dx < .002f && dy < .002f && dz < .002f, $"{id}: imported size {size.x:F3} x {size.z:F3} x {size.y:F3} m matches model_info (max error {Mathf.Max(dx, dy, dz) * 1000:F1} mm)");
            var lo = b.min - o; var hi = b.max - o;
            float e = Mathf.Max(Mathf.Abs(lo.x - info.bounds_min_m[0]), Mathf.Abs(lo.z - info.bounds_min_m[1]), Mathf.Abs(lo.y - info.bounds_min_m[2]),
                                Mathf.Abs(hi.x - info.bounds_max_m[0]), Mathf.Abs(hi.z - info.bounds_max_m[1]), Mathf.Abs(hi.y - info.bounds_max_m[2]));
            Check(e < .002f, $"{id}: bounds about the origin {lo.x:F3}..{hi.x:F3}, {lo.z:F3}..{hi.z:F3}, {lo.y:F3}..{hi.y:F3} m equal model_info (origin as designed, max error {e * 1000:F1} mm)");
            Check(Mathf.Abs(lo.y) < .002f, $"{id}: base on the origin height (min y {lo.y:F4})");
            Report.Add($"INFO {id}: minTier {info.minTier}");
            var lod = go.GetComponent<LODGroup>();
            Check(lod != null && lod.GetLODs().Length == 3, $"{id}: LODGroup with 3 levels");
            int tri(string s) => go.GetComponentsInChildren<MeshFilter>(true).Where(m => m.name.EndsWith(s)).Sum(m => m.sharedMesh.triangles.Length / 3);
            Check(tri("_LOD0") == info.lod_totals.LOD0 && tri("_LOD1") == info.lod_totals.LOD1 && tri("_LOD2") == info.lod_totals.LOD2,
                  $"{id}: imported LOD triangles {tri("_LOD0")}/{tri("_LOD1")}/{tri("_LOD2")} equal model_info {info.lod_totals.LOD0}/{info.lod_totals.LOD1}/{info.lod_totals.LOD2}");
            var col = go.GetComponentsInChildren<MeshCollider>(true).FirstOrDefault(c => c.name == id + "_Collision");
            Check(col != null && col.sharedMesh.triangles.Length > 0, $"{id}: {id}_Collision imported as MeshCollider ({(col ? col.sharedMesh.triangles.Length / 3 : 0)} triangles), renderer hidden");
            if (col != null)
            {
                var box = col.bounds; var all = b; all.Expand(.1f);
                Check(all.Contains(box.min) && all.Contains(box.max), $"{id}: the collider stays on the model");
            }
            Check(!go.GetComponentsInChildren<Renderer>(true).Any(r => r.enabled && r.sharedMaterial != null && r.sharedMaterial.shader.name.Contains("Error")), $"{id}: no error shaders");
        }

        static void Wind(string id, GameObject go)
        {
            foreach (var mf in go.GetComponentsInChildren<MeshFilter>(true).Where(m => m.name.Contains("_LOD")))
            {
                var c = mf.sharedMesh.colors;
                Check(c.Length == mf.sharedMesh.vertexCount, $"{mf.name}: vertex colour Wind on every vertex ({c.Length} of {mf.sharedMesh.vertexCount})");
                if (c.Length == 0) continue;
                Report.Add($"INFO {mf.name}: wind R {c.Min(x => x.r):F2}..{c.Max(x => x.r):F2}, phase G {c.Min(x => x.g):F2}..{c.Max(x => x.g):F2}, height B {c.Min(x => x.b):F2}..{c.Max(x => x.b):F2}");
            }
            var root = go.GetComponentsInChildren<MeshFilter>(true).First(m => m.name == id + "_LOD0").sharedMesh.colors;
            var leaves = go.GetComponentsInChildren<MeshFilter>(true).First(m => m.name == id + "_Leaves_LOD0").sharedMesh.colors;
            Check(root.Min(x => x.r) < .02f && leaves.Max(x => x.r) > .95f, $"{id}: wind weight 0 at the root, 1 on the outer leaves (linear, not sRGB-shifted)");
            var leafMat = go.GetComponentsInChildren<Renderer>(true).First(r => r.name == id + "_Leaves_LOD0").sharedMaterial;
            Check(leafMat.IsKeywordEnabled("_ALPHATEST_ON") && leafMat.GetFloat("_Cull") == 0, $"{id}: leaf cards alpha clipped, both faces");
        }

        static void Sockets(string id, GameObject go)
        {
            var info = File.ReadAllText(Path.Combine(Exports, id, "model_info.json"));
            int n = 0, good = 0;
            foreach (var t in go.GetComponentsInChildren<Transform>(true).Where(t => t.name.StartsWith("Socket_")))
            {
                n++;
                var key = "\"" + t.name.Split('.')[0] + "\": [";
                int at = info.IndexOf(key, info.IndexOf("sockets_blender_xyz")); if (at < 0) continue;
                var nums = info.Substring(at + key.Length, info.IndexOf(']', at) - at - key.Length).Split(',').Select(s => float.Parse(s.Trim(), System.Globalization.CultureInfo.InvariantCulture)).ToArray();
                if ((t.position - go.transform.position - U(nums[0], nums[1], nums[2])).magnitude < .002f) good++;
            }
            if (n > 0) Check(good == n, $"{id}: {good} of {n} sockets where model_info puts them");
        }

        // The joints: rays straight down onto the LOD0 render meshes just either side of every connector plane; heights must agree within 2 mm and nothing may fall through.
        static void Seams(List<(Placement p, GameObject go)> placed, int rows)
        {
            var added = new List<MeshCollider>();
            foreach (var (p, go) in placed.Where(x => x.p.id.StartsWith("TE01")))
                foreach (var mf in go.GetComponentsInChildren<MeshFilter>(true).Where(m => m.name == p.id + "_LOD0"))
                {
                    var c = mf.gameObject.AddComponent<MeshCollider>(); c.sharedMesh = mf.sharedMesh; mf.gameObject.layer = SeamLayer; added.Add(c);
                }
            // the bend clusters too
            foreach (var go in UnityEngine.Object.FindObjectsByType<MeshFilter>(FindObjectsSortMode.None).Where(m => (m.name == "TE01_OuterBend_LOD0" || m.name == "TE01_InnerBend_LOD0" || ((m.name == "TE01_StraightA_LOD0" || m.name == "TE01_StraightB_LOD0") && m.transform.position.x > 50)) && m.GetComponent<MeshCollider>() == null))
            { var c = go.gameObject.AddComponent<MeshCollider>(); c.sharedMesh = go.sharedMesh; go.gameObject.layer = SeamLayer; added.Add(c); }
            Physics.SyncTransforms();
            int mask = 1 << SeamLayer;
            float? Z(float x, float y) => Physics.Raycast(new Vector3(x, 30, y), Vector3.down, out var h, 60, mask) ? h.point.y : (float?)null;
            float worst = 0; int holes = 0, n = 0; var lines = new List<string>();
            void Joint(string what, float x, float y0, float soil)
            {
                for (float d = .8f; d <= 3.81f; d += .5f)
                {
                    float y = y0 + d; var a = Z(x - .003f, y); var b = Z(x + .003f, y); var m = Z(x, y); n++;
                    if (a == null || b == null || m == null) { holes++; lines.Add($"{what} d {d:F1}: hole"); continue; }
                    float diff = Mathf.Abs(a.Value - b.Value); worst = Mathf.Max(worst, diff);
                    if (diff > .002f || Mathf.Abs(m.Value - soil) > .03f) lines.Add($"{what} d {d:F1}: {a:F4} | {b:F4} (centre {m:F4})");
                }
            }
            for (int k = 0; k < rows; k++) foreach (var x in new[] { -12f, -4f, 4f, 12f }) Joint($"row {k} x {x}", x, Front(k), k + 1);
            Joint("straight to outer bend", 104, -2, 1); Joint("straight to inner bend", 104, -32, 1);
            Check(holes == 0 && worst <= .002f, $"joints: {n} ray pairs across {rows * 4 + 2} connector lines, largest step {worst * 1000:F2} mm (limit 2), {holes} holes");
            foreach (var l in lines.Take(30)) Report.Add("  " + l);
            foreach (var c in added) UnityEngine.Object.DestroyImmediate(c);
            foreach (var go in UnityEngine.Object.FindObjectsByType<MeshFilter>(FindObjectsSortMode.None).Where(m => m.gameObject.layer == SeamLayer)) go.gameObject.layer = 0;
            Physics.SyncTransforms();
        }

        struct WalkResult { public bool reached; public float low, high, fall, rise; public Vector3 end; public string touch; }

        static WalkResult Walk(string what, float expectLow, float expectHigh, params Vector3[] path) => Walk(what, expectLow, expectHigh, true, path);

        static WalkResult Walk(string what, float expectLow, float expectHigh, bool mustReach, params Vector3[] path)
        {
            cc.enabled = false; cc.transform.position = path[0] + Vector3.up * .9f; cc.enabled = true; Physics.SyncTransforms();
            for (int i = 0; i < 80; i++) cc.Move(Vector3.down * .05f);
            var r = new WalkResult { reached = true, low = cc.transform.position.y, high = cc.transform.position.y, touch = "none" };
            var trace = new List<string>(); var along = new List<Vector2>(); float run = 0; var last = cc.transform.position;
            for (int leg = 1; leg < path.Length && r.reached; leg++)
            {
                var goal = path[leg]; int steps = 0;
                while (true)
                {
                    var d = goal - cc.transform.position; d.y = 0;
                    if (d.magnitude < .12f) break;
                    if (++steps > 3000) { r.reached = false; break; }
                    var flags = cc.Move(d.normalized * .035f + Vector3.down * .06f); var p = cc.transform.position;
                    r.low = Mathf.Min(r.low, p.y); r.high = Mathf.Max(r.high, p.y);
                    run += new Vector2(p.x - last.x, p.z - last.z).magnitude; last = p; along.Add(new Vector2(run, p.y));
                    if (steps % 4 == 0) trace.Add($"[{p.x:F3},{p.y:F3},{p.z:F3},{(int)flags}]");
                }
            }
            r.end = cc.transform.position;
            // no falling and no climbing walls: within any 0.3 m of horizontal travel the feet may not drop more than 0.25 m or rise more than stepOffset (a riser is 0.167; a collapse bank reaches ~41 deg)
            for (int i = 0, j = 0; i < along.Count; i++)
            {
                while (j < along.Count && along[j].x - along[i].x <= .3f) j++;
                for (int k = i + 1; k < j; k++) { float dy = along[k].y - along[i].y; r.fall = Mathf.Max(r.fall, -dy); r.rise = Mathf.Max(r.rise, dy); }
            }
            File.WriteAllText(Path.Combine(Out, "walks", $"walk-{what.Replace(" ", "_").Replace(",", "").Replace("/", "-")}.json"),
                $"{{\"walk\":\"{what}\",\"reached\":{(r.reached ? "true" : "false")},\"feet_low\":{r.low:F4},\"feet_high\":{r.high:F4},\"radius\":{cc.radius},\"height\":{cc.height},\"stepOffset\":{cc.stepOffset},\"slopeLimit\":{cc.slopeLimit},\"largest_drop_per_0_3m\":{r.fall:F4},\"largest_rise_per_0_3m\":{r.rise:F4},\"trace\":[{string.Join(",", trace)}]}}");
            if (mustReach) Check(r.reached && r.low >= expectLow && r.high <= expectHigh && r.fall <= .25f && r.rise <= cc.stepOffset,
                $"walk {what}: {(r.reached ? "reached" : "STUCK at")} ({r.end.x:F2}, {r.end.y:F2}, {r.end.z:F2}), feet {r.low:F3}..{r.high:F3} m (expected {expectLow:F2}..{expectHigh:F2}), largest drop {r.fall:F3} / rise {r.rise:F3} m per 0.3 m (limits drop 0.25, rise = stepOffset {cc.stepOffset:F2})");
            return r;
        }

        static void Walks(Assembly asm, List<(Placement p, GameObject go)> placed)
        {
            Directory.CreateDirectory(Path.Combine(Out, "walks"));
            cc = new GameObject("WalkProbe", typeof(CharacterController)).GetComponent<CharacterController>();
            cc.height = 1.75f; cc.radius = .3f; cc.center = Vector3.up * .875f; cc.stepOffset = .3f; cc.slopeLimit = 45; cc.skinWidth = .02f;
            Vector3 P(float x, int row, float d) => U(x, Front(row) + d, 0);
            Vector3 At(float x, int row, float d) { var v = P(x, row, d); v.y = row + 1; return v; }
            // 1. along the path line of three rows, end to end across both inner joints (x -4 and 4) and the outer ones (x -12, 12)
            foreach (var row in new[] { 1, 4, 7 })
            {
                bool breach = asm.pieces.Any(p => p.row == row && p.id == "TE01_Broken");
                Walk($"row {row} along the path line x -13 to 13{(breach ? " (through the slumped breach)" : "")}", row + (breach ? .3f : .97f), row + 1.12f, At(-13, row, 1.15f), At(13, row, 1.15f));
            }
            // 2. between the path and the bushes, across a breach and its slumped bank
            Walk("row 3 at d 1.9 through the breach of the left Broken piece", 3 + .4f, 3 + 1.12f, At(-13, 3, 1.9f), At(-3, 3, 1.9f));
            // 3. the whole hill: every stair in turn, from row 0 to row 8
            var stairs = asm.pieces.Where(p => p.id == "TE03_Stair").OrderBy(p => p.row).ToArray();
            var route = new List<Vector3> { U(stairs[0].position_m[0] + 2, -21.4f, 0), U(stairs[0].position_m[0], -21.4f, 0) };
            foreach (var s in stairs) { if (s.row > 0) route.Add(At(s.position_m[0], s.row - 1, 1.15f)); route.Add(At(s.position_m[0], s.row, 1.15f)); }
            var climb = Walk($"front strip to row 8 up all {stairs.Length} stairs", -.03f, 9.12f, route.ToArray());
            Check(Mathf.Abs(climb.end.y - 9f) < .1f, $"the climb ends on row 8 soil ({climb.end.y:F2} m, soil 9.00)");
            foreach (var s in stairs.Skip(1).Take(3))
                Walk($"down the stair into row {s.row}", s.row - .03f, s.row + 1.12f, At(s.position_m[0], s.row, 1.2f), At(s.position_m[0], s.row - 1, .9f));
            // 4. the ends: row 0 runs down to the strip at both sides (the left one mirrored), row 5 runs down to row 4's level
            Walk("row 0 right End down to the ground", -.03f, 1.12f, At(13, 0, 2), U(21.5f, Front(0) + 2, 0));
            Walk("row 0 left End (mirrored) down to the ground", -.03f, 1.12f, At(-13, 0, 2), U(-21.5f, Front(0) + 2, 0));
            var e5 = Walk("row 5 right End to its low tip", 4.97f, 6.12f, At(13, 5, 2), new Vector3(19.7f, 0, Front(5) + 2));
            Check(e5.end.y < 5.15f, $"row 5 End tip comes down to {e5.end.y:F2} m (row 4 soil 5.00)");
            // 5. stepping stones on row 0, end to end
            foreach (var s in asm.pieces.Where(p => p.id == "TE03_Stepping"))
                Walk($"over the stepping stones at x {s.position_m[0]}", .97f, 1.15f, At(s.position_m[0] - 1.3f, 0, 1.15f), At(s.position_m[0] + 1.3f, 0, 1.15f));
            // 6. a bush stops the walker: from the path straight at the trunk
            var bush = asm.pieces.First(p => p.id.StartsWith("TE02") && p.row == 2);
            var bc = U(bush.position_m[0], bush.position_m[1], bush.position_m[2] + 0);
            var hit = Walk($"from the path into a {bush.id}", 2.97f, 3.12f, false, At(bush.position_m[0], 2, 1.15f), bc);
            var gap = Vector2.Distance(new Vector2(hit.end.x, hit.end.z), new Vector2(bc.x, bc.z));
            Check(!hit.reached && gap > .6f && gap < .8f && hit.high < 3.12f, $"{bush.id}: the walker stops {gap:F2} m from the trunk (collision radius 0.42 + capsule 0.30), feet never above {hit.high:F3} m");
            // 7. bends: along the tread centre line round both quarter circles, from the straight
            var outer = new List<Vector3> { U(97, 0, 1) }; var inner = new List<Vector3> { U(97, -30, 1) };
            for (int i = 0; i <= 9; i++)
            {
                float a = -Mathf.PI / 2 + i * Mathf.PI / 18; outer.Add(U(104 + 6 * Mathf.Cos(a), 6 + 6 * Mathf.Sin(a), 1));
                float b = Mathf.PI / 2 - i * Mathf.PI / 18; inner.Add(U(104 + 6 * Mathf.Cos(b), -36 + 6 * Mathf.Sin(b), 1));
            }
            Walk("straight into the outer bend and round it", .97f, 1.12f, outer.ToArray());
            Walk("straight into the inner bend and round it", .97f, 1.12f, inner.ToArray());
            UnityEngine.Object.DestroyImmediate(cc.gameObject);
        }

        static void Lighting()
        {
            RenderSettings.ambientMode = AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = new Color(.62f, .68f, .7f); RenderSettings.ambientEquatorColor = new Color(.45f, .44f, .38f); RenderSettings.ambientGroundColor = new Color(.2f, .18f, .14f);
            var sun = new GameObject("Sun").AddComponent<Light>(); sun.type = LightType.Directional; sun.intensity = 1.25f;
            sun.color = new Color(1, .96f, .88f); sun.transform.rotation = Quaternion.Euler(38, -30, 0); sun.shadows = LightShadows.Soft;
            var cam = new GameObject("Main Camera", typeof(Camera)).GetComponent<Camera>(); cam.tag = "MainCamera"; cam.nearClipPlane = .05f; cam.farClipPlane = 300;
            cam.clearFlags = CameraClearFlags.SolidColor; cam.backgroundColor = new Color(.74f, .82f, .84f);
            cam.GetUniversalAdditionalCameraData().renderPostProcessing = false;
        }

        static void Shot(string file, Vector3 target, Vector3 eye, float fov = 40)
        {
            var cam = Camera.main; var rt = new RenderTexture(1600, 900, 24, RenderTextureFormat.ARGB32) { antiAliasing = 4 };
            cam.transform.position = eye; cam.transform.LookAt(target); cam.fieldOfView = fov; cam.targetTexture = rt; cam.Render();
            RenderTexture.active = rt; var tex = new Texture2D(1600, 900, TextureFormat.RGB24, false); tex.ReadPixels(new Rect(0, 0, 1600, 900), 0, 0); tex.Apply();
            File.WriteAllBytes(Path.Combine(Out, file + ".png"), tex.EncodeToPNG()); UnityEngine.Object.DestroyImmediate(tex);
            RenderTexture.active = null; cam.targetTexture = null; rt.Release(); Report.Add("SHOT " + file);
        }

        static void Capture(List<(Placement p, GameObject go)> placed, Dictionary<string, GameObject> single, List<GameObject> bend)
        {
            foreach (var kv in single)
            {
                var b = LodBounds(kv.Value); float d = Mathf.Max(b.size.magnitude * 1.25f, 2.2f); var c = b.center;
                Shot(kv.Key + "_three_quarter", c, c + new Vector3(.7f, .45f, -.85f).normalized * d, 35);
                Shot(kv.Key + "_front", c, c + new Vector3(0, .12f, -1) * d, 35);
            }
            // the sample
            Shot("assembly_aerial", new Vector3(0, 3, -2), new Vector3(24, 34, -46), 45);
            Shot("assembly_walk_row2", At2(4, 2, 2.6f, 2.9f), At2(-11.5f, 2, 1.15f, 3 + 1.6f), 60);
            Shot("assembly_stairs_from_row1", At2(-1.5f, 3, 1f, 4.4f), At2(-6.5f, 1, 1.0f, 2 + 1.6f), 55);
            Shot("assembly_joint_x-4_row3_wall", U(-4, Front(3) + .1f, 3.5f), U(-3.2f, Front(3) - 2.2f, 3 + 1.5f), 50);
            Shot("assembly_left_end_mirrored", U(-16, Front(1) + 2, 1.6f), U(-23, Front(1) - 5, 4.5f), 50);
            Shot("assembly_breach_row1", U(2, Front(1) + 1, 1.6f), U(3.5f, Front(1) - 3.2f, 1 + 1.6f), 55);
            Shot("assembly_bushes_close", At2(-6, 4, 2.95f, 5.4f), At2(-8.5f, 4, .9f, 5 + 1.6f), 50);
            Shot("bends_outer", U(104, 2, 1), U(96, -10, 7), 50);
            Shot("bends_inner", U(104, -32, 1), U(96, -42, 7), 50);
            Flicker();
        }

        static Vector3 At2(float x, int row, float d, float h) => U(x, Front(row) + d, h);

        // A surface fighting another one flips colour and back as the camera turns a hair: count pixels that go A, B, A over three frames.
        static void Flicker()
        {
            const int W = 960, H = 540, Frames = 20;
            var cam = Camera.main; var rt = new RenderTexture(W, H, 24, RenderTextureFormat.ARGB32); var tex = new Texture2D(W, H, TextureFormat.RGB24, false);
            foreach (var (name, target, eye) in new[] { ("row 3 wall at the x -4 joint", U(-4, Front(3) + .1f, 3.5f), U(-3.2f, Front(3) - 2.2f, 4.5f)), ("stair into row 2", U(5.5f, Front(2) - 1, 2.4f), U(8, Front(2) - 4, 3.4f)), ("bush row 4", At2(-6, 4, 2.95f, 5.4f), At2(-8.5f, 4, .9f, 6.6f)) })
            {
                var look = new float[Frames][]; var off = eye - target;
                for (int i = 0; i < Frames; i++)
                {
                    cam.transform.position = target + Quaternion.Euler(0, i * .1f, 0) * off; cam.transform.LookAt(target); cam.fieldOfView = 45; cam.targetTexture = rt; cam.Render();
                    RenderTexture.active = rt; tex.ReadPixels(new Rect(0, 0, W, H), 0, 0); tex.Apply(); look[i] = tex.GetPixels().Select(c => c.r * .2126f + c.g * .7152f + c.b * .0722f).ToArray();
                }
                RenderTexture.active = null; cam.targetTexture = null; int worst = 0, all = 0;
                for (int i = 0; i + 2 < Frames; i++)
                {
                    int n = 0;
                    for (int k = 0; k < look[i].Length; k++) if (Mathf.Abs(look[i][k] - look[i + 1][k]) > .2f && Mathf.Abs(look[i][k] - look[i + 2][k]) < .05f) n++;
                    worst = Mathf.Max(worst, n); all += n;
                }
                Report.Add($"FLICKER {name}: A-B-A pixels per frame mean {all / (float)(Frames - 2):0.0}, worst {worst}, of {W * H}");
            }
            UnityEngine.Object.DestroyImmediate(tex); rt.Release();
        }
    }
}
