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
    // Unity check of the 11/05 package A MC02 rope bridges (art/exports/mc02-rope-bridge, Johnnnny0823).
    // Imports MC02_B24 / MC02_B12 and the shared MC01 trim sheet, builds M_MountainStreet_Trim, LODGroups and mesh colliders,
    // compares each bridge with its model_info.json (size, bounds, LOD triangles, material, collision), then proves the deck is
    // walkable: rays down the deck centre line every 0.25 m must hit the collision within 3 cm of the modelled deck with no step
    // over 5 cm, and the existing CliffBoardwalk v001 placed on both ends by its connectors must meet the bridge with no step at
    // the joints. Renders module and joint shots. Needs a graphics device (no -nographics):
    //   Unity -batchmode -quit -projectPath apps/game -executeMethod YunJing.Editor.Mc02RopeBridgeVerify.Run -logFile <log>
    // Output: art/previews/mc02-rope-bridge/unity/*.png and report.txt; the run fails when a check fails.
    public static class Mc02RopeBridgeVerify
    {
        const string Models = "Assets/YunJing/Models/Mc02RopeBridge";   // copied from art/exports, gitignored
        const string Boardwalk = "Assets/YunJing/Models/CollaboratorWorldV1/CliffBoardwalk_v001.fbx";
        const string Pkg = "mc02-rope-bridge";
        static string Repo => Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", ".."));
        static string Exports => Path.Combine(Repo, "art/exports", Pkg);
        static string Out => Path.Combine(Repo, "art/previews", Pkg, "unity");
        static readonly List<string> Report = new List<string>();
        static int failures;
        static Material trim;

        [Serializable] class Lod { public int lod, triangles, objects, materials; }
        [Serializable] class Info { public string id; public float length_m, sag_m, bridgehead_m, deckWidth_m; public float[] dimensions_m, bounds_min_m, bounds_max_m; public Lod[] lods; public string[] materials; }
        [Serializable] class BwInfo { public Connectors connectors; }
        [Serializable] class Connectors { public float[] entry, exit; }

        static string[] Ids => Directory.GetFiles(Exports, "MC02_*.fbx").Select(f => Path.GetFileNameWithoutExtension(f).Substring(5)).OrderBy(s => s).ToArray();

        public static void Run()
        {
            Report.Clear(); failures = 0; Directory.CreateDirectory(Out);
            Import();
            QingxiUrpUpgrade.EnsurePipeline();
            Materials();
            Report.Add($"Unity {Application.unityVersion}, pipeline {GraphicsSettings.currentRenderPipeline?.name ?? "built-in"}");
            Setup();
            foreach (var id in Ids) Inspect(id, JsonUtility.FromJson<Info>(File.ReadAllText(Path.Combine(Exports, $"MC02_{id}.model_info.json"))));
            File.WriteAllLines(Path.Combine(Out, "report.txt"), Report);
            foreach (var line in Report) Debug.Log("MC02 " + line);
            if (failures > 0) throw new Exception($"MC02_VERIFY {failures} check(s) failed, see {Out}/report.txt");
            Debug.Log($"MC02_VERIFY_DONE all checks passed, output {Out}");
        }

        static void Check(bool ok, string line) { Report.Add((ok ? "PASS " : "FAIL ") + line); if (!ok) failures++; }

        static void Import()
        {
            Copy(Exports, Path.Combine(Repo, "apps/game", Models), "MC02_*.fbx");
            Copy(Path.Combine(Repo, "art/textures/mountain-street-houses-a"), Path.Combine(Repo, "apps/game", Models, "Textures"), "T_MountainStreet_*.png");
            AssetDatabase.Refresh();
            foreach (var guid in AssetDatabase.FindAssets("t:Model", new[] { Models }))
            {
                var importer = (ModelImporter)AssetImporter.GetAtPath(AssetDatabase.GUIDToAssetPath(guid));
                if (importer.bakeAxisConversion && importer.materialImportMode == ModelImporterMaterialImportMode.None) continue;
                importer.bakeAxisConversion = true; importer.importCameras = false; importer.importLights = false; importer.addCollider = false;
                importer.importAnimation = false; importer.materialImportMode = ModelImporterMaterialImportMode.None; importer.importTangents = ModelImporterTangents.CalculateMikk;
                importer.SaveAndReimport();
            }
            foreach (var guid in AssetDatabase.FindAssets("t:Texture2D", new[] { Models }))
            {
                var path = AssetDatabase.GUIDToAssetPath(guid); var ti = (TextureImporter)AssetImporter.GetAtPath(path);
                bool normal = path.EndsWith("_Normal.png"), linear = normal || path.EndsWith("_MetallicSmoothness.png");
                var type = normal ? TextureImporterType.NormalMap : TextureImporterType.Default;
                if (ti.textureType == type && ti.sRGBTexture == !linear) continue;   // QingxiImportBudget's 1024 cap is left alone
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

        static void Materials()
        {
            Texture2D T(string kind) => AssetDatabase.LoadAssetAtPath<Texture2D>($"{Models}/Textures/T_MountainStreet_{kind}.png");
            var albedo = T("Albedo"); var normal = T("Normal"); var ms = T("MetallicSmoothness");
            Check(albedo && normal && ms, "shared MC01 trim sheet: Albedo / Normal / MetallicSmoothness imported");
            var path = $"{Models}/M_MountainStreet_Trim.mat"; trim = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (trim == null) { trim = new Material(Shader.Find("Universal Render Pipeline/Lit")); AssetDatabase.CreateAsset(trim, path); }
            trim.SetTexture("_BaseMap", albedo); trim.SetColor("_BaseColor", Color.white);
            trim.SetTexture("_BumpMap", normal); trim.EnableKeyword("_NORMALMAP");
            trim.SetTexture("_MetallicGlossMap", ms); trim.EnableKeyword("_METALLICSPECGLOSSMAP"); trim.SetFloat("_Smoothness", 1);
            trim.enableInstancing = true; EditorUtility.SetDirty(trim); AssetDatabase.SaveAssets();
        }

        static GameObject Place(string id, Vector3 at)
        {
            if (trim == null) trim = AssetDatabase.LoadAssetAtPath<Material>($"{Models}/M_MountainStreet_Trim.mat");   // survives NewScene
            var go = (GameObject)PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>($"{Models}/MC02_{id}.fbx"));
            go.transform.position = at;
            foreach (var r in go.GetComponentsInChildren<Renderer>(true))
            {
                if (r.name.StartsWith($"MC02_{id}_Collision")) { r.enabled = false; continue; }
                r.sharedMaterials = Enumerable.Repeat(trim, r.sharedMaterials.Length).ToArray();
            }
            float[] cut = { .30f, .10f, .015f };   // the FBX importer may already add a LODGroup from the _LODn names
            (go.GetComponent<LODGroup>() ?? go.AddComponent<LODGroup>()).SetLODs(Enumerable.Range(0, 3).Select(i => new LOD(cut[i], go.GetComponentsInChildren<Renderer>().Where(r => r.name.EndsWith("_LOD" + i)).ToArray())).ToArray());
            var col = go.GetComponentsInChildren<MeshFilter>(true).FirstOrDefault(m => m.name == $"MC02_{id}_Collision");
            if (col != null) col.gameObject.AddComponent<MeshCollider>().sharedMesh = col.sharedMesh;
            Physics.SyncTransforms(); return go;
        }

        static Renderer[] Level(GameObject go, int i) => go.GetComponentsInChildren<Renderer>(true).Where(r => r.name.EndsWith("_LOD" + i)).ToArray();
        static int Tris(IEnumerable<Renderer> rs) => rs.Sum(r => { var m = r.GetComponent<MeshFilter>().sharedMesh; return Enumerable.Range(0, m.subMeshCount).Sum(s => (int)m.GetIndexCount(s)) / 3; });
        static Bounds Box(IEnumerable<Renderer> rs) { var a = rs.ToArray(); var b = a[0].bounds; foreach (var r in a) b.Encapsulate(r.bounds); return b; }

        // walking surface of the model (same formula as build_mc02.deck_z): 0 on the bridgeheads, a parabola sagging `sag` between them
        static float Deck(float y, Info i) { float a = i.bridgehead_m, b = i.length_m - i.bridgehead_m; if (y <= a || y >= b) return 0; float t = (y - a) / (b - a); return -i.sag_m * 4 * t * (1 - t); }

        static void Inspect(string id, Info info)
        {
            var go = Place(id, Vector3.zero);
            var lod0 = Level(go, 0); var b = Box(lod0); var d = info.dimensions_m;
            Check(Mathf.Abs(b.size.x - d[0]) < .02f && Mathf.Abs(b.size.z - d[1]) < .02f && Mathf.Abs(b.size.y - d[2]) < .02f,
                $"{id}: imported size {b.size.x:0.000} x {b.size.z:0.000} x {b.size.y:0.000} m matches model_info {d[0]} x {d[1]} x {d[2]}");
            Check(Mathf.Abs(b.min.z - info.bounds_min_m[1]) < .02f && Mathf.Abs(b.max.z - info.bounds_max_m[1]) < .02f,
                $"{id}: runs along +Z from {b.min.z:0.000} to {b.max.z:0.000} m (origin at end A, length {info.length_m} m)");
            var tris = Enumerable.Range(0, 3).Select(i => Tris(Level(go, i))).ToArray();
            Check(Enumerable.Range(0, 3).All(i => Mathf.Abs(tris[i] - info.lods[i].triangles) <= info.lods[i].triangles * .01f + 2),
                $"{id}: triangles LOD0/1/2 = {tris[0]} / {tris[1]} / {tris[2]}, model_info {info.lods[0].triangles} / {info.lods[1].triangles} / {info.lods[2].triangles}");
            Check(lod0.SelectMany(r => r.sharedMaterials).Distinct().Count() == 1, $"{id}: one shared material (M_MountainStreet_Trim)");
            var col = go.GetComponentsInChildren<MeshCollider>().FirstOrDefault();
            Check(col != null && col.sharedMesh.triangles.Length > 0, $"{id}: collision imported as MeshCollider ({(col ? col.sharedMesh.triangles.Length / 3 : 0)} tris), render hidden");

            // walkable deck: rays down the centre line
            // a step = a jump in height beyond what the slope itself gives between two samples (the 12 m deck is ~33 deg at its ends by spec)
            float worst = 0, maxStep = 0, prev = float.NaN, prevDeck = 0; int misses = 0, n = 0;
            for (float y = .1f; y <= info.length_m - .1f; y += .25f, n++)
            {
                if (!Physics.Raycast(new Vector3(0, 5, y), Vector3.down, out var hit, 20)) { misses++; continue; }
                var deck = Deck(y, info); worst = Mathf.Max(worst, Mathf.Abs(hit.point.y - deck));
                if (!float.IsNaN(prev)) maxStep = Mathf.Max(maxStep, Mathf.Abs((hit.point.y - prev) - (deck - prevDeck))); prev = hit.point.y; prevDeck = deck;
            }
            Check(misses == 0 && worst < .03f && maxStep < .05f, $"{id}: walkable deck, {n} rays along the centre line: {misses} misses, max offset from the modelled deck {worst * 100:0.0} cm, max step beyond the slope between 25 cm samples {maxStep * 100:0.0} cm");
            float wall = 0;
            foreach (var y in new[] { info.length_m * .25f, info.length_m * .5f })
                if (Physics.Raycast(new Vector3(0, Deck(y, info) + .6f, y), Vector3.right, out var h, 3)) wall = Mathf.Max(wall, h.distance);
            Check(wall > .5f && wall < 1.0f, $"{id}: guard collision at the deck edge ({wall:0.00} m from the centre line at 0.6 m above the deck)");

            // the existing CliffBoardwalk on both ends, by its connectors (Blender (x, y, z) -> Unity (x, z, y))
            var bw = JsonUtility.FromJson<BwInfo>(File.ReadAllText(Path.Combine(Repo, "art/incoming/dondon/CliffBoardwalk/v001/model_info.json"))).connectors;
            Vector3 U(float[] p) => new Vector3(p[0], p[2], p[1]);
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(Boardwalk);
            Check(prefab != null, $"{id}: CliffBoardwalk v001 found in the project ({Boardwalk})");
            if (prefab != null)
            {
                var A = (GameObject)PrefabUtility.InstantiatePrefab(prefab); A.transform.position = Vector3.zero - U(bw.exit);
                var B = (GameObject)PrefabUtility.InstantiatePrefab(prefab); B.transform.position = new Vector3(0, 0, info.length_m) - U(bw.entry);
                foreach (var mf in A.GetComponentsInChildren<MeshFilter>().Concat(B.GetComponentsInChildren<MeshFilter>())) mf.gameObject.AddComponent<MeshCollider>().sharedMesh = mf.sharedMesh;
                Physics.SyncTransforms();
                foreach (var (name, z0, z1) in new[] { ("end A", -1.0f, 1.0f), ("end B", info.length_m - 1.0f, info.length_m + 1.0f) })
                {
                    float lo = float.MaxValue, hi = float.MinValue; int hits = 0;
                    for (float z = z0; z <= z1; z += .1f)
                        // a 0.1 m sphere (a character's foot, not a needle) so the boardwalk's 1-2 cm plank gaps are not read as steps
                        if (Physics.SphereCast(new Vector3(.3f, 5, z), .1f, Vector3.down, out var hit, 20)) { var top = hit.point.y; lo = Mathf.Min(lo, top); hi = Mathf.Max(hi, top); hits++; }
                    Check(hits >= 19 && hi - lo < .03f, $"{id}: joint {name} with CliffBoardwalk: walking height {lo:0.000} .. {hi:0.000} m over 2 m across the joint (step {(hi - lo) * 100:0.0} cm)");
                }
                var bb = Box(lod0); bb.Encapsulate(Box(A.GetComponentsInChildren<Renderer>())); bb.Encapsulate(Box(B.GetComponentsInChildren<Renderer>()));
                Frame($"{id}-with-boardwalk", bb, new Vector3(-1, .45f, -.35f), 1.0f);
                Shot($"{id}-joint-A", new Vector3(-3.2f, 1.6f, -2.4f), new Vector3(0, 0, .8f), 40);
                UnityEngine.Object.DestroyImmediate(A); UnityEngine.Object.DestroyImmediate(B);
            }
            Frame($"{id}", b, new Vector3(-1, .4f, -.3f), 1.1f);
            UnityEngine.Object.DestroyImmediate(go);
        }

        // ------------------------------------------------------------------ renders
        static Camera cam; static RenderTexture target;
        static void Setup()
        {
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene);
            var sun = new GameObject("Sun").AddComponent<Light>(); sun.type = LightType.Directional; sun.shadows = LightShadows.Soft;
            sun.transform.rotation = Quaternion.Euler(40, -60, 0); sun.color = new Color(1, .86f, .66f); sun.intensity = 1.7f;
            RenderSettings.ambientMode = AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = new Color(.52f, .60f, .74f); RenderSettings.ambientEquatorColor = new Color(.50f, .50f, .48f); RenderSettings.ambientGroundColor = new Color(.30f, .27f, .22f);
            cam = new GameObject("Review Camera").AddComponent<Camera>(); cam.nearClipPlane = .05f; cam.farClipPlane = 400;
            cam.clearFlags = CameraClearFlags.SolidColor; cam.backgroundColor = new Color(.62f, .72f, .86f);
            UnityEngine.Rendering.Universal.CameraExtensions.GetUniversalAdditionalCameraData(cam).renderPostProcessing = true;
            target = new RenderTexture(1600, 1000, 24) { antiAliasing = 4 }; cam.targetTexture = target;
        }

        static void Frame(string file, Bounds b, Vector3 dir, float pad)
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
    }
}
