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
    // Work pack 2026-11-07, part 2 (FR01-FR04 ancient-forest roots), exported into art/exports/forest-roots-b.
    // Imports each model into a gitignored folder, checks it against its model_info.json (size, origin, LOD levels and triangles,
    // objects, Detail_* objects, collider or none, shaders, socket empties), then walks a 1.75 m CharacterController:
    // FR01 a walker pushed at each wall stops in front of it; FR02 through the arch along the path; FR04 up the stepping rounds,
    // along the deck and down the far steps; FR03 (no collider) straight through the hanging curtain. URP captures beside a 1.75 m capsule.
    // Writes artifacts/forest-roots-unity/. Run with -executeMethod YunJing.Editor.ForestRootsModelCheck.Run
    // This is an editor batch check, not play in the game: nothing is placed in the main scene.
    public static class ForestRootsModelCheck
    {
        const string Root = "Assets/YunJing/Generated/ForestRootsB";
        static string Repo => Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", ".."));
        static string Exports => Path.Combine(Repo, "art", "exports", "forest-roots-b");
        static string Out => Path.Combine(Repo, "artifacts", "forest-roots-unity");
        static readonly string[] Wanted = { "FR01_RootWall_Stacked", "FR01_RootWall_Braided", "FR01_RootWall_Wave", "FR02_RootArch",
                                            "FR03_VineCurtain_Dense", "FR03_VineCurtain_Sparse", "FR04_LogBridge" };
        static readonly List<string> Report = new List<string>();
        static int failed;

        [Serializable] class Budget { public int triangles, objects, objects_without_detail, materials; }
        [Serializable] class BudgetPerLod { public Budget LOD0, LOD1, LOD2; }
        [Serializable] class LodTotals { public int LOD0, LOD1, LOD2; }
        [Serializable] class ModelInfo { public string version, minTier; public float[] dimensions_m, bounds_min_m, bounds_max_m; public float ground_z_m; public bool collision; public LodTotals lod_totals; public BudgetPerLod budget_per_lod; public string[] detailObjects; }

        static readonly Dictionary<string, ModelInfo> infos = new Dictionary<string, ModelInfo>();
        static ModelInfo Info(string id)
        {
            if (!infos.TryGetValue(id, out var i)) infos[id] = i = JsonUtility.FromJson<ModelInfo>(File.ReadAllText(Path.Combine(Exports, id, "model_info.json")));
            return i;
        }
        static string Fbx(string id) => $"{Root}/{id}/{id}_{Info(id).version}.fbx";
        static void Check(bool ok, string what) { Report.Add((ok ? "PASS " : "FAIL ") + what); if (!ok) failed++; }
        static bool IsCards(Renderer r) => r.name.Contains("_Leaves_LOD");

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
            var ground = GameObject.CreatePrimitive(PrimitiveType.Plane); ground.name = "Placeholder_Ground"; ground.transform.localScale = new Vector3(60, 1, 20);
            ground.transform.position = new Vector3(ids.Length * 15, -.001f, 0);
            var gm = new Material(Shader.Find("Universal Render Pipeline/Lit")); gm.SetColor("_BaseColor", new Color(.3f, .29f, .24f)); gm.SetFloat("_Smoothness", 0);
            gm.SetFloat("_SpecularHighlights", 0); gm.EnableKeyword("_SPECULARHIGHLIGHTS_OFF");
            gm.SetFloat("_EnvironmentReflections", 0); gm.EnableKeyword("_ENVIRONMENTREFLECTIONS_OFF");
            ground.GetComponent<Renderer>().sharedMaterial = gm;
            for (int n = 0; n < ids.Length; n++)
            {
                var id = ids[n];
                var at = new Vector3(n * 30, -Info(id).ground_z_m, 0);       // FR03 hangs from its origin: the hang line 3 m above the ground
                var go = Place(id, at); Verify(id, go); Sockets(id, go);
                var foot = new Vector3(at.x, 0, at.z);
                if (id.StartsWith("FR01_")) Blocks(id, go, foot);
                if (id == "FR02_RootArch") WalkThroughArch(id, foot);
                if (id.StartsWith("FR03_")) WalkThroughCurtain(id, foot);
                if (id == "FR04_LogBridge") WalkOverBridge(id, foot);
                var b = LodBounds(go);
                var person = Person(foot + new Vector3(-(b.extents.x + .6f), 0, 0));
                var both = b; both.Encapsulate(person.GetComponent<Renderer>().bounds);
                float d = both.size.magnitude * 1.5f; var c = both.center;
                Shot(id + "_three_quarter", c, c + new Vector3(.75f, .35f, -.85f).normalized * d, 35);
                Shot(id + "_front", c, c + new Vector3(0, .1f, -1).normalized * d, 35);
                person.SetActive(false);
                if (id == "FR02_RootArch" || id == "FR04_LogBridge")
                {   // the capsule where a player walks: under the crown / on the deck
                    var on = Person(foot + (id == "FR02_RootArch" ? new Vector3(0, .012f, 0) : new Vector3(-.6f, .85f, 0)));
                    Shot(id + "_walk", b.center, b.center + new Vector3(.8f, .45f, -.9f).normalized * b.size.magnitude * 1.15f, 35);
                    UnityEngine.Object.DestroyImmediate(on);
                }
                var dc = b.center; float dd = Mathf.Max(b.size.magnitude * 1.0f, .9f);
                Shot(id + "_close", dc, dc + new Vector3(.6f, .45f, -.85f).normalized * dd, 35);
                var det = go.GetComponentsInChildren<Renderer>(true).Where(r => r.name.Contains("_Detail_")).ToArray();
                if (det.Length > 0)
                {
                    foreach (var r in det) r.enabled = false;
                    Shot(id + "_close_no_detail", dc, dc + new Vector3(.6f, .45f, -.85f).normalized * dd, 35);
                    foreach (var r in det) r.enabled = true;
                }
            }
            File.WriteAllText(Path.Combine(Out, "unity-verify-report.txt"), string.Join("\n", Report) + $"\n\nUnity {Application.unityVersion}; failed checks: {failed}; editor batch check only, not placed in the main scene, not played\n");
            Debug.Log("FOREST_ROOTS_" + (failed == 0 ? "PASS" : "FAIL") + "\n" + string.Join("\n", Report));
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
                if (path.Contains("_VineCards_")) { ti.alphaIsTransparency = !normal; ti.mipMapsPreserveCoverage = !normal; ti.alphaTestReferenceValue = .5f; }
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

        // FR03 vine cards: URP Lit, alpha clip 0.5, both faces rendered
        static Material CardMat(string id)
        {
            var path = $"{Root}/{id}_VineCards.mat";
            var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (mat == null) { mat = new Material(Shader.Find("Universal Render Pipeline/Lit")); AssetDatabase.CreateAsset(mat, path); }
            mat.SetTexture("_BaseMap", Tex(id, "FR03_VineCards_BaseColor.png")); mat.SetColor("_BaseColor", Color.white);
            mat.SetTexture("_BumpMap", Tex(id, "FR03_VineCards_Normal.png")); mat.EnableKeyword("_NORMALMAP");
            mat.SetFloat("_AlphaClip", 1); mat.SetFloat("_Cutoff", .5f); mat.EnableKeyword("_ALPHATEST_ON");
            mat.SetFloat("_Cull", (float)CullMode.Off); mat.doubleSidedGI = true;
            mat.SetFloat("_Smoothness", .3f); mat.renderQueue = (int)RenderQueue.AlphaTest; mat.SetOverrideTag("RenderType", "TransparentCutout");
            EditorUtility.SetDirty(mat); return mat;
        }

        static GameObject Place(string id, Vector3 position)
        {
            var go = (GameObject)PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>(Fbx(id)));
            PrefabUtility.UnpackPrefabInstance(go, PrefabUnpackMode.Completely, InteractionMode.AutomatedAction);
            go.transform.position = position;
            var mat = Mat(id); Material cards = null;
            foreach (var r in go.GetComponentsInChildren<Renderer>(true))
            {
                if (r.name == id + "_Collision") { r.enabled = false; continue; }
                if (IsCards(r)) { cards = cards ?? CardMat(id); r.sharedMaterials = Enumerable.Repeat(cards, r.sharedMaterials.Length).ToArray(); continue; }
                r.sharedMaterials = Enumerable.Repeat(mat, r.sharedMaterials.Length).ToArray();
            }
            var cut = new[] { .1f, .035f, .006f };
            var group = go.GetComponent<LODGroup>(); if (group == null) group = go.AddComponent<LODGroup>();
            group.SetLODs(Enumerable.Range(0, 3).Select(i => new LOD(cut[i], go.GetComponentsInChildren<Renderer>(true).Where(r => r.name.EndsWith("_LOD" + i)).ToArray())).ToArray());
            var col = go.GetComponentsInChildren<MeshFilter>(true).FirstOrDefault(m => m.name == id + "_Collision");
            if (col != null) col.gameObject.AddComponent<MeshCollider>().sharedMesh = col.sharedMesh;
            return go;
        }

        static GameObject Person(Vector3 feet)
        {
            var p = GameObject.CreatePrimitive(PrimitiveType.Capsule); p.name = "Person_1.75m";
            UnityEngine.Object.DestroyImmediate(p.GetComponent<Collider>());
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
                Report.Add($"INFO {id}: LOD0 material slots {slots} (model_info materials {bl[0].materials})");
            }
            foreach (var d in info.detailObjects ?? new string[0])
                Check(Enumerable.Range(0, 3).All(i => mfs.Any(m => m.name == $"{d}_LOD{i}")), $"{id}: {d} present at LOD0/1/2 as its own object (can be switched off)");
            var col = go.GetComponentsInChildren<MeshCollider>(true).FirstOrDefault(c => c.name == id + "_Collision");
            if (info.collision)
            {
                Check(col != null && col.sharedMesh.triangles.Length > 0, $"{id}: {id}_Collision imported as MeshCollider ({(col ? col.sharedMesh.triangles.Length / 3 : 0)} triangles), renderer hidden");
                if (col != null)
                {
                    var box = col.bounds; var all = b; all.Expand(.1f);
                    Check(all.Contains(box.min) && all.Contains(box.max), $"{id}: the collider stays on the model");
                }
            }
            else Check(col == null && go.GetComponentsInChildren<Collider>(true).Length == 0, $"{id}: no collider at all (decorative; switching it off changes nothing for walking)");
            if (id.StartsWith("FR03_"))
            {
                var cr = go.GetComponentsInChildren<Renderer>(true).Where(IsCards).ToArray();
                Check(cr.Length == 3 && cr.All(r => r.sharedMaterial.IsKeywordEnabled("_ALPHATEST_ON") && r.sharedMaterial.GetFloat("_Cull") == 0),
                      $"{id}: vine cards at LOD0/1/2 with an alpha-clipped two-sided URP material ({cr.Length} renderers)");
                var mf = mfs.First(m => m.name.EndsWith("_Leaves_LOD0")); var cols = mf.sharedMesh.colors;
                Check(cols != null && cols.Length == mf.sharedMesh.vertexCount && cols.Max(c => c.r) > .95f && cols.Min(c => c.r) < .03f,
                      $"{id}: Wind vertex colour imported on the cards (R {(cols.Length > 0 ? cols.Min(c => c.r) : -1):F2}..{(cols.Length > 0 ? cols.Max(c => c.r) : -1):F2})");
            }
            Check(!go.GetComponentsInChildren<Renderer>(true).Any(r => r.enabled && r.sharedMaterial != null && r.sharedMaterial.shader.name.Contains("Error")), $"{id}: no error shaders");
            foreach (var t in Directory.GetFiles(Path.Combine(Repo, "apps", "game", Root, id, "Textures"), "*.png"))
            {
                var tex = Tex(id, Path.GetFileName(t)); if (tex != null) Report.Add($"INFO {id}: texture {tex.name} {tex.width}x{tex.height}");
            }
        }

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

        static CharacterController Walker()
        {
            var body = new GameObject("Walker_1.75m"); var cc = body.AddComponent<CharacterController>();
            cc.height = 1.75f; cc.radius = .25f; cc.center = new Vector3(0, .875f, 0); cc.stepOffset = .3f; cc.slopeLimit = 45; cc.skinWidth = .02f;
            return cc;
        }

        // walk dir at 1.4 m/s with gravity for n frames; returns (lowest, highest) feet height relative to o after the first 20 frames
        static Vector2 Stroll(CharacterController cc, Vector3 o, Vector3 dir, int n, Func<Vector3, bool> record = null)
        {
            float lo = 99, hi = -99;
            for (int f = 0; f < n; f++)
            {
                cc.Move(dir * (1.4f / 60f) + Vector3.down * (9.8f / 60f));
                var p = cc.transform.position - o;
                if (f > 20 && (record == null || record(p))) { lo = Mathf.Min(lo, p.y); hi = Mathf.Max(hi, p.y); }
            }
            return new Vector2(lo, hi);
        }

        // FR01: a walker pushed at the wall from the front stops in front of it, at three points along the section
        static void Blocks(string id, GameObject go, Vector3 o)
        {
            Physics.SyncTransforms(); var cc = Walker();
            foreach (float x in new[] { -1.5f, 0f, 1.5f })
            {
                cc.transform.position = o + new Vector3(x, .02f, -2.2f); Physics.SyncTransforms();
                Stroll(cc, o, Vector3.forward, 150); var end = cc.transform.position - o;
                Check(end.z < -.3f && end.y < .1f, $"{id}: a walker pushed at the wall on x {x:F1} stops in front of it (centre z {end.z:F2} m, feet {end.y:F3} m)");
            }
            UnityEngine.Object.DestroyImmediate(cc.gameObject);
        }

        // FR02: from 2.5 m in front, along the path (+Z) right through under the crown to 2.5 m behind; head room is the collider's
        static void WalkThroughArch(string id, Vector3 o)
        {
            Physics.SyncTransforms(); var cc = Walker();
            foreach (float x in new[] { -.35f, 0f, .35f })
            {
                cc.transform.position = o + new Vector3(x, .02f, -2.6f); Physics.SyncTransforms();
                var feet = Stroll(cc, o, Vector3.forward, 230); var end = cc.transform.position - o;
                Check(end.z > 2.2f && feet.y < .08f && Mathf.Abs(end.x - x) < .15f,
                      $"{id}: walker on x {x:F2} walks through under the arch along the path (end z {end.z:F2} m, x {end.x:F2} m, feet {feet.x:F3}-{feet.y:F3} m)");
            }
            // pushed head-on at the front-left leg from outside, along its outward diagonal: it must stop against the root, not pass into it.
            // (Pushed square from the side the round leg deflects the walker round it and into the arch, as any round post would.)
            var leg = new Vector3(-1.86f, 0, -.82f); var outward = new Vector3(-1, 0, -.6f).normalized;
            cc.transform.position = o + leg + outward * 1.8f + Vector3.up * .02f; Physics.SyncTransforms();
            Stroll(cc, o, -outward, 120); var p = cc.transform.position - o; var flat = new Vector3(p.x, 0, p.z);
            float dist = Vector3.Distance(flat, leg);
            Check(dist > .62f && Vector3.Dot(flat - leg, outward) > .5f, $"{id}: a walker pushed head-on at a leg stops outside it ({dist:F2} m from the leg's foot centre, on the outer side; the leg leans in, its collider radius about 0.48 m at hip height)");
            UnityEngine.Object.DestroyImmediate(cc.gameObject);
        }

        // FR03: no collider, so a walker goes straight through the curtain hanging 3 m up (its tips about 5 cm off the ground)
        static void WalkThroughCurtain(string id, Vector3 o)
        {
            Physics.SyncTransforms(); var cc = Walker();
            cc.transform.position = o + new Vector3(0, .02f, -1.5f); Physics.SyncTransforms();
            var feet = Stroll(cc, o, Vector3.forward, 140); var end = cc.transform.position - o;
            Check(end.z > 1.4f && feet.y < .03f, $"{id}: walker walks straight through the curtain (end z {end.z:F2} m, feet {feet.x:F3}-{feet.y:F3} m)");
            UnityEngine.Object.DestroyImmediate(cc.gameObject);
        }

        // FR04: from the ground 0.8 m beyond the west end, up the four stepping rounds, along the deck, down the east rounds to the ground
        static void WalkOverBridge(string id, Vector3 o)
        {
            Physics.SyncTransforms(); var cc = Walker();
            cc.transform.position = o + new Vector3(-4.3f, .02f, 0); Physics.SyncTransforms();
            float deckLo = 99, deckHi = -99, top = -99;
            for (int f = 0; f < 520; f++)
            {
                cc.Move(Vector3.right * (1.4f / 60f) + Vector3.down * (9.8f / 60f));
                var p = cc.transform.position - o; top = Mathf.Max(top, p.y);
                if (p.x > -1.8f && p.x < 1.8f) { deckLo = Mathf.Min(deckLo, p.y); deckHi = Mathf.Max(deckHi, p.y); }
            }
            var end = cc.transform.position - o;
            Check(deckLo > .82f && deckHi < .88f && end.x > 3.7f && end.y < .05f && Mathf.Abs(end.z) < .15f,
                  $"{id}: walker climbs the west rounds, crosses on the deck and steps down the east rounds (feet on the deck {deckLo:F3}-{deckHi:F3} m, highest {top:F3} m, end x {end.x:F2} m, y {end.y:F3} m, z {end.z:F2} m)");
            cc.transform.position = o + new Vector3(0, .02f, -1.2f); Physics.SyncTransforms();
            Stroll(cc, o, Vector3.forward, 90); var side = cc.transform.position - o;
            Check(side.z < -.4f && side.y < .1f, $"{id}: a walker on the ground pushed at the log's flank stops at it (centre z {side.z:F2} m)");
            UnityEngine.Object.DestroyImmediate(cc.gameObject);
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
