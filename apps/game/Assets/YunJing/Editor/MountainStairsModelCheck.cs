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
    // Work pack 2026-11-07, part 2 (SG01-SG04 mountain-city stairway), exported into art/exports/mountain-stairs-b.
    // Imports each model into a gitignored folder, checks it against its model_info.json (size, origin, LOD levels and triangles,
    // object and material counts, Detail_* objects, collider, shaders, socket empties), walks a 1.75 m CharacterController up
    // each stair flight on its collider, and takes URP captures beside a 1.75 m capsule.
    // Writes artifacts/mountain-stairs-unity/. Run with -executeMethod YunJing.Editor.MountainStairsModelCheck.Run
    // This is an editor batch check, not play in the game: nothing is placed in the main scene.
    public static class MountainStairsModelCheck
    {
        const string Root = "Assets/YunJing/Generated/MountainStairsB";
        static string Repo => Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", ".."));
        static string Exports => Path.Combine(Repo, "art", "exports", "mountain-stairs-b");
        static string Out => Path.Combine(Repo, "artifacts", "mountain-stairs-unity");
        // only the pieces that have been exported so far; the rest of the SG set is added when it exists
        static readonly string[] Wanted = { "SG01_StraightRun", "SG02_Landing", "SG03_RailStraight", "SG03_RailSloped", "SG03_PostCorner", "SG03_PostEnd", "SG04_RestShelter" };
        static readonly List<string> Report = new List<string>();
        static int failed;

        [Serializable] class Budget { public int triangles, objects, objects_without_detail, materials; }
        [Serializable] class BudgetPerLod { public Budget LOD0, LOD1, LOD2; }
        [Serializable] class LodTotals { public int LOD0, LOD1, LOD2; }
        [Serializable] class ModelInfo { public string version, minTier; public float[] dimensions_m, bounds_min_m, bounds_max_m; public float ground_z_m; public LodTotals lod_totals; public BudgetPerLod budget_per_lod; public string[] detailObjects; }

        static readonly Dictionary<string, ModelInfo> infos = new Dictionary<string, ModelInfo>();
        static ModelInfo Info(string id)
        {
            if (!infos.TryGetValue(id, out var i)) infos[id] = i = JsonUtility.FromJson<ModelInfo>(File.ReadAllText(Path.Combine(Exports, id, "model_info.json")));
            return i;
        }
        static string Fbx(string id) => $"{Root}/{id}/{id}_{Info(id).version}.fbx";
        static void Check(bool ok, string what) { Report.Add((ok ? "PASS " : "FAIL ") + what); if (!ok) failed++; }

        static void UsePipeline()
        {
            var pipeline = AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>("Assets/YunJing/Generated/URP.asset");
            if (pipeline == null) { ProjectBuilder.Generate(); pipeline = AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>("Assets/YunJing/Generated/URP.asset"); }
            if (GraphicsSettings.defaultRenderPipeline != pipeline) GraphicsSettings.defaultRenderPipeline = pipeline;
            if (QualitySettings.renderPipeline != pipeline) QualitySettings.renderPipeline = pipeline;
            pipeline.shadowDistance = 40;
        }

        public static void Run()
        {
            Report.Clear(); failed = 0; infos.Clear();
            UsePipeline();
            if (Directory.Exists(Out)) Directory.Delete(Out, true);
            Directory.CreateDirectory(Out);
            var ids = Wanted.Where(i => File.Exists(Path.Combine(Exports, i, "model_info.json"))).ToArray();
            Report.Add("INFO checked: " + string.Join(", ", ids.Select(i => $"{i} {Info(i).version}")) + "; not exported yet: " + string.Join(", ", Wanted.Except(ids)));
            foreach (var id in ids) Copy(id);
            AssetDatabase.Refresh();
            foreach (var id in ids) Configure(id);
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            Lighting();
            var ground = GameObject.CreatePrimitive(PrimitiveType.Plane); ground.name = "Placeholder_Ground"; ground.transform.localScale = new Vector3(60, 1, 20);       // 600 x 200 m: under every piece placed 30 m apart and the combo
            ground.transform.position = new Vector3(ids.Length * 15, -.001f, 0);
            var gm = new Material(Shader.Find("Universal Render Pipeline/Lit")); gm.SetColor("_BaseColor", new Color(.36f, .33f, .29f)); gm.SetFloat("_Smoothness", 0);
            gm.SetFloat("_SpecularHighlights", 0); gm.EnableKeyword("_SPECULARHIGHLIGHTS_OFF");
            gm.SetFloat("_EnvironmentReflections", 0); gm.EnableKeyword("_ENVIRONMENTREFLECTIONS_OFF");   // a matte placeholder floor, no sky glare
            ground.GetComponent<Renderer>().sharedMaterial = gm;
            for (int n = 0; n < ids.Length; n++)
            {
                var id = ids[n]; var at = new Vector3(n * 30, 0, 0);
                var go = Place(id, at); Verify(id, go); Sockets(id, go);
                if (id == "SG01_StraightRun") Walk(id, go);
                if (id == "SG02_Landing") WalkAcross(id, go);
                if (id == "SG04_RestShelter") WalkIn(id, go);
                if (id == "SG03_RailStraight") Blocks(id, go);
                var b = LodBounds(go);
                var person = Person(at + new Vector3(-(b.extents.x + .6f), 0, 0));
                var both = b; both.Encapsulate(person.GetComponent<Renderer>().bounds);   // frame the model and the 1.75 m capsule together
                float d = both.size.magnitude * 1.7f; var c = both.center;
                Shot(id + "_three_quarter", c, c + new Vector3(.75f, .35f, -.85f).normalized * d, 35);
                Shot(id + "_front", c, c + new Vector3(0, .1f, -1).normalized * d, 35);
                person.SetActive(false);
                var dc = b.center; float dd = Mathf.Max(b.size.magnitude * 1.3f, .9f);
                Shot(id + "_close", dc, dc + new Vector3(.6f, .55f, -.85f).normalized * dd, 35);
                // the same view with the Detail_* objects switched off (what a low tier sees)
                foreach (var r in go.GetComponentsInChildren<Renderer>(true).Where(r => r.name.Contains("_Detail_"))) r.enabled = false;
                Shot(id + "_close_no_detail", dc, dc + new Vector3(.6f, .55f, -.85f).normalized * dd, 35);
                foreach (var r in go.GetComponentsInChildren<Renderer>(true).Where(r => r.name.Contains("_Detail_"))) r.enabled = true;
            }
            if (ids.Contains("SG01_StraightRun") && ids.Contains("SG02_Landing") && ids.Contains("SG03_RailSloped")) Combo(new Vector3(ids.Length * 30, 0, 0));
            File.WriteAllText(Path.Combine(Out, "unity-verify-report.txt"), string.Join("\n", Report) + $"\n\nUnity {Application.unityVersion}; failed checks: {failed}; editor batch check only, not placed in the main scene, not played\n");
            Debug.Log("MOUNTAIN_STAIRS_" + (failed == 0 ? "PASS" : "FAIL") + "\n" + string.Join("\n", Report));
            if (failed > 0 && Application.isBatchMode) EditorApplication.Exit(1);
        }

        static void Copy(string id)
        {
            var src = Path.Combine(Exports, id); var dst = Path.Combine(Repo, "apps", "game", Root, id);
            Directory.CreateDirectory(Path.Combine(dst, "Textures"));
            foreach (var old in Directory.GetFiles(dst, "*.fbx").Where(f => !f.EndsWith($"_{Info(id).version}.fbx"))) { File.Delete(old); if (File.Exists(old + ".meta")) File.Delete(old + ".meta"); }
            foreach (var file in Directory.GetFiles(src, $"{id}_{Info(id).version}.fbx").Concat(Directory.GetFiles(Path.Combine(src, "Textures"), "*.png")))
                File.Copy(file, Path.Combine(dst, file.Substring(src.Length + 1)), true);
        }

        static void Configure(string id)
        {
            var importer = AssetImporter.GetAtPath(Fbx(id)) as ModelImporter;
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

        static GameObject Place(string id, Vector3 position)
        {
            var go = (GameObject)PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>(Fbx(id)));
            PrefabUtility.UnpackPrefabInstance(go, PrefabUnpackMode.Completely, InteractionMode.AutomatedAction);
            go.transform.position = position;
            var mat = Mat(id);
            foreach (var r in go.GetComponentsInChildren<Renderer>(true))
            {
                if (r.name == id + "_Collision") { r.enabled = false; continue; }
                r.sharedMaterials = Enumerable.Repeat(mat, r.sharedMaterials.Length).ToArray();
            }
            var cut = new[] { .1f, .035f, .006f };
            // Unity builds a LODGroup itself from the _LOD0/1/2 names; set the same cut-offs on it (or add one if it did not)
            var group = go.GetComponent<LODGroup>(); if (group == null) group = go.AddComponent<LODGroup>();
            group.SetLODs(Enumerable.Range(0, 3).Select(i => new LOD(cut[i], go.GetComponentsInChildren<Renderer>(true).Where(r => r.name.EndsWith("_LOD" + i)).ToArray())).ToArray());
            var col = go.GetComponentsInChildren<MeshFilter>(true).FirstOrDefault(m => m.name == id + "_Collision");
            if (col != null) col.gameObject.AddComponent<MeshCollider>().sharedMesh = col.sharedMesh;
            return go;
        }

        static GameObject Person(Vector3 feet)
        {
            var p = GameObject.CreatePrimitive(PrimitiveType.Capsule); p.name = "Person_1.75m";
            p.transform.localScale = new Vector3(.45f, .875f, .45f); p.transform.position = feet + Vector3.up * .875f;
            var m = new Material(Shader.Find("Universal Render Pipeline/Lit")); m.SetColor("_BaseColor", new Color(.55f, .57f, .6f)); p.GetComponent<Renderer>().sharedMaterial = m;
            return p;
        }

        static Bounds LodBounds(GameObject go, string suffix = "_LOD0")
        {
            var rs = go.GetComponentsInChildren<Renderer>(true).Where(r => r.name.EndsWith(suffix)).ToArray();
            var b = rs[0].bounds; foreach (var r in rs) b.Encapsulate(r.bounds); return b;
        }

        static void Verify(string id, GameObject go)
        {
            var info = Info(id);
            var b = LodBounds(go); var o = go.transform.position;
            float[] want = info.dimensions_m; Vector3 size = b.size;
            float dx = Mathf.Abs(size.x - want[0]), dy = Mathf.Abs(size.z - want[1]), dz = Mathf.Abs(size.y - want[2]);
            Check(dx < .002f && dy < .002f && dz < .002f, $"{id}: imported size {size.x:F3} x {size.z:F3} x {size.y:F3} m matches model_info (max error {Mathf.Max(dx, dy, dz) * 1000:F1} mm)");
            var lo = b.min - o; var hi = b.max - o;
            float e = Mathf.Max(Mathf.Abs(lo.x - info.bounds_min_m[0]), Mathf.Abs(lo.z - info.bounds_min_m[1]), Mathf.Abs(lo.y - info.bounds_min_m[2]),
                                Mathf.Abs(hi.x - info.bounds_max_m[0]), Mathf.Abs(hi.z - info.bounds_max_m[1]), Mathf.Abs(hi.y - info.bounds_max_m[2]));
            Check(e < .002f, $"{id}: bounds about the origin {lo.x:F3}..{hi.x:F3}, {lo.z:F3}..{hi.z:F3}, {lo.y:F3}..{hi.y:F3} m equal model_info (max error {e * 1000:F1} mm)");
            Report.Add($"INFO {id}: minTier {info.minTier}");
            var lod = go.GetComponent<LODGroup>();
            Check(lod != null && lod.GetLODs().Length == 3 && lod.GetLODs().All(l => l.renderers.Length > 0), $"{id}: LODGroup with 3 filled levels");
            var mfs = go.GetComponentsInChildren<MeshFilter>(true);
            int tri(string s) => mfs.Where(m => m.name.EndsWith(s)).Sum(m => m.sharedMesh.triangles.Length / 3);
            int objs(string s) => mfs.Count(m => m.name.EndsWith(s));
            Check(tri("_LOD0") == info.lod_totals.LOD0 && tri("_LOD1") == info.lod_totals.LOD1 && tri("_LOD2") == info.lod_totals.LOD2,
                  $"{id}: imported LOD triangles {tri("_LOD0")}/{tri("_LOD1")}/{tri("_LOD2")} equal model_info {info.lod_totals.LOD0}/{info.lod_totals.LOD1}/{info.lod_totals.LOD2}");
            if (info.budget_per_lod != null && info.budget_per_lod.LOD0 != null)
            {
                var bl = new[] { info.budget_per_lod.LOD0, info.budget_per_lod.LOD1, info.budget_per_lod.LOD2 };
                Check(Enumerable.Range(0, 3).All(i => objs("_LOD" + i) == bl[i].objects), $"{id}: objects per LOD {objs("_LOD0")}/{objs("_LOD1")}/{objs("_LOD2")} equal model_info {bl[0].objects}/{bl[1].objects}/{bl[2].objects}");
                int slots = go.GetComponentsInChildren<Renderer>(true).Where(r => r.name.EndsWith("_LOD0")).Sum(r => r.sharedMaterials.Length);
                Report.Add($"INFO {id}: LOD0 material slots {slots} (model_info materials {bl[0].materials}); one URP Lit material shared by every LOD");
            }
            foreach (var d in info.detailObjects ?? new string[0])
                Check(Enumerable.Range(0, 3).All(i => mfs.Any(m => m.name == $"{d}_LOD{i}")), $"{id}: {d} present at LOD0/1/2 as its own object (can be switched off)");
            var col = go.GetComponentsInChildren<MeshCollider>(true).FirstOrDefault(c => c.name == id + "_Collision");
            Check(col != null && col.sharedMesh.triangles.Length > 0, $"{id}: {id}_Collision imported as MeshCollider ({(col ? col.sharedMesh.triangles.Length / 3 : 0)} triangles), renderer hidden");
            if (col != null)
            {
                var box = col.bounds; var all = b; all.Expand(.1f);
                Check(all.Contains(box.min) && all.Contains(box.max), $"{id}: the collider stays on the model");
                Physics.SyncTransforms();
                var top = o + Vector3.up * (b.size.y + 1);
                Check(Physics.Raycast(top, Vector3.down, out var hit, b.size.y + 2) && hit.collider == col, $"{id}: a ray from above hits the collider ({(hit.collider ? hit.point.y - o.y : -1):F3} m)");
            }
            Check(!go.GetComponentsInChildren<Renderer>(true).Any(r => r.enabled && r.sharedMaterial != null && r.sharedMaterial.shader.name.Contains("Error")), $"{id}: no error shaders");
            foreach (var t in Directory.GetFiles(Path.Combine(Repo, "apps", "game", Root, id, "Textures"), "*.png"))
            {
                var tex = Tex(id, Path.GetFileName(t)); if (tex != null) Report.Add($"INFO {id}: texture {tex.name} {tex.width}x{tex.height}");
            }
        }

        // Socket empties come through the FBX as plain transforms; their positions must match model_info (Blender x, y, z -> Unity x, z, y).
        static void Sockets(string id, GameObject go)
        {
            var text = File.ReadAllText(Path.Combine(Exports, id, "model_info.json"));
            int a = text.IndexOf("\"sockets_blender_xyz\""); if (a < 0) { Report.Add($"INFO {id}: no sockets in model_info"); return; }
            int b = text.IndexOf('{', a), e = text.IndexOf('}', b);
            var o = go.transform.position; float worst = 0; int found = 0, wanted = 0;
            foreach (var entry in text.Substring(b + 1, e - b - 1).Split(new[] { "]," }, StringSplitOptions.RemoveEmptyEntries))
            {
                var kv = entry.Split(':'); var name = kv[0].Trim().Trim('"', ' ', (char)10, (char)13);
                var v = kv[1].Replace("[", "").Replace("]", "").Split(',').Select(x => float.Parse(x.Trim(), System.Globalization.CultureInfo.InvariantCulture)).ToArray();
                wanted++;
                var t = go.GetComponentsInChildren<Transform>(true).FirstOrDefault(x => x.name == name); if (t == null) continue;
                found++; var p = t.position - o; worst = Mathf.Max(worst, Vector3.Distance(p, new Vector3(v[0], v[2], v[1])));
            }
            Check(found == wanted && worst < .002f, $"{id}: {found}/{wanted} socket empties imported at the model_info positions (max error {worst * 1000:F1} mm)");
        }

        // A 1.75 m CharacterController (radius 0.25, step offset 0.3, slope limit 45) walks from 1 m before the first riser up the centre line
        // on the stair collider and must end standing on the top tread. Done with CharacterController.Move in the editor, not in play mode.
        static void Walk(string id, GameObject go)
        {
            Physics.SyncTransforms();
            var o = go.transform.position; var b = LodBounds(go);
            var body = new GameObject("Walker_1.75m"); var cc = body.AddComponent<CharacterController>();
            cc.height = 1.75f; cc.radius = .25f; cc.center = new Vector3(0, .875f, 0); cc.stepOffset = .3f; cc.slopeLimit = 45; cc.skinWidth = .02f;
            foreach (float x in new[] { -.85f, 0f, .85f })   // 0.25 m radius: the body stays inside the 2.4 m walking width
            {
                body.transform.position = o + new Vector3(x, .02f, b.min.z - o.z - 1f); Physics.SyncTransforms();
                float topZ = b.max.z - o.z - .3f, highest = 0; int frames = 0;
                for (; frames < 900 && body.transform.position.z - o.z < topZ; frames++)
                {
                    cc.Move(new Vector3(0, -9.8f * (1 / 60f), 1.4f / 60f));
                    highest = Mathf.Max(highest, body.transform.position.y - o.y);
                }
                var end = body.transform.position - o;
                Check(end.z >= topZ && Mathf.Abs(end.y - 1.6f) < .06f, $"{id}: walker on x {x:F2} climbs the ten steps on the collider (end y {end.y:F3} m, z {end.z:F2} m, {frames} frames at 1.4 m/s)");
            }
            UnityEngine.Object.DestroyImmediate(body);
        }

        static CharacterController Walker()
        {
            var body = new GameObject("Walker_1.75m"); var cc = body.AddComponent<CharacterController>();
            cc.height = 1.75f; cc.radius = .25f; cc.center = new Vector3(0, .875f, 0); cc.stepOffset = .3f; cc.slopeLimit = 45; cc.skinWidth = .02f;
            return cc;
        }

        // walk dir at 1.4 m/s with gravity for up to n frames; returns the lowest and highest feet height relative to o
        static Vector2 Stroll(CharacterController cc, Vector3 o, Vector3 dir, int n)
        {
            float lo = 99, hi = -99;
            for (int f = 0; f < n; f++)
            {
                cc.Move(dir * (1.4f / 60f) + Vector3.down * (9.8f / 60f));
                if (f > 20) { float y = cc.transform.position.y - o.y; lo = Mathf.Min(lo, y); hi = Mathf.Max(hi, y); }
            }
            return new Vector2(lo, hi);
        }

        // SG02: stand on the landing and walk across it over the slab joints, both ways; the feet stay at the 0.4 m surface
        static void WalkAcross(string id, GameObject go)
        {
            Physics.SyncTransforms(); var o = go.transform.position; var cc = Walker();
            foreach (var (from, dir) in new[] { (new Vector3(-1.5f, .45f, -.3f), Vector3.right), (new Vector3(-.3f, .45f, -1.5f), Vector3.forward) })
            {
                cc.transform.position = o + from; Physics.SyncTransforms();
                var r = Stroll(cc, o, dir, 120); var end = cc.transform.position - o;
                Check(r.x > .38f && r.y < .43f && Vector3.Dot(end - from, dir) > 2.4f, $"{id}: walker crosses the landing along {dir} over the joints (feet {r.x:F3}-{r.y:F3} m, moved {Vector3.Dot(end - from, dir):F2} m)");
            }
            UnityEngine.Object.DestroyImmediate(cc.gameObject);
        }

        // SG04: walk in from 1 m in front of the open side; the walker steps onto the 6 cm floor and stops at the bench or the rock
        static void WalkIn(string id, GameObject go)
        {
            Physics.SyncTransforms(); var o = go.transform.position; var cc = Walker();
            // x 0.4: into the bench front (y 0.51); x -0.6: through the 0.6 m slot between the basin and the bench end to the cliff foot (y 1.0),
            // staying on the floor all the way (a narrower slot wedged the walker and lifted it)
            foreach (var (x, zlo, zhi, what) in new[] { (.4f, .0f, .5f, "stops at the bench"), (-.6f, .6f, 1f, "passes between the basin and the bench to the cliff") })
            {
                cc.transform.position = o + new Vector3(x, .02f, -2.5f); Physics.SyncTransforms();
                Stroll(cc, o, Vector3.forward, 60);                       // from open ground up onto the 0.06 m floor
                var feet = Stroll(cc, o, Vector3.forward, 160); var end = cc.transform.position - o;   // then on the floor only
                Check(end.z > zlo && end.z < zhi && Mathf.Abs(feet.x - .06f) < .03f && Mathf.Abs(feet.y - .06f) < .03f,
                      $"{id}: walker on x {x:F1} walks in under the roof and {what} (end z {end.z:F2} m, feet {feet.x:F3}-{feet.y:F3} m)");
            }
            UnityEngine.Object.DestroyImmediate(cc.gameObject);
        }

        // SG03 straight bay: a walker pushed at it stops in front of it
        static void Blocks(string id, GameObject go)
        {
            Physics.SyncTransforms(); var o = go.transform.position; var cc = Walker();
            cc.transform.position = o + new Vector3(0, .02f, -1.2f); Physics.SyncTransforms();
            Stroll(cc, o, Vector3.forward, 120); var end = cc.transform.position - o;
            Check(end.z < -.3f && end.z > -.45f, $"{id}: a walker pushed at the rail stops in front of it (centre z {end.z:F2} m; rail face at -0.10 m)");
            UnityEngine.Object.DestroyImmediate(cc.gameObject);
        }

        // SG01 with SG03 sloped runs on both kerbs and SG02 at the top (its Socket_Edge_S on SG01's Socket_Top): climb onto the landing,
        // the rails stand in their sockets, and the walker cannot step off sideways through a rail.
        static void Combo(Vector3 at)
        {
            var stair = Place("SG01_StraightRun", at);
            var land = Place("SG02_Landing", at + new Vector3(0, 1.2f, 3.6f));
            var rails = new[] { -1.34f, 1.34f }.Select(x => Place("SG03_RailSloped", at + new Vector3(x, 0, 0))).ToArray();
            Physics.SyncTransforms();
            var top = stair.GetComponentsInChildren<Transform>().First(t => t.name == "Socket_Top").position;
            var edge = land.GetComponentsInChildren<Transform>().First(t => t.name == "Socket_Edge_S").position;
            Check(Vector3.Distance(top, edge) < .002f, $"combo: SG02 Socket_Edge_S on SG01 Socket_Top ({Vector3.Distance(top, edge) * 1000:F1} mm)");
            float worst = 0;
            foreach (var (r, s) in rails.Select((r, i) => (r, i == 0 ? "L" : "R")))
                for (int i = 0; i < 3; i++)
                {
                    var a = r.GetComponentsInChildren<Transform>().First(t => t.name == "Socket_Post_" + i).position;
                    var b = stair.GetComponentsInChildren<Transform>().First(t => t.name == $"Socket_Post_{s}{i}").position;
                    worst = Mathf.Max(worst, Vector3.Distance(a, b));
                }
            Check(worst < .002f, $"combo: six SG03 posts on the six SG01 sockets (max error {worst * 1000:F1} mm)");
            var cc = Walker(); cc.transform.position = at + new Vector3(0, .02f, -2.6f); Physics.SyncTransforms();
            Stroll(cc, at, Vector3.forward, 300); var end = cc.transform.position - at;
            Check(Mathf.Abs(end.y - 1.6f) < .06f && end.z > 2.5f, $"combo: walker climbs SG01 onto the SG02 landing (feet {end.y:F3} m, z {end.z:F2} m)");
            cc.transform.position = at + new Vector3(0, .82f, -.4f); Physics.SyncTransforms();
            Stroll(cc, at, Vector3.right, 120); var side = cc.transform.position - at;
            Check(side.x < 1.2f, $"combo: walker pushed sideways on the flight stays inside the kerb and rail (centre x {side.x:F2} m)");
            UnityEngine.Object.DestroyImmediate(cc.gameObject);
            var b2 = LodBounds(land); b2.Encapsulate(LodBounds(stair));
            var person = Person(at + new Vector3(-2.2f, 0, -1.2f));
            Shot("combo_SG01_SG03_SG02", b2.center, b2.center + new Vector3(.8f, .45f, -.9f).normalized * b2.size.magnitude * 1.25f, 35);
            Shot("combo_on_the_flight", at + new Vector3(0, 1.5f, 1.5f), at + new Vector3(.3f, 1.65f, -2.4f), 55);
            person.SetActive(false);
        }

        static void Lighting()
        {
            RenderSettings.ambientMode = AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = new Color(.62f, .68f, .7f); RenderSettings.ambientEquatorColor = new Color(.45f, .44f, .38f); RenderSettings.ambientGroundColor = new Color(.2f, .18f, .14f);
            var sun = new GameObject("Sun").AddComponent<Light>(); sun.type = LightType.Directional; sun.intensity = 1.25f;
            sun.color = new Color(1, .96f, .88f); sun.transform.rotation = Quaternion.Euler(38, -30, 0); sun.shadows = LightShadows.Soft;
            var cam = new GameObject("Main Camera", typeof(Camera)).GetComponent<Camera>(); cam.tag = "MainCamera"; cam.nearClipPlane = .02f; cam.farClipPlane = 300;
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
    }
}
