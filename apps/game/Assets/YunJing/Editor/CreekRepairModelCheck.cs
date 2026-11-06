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
    // Work pack B-56h model check: imports the art/exports/creek-repair-b FBXs into a gitignored folder, checks sizes against
    // model_info.json, LODGroup, _Collision, the separate Gate / Slip / TeaCup objects and the 0.3 m gate lift, then takes
    // URP captures. Writes artifacts/creek-repair-unity/ (report and PNGs). Run with -executeMethod YunJing.Editor.CreekRepairModelCheck.Run
    public static class CreekRepairModelCheck
    {
        const string Root = "Assets/YunJing/Generated/CreekRepairB";
        static string Repo => Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", ".."));
        static string Exports => Path.Combine(Repo, "art", "exports", "creek-repair-b");
        static string Out => Path.Combine(Repo, "artifacts", "creek-repair-unity");
        static readonly string[] Ids = { "CR05_WorkShelter", "CR09_A_RopeGate", "CR09_B_TenonGate", "CR12_RankingBoard",
            "CR03_StonePile", "CR03_TimberRack", "CR03_MudHeap", "CR04_Tools", "CR06_Straight", "CR06_Short", "CR06_Bend", "CR08_Straight", "CR08_Bend", "CR14_WeedClump", "CR15_DitchCross", "CR08_Trestle_080", "CR08_Trestle_150", "CR08_Trestle_250",
            "CR07_Celebration", "CR10_CharmStall", "CR11_NoodleStall", "WM01_MillHouse", "WM02_WaterWheel", "WM04_Millstones", "WM05_WashSteps", "WM07_StoneBridge", "WM09_BambooPavilion" };
        static readonly List<string> Report = new List<string>();
        static int failed;

        [Serializable] class ModelInfo { public float[] dimensions_m; public float[] size_limit_m; public string minTier; public LodTotals lod_totals; }
        [Serializable] class LodTotals { public int LOD0, LOD1, LOD2; }

        static void Check(bool ok, string what) { Report.Add((ok ? "PASS " : "FAIL ") + what); if (!ok) failed++; }

        static void UsePipeline()
        {
            var pipeline = AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>("Assets/YunJing/Generated/URP.asset");
            if (pipeline == null) { ProjectBuilder.Generate(); pipeline = AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>("Assets/YunJing/Generated/URP.asset"); }
            if (GraphicsSettings.defaultRenderPipeline != pipeline) GraphicsSettings.defaultRenderPipeline = pipeline;
            if (QualitySettings.renderPipeline != pipeline) QualitySettings.renderPipeline = pipeline;
            pipeline.shadowDistance = 16;
        }

        public static void Run()
        {
            Report.Clear(); failed = 0;
            UsePipeline();
            Directory.CreateDirectory(Out);
            // the models come in three PRs: this check needs all of them in the checkout
            var missing = Ids.Where(id => !Directory.Exists(Path.Combine(Exports, id))).ToArray();
            if (missing.Length > 0) throw new DirectoryNotFoundException("merge the model PRs first, missing: " + string.Join(", ", missing));
            foreach (var id in Ids) Copy(id);
            AssetDatabase.Refresh();
            foreach (var id in Ids) Configure(id);
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            Lighting();
            var at = new Dictionary<string, Vector3> { { Ids[0], new Vector3(-4.5f, 0, 2) }, { Ids[1], new Vector3(.3f, 0, 0) }, { Ids[2], new Vector3(1.6f, 0, 0) }, { Ids[3], new Vector3(5.2f, 0, 1) } };
            for (int i = 4; i < Ids.Length; i++) at[Ids[i]] = new Vector3(-90 + (i - 4) % 5 * 45, Ids[i] == "WM02_WaterWheel" ? 2.3f : 0, 40 + (i - 4) / 5 * 45);
            var models = Ids.ToDictionary(id => id, id => Place(id, at[id]));
            foreach (var id in Ids) Verify(id, models[id]);
            Gate(Ids[1], models[Ids[1]]); Gate(Ids[2], models[Ids[2]]);
            Slips(models[Ids[3]]);
            Shelter(models[Ids[0]]);
            Extras(models);
            Capture(models);
            File.WriteAllText(Path.Combine(Out, "unity-verify-report.txt"), string.Join("\n", Report) + $"\n\nUnity {Application.unityVersion}; failed checks: {failed}\n");
            Debug.Log("CREEK_MODELS_" + (failed == 0 ? "PASS" : "FAIL") + "\n" + string.Join("\n", Report));
            if (failed > 0 && Application.isBatchMode) EditorApplication.Exit(1);
        }

        // Run after CreekRepairSceneBuilder.Build: in the saved scene the field's collision mesh must not draw and must collide. Then, with only that collision and a flat ground
        // (the test scene has no walking character and its spade probes are not walkable), a 1.75 m capsule walks the ridges and in and out of the water gaps.
        // Scripted steps, an aid only: it does not replace a person walking it with keyboard and mouse.
        public static void FieldWalk()
        {
            Report.Clear(); failed = 0;
            EditorSceneManager.OpenScene("Assets/YunJing/Generated/CreekRepair.unity", OpenSceneMode.Single);
            var field = GameObject.Find("Field_0");
            Check(field != null, "Field_0 is in the scene");
            if (field != null)
            {
                var col = field.GetComponentsInChildren<Transform>(true).Where(t => t.name.EndsWith("_Collision")).ToArray();
                Check(col.Length > 0, "F01 has a _Collision object");
                Check(col.All(t => t.GetComponent<Renderer>() == null || !t.GetComponent<Renderer>().enabled), "F01 collision mesh does not draw");
                Check(col.All(t => t.GetComponent<MeshCollider>() != null), "F01 collision mesh has a MeshCollider");
                var prefab = AssetDatabase.LoadAssetAtPath<GameObject>("Assets/YunJing/Generated/CreekRepairScene/F01_Field/F01_Field.fbx");
                EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
                field = (GameObject)UnityEngine.Object.Instantiate(prefab); field.transform.position = new Vector3(0, -.191f, 0);
                foreach (var t in field.GetComponentsInChildren<Transform>(true).Where(t => t.name.EndsWith("_Collision"))) t.gameObject.AddComponent<MeshCollider>().sharedMesh = t.GetComponent<MeshFilter>().sharedMesh;
                var flat = GameObject.CreatePrimitive(PrimitiveType.Plane); flat.transform.localScale = Vector3.one * 5;
                var cc = new GameObject("WalkProbe", typeof(CharacterController)).GetComponent<CharacterController>(); cc.height = 1.75f; cc.radius = .3f; cc.center = Vector3.up * .875f; cc.stepOffset = .3f; cc.slopeLimit = 50;
                // field local: x across, z along, half sizes 3.003 and 2; banks .5 wide; the gaps are the middle 1.6 m of the near and far banks
                var o = field.transform.position;
                void Walk(string what, params Vector3[] path)
                {
                    cc.enabled = false; cc.transform.position = o + path[0] + Vector3.up * .9f; cc.enabled = true; Physics.SyncTransforms();
                    for (int i = 0; i < 80; i++) cc.Move(Vector3.down * .05f);
                    float lowest = cc.transform.position.y, highest = lowest; bool reached = true;
                    for (int leg = 1; leg < path.Length && reached; leg++)
                    {
                        var goal = o + path[leg]; int steps = 0;
                        while (true)
                        {
                            var d = goal - cc.transform.position; d.y = 0;
                            if (d.magnitude < .12f) break;
                            if (++steps > 800) { reached = false; break; }
                            cc.Move(d.normalized * .035f + Vector3.down * .06f); lowest = Mathf.Min(lowest, cc.transform.position.y); highest = Mathf.Max(highest, cc.transform.position.y);
                        }
                    }
                    var end = cc.transform.position - o;
                    Check(reached && lowest - o.y > -.01f, $"walk {what}: ended at ({end.x:F2}, {end.y:F2}, {end.z:F2}), feet between {lowest - o.y:F3} and {highest - o.y:F3} m from the field base");
                }
                Walk("east ridge end to end", new Vector3(2.72f, 0, -1.72f), new Vector3(2.72f, 0, 1.72f));
                Walk("near ridge, right of the gap", new Vector3(1.2f, 0, -1.75f), new Vector3(2.6f, 0, -1.75f));
                Walk("far ridge, left of the gap", new Vector3(-2.6f, 0, 1.75f), new Vector3(-1.2f, 0, 1.75f));
                Walk("in through the near gap", new Vector3(0, 0, -3.4f), new Vector3(0, 0, 0));
                Walk("out through the far gap", new Vector3(0, 0, 0), new Vector3(0, 0, 3.4f));
                Walk("down off the ridge into the field and back up", new Vector3(2.72f, 0, 0), new Vector3(1, 0, 0), new Vector3(2.72f, 0, 0));
                // the channel banks: a walker coming from outside has to stop at the outer face
                UnityEngine.Object.DestroyImmediate(field);
                void Blocked(string id, Vector3 from, Vector3 to)
                {
                    var piece = (GameObject)UnityEngine.Object.Instantiate(AssetDatabase.LoadAssetAtPath<GameObject>($"{Root}/{id}/{id}_v001.fbx"));
                    var box = piece.GetComponentsInChildren<MeshFilter>(true).FirstOrDefault(m => m.name == id + "_Collision");
                    Check(box != null, $"{id}: has a _Collision");
                    if (box != null)
                    {
                        box.gameObject.AddComponent<MeshCollider>().sharedMesh = box.sharedMesh;
                        cc.enabled = false; cc.transform.position = from + Vector3.up * .1f; cc.enabled = true; Physics.SyncTransforms();
                        var way = (to - from).normalized; float length = (to - from).magnitude; float gone = 0;
                        // every step is kept, with the first place the capsule touches the collision, so a failure can be drawn against the collision section
                        float high = 0; var trace = new List<string>(); string touch = "none";
                        for (int i = 0; i < 400; i++)
                        {
                            var p = cc.transform.position; var step = way * .035f + Vector3.down * .06f;
                            var hit = Physics.CapsuleCastAll(p + Vector3.up * cc.radius, p + Vector3.up * (cc.height - cc.radius), cc.radius, way, .035f + cc.skinWidth).Where(h => h.collider.gameObject != flat && h.distance > 0).OrderBy(h => h.distance).FirstOrDefault();
                            if (touch == "none" && hit.collider != null)
                                touch = $"{{\"step\":{i},\"capsule\":[{p.x:F4},{p.y:F4},{p.z:F4}],\"point\":[{hit.point.x:F4},{hit.point.y:F4},{hit.point.z:F4}],\"normal\":[{hit.normal.x:F3},{hit.normal.y:F3},{hit.normal.z:F3}]}}";
                            var flags = cc.Move(step); p = cc.transform.position;
                            trace.Add($"[{p.x:F4},{p.y:F4},{p.z:F4},{(int)flags}]");
                            gone = Vector3.Dot(p - from, way); high = Mathf.Max(high, p.y);
                        }
                        Check(gone < length / 2 - .3f && high < .12f, $"{id}: stopped at the bank after {gone:F2} of {length:F2} m, feet never above {high:F3} m (skin .08)");
                        Directory.CreateDirectory(Out);
                        File.WriteAllText(Path.Combine(Out, $"walk-trace-{id}-{from.x:F1}_{from.z:F1}.json"), $"{{\"id\":\"{id}\",\"from\":[{from.x:F3},{from.z:F3}],\"to\":[{to.x:F3},{to.z:F3}],\"radius\":{cc.radius},\"height\":{cc.height},\"stepOffset\":{cc.stepOffset},\"skin\":{cc.skinWidth},\"first_touch\":{touch},\"trace\":[{string.Join(",", trace)}]}}");
                    }
                    UnityEngine.Object.DestroyImmediate(piece);
                }
                Blocked("CR06_Straight", new Vector3(-1.5f, 0, 0), new Vector3(1.5f, 0, 0));
                Blocked("CR06_Short", new Vector3(1.5f, 0, 0), new Vector3(-1.5f, 0, 0));
                Blocked("CR06_Bend", new Vector3(-1.32f, 0, 1.32f), new Vector3(.8f, 0, -.8f));
                Blocked("CR15_DitchCross", new Vector3(.6f, 0, -1.5f), new Vector3(.6f, 0, 1.5f));
                Blocked("CR15_DitchCross", new Vector3(1.5f, 0, 1.5f), new Vector3(-1.5f, 0, -1.5f));
                // the other three outer corners, from the other sides: a 0.6 m capsule does not fit the 0.29 m notch between two arms, so each of these meets the corner face
                Blocked("CR15_DitchCross", new Vector3(-.6f, 0, 1.5f), new Vector3(-.6f, 0, -1.5f));
                Blocked("CR15_DitchCross", new Vector3(1.5f, 0, .6f), new Vector3(-1.5f, 0, .6f));
                Blocked("CR15_DitchCross", new Vector3(-1.5f, 0, -.6f), new Vector3(1.5f, 0, -.6f));
                UnityEngine.Object.DestroyImmediate(cc.gameObject);
            }
            Directory.CreateDirectory(Out);
            File.WriteAllText(Path.Combine(Out, "field-walk-report.txt"), string.Join("\n", Report) + $"\n\nUnity {Application.unityVersion}; failed checks: {failed}; scripted CharacterController, not a person\n");
            Debug.Log("CREEK_FIELDWALK_" + (failed == 0 ? "PASS" : "FAIL") + "\n" + string.Join("\n", Report));
            if (failed > 0 && Application.isBatchMode) EditorApplication.Exit(1);
        }

        // The test scene needs only the site models, so it builds without the stall and A3 PRs and without running this check first.
        internal static void ImportForScene()
        {
            var have = Ids.Where(id => Directory.Exists(Path.Combine(Exports, id))).ToArray();
            foreach (var id in have) Copy(id);
            AssetDatabase.Refresh();
            foreach (var id in have) { Configure(id); Mat(id); }
        }

        static void Copy(string id)
        {
            var src = Path.Combine(Exports, id); var dst = Path.Combine(Repo, "apps", "game", Root, id);
            Directory.CreateDirectory(Path.Combine(dst, "Textures"));
            foreach (var file in Directory.GetFiles(src, "*.fbx").Concat(Directory.GetFiles(Path.Combine(src, "Textures"), "*.png")))
                File.Copy(file, Path.Combine(dst, file.Substring(src.Length + 1)), true);
        }

        static void Configure(string id)
        {
            var importer = AssetImporter.GetAtPath($"{Root}/{id}/{id}_v001.fbx") as ModelImporter;
            if (importer == null) throw new FileNotFoundException("FBX not imported", id);
            importer.bakeAxisConversion = true; importer.materialImportMode = ModelImporterMaterialImportMode.None;
            importer.importAnimation = false; importer.importCameras = false; importer.importLights = false; importer.addCollider = false;
            importer.SaveAndReimport();
            if (AssetImporter.GetAtPath($"{Root}/{id}/{id}_water_v001.fbx") is ModelImporter water)
            {
                water.bakeAxisConversion = true; water.materialImportMode = ModelImporterMaterialImportMode.None; water.isReadable = true;
                water.importAnimation = false; water.importCameras = false; water.importLights = false; water.addCollider = false;
                water.SaveAndReimport();
            }
            foreach (var tex in Directory.GetFiles(Path.Combine(Repo, "apps", "game", Root, id, "Textures"), "*.png"))
            {
                var path = $"{Root}/{id}/Textures/{Path.GetFileName(tex)}";
                var ti = AssetImporter.GetAtPath(path) as TextureImporter; if (ti == null) continue;
                bool normal = path.EndsWith("_Normal.png");
                bool data = path.EndsWith("_MetallicSmoothness.png") || path.EndsWith("_Roughness.png") || path.EndsWith("_Metallic.png");
                ti.textureType = normal ? TextureImporterType.NormalMap : TextureImporterType.Default;
                ti.sRGBTexture = !normal && !data; ti.maxTextureSize = 4096; ti.SaveAndReimport();
            }
        }

        static Material Mat(string id)
        {
            var path = $"{Root}/{id}.mat";
            var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (mat == null) { mat = new Material(Shader.Find("Universal Render Pipeline/Lit")); AssetDatabase.CreateAsset(mat, path); }
            string tex(string ch) => $"{Root}/{id}/Textures/{id}_{ch}.png";
            mat.SetTexture("_BaseMap", AssetDatabase.LoadAssetAtPath<Texture2D>(tex("BaseColor"))); mat.SetColor("_BaseColor", Color.white);
            mat.SetTexture("_BumpMap", AssetDatabase.LoadAssetAtPath<Texture2D>(tex("Normal"))); mat.EnableKeyword("_NORMALMAP");
            mat.SetTexture("_MetallicGlossMap", AssetDatabase.LoadAssetAtPath<Texture2D>(tex("MetallicSmoothness"))); mat.EnableKeyword("_METALLICSPECGLOSSMAP"); mat.SetFloat("_Smoothness", 1);
            EditorUtility.SetDirty(mat); return mat;
        }

        static GameObject Place(string id, Vector3 position)
        {
            var go = (GameObject)PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>($"{Root}/{id}/{id}_v001.fbx"));
            PrefabUtility.UnpackPrefabInstance(go, PrefabUnpackMode.Completely, InteractionMode.AutomatedAction);
            go.transform.position = position;
            var mat = Mat(id);
            foreach (var r in go.GetComponentsInChildren<Renderer>(true))
            {
                if (r.name == id + "_Collision") { r.enabled = false; continue; }
                r.sharedMaterials = Enumerable.Repeat(mat, r.sharedMaterials.Length).ToArray();
            }
            if (go.GetComponent<LODGroup>() == null)
            {
                float[] cut = { .25f, .08f, .015f };
                go.AddComponent<LODGroup>().SetLODs(Enumerable.Range(0, 3).Select(i => new LOD(cut[i], go.GetComponentsInChildren<Renderer>(true).Where(r => r.name.EndsWith("_LOD" + i)).ToArray())).ToArray());
            }
            var col = go.GetComponentsInChildren<MeshFilter>(true).FirstOrDefault(m => m.name == id + "_Collision");
            if (col != null) col.gameObject.AddComponent<MeshCollider>().sharedMesh = col.sharedMesh;
            Physics.SyncTransforms();
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
            var b = LodBounds(go);
            float[] want = info.dimensions_m;
            Vector3 size = b.size;   // Blender x, y, z map to Unity x, z, y
            float dx = Mathf.Abs(size.x - want[0]), dy = Mathf.Abs(size.z - want[1]), dz = Mathf.Abs(size.y - want[2]);
            Check(dx < .002f && dy < .002f && dz < .002f, $"{id}: imported size {size.x:F3} x {size.z:F3} x {size.y:F3} m matches model_info (max error {Mathf.Max(dx, dy, dz) * 1000:F1} mm)");
            float[] lim = info.size_limit_m;
            Check(size.x <= lim[0] + .002f && size.z <= lim[1] + .002f && size.y <= lim[2] + .002f, $"{id}: within limit {lim[0]} x {lim[1]} x {lim[2]} m");
            if (id == "WM02_WaterWheel") Check(Mathf.Abs(b.center.y - go.transform.position.y) < .003f, $"{id}: origin at the axle centre");
            else Check(Mathf.Abs(b.min.y - go.transform.position.y) < .002f, $"{id}: base on origin height (min y {b.min.y - go.transform.position.y:F4})");
            Report.Add($"INFO {id}: minTier {info.minTier}");
            Check(Mathf.Abs(b.center.x - go.transform.position.x) < .003f && Mathf.Abs(b.center.z - go.transform.position.z) < .003f, $"{id}: origin at footprint centre");
            var lod = go.GetComponent<LODGroup>();
            Check(lod != null && lod.GetLODs().Length == 3, $"{id}: LODGroup with 3 levels");
            int tri(string s) => go.GetComponentsInChildren<MeshFilter>(true).Where(m => m.name.EndsWith(s)).Sum(m => m.sharedMesh.triangles.Length / 3);
            Report.Add($"INFO {id}: triangles LOD0 {tri("_LOD0")}, LOD1 {tri("_LOD1")}, LOD2 {tri("_LOD2")}");
            // the same final FBX, counted by Unity's importer, against the totals the build wrote
            if (info.lod_totals != null && info.lod_totals.LOD0 > 0)
                Check(tri("_LOD0") == info.lod_totals.LOD0 && tri("_LOD1") == info.lod_totals.LOD1 && tri("_LOD2") == info.lod_totals.LOD2,
                      $"{id}: imported LOD triangles {tri("_LOD0")}/{tri("_LOD1")}/{tri("_LOD2")} equal model_info {info.lod_totals.LOD0}/{info.lod_totals.LOD1}/{info.lod_totals.LOD2}");
            var col = go.GetComponentsInChildren<MeshCollider>(true).FirstOrDefault(c => c.name == id + "_Collision");
            if (id == "CR04_Tools") Report.Add($"INFO {id}: no _Collision, hand tools do not block");
            else Check(col != null && col.sharedMesh.triangles.Length > 0, $"{id}: {id}_Collision imported as MeshCollider ({(col ? col.sharedMesh.triangles.Length / 3 : 0)} triangles), renderer hidden");
            if (col != null)
            {
                var seen = go.GetComponentsInChildren<MeshFilter>(true).Where(m => m.name.EndsWith("_LOD0")).Select(MeshBounds).ToArray(); var all = seen[0]; foreach (var one in seen) all.Encapsulate(one);
                var box = MeshBounds(col.GetComponent<MeshFilter>()); all.Expand(.16f);
                Check(all.Contains(box.min) && all.Contains(box.max), $"{id}: the collider stays on the model");
            }
            bool magenta = go.GetComponentsInChildren<Renderer>(true).Any(r => r.enabled && r.sharedMaterial != null && r.sharedMaterial.shader.name.Contains("Error"));
            Check(!magenta, $"{id}: no error shaders");
        }

        static void Gate(string id, GameObject go)
        {
            var gate = go.GetComponentsInChildren<Transform>(true).FirstOrDefault(t => t.name == id + "_Gate_LOD0");
            Check(gate != null, $"{id}: Gate is its own object");
            if (gate == null) return;
            var r = gate.GetComponent<Renderer>(); float z0 = r.bounds.max.y - go.transform.position.y;
            var open = go.GetComponentsInChildren<Transform>(true).First(t => t.name == "Socket_GateOpen");
            float lift = open.position.y - (gate.position.y);
            Check(Mathf.Abs(lift - .3f) < .002f, $"{id}: Socket_GateOpen is {lift:F3} m above the gate pivot");
            Vector3 p = gate.position; gate.position += Vector3.up * .3f;
            float top = r.bounds.max.y - go.transform.position.y;
            Check(top <= .9005f, $"{id}: top {z0:F3} m closed, {top:F3} m open (limit 0.9)");
            gate.position = p;
            var ports = go.GetComponentsInChildren<Transform>(true).Where(t => t.name.StartsWith("Socket_Port")).ToArray();
            Check(ports.Length == 2 && ports.All(t => Mathf.Abs(t.position.y - go.transform.position.y - .1f) < .002f) && Mathf.Abs(Mathf.Abs(ports[0].position.z - ports[1].position.z) - .5f) < .002f,
                  $"{id}: channel ports at floor 0.10 m, 0.50 m apart along the flow");
        }

        static void Slips(GameObject go)
        {
            var slips = Enumerable.Range(1, 12).Select(i => go.GetComponentsInChildren<Transform>(true).FirstOrDefault(t => t.name == $"CR12_RankingBoard_Slip_{i:00}_LOD0")).ToArray();
            Check(slips.All(s => s != null), "CR12: Slip_01..12 are 12 separate objects");
            if (slips.Any(s => s == null)) return;
            Check(slips.Skip(1).All(s => slips[0].GetComponent<Renderer>().bounds.size.x > s.GetComponent<Renderer>().bounds.size.x), "CR12: Slip_01 is the largest");
            Check(go.GetComponentsInChildren<Transform>(true).Any(t => t.name == "CR12_RankingBoard_TeaCup_LOD0"), "CR12: TeaCup is its own object");
            var cup = go.GetComponentsInChildren<Transform>(true).First(t => t.name == "CR12_RankingBoard_TeaCup_LOD0");
            Check(cup.GetComponent<Renderer>().bounds.min.y - go.transform.position.y > .95f, $"CR12: cup sits on the rail at {cup.GetComponent<Renderer>().bounds.min.y - go.transform.position.y:F3} m");
        }

        static void Shelter(GameObject go)
        {
            foreach (var n in new[] { "Canopy", "Bench", "Crate", "TeaBucket", "Ladle", "Bowl_01", "Bowl_02", "Bowl_03", "Bowl_04" })
                Check(go.GetComponentsInChildren<Transform>(true).Any(t => t.name == $"CR05_WorkShelter_{n}_LOD0"), $"CR05: {n} is its own object");
            // a 1.75 m capsule walks through the middle under the canopy and is stopped only by a post
            var c = go.transform.position; Physics.SyncTransforms();
            Check(!Physics.CheckCapsule(c + new Vector3(0, .32f, -.8f), c + new Vector3(0, 1.45f, -.8f), .3f), "CR05: a 0.3 m radius capsule stands free between the posts");
            Check(Physics.CheckCapsule(c + new Vector3(1.72f, .3f, -1.2f), c + new Vector3(1.72f, 1.45f, -1.2f), .3f), "CR05: the same capsule collides at a post");
        }

        static Bounds MeshBounds(MeshFilter m)
        {
            var b = m.sharedMesh.bounds; var w = new Bounds(m.transform.TransformPoint(b.min), Vector3.zero);
            for (int i = 0; i < 8; i++) w.Encapsulate(m.transform.TransformPoint(new Vector3((i & 1) == 0 ? b.min.x : b.max.x, (i & 2) == 0 ? b.min.y : b.max.y, (i & 4) == 0 ? b.min.z : b.max.z)));
            return w;
        }

        static bool Has(GameObject go, string name) => go.GetComponentsInChildren<Transform>(true).Any(t => t.name == name);

        static void Extras(Dictionary<string, GameObject> m)
        {
            foreach (var id in new[] { "CR03_StonePile", "CR03_TimberRack", "CR03_MudHeap" })
            {
                Check(new[] { "Stage_Low", "Stage_Mid", "Stage_High" }.All(st => Has(m[id], $"{id}_{st}_LOD0")), $"{id}: three stages are separate objects");
                foreach (var st in new[] { "Stage_Low", "Stage_Mid" }) m[id].GetComponentsInChildren<Transform>(true).Where(t => t.name.Contains(st)).ToList().ForEach(t => t.gameObject.SetActive(false));
            }
            foreach (var tool in new[] { "Spade", "Basket", "Tamper", "MortarBucket", "Trowel" })
                Check(Has(m["CR04_Tools"], "CR04_Tools_" + tool + "_LOD0") && Has(m["CR04_Tools"], "Socket_Hand_" + tool), $"CR04: {tool} is its own object with a hand socket");
            foreach (var id in new[] { "CR06_Straight", "CR06_Short", "CR06_Bend", "CR08_Straight", "CR08_Bend" })
            {
                Check(m[id].GetComponentsInChildren<Transform>(true).Count(t => t.name.StartsWith("Socket_Port")) == 2, $"{id}: two ports");
                Check(!m[id].GetComponentsInChildren<Transform>(true).Any(t => t.name.ToLowerInvariant().Contains("water")), $"{id}: no water in the body FBX");
                var waterFbx = AssetDatabase.LoadAssetAtPath<GameObject>($"{Root}/{id}/{id}_water_v001.fbx");
                Check(waterFbx != null && Enumerable.Range(0, 3).All(i => Has(waterFbx, $"{id}_water_LOD{i}")), $"{id}: water is its own FBX with three LODs");
                var water = waterFbx.GetComponentsInChildren<MeshFilter>(true).First(f => f.name.EndsWith("_LOD0")).sharedMesh;
                float vMax = water.uv.Max(u => u.y), uMax = water.uv.Max(u => u.x);
                Check(water.uv.Min(u => u.x) > -.001f && uMax < 1.001f && water.uv.Min(u => u.y) > -.001f && Mathf.Abs(vMax - Mathf.Round(vMax)) < .001f && vMax >= 1, $"{id}: water UV u 0..1 across, v {vMax:F2} m along the flow");
                Check(Mathf.Abs(water.bounds.center.y - .28f) < .005f && water.bounds.size.y < .005f, $"{id}: water sits flat at z 0.28 in the body's coordinates (y {water.bounds.center.y:F3})");
            }
            var cele = m["CR07_Celebration"];
            Check(Enumerable.Range(1, 9).All(i => Has(cele, $"CR07_Celebration_Lantern_{i:00}_LOD0") && Has(cele, $"CR07_Celebration_Lantern_{i:00}_Lit_LOD0")), "CR07: nine lanterns, each with its own _Lit");
            cele.GetComponentsInChildren<Transform>(true).Where(t => t.name.Contains("_Lit_")).ToList().ForEach(t => t.gameObject.SetActive(false));
            var charm = m["CR10_CharmStall"]; int good = 0;
            for (int i = 1; i <= 24; i++)
            {
                var t = charm.GetComponentsInChildren<Transform>(true).FirstOrDefault(x => x.name == $"CR10_CharmStall_CharmString_{i:00}_LOD0");
                if (t != null && Mathf.Abs(t.position.y - t.GetComponent<Renderer>().bounds.max.y) < .03f) good++;
            }
            Check(good == 24, $"CR10: {good} of 24 charm strings are separate with their pivot at the top");
            var noodle = m["CR11_NoodleStall"];
            Check(Has(noodle, "CR11_NoodleStall_Bowl_Full_LOD0") && Has(noodle, "CR11_NoodleStall_Bowl_Empty_LOD0") && Has(noodle, "Socket_Steam"), "CR11: full and empty bowls are separate; Socket_Steam present");
            Check(Has(m["WM01_MillHouse"], "Socket_WheelAxle"), "WM01: Socket_WheelAxle present");
            // the bridge: a capsule rests on the deck, the rail stops it, the road end is reached at both ends
            var br = m["WM07_StoneBridge"].transform.position; Physics.SyncTransforms();
            bool deck(float y, out RaycastHit h) => Physics.Raycast(br + new Vector3(0, 8, y), Vector3.down, out h, 12);
            Check(deck(0, out var mid) && Mathf.Abs(mid.point.y - br.y - 3.2f) < .05f, $"WM07: the collider carries the deck at the crown ({mid.point.y - br.y:F2} m)");
            Check(deck(-5.5f, out var low) && Vector3.Angle(low.normal, Vector3.up) <= 15.01f, $"WM07: ramp slope {Vector3.Angle(low.normal, Vector3.up):F1} degrees");
            Check(!Physics.CheckCapsule(br + new Vector3(0, 3.55f, 0), br + new Vector3(0, 4.6f, 0), .3f), "WM07: a 0.3 m capsule stands free on the crown");
            Check(Physics.CheckCapsule(br + new Vector3(1.2f, 3.55f, 0), br + new Vector3(1.2f, 4.6f, 0), .3f), "WM07: the rail stops the capsule");
            var mill = m["WM01_MillHouse"].transform.position;
            Check(!Physics.CheckCapsule(mill + new Vector3(0, 1.2f, -2.2f), mill + new Vector3(0, 2.2f, -2.2f), .3f), "WM01: the doorway lets a 0.3 m capsule through");
            Check(Physics.CheckCapsule(mill + new Vector3(2.2f, 1.2f, -2.2f), mill + new Vector3(2.2f, 2.2f, -2.2f), .3f), "WM01: the front wall stops it");
        }

        static void Lighting()
        {
            RenderSettings.ambientMode = AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = new Color(.62f, .68f, .7f); RenderSettings.ambientEquatorColor = new Color(.45f, .44f, .38f); RenderSettings.ambientGroundColor = new Color(.2f, .18f, .14f);
            var sun = new GameObject("Sun").AddComponent<Light>(); sun.type = LightType.Directional; sun.intensity = 1.25f;
            sun.color = new Color(1, .96f, .88f); sun.transform.rotation = Quaternion.Euler(36, -38, 0); sun.shadows = LightShadows.Soft;
            var ground = GameObject.CreatePrimitive(PrimitiveType.Plane); ground.name = "Placeholder_Ground"; ground.transform.localScale = Vector3.one * 60; UnityEngine.Object.DestroyImmediate(ground.GetComponent<Collider>());
            var g = new Material(Shader.Find("Universal Render Pipeline/Lit")); g.SetColor("_BaseColor", new Color(.38f, .34f, .26f)); g.SetFloat("_Smoothness", .05f); ground.GetComponent<Renderer>().sharedMaterial = g;
            var cam = new GameObject("Main Camera", typeof(Camera)).GetComponent<Camera>(); cam.tag = "MainCamera"; cam.nearClipPlane = .05f; cam.farClipPlane = 120;
            cam.clearFlags = CameraClearFlags.SolidColor; cam.backgroundColor = new Color(.74f, .82f, .84f);
            cam.GetUniversalAdditionalCameraData().renderPostProcessing = false;
        }

        static void Capture(Dictionary<string, GameObject> models)
        {
            var cam = Camera.main; var rt = new RenderTexture(1280, 720, 24, RenderTextureFormat.ARGB32) { antiAliasing = 4 };
            void Shot(string file, Vector3 target, Vector3 offset, float fov = 35)
            {
                cam.transform.position = target + offset; cam.transform.LookAt(target); cam.fieldOfView = fov; cam.targetTexture = rt; cam.Render();
                RenderTexture.active = rt; var tex = new Texture2D(1280, 720, TextureFormat.RGB24, false); tex.ReadPixels(new Rect(0, 0, 1280, 720), 0, 0); tex.Apply();
                File.WriteAllBytes(Path.Combine(Out, file + ".png"), tex.EncodeToPNG()); UnityEngine.Object.DestroyImmediate(tex);
                RenderTexture.active = null; cam.targetTexture = null; Report.Add("SHOT " + file);
            }
            // Blender front (-Y) imports as Unity -Z, so the front views stand on -Z.
            foreach (var id in Ids)
            {
                var b = LodBounds(models[id]); float d = b.size.magnitude * 1.5f; var c = b.center;
                Shot(id + "_front", c, new Vector3(0, .1f, -1) * d);
                Shot(id + "_three_quarter", c, new Vector3(.7f, .35f, -.85f).normalized * d);
                Shot(id + "_rear", c, new Vector3(-.5f, .25f, .9f).normalized * d);
            }
            T(models[Ids[0]], "CR05_WorkShelter_TeaBucket_LOD0", out var bucket);
            Shot("CR05_tea_closeup", bucket + new Vector3(.25f, .05f, 0), new Vector3(.5f, .75f, -1.5f));
            var s = LodBounds(models[Ids[3]]).center;
            Shot("CR12_slips_closeup", new Vector3(s.x, 1.65f, s.z), new Vector3(.3f, -.15f, -2.1f));
            T(models[Ids[3]], "CR12_RankingBoard_TeaCup_LOD0", out var cup);
            Shot("CR12_cup_closeup", cup + new Vector3(0, .05f, 0), new Vector3(.1f, .22f, -.5f), 30);
            var a = LodBounds(models[Ids[1]]).center;
            Shot("CR09_A_closeup", a, new Vector3(.35f, .28f, -1.05f));
            var gate = models[Ids[2]].GetComponentsInChildren<Transform>(true).First(t => t.name == Ids[2] + "_Gate_LOD0");
            gate.position += Vector3.up * .3f;
            Shot("CR09_B_open_closeup", LodBounds(models[Ids[2]]).center, new Vector3(-.4f, .28f, -1.1f));
            gate.position -= Vector3.up * .3f;
            Flicker(models);
        }

        // A surface fighting another one flips colour and flips back as the camera turns a hair: count pixels that go A, B, A over three frames.
        static void Flicker(Dictionary<string, GameObject> models)
        {
            const int W = 960, H = 540, Frames = 24;
            var cam = Camera.main; var rt = new RenderTexture(W, H, 24, RenderTextureFormat.ARGB32); var tex = new Texture2D(W, H, TextureFormat.RGB24, false); var back = cam.backgroundColor;
            foreach (var id in new[] { "CR10_CharmStall", "CR11_NoodleStall", "CR12_RankingBoard", "CR05_WorkShelter", "WM01_MillHouse", "WM07_StoneBridge", "WM02_WaterWheel", "CR03_TimberRack" })
            {
                if (!models.ContainsKey(id)) continue;
                var b = LodBounds(models[id]);
                foreach (var far in new[] { 1.1f, 2.6f })
                {
                    var look = new float[Frames][]; float d = b.size.magnitude * far; var off = new Vector3(.7f, .35f, -.85f).normalized * d;
                    for (int i = 0; i < Frames; i++)
                    {
                        cam.transform.position = b.center + Quaternion.Euler(0, i * .12f, 0) * off; cam.transform.LookAt(b.center); cam.fieldOfView = 35; cam.targetTexture = rt; cam.Render();
                        RenderTexture.active = rt; tex.ReadPixels(new Rect(0, 0, W, H), 0, 0); tex.Apply(); look[i] = tex.GetPixels().Select(c => c.r * .2126f + c.g * .7152f + c.b * .0722f).ToArray();
                    }
                    RenderTexture.active = null; cam.targetTexture = null; int worst = 0, all = 0;
                    for (int i = 0; i + 2 < Frames; i++)
                    {
                        int n = 0;
                        for (int k = 0; k < look[i].Length; k++) if (Mathf.Abs(look[i][k] - look[i + 1][k]) > .2f && Mathf.Abs(look[i][k] - look[i + 2][k]) < .05f) n++;
                        worst = Mathf.Max(worst, n); all += n;
                    }
                    Report.Add($"FLICKER {id} distance {d:0.0} m: A-B-A pixels per frame mean {all / (float)(Frames - 2):0.0}, worst {worst}, of {W * H}");
                }
            }
            UnityEngine.Object.DestroyImmediate(tex); cam.backgroundColor = back;
        }

        static void T(GameObject go, string name, out Vector3 at)
        {
            at = go.GetComponentsInChildren<Transform>(true).First(t => t.name == name).GetComponent<Renderer>().bounds.center;
        }
    }
}
