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
    // Work pack 2026-11-07, LOD backfill (art/exports/lod-backfill-b): StarterHouse, Blacksmith, TownInn, qingxi-alchemy-b B01-B12,
    // creek-repair-b-props C03/C04/C06/C07 and A04. Imports each <ID>_LOD_v001.fbx into a gitignored folder and checks it against its
    // model_info.json: <ID>_LOD0/1/2 and <ID>_Detail_Small_LOD0/1/2 present as their own objects, triangles and objects per level equal,
    // imported size equal (2 mm), a LODGroup with three filled levels can be built, no missing / error shaders; one URP capture per asset
    // with LOD0 / LOD1 / LOD2 / LOD1 without Detail side by side.
    // Writes artifacts/lod-backfill-unity/. Run with -executeMethod YunJing.Editor.LodBackfillModelCheck.Run
    // This is an editor batch check, not play in the game: nothing is placed in the main scene.
    public static class LodBackfillModelCheck
    {
        const string Root = "Assets/YunJing/Generated/LodBackfillB";
        static string Repo => Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", ".."));
        static string Exports => Path.Combine(Repo, "art", "exports", "lod-backfill-b");
        static string Out => Path.Combine(Repo, "artifacts", "lod-backfill-unity");
        static readonly List<string> Report = new List<string>();
        static int failed;

        [Serializable] class Budget { public int triangles, triangles_without_detail, objects, objects_without_detail, materials; }
        [Serializable] class BudgetPerLod { public Budget LOD0, LOD1, LOD2; }
        [Serializable] class ModelInfo { public string asset, version, minTier, fbx; public int lod0_zero_area_triangles; public float[] dimensions_m; public BudgetPerLod budget_per_lod; public string[] detailObjects; }

        static void Check(bool ok, string what) { Report.Add((ok ? "PASS " : "FAIL ") + what); if (!ok) failed++; }

        static void UsePipeline()
        {
            var pipeline = AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>("Assets/YunJing/Generated/URP.asset");
            if (pipeline == null) { ProjectBuilder.Generate(); pipeline = AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>("Assets/YunJing/Generated/URP.asset"); }
            if (GraphicsSettings.defaultRenderPipeline != pipeline) GraphicsSettings.defaultRenderPipeline = pipeline;
            if (QualitySettings.renderPipeline != pipeline) QualitySettings.renderPipeline = pipeline;
        }

        public static void Run()
        {
            Report.Clear(); failed = 0;
            UsePipeline();
            if (Directory.Exists(Out)) Directory.Delete(Out, true);
            Directory.CreateDirectory(Out);
            var infos = Directory.GetDirectories(Exports).Where(d => File.Exists(Path.Combine(d, "model_info.json")))
                .Select(d => JsonUtility.FromJson<ModelInfo>(File.ReadAllText(Path.Combine(d, "model_info.json")))).OrderBy(i => i.asset).ToList();
            Report.Add("INFO checked: " + infos.Count + " assets: " + string.Join(", ", infos.Select(i => i.asset)));
            foreach (var i in infos) Copy(i);
            AssetDatabase.Refresh();
            foreach (var i in infos) Configure(i);
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            Lighting();
            foreach (var i in infos)
            {
                var go = Place(i, Vector3.zero);
                Verify(i, go);
                Capture(i, go);
                UnityEngine.Object.DestroyImmediate(go);
            }
            File.WriteAllText(Path.Combine(Out, "unity-verify-report.txt"), string.Join("\n", Report) + $"\n\nUnity {Application.unityVersion}; failed checks: {failed}; editor batch check only, not placed in the main scene, not played\n");
            Debug.Log("LOD_BACKFILL_" + (failed == 0 ? "PASS" : "FAIL") + "\n" + string.Join("\n", Report));
            if (failed > 0 && Application.isBatchMode) EditorApplication.Exit(1);
        }

        static string Fbx(ModelInfo i) => $"{Root}/{i.asset}/{i.fbx}";

        static void Copy(ModelInfo i)
        {
            var src = Path.Combine(Exports, i.asset); var dst = Path.Combine(Repo, "apps", "game", Root, i.asset);
            Directory.CreateDirectory(dst);
            File.Copy(Path.Combine(src, i.fbx), Path.Combine(dst, i.fbx), true);
            foreach (var fbm in Directory.GetDirectories(src, "*.fbm"))              // textures the source FBX carried, beside the FBX as exported
            {
                var to = Path.Combine(dst, Path.GetFileName(fbm)); Directory.CreateDirectory(to);
                foreach (var f in Directory.GetFiles(fbm)) File.Copy(f, Path.Combine(to, Path.GetFileName(f)), true);
            }
        }

        static void Configure(ModelInfo i)
        {
            var importer = AssetImporter.GetAtPath(Fbx(i)) as ModelImporter;
            if (importer == null) throw new FileNotFoundException("FBX not imported", i.asset);
            importer.bakeAxisConversion = true; importer.isReadable = true;
            importer.materialImportMode = ModelImporterMaterialImportMode.ImportViaMaterialDescription;
            importer.materialLocation = ModelImporterMaterialLocation.InPrefab;
            importer.importAnimation = false; importer.importCameras = false; importer.importLights = false; importer.addCollider = false;
            importer.importNormals = ModelImporterNormals.Import;
            importer.SaveAndReimport();
        }

        static GameObject Place(ModelInfo i, Vector3 position)
        {
            var go = (GameObject)PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>(Fbx(i)));
            PrefabUtility.UnpackPrefabInstance(go, PrefabUnpackMode.Completely, InteractionMode.AutomatedAction);
            go.transform.position = position;
            var cut = new[] { .1f, .035f, .006f };
            var group = go.GetComponent<LODGroup>(); if (group == null) group = go.AddComponent<LODGroup>();   // Unity already adds one for _LOD0/1/2 names
            group.SetLODs(Enumerable.Range(0, 3).Select(k => new LOD(cut[k], go.GetComponentsInChildren<Renderer>(true).Where(r => r.name.EndsWith("_LOD" + k)).ToArray())).ToArray());
            return go;
        }

        static Bounds LodBounds(GameObject go, string suffix)
        {
            var rs = go.GetComponentsInChildren<Renderer>(true).Where(r => r.name.EndsWith(suffix)).ToArray();
            var b = rs[0].bounds; foreach (var r in rs) b.Encapsulate(r.bounds); return b;
        }

        static void Verify(ModelInfo i, GameObject go)
        {
            var id = i.asset;
            var mfs = go.GetComponentsInChildren<MeshFilter>(true);
            Check(Enumerable.Range(0, 3).All(k => mfs.Any(m => m.name == $"{id}_LOD{k}")), $"{id}: {id}_LOD0/1/2 present");
            var b = LodBounds(go, "_LOD0"); Vector3 size = b.size; float[] want = i.dimensions_m;
            float e = Mathf.Max(Mathf.Abs(size.x - want[0]), Mathf.Abs(size.z - want[1]), Mathf.Abs(size.y - want[2]));
            Check(e < .002f, $"{id}: imported LOD0 size {size.x:F3} x {size.z:F3} x {size.y:F3} m matches model_info (max error {e * 1000:F1} mm)");
            var bl = new[] { i.budget_per_lod.LOD0, i.budget_per_lod.LOD1, i.budget_per_lod.LOD2 };
            int tri(string s) => mfs.Where(m => m.name.EndsWith(s)).Sum(m => m.sharedMesh.triangles.Length / 3);
            int objs(string s) => mfs.Count(m => m.name.EndsWith(s));
            // LOD0 is the source left unedited; Unity drops the source's zero-area triangles on import, so LOD0 may come in up to
            // lod0_zero_area_triangles short. LOD1 / LOD2 are rebuilt without them and must match exactly.
            bool same(int got, int want, int k) => k == 0 ? got <= want && want - got <= i.lod0_zero_area_triangles : got == want;
            Check(Enumerable.Range(0, 3).All(k => same(tri("_LOD" + k), bl[k].triangles, k)),
                  $"{id}: imported triangles {tri("_LOD0")}/{tri("_LOD1")}/{tri("_LOD2")} equal model_info {bl[0].triangles}/{bl[1].triangles}/{bl[2].triangles}" +
                  (i.lod0_zero_area_triangles > 0 ? $" (LOD0 may drop the source's {i.lod0_zero_area_triangles} zero-area triangles: dropped {bl[0].triangles - tri("_LOD0")})" : ""));
            Check(Enumerable.Range(0, 3).All(k => objs("_LOD" + k) == bl[k].objects),
                  $"{id}: objects per LOD {objs("_LOD0")}/{objs("_LOD1")}/{objs("_LOD2")} equal model_info {bl[0].objects}/{bl[1].objects}/{bl[2].objects}");
            foreach (var d in i.detailObjects ?? new string[0])
                Check(Enumerable.Range(0, 3).All(k => mfs.Any(m => m.name == $"{d}_LOD{k}")), $"{id}: {d} present at LOD0/1/2 as its own object (can be switched off)");
            int body(string s) => mfs.Where(m => m.name == id + s).Sum(m => m.sharedMesh.triangles.Length / 3);
            Check(Enumerable.Range(0, 3).All(k => same(body("_LOD" + k), bl[k].triangles_without_detail, k)),
                  $"{id}: triangles without Detail {body("_LOD0")}/{body("_LOD1")}/{body("_LOD2")} equal model_info {bl[0].triangles_without_detail}/{bl[1].triangles_without_detail}/{bl[2].triangles_without_detail}");
            var lod = go.GetComponent<LODGroup>();
            Check(lod.GetLODs().Length == 3 && lod.GetLODs().All(l => l.renderers.Length > 0), $"{id}: LODGroup with 3 filled levels");
            Check(!go.GetComponentsInChildren<Renderer>(true).Any(r => r.sharedMaterials.Any(m => m == null || m.shader.name.Contains("Error"))), $"{id}: no missing or error shaders");
            Report.Add($"INFO {id}: minTier {i.minTier}");
        }

        static void Capture(ModelInfo i, GameObject go)
        {
            // four copies side by side: LOD0, LOD1, LOD2, LOD1 with Detail_* off
            var b = LodBounds(go, "_LOD0"); float step = Mathf.Max(b.size.x, b.size.z) * 1.25f;
            var copies = new List<GameObject>();
            for (int n = 0; n < 4; n++)
            {
                var c = UnityEngine.Object.Instantiate(go); c.transform.position = new Vector3(n * step, 0, 0);
                UnityEngine.Object.DestroyImmediate(c.GetComponent<LODGroup>());
                int lv = n == 3 ? 1 : n;
                foreach (var r in c.GetComponentsInChildren<Renderer>(true)) r.enabled = r.name.EndsWith("_LOD" + lv) && !(n == 3 && r.name.Contains("_Detail_"));
                copies.Add(c);
            }
            go.SetActive(false);
            var all = new Bounds(b.center, b.size); all.Encapsulate(b.center + new Vector3(3 * step, 0, 0)); all.Expand(b.size * .5f);
            float d = all.size.magnitude * .95f; var t = all.center;
            Shot(i.asset + "_LOD0_LOD1_LOD2_LOD1nodetail", t, t + new Vector3(.25f, .45f, -1).normalized * d, 35);
            foreach (var c in copies) UnityEngine.Object.DestroyImmediate(c);
            go.SetActive(true);
        }

        static void Lighting()
        {
            RenderSettings.ambientMode = AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = new Color(.62f, .68f, .7f); RenderSettings.ambientEquatorColor = new Color(.45f, .44f, .38f); RenderSettings.ambientGroundColor = new Color(.2f, .18f, .14f);
            var sun = new GameObject("Sun").AddComponent<Light>(); sun.type = LightType.Directional; sun.intensity = 1.25f;
            sun.color = new Color(1, .96f, .88f); sun.transform.rotation = Quaternion.Euler(38, -30, 0); sun.shadows = LightShadows.Soft;
            var cam = new GameObject("Main Camera", typeof(Camera)).GetComponent<Camera>(); cam.tag = "MainCamera"; cam.nearClipPlane = .01f; cam.farClipPlane = 300;
            cam.clearFlags = CameraClearFlags.SolidColor; cam.backgroundColor = new Color(.74f, .82f, .84f);
            cam.GetUniversalAdditionalCameraData().renderPostProcessing = false;
        }

        static void Shot(string file, Vector3 target, Vector3 eye, float fov = 40)
        {
            var cam = Camera.main; var rt = new RenderTexture(1600, 600, 24, RenderTextureFormat.ARGB32) { antiAliasing = 4 };
            cam.transform.position = eye; cam.transform.LookAt(target); cam.fieldOfView = fov; cam.targetTexture = rt; cam.Render();
            RenderTexture.active = rt; var tex = new Texture2D(1600, 600, TextureFormat.RGB24, false); tex.ReadPixels(new Rect(0, 0, 1600, 600), 0, 0); tex.Apply();
            File.WriteAllBytes(Path.Combine(Out, file + ".png"), tex.EncodeToPNG()); UnityEngine.Object.DestroyImmediate(tex);
            RenderTexture.active = null; cam.targetTexture = null; rt.Release(); Report.Add("SHOT " + file);
        }
    }
}
