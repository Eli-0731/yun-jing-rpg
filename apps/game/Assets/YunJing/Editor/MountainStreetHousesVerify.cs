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
    // Unity check of the 11/05 package A MC01 mountain street kit (art/exports/mountain-street-houses-a, Johnnnny0823).
    // Imports every MC01_*.fbx and the shared 2048 trim sheet, builds the two shared URP materials (M_MountainStreet_Trim and
    // M_MountainStreet_Glow), LODGroups and mesh colliders from the node names, compares each module with its model_info.json
    // (size, LOD triangles, objects, Detail_* groups, collision, base on the ground) and assembles the three demo buildings from
    // b-street-assembly.json. Needs a graphics device (no -nographics):
    //   Unity -batchmode -quit -projectPath apps/game -executeMethod YunJing.Editor.MountainStreetHousesVerify.Run -logFile <log>
    // Output: art/previews/mountain-street-houses-a/unity/*.png and report.txt; the run fails when a check fails.
    public static class MountainStreetHousesVerify
    {
        const string Models = "Assets/YunJing/Models/MountainStreetHousesA";   // copied from art/exports, gitignored
        const string Pkg = "mountain-street-houses-a";
        static string Repo => Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", ".."));
        static string Exports => Path.Combine(Repo, "art/exports", Pkg);
        static string Out => Path.Combine(Repo, "art/previews", Pkg, "unity");
        static readonly List<string> Report = new List<string>();
        static int failures;
        static Material trim, glow;
        static float sx = 1;   // Blender +X -> Unity sx * X, measured on the asymmetric RF03

        [Serializable] class Lod { public int lod, triangles, objects, materials; }
        [Serializable] class Info { public string id, minTier, collision; public float[] dimensions_m; public Lod[] lods; public string[] detailObjects, objectsLOD0; }
        [Serializable] class Part { public string id; public float[] pos; public float rotZ; }
        [Serializable] class Building { public string name, note; public Part[] parts; public float[] camera; }
        [Serializable] class Assembly { public Building[] buildings; }

        static string[] Ids => Directory.GetFiles(Exports, "MC01_*.fbx").Select(f => Path.GetFileNameWithoutExtension(f).Substring(5)).OrderBy(s => s).ToArray();

        public static void Run()
        {
            Report.Clear(); failures = 0; Directory.CreateDirectory(Out);
            Import();
            QingxiUrpUpgrade.EnsurePipeline();
            Materials();
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene);
            Report.Add($"Unity {Application.unityVersion}, pipeline {GraphicsSettings.currentRenderPipeline?.name ?? "built-in"}");
            Measure();
            foreach (var id in Ids) Inspect(id, JsonUtility.FromJson<Info>(File.ReadAllText(Path.Combine(Exports, $"MC01_{id}.model_info.json"))));
            Shots();
            File.WriteAllLines(Path.Combine(Out, "report.txt"), Report);
            foreach (var line in Report) Debug.Log("MC01 " + line);
            if (failures > 0) throw new Exception($"MC01_VERIFY {failures} check(s) failed, see {Out}/report.txt");
            Debug.Log($"MC01_VERIFY_DONE all checks passed, output {Out}");
        }

        static void Check(bool ok, string line) { Report.Add((ok ? "PASS " : "FAIL ") + line); if (!ok) failures++; }

        // ------------------------------------------------------------------ import
        static void Import()
        {
            Copy(Exports, Path.Combine(Repo, "apps/game", Models), "MC01_*.fbx");
            Copy(Path.Combine(Repo, "art/textures", Pkg), Path.Combine(Repo, "apps/game", Models, "Textures"), "T_MountainStreet_*.png");
            AssetDatabase.Refresh();
            foreach (var guid in AssetDatabase.FindAssets("t:Model", new[] { Models }))
            {
                var importer = (ModelImporter)AssetImporter.GetAtPath(AssetDatabase.GUIDToAssetPath(guid));
                if (importer.bakeAxisConversion && importer.materialImportMode == ModelImporterMaterialImportMode.None) continue;
                importer.bakeAxisConversion = true; importer.importCameras = false; importer.importLights = false; importer.addCollider = false;
                importer.importAnimation = false; importer.materialImportMode = ModelImporterMaterialImportMode.None;
                importer.importTangents = ModelImporterTangents.CalculateMikk;
                importer.SaveAndReimport();
            }
            foreach (var guid in AssetDatabase.FindAssets("t:Texture2D", new[] { Models }))
            {
                var path = AssetDatabase.GUIDToAssetPath(guid);
                var ti = (TextureImporter)AssetImporter.GetAtPath(path);
                bool normal = path.EndsWith("_Normal.png"), linear = normal || path.EndsWith("_MetallicSmoothness.png");
                var type = normal ? TextureImporterType.NormalMap : TextureImporterType.Default;
                // the project's QingxiImportBudget caps every texture under Assets/YunJing/Models at 1024 on import; leave that rule alone
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

        // The whole kit shares two URP Lit materials on one trim sheet (D3 §4: one 2048 set so the street batches).
        static void Materials()
        {
            Texture2D T(string kind) => AssetDatabase.LoadAssetAtPath<Texture2D>($"{Models}/Textures/T_MountainStreet_{kind}.png");
            var albedo = T("Albedo"); var normal = T("Normal"); var ms = T("MetallicSmoothness"); var em = T("Emission");
            Check(albedo && normal && ms && em, "shared trim sheet: Albedo / Normal / MetallicSmoothness / Emission imported");
            foreach (var t in new[] { albedo, normal, ms, em }.Where(t => t))
            {
                var src = Path.Combine(Repo, "art/textures", Pkg, t.name + ".png"); var png = File.ReadAllBytes(src);
                int sw = (png[16] << 24) | (png[17] << 16) | (png[18] << 8) | png[19], sh = (png[20] << 24) | (png[21] << 16) | (png[22] << 8) | png[23];
                Check(sw == 2048 && sh == 2048 && t.width == Math.Min(sw, 1024),
                    $"{t.name}: source {sw} x {sh}, imported {t.width} x {t.height} (QingxiImportBudget caps model textures at 1024)");
            }
            Material Make(string name, bool emissive)
            {
                var path = $"{Models}/{name}.mat"; var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
                if (mat == null) { mat = new Material(Shader.Find("Universal Render Pipeline/Lit")); AssetDatabase.CreateAsset(mat, path); }
                mat.SetTexture("_BaseMap", albedo); mat.SetColor("_BaseColor", Color.white);
                mat.SetTexture("_BumpMap", normal); mat.EnableKeyword("_NORMALMAP");
                mat.SetTexture("_MetallicGlossMap", ms); mat.EnableKeyword("_METALLICSPECGLOSSMAP"); mat.SetFloat("_Smoothness", 1);
                if (emissive)
                {
                    mat.SetTexture("_EmissionMap", em); mat.SetColor("_EmissionColor", new Color(1, .8f, .5f) * 1.2f); mat.EnableKeyword("_EMISSION");
                    mat.globalIlluminationFlags = MaterialGlobalIlluminationFlags.RealtimeEmissive;
                }
                mat.enableInstancing = true; EditorUtility.SetDirty(mat); return mat;
            }
            trim = Make("M_MountainStreet_Trim", false); glow = Make("M_MountainStreet_Glow", true);
            AssetDatabase.SaveAssets();
        }

        static GameObject Place(string id, Vector3 at, float yaw, Transform parent = null)
        {
            var go = (GameObject)PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>($"{Models}/MC01_{id}.fbx"));
            go.transform.SetPositionAndRotation(at, Quaternion.Euler(0, yaw, 0)); if (parent) go.transform.SetParent(parent, true);
            foreach (var r in go.GetComponentsInChildren<Renderer>(true))
            {
                if (r.name.StartsWith($"MC01_{id}_Collision")) { r.enabled = false; continue; }
                r.sharedMaterials = Enumerable.Repeat(r.name.StartsWith("Glow_") ? glow : trim, r.sharedMaterials.Length).ToArray();
            }
            if (go.GetComponent<LODGroup>() == null)
            {
                float[] cut = { .30f, .10f, .015f };
                var lods = Enumerable.Range(0, 3).Select(i => new LOD(cut[i], go.GetComponentsInChildren<Renderer>().Where(r => r.name.EndsWith("_LOD" + i)).ToArray())).ToArray();
                go.AddComponent<LODGroup>().SetLODs(lods);
            }
            var col = go.GetComponentsInChildren<MeshFilter>(true).FirstOrDefault(m => m.name == $"MC01_{id}_Collision");
            if (col != null && col.GetComponent<MeshCollider>() == null) col.gameObject.AddComponent<MeshCollider>().sharedMesh = col.sharedMesh;
            Physics.SyncTransforms();
            return go;
        }

        static Transform Node(GameObject go, string name) => go.GetComponentsInChildren<Transform>(true).FirstOrDefault(t => t.name == name);
        static Renderer[] Level(GameObject go, int i) => go.GetComponentsInChildren<Renderer>(true).Where(r => r.name.EndsWith("_LOD" + i)).ToArray();
        static int Tris(IEnumerable<Renderer> rs) => rs.Sum(r => { var m = r.GetComponent<MeshFilter>().sharedMesh; return Enumerable.Range(0, m.subMeshCount).Sum(s => (int)m.GetIndexCount(s)) / 3; });
        static Bounds Box(IEnumerable<Renderer> rs) { var a = rs.ToArray(); var b = a[0].bounds; foreach (var r in a) b.Encapsulate(r.bounds); return b; }

        // Blender -> Unity mapping, measured instead of assumed: RF03's hip end sits on Blender +X.
        static void Measure()
        {
            var go = Place("RF03", Vector3.zero, 0); var c = Box(Level(go, 0)).center.x; UnityEngine.Object.DestroyImmediate(go);
            sx = c > 0 ? 1 : -1;
            Report.Add($"INFO axis: Blender +X -> Unity {(sx > 0 ? "+X" : "-X")}, Blender +Y -> Unity +Z, Blender +Z -> Unity +Y (RF03 bounds centre x = {c:0.000})");
        }
        static Vector3 U(float[] p) => new Vector3(sx * p[0], p[2], p[1]);
        static float Yaw(float rotZ) => -sx * rotZ;

        // ------------------------------------------------------------------ checks
        static void Inspect(string id, Info info)
        {
            var go = Place(id, Vector3.zero, 0);
            var lod0 = Level(go, 0); var b = Box(lod0); var d = info.dimensions_m;
            Check(Mathf.Abs(b.size.x - d[0]) < .02f && Mathf.Abs(b.size.z - d[1]) < .02f && Mathf.Abs(b.size.y - d[2]) < .02f,
                $"{id}: imported size {b.size.x:0.000} x {b.size.z:0.000} x {b.size.y:0.000} m matches model_info {d[0]} x {d[1]} x {d[2]}");
            Check(Mathf.Abs(b.min.y) < .01f, $"{id}: base at y = {b.min.y:0.000}");
            var tris = Enumerable.Range(0, 3).Select(i => Tris(Level(go, i))).ToArray();
            Check(Enumerable.Range(0, 3).All(i => Mathf.Abs(tris[i] - info.lods[i].triangles) <= info.lods[i].triangles * .01f + 2),
                $"{id}: triangles LOD0/1/2 = {tris[0]} / {tris[1]} / {tris[2]}, model_info {info.lods[0].triangles} / {info.lods[1].triangles} / {info.lods[2].triangles}");
            Check(lod0.Length == info.lods[0].objects, $"{id}: {lod0.Length} LOD0 objects (model_info {info.lods[0].objects})");
            var mats = lod0.SelectMany(r => r.sharedMaterials).Distinct().Count();
            Check(mats == info.lods[0].materials, $"{id}: {mats} shared material(s) on LOD0 (model_info {info.lods[0].materials})");
            foreach (var g in info.detailObjects ?? new string[0])
                Check(Node(go, g + "_LOD0") && Node(go, g + "_LOD1") && Node(go, g + "_LOD2"), $"{id}: removable {g} present on LOD0/1/2");
            var lods = go.GetComponent<LODGroup>().GetLODs();
            Check(lods.Length == 3 && lods.All(l => l.renderers.Length == lod0.Length), $"{id}: LODGroup 3 levels x {lod0.Length} renderers");
            var col = Node(go, $"MC01_{id}_Collision")?.GetComponent<MeshCollider>();
            if (info.collision != null && info.collision.Contains("(0 boxes)")) { Report.Add($"INFO {id}: no collision by design (hanging / wall-mounted decor)"); UnityEngine.Object.DestroyImmediate(go); return; }
            Check(col != null && col.sharedMesh.triangles.Length > 0, $"{id}: collision imported as MeshCollider ({(col ? col.sharedMesh.triangles.Length / 3 : 0)} tris), render hidden");
            UnityEngine.Object.DestroyImmediate(go);
        }

        // ------------------------------------------------------------------ renders
        static Camera cam; static RenderTexture target; static Light sun; static Material groundMat, rulerMat;

        static void Shots()
        {
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene);
            sun = new GameObject("Sun").AddComponent<Light>(); sun.type = LightType.Directional; sun.shadows = LightShadows.Soft;
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
            var front = Vector3.back; var side = Vector3.Cross(Vector3.up, front);
            foreach (var id in Ids)
            {
                var go = Place(id, Vector3.zero, 0); var b = Box(Level(go, 0)); var ruler = Ruler(new Vector3(b.max.x + .5f, 0, b.min.z - .4f));
                Frame($"modules/{id}", b, (front - side * .8f).normalized + Vector3.up * .5f);
                UnityEngine.Object.DestroyImmediate(ruler); UnityEngine.Object.DestroyImmediate(go);
            }
            var asm = JsonUtility.FromJson<Assembly>(File.ReadAllText(Path.Combine(Exports, "b-street-assembly.json")));
            var root = new GameObject("MC01 street"); var all = new List<Renderer>();
            foreach (var bd in asm.buildings)
            {
                var g = new GameObject(bd.name); g.transform.SetParent(root.transform, false); int n = 0;
                foreach (var p in bd.parts)
                {
                    if (!File.Exists(Path.Combine(Exports, $"MC01_{p.id}.fbx"))) { Check(false, $"{bd.name}: part {p.id} has no FBX"); continue; }
                    Place(p.id, U(p.pos), Yaw(p.rotZ), g.transform); n++;
                }
                var rs = g.GetComponentsInChildren<Renderer>().Where(r => r.enabled && r.name.EndsWith("_LOD0")).ToArray(); all.AddRange(rs);
                Check(n == bd.parts.Length, $"{bd.name}: {n} / {bd.parts.Length} modules placed from b-street-assembly.json");
                var bb = Box(rs); var ruler = Ruler(new Vector3(bb.min.x - .6f, 0, bb.min.z - 1.2f));
                Frame($"assembly/{bd.name}-threequarter", bb, (front - side * .8f).normalized + Vector3.up * .45f, 1.1f);
                Frame($"assembly/{bd.name}-front", bb, front + Vector3.up * .15f, 1.1f);
                UnityEngine.Object.DestroyImmediate(ruler);
            }
            var sb = Box(all);
            Frame("assembly/street-overview", sb, (front - side * .5f).normalized + Vector3.up * .6f, 1.0f);
            Shot("assembly/street-eye-1p7m", new Vector3(sb.center.x - 3, 1.7f + 2f, sb.min.z - 7), new Vector3(sb.center.x, 4.5f, sb.center.z), 60);
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
