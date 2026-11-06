using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

namespace YunJing.Editor
{
    // Unity check of C's day 3-4 models (art/exports/qingxi-day34-c, Eli-0731). The work pack says not to change apps/game,
    // so this file lives in art/source/qingxi-day34-c/unity and run_unity_check.sh copies it in for the run and removes it after.
    // Imports the delivered FBX and textures, builds URP materials, LODGroup and colliders from the node names,
    // compares them with model_info.json, walks the weir crest, toggles the states and renders review shots.
    //   Unity -batchmode -quit -projectPath apps/game -executeMethod YunJing.Editor.QingxiDay34Verify.Run -logFile <log>
    // Output: art/previews/qingxi-day34-c/unity/*.png and report.txt; the run fails when a check fails.
    public static class QingxiDay34Verify
    {
        const string Models = "Assets/YunJing/Models/Day34C";   // temporary copy of art/exports, removed by the run script
        static readonly string[] Ids = { "UP01", "UP02_01", "UP02_02", "UP02_03", "UP03", "UP04", "UP05_CushionNew", "UP05_CushionOld", "UP05_Table", "UP05_Burner", "UP06" };
        static string Repo => Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", ".."));
        static string Out => Path.Combine(Repo, "art/previews/qingxi-day34-c/unity");
        static readonly List<string> Report = new List<string>();
        static int failures;
        static readonly HashSet<string> Checked = new HashSet<string>();
        static Vector3 front = Vector3.back;
        static string json;

        [Serializable] class Info { public float[] dimensions_xyz_m, size_limit_m; public int[] triangles_total; }

        public static void Run()
        {
            Report.Clear(); Checked.Clear(); failures = 0;
            Directory.CreateDirectory(Out);
            Import();
            QingxiUrpUpgrade.EnsurePipeline();
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene);
            json = File.ReadAllText(Path.Combine(Repo, "art/exports/qingxi-day34-c/model_info.json"));
            Report.Add($"Unity {Application.unityVersion}, pipeline {GraphicsSettings.currentRenderPipeline?.name ?? "built-in"}");
            foreach (var id in Ids) Inspect(id, JsonUtility.FromJson<Info>(Block(json, id)));
            Shots();
            File.WriteAllLines(Path.Combine(Out, "report.txt"), Report);
            foreach (var line in Report) Debug.Log("DAY34 " + line);
            if (failures > 0) throw new Exception($"DAY34_VERIFY {failures} check(s) failed, see {Out}/report.txt");
            Debug.Log($"DAY34_VERIFY_DONE all checks passed, output {Out}");
        }

        static void Check(bool ok, string line) { Report.Add((ok ? "PASS " : "FAIL ") + line); if (!ok) failures++; }

        // model_info.json is keyed by id; JsonUtility only reads objects, so cut out each item's braces.
        static string Block(string text, string key)
        {
            int at = text.IndexOf($"\"{key}\":", StringComparison.Ordinal);
            if (at < 0) return null;
            int start = text.IndexOf('{', at), depth = 0;
            for (int i = start; i < text.Length; i++)
            {
                if (text[i] == '{') depth++;
                else if (text[i] == '}' && --depth == 0) return text.Substring(start, i - start + 1);
            }
            throw new InvalidDataException("model_info.json: no item " + key);
        }

        // "name": [x, y, z] pairs inside a block (sockets, pivots); Blender z is Unity height
        static Dictionary<string, float[]> Points(string block)
        {
            var d = new Dictionary<string, float[]>();
            if (block == null) return d;
            foreach (Match m in Regex.Matches(block, "\"([^\"]+)\":\\s*\\[([-0-9.e, ]+)\\]"))
                d[m.Groups[1].Value] = m.Groups[2].Value.Split(',').Select(s => float.Parse(s, CultureInfo.InvariantCulture)).ToArray();
            return d;
        }

