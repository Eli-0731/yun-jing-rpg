using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

namespace YunJing.Editor
{
    // Unity check of C's day 1-2 models (art/exports/qingxi-day12-c, Eli-0731): imports the delivered FBX and
    // textures under the game's import budget, builds URP materials, LODGroup and collider from the node names,
    // compares them with model_info.json and renders review shots. Needs a graphics device (no -nographics):
    //   Unity -batchmode -quit -projectPath apps/game -executeMethod YunJing.Editor.QingxiDay12Verify.Run -logFile <log>
    // Output: art/previews/qingxi-day12-c/unity/*.png and report.txt; the run fails when a check fails.
    public static class QingxiDay12Verify
    {
        const string Models = "Assets/YunJing/Models/Day12C";   // copied from art/exports, gitignored
        static readonly string[] Ids = { "RK03", "G01", "TY04", "TY08", "TY09" };
        static readonly float[] Ty04Levels = { 0, .35f, .9f, 1.7f, 2.8f };   // glow_level 0-4, same table as Blender
        static string Repo => Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", ".."));
        static string Out => Path.Combine(Repo, "art/previews/qingxi-day12-c/unity");
        static readonly List<string> Report = new List<string>();
        static int failures;
        static readonly HashSet<string> Checked = new HashSet<string>();
        static Vector3 front = Vector3.back;   // Blender -Y; confirmed from RK03's steps below

        [Serializable] class Info { public float[] dimensions_xyz_m, size_limit_m, light_socket; public int[] triangles_total; }

        public static void Run()
        {
            Report.Clear(); Checked.Clear(); failures = 0;
            Directory.CreateDirectory(Out);
            Import();
            QingxiUrpUpgrade.EnsurePipeline();
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene);
            var json = File.ReadAllText(Path.Combine(Repo, "art/exports/qingxi-day12-c/model_info.json"));
            Report.Add($"Unity {Application.unityVersion}, pipeline {GraphicsSettings.currentRenderPipeline?.name ?? "built-in"}");
            foreach (var id in Ids) Inspect(id, JsonUtility.FromJson<Info>(Block(json, id)));
            Shots();
            File.WriteAllLines(Path.Combine(Out, "report.txt"), Report);
            foreach (var line in Report) Debug.Log("DAY12 " + line);
            if (failures > 0) throw new Exception($"DAY12_VERIFY {failures} check(s) failed, see {Out}/report.txt");
            Debug.Log($"DAY12_VERIFY_DONE all checks passed, output {Out}");
        }

        static void Check(bool ok, string line) { Report.Add((ok ? "PASS " : "FAIL ") + line); if (!ok) failures++; }

        // model_info.json is keyed by id; JsonUtility only reads objects, so cut out each item's braces.
        static string Block(string json, string id)
        {
            int start = json.IndexOf('{', json.IndexOf($"\"{id}\":", StringComparison.Ordinal)), depth = 0;
            for (int i = start; i < json.Length; i++)
            {
                if (json[i] == '{') depth++;
                else if (json[i] == '}' && --depth == 0) return json.Substring(start, i - start + 1);
            }
            throw new InvalidDataException("model_info.json: no item " + id);
        }

        // ------------------------------------------------------------------ import
        static void Import()
        {
            foreach (var id in Ids)
            {
                Copy(Path.Combine(Repo, "art/exports/qingxi-day12-c"), Path.Combine(Repo, "apps/game", Models, id), id + ".fbx");
                Copy(Path.Combine(Repo, "art/textures/qingxi-day12-c"), Path.Combine(Repo, "apps/game", Models, id, "Textures"), id + "_*.png");
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
                if (!File.Exists(target) || new FileInfo(target).Length != new FileInfo(file).Length) File.Copy(file, target, true);
            }
        }

