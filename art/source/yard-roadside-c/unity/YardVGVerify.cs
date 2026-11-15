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
    // Unity check of C's yard and roadside props VG01–VG08 (art/exports/yard-roadside-c, Eli-0731), after art/source/village-life-c/unity (itself after the modelling-basics-c
    // check (QingxiBasicsVerify). It does not change apps/game: run_unity_check.sh copies this file in for one batch run and removes it.
    // Imports the delivered FBX and textures, builds one URP Lit per item, compares with model_info.json (size within 2 cm, the work
    // pack's size limit, triangles per LOD, objects, one material, 1024 textures, minTier, detailObjects), switches Detail_* off the
    // way the standard tier will, and renders review shots. Items in Cloth (open weave, thin cloth) get a two-sided material.
    //   Unity -batchmode -quit -projectPath apps/game -executeMethod YunJing.Editor.YardVGVerify.Run -logFile <log>
    // Output: art/previews/yard-roadside-c/unity/*.png and report.txt; the run fails when a check fails.
    public static class YardVGVerify
    {
        const string Models = "Assets/YunJing/Models/YardC";   // temporary copy of art/exports, removed by the run script
        const string Version = "v001";
        static readonly string[] AllIds = { "VG01", "VG02", "VG03", "VG04_01", "VG04_02", "VG05", "VG06", "VG07", "VG08" };
        static string[] Ids;   // the ones model_info.json holds (the two batches are delivered separately)
        const string Old = "LV05";   // an older prop of C's (village-life-c, merged in #116) for the side-by-side shot
        static readonly HashSet<string> Cloth = new HashSet<string> { "VG01", "VG02", "VG03", "VG04_01", "VG04_02" };   // single-sided leaves, cloth cards, thatch skirts: both faces
        static readonly HashSet<string> Cutout = new HashSet<string> { "VG02", "VG03", "VG04_01", "VG04_02" };   // alpha-clip cards: vine leaves, frayed hems, straw fringes (work pack §3.4)
        static readonly HashSet<string> Collide = new HashSet<string> { "VG01", "VG05", "VG07", "VG08" };   // work pack §3.5: a simple collider
        static string Repo => Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", ".."));
        static string Out => Path.Combine(Repo, "art/previews/yard-roadside-c/unity");
        static readonly List<string> Report = new List<string>();
        static int failures;
        static string json;

        [Serializable] class Lod { public int triangles, objects, materials; }
        [Serializable] class Lods { public Lod LOD0, LOD1, LOD2; public Lod[] All => new[] { LOD0, LOD1, LOD2 }; }
        [Serializable] class Info { public float[] dimensions_xyz_m, body_dimensions_xyz_m, size_limit_xyz_m; public string minTier, material; public string[] detailObjects, detailMeshes; public Lods lods; }

        public static void Run()
        {
            Report.Clear(); failures = 0;
            Directory.CreateDirectory(Out);
            json = File.ReadAllText(Path.Combine(Repo, "art/exports/yard-roadside-c/model_info.json"));
            Ids = AllIds.Where(id => json.Contains($"\"{id}\":")).ToArray();
            Import();
            QingxiUrpUpgrade.EnsurePipeline();
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene);
            Report.Add($"Unity {Application.unityVersion}, pipeline {GraphicsSettings.currentRenderPipeline?.name ?? "built-in"}");
            foreach (var id in Ids) Inspect(id, JsonUtility.FromJson<Info>(Block(json, id)));
            Shots();
            File.WriteAllLines(Path.Combine(Out, "report.txt"), Report);
            foreach (var line in Report) Debug.Log("VG " + line);
            if (failures > 0) throw new Exception($"VG_VERIFY {failures} check(s) failed, see {Out}/report.txt");
            Debug.Log($"VG_VERIFY_DONE all checks passed, output {Out}");
        }

        static void Check(bool ok, string line) { Report.Add((ok ? "PASS " : "FAIL ") + line); if (!ok) failures++; }

        static string Block(string text, string key)
        {
            int at = text.IndexOf($"\"{key}\":", StringComparison.Ordinal);
            if (at < 0) throw new InvalidDataException("model_info.json: no item " + key);
            int start = text.IndexOf('{', at), depth = 0;
            for (int i = start; i < text.Length; i++)
            {
                if (text[i] == '{') depth++;
                else if (text[i] == '}' && --depth == 0) return text.Substring(start, i - start + 1);
            }
            throw new InvalidDataException("model_info.json: no item " + key);
        }

        // ------------------------------------------------------------------ import
        static void Import()
        {
            foreach (var id in Ids)
            {
                Copy(Path.Combine(Repo, "art/exports/yard-roadside-c"), Path.Combine(Repo, "apps/game", Models, id), $"{id}_{Version}.fbx");
                Copy(Path.Combine(Repo, "art/textures/yard-roadside-c"), Path.Combine(Repo, "apps/game", Models, id, "Textures"), id + "_*.png");
            }
            Copy(Path.Combine(Repo, "art/exports/village-life-c"), Path.Combine(Repo, "apps/game", Models, Old), $"{Old}_{Version}.fbx");
            Copy(Path.Combine(Repo, "art/textures/village-life-c"), Path.Combine(Repo, "apps/game", Models, Old, "Textures"), Old + "_*.png");
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
                bool cut = Cutout.Any(c => path.EndsWith($"/{c}_Albedo.png"));   // alpha-tested cards: keep their coverage in the smaller mips, or leaves and fringes thin out with distance
                if (ti.textureType == type && ti.sRGBTexture == !linear && ti.mipMapsPreserveCoverage == cut) continue;
                ti.textureType = type; ti.sRGBTexture = !linear; ti.mipmapEnabled = true;
                ti.mipMapsPreserveCoverage = cut; if (cut) { ti.alphaTestReferenceValue = .5f; ti.alphaSource = TextureImporterAlphaSource.FromInput; }
                ti.SaveAndReimport();
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

        // One URP Lit per item: Albedo, Normal, MaskURP (R metal, G AO, A smoothness); cloth renders both faces.
        static readonly Dictionary<string, Material> Mats = new Dictionary<string, Material>();
        static Material Mat(string id, string name)
        {
            if (Mats.TryGetValue(id, out var cached)) return cached;
            var dir = $"{Models}/{id}/Materials"; Directory.CreateDirectory(Path.Combine(Repo, "apps/game", dir));
            var path = $"{dir}/{name}.mat";
            var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (mat == null) { mat = new Material(Shader.Find("Universal Render Pipeline/Lit")); AssetDatabase.CreateAsset(mat, path); }
            var albedo = Tex(id, "Albedo"); var mask = Tex(id, "MaskURP"); var normal = Tex(id, "Normal");
            Check(albedo != null && mask != null && normal != null, $"{id}: Albedo / MaskURP / Normal textures found");
            var sizes = new[] { albedo, mask, normal }.Where(t => t).Select(t => $"{t.width}x{t.height}").Distinct().ToArray();
            Check(new[] { albedo, mask, normal }.All(t => t && t.width <= 1024 && t.height <= 1024), $"{id}: textures {string.Join(", ", sizes)} (1024 or less)");
            mat.SetTexture("_BaseMap", albedo); mat.SetColor("_BaseColor", Color.white);
            mat.SetTexture("_BumpMap", normal); mat.EnableKeyword("_NORMALMAP");
            mat.SetTexture("_MetallicGlossMap", mask); mat.EnableKeyword("_METALLICSPECGLOSSMAP"); mat.SetFloat("_Smoothness", 1);
            mat.SetTexture("_OcclusionMap", mask); mat.EnableKeyword("_OCCLUSIONMAP");
            if (Cloth.Contains(id)) mat.SetFloat("_Cull", (float)CullMode.Off);
            if (Cutout.Contains(id)) { mat.SetFloat("_AlphaClip", 1); mat.SetFloat("_Cutoff", .5f); mat.EnableKeyword("_ALPHATEST_ON"); mat.SetOverrideTag("RenderType", "TransparentCutout"); mat.renderQueue = (int)RenderQueue.AlphaTest; }
            EditorUtility.SetDirty(mat); Mats[id] = mat;
            return mat;
        }
        static Texture2D Tex(string id, string kind) => AssetDatabase.LoadAssetAtPath<Texture2D>($"{Models}/{id}/Textures/{id}_{kind}.png");

        static GameObject Place(string id, string material, Vector3 at, float yaw)
        {
            var go = (GameObject)PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>($"{Models}/{id}/{id}_{Version}.fbx"));
            go.transform.SetPositionAndRotation(at, Quaternion.Euler(0, yaw, 0));
            var m = Mat(id, material);
            foreach (var c in go.GetComponentsInChildren<Transform>(true).Where(t => t.name.EndsWith("_Collision")).ToArray())
            {   // the delivered collider mesh: a box collider of its bounds, never drawn
                var mf = c.GetComponent<MeshFilter>(); var box = c.gameObject.AddComponent<BoxCollider>(); box.center = mf.sharedMesh.bounds.center; box.size = mf.sharedMesh.bounds.size;
                UnityEngine.Object.DestroyImmediate(c.GetComponent<Renderer>());
            }
            foreach (var r in go.GetComponentsInChildren<Renderer>(true)) r.sharedMaterials = Enumerable.Repeat(m, r.sharedMaterials.Length).ToArray();
            foreach (var parent in go.GetComponentsInChildren<Renderer>(true).Where(r => r.name.EndsWith("_LOD0")).Select(r => r.transform.parent).Distinct().ToArray())
            {
                if (parent.GetComponentsInParent<LODGroup>(true).Any(g => g.GetLODs().Any(l => l.renderers.Any(x => x && x.transform.parent == parent)))) continue;
                float[] cut = { .25f, .08f, .015f };
                var kids = parent.Cast<Transform>().Select(t => t.GetComponent<Renderer>()).Where(r => r).ToArray();
                parent.gameObject.AddComponent<LODGroup>().SetLODs(Enumerable.Range(0, 3).Select(i => new LOD(cut[i], kids.Where(r => r.name.EndsWith("_LOD" + i)).ToArray())).ToArray());
            }
            return go;
        }

        static void Detail(GameObject go, bool on) { foreach (var r in go.GetComponentsInChildren<Renderer>(true).Where(r => r.name.Contains("_Detail_"))) r.enabled = on; }
        static Transform Node(GameObject go, string name) => go.GetComponentsInChildren<Transform>(true).FirstOrDefault(t => t.name == name);
        static Renderer[] Level(GameObject go, int i, bool detail = true) =>
            go.GetComponentsInChildren<Renderer>(true).Where(r => r.name.EndsWith("_LOD" + i) && (detail || !r.name.Contains("_Detail_"))).ToArray();
        static int Tris(IEnumerable<Renderer> rs) => rs.Sum(r => { var m = r.GetComponent<MeshFilter>().sharedMesh; return Enumerable.Range(0, m.subMeshCount).Sum(s => (int)m.GetIndexCount(s)) / 3; });
        static Bounds Box(IEnumerable<Renderer> rs) { var a = rs.ToArray(); var b = a[0].bounds; foreach (var r in a) b.Encapsulate(r.bounds); return b; }

        // ------------------------------------------------------------------ checks
        static readonly Dictionary<string, string> MatName = new Dictionary<string, string>();
        static void Inspect(string id, Info info)
        {
            MatName[id] = info.material;
            var go = Place(id, info.material, Vector3.zero, 0);
            var lod0 = Level(go, 0); var b = Box(lod0); var body = Box(Level(go, 0, false));
            Check(Node(go, id + "_GroundOrigin") != null || lod0.All(r => r.transform.IsChildOf(go.transform)), $"{id}: {id}_GroundOrigin is the model root; all LOD meshes hang under it");
            float[] d = info.dimensions_xyz_m, lim = info.size_limit_xyz_m;
            Check(Mathf.Abs(b.size.x - d[0]) <= .02f && Mathf.Abs(b.size.z - d[1]) <= .02f && Mathf.Abs(b.size.y - d[2]) <= .02f,
                $"{id}: imported size {b.size.x:0.000} x {b.size.z:0.000} x {b.size.y:0.000} m matches model_info {d[0]} x {d[1]} x {d[2]} within 2 cm");
            Check(b.size.x <= lim[0] + .005f && b.size.z <= lim[1] + .005f && b.size.y <= lim[2] + .005f,
                $"{id}: within the work pack's limit {lim[0]} x {lim[1]} x {lim[2]} m");
            Check(Mathf.Abs(body.min.y) < .005f, $"{id}: base at y = {body.min.y:0.000} (origin on the ground)");
            var levels = info.lods.All;
            var tris = Enumerable.Range(0, 3).Select(i => Tris(Level(go, i))).ToArray();
            Check(Enumerable.Range(0, 3).All(i => Mathf.Abs(tris[i] - levels[i].triangles) <= levels[i].triangles * .01f),
                $"{id}: triangles LOD0/1/2 = {tris[0]} / {tris[1]} / {tris[2]} ({100f * tris[1] / tris[0]:0}% / {100f * tris[2] / tris[0]:0}%), model_info {levels[0].triangles} / {levels[1].triangles} / {levels[2].triangles}");
            var objs = Enumerable.Range(0, 3).Select(i => Level(go, i).Length).ToArray();
            Check(Enumerable.Range(0, 3).All(i => objs[i] == levels[i].objects), $"{id}: objects per LOD {string.Join(" / ", objs)} (model_info {string.Join(" / ", levels.Select(l => l.objects))})");
            var mats = go.GetComponentsInChildren<Renderer>(true).SelectMany(r => r.sharedMaterials).Distinct().Count();
            Check(mats == 1 && levels.All(l => l.materials == 1), $"{id}: {mats} material for every LOD and Detail_ mesh (one material)");
            var groups = go.GetComponentsInChildren<LODGroup>(true);
            int inGroups = groups.Sum(g => g.GetLODs().Length == 3 ? g.GetLODs()[0].renderers.Length : 0);
            Check(groups.Length > 0 && groups.All(g => g.GetLODs().Length == 3) && inGroups == lod0.Length, $"{id}: {groups.Length} LODGroup(s) with 3 levels covering all {lod0.Length} LOD0 renderers");
            Check(info.minTier == "standard", $"{id}: minTier = {info.minTier} (work pack §3.5: large yard pieces, shown at the standard tier too)");
            var missing = info.detailMeshes.Where(n => Node(go, n) == null).ToArray();
            if (info.detailObjects.Length == 0)   // an item with nothing optional on it: no Detail_ mesh may exist either
                Check(!go.GetComponentsInChildren<Renderer>(true).Any(r => r.name.Contains("_Detail_")), $"{id}: no detailObjects, and no Detail_ mesh in the model");
            else
                Check(missing.Length == 0 && info.detailObjects.All(g => g.StartsWith("Detail_")),
                    $"{id}: detailObjects {string.Join(", ", info.detailObjects)} → {info.detailMeshes.Length} meshes present{(missing.Length > 0 ? ", missing " + string.Join(", ", missing) : "")}");
            Detail(go, false);
            int shown = Level(go, 0).Count(r => r.enabled);
            Check(shown == 1 && Level(go, 0).Where(r => r.enabled).All(r => !r.name.Contains("_Detail_")), $"{id}: Detail_* off still shows the body ({shown} mesh per LOD)");
            Detail(go, true);
            var cols = go.GetComponentsInChildren<Collider>(true);
            if (Collide.Contains(id))
            {
                var cb = cols.Length == 1 ? cols[0].bounds : new Bounds();
                Check(cols.Length == 1 && Node(go, id + "_Collision") != null && cb.size.x <= b.size.x + .01f && cb.size.z <= b.size.z + .01f && cb.min.y > -.01f,
                    $"{id}: one simple collider {id}_Collision, {cb.size.x:0.00} x {cb.size.z:0.00} x {cb.size.y:0.00} m, inside the model's footprint");
            }
            else Check(cols.Length == 0, $"{id}: no collider in the model");
            if (Cloth.Contains(id)) Check(Mats[id].GetFloat("_Cull") == (float)CullMode.Off, $"{id}: cloth material renders both faces (Cull Off)");
            if (Cutout.Contains(id))
            {
                var ti = (TextureImporter)AssetImporter.GetAtPath(AssetDatabase.GetAssetPath(Tex(id, "Albedo")));
                Check(Mats[id].GetFloat("_AlphaClip") == 1 && Mats[id].IsKeywordEnabled("_ALPHATEST_ON") && ti.DoesSourceTextureHaveAlpha() && ti.mipMapsPreserveCoverage,
                    $"{id}: alpha clip 0.5 on, albedo has alpha, Mip Maps Preserve Coverage on");
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
            var ground = GameObject.CreatePrimitive(PrimitiveType.Plane); ground.transform.localScale = Vector3.one * 12;
            groundMat = Flat("ground", new Color(.40f, .38f, .33f)); ground.GetComponent<Renderer>().sharedMaterial = groundMat;
            rulerMat = Flat("ruler", new Color(.30f, .42f, .55f));
            cam = new GameObject("Review Camera").AddComponent<Camera>(); cam.nearClipPlane = .02f; cam.farClipPlane = 300;
            UnityEngine.Rendering.Universal.CameraExtensions.GetUniversalAdditionalCameraData(cam).renderPostProcessing = true;
            target = new RenderTexture(1280, 960, 24) { antiAliasing = 4 }; cam.targetTexture = target;
            Day();
            var front = Vector3.back; var side = Vector3.right; var tq = (front - side).normalized + Vector3.up * .55f;
            foreach (var id in Ids)
            {
                var go = Place(id, MatName[id], Vector3.zero, 0); var b = Box(Level(go, 0));
                var ruler = Ruler(new Vector3(b.max.x + .45f, 0, 0));
                var all = b; all.Encapsulate(ruler.GetComponent<Renderer>().bounds);
                foreach (var (view, dir) in new[] { ("front", front), ("side", side), ("back", -front), ("threequarter", tq) })
                    Frame($"{id}/{id}-{view}", all, dir);
                UnityEngine.Object.DestroyImmediate(ruler);
                Frame($"{id}/{id}-close", b, tq, 1.05f);
                if (Cloth.Contains(id)) Frame($"{id}/{id}-low-grazing", b, (front + Vector3.up * .08f).normalized, 1.05f);   // low view along the cloth: no see-through faces
                for (int i = 0; i < 3; i++) { foreach (var g in go.GetComponentsInChildren<LODGroup>()) g.ForceLOD(i); Frame($"{id}/{id}-lod{i}", b, tq); }
                foreach (var g in go.GetComponentsInChildren<LODGroup>()) g.ForceLOD(1);
                Detail(go, false); Frame($"{id}/{id}-standard-tier-lod1-nodetail", b, tq); Detail(go, true);
                foreach (var g in go.GetComponentsInChildren<LODGroup>()) g.ForceLOD(-1);
                UnityEngine.Object.DestroyImmediate(go);
            }
            // work pack §2 "全包檢查": the delivered pieces side by side with the 1.75 m figure and one older prop
            var set = new List<GameObject>(); float sx = 0;
            foreach (var id in Ids.Concat(new[] { Old }))
            {
                var g = Place(id, id == Old ? "M_" + Old : MatName[id], Vector3.zero, 0); var bb = Box(Level(g, 0));
                g.transform.position += new Vector3(sx - bb.min.x, 0, -bb.center.z); sx += bb.size.x + .45f; set.Add(g);
            }
            foreach (var g in set) g.transform.position += new Vector3(-(sx - .45f) / 2, 0, 0);
            var s3 = Box(set.SelectMany(g => Level(g, 0)));
            var r5 = Ruler(new Vector3(s3.max.x + .6f, 0, 0)); var a3 = s3; a3.Encapsulate(r5.GetComponent<Renderer>().bounds);
            Frame("VG-set-front", a3, front, 1.02f); Frame("VG-set-threequarter", a3, tq, 1.02f); UnityEngine.Object.DestroyImmediate(r5);
            foreach (var g in set) UnityEngine.Object.DestroyImmediate(g);
            Report.Add("INFO renders written to art/previews/yard-roadside-c/unity");
        }

        static void Day()
        {
            sun.transform.rotation = Quaternion.Euler(38, -40, 0); sun.color = new Color(1, .86f, .66f); sun.intensity = 1.7f;
            RenderSettings.ambientMode = AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = new Color(.52f, .60f, .74f); RenderSettings.ambientEquatorColor = new Color(.50f, .50f, .48f); RenderSettings.ambientGroundColor = new Color(.30f, .27f, .22f);
            cam.clearFlags = CameraClearFlags.SolidColor; cam.backgroundColor = new Color(.62f, .72f, .86f);
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
            float radius = b.extents.magnitude * pad;
            float dist = radius / Mathf.Sin(15 * Mathf.Deg2Rad);
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
