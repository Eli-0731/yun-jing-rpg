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
    // Unity check of the 11/05 package A TX04 Taixuan branch academy kit (art/exports/tx04-branch-court, Johnnnny0823).
    // Imports every TX04_*.fbx, the shared MC01 trim sheet and the TX04 wall tile, builds the four URP materials named in
    // model_info (M_MountainStreet_Trim, M_TX04_Roof = trim with normal 0.5, M_TX04_Wall, M_TX04_Accent = trim x sect colour),
    // maps them by the FBX material names, adds LODGroups and mesh colliders, compares each module with its model_info.json
    // (size, base, LOD triangles, objects, materials, accent object, sockets, collision), recolours the accent once to prove the
    // interface, and places the academy from tx04-academy-assembly.json. Needs a graphics device (no -nographics):
    //   Unity -batchmode -quit -projectPath apps/game -executeMethod YunJing.Editor.Tx04BranchCourtVerify.Run -logFile <log>
    // Output: art/previews/tx04-branch-court/unity/*.png and report.txt; the run fails when a check fails.
    public static class Tx04BranchCourtVerify
    {
        const string Models = "Assets/YunJing/Models/Tx04BranchCourt";   // copied from art/exports, gitignored
        const string Pkg = "tx04-branch-court";
        static string Repo => Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", ".."));
        static string Exports => Path.Combine(Repo, "art/exports", Pkg);
        static string Out => Path.Combine(Repo, "art/previews", Pkg, "unity");
        static readonly List<string> Report = new List<string>();
        static int failures;
        static readonly Dictionary<string, Material> Mats = new Dictionary<string, Material>();
        static float sx = 1;   // Blender +X -> Unity sx * X, measured on the asymmetric WALL_CO

        [Serializable] class Lod { public int lod, triangles, objects, materials; }
        [Serializable] class Accent { public string material, @object, defaultColor; public float surfaceShare, limit; }
        [Serializable] class Socket { public string name; public float[] location_m; }
        [Serializable] class Info { public string id, minTier, collision; public float[] dimensions_m; public Lod[] lods; public string[] materials; public Accent accent; public Socket[] sockets; }
        [Serializable] class Part { public string id; public float[] pos; public float rotZ; }
        [Serializable] class Assembly { public Part[] parts; }

        static string[] Ids => Directory.GetFiles(Exports, "TX04_*.fbx").Select(f => Path.GetFileNameWithoutExtension(f).Substring(5)).OrderBy(s => s).ToArray();

        public static void Run()
        {
            Report.Clear(); failures = 0; Directory.CreateDirectory(Out);
            Import();
            QingxiUrpUpgrade.EnsurePipeline();
            Materials();
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene);
            Report.Add($"Unity {Application.unityVersion}, pipeline {GraphicsSettings.currentRenderPipeline?.name ?? "built-in"}");
            Measure();
            foreach (var id in Ids) Inspect(id, JsonUtility.FromJson<Info>(File.ReadAllText(Path.Combine(Exports, $"TX04_{id}.model_info.json"))));
            Shots();
            File.WriteAllLines(Path.Combine(Out, "report.txt"), Report);
            foreach (var line in Report) Debug.Log("TX04 " + line);
            if (failures > 0) throw new Exception($"TX04_VERIFY {failures} check(s) failed, see {Out}/report.txt");
            Debug.Log($"TX04_VERIFY_DONE all checks passed, output {Out}");
        }

        static void Check(bool ok, string line) { Report.Add((ok ? "PASS " : "FAIL ") + line); if (!ok) failures++; }

        // ------------------------------------------------------------------ import
        static void Import()
        {
            Copy(Exports, Path.Combine(Repo, "apps/game", Models), "TX04_*.fbx");
            Copy(Path.Combine(Repo, "art/textures/mountain-street-houses-a"), Path.Combine(Repo, "apps/game", Models, "Textures"), "T_MountainStreet_*.png");
            Copy(Path.Combine(Repo, "art/textures", Pkg), Path.Combine(Repo, "apps/game", Models, "Textures"), "T_TX04_*.png");
            AssetDatabase.Refresh();
            foreach (var guid in AssetDatabase.FindAssets("t:Model", new[] { Models }))
            {
                var importer = (ModelImporter)AssetImporter.GetAtPath(AssetDatabase.GUIDToAssetPath(guid));
                // keep the FBX material slots (names) so each submesh can be mapped to its shared URP material
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

        static int PngSize(string file) { var png = File.ReadAllBytes(file); return (png[16] << 24) | (png[17] << 16) | (png[18] << 8) | png[19]; }

        static void Materials()
        {
            Texture2D T(string name) => AssetDatabase.LoadAssetAtPath<Texture2D>($"{Models}/Textures/{name}.png");
            var albedo = T("T_MountainStreet_Albedo"); var normal = T("T_MountainStreet_Normal"); var ms = T("T_MountainStreet_MetallicSmoothness");
            var wAlb = T("T_TX04_Wall_Albedo"); var wNrm = T("T_TX04_Wall_Normal");
            Check(albedo && normal && ms, "shared MC01 trim sheet: Albedo / Normal / MetallicSmoothness imported");
            Check(wAlb && wNrm, "TX04 wall tile: T_TX04_Wall_Albedo / _Normal imported");
            foreach (var (t, src, size) in new[] { (albedo, "mountain-street-houses-a", 2048), (normal, "mountain-street-houses-a", 2048), (wAlb, Pkg, 1024), (wNrm, Pkg, 1024) })
            {
                if (!t) continue; int sw = PngSize(Path.Combine(Repo, "art/textures", src, t.name + ".png"));
                Check(sw == size && t.width == Math.Min(sw, 1024), $"{t.name}: source {sw}, imported {t.width} x {t.height} (QingxiImportBudget caps model textures at 1024)");
            }
            Material Make(string name)
            {
                var path = $"{Models}/{name}.mat"; var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
                if (mat == null) { mat = new Material(Shader.Find("Universal Render Pipeline/Lit")); AssetDatabase.CreateAsset(mat, path); }
                mat.enableInstancing = true; Mats[name] = mat; return mat;
            }
            void Trim(Material mat, float bump, Color c)
            {
                mat.SetTexture("_BaseMap", albedo); mat.SetColor("_BaseColor", c);
                mat.SetTexture("_BumpMap", normal); mat.SetFloat("_BumpScale", bump); mat.EnableKeyword("_NORMALMAP");
                mat.SetTexture("_MetallicGlossMap", ms); mat.EnableKeyword("_METALLICSPECGLOSSMAP"); mat.SetFloat("_Smoothness", 1);
                EditorUtility.SetDirty(mat);
            }
            Trim(Make("M_MountainStreet_Trim"), 1f, Color.white);
            Trim(Make("M_TX04_Roof"), .5f, Color.white);   // review #90: fine tile noise halved
            ColorUtility.TryParseHtmlString("#8E2F25", out var lacquer);
            Trim(Make("M_TX04_Accent"), 1f, lacquer);      // sect colour = _BaseColor over the plaster strip
            var accent = Mats["M_TX04_Accent"]; accent.DisableKeyword("_METALLICSPECGLOSSMAP"); accent.SetTexture("_MetallicGlossMap", null); accent.SetFloat("_Smoothness", .45f);
            var wall = Make("M_TX04_Wall");
            wall.SetTexture("_BaseMap", wAlb); wall.SetColor("_BaseColor", Color.white); wall.SetTexture("_BumpMap", wNrm); wall.SetFloat("_BumpScale", .6f);
            wall.EnableKeyword("_NORMALMAP"); wall.SetFloat("_Smoothness", .08f); EditorUtility.SetDirty(wall);
            AssetDatabase.SaveAssets();
        }

        static Material Map(Material m)
        {
            if (m == null) return Mats["M_MountainStreet_Trim"];
            foreach (var kv in Mats) if (m.name.StartsWith(kv.Key)) return kv.Value;
            return null;
        }

        static GameObject Place(string id, Vector3 at, float yaw, Transform parent = null)
        {
            var go = (GameObject)PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>($"{Models}/TX04_{id}.fbx"));
            go.transform.SetPositionAndRotation(at, Quaternion.Euler(0, yaw, 0)); if (parent) go.transform.SetParent(parent, true);
            foreach (var r in go.GetComponentsInChildren<Renderer>(true))
            {
                if (r.name.StartsWith($"TX04_{id}_Collision")) { r.enabled = false; continue; }
                r.sharedMaterials = r.sharedMaterials.Select(Map).ToArray();
            }
            if (go.GetComponent<LODGroup>() == null)
            {
                float[] cut = { .30f, .10f, .015f };
                var lods = Enumerable.Range(0, 3).Select(i => new LOD(cut[i], go.GetComponentsInChildren<Renderer>().Where(r => r.name.EndsWith("_LOD" + i)).ToArray())).ToArray();
                go.AddComponent<LODGroup>().SetLODs(lods);
            }
            var col = go.GetComponentsInChildren<MeshFilter>(true).FirstOrDefault(m => m.name == $"TX04_{id}_Collision");
            if (col != null && col.GetComponent<MeshCollider>() == null) col.gameObject.AddComponent<MeshCollider>().sharedMesh = col.sharedMesh;
            Physics.SyncTransforms();
            return go;
        }

        static Transform Node(GameObject go, string name) => go.GetComponentsInChildren<Transform>(true).FirstOrDefault(t => t.name == name);
        static Renderer[] Level(GameObject go, int i) => go.GetComponentsInChildren<Renderer>(true).Where(r => r.name.EndsWith("_LOD" + i)).ToArray();
        static int Tris(IEnumerable<Renderer> rs) => rs.Sum(r => { var m = r.GetComponent<MeshFilter>().sharedMesh; return Enumerable.Range(0, m.subMeshCount).Sum(s => (int)m.GetIndexCount(s)) / 3; });
        static Bounds Box(IEnumerable<Renderer> rs) { var a = rs.ToArray(); var b = a[0].bounds; foreach (var r in a) b.Encapsulate(r.bounds); return b; }

        // Blender -> Unity mapping, measured: WALL_CO's arm A runs to Blender -X, so its bounds centre has Blender x < 0.
        static void Measure()
        {
            var go = Place("WALL_CO", Vector3.zero, 0); var c = Box(Level(go, 0)).center.x; UnityEngine.Object.DestroyImmediate(go);
            sx = c < 0 ? 1 : -1;
            Report.Add($"INFO axis: Blender +X -> Unity {(sx > 0 ? "+X" : "-X")}, Blender +Y -> Unity +Z, Blender +Z -> Unity +Y (WALL_CO bounds centre x = {c:0.000})");
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
            var used = lod0.SelectMany(r => r.sharedMaterials).ToArray();
            Check(used.All(m => m != null), $"{id}: every FBX material slot mapped to a shared URP material");
            var names = used.Where(m => m).Select(m => m.name).Distinct().OrderBy(s => s).ToArray();
            Check(names.SequenceEqual(info.materials.OrderBy(s => s)), $"{id}: materials {string.Join(", ", names)} (model_info {string.Join(", ", info.materials)})");
            if (info.accent != null && !string.IsNullOrEmpty(info.accent.@object))
            {
                var acc = Node(go, info.accent.@object + "_LOD0")?.GetComponent<Renderer>();
                Check(acc && acc.sharedMaterials.All(m => m == Mats["M_TX04_Accent"]), $"{id}: {info.accent.@object} on M_TX04_Accent, lacquer share {info.accent.surfaceShare:P1} (limit {info.accent.limit:P0})");
            }
            else Report.Add($"INFO {id}: no lacquer (review #90: lacquer only on gate / hall doors, plaque frames, lintel band)");
            foreach (var s in info.sockets ?? new Socket[0])
            {
                var t = Node(go, s.name); var want = U(s.location_m);
                Check(t && Vector3.Distance(t.position, want) < .02f, $"{id}: {s.name} at {(t ? t.position.ToString("0.00") : "missing")} (Blender {string.Join(", ", s.location_m)})");
            }
            var lods = go.GetComponent<LODGroup>().GetLODs();
            Check(lods.Length == 3 && lods.All(l => l.renderers.Length == lod0.Length), $"{id}: LODGroup 3 levels x {lod0.Length} renderers");
            var col = Node(go, $"TX04_{id}_Collision")?.GetComponent<MeshCollider>();
            Check(col != null && col.sharedMesh.triangles.Length > 0, $"{id}: collision imported as MeshCollider ({(col ? col.sharedMesh.triangles.Length / 3 : 0)} tris), render hidden");
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
                var go = Place(id, Vector3.zero, 0); var b = Box(Level(go, 0)); var ruler = Ruler(new Vector3(b.max.x + .5f, 0, b.min.z - .4f));
                Frame($"modules/{id}", b, (front - side * .8f).normalized + Vector3.up * .5f);
                UnityEngine.Object.DestroyImmediate(ruler); UnityEngine.Object.DestroyImmediate(go);
            }
            var asm = JsonUtility.FromJson<Assembly>(File.ReadAllText(Path.Combine(Exports, "tx04-academy-assembly.json")));
            var root = new GameObject("TX04 academy"); int n = 0;
            foreach (var p in asm.parts)
            {
                if (!File.Exists(Path.Combine(Exports, $"TX04_{p.id}.fbx"))) { Check(false, $"academy: part {p.id} has no FBX"); continue; }
                Place(p.id, U(p.pos), Yaw(p.rotZ), root.transform); n++;
            }
            Check(n == asm.parts.Length, $"academy: {n} / {asm.parts.Length} modules placed from tx04-academy-assembly.json");
            var rs = root.GetComponentsInChildren<Renderer>().Where(r => r.enabled && r.name.EndsWith("_LOD0")).ToArray(); var ab = Box(rs);
            var ruler2 = Ruler(U(new[] { 1.6f, -6f, 0f }));
            Frame("assembly/academy-overview", ab, (front - side * .8f).normalized + Vector3.up * .75f, 1.0f);
            Frame("assembly/academy-front", ab, front + Vector3.up * .15f, 1.0f);
            Shot("assembly/academy-courtyard-eye-1p7m", U(new[] { -1.2f, -7.6f, 1.7f }), U(new[] { 0f, 4.5f, 3.6f }), 60);
            UnityEngine.Object.DestroyImmediate(ruler2); UnityEngine.Object.DestroyImmediate(root);
            // the sect colour interface, in the same scene as the shots: one material colour recolours every accent part, nothing else changes
            var acc = Mats["M_TX04_Accent"]; var keep = acc.GetColor("_BaseColor"); var probe = new Color(.16f, .30f, .42f);
            var g = Place("GATE", Vector3.zero, 0); var accR = Node(g, "TX04_GATE_Accent_LOD0").GetComponent<Renderer>(); var gb = Box(Level(g, 0));
            Frame("modules/GATE-recolour-before", gb, (front - side * .8f).normalized + Vector3.up * .4f);
            acc.SetColor("_BaseColor", probe);
            Check(accR.sharedMaterials.All(m => m == acc && m.GetColor("_BaseColor") == probe) && Mats["M_MountainStreet_Trim"].GetColor("_BaseColor") == Color.white,
                "accent recolour: M_TX04_Accent _BaseColor set to a blue sect colour, only the gate lacquer parts use it");
            Frame("modules/GATE-recolour-probe", gb, (front - side * .8f).normalized + Vector3.up * .4f);
            acc.SetColor("_BaseColor", keep); EditorUtility.SetDirty(acc); AssetDatabase.SaveAssets(); UnityEngine.Object.DestroyImmediate(g);
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
