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
    // Unity check of the 11/03 package A world models (art/exports/world-props-a, Johnnnny0823), adapted from QingxiDay12Verify:
    // imports the delivered FBX and textures, builds URP materials, LODGroup and collider from the node names, compares them with
    // model_info.json (size, limit, LOD triangles, minTier, Detail_* objects, collision, wheel pivots, the shrine's Glow) and renders
    // review shots plus 1.7 m eye-height lineups. Needs a graphics device (no -nographics):
    //   Unity -batchmode -quit -projectPath apps/game -executeMethod YunJing.Editor.QingxiWorldPropsAVerify.Run -logFile <log>
    // Output: art/previews/world-props-a/unity/*.png and report.txt; the run fails when a check fails.
    public static class QingxiWorldPropsAVerify
    {
        const string Models = "Assets/YunJing/Models/WorldPropsA";   // copied from art/exports, gitignored
        static readonly string[] Ids = { "SC04", "SC01", "SC02", "SC03", "RK05", "RK06", "RK01A", "RK01B", "RK09", "RK10A", "RK10B", "RK12A", "RK12B", "RK12C", "RK12D", "WM08A", "WM08B", "WM08C", "WM10A", "WM10B", "WM10C", "WM10D", "TY03A", "TY03B", "TY03C", "TY03D", "TY06", "TY05A", "TY05B", "TY10A", "TY10B", "TY10C" };
        static string Repo => Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", ".."));
        static string Out => Path.Combine(Repo, "art/previews/world-props-a/unity");
        static readonly List<string> Report = new List<string>();
        static int failures;
        static readonly HashSet<string> Checked = new HashSet<string>();
        static Vector3 front = Vector3.back;   // Blender -Y

        [Serializable] class Info { public float[] dimensions_xyz_m, size_limit_m; public int[] triangles_total; public string minTier; public string[] detailObjects; }

        public static void Run()
        {
            Report.Clear(); Checked.Clear(); failures = 0;
            Directory.CreateDirectory(Out);
            Import();
            QingxiUrpUpgrade.EnsurePipeline();
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene);
            var json = File.ReadAllText(Path.Combine(Repo, "art/exports/world-props-a/model_info.json"));
            Report.Add($"Unity {Application.unityVersion}, pipeline {GraphicsSettings.currentRenderPipeline?.name ?? "built-in"}");
            foreach (var id in Ids) { var block = Block(json, id); Inspect(id, JsonUtility.FromJson<Info>(block), !block.Contains("\"collision\": null")); }
            Shots();
            File.WriteAllLines(Path.Combine(Out, "report.txt"), Report);
            foreach (var line in Report) Debug.Log("WORLDA " + line);
            if (failures > 0) throw new Exception($"WORLDA_VERIFY {failures} check(s) failed, see {Out}/report.txt");
            Debug.Log($"WORLDA_VERIFY_DONE all checks passed, output {Out}");
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
                Copy(Path.Combine(Repo, "art/exports/world-props-a"), Path.Combine(Repo, "apps/game", Models, id), id + ".fbx");
                bool ground = id.StartsWith("TY05") || id.StartsWith("TY10");   // ground pieces name their maps T_<ID>_*
                Copy(Path.Combine(Repo, "art/textures/world-props-a"), Path.Combine(Repo, "apps/game", Models, id, "Textures"), (ground ? "T_" : "") + id + "_*.png");
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
            string key = name == id ? "T_" + id : name.StartsWith("Detail_") ? id + "_" + name : name;   // ground / removable detail / group
            Texture2D T(string kind) => AssetDatabase.LoadAssetAtPath<Texture2D>($"{Models}/{id}/Textures/{key}_{kind}.png");
            var albedo = T("Albedo"); var mask = T("MaskURP"); var normal = T("Normal"); var glow = T("Emission");
            if (Checked.Add(id + "/" + name)) Check(albedo != null && mask != null && normal != null, $"{id}/{name}: Albedo / MaskURP / Normal{(glow ? " / Emission" : "")} textures found");
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
        static void Inspect(string id, Info info, bool hasCollision)
        {
            var go = Place(id, Vector3.zero, 0);
            var lod0 = Level(go, 0); var b = Box(lod0);
            // <ID>_GroundOrigin is the FBX's only root node, which Unity merges into the prefab root (named after the file).
            bool rooted = Node(go, id + "_GroundOrigin") != null || lod0.All(r => r.transform.parent == go.transform);
            Check(rooted, $"{id}: {id}_GroundOrigin is the model root (Unity names it {go.name}); all LOD meshes hang under it");
            float[] d = info.dimensions_xyz_m, lim = info.size_limit_m;
            Check(Mathf.Abs(b.size.x - d[0]) < .02f && Mathf.Abs(b.size.z - d[1]) < .02f && Mathf.Abs(b.size.y - d[2]) < .02f,
                $"{id}: imported size {b.size.x:0.000} x {b.size.z:0.000} x {b.size.y:0.000} m matches model_info {d[0]} x {d[1]} x {d[2]}");
            if (lim != null && lim.Length == 3) Check(b.size.x <= lim[0] + .001f && b.size.z <= lim[1] + .001f && b.size.y <= lim[2] + .001f, $"{id}: within the {lim[0]} x {lim[1]} x {lim[2]} m limit");
            else Check(b.size.y <= .02f, $"{id}: ground piece rises {b.size.y:0.000} m (limit 0.02 m)");
            Check(!string.IsNullOrEmpty(info.minTier), $"{id}: minTier = {info.minTier}");
            foreach (var d_ in info.detailObjects ?? new string[0])
                Check(Node(go, d_ + "_LOD0") != null && Node(go, d_ + "_LOD1") != null, $"{id}: removable {d_} present (LOD0/1/2)");
            Check(Mathf.Abs(b.min.y) < .01f, $"{id}: base at y = {b.min.y:0.000} (origin on the ground)");
            var tris = Enumerable.Range(0, 3).Select(i => Tris(Level(go, i))).ToArray();
            Check(Enumerable.Range(0, 3).All(i => Mathf.Abs(tris[i] - info.triangles_total[i]) <= info.triangles_total[i] * .01f),
                $"{id}: triangles LOD0/1/2 = {tris[0]} / {tris[1]} / {tris[2]} ({100f * tris[1] / tris[0]:0}% / {100f * tris[2] / tris[0]:0}%), model_info {string.Join(" / ", info.triangles_total)}");
            var lodGroup = go.GetComponent<LODGroup>(); var lods = lodGroup.GetLODs();
            Check(lods.Length == 3 && lods.All(l => l.renderers.Length == lod0.Length), $"{id}: LODGroup with 3 levels x {lod0.Length} renderers (one per material group)");
            var col = Node(go, id + "_Collision")?.GetComponent<MeshCollider>();
            if (!hasCollision) Report.Add($"INFO {id}: no collision by design (decor / ground)");
            else Check(col != null && col.sharedMesh.triangles.Length > 0, $"{id}: {id}_Collision imported as MeshCollider ({(col ? col.sharedMesh.triangles.Length / 3 : 0)} triangles), render hidden");
            if (id == "RK05")
                foreach (var w in new[] { "RK05_WheelL_LOD0", "RK05_WheelR_LOD0" })
                {
                    var n = Node(go, w);
                    Check(n != null && n.localPosition.sqrMagnitude > .01f, $"RK05: {w} is its own mesh with its origin on the axle at {(n ? n.position : Vector3.zero)}");
                }
            if (id == "RK06")
            {
                var lamp = go.GetComponentsInChildren<Renderer>().Select(r => r.sharedMaterial).FirstOrDefault(m => m && m.IsKeywordEnabled("_EMISSION"));
                Check(lamp != null && lamp.name.EndsWith("Glow"), $"RK06: the niche flame is its own emissive Glow material ({(lamp ? lamp.name : "none")})");
            }
            if (col != null)
            {
                var cb = col.bounds; var inside = new Bounds(b.center, b.size + Vector3.one * .1f);
                Check(inside.Contains(cb.min) && inside.Contains(cb.max), $"{id}: collider {cb.size.x:0.00} x {cb.size.z:0.00} x {cb.size.y:0.00} m stays within the model");
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
                UnityEngine.Object.DestroyImmediate(ruler); UnityEngine.Object.DestroyImmediate(go);
            }

            // 1.7 m eye-height lineups: the official road, the creek, the home yard, the old scenes; the shrine flame by day and night
            Day();
            void Lineup(string file, (string id, float x, float z, float yaw)[] items, Vector3 eye, Vector3 at, float fov)
            {
                var gos = items.Select(i => Place(i.id, new Vector3(i.x, 0, i.z), i.yaw)).ToList(); var r = Ruler(new Vector3(eye.x + 1.2f, 0, eye.z + 3.5f));
                Shot(file, eye, at, fov);
                foreach (var g in gos) UnityEngine.Object.DestroyImmediate(g);
                UnityEngine.Object.DestroyImmediate(r);
            }
            Lineup("eye/road-1p7m", new[] { ("TY10A", 0f, 0f, 0f), ("TY10B", 0f, 2f, 0f), ("TY10A", 0f, 4f, 0f), ("TY10B", 0f, 6f, 0f), ("TY10C", 0f, 7.5f, 0f),
                ("RK12A", -.9f, 1.5f, 90f), ("RK12B", .9f, 3.2f, 90f), ("RK01A", -1.2f, 5.5f, 20f), ("RK06", 2.4f, 7.5f, 200f), ("RK09", -2.2f, 8.5f, 160f),
                ("RK05", 2.4f, 3.5f, 10f), ("RK10A", -4f, 10f, 0f), ("RK10B", 4.5f, 11.5f, 0f) }, new Vector3(-.4f, 1.7f, -4.5f), new Vector3(0, 1.0f, 5), 55);
            Lineup("eye/creek-1p7m", new[] { ("WM08A", -.4f, 1f, 0f), ("WM08B", .5f, 2.2f, 40f), ("WM08C", -.2f, 3.4f, 80f), ("WM10A", 1.6f, 1.2f, 0f),
                ("WM10B", -2f, 2.6f, 30f), ("WM10C", 2.8f, 4.5f, 200f), ("WM10D", -2.6f, 5.2f, 100f) }, new Vector3(0, 1.7f, -3.5f), new Vector3(0, .3f, 3), 55);
            Lineup("eye/yard-1p7m", new[] { ("TY05A", 0f, 2f, 0f), ("TY05B", 2f, 2f, 0f), ("TY05A", 0f, 4f, 0f), ("TY05B", 2f, 4f, 0f), ("TY06", 1f, 3f, 20f),
                ("TY03A", -2.2f, 1.5f, 0f), ("TY03B", -2.2f, 2.3f, 0f), ("TY03C", -2.2f, 3.1f, 0f), ("TY03D", -2.2f, 3.9f, 0f) }, new Vector3(-.6f, 1.7f, -2.2f), new Vector3(0, .4f, 3), 55);
            Lineup("eye/old-scenes-1p7m", new[] { ("SC04", -4f, 4f, 15f), ("SC02", 0f, 2.5f, 0f), ("SC03", 4.5f, 5f, -20f), ("SC01", 1.8f, .8f, 30f) },
                new Vector3(0, 1.7f, -5f), new Vector3(0, 1.2f, 4), 60);
            foreach (var night in new[] { false, true })
            {
                if (night) Night(); else Day();
                var rk6 = Place("RK06", Vector3.zero, 0); Glow(rk6, night ? 2.5f : 1f);
                Frame($"RK06/RK06-{(night ? "night" : "day")}-glow", Box(Level(rk6, 0)), front + Vector3.up * .25f, 1.1f);
                UnityEngine.Object.DestroyImmediate(rk6);
            }
            Day();
            Report.Add($"INFO renders written to art/previews/world-props-a/unity");
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
