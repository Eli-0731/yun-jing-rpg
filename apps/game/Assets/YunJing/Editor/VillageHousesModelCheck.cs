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
    // Work pack 2026-11-07, part 2 (VL01-VL03 empty-house variants of the Dondon StarterHouse), exported into art/exports/village-houses-b.
    // Imports each model into a gitignored folder, checks it against its model_info.json (size, origin, LOD levels and triangles, objects,
    // Detail_* objects, collider, four material slots: Main / Stone / Wood atlases and the roof-tile material, sockets), then walks a 1.75 m
    // CharacterController: up the three steps onto the porch and against the (closed) door; pushed at the back, left and right walls from
    // outside it stops outside; VL03: from outside the fallen right wall, up the rubble, stopped at the old wall line (nobody gets into the
    // room or stuck in the heap). URP captures beside a 1.75 m capsule.
    // Writes artifacts/village-houses-unity/. Run with -executeMethod YunJing.Editor.VillageHousesModelCheck.Run
    // This is an editor batch check, not play in the game: nothing is placed in the main scene.
    public static class VillageHousesModelCheck
    {
        const string Root = "Assets/YunJing/Generated/VillageHousesB";
        static string Repo => Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", ".."));
        static string Exports => Path.Combine(Repo, "art", "exports", "village-houses-b");
        static string Out => Path.Combine(Repo, "artifacts", "village-houses-unity");
        static readonly string[] Wanted = { "VL01_LongEmptyHouse", "VL02_MovedInHouse", "VL03_HalfCollapsedHouse" };
        static readonly string[] Slots = { "Main", "Stone", "Wood", "RoofTiles" };
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
            var ground = GameObject.CreatePrimitive(PrimitiveType.Plane); ground.name = "Placeholder_Ground"; ground.transform.localScale = new Vector3(80, 1, 20);
            ground.transform.position = new Vector3(ids.Length * 20, -.001f, 0);
            var gm = new Material(Shader.Find("Universal Render Pipeline/Lit")); gm.SetColor("_BaseColor", new Color(.3f, .29f, .24f)); gm.SetFloat("_Smoothness", 0);
            gm.SetFloat("_SpecularHighlights", 0); gm.EnableKeyword("_SPECULARHIGHLIGHTS_OFF");
            gm.SetFloat("_EnvironmentReflections", 0); gm.EnableKeyword("_ENVIRONMENTREFLECTIONS_OFF");
            ground.GetComponent<Renderer>().sharedMaterial = gm;
            for (int n = 0; n < ids.Length; n++)
            {
                var id = ids[n];
                var at = new Vector3(n * 40, -Info(id).ground_z_m, 0);
                var go = Place(id, at); Verify(id, go); Sockets(id, go);
                var foot = new Vector3(at.x, 0, at.z);
                UpTheSteps(id, foot); Walls(id, foot);
                if (id.StartsWith("VL03_")) OverTheRubble(id, foot);
                var b = LodBounds(go);
                var person = Person(foot + new Vector3(-(b.extents.x + .6f), 0, -2f));
                var both = b; both.Encapsulate(person.GetComponent<Renderer>().bounds);
                float d = both.size.magnitude * 1.25f; var c = both.center;
                Shot(id + "_three_quarter", c, c + new Vector3(.75f, .45f, -.85f).normalized * d, 35);
                Shot(id + "_front", c, c + new Vector3(0, .12f, -1).normalized * d, 35);
                Shot(id + "_back_right", c, c + new Vector3(.85f, .4f, .75f).normalized * d, 35);
                person.SetActive(false);
                var on = Person(foot + new Vector3(-.6f, .54f, -3.1f));       // on the porch, where the player stands at the door
                var dc = foot + new Vector3(0, 1.4f, -3.2f);
                Shot(id + "_porch", dc, dc + new Vector3(.55f, .25f, -1).normalized * 6.5f, 40);
                UnityEngine.Object.DestroyImmediate(on);
                var det = go.GetComponentsInChildren<Renderer>(true).Where(r => r.name.Contains("_Detail_")).ToArray();
                if (det.Length > 0)
                {
                    foreach (var r in det) r.enabled = false;
                    Shot(id + "_porch_no_detail", dc, dc + new Vector3(.55f, .25f, -1).normalized * 6.5f, 40);
                    foreach (var r in det) r.enabled = true;
                }
                // LOD1 / LOD2 as they look from the distances where the LODGroup switches to them
                var group = go.GetComponent<LODGroup>(); var lods = group.GetLODs();
                for (int lv = 1; lv < 3; lv++)
                {
                    for (int k = 0; k < 3; k++) foreach (var r in lods[k].renderers) r.enabled = k == lv;
                    Shot($"{id}_LOD{lv}", c, c + new Vector3(.75f, .45f, -.85f).normalized * d, 35);
                }
                for (int k = 0; k < 3; k++) foreach (var r in lods[k].renderers) r.enabled = true;
            }
            File.WriteAllText(Path.Combine(Out, "unity-verify-report.txt"), string.Join("\n", Report) + $"\n\nUnity {Application.unityVersion}; failed checks: {failed}; editor batch check only, not placed in the main scene, not played\n");
            Debug.Log("VILLAGE_HOUSES_" + (failed == 0 ? "PASS" : "FAIL") + "\n" + string.Join("\n", Report));
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
            importer.bakeAxisConversion = true; importer.isReadable = true;
            importer.materialImportMode = ModelImporterMaterialImportMode.ImportViaMaterialDescription;     // keeps the FBX slot names (M_<id>_Main ...) to map onto
            importer.materialLocation = ModelImporterMaterialLocation.InPrefab;
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
                ti.wrapMode = path.Contains("VL_RoofTiles_") ? TextureWrapMode.Repeat : TextureWrapMode.Clamp;
                ti.SaveAndReimport();
            }
        }

        static Texture2D Tex(string id, string file) => AssetDatabase.LoadAssetAtPath<Texture2D>($"{Root}/{id}/Textures/{file}");

        static string Prefix(string id, string slot) => slot == "Main" ? id : slot == "RoofTiles" ? "VL_RoofTiles" : $"{id}_{slot}";

        static Material Mat(string id, string slot)
        {
            var path = $"{Root}/{id}_{slot}.mat";
            var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (mat == null) { mat = new Material(Shader.Find("Universal Render Pipeline/Lit")); AssetDatabase.CreateAsset(mat, path); }
            var p = Prefix(id, slot);
            mat.SetTexture("_BaseMap", Tex(id, p + "_BaseColor.png")); mat.SetColor("_BaseColor", Color.white);
            mat.SetTexture("_BumpMap", Tex(id, p + "_Normal.png")); mat.EnableKeyword("_NORMALMAP");
            mat.SetTexture("_MetallicGlossMap", Tex(id, p + "_MetallicSmoothness.png")); mat.EnableKeyword("_METALLICSPECGLOSSMAP"); mat.SetFloat("_Smoothness", 1);
            EditorUtility.SetDirty(mat); return mat;
        }

        static readonly Dictionary<string, string> unmapped = new Dictionary<string, string>();

        static GameObject Place(string id, Vector3 position)
        {
            var go = (GameObject)PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>(Fbx(id)));
            PrefabUtility.UnpackPrefabInstance(go, PrefabUnpackMode.Completely, InteractionMode.AutomatedAction);
            go.transform.position = position;
            var mats = Slots.ToDictionary(s => s, s => Mat(id, s));
            foreach (var r in go.GetComponentsInChildren<Renderer>(true))
            {
                if (r.name == id + "_Collision") { r.enabled = false; continue; }
                r.sharedMaterials = r.sharedMaterials.Select(m =>
                {
                    var name = m != null ? m.name : "";
                    var slot = Slots.FirstOrDefault(s => name.EndsWith("_" + s));
                    if (slot == null) { unmapped[r.name] = name; slot = "Main"; }
                    return mats[slot];
                }).ToArray();
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
            }
            var body = go.GetComponentsInChildren<Renderer>(true).FirstOrDefault(r => r.name == id + "_LOD0");
            var names = body != null ? body.sharedMaterials.Select(m => m.name).ToArray() : new string[0];
            Check(names.Length == 4 && Slots.All(s => names.Contains($"{id}_{s}")),
                  $"{id}: {id}_LOD0 has the four material slots Main / Stone / Wood / RoofTiles, each mapped from its FBX slot name ({string.Join(", ", names)})");
            Check(!unmapped.Keys.Any(k => k.StartsWith(id)), $"{id}: every FBX material slot name was recognised" + (unmapped.Count > 0 ? " (unmapped: " + string.Join("; ", unmapped.Select(kv => kv.Key + "=" + kv.Value)) + ")" : ""));
            foreach (var d in info.detailObjects ?? new string[0])
                Check(Enumerable.Range(0, 3).All(i => mfs.Any(m => m.name == $"{d}_LOD{i}")), $"{id}: {d} present at LOD0/1/2 as its own object (can be switched off)");
            var col = go.GetComponentsInChildren<MeshCollider>(true).FirstOrDefault(c => c.name == id + "_Collision");
            Check(info.collision && col != null && col.sharedMesh.triangles.Length > 0, $"{id}: {id}_Collision imported as MeshCollider ({(col ? col.sharedMesh.triangles.Length / 3 : 0)} triangles), renderer hidden");
            if (col != null) { var box = col.bounds; var all = b; all.Expand(.1f); Check(all.Contains(box.min) && all.Contains(box.max), $"{id}: the collider stays on the model"); }
            Check(!go.GetComponentsInChildren<Renderer>(true).Any(r => r.enabled && r.sharedMaterials.Any(m => m == null || m.shader.name.Contains("Error"))), $"{id}: no missing or error shaders");
            foreach (var t in Directory.GetFiles(Path.Combine(Repo, "apps", "game", Root, id, "Textures"), "*_BaseColor.png"))
            {
                var tex = Tex(id, Path.GetFileName(t)); if (tex != null) Report.Add($"INFO {id}: texture {tex.name} {tex.width}x{tex.height} (+ Normal, MetallicSmoothness of the same size)");
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

        static Vector2 Stroll(CharacterController cc, Vector3 o, Vector3 dir, int n)
        {
            float lo = 99, hi = -99;
            for (int f = 0; f < n; f++)
            {
                cc.Move(dir * (1.4f / 60f) + Vector3.down * (9.8f / 60f));
                var p = cc.transform.position - o;
                if (f > 20) { lo = Mathf.Min(lo, p.y); hi = Mathf.Max(hi, p.y); }
            }
            return new Vector2(lo, hi);
        }

        // from the path 1 m in front of the bottom step: up the three 0.18 m steps onto the 0.54 m porch, then against the closed door
        static void UpTheSteps(string id, Vector3 o)
        {
            Physics.SyncTransforms(); var cc = Walker();
            foreach (float x in new[] { -.6f, 0f, .6f })
            {
                cc.transform.position = o + new Vector3(x, .02f, -5.7f); Physics.SyncTransforms();
                var feet = Stroll(cc, o, Vector3.forward, 260); var end = cc.transform.position - o;
                Check(Mathf.Abs(end.y - .54f) < .04f && end.z > -3.0f && end.z < -2.61f - .2f && Mathf.Abs(end.x - x) < .15f,
                      $"{id}: walker on x {x:F1} climbs the steps onto the porch and stops at the closed door (end z {end.z:F2} m, feet {end.y:F3} m, highest {feet.y:F3} m)");
            }
            UnityEngine.Object.DestroyImmediate(cc.gameObject);
        }

        // pushed at the back, left and right walls from outside (on the ground): stops outside the wall line (2.61 / 3.61 m)
        static void Walls(string id, Vector3 o)
        {
            Physics.SyncTransforms(); var cc = Walker();
            var tests = new List<(string what, Vector3 start, Vector3 dir, Func<Vector3, bool> ok)>
            {
                ("back wall", new Vector3(-1.5f, .02f, 4.6f), Vector3.back, p => p.z > 2.61f + .2f),
                ("back wall", new Vector3(1.8f, .02f, 4.6f), Vector3.back, p => p.z > 2.61f + .2f),
                ("left wall", new Vector3(-5.6f, .02f, 0f), Vector3.right, p => p.x < -3.61f - .2f),
            };
            if (!id.StartsWith("VL03_")) tests.Add(("right wall", new Vector3(5.6f, .02f, 0f), Vector3.left, p => p.x > 3.61f + .2f));
            foreach (var t in tests)
            {
                cc.transform.position = o + t.start; Physics.SyncTransforms();
                var feet = Stroll(cc, o, t.dir, 240); var end = cc.transform.position - o;
                Check(t.ok(end), $"{id}: a walker pushed at the {t.what} from outside stops outside it (end x {end.x:F2}, z {end.z:F2} m, feet {feet.x:F3}-{feet.y:F3} m)");
            }
            UnityEngine.Object.DestroyImmediate(cc.gameObject);
        }

        // VL03: from outside the fallen right wall, three lines across the heap: up the rubble ramp, stopped at the old wall line,
        // then back down the way it came (it is not caught in the heap)
        static void OverTheRubble(string id, Vector3 o)
        {
            Physics.SyncTransforms(); var cc = Walker();
            foreach (float z in new[] { -.4f, .5f, 1.4f })
            {
                cc.transform.position = o + new Vector3(6.0f, .02f, z); Physics.SyncTransforms();
                var feet = Stroll(cc, o, Vector3.left, 260); var mid = cc.transform.position - o;
                Stroll(cc, o, Vector3.right, 260); var back = cc.transform.position - o;
                Check(mid.x > 3.61f + .2f && back.x > 5.5f && back.y < .05f,
                      $"{id}: on z {z:F1} a walker goes up the rubble, stops outside the fallen wall's line (x {mid.x:F2} m, feet up to {feet.y:F3} m) and walks back off it (x {back.x:F2} m, feet {back.y:F3} m)");
            }
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