        // One URP Lit per group: Albedo, Normal, MaskURP (R metal, G AO, A smoothness), lamps add Emission.
        static Material Mat(string id, string name)
        {
            var dir = $"{Models}/{id}/Materials"; Directory.CreateDirectory(Path.Combine(Repo, "apps/game", dir));
            var path = $"{dir}/{name}.mat";
            var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (mat == null) { mat = new Material(Shader.Find("Universal Render Pipeline/Lit")); AssetDatabase.CreateAsset(mat, path); }
            Texture2D T(string kind) => AssetDatabase.LoadAssetAtPath<Texture2D>($"{Models}/{id}/Textures/{name}_{kind}.png");
            var albedo = T("Albedo"); var mask = T("MaskURP"); var normal = T("Normal"); var glow = T("Emission");
            if (Checked.Add(name)) Check(albedo != null && mask != null && normal != null, $"{name}: Albedo / MaskURP / Normal{(glow ? " / Emission" : "")} textures found");
            mat.SetTexture("_BaseMap", albedo); mat.SetColor("_BaseColor", Color.white);
            mat.SetTexture("_BumpMap", normal); mat.EnableKeyword("_NORMALMAP");
            mat.SetTexture("_MetallicGlossMap", mask); mat.EnableKeyword("_METALLICSPECGLOSSMAP"); mat.SetFloat("_Smoothness", 1);
            mat.SetTexture("_OcclusionMap", mask); mat.EnableKeyword("_OCCLUSIONMAP");
            if (glow != null)
            {
                mat.SetTexture("_EmissionMap", glow); mat.SetColor("_EmissionColor", Color.black); mat.EnableKeyword("_EMISSION");
                mat.globalIlluminationFlags = MaterialGlobalIlluminationFlags.RealtimeEmissive;
            }
            EditorUtility.SetDirty(mat);
            return mat;
        }