        static float Number(string block, string key) =>
            float.Parse(Regex.Match(block, $"\"{key}\":\\s*([-0-9.]+)").Groups[1].Value, CultureInfo.InvariantCulture);

        // ------------------------------------------------------------------ import
        static void Import()
        {
            foreach (var id in Ids)
            {
                Copy(Path.Combine(Repo, "art/exports/qingxi-day34-c"), Path.Combine(Repo, "apps/game", Models, id), id + ".fbx");
                Copy(Path.Combine(Repo, "art/textures/qingxi-day34-c"), Path.Combine(Repo, "apps/game", Models, id, "Textures"), id + "_*.png");
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
                bool normal = path.EndsWith("_Normal.png"), linear = normal || path.EndsWith("_MaskURP.png") || path.EndsWith("_ORM.png") || path.EndsWith("_WarmthMask.png");
                var type = normal ? TextureImporterType.NormalMap : TextureImporterType.Default;
                bool alpha = path.EndsWith("_Drawing_Albedo.png");
                if (ti.textureType == type && ti.sRGBTexture == !linear && ti.alphaIsTransparency == alpha) continue;
                ti.textureType = type; ti.sRGBTexture = !linear; ti.mipmapEnabled = true; ti.alphaIsTransparency = alpha; ti.SaveAndReimport();
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

        // One URP Lit per group: Albedo, Normal, MaskURP (R metal, G AO, A smoothness), + Emission; the drawing decal is transparent.
        static Material Mat(string id, string name)
        {
            var dir = $"{Models}/{id}/Materials"; Directory.CreateDirectory(Path.Combine(Repo, "apps/game", dir));
            var path = $"{dir}/{name}.mat";
            var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (mat == null) { mat = new Material(Shader.Find("Universal Render Pipeline/Lit")); AssetDatabase.CreateAsset(mat, path); }
            var albedo = Tex(id, name, "Albedo"); var mask = Tex(id, name, "MaskURP"); var normal = Tex(id, name, "Normal"); var glow = Tex(id, name, "Emission");
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
            if (name.EndsWith("_Drawing"))   // alpha-blended charcoal decal
            {
                mat.SetFloat("_Surface", 1); mat.SetFloat("_Blend", 0); mat.SetFloat("_ZWrite", 0);
                mat.SetFloat("_SrcBlend", (float)BlendMode.SrcAlpha); mat.SetFloat("_DstBlend", (float)BlendMode.OneMinusSrcAlpha);
                mat.EnableKeyword("_SURFACE_TYPE_TRANSPARENT"); mat.renderQueue = (int)RenderQueue.Transparent;
            }
            EditorUtility.SetDirty(mat);
            return mat;
        }
        static Texture2D Tex(string id, string group, string kind) => AssetDatabase.LoadAssetAtPath<Texture2D>($"{Models}/{id}/Textures/{group}_{kind}.png");

        static GameObject Place(string id, Vector3 at, float yaw)
        {
            var go = (GameObject)PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>($"{Models}/{id}/{id}.fbx"));
            go.transform.SetPositionAndRotation(at, Quaternion.Euler(0, yaw, 0));
            foreach (var r in go.GetComponentsInChildren<Renderer>(true))
            {
                if (r.name.StartsWith(id + "_Collision")) { r.enabled = false; continue; }
                var group = Regex.Match(r.name, @"^(.+)_LOD\d$");
                if (group.Success) r.sharedMaterials = Enumerable.Repeat(Mat(id, group.Groups[1].Value), r.sharedMaterials.Length).ToArray();
            }
            // Unity builds LODGroups from _LOD0/_LOD1/_LOD2 siblings on import; build one per parent only if it did not.
            foreach (var parent in go.GetComponentsInChildren<Renderer>(true).Where(r => r.name.EndsWith("_LOD0")).Select(r => r.transform.parent).Distinct().ToArray())
            {
                if (parent.GetComponentsInParent<LODGroup>(true).Any(g => g.GetLODs().Any(l => l.renderers.Any(x => x && x.transform.parent == parent)))) continue;
                float[] cut = { .25f, .08f, .015f };
                var kids = parent.Cast<Transform>().Select(t => t.GetComponent<Renderer>()).Where(r => r).ToArray();
                parent.gameObject.AddComponent<LODGroup>().SetLODs(Enumerable.Range(0, 3).Select(i => new LOD(cut[i], kids.Where(r => r.name.EndsWith("_LOD" + i)).ToArray())).ToArray());
            }
            foreach (var col in go.GetComponentsInChildren<MeshFilter>(true).Where(m => m.name.StartsWith(id + "_Collision")))
                if (col.GetComponent<MeshCollider>() == null) col.gameObject.AddComponent<MeshCollider>().sharedMesh = col.sharedMesh;
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
            bool rooted = Node(go, id + "_GroundOrigin") != null || lod0.All(r => r.transform.IsChildOf(go.transform));
            Check(rooted, $"{id}: {id}_GroundOrigin is the model root (Unity names it {go.name}); all LOD meshes hang under it");
            float[] d = info.dimensions_xyz_m, lim = info.size_limit_m;
            Check(Mathf.Abs(b.size.x - d[0]) < .02f && Mathf.Abs(b.size.z - d[1]) < .02f && Mathf.Abs(b.size.y - d[2]) < .02f,
                $"{id}: imported size {b.size.x:0.000} x {b.size.z:0.000} x {b.size.y:0.000} m matches model_info {d[0]} x {d[1]} x {d[2]}");
            Check(b.size.x <= lim[0] + .001f && b.size.z <= lim[1] + .001f && b.size.y <= lim[2] + .001f, $"{id}: within the {lim[0]} x {lim[1]} x {lim[2]} m limit");
            Check(Mathf.Abs(b.min.y) < .01f, $"{id}: base at y = {b.min.y:0.000} (origin on the ground)");
            var tris = Enumerable.Range(0, 3).Select(i => Tris(Level(go, i))).ToArray();
            Check(Enumerable.Range(0, 3).All(i => Mathf.Abs(tris[i] - info.triangles_total[i]) <= info.triangles_total[i] * .01f),
                $"{id}: triangles LOD0/1/2 = {tris[0]} / {tris[1]} / {tris[2]} ({100f * tris[1] / tris[0]:0}% / {100f * tris[2] / tris[0]:0}%), model_info {string.Join(" / ", info.triangles_total)}");
            var groups = go.GetComponentsInChildren<LODGroup>(true);
            int inGroups = groups.Sum(g => g.GetLODs().Length == 3 ? g.GetLODs()[0].renderers.Length : 0);
            Check(groups.Length > 0 && groups.All(g => g.GetLODs().Length == 3) && inGroups == lod0.Length,
                $"{id}: {groups.Length} LODGroup(s) with 3 levels covering all {lod0.Length} LOD0 renderers");
            var block = Block(json, id);
            foreach (Match m in Regex.Matches(Block(block, "collision") ?? "{}", $"\"({Regex.Escape(id)}_Collision[A-Za-z_]*)\":"))
            {
                var col = Node(go, m.Groups[1].Value)?.GetComponent<MeshCollider>();
                Check(col != null && col.sharedMesh.triangles.Length > 0, $"{id}: {m.Groups[1].Value} imported as MeshCollider ({(col ? col.sharedMesh.triangles.Length / 3 : 0)} triangles), render hidden");
                if (col == null) continue;
                var cb = col.bounds; var inside = new Bounds(b.center, b.size + Vector3.one * .1f);
                Check(inside.Contains(cb.min) && inside.Contains(cb.max), $"{id}: {m.Groups[1].Value} {cb.size.x:0.00} x {cb.size.z:0.00} x {cb.size.y:0.00} m stays within the model");
            }
            foreach (var s in Points(Block(block, "sockets")))
            {
                var t = Node(go, s.Key);
                Check(t != null && Mathf.Abs(t.position.y - s.Value[2]) < .01f, $"{id}: {s.Key} at height {(t ? t.position.y : -1):0.000} m (model_info {s.Value[2]:0.000})");
            }
            if (id == "UP06" || id.StartsWith("UP02"))
            {
                var em = go.GetComponentsInChildren<Renderer>().Select(r => r.sharedMaterial).FirstOrDefault(m => m && m.IsKeywordEnabled("_EMISSION"));
                Check(em != null, $"{id}: {(id == "UP06" ? "paper shade" : "crack glow")} is an emissive material ({(em ? em.name : "none")})");
            }
            if (id.StartsWith("UP02"))
                Check(Tex(id, id + "_Stone", "Albedo_Warm") != null && Tex(id, id + "_Stone", "WarmthMask") != null, $"{id}: _Warmth maps Albedo_Warm and WarmthMask imported");
            if (id == "UP01") Weir(go, block);
            if (id == "UP04")
            {
                var hit = Physics.Raycast(new Vector3(0, 2, 0), Vector3.down, out var h, 3);
                Check(hit && h.point.y > .28f, $"UP04: the top can be stood on (collider top {(hit ? h.point.y : -1):0.00} m)");
            }
            UnityEngine.Object.DestroyImmediate(go);
        }

        // UP01: walk the 0.9 m crest end to end with a 1.75 m, r 0.3 m capsule; the debris layer blocks the sluice and clears;
        // the gate pivot lifts 1.2 m under the windlass beam.
        static void Weir(GameObject go, string block)
        {
            var heights = Block(block, "heights");
            float crest = Number(heights, "crest_walk_z"), frameTop = Number(heights, "frame_top_z"), lift = Number(heights, "gate_lift_m");
            var main = Node(go, "UP01_Collision").GetComponent<MeshCollider>();
            var verts = main.sharedMesh.vertices.Select(v => main.transform.TransformPoint(v)).ToArray();
            // the arch bows upstream: the middle of the crest sits further from the downstream face than the ends
            float zEnds = verts.Where(v => Mathf.Abs(v.x) > 5.5f && v.y > crest - .05f).Average(v => v.z), zMid = verts.Where(v => Mathf.Abs(v.x) < 1 && v.y > crest - .05f).Average(v => v.z);
            front = zMid > zEnds ? Vector3.back : Vector3.forward;
            Report.Add($"INFO Blender front (-Y, downstream face) imports as Unity {(front.z > 0 ? "+Z" : "-Z")}");
            int ok = 0, n = 0; string worst = "";
            for (float x = -5f; x <= 5.01f; x += .5f)
            {
                var zs = new List<float>();
                for (float z = -2.5f; z <= 2.5f; z += .02f)
                    if (Physics.Raycast(new Vector3(x, 6, z), Vector3.down, out var h, 8) && Mathf.Abs(h.point.y - crest) < .04f) zs.Add(z);
                n++;
                if (zs.Count == 0) { worst += $" x={x:0.0}: no crest"; continue; }
                float zw = front.z < 0 ? zs.Min() + .46f : zs.Max() - .46f;   // the downstream row is the walkway
                var feet = new Vector3(x, crest, zw);
                bool clear = !Physics.CheckCapsule(feet + Vector3.up * .32f, feet + Vector3.up * 1.45f, .3f);
                bool ground = Physics.Raycast(feet + Vector3.up * .3f, Vector3.down, out var g, .6f) && Mathf.Abs(g.point.y - crest) < .04f;
                if (clear && ground) ok++;
                else worst += $" x={x:0.0}({(clear ? "" : "blocked by " + string.Join("/", Physics.OverlapCapsule(feet + Vector3.up * .32f, feet + Vector3.up * 1.45f, .3f).Select(c => c.name)))}{(ground ? "" : " no ground")})";
            }
            Check(ok == n, $"UP01 crest: a 1.75 m player (r 0.3) stands on the downstream walk at {ok}/{n} points from x -5 to 5 m (the bank rocks close the ends), over the outlet bridge too{(worst.Length > 0 ? ":" + worst : "")}");
            // sluice: a ray along the outlet at knee height hits the debris; with the Debris layer off it reaches the gate
            var debris = Node(go, "UP01_Collision_Debris").GetComponent<MeshCollider>(); var gateCol = Node(go, "UP01_Collision_Gate").GetComponent<MeshCollider>();
            var from = new Vector3(0, .6f, front.z * 4); var dir = -front;
            bool hitDebris = Physics.Raycast(from, dir, out var h1, 8) && h1.collider == debris;
            debris.gameObject.SetActive(false); Physics.SyncTransforms();
            bool hitGate = Physics.Raycast(from, dir, out var h2, 8) && h2.collider == gateCol;
            Check(hitDebris && hitGate, $"UP01 sluice: blocked by {(hitDebris ? "UP01_Collision_Debris" : h1.collider?.name ?? "nothing")}; with Debris off the outlet runs to {(hitGate ? "the gate" : h2.collider?.name ?? "nothing")}");
            var gate = Gate(go);
            bool samePivot = gate.Length == 4 && gate.All(t => (t.position - gate[0].position).sqrMagnitude < 1e-6f) && Mathf.Abs(gate[0].position.y - frameTop) < .01f;
            Check(samePivot, $"UP01: gate LOD0/1/2 and UP01_Collision_Gate share one origin at the frame top ({(gate.Length > 0 ? gate[0].position.y : -1):0.00} m)");
            foreach (var t in gate) t.position += Vector3.up * lift; Physics.SyncTransforms();
            float top = gateCol.bounds.max.y, bottom = gateCol.bounds.min.y;
            bool passage = !Physics.Raycast(from, dir, out var h3, Mathf.Abs(from.z) + 2.5f) || h3.collider != gateCol;
            Check(top <= frameTop + .001f && passage, $"UP01: gate raised {lift} m spans {bottom:0.00}-{top:0.00} m, under the frame top {frameTop:0.00} m; the outlet is open at 0.6 m");
            foreach (var t in gate) t.position -= Vector3.up * lift; debris.gameObject.SetActive(true); Physics.SyncTransforms();
        }

        // the moving gate: its three LOD meshes and its collider, each with the origin on the pivot
        static Transform[] Gate(GameObject go) => go.GetComponentsInChildren<Transform>(true).Where(t => t.name.StartsWith("UP01_Gate_LOD") || t.name == "UP01_Collision_Gate").ToArray();

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
            cam = new GameObject("Review Camera").AddComponent<Camera>(); cam.nearClipPlane = .02f; cam.farClipPlane = 300;
            UnityEngine.Rendering.Universal.CameraExtensions.GetUniversalAdditionalCameraData(cam).renderPostProcessing = true;
            target = new RenderTexture(1280, 960, 24) { antiAliasing = 4 }; cam.targetTexture = target;
            Day();
            var side = Vector3.Cross(Vector3.up, front); var tq = (front - side).normalized + Vector3.up * .55f;
            foreach (var id in Ids)   // four views with the 1.75 m figure, plus forced LOD0/1/2
            {
                var go = Place(id, Vector3.zero, 0); var b = Box(Level(go, 0));
                var ruler = Ruler(new Vector3(b.max.x + .45f, 0, 0));
                var all = b; all.Encapsulate(ruler.GetComponent<Renderer>().bounds);
                foreach (var (view, dir) in new[] { ("front", front), ("side", side), ("back", -front), ("threequarter", tq) })
                    Frame($"{id}/{id}-{view}", all, dir);
                foreach (var group in go.GetComponentsInChildren<LODGroup>()) group.ForceLOD(0);
                for (int i = 0; i < 3; i++) { foreach (var g in go.GetComponentsInChildren<LODGroup>()) g.ForceLOD(i); Frame($"{id}/{id}-lod{i}", b, tq); }
                foreach (var g in go.GetComponentsInChildren<LODGroup>()) g.ForceLOD(-1);
                UnityEngine.Object.DestroyImmediate(ruler); UnityEngine.Object.DestroyImmediate(go);
            }
            // UP01 states: blocked / cleared / cleared with the gate raised
            var weir = Place("UP01", Vector3.zero, 0); var wb = Box(Level(weir, 0));
            Frame("UP01/UP01-blocked", wb, tq, 1.0f);
            foreach (var r in weir.GetComponentsInChildren<Renderer>().Where(r => r.name.StartsWith("UP01_Debris"))) r.enabled = false;
            Frame("UP01/UP01-cleared", wb, tq, 1.0f);
            foreach (var t in Gate(weir)) t.position += Vector3.up * 1.2f;
            Frame("UP01/UP01-cleared-gate-open", wb, tq, 1.0f);
            Shot("UP01/UP01-cleared-gate-open-closeup", new Vector3(1.6f, 1.5f, front.z * 3.4f), new Vector3(0, 1.1f, front.z * -.5f), 45);
            foreach (var t in Gate(weir)) t.position -= Vector3.up * 1.2f;
            foreach (var r in weir.GetComponentsInChildren<Renderer>().Where(r => r.name.StartsWith("UP01_Debris"))) r.enabled = true;
            Shot("UP01/UP01-blocked-closeup", new Vector3(1.6f, 1.5f, front.z * 3.4f), new Vector3(0, 1.1f, front.z * -.5f), 45);
            var rw = Ruler(new Vector3(2.2f, 0, front.z * 2.5f));
            Shot("eye/UP01-from-dry-bed-1p7m", new Vector3(-2.5f, 1.7f, front.z * 11), new Vector3(0, 1.6f, 0), 50);
            Shot("eye/UP01-on-crest-1p7m", new Vector3(-5f, 3.9f, front.z * -.2f), new Vector3(2, 2.6f, front.z * -.55f), 55);
            UnityEngine.Object.DestroyImmediate(rw); UnityEngine.Object.DestroyImmediate(weir);
            // UP02 _Warmth: URP Lit has no blend slot, so the check swaps the base map and sets the emission the way a game material would
            foreach (var id in new[] { "UP02_01", "UP02_02", "UP02_03" })
            {
                var st = Place(id, Vector3.zero, 0); var sb = Box(Level(st, 0));
                foreach (var (light, label) in new[] { (0, "afternoon"), (1, "dusk") })
                {
                    if (light == 0) Afternoon(); else Dusk();
                    foreach (var w in new[] { 0f, 1f }) { Warmth(st, id, w); Frame($"UP02/{id}-{label}-warmth{w:0}", sb, tq, 1.1f); }
                }
                Warmth(st, id, 0); UnityEngine.Object.DestroyImmediate(st);
            }
            // UP06 _Lit by day and at night
            var lamp = Place("UP06", Vector3.zero, 0); var lb = Box(Level(lamp, 0));
            foreach (var night in new[] { false, true })
            {
                if (night) Night(); else Day();
                foreach (var lit in new[] { 0f, 1f }) { Lit(lamp, lit); Frame($"UP06/UP06-{(night ? "night" : "day")}-{(lit > 0 ? "lit" : "unlit")}", lb, front + Vector3.up * .2f, 1.1f); }
            }
            Lit(lamp, 0); UnityEngine.Object.DestroyImmediate(lamp);
            // lesson layout on the terrace at 1.7 m
            Day();
            var set = new List<GameObject> { Place("UP05_Table", Vector3.zero, 0), Place("UP05_Burner", new Vector3(.035f, .3f, front.z * -.06f), 0) };
            float[][] seats = { new[] { -1.2f, 1.4f }, new[] { -.4f, 1.4f }, new[] { .4f, 1.4f }, new[] { 1.2f, 1.4f }, new[] { -.8f, 2.2f }, new[] { .8f, 2.2f } };
            for (int i = 0; i < seats.Length; i++) set.Add(Place(i % 2 == 0 ? "UP05_CushionNew" : "UP05_CushionOld", new Vector3(seats[i][0], 0, front.z * seats[i][1]), i * 37));
            Shot("eye/UP05-lesson-layout-1p7m", new Vector3(0, 1.7f, -front.z * 1.6f), new Vector3(0, .2f, front.z * 1.2f), 48);
            foreach (var g in set) UnityEngine.Object.DestroyImmediate(g);
            Report.Add("INFO renders written to art/previews/qingxi-day34-c/unity");
        }

