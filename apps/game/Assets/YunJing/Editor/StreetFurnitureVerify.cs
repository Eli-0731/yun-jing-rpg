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
    // Unity check of the 11/08 package A ST01-ST06 mountain-city street furniture (art/exports/mountain-street-a, Johnnnny0823).
    // Imports every ST_*.fbx (and the MC01_*.fbx used by the 20 m street sample), the shared MC01 trim sheet and the small
    // street-furniture sheet, builds the four URP materials named in model_info (M_MountainStreet_Trim / _Glow, M_StreetFurniture
    // / _Glow, the glow ones emissive), maps them by FBX material name, adds LODGroups and mesh colliders, compares each module
    // with its model_info.json (size, bounds, LOD triangles, objects, materials, sockets, collision), probes the colliders that
    // matter (bench seat, gutter floor, railing, cascade steps), and places the street from st-street-assembly.json.
    // Needs a graphics device (no -nographics):
    //   Unity -batchmode -quit -projectPath apps/game -executeMethod YunJing.Editor.StreetFurnitureVerify.Run -logFile <log>
    // Output: art/previews/mountain-street-a/unity/*.png and report.txt; the run fails when a check fails.
    public static class StreetFurnitureVerify
    {
        const string Models = "Assets/YunJing/Models/StreetFurniture";   // copied from art/exports, gitignored
        const string Pkg = "mountain-street-a";
        static string Repo => Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", ".."));
        static string Exports => Path.Combine(Repo, "art/exports", Pkg);
        static string Mc01 => Path.Combine(Repo, "art/exports/mountain-street-houses-a");
        static string Out => Path.Combine(Repo, "art/previews", Pkg, "unity");
        static readonly List<string> Report = new List<string>();
        static int failures;
        static readonly Dictionary<string, Material> Mats = new Dictionary<string, Material>();
        static float sx = 1;   // Blender +X -> Unity sx * X, measured on the asymmetric ST06_E (buttress on Blender +X)

        [Serializable] class Lod { public int lod, triangles, objects, materials; }
        [Serializable] class Socket { public string name; public float[] location_m; }
        [Serializable] class Info { public string id, collision; public float[] dimensions_m, bounds_min_m; public Lod[] lods; public string[] materials, glowObjects; public Socket[] sockets; }
        [Serializable] class Part { public string id; public float[] pos; public float rotZ; }
        [Serializable] class Assembly { public Part[] parts; }

        static string[] Ids => Directory.GetFiles(Exports, "ST_*.fbx").Select(f => Path.GetFileNameWithoutExtension(f).Substring(3)).OrderBy(s => s).ToArray();

        public static void Run()
        {
            Report.Clear(); failures = 0; Directory.CreateDirectory(Out);
            Import();
            QingxiUrpUpgrade.EnsurePipeline();
            Materials();
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene);
            Report.Add($"Unity {Application.unityVersion}, pipeline {GraphicsSettings.currentRenderPipeline?.name ?? "built-in"}");
            Measure();
            foreach (var id in Ids) Inspect(id, JsonUtility.FromJson<Info>(File.ReadAllText(Path.Combine(Exports, $"ST_{id}.model_info.json"))));
            Probes();
            Shots();
            File.WriteAllLines(Path.Combine(Out, "report.txt"), Report);
            foreach (var line in Report) Debug.Log("ST " + line);
            if (failures > 0) throw new Exception($"ST_VERIFY {failures} check(s) failed, see {Out}/report.txt");
            Debug.Log($"ST_VERIFY_DONE all checks passed, output {Out}");
        }

        static void Check(bool ok, string line) { Report.Add((ok ? "PASS " : "FAIL ") + line); if (!ok) failures++; }

        // ------------------------------------------------------------------ import
        static void Import()
        {
            Copy(Exports, Path.Combine(Repo, "apps/game", Models), "ST_*.fbx");
            Copy(Mc01, Path.Combine(Repo, "apps/game", Models), "MC01_*.fbx");
            Copy(Path.Combine(Repo, "art/textures/mountain-street-houses-a"), Path.Combine(Repo, "apps/game", Models, "Textures"), "T_MountainStreet_*.png");
            Copy(Path.Combine(Repo, "art/textures", Pkg), Path.Combine(Repo, "apps/game", Models, "Textures"), "T_StreetFurniture_*.png");
            AssetDatabase.Refresh();
            foreach (var guid in AssetDatabase.FindAssets("t:Model", new[] { Models }))
            {
                var importer = (ModelImporter)AssetImporter.GetAtPath(AssetDatabase.GUIDToAssetPath(guid));
                if (importer.bakeAxisConversion && importer.materialImportMode == ModelImporterMaterialImportMode.ImportStandard && importer.materialLocation == ModelImporterMaterialLocation.InPrefab) continue;
                importer.bakeAxisConversion = true; importer.importCameras = false; importer.importLights = false; importer.addCollider = false;
                importer.importAnimation = false; importer.materialImportMode = ModelImporterMaterialImportMode.ImportStandard;
                importer.materialLocation = ModelImporterMaterialLocation.InPrefab; importer.importTangents = ModelImporterTangents.CalculateMikk;
                importer.SaveAndReimport();
            }
            foreach (var guid in AssetDatabase.FindAssets("t:Texture2D", new[] { Models }))
            {
                var path = AssetDatabase.GUIDToAssetPath(guid);
                var ti = (TextureImporter)AssetImporter.GetAtPath(path);
                bool normal = path.EndsWith("_Normal.png"), linear = normal || path.EndsWith("_MetallicSmoothness.png");
                var type = normal ? TextureImporterType.NormalMap : TextureImporterType.Default;
                if (ti.textureType == type && ti.sRGBTexture == !linear) continue;
                ti.textureType = type; ti.sRGBTexture = !linear; ti.mipmapEnabled = true; ti.SaveAndReimport();
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
                if (!File.Exists(target) || new FileInfo(target).Length != new FileInfo(file).Length || File.GetLastWriteTimeUtc(target) < File.GetLastWriteTimeUtc(file))
                    File.Copy(file, target, true);
            }
        }

        static int PngSize(string file) { var png = File.ReadAllBytes(file); return (png[16] << 24) | (png[17] << 16) | (png[18] << 8) | png[19]; }

        static void Materials()
        {
            Texture2D T(string name) => AssetDatabase.LoadAssetAtPath<Texture2D>($"{Models}/Textures/{name}.png");
            foreach (var (set, src, size) in new[] { ("MountainStreet", "mountain-street-houses-a", 2048), ("StreetFurniture", Pkg, 1024) })
            {
                var alb = T($"T_{set}_Albedo"); var nrm = T($"T_{set}_Normal"); var ms = T($"T_{set}_MetallicSmoothness"); var em = T($"T_{set}_Emission");
                Check(alb && nrm && ms && em, $"T_{set}_*: Albedo / Normal / MetallicSmoothness / Emission imported");
                if (!(alb && nrm && ms && em)) continue;
                int sw = PngSize(Path.Combine(Repo, "art/textures", src, alb.name + ".png"));
                Check(sw == size && alb.width == Math.Min(sw, 1024), $"{alb.name}: source {sw}, imported {alb.width} x {alb.height} (QingxiImportBudget caps model textures at 1024)");
                foreach (var glow in new[] { false, true })
                {
                    var name = $"M_{set}" + (glow ? "_Glow" : (set == "MountainStreet" ? "_Trim" : ""));
                    var path = $"{Models}/{name}.mat"; var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
                    if (mat == null) { mat = new Material(Shader.Find("Universal Render Pipeline/Lit")); AssetDatabase.CreateAsset(mat, path); }
                    mat.enableInstancing = true; Mats[name] = mat;
                    mat.SetTexture("_BaseMap", alb); mat.SetColor("_BaseColor", Color.white);
                    mat.SetTexture("_BumpMap", nrm); mat.SetFloat("_BumpScale", 1); mat.EnableKeyword("_NORMALMAP");
                    mat.SetTexture("_MetallicGlossMap", ms); mat.EnableKeyword("_METALLICSPECGLOSSMAP"); mat.SetFloat("_Smoothness", 1);
                    if (glow)
                    {
                        mat.SetTexture("_EmissionMap", em); mat.SetColor("_EmissionColor", Color.white * 2.5f); mat.EnableKeyword("_EMISSION");
                        mat.globalIlluminationFlags = MaterialGlobalIlluminationFlags.BakedEmissive;
                    }
                    EditorUtility.SetDirty(mat);
                }
            }
            AssetDatabase.SaveAssets();
        }

        static Material Map(Material m)
        {
            if (m == null) return Mats["M_MountainStreet_Trim"];
            foreach (var kv in Mats.OrderByDescending(k => k.Key.Length)) if (m.name.StartsWith(kv.Key)) return kv.Value;
            return null;
        }

        static GameObject Place(string file, Vector3 at, float yaw, Transform parent = null)
        {
            var go = (GameObject)PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>($"{Models}/{file}.fbx"));
            go.transform.SetPositionAndRotation(at, Quaternion.Euler(0, yaw, 0)); if (parent) go.transform.SetParent(parent, true);
            foreach (var r in go.GetComponentsInChildren<Renderer>(true))
            {
                if (r.name.Contains("_Collision")) { r.enabled = false; continue; }
                r.sharedMaterials = r.sharedMaterials.Select(Map).ToArray();
            }
            // the FBX importer may already add a LODGroup for _LODn names; fill it either way
            var lg = go.GetComponent<LODGroup>() ?? go.AddComponent<LODGroup>();
            float[] cut = { .30f, .10f, .015f };
            lg.SetLODs(Enumerable.Range(0, 3).Select(i => new LOD(cut[i], go.GetComponentsInChildren<Renderer>().Where(r => r.name.EndsWith("_LOD" + i)).ToArray())).ToArray());
            var col = go.GetComponentsInChildren<MeshFilter>(true).FirstOrDefault(m => m.name.EndsWith("_Collision"));
            if (col != null && col.GetComponent<MeshCollider>() == null) col.gameObject.AddComponent<MeshCollider>().sharedMesh = col.sharedMesh;
            Physics.SyncTransforms();
            return go;
        }

        static Transform Node(GameObject go, string name) => go.GetComponentsInChildren<Transform>(true).FirstOrDefault(t => t.name == name);
        static Renderer[] Level(GameObject go, int i) => go.GetComponentsInChildren<Renderer>(true).Where(r => r.name.EndsWith("_LOD" + i)).ToArray();
        static int Tris(IEnumerable<Renderer> rs) => rs.Sum(r => { var m = r.GetComponent<MeshFilter>().sharedMesh; return Enumerable.Range(0, m.subMeshCount).Sum(s => (int)m.GetIndexCount(s)) / 3; });
        static Bounds Box(IEnumerable<Renderer> rs) { var a = rs.ToArray(); var b = a[0].bounds; foreach (var r in a) b.Encapsulate(r.bounds); return b; }

        static void Measure()
        {
            var go = Place("ST_ST06_E", Vector3.zero, 0); var c = Box(Level(go, 0)).center.x; UnityEngine.Object.DestroyImmediate(go);
            sx = c > 0 ? 1 : -1;
            Report.Add($"INFO axis: Blender +X -> Unity {(sx > 0 ? "+X" : "-X")}, Blender +Y -> Unity +Z, Blender +Z -> Unity +Y (ST06_E bounds centre x = {c:0.000})");
        }
        static Vector3 U(float[] p) => new Vector3(sx * p[0], p[2], p[1]);
        static float Yaw(float rotZ) => -sx * rotZ;

        // ------------------------------------------------------------------ checks
        static void Inspect(string id, Info info)
        {
            var go = Place($"ST_{id}", Vector3.zero, 0);
            var lod0 = Level(go, 0); var b = Box(lod0); var d = info.dimensions_m;
            Check(Mathf.Abs(b.size.x - d[0]) < .02f && Mathf.Abs(b.size.z - d[1]) < .02f && Mathf.Abs(b.size.y - d[2]) < .02f,
                $"{id}: imported size {b.size.x:0.000} x {b.size.z:0.000} x {b.size.y:0.000} m matches model_info {d[0]} x {d[1]} x {d[2]}");
            Check(Mathf.Abs(b.min.y - info.bounds_min_m[2]) < .01f, $"{id}: lowest point y = {b.min.y:0.000} (model_info {info.bounds_min_m[2]})");
            var tris = Enumerable.Range(0, 3).Select(i => Tris(Level(go, i))).ToArray();
            Check(Enumerable.Range(0, 3).All(i => Mathf.Abs(tris[i] - info.lods[i].triangles) <= info.lods[i].triangles * .01f + 2),
                $"{id}: triangles LOD0/1/2 = {tris[0]} / {tris[1]} / {tris[2]}, model_info {info.lods[0].triangles} / {info.lods[1].triangles} / {info.lods[2].triangles}");
            Check(lod0.Length == info.lods[0].objects, $"{id}: {lod0.Length} LOD0 objects (model_info {info.lods[0].objects})");
            var used = lod0.SelectMany(r => r.sharedMaterials).ToArray();
            Check(used.All(m => m != null), $"{id}: every FBX material slot mapped to a shared URP material");
            var names = used.Where(m => m).Select(m => m.name).Distinct().OrderBy(s => s).ToArray();
            Check(names.SequenceEqual(info.materials.OrderBy(s => s)), $"{id}: materials {string.Join(", ", names)} (model_info {string.Join(", ", info.materials)})");
            foreach (var g in info.glowObjects ?? new string[0])
            {
                var r = Node(go, g)?.GetComponent<Renderer>();
                Check(r && r.sharedMaterials.All(m => m && m.name.EndsWith("_Glow") && m.IsKeywordEnabled("_EMISSION")), $"{id}: {g} on an emissive _Glow material");
            }
            foreach (var s in info.sockets ?? new Socket[0])
            {
                var t = Node(go, s.name); var want = U(s.location_m);
                Check(t && Vector3.Distance(t.position, want) < .02f, $"{id}: {s.name} at {(t ? t.position.ToString("0.00") : "missing")} (Blender {string.Join(", ", s.location_m)})");
            }
            var lods = go.GetComponent<LODGroup>().GetLODs();
            Check(lods.Length == 3 && lods.All(l => l.renderers.Length == lod0.Length), $"{id}: LODGroup 3 levels x {lod0.Length} renderers");
            var col = go.GetComponentsInChildren<MeshCollider>(true).FirstOrDefault();
            if (info.collision.StartsWith("none")) Check(col == null, $"{id}: no collision (hanging piece)");
            else Check(col != null && col.sharedMesh.triangles.Length > 0, $"{id}: collision imported as MeshCollider ({(col ? col.sharedMesh.triangles.Length / 3 : 0)} tris), render hidden");
            UnityEngine.Object.DestroyImmediate(go);
        }

        static bool Down(Vector3 from, out RaycastHit hit) => Physics.Raycast(from + Vector3.up * 3, Vector3.down, out hit, 10);

        static void Probes()
        {
            // bench: the seat collider is at the seat height in the middle and at both sitting places
            var go = Place("ST_ST04", Vector3.zero, 0);
            foreach (var x in new[] { -.42f, 0f, .42f })
                Check(Down(new Vector3(x, 0, 0), out var h) && Mathf.Abs(h.point.y - .48f) < .03f, $"ST04 seat: ray at x = {x:0.00} hits collision at {h.point.y:0.000} m (seat .48)");
            UnityEngine.Object.DestroyImmediate(go);
            // gutter: the channel floor is 0.18 below the 0.3 m rim, the rims are 0.3
            go = Place("ST_ST03_S", Vector3.zero, 0);
            Check(Down(new Vector3(.3f, 0, 0), out var f) && Mathf.Abs(f.point.y - .12f) < .02f, $"ST03_S: channel floor collision at {f.point.y:0.000} m (.12)");
            Check(Down(new Vector3(.3f, 0, -.18f), out var rim) && Mathf.Abs(rim.point.y - .3f) < .02f, $"ST03_S: rim collision at {rim.point.y:0.000} m (.30)");
            UnityEngine.Object.DestroyImmediate(go);
            // cascade: eleven floor steps, each 0.182 lower along Blender +X
            go = Place("ST_ST03_D", Vector3.zero, 0); var ys = new List<float>();
            for (int k = 0; k < 11; k++) { Down(new Vector3(sx * (-2f + (k + .5f) * 4f / 11), 0, 0), out var s); ys.Add(s.collider ? s.point.y : float.NaN); }
            var steps = ys.Zip(ys.Skip(1), (a, c) => a - c).ToArray();
            Check(ys.All(y => !float.IsNaN(y)) && steps.All(s => Mathf.Abs(s - 2f / 11) < .01f) && Mathf.Abs(ys[0] - (.12f + 2f)) < .02f,
                $"ST03_D: floor steps {string.Join(" ", ys.Select(y => y.ToString("0.00")))} m, each {2f / 11:0.000} lower");
            UnityEngine.Object.DestroyImmediate(go);
            // railing: a 1.75 m capsule walking into the panel is stopped
            go = Place("ST_ST06_S", Vector3.zero, 0);
            foreach (var hgt in new[] { .3f, .9f })
                Check(Physics.Raycast(new Vector3(0, hgt, -1), Vector3.forward, out var r, 2) && Mathf.Abs(r.point.z) < .08f, $"ST06_S: horizontal ray at {hgt} m stops at the railing (z = {r.point.z:0.000})");
            Check(Physics.CapsuleCast(new Vector3(0, .35f, -1), new Vector3(0, 1.4f, -1), .35f, Vector3.forward, out var cap, 2), $"ST06_S: 1.75 m capsule moving into the panel is stopped at z = {cap.point.z:0.000}");
            UnityEngine.Object.DestroyImmediate(go);
        }

        // ------------------------------------------------------------------ renders
        static Camera cam; static RenderTexture target; static Material groundMat, rulerMat;

        static void Setup()
        {
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene);
            var sun = new GameObject("Sun").AddComponent<Light>(); sun.type = LightType.Directional; sun.shadows = LightShadows.Soft;
            sun.transform.rotation = Quaternion.Euler(38, -40, 0); sun.color = new Color(1, .86f, .66f); sun.intensity = 1.7f;
            RenderSettings.ambientMode = AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = new Color(.52f, .60f, .74f); RenderSettings.ambientEquatorColor = new Color(.50f, .50f, .48f); RenderSettings.ambientGroundColor = new Color(.30f, .27f, .22f);
            var ground = GameObject.CreatePrimitive(PrimitiveType.Plane); ground.transform.localScale = Vector3.one * 12;
            groundMat = Flat("ground", new Color(.40f, .38f, .33f)); ground.GetComponent<Renderer>().sharedMaterial = groundMat;
            rulerMat = Flat("ruler", new Color(.30f, .42f, .55f));
            cam = new GameObject("Review Camera").AddComponent<Camera>(); cam.nearClipPlane = .05f; cam.farClipPlane = 400;
            cam.clearFlags = CameraClearFlags.SolidColor; cam.backgroundColor = new Color(.62f, .72f, .86f);
            UnityEngine.Rendering.Universal.CameraExtensions.GetUniversalAdditionalCameraData(cam).renderPostProcessing = true;
            target = new RenderTexture(1600, 1200, 24) { antiAliasing = 4 }; cam.targetTexture = target;
        }

        static void Shots()
        {
            var front = Vector3.back; var side = Vector3.Cross(Vector3.up, front);
            Setup();
            foreach (var id in Ids)
            {
                var lift = id.StartsWith("ST02") ? 2.6f : 0f;   // hanging string: hook tips at 2.6 m
                var go = Place($"ST_{id}", Vector3.up * lift, 0); var b = Box(Level(go, 0)); var ruler = Ruler(new Vector3(b.max.x + .5f, 0, b.min.z - .4f));
                Frame($"modules/{id}", b, (front - side * .8f).normalized + Vector3.up * .5f);
                UnityEngine.Object.DestroyImmediate(ruler); UnityEngine.Object.DestroyImmediate(go);
            }
            var asm = JsonUtility.FromJson<Assembly>(File.ReadAllText(Path.Combine(Exports, "st-street-assembly.json")));
            var root = new GameObject("ST street"); int n = 0;
            foreach (var p in asm.parts)
            {
                var pre = p.id.Split('-')[0]; var file = pre == "MC01" ? "MC01_" + p.id.Substring(5).Replace('-', '_') : "ST_" + p.id.Replace('-', '_');
                if (!File.Exists(Path.Combine(Repo, "apps/game", Models, file + ".fbx"))) { Check(false, $"street: part {p.id} has no FBX"); continue; }
                Place(file, U(p.pos), Yaw(p.rotZ), root.transform); n++;
            }
            Check(n == asm.parts.Length, $"street: {n} / {asm.parts.Length} parts placed from st-street-assembly.json");
            Physics.SyncTransforms();
            // the bench and the railing work in place: stand on the street in front of the bench, walk toward the cliff
            Check(Physics.Raycast(U(new[] { -2.2f, -4.0f, 1.0f }), U(new[] { 0f, -1f, 0f }) - U(new[] { 0f, 0f, 0f }), out var rr, 3) && rr.distance < 2.2f,
                $"street: walking from the street toward the cliff at x = -2.2 hits the bench / railing after {rr.distance:0.00} m");
            var rs = root.GetComponentsInChildren<Renderer>().Where(r => r.enabled && r.name.EndsWith("_LOD0")).ToArray(); var ab = Box(rs);
            Frame("assembly/street-overview", ab, (front - side * .6f).normalized + Vector3.up * .7f, .9f);
            Shot("assembly/street-eye-1p7m", U(new[] { -11.5f, -3.6f, 1.7f }), U(new[] { 2.0f, -1.0f, 2.6f }), 60);
            Shot("assembly/railing-side", U(new[] { -6.5f, -1.2f, 1.9f }), U(new[] { -2.5f, -5.2f, .7f }), 50);
            Shot("assembly/stair-cascade", U(new[] { 13.8f, -4.6f, 2.6f }), U(new[] { 9.4f, 1.6f, 1.3f }), 50);
            UnityEngine.Object.DestroyImmediate(root);
            Report.Add($"INFO renders written to art/previews/{Pkg}/unity");
        }

        static GameObject Ruler(Vector3 at)
        {
            var r = GameObject.CreatePrimitive(PrimitiveType.Capsule);
            UnityEngine.Object.DestroyImmediate(r.GetComponent<Collider>());
            r.transform.position = at + Vector3.up * .875f; r.transform.localScale = new Vector3(.42f, .875f, .42f);
            r.GetComponent<Renderer>().sharedMaterial = rulerMat; return r;
        }

        static void Frame(string file, Bounds b, Vector3 dir, float pad = 1.2f)
        {
            float radius = b.extents.magnitude * pad, dist = radius / Mathf.Sin(30 * .5f * Mathf.Deg2Rad);
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
            var path = $"{Models}/{name}.mat"; var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (mat == null) { mat = new Material(Shader.Find("Universal Render Pipeline/Lit")); AssetDatabase.CreateAsset(mat, path); }
            mat.SetColor("_BaseColor", color); mat.SetFloat("_Smoothness", .1f); return mat;
        }
    }
}