        static GameObject Place(string id, Vector3 at, float yaw)
        {
            var go = (GameObject)PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>($"{Models}/{id}/{id}.fbx"));
            go.transform.SetPositionAndRotation(at, Quaternion.Euler(0, yaw, 0));
            foreach (var r in go.GetComponentsInChildren<Renderer>(true))
            {
                if (r.name == id + "_Collision") { r.enabled = false; continue; }
                var group = Regex.Match(r.name, @"^(.+)_LOD\d$");
                if (group.Success) r.sharedMaterials = Enumerable.Repeat(Mat(id, group.Groups[1].Value), r.sharedMaterials.Length).ToArray();
            }
            // Unity builds a LODGroup from _LOD0/_LOD1/_LOD2 names on import; build one only if it did not.
            if (go.GetComponent<LODGroup>() == null)
            {
                float[] cut = { .25f, .08f, .015f };
                var lods = Enumerable.Range(0, 3).Select(i => new LOD(cut[i], go.GetComponentsInChildren<Renderer>().Where(r => r.name.EndsWith("_LOD" + i)).ToArray())).ToArray();
                go.AddComponent<LODGroup>().SetLODs(lods);
            }
            var col = go.GetComponentsInChildren<MeshFilter>(true).FirstOrDefault(m => m.name == id + "_Collision");
            if (col != null && col.GetComponent<MeshCollider>() == null) col.gameObject.AddComponent<MeshCollider>().sharedMesh = col.sharedMesh;
            Physics.SyncTransforms();
            return go;
        }

        static Transform Node(GameObject go, string name) => go.GetComponentsInChildren<Transform>(true).FirstOrDefault(t => t.name == name);
        static Renderer[] Level(GameObject go, int i) => go.GetComponentsInChildren<Renderer>(true).Where(r => r.name.EndsWith("_LOD" + i)).ToArray();
        static int Tris(IEnumerable<Renderer> rs) => rs.Sum(r => { var m = r.GetComponent<MeshFilter>().sharedMesh; return Enumerable.Range(0, m.subMeshCount).Sum(s => (int)m.GetIndexCount(s)) / 3; });
        static Bounds Box(IEnumerable<Renderer> rs) { var a = rs.ToArray(); var b = a[0].bounds; foreach (var r in a) b.Encapsulate(r.bounds); return b; }

        // ------------------------------------------------------------------ checks
        static void Inspect(string id, Info info)
        {
            var go = Place(id, Vector3.zero, 0);
            var lod0 = Level(go, 0); var b = Box(lod0);
            // <ID>_GroundOrigin is the FBX's only root node, which Unity merges into the prefab root (named after the file).
            bool rooted = Node(go, id + "_GroundOrigin") != null || lod0.All(r => r.transform.parent == go.transform);
            Check(rooted, $"{id}: {id}_GroundOrigin is the model root (Unity names it {go.name}); all LOD meshes hang under it");
            float[] d = info.dimensions_xyz_m, lim = info.size_limit_m;
            Check(Mathf.Abs(b.size.x - d[0]) < .02f && Mathf.Abs(b.size.z - d[1]) < .02f && Mathf.Abs(b.size.y - d[2]) < .02f,
                $"{id}: imported size {b.size.x:0.000} x {b.size.z:0.000} x {b.size.y:0.000} m matches model_info {d[0]} x {d[1]} x {d[2]}");
            Check(b.size.x <= lim[0] + .001f && b.size.z <= lim[1] + .001f && b.size.y <= lim[2] + .001f, $"{id}: within the {lim[0]} x {lim[1]} x {lim[2]} m limit");
            Check(Mathf.Abs(b.min.y) < .01f, $"{id}: base at y = {b.min.y:0.000} (origin on the ground)");
            var tris = Enumerable.Range(0, 3).Select(i => Tris(Level(go, i))).ToArray();
            Check(Enumerable.Range(0, 3).All(i => Mathf.Abs(tris[i] - info.triangles_total[i]) <= info.triangles_total[i] * .01f),
                $"{id}: triangles LOD0/1/2 = {tris[0]} / {tris[1]} / {tris[2]} ({100f * tris[1] / tris[0]:0}% / {100f * tris[2] / tris[0]:0}%), model_info {string.Join(" / ", info.triangles_total)}");
            var lodGroup = go.GetComponent<LODGroup>(); var lods = lodGroup.GetLODs();
            Check(lods.Length == 3 && lods.All(l => l.renderers.Length == lod0.Length), $"{id}: LODGroup with 3 levels x {lod0.Length} renderers (one per material group)");
            var col = Node(go, id + "_Collision")?.GetComponent<MeshCollider>();
            Check(col != null && col.sharedMesh.triangles.Length > 0, $"{id}: {id}_Collision imported as MeshCollider ({(col ? col.sharedMesh.triangles.Length / 3 : 0)} triangles), render hidden");
            if (col != null)
            {
                var cb = col.bounds; var inside = new Bounds(b.center, b.size + Vector3.one * .1f);
                Check(inside.Contains(cb.min) && inside.Contains(cb.max), $"{id}: collider {cb.size.x:0.00} x {cb.size.z:0.00} x {cb.size.y:0.00} m stays within the model");
            }
            if (info.light_socket != null && info.light_socket.Length == 3)
            {
                var s = Node(go, id + "_LightSocket");
                Check(s != null && Mathf.Abs(s.position.y - info.light_socket[2]) < .02f, $"{id}: {id}_LightSocket at height {(s ? s.position.y : -1):0.000} m");
                var lamp = go.GetComponentsInChildren<Renderer>().Select(r => r.sharedMaterial).FirstOrDefault(m => m && m.IsKeywordEnabled("_EMISSION"));
                Check(lamp != null && lamp.GetTexture("_EmissionMap") != null, $"{id}: lamp chamber is its own emissive material ({(lamp ? lamp.name : "none")})");
            }
            if (id == "RK03") WalkIn(go);
            UnityEngine.Object.DestroyImmediate(go);
        }

        // RK03 is walk-in: a 1.75 m, r 0.3 m player fits on the path up the steps and under the eaves. Like a
        // CharacterController (default stepOffset 0.3 m) the capsule ignores what is below the step height, and each rise must fit it.
        static void WalkIn(GameObject go)
        {
            var col = Node(go, "RK03_Collision").GetComponent<MeshCollider>();
            var verts = col.sharedMesh.vertices.Select(v => col.transform.TransformPoint(v)).ToArray();
            front = verts.Max(v => v.z) > -verts.Min(v => v.z) ? Vector3.forward : Vector3.back;   // the steps stick out on the front
            Report.Add($"INFO Blender front (-Y) imports as Unity {(front.z > 0 ? "+Z" : "-Z")}");
            float s = front.z;
            var path = new (float x, float floor, float z, string where)[] {
                (0, 0, 2.75f, "road before the steps"), (0, .15f, 2.35f, "first step"), (0, .30f, 2.05f, "second step"),
                (0, .45f, 1.65f, "platform edge"), (0, .45f, 1.25f, "doorway between the low walls"),
                (-1.2f, .45f, 1.0f, "inside, beside the bench"), (-1.2f, .45f, 0, "inside, beside the tea table"), (-1.2f, .45f, -1.0f, "inside, back corner") };
            const float stepOffset = .3f;
            float previous = 0;
            foreach (var (x, floor, z, where) in path)
            {
                var feet = new Vector3(x, floor, s * z);
                bool clear = !Physics.CheckCapsule(feet + Vector3.up * (stepOffset + .32f), feet + Vector3.up * 1.45f, .3f);
                float found = floor == 0 ? 0 : Physics.Raycast(feet + Vector3.up * .3f, Vector3.down, out var hit, .6f) ? hit.point.y : -1;
                bool ground = Mathf.Abs(found - floor) < .03f, rise = found - previous <= stepOffset + .001f;
                Check(clear && ground && rise, $"RK03 walk-in: player fits at the {where} (floor {found:0.00} m, rise {found - previous:0.00} m)");
                previous = found;
            }
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
            cam = new GameObject("Review Camera").AddComponent<Camera>(); cam.nearClipPlane = .03f; cam.farClipPlane = 300;
            UnityEngine.Rendering.Universal.CameraExtensions.GetUniversalAdditionalCameraData(cam).renderPostProcessing = true;
            target = new RenderTexture(1280, 960, 24) { antiAliasing = 4 }; cam.targetTexture = target;
            Day();

            foreach (var id in Ids)   // four views with the 1.75 m figure, plus forced LOD0/1/2
            {
                var go = Place(id, Vector3.zero, 0); var b = Box(Level(go, 0));
                var ruler = Ruler(new Vector3(b.max.x + .45f, 0, 0));
                var all = b; all.Encapsulate(ruler.GetComponent<Renderer>().bounds);
                var side = Vector3.Cross(Vector3.up, front);
                foreach (var (view, dir) in new[] { ("front", front), ("side", side), ("back", -front), ("threequarter", (front - side).normalized + Vector3.up * .55f) })
                    Frame($"{id}/{id}-{view}", all, dir);
                var group = go.GetComponent<LODGroup>();
                for (int i = 0; i < 3; i++) { group.ForceLOD(i); Frame($"{id}/{id}-lod{i}", b, (front - side).normalized + Vector3.up * .55f); }
                group.ForceLOD(-1);
                if (id == "TY08")
                {
                    foreach (var r in go.GetComponentsInChildren<Renderer>().Where(r => r.name.StartsWith("TY08_Herbs"))) r.enabled = false;
                    Frame("TY08/TY08-empty", b, (front - side).normalized + Vector3.up * .55f);
                }
                UnityEngine.Object.DestroyImmediate(ruler); UnityEngine.Object.DestroyImmediate(go);
            }

            // Lamp states: G01 unlit / lit and TY04 brightness 0-4, by day and by night (point light on the socket).
            foreach (var night in new[] { false, true })
            {
                if (night) Night(); else Day();
                string t = night ? "night" : "day";
                var g01 = Place("G01", Vector3.zero, 0);
                foreach (var (state, strength) in new[] { ("unlit", 0f), ("lit", 1.2f) }) { Glow(g01, strength); Frame($"G01/G01-{t}-{state}", Box(Level(g01, 0)), front + Vector3.up * .35f, 1.15f); }
                UnityEngine.Object.DestroyImmediate(g01);
                var ty04 = Place("TY04", Vector3.zero, 0);
                for (int i = 0; i < Ty04Levels.Length; i++) { Glow(ty04, Ty04Levels[i]); Frame($"TY04/TY04-{t}-level{i}", Box(Level(ty04, 0)), front + Vector3.up * .2f, 1.15f); }
                if (!night) { Glow(ty04, 0); float s = front.z;   // crescent at Blender (-0.12, -0.40, 0.075): low on the front, left as seen from the front
                    Shot("TY04/TY04-crescent-closeup", new Vector3(.08f * s, .20f, .70f * s), new Vector3(.12f * s, .09f, .40f * s), 30); }
                UnityEngine.Object.DestroyImmediate(ty04);
            }

            // 1.7 m eye height: the road to the tea pavilion, the village gate pair by day and night, the yard from the back door.
            Day();
            var rk = Place("RK03", Vector3.zero, 0); var r1 = Ruler(new Vector3(3.6f, 0, 2.5f * front.z));
            Shot("eye/RK03-road-1p7m", new Vector3(-2.2f, 1.7f, 9.5f * front.z), new Vector3(0, 1.8f, 0), 50);
            UnityEngine.Object.DestroyImmediate(r1); UnityEngine.Object.DestroyImmediate(rk);
            var gate = new[] { Place("G01", new Vector3(-3.6f, 0, 0), 0), Place("G01", new Vector3(3.6f, 0, 0), 0) };
            var r2 = Ruler(new Vector3(1.2f, 0, 0));
            foreach (var night in new[] { false, true })
            {
                if (night) Night(); else Day();
                foreach (var g in gate) Glow(g, night ? 1.2f : 0);
                Shot($"eye/G01-gate-{(night ? "night" : "day")}-1p7m", new Vector3(0, 1.7f, 9 * front.z), new Vector3(0, 1.3f, 0), 45);
            }
            foreach (var g in gate) UnityEngine.Object.DestroyImmediate(g);
            UnityEngine.Object.DestroyImmediate(r2);
            Day();
            // Yard slots from the brief (x, z): TY04 (-5.2, 12), TY08 (5.4, 4) turned 90 to fit its 0.8 x 2.0 slot, TY09 (5.0, 11.5).
            var yard = new[] { Place("TY04", new Vector3(-5.2f, 0, 12), 0), Place("TY08", new Vector3(5.4f, 0, 4), 90), Place("TY09", new Vector3(5f, 0, 11.5f), 180) };
            Glow(yard[0], Ty04Levels[1]);
            var r3 = Ruler(new Vector3(1, 0, 6));
            Shot("eye/yard-from-backdoor-1p7m", new Vector3(2, 1.7f, .5f), new Vector3(3, .8f, 9), 72);   // same aim as the Blender review (18 mm)
            foreach (var g in yard) UnityEngine.Object.DestroyImmediate(g);
            UnityEngine.Object.DestroyImmediate(r3);
            Report.Add($"INFO renders written to art/previews/qingxi-day12-c/unity");
        }

        static void Day()
        {
            sun.transform.rotation = Quaternion.Euler(38, -40, 0); sun.color = new Color(1, .86f, .66f); sun.intensity = 1.7f;
            RenderSettings.ambientMode = AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = new Color(.52f, .60f, .74f); RenderSettings.ambientEquatorColor = new Color(.50f, .50f, .48f); RenderSettings.ambientGroundColor = new Color(.30f, .27f, .22f);
            cam.clearFlags = CameraClearFlags.SolidColor; cam.backgroundColor = new Color(.62f, .72f, .86f);
        }

        static void Night()   // moonlit blue: the lamps are the only warm light
        {
            sun.transform.rotation = Quaternion.Euler(40, 150, 0); sun.color = new Color(.65f, .75f, 1); sun.intensity = .12f;
            RenderSettings.ambientMode = AmbientMode.Flat; RenderSettings.ambientLight = new Color(.05f, .07f, .12f);
            cam.backgroundColor = new Color(.03f, .04f, .08f);
        }

        // Brightness is one material value (emission strength); the socket carries a matching point light.
        static void Glow(GameObject go, float strength)
        {
            foreach (var m in go.GetComponentsInChildren<Renderer>().Select(r => r.sharedMaterial).Where(m => m && m.IsKeywordEnabled("_EMISSION")).Distinct())
                m.SetColor("_EmissionColor", new Color(1, .78f, .45f) * strength);
            var socket = go.GetComponentsInChildren<Transform>().FirstOrDefault(t => t.name.EndsWith("_LightSocket"));
            if (socket == null) return;
            var light = socket.GetComponent<Light>();
            if (light == null) light = socket.gameObject.AddComponent<Light>();
            light.type = LightType.Point; light.color = new Color(1, .74f, .42f); light.range = 4; light.intensity = strength * 1.4f; light.enabled = strength > 0;
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
