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
    // Unity check of C's old-set LOD backfill (art/exports/lod-backfill-c: #34 Q01–Q04, #35 C01–C08; Eli-0731). It does not change
    // apps/game: run_unity_check.sh copies this file in for one batch run and removes it with the temporary model copies.
    // Imports each <ID>_LOD_v001.fbx with its Textures folder (materials from the file), puts the _LOD0/1/2 meshes in one 3-level
    // LODGroup, and compares with model_info.json: LOD0 triangles equal to the source, LOD1/LOD2 triangles, objects per LOD,
    // materials, size within 2 cm of the source; renders LOD0/1/2 of every item side by side.
    //   Unity -batchmode -quit -projectPath apps/game -executeMethod YunJing.Editor.LodCVerify.Run -logFile <log>
    public static class LodCVerify
    {
        const string Models = "Assets/YunJing/Models/LodBackfillC";   // temporary copy of art/exports, removed by the run script
        static readonly string[] Ids = { "Q01", "Q02", "Q03", "Q04", "C01", "C02", "C03", "C04", "C05", "C06", "C07", "C08" };
        static string Repo => Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", ".."));
        static string Out => Path.Combine(Repo, "art/previews/lod-backfill-c/unity");
        static readonly List<string> Report = new List<string>();
        static int failures;

        [Serializable] class Lod { public int triangles, objects, materials; }
        [Serializable] class Lods { public Lod LOD0, LOD1, LOD2; public Lod[] All => new[] { LOD0, LOD1, LOD2 }; }
        [Serializable] class Info { public float[] dimensions_xyz_m, source_dimensions_xyz_m; public int source_triangles; public Lods lods; }

        public static void Run()
        {
            Report.Clear(); failures = 0; Directory.CreateDirectory(Out);
            foreach (var id in Ids) Copy(Path.Combine(Repo, "art/exports/lod-backfill-c", id), Path.Combine(Repo, "apps/game", Models, id));
            AssetDatabase.Refresh();
            foreach (var guid in AssetDatabase.FindAssets("t:Model", new[] { Models }))
            {
                var im = (ModelImporter)AssetImporter.GetAtPath(AssetDatabase.GUIDToAssetPath(guid));
                im.bakeAxisConversion = true; im.importCameras = false; im.importLights = false; im.addCollider = false; im.importAnimation = false;
                im.materialImportMode = ModelImporterMaterialImportMode.ImportStandard; im.materialLocation = ModelImporterMaterialLocation.InPrefab;
                im.materialSearch = ModelImporterMaterialSearch.Local; im.SaveAndReimport();
            }
            QingxiUrpUpgrade.EnsurePipeline();
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene);
            var json = File.ReadAllText(Path.Combine(Repo, "art/exports/lod-backfill-c/model_info.json"));
            Report.Add($"Unity {Application.unityVersion}, pipeline {GraphicsSettings.currentRenderPipeline?.name ?? "built-in"}");
            Setup();
            foreach (var id in Ids) Inspect(id, JsonUtility.FromJson<Info>(Block(json, id)));
            File.WriteAllLines(Path.Combine(Out, "report.txt"), Report);
            foreach (var line in Report) Debug.Log("LODC " + line);
            if (failures > 0) throw new Exception($"LODC_VERIFY {failures} check(s) failed, see {Out}/report.txt");
            Debug.Log($"LODC_VERIFY_DONE all checks passed, output {Out}");
        }

        static void Check(bool ok, string line) { Report.Add((ok ? "PASS " : "FAIL ") + line); if (!ok) failures++; }
        static string Block(string text, string key)
        {
            int at = text.IndexOf($"\"{key}\":", StringComparison.Ordinal); int start = text.IndexOf('{', at), depth = 0;
            for (int i = start; i < text.Length; i++) { if (text[i] == '{') depth++; else if (text[i] == '}' && --depth == 0) return text.Substring(start, i - start + 1); }
            throw new InvalidDataException("model_info.json: no item " + key);
        }
        static void Copy(string src, string dst)
        {
            foreach (var file in Directory.GetFiles(src, "*", SearchOption.AllDirectories).Where(f => f.EndsWith(".fbx") || f.EndsWith(".png")))
            {
                if (new FileInfo(file).Length < 1024 && File.ReadAllText(file).StartsWith("version https://git-lfs")) throw new InvalidOperationException("Git LFS pointer: " + file);
                var t = Path.Combine(dst, file.Substring(src.Length + 1)); Directory.CreateDirectory(Path.GetDirectoryName(t)); File.Copy(file, t, true);
            }
        }
        static Renderer[] Level(GameObject go, int i) => go.GetComponentsInChildren<Renderer>(true).Where(r => r.name.EndsWith("_LOD" + i)).ToArray();
        static int Tris(IEnumerable<Renderer> rs) => rs.Sum(r => { var m = r.GetComponent<MeshFilter>().sharedMesh; return Enumerable.Range(0, m.subMeshCount).Sum(s => (int)m.GetIndexCount(s)) / 3; });
        static Bounds Box(IEnumerable<Renderer> rs) { var a = rs.ToArray(); var b = a[0].bounds; foreach (var r in a) b.Encapsulate(r.bounds); return b; }

        static void Inspect(string id, Info info)
        {
            var go = (GameObject)PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>($"{Models}/{id}/{id}_LOD_v001.fbx"));
            var lv = Enumerable.Range(0, 3).Select(i => Level(go, i)).ToArray();
            float[] cut = { .25f, .08f, .015f };
            var g = go.GetComponent<LODGroup>(); if (g == null) g = go.AddComponent<LODGroup>(); g.SetLODs(Enumerable.Range(0, 3).Select(i => new LOD(cut[i], lv[i])).ToArray());
            Check(g.GetLODs().Length == 3 && lv.All(l => l.Length >= 1), $"{id}: one LODGroup, 3 levels, {string.Join(" / ", lv.Select(l => l.Length))} renderer(s)");
            var tris = lv.Select(Tris).ToArray(); var L = info.lods.All;
            Check(tris[0] == info.source_triangles, $"{id}: LOD0 {tris[0]} triangles = the source {info.source_triangles} (LOD0 untouched)");
            Check(Enumerable.Range(0, 3).All(i => Mathf.Abs(tris[i] - L[i].triangles) <= L[i].triangles * .01f) && tris[1] < tris[0] && tris[2] <= tris[1],
                $"{id}: triangles LOD0/1/2 = {tris[0]} / {tris[1]} / {tris[2]} ({100f * tris[1] / tris[0]:0}% / {100f * tris[2] / tris[0]:0}%), model_info {L[0].triangles} / {L[1].triangles} / {L[2].triangles}");
            Check(Enumerable.Range(0, 3).All(i => lv[i].Length == L[i].objects), $"{id}: objects per LOD {string.Join(" / ", lv.Select(l => l.Length))}");
            var mats = Enumerable.Range(0, 3).Select(i => lv[i].SelectMany(r => r.sharedMaterials).Where(m => m).Select(m => m.name).Distinct().Count()).ToArray();
            Check(mats.All(m => m == mats[0]) && mats[0] == L[0].materials, $"{id}: materials per LOD {string.Join(" / ", mats)} (same set on every level; model_info {L[0].materials})");
            var notex = lv[0].SelectMany(r => r.sharedMaterials).Where(m => m && m.HasProperty("_BaseMap") && m.GetTexture("_BaseMap") == null && m.HasProperty("_MainTex") && m.GetTexture("_MainTex") == null).Select(m => m.name).Distinct().ToArray();
            var b = Box(lv[0]); var d = info.source_dimensions_xyz_m;
            Check(Mathf.Abs(b.size.x - d[0]) <= .02f && Mathf.Abs(b.size.z - d[1]) <= .02f && Mathf.Abs(b.size.y - d[2]) <= .02f, $"{id}: LOD0 size {b.size.x:0.000} x {b.size.z:0.000} x {b.size.y:0.000} m = the source {d[0]} x {d[1]} x {d[2]} within 2 cm");
            Report.Add($"INFO {id}: materials without a base texture in Unity: {(notex.Length == 0 ? "none" : string.Join(", ", notex))}");
            // LOD0, LOD1, LOD2 side by side (same item three times, each forced to one level)
            var copies = new List<GameObject> { go };
            for (int i = 1; i < 3; i++) { var c = UnityEngine.Object.Instantiate(go); c.transform.position = Vector3.right * (b.size.x + .3f) * i; copies.Add(c); }
            for (int i = 0; i < 3; i++) copies[i].GetComponent<LODGroup>().ForceLOD(i);
            var all = Box(copies.SelectMany(c => c.GetComponentsInChildren<Renderer>()));
            Frame($"{id}-lod012", all, (Vector3.back + Vector3.left * .6f).normalized + Vector3.up * .55f, 1.1f);
            foreach (var c in copies) UnityEngine.Object.DestroyImmediate(c);
        }

        static Camera cam; static RenderTexture target;
        static void Setup()
        {
            var sun = new GameObject("Sun").AddComponent<Light>(); sun.type = LightType.Directional; sun.shadows = LightShadows.Soft;
            sun.transform.rotation = Quaternion.Euler(38, -40, 0); sun.color = new Color(1, .86f, .66f); sun.intensity = 1.7f;
            RenderSettings.ambientMode = AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = new Color(.52f, .60f, .74f); RenderSettings.ambientEquatorColor = new Color(.50f, .50f, .48f); RenderSettings.ambientGroundColor = new Color(.30f, .27f, .22f);
            var ground = GameObject.CreatePrimitive(PrimitiveType.Plane); ground.transform.localScale = Vector3.one * 8;
            var gm = new Material(Shader.Find("Universal Render Pipeline/Lit")); gm.SetColor("_BaseColor", new Color(.40f, .38f, .33f)); ground.GetComponent<Renderer>().sharedMaterial = gm;
            cam = new GameObject("Review Camera").AddComponent<Camera>(); cam.nearClipPlane = .02f; cam.farClipPlane = 300;
            cam.clearFlags = CameraClearFlags.SolidColor; cam.backgroundColor = new Color(.62f, .72f, .86f);
            target = new RenderTexture(1280, 960, 24) { antiAliasing = 4 }; cam.targetTexture = target;
        }
        static void Frame(string file, Bounds b, Vector3 dir, float pad)
        {
            float dist = b.extents.magnitude * pad / Mathf.Sin(15 * Mathf.Deg2Rad);
            cam.fieldOfView = 30; cam.transform.position = b.center + dir.normalized * dist; cam.transform.LookAt(b.center); cam.Render();
            RenderTexture.active = target; var image = new Texture2D(target.width, target.height, TextureFormat.RGB24, false);
            image.ReadPixels(new Rect(0, 0, target.width, target.height), 0, 0); image.Apply();
            File.WriteAllBytes(Path.Combine(Out, file + ".png"), image.EncodeToPNG()); RenderTexture.active = null; UnityEngine.Object.DestroyImmediate(image);
        }
    }
}