        static void Warmth(GameObject go, string id, float w)
        {
            foreach (var r in go.GetComponentsInChildren<Renderer>().Where(r => Regex.IsMatch(r.name, @"_(Stone|Plants)_LOD\d$")))
            {
                var g = Regex.Match(r.name, @"^(.+)_LOD\d$").Groups[1].Value; var m = r.sharedMaterial;
                m.SetTexture("_BaseMap", Tex(id, g, w > .5f ? "Albedo_Warm" : "Albedo"));
                if (m.IsKeywordEnabled("_EMISSION")) m.SetColor("_EmissionColor", Color.white * (.12f * w * w));
            }
        }

        static void Lit(GameObject go, float lit)
        {
            foreach (var m in go.GetComponentsInChildren<Renderer>().Select(r => r.sharedMaterial).Where(m => m && m.IsKeywordEnabled("_EMISSION")).Distinct())
                m.SetColor("_EmissionColor", Color.white * (1f * lit));   // URP: 1.0 reads like Blender's 2.0 (no bloom there)
            var socket = Node(go, "UP06_LightSocket");
            var light = socket.GetComponent<Light>();
            if (light == null) light = socket.gameObject.AddComponent<Light>();
            light.type = LightType.Point; light.color = new Color(1, .93f, .82f); light.range = 3; light.intensity = lit * 1.2f; light.enabled = lit > 0;
        }

        static void Day()
        {
            sun.transform.rotation = Quaternion.Euler(38, -40, 0); sun.color = new Color(1, .86f, .66f); sun.intensity = 1.7f;
            RenderSettings.ambientMode = AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = new Color(.52f, .60f, .74f); RenderSettings.ambientEquatorColor = new Color(.50f, .50f, .48f); RenderSettings.ambientGroundColor = new Color(.30f, .27f, .22f);
            cam.clearFlags = CameraClearFlags.SolidColor; cam.backgroundColor = new Color(.62f, .72f, .86f);
        }
        static void Afternoon()
        {
            Day(); sun.transform.rotation = Quaternion.Euler(55, -30, 0); sun.color = new Color(1, .95f, .86f); sun.intensity = 2.2f;
        }
        static void Dusk()
        {
            sun.transform.rotation = Quaternion.Euler(4, -60, 0); sun.color = new Color(1, .6f, .4f); sun.intensity = .25f;
            RenderSettings.ambientMode = AmbientMode.Flat; RenderSettings.ambientLight = new Color(.16f, .19f, .28f);
            cam.backgroundColor = new Color(.16f, .20f, .32f);
        }
        static void Night()
        {
            sun.transform.rotation = Quaternion.Euler(40, 150, 0); sun.color = new Color(.65f, .75f, 1); sun.intensity = .12f;
            RenderSettings.ambientMode = AmbientMode.Flat; RenderSettings.ambientLight = new Color(.05f, .07f, .12f);
            cam.backgroundColor = new Color(.03f, .04f, .08f);
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
