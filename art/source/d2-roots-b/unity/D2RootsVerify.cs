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
    // Unity check of B's D2 roots and wood (art/exports/d2-roots-b, joshsu54), modelled on CreeksideWLVerify. It does not change apps/game:
    // run_unity_check.sh copies this file in for one batch run and removes it together with the temporary model copies.
    // Imports the delivered FBX and textures, builds one URP Lit per texture set (A-D: Albedo, Normal, MaskURP, shared bark detail), compares
    // with model_info.json (size within 2 cm, triangles per LOD, objects, materials, 2048 textures, minTier, detailObjects), switches Detail_*
    // off the way the standard tier will, gives the collision shell a MeshCollider and walks the path through the arch, then renders
    // review shots, one from the V2 concept camera.
    //   Unity -batchmode -quit -projectPath apps/game -executeMethod YunJing.Editor.D2RootsVerify.Run -logFile <log>
    // Output: art/previews/d2-roots-b/<asset>/unity/*.png and report.txt; the run fails when a check fails.
    public static class D2RootsVerify
    {
        // Two temporary copies of art/exports, both removed by the run script. The first sits where the game keeps models, so the project's
        // import budget applies (QingxiImportBudget: textures at most 1024 px and crunch-compressed, medium mesh compression): that is what
        // players see. The second sits outside it and shows the files as delivered (2048, no crunch), for comparison only.
        const string BudgetModels = "Assets/YunJing/Models/D2RootsB", RawModels = "Assets/D2RootsBRawCheck";
        static string Models = BudgetModels;
        static bool Raw => Models == RawModels;
        // DR01 is at v005, the DR02 wall modules at v001. D2_IDS (comma separated) limits a run to some of them.
        static string Version(string id) => id.StartsWith("DR01") ? "v005" : "v001";
        static readonly string[] AllIds = { "DR01_RootArch", "DR02_RootWall_A", "DR02_RootWall_B", "DR02_RootWall_C", "DR03_RootEnd", "DR03_RootCross", "DR04_RootHollow" };
        static string[] Ids => string.IsNullOrEmpty(Environment.GetEnvironmentVariable("D2_IDS")) ? AllIds
            : Environment.GetEnvironmentVariable("D2_IDS").Split(',').Select(x => x.Trim()).Where(x => x.Length > 0).ToArray();
        static bool Wall(string id) => id.StartsWith("DR02");
        static bool Piece(string id) => id.StartsWith("DR03");      // DR03 end cap / crossing piece: one socket, used together with DR02
        static bool Hollow(string id) => id.StartsWith("DR04");     // DR04 hollow between two buttress roots: one socket (Socket_Back)
        // DR03 is checked joined to DR02 A (end cap) and B (crossing piece), so those are imported too
        static string[] ImportIds => Ids.Concat(Ids.Any(Piece) ? new[] { "DR02_RootWall_A", "DR02_RootWall_B" } : new string[0]).Distinct().ToArray();
        static string Repo => Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", ".."));
        static string Exports => Path.Combine(Repo, "art/exports/d2-roots-b");
        static string Out(string id) => Path.Combine(Repo, "art/previews/d2-roots-b", id, "unity");
        static readonly List<string> Report = new List<string>();
        static int failures;

        [Serializable] class Lod { public int triangles, objects, materials; }
        [Serializable] class Lods { public Lod LOD0, LOD1, LOD2; public Lod[] All => new[] { LOD0, LOD1, LOD2 }; }
        [Serializable] class UnityInfo { public float detail_tiling_on_uv0; }
        [Serializable] class Info { public float[] dimensions_m; public string minTier; public string[] detailObjects; public Lods budget_per_lod; public UnityInfo unity; }

        public static void Run()
        {
            Report.Clear(); failures = 0;
            Import();
            QingxiUrpUpgrade.EnsurePipeline();
            Report.Add($"Unity {Application.unityVersion}, pipeline {GraphicsSettings.currentRenderPipeline?.name ?? "built-in"}");
            var own = new Dictionary<string, List<string>>();     // each report.txt gets the header and only its own asset's lines
            foreach (var id in Ids)
            {
                Directory.CreateDirectory(Out(id));
                EditorSceneManager.NewScene(NewSceneSetup.EmptyScene);
                var info = JsonUtility.FromJson<Info>(File.ReadAllText(Path.Combine(Exports, id, "model_info.json")));
                int start = Report.Count;
                Inspect(id, info);
                Shots(id, info);
                own[id] = Report.Skip(start).ToList();
                File.WriteAllLines(Path.Combine(Out(id), "report.txt"), new[] { Report[0] }.Concat(own[id]));
            }
            // second pass: the same files outside the import budget, two shots for comparison
            Models = RawModels; Mats.Clear();
            Import();
            foreach (var id in Ids)
            {
                var info = JsonUtility.FromJson<Info>(File.ReadAllText(Path.Combine(Exports, id, "model_info.json")));
                var before = Report.Count; int f0 = failures;
                Shots(id, info);
                Report.RemoveRange(before, Report.Count - before); failures = f0;
                var note = $"INFO {id}: *-rawimport.png show the delivered files without the project's import budget (2048 textures, no crunch, no mesh compression)";
                Report.Add(note); own[id].Add(note);
                File.WriteAllLines(Path.Combine(Out(id), "report.txt"), new[] { Report[0] }.Concat(own[id]));
            }
            Models = BudgetModels; Mats.Clear();
            foreach (var line in Report) Debug.Log("DR " + line);
            if (failures > 0) throw new Exception($"DR_VERIFY {failures} check(s) failed, see report.txt");
            Debug.Log("DR_VERIFY_DONE all checks passed");
        }

        static void Check(bool ok, string line) { Report.Add((ok ? "PASS " : "FAIL ") + line); if (!ok) failures++; }

        // ------------------------------------------------------------------ import
        static void Import()
        {
            foreach (var id in ImportIds)
            {
                Copy(Path.Combine(Exports, id), Path.Combine(Repo, "apps/game", Models, id), $"{id}_{Version(id)}.fbx");
                Copy(Path.Combine(Exports, id, "Textures"), Path.Combine(Repo, "apps/game", Models, id, "Textures"), id + "_*.png");
            }
            Copy(Path.Combine(Exports, "Shared"), Path.Combine(Repo, "apps/game", Models, "Shared"), "*.png");
            AssetDatabase.Refresh();
            foreach (var guid in AssetDatabase.FindAssets("t:Model", new[] { Models }))
            {
                var importer = (ModelImporter)AssetImporter.GetAtPath(AssetDatabase.GUIDToAssetPath(guid));
                if (importer.bakeAxisConversion && importer.materialImportMode == ModelImporterMaterialImportMode.ImportViaMaterialDescription) continue;
                importer.bakeAxisConversion = true; importer.importCameras = false; importer.importLights = false; importer.addCollider = false;
                importer.importAnimation = false; importer.materialImportMode = ModelImporterMaterialImportMode.ImportViaMaterialDescription;   // keeps the FBX material names (M_<id>_A …) on the slots
                importer.SaveAndReimport();
            }
            foreach (var guid in AssetDatabase.FindAssets("t:Texture2D", new[] { Models }))
            {
                var path = AssetDatabase.GUIDToAssetPath(guid);
                var ti = (TextureImporter)AssetImporter.GetAtPath(path);
                bool normal = path.EndsWith("_Normal.png"), linear = normal || path.EndsWith("_MaskURP.png") || path.EndsWith("_ORM.png");
                var type = normal ? TextureImporterType.NormalMap : TextureImporterType.Default;
                if (ti.textureType == type && ti.sRGBTexture == !linear && ti.maxTextureSize == 2048) continue;
                ti.textureType = type; ti.sRGBTexture = !linear; ti.mipmapEnabled = true; ti.maxTextureSize = 2048;
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

        // One URP Lit per texture set: Albedo, Normal, MaskURP (R metal, G AO, A smoothness) + the shared tiling bark detail on UV0.
        static readonly Dictionary<string, Material> Mats = new Dictionary<string, Material>();
        static Material Mat(string id, string set, Info info)
        {
            bool leaf = set == "Leaf"; string key = id + set; if (leaf) set = "A";   // the plants use set A (leaf strip at the bottom of the atlas), both faces
            if (Mats.TryGetValue(key, out var cached) && cached) return cached;
            var dir = $"{Models}/{id}/Materials"; Directory.CreateDirectory(Path.Combine(Repo, "apps/game", dir));
            var path = $"{dir}/M_{id}_{(leaf ? "Leaf" : set)}.mat";
            var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (mat == null) { mat = new Material(Shader.Find("Universal Render Pipeline/Lit")); AssetDatabase.CreateAsset(mat, path); }
            var albedo = Tex(id, set, "Albedo"); var mask = Tex(id, set, "MaskURP"); var normal = Tex(id, set, "Normal"); var orm = Tex(id, set, "ORM");
            var detail = AssetDatabase.LoadAssetAtPath<Texture2D>($"{Models}/Shared/D2Bark_Detail_Normal.png");
            if (!leaf) Check(albedo != null && mask != null && normal != null && orm != null, $"{id} set {set}: Albedo / Normal / ORM / MaskURP textures found");
            if (leaf) { Setup(mat, albedo, normal, mask, null, info); mat.SetFloat("_Cull", (float)CullMode.Off); mat.doubleSidedGI = true; EditorUtility.SetDirty(mat); Mats[key] = mat; return mat; }
            var all = new[] { albedo, normal, orm, mask };
            var src = all.Where(t => t).Select(t => { ((TextureImporter)AssetImporter.GetAtPath(AssetDatabase.GetAssetPath(t))).GetSourceTextureWidthAndHeight(out int w, out int h); return $"{w}x{h}"; }).Distinct().ToArray();
            Check(src.Length == 1 && src[0] == "2048x2048", $"{id} set {set}: delivered textures {string.Join(", ", src)} (larger than a person: 2048)");
            var tiA = (TextureImporter)AssetImporter.GetAtPath(AssetDatabase.GetAssetPath(albedo));
            if (set == "A") Report.Add($"INFO {id}: imported at {string.Join(", ", all.Where(t => t).Select(t => $"{t.width}x{t.height}").Distinct())} on {EditorUserBuildSettings.activeBuildTarget} (importer max {tiA.maxTextureSize}, default platform max {tiA.GetDefaultPlatformTextureSettings().maxTextureSize}, build override max {EditorUserBuildSettings.overrideMaxTextureSize})");
            Setup(mat, albedo, normal, mask, detail, info);
            if (set == "A" && detail != null) Report.Add($"INFO {id}: bark detail on UV0, tiling {info.unity.detail_tiling_on_uv0:0.00}");
            EditorUtility.SetDirty(mat); Mats[key] = mat;
            return mat;
        }

        static void Setup(Material mat, Texture2D albedo, Texture2D normal, Texture2D mask, Texture2D detail, Info info)
        {
            mat.SetTexture("_BaseMap", albedo); mat.SetColor("_BaseColor", Color.white);
            mat.SetTexture("_BumpMap", normal); mat.EnableKeyword("_NORMALMAP");
            mat.SetTexture("_MetallicGlossMap", mask); mat.EnableKeyword("_METALLICSPECGLOSSMAP"); mat.SetFloat("_Smoothness", 1);
            mat.SetTexture("_OcclusionMap", mask); mat.EnableKeyword("_OCCLUSIONMAP");
            if (detail != null && info.unity != null && info.unity.detail_tiling_on_uv0 > 0)
            {
                var path2 = AssetDatabase.GetAssetPath(detail);
                var ti = (TextureImporter)AssetImporter.GetAtPath(path2);
                if (ti.textureType != TextureImporterType.NormalMap) { ti.textureType = TextureImporterType.NormalMap; ti.SaveAndReimport(); }
                var detailAlbedo = AssetDatabase.LoadAssetAtPath<Texture2D>($"{Models}/Shared/D2Bark_Detail_Albedo.png");
                mat.SetTexture("_DetailNormalMap", detail); mat.SetFloat("_DetailNormalMapScale", 1);
                mat.SetTexture("_DetailAlbedoMap", detailAlbedo); mat.SetFloat("_DetailAlbedoMapScale", 1);
                mat.SetTexture("_DetailMask", albedo);   // alpha of the albedo: 1 on bark, 0 on moss and leaves
                float t = info.unity.detail_tiling_on_uv0;
                mat.SetTextureScale("_DetailAlbedoMap", new Vector2(t, t));
                mat.EnableKeyword("_DETAIL_MULX2");
            }
        }
        static Texture2D Tex(string id, string set, string kind) => AssetDatabase.LoadAssetAtPath<Texture2D>($"{Models}/{id}/Textures/{id}_{set}_{kind}.png");
        // texture set of a slot, from the FBX material name M_<id>_<set>
        static string SetOf(Material m) { var n = m ? m.name : ""; if (n.EndsWith("_Leaf")) return "Leaf"; int k = n.LastIndexOf('_'); return k >= 0 && n.Length == k + 2 ? n.Substring(k + 1) : "A"; }

        static bool IsDetail(Renderer r) => r.name.StartsWith("Detail_");
        static bool IsCollision(Component r) => r.name.EndsWith("_Collision");

        static GameObject Place(string id, Info info)
        {
            var go = (GameObject)PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>($"{Models}/{id}/{id}_{Version(id)}.fbx"));
            foreach (var r in go.GetComponentsInChildren<Renderer>(true))
            {
                r.sharedMaterials = r.sharedMaterials.Select(sm => Mat(id, SetOf(sm), info)).ToArray();
                if (IsCollision(r)) { r.enabled = false; r.gameObject.AddComponent<MeshCollider>().sharedMesh = r.GetComponent<MeshFilter>().sharedMesh; }
            }
            float[] cut = { .25f, .08f, .015f };
            var kids = go.GetComponentsInChildren<Renderer>(true).Where(r => !IsCollision(r)).ToArray();
            var lg = go.GetComponent<LODGroup>(); if (lg == null) lg = go.AddComponent<LODGroup>();   // the importer already makes one from the _LODn names
            lg.SetLODs(Enumerable.Range(0, 3).Select(i => new LOD(cut[i], kids.Where(r => r.name.EndsWith("_LOD" + i)).ToArray())).ToArray());
            return go;
        }

        static void Detail(GameObject go, bool on) { foreach (var r in go.GetComponentsInChildren<Renderer>(true).Where(IsDetail)) r.enabled = on; }
        static Renderer[] Level(GameObject go, int i, bool detail = true) =>
            go.GetComponentsInChildren<Renderer>(true).Where(r => r.name.EndsWith("_LOD" + i) && (detail || !IsDetail(r))).ToArray();
        static int Tris(IEnumerable<Renderer> rs) => rs.Sum(r => { var m = r.GetComponent<MeshFilter>().sharedMesh; return Enumerable.Range(0, m.subMeshCount).Sum(s => (int)m.GetIndexCount(s)) / 3; });
        static Bounds Box(IEnumerable<Renderer> rs) { var a = rs.ToArray(); var b = a[0].bounds; foreach (var r in a) b.Encapsulate(r.bounds); return b; }

        // ------------------------------------------------------------------ checks
        static void Inspect(string id, Info info)
        {
            var go = Place(id, info);
            var body = Box(Level(go, 0, false));
            float[] d = info.dimensions_m;
            Check(Mathf.Abs(body.size.x - d[0]) <= .02f && Mathf.Abs(body.size.z - d[1]) <= .02f && Mathf.Abs(body.size.y - d[2]) <= .02f,
                $"{id}: imported size {body.size.x:0.000} x {body.size.z:0.000} x {body.size.y:0.000} m matches model_info {d[0]} x {d[1]} x {d[2]} within 2 cm");
            Check(body.min.y < 0 && body.min.y > -1.5f, $"{id}: lowest point y = {body.min.y:0.000} (root tips dive below the ground, origin on the ground)");
            var levels = info.budget_per_lod.All;
            var tris = Enumerable.Range(0, 3).Select(i => Tris(Level(go, i))).ToArray();
            Check(Enumerable.Range(0, 3).All(i => Mathf.Abs(tris[i] - levels[i].triangles) <= levels[i].triangles * .01f),
                $"{id}: triangles LOD0/1/2 = {tris[0]} / {tris[1]} / {tris[2]} ({100f * tris[1] / tris[0]:0}% / {100f * tris[2] / tris[0]:0}%), model_info {levels[0].triangles} / {levels[1].triangles} / {levels[2].triangles}");
            var objs = Enumerable.Range(0, 3).Select(i => Level(go, i).Length).ToArray();
            Check(Enumerable.Range(0, 3).All(i => objs[i] == levels[i].objects), $"{id}: objects per LOD {string.Join(" / ", objs)} (model_info {string.Join(" / ", levels.Select(l => l.objects))})");
            var mats = go.GetComponentsInChildren<Renderer>(true).Where(r => !IsCollision(r)).SelectMany(r => r.sharedMaterials).Distinct().Count();
            Check(mats == levels[0].materials, $"{id}: {mats} materials over every LOD and Detail_ mesh (model_info {levels[0].materials}; one per texture set and one two-sided for the plants)");
            Check(go.GetComponentsInChildren<Renderer>(true).Where(IsDetail).All(r => r.sharedMaterials.All(x => x.GetFloat("_Cull") == 0)), $"{id}: Detail_* leaves render both faces");
            Check(Level(go, 0, false).All(r => r.sharedMaterials.Select(x => x.name).Distinct().Count() == r.sharedMaterials.Length),
                $"{id}: each slot of the body has its own texture set ({string.Join(", ", Level(go, 0, false)[0].sharedMaterials.Select(x => x.name))})");
            Check(info.minTier == "standard", $"{id}: minTier = {info.minTier} (landmark that blocks the way: everyone sees it)");
            Check(info.detailObjects.Length > 0 && info.detailObjects.All(g => g.StartsWith("Detail_") && Level(go, 0).Any(r => r.name.StartsWith(g))),
                $"{id}: detailObjects {string.Join(", ", info.detailObjects)} present in the FBX");
            Detail(go, false);
            int shown = Level(go, 0).Count(r => r.enabled);
            Check(shown == 1, $"{id}: Detail_* off still shows the body ({shown} mesh per LOD)");
            Detail(go, true);
            foreach (var mf in Level(go, 0).Select(r => r.GetComponent<MeshFilter>().sharedMesh))
                Check(mf.uv.Length == mf.vertexCount && mf.uv2.Length == mf.vertexCount, $"{id}: {mf.name} has UV0 (atlas) and UV1 (TileUV)");
            {
                var m0 = Level(go, 0, false)[0].GetComponent<MeshFilter>().sharedMesh; var uv = m0.uv;
                var us = uv.Select(q => q.x).Distinct().OrderBy(x => x).ToArray(); var vs = uv.Select(q => q.y).Distinct().OrderBy(x => x).ToArray();
                float du = Enumerable.Range(1, us.Length - 1).Min(i => us[i] - us[i - 1]), dv = Enumerable.Range(1, vs.Length - 1).Min(i => vs[i] - vs[i - 1]);
                var imp = (ModelImporter)AssetImporter.GetAtPath(AssetDatabase.GetAssetPath(m0));
                Report.Add($"INFO {id}: mesh compression {imp.meshCompression}; UV0 of LOD0 has {us.Length} distinct u and {vs.Length} distinct v over {m0.vertexCount} vertices (smallest step {du:0.000000} / {dv:0.000000})");
            }
            var sockets = go.GetComponentsInChildren<Transform>(true).Where(t => t.name.StartsWith("Socket_")).Select(t => $"{t.name} ({t.position.x:0.0}, {t.position.y:0.0}, {t.position.z:0.0})").ToArray();
            Check(sockets.Length == (Wall(id) ? 2 : Piece(id) || Hollow(id) ? 1 : 4), $"{id}: sockets {string.Join(", ", sockets)}");
            // collision: a 1.75 m walker (radius 0.35) passes along the path through the arch; the arch feet block
            var col = go.GetComponentsInChildren<MeshCollider>(true);
            Check(col.Length == 1, $"{id}: one collision shell (MeshCollider, renderer off)");
            Physics.SyncTransforms();
            if (Wall(id)) { WallChecks(id, go); UnityEngine.Object.DestroyImmediate(go); return; }
            if (Piece(id)) { PieceChecks(id, go); UnityEngine.Object.DestroyImmediate(go); return; }
            if (Hollow(id)) { HollowChecks(id, go); UnityEngine.Object.DestroyImmediate(go); return; }
            bool through = !Physics.CapsuleCast(new Vector3(0, .45f, -16), new Vector3(0, 1.40f, -16), .35f, Vector3.forward, 32);
            bool wide = !Physics.CapsuleCast(new Vector3(-.75f, .45f, -16), new Vector3(-.75f, 1.40f, -16), .35f, Vector3.forward, 32)
                     && !Physics.CapsuleCast(new Vector3(.75f, .45f, -16), new Vector3(.75f, 1.40f, -16), .35f, Vector3.forward, 32);
            Check(through && wide, $"{id}: a walker passes through the arch along the 2.2 m path (centre and both edges, 32 m)");
            // v004: two arches, the south one at z = 0 (origin) and the north one at z = 6.2
            foreach (var (nm, z) in new[] { ("south", 0f), ("north", 6.2f) })
            {
                bool footW = Physics.Raycast(new Vector3(-12, 1.2f, z), Vector3.right, out var hw, 12) && hw.point.x < -3.5f;
                bool footE = Physics.Raycast(new Vector3(12, 1.2f, z), Vector3.left, out var he, 12) && he.point.x > 3.5f;
                Check(footW && footE, $"{id}: {nm} arch feet block (hit at x = {hw.point.x:0.00} and {he.point.x:0.00})");
                bool up = Physics.Raycast(new Vector3(0, .1f, z), Vector3.up, out var hu, 20);
                Check(up && hu.distance > 4.5f, $"{id}: collision clear height under the {nm} crown {hu.distance + .1f:0.00} m");
            }
            UnityEngine.Object.DestroyImmediate(go);
        }

        // DR02: the root is a wall along x between its two sockets. A 1.75 m walker (radius 0.35) crossing it (along Unity z) is stopped
        // everywhere between the sockets, also under variant A's raised hump (the gap there is about 1 m).
        static void WallChecks(string id, GameObject go)
        {
            var s = go.GetComponentsInChildren<Transform>(true).Where(t => t.name.StartsWith("Socket_")).Select(t => t.position.x).OrderBy(x => x).ToArray();
            int n = 0, stopped = 0;
            for (float x = s[0] + .6f; x <= s[s.Length - 1] - .6f; x += .5f)
            {
                n++;
                bool a = Physics.CapsuleCast(new Vector3(x, .45f, -9), new Vector3(x, 1.40f, -9), .35f, Vector3.forward, 18);
                bool b = Physics.CapsuleCast(new Vector3(x, .45f, 9), new Vector3(x, 1.40f, 9), .35f, Vector3.back, 18);
                if (a && b) stopped++;
            }
            Check(n > 0 && stopped >= n - 1, $"{id}: a walker crossing the wall is stopped at {stopped} of {n} places between the sockets (every 0.5 m)");
            // an opening = every height from 0.3 m to 1.75 m clear (rays across the wall every 0.15 m) over at least 0.75 m of width
            int run = 0, widest = 0;
            for (float x = s[0] + .6f; x <= s[s.Length - 1] - .6f; x += .25f)
            {
                bool clear = true;
                for (float y = .3f; y <= 1.76f && clear; y += .15f)
                    clear = !Physics.Raycast(new Vector3(x, y, -9), Vector3.forward, 18) && !Physics.Raycast(new Vector3(x, y, 9), Vector3.back, 18);
                run = clear ? run + 1 : 0; widest = Math.Max(widest, run);
            }
            Check(widest < 3, $"{id}: no opening a person could walk through between the sockets (widest column clear from 0.3 to 1.75 m: {widest * .25f:0.00} m)");
            // two copies joined by the sockets (the copy's Socket_Head put on this one's Socket_Tail, position and rotation):
            // a walker crossing the joint (2 m either side of it, every 0.5 m) is stopped
            var tail = go.GetComponentsInChildren<Transform>(true).First(t => t.name.StartsWith("Socket_Tail"));
            var head0 = go.GetComponentsInChildren<Transform>(true).First(t => t.name.StartsWith("Socket_Head"));
            var dup = UnityEngine.Object.Instantiate(go);
            var head = dup.GetComponentsInChildren<Transform>(true).First(t => t.name.StartsWith("Socket_Head"));
            dup.transform.rotation = tail.rotation * Quaternion.Inverse(head.rotation) * dup.transform.rotation;
            dup.transform.position += tail.position - head.position;
            Physics.SyncTransforms();
            var along = Vector3.ProjectOnPlane(tail.position - head0.position, Vector3.up).normalized;
            var across = Vector3.Cross(Vector3.up, along);
            int jn = 0, js = 0;
            for (float k = -2; k <= 2.01f; k += .5f)
            {
                var p = tail.position + along * k;
                jn++;
                bool a1 = Physics.CapsuleCast(p - across * 9 + Vector3.up * .45f, p - across * 9 + Vector3.up * 1.4f, .35f, across, 18);
                bool b1 = Physics.CapsuleCast(p + across * 9 + Vector3.up * .45f, p + across * 9 + Vector3.up * 1.4f, .35f, -across, 18);
                if (a1 && b1) js++;
            }
            Check(js == jn && (head.position - tail.position).magnitude < .01f, $"{id}: two copies joined Socket_Head on Socket_Tail: a walker crossing the joint is stopped at {js} of {jn} places");
            UnityEngine.Object.DestroyImmediate(dup);
            Physics.SyncTransforms();
            bool top = Physics.Raycast(new Vector3((s[0] + s[s.Length - 1]) / 2, 20, 0), Vector3.down, out var h, 25);
            Report.Add($"INFO {id}: collision top at the middle {(top ? h.point.y : 0):0.00} m");
        }

        static Info InfoOf(string id) => JsonUtility.FromJson<Info>(File.ReadAllText(Path.Combine(Exports, id, "model_info.json")));
        static Transform Sock(GameObject g, string name) => g.GetComponentsInChildren<Transform>(true).First(t => t.name.StartsWith(name));
        // put `g` so that its socket `gs` sits exactly on `target` (position and rotation)
        static void Snap(GameObject g, Transform gs, Transform target)
        {
            g.transform.rotation = target.rotation * Quaternion.Inverse(gs.rotation) * g.transform.rotation;
            g.transform.position += target.position - gs.position;
            Physics.SyncTransforms();
        }
        // a walker crossing a line (centre p, direction along) is stopped at every 0.5 m from k0 to k1
        static int Stopped(Vector3 p, Vector3 along, float k0, float k1, out int n)
        {
            var across = Vector3.Cross(Vector3.up, along); int js = 0; n = 0;
            for (float k = k0; k <= k1 + .01f; k += .5f)
            {
                var q = p + along * k; n++;
                bool a = Physics.CapsuleCast(q - across * 9 + Vector3.up * .45f, q - across * 9 + Vector3.up * 1.4f, .35f, across, 18);
                bool b = Physics.CapsuleCast(q + across * 9 + Vector3.up * .45f, q + across * 9 + Vector3.up * 1.4f, .35f, -across, 18);
                if (a && b) js++;
            }
            return js;
        }
        static GameObject Partner(string id) => id == "DR03_RootEnd" ? Place("DR02_RootWall_A", InfoOf("DR02_RootWall_A")) : null;

        // DR03 end cap: its Socket_Wall on DR02 A's Socket_Head; a walker crossing the line wall + cap is stopped from 2 m into the
        // wall to 2 m out along the cap (no gap at the joint). Crossing piece: a walker crossing the lower root near the crossing is stopped.
        static void PieceChecks(string id, GameObject go)
        {
            Physics.SyncTransforms();
            if (id == "DR03_RootEnd")
            {
                var sw = Sock(go, "Socket_Wall");
                var wall = Partner(id);
                Snap(wall, Sock(wall, "Socket_Head"), sw);
                var along = Vector3.ProjectOnPlane(sw.right, Vector3.up).normalized;      // Blender +X of the socket = towards the wall
                var tail = Sock(wall, "Socket_Tail").position;
                Check(Vector3.Dot(tail - sw.position, along) > 5, $"{id}: Socket_Wall points into the wall (DR02 A's tail lies {Vector3.Dot(tail - sw.position, along):0.0} m along it)");
                int js = Stopped(sw.position, along, -2, 2, out int jn);
                Check(js == jn, $"{id}: joined to DR02_RootWall_A (Socket_Wall on Socket_Head): a walker crossing the wall and cap is stopped at {js} of {jn} places (2 m either side of the joint, every 0.5 m)");
                bool top = Physics.Raycast(sw.position - along * 1.5f + Vector3.up * 20, Vector3.down, out var h, 25);
                Report.Add($"INFO {id}: collision top 1.5 m out from the wall {(top ? h.point.y : 0):0.00} m");
                UnityEngine.Object.DestroyImmediate(wall);
            }
            else
            {
                var sj = Sock(go, "Socket_Joint");
                int js = Stopped(sj.position, Vector3.right, -1.5f, 1.5f, out int jn);
                Check(js == jn, $"{id}: a walker crossing the lower root is stopped at {js} of {jn} places (1.5 m either side of the crossing, every 0.5 m)");
                bool top = Physics.Raycast(sj.position + Vector3.up * 20, Vector3.down, out var h, 25);
                Report.Add($"INFO {id}: collision top at the crossing {(top ? h.point.y : 0):0.00} m");
            }
            Physics.SyncTransforms();
        }

        // DR04 hollow: the hole is 1.2 m deep and dark, a set piece and not a passage. A 1.75 m walker (radius 0.35) heading into it
        // along its centre line is stopped at the mouth; walking across the piece (along x) the arches and buttresses stop it; from
        // behind the back wall stops it.
        static void HollowChecks(string id, GameObject go)
        {
            Physics.SyncTransforms();
            bool mouth = Physics.CapsuleCast(new Vector3(0, .45f, -6), new Vector3(0, 1.4f, -6), .35f, Vector3.forward, out var hm, 12);
            float stop = mouth ? -6 + hm.distance : 99;
            Check(mouth && stop > -1.2f && stop < 1.0f, $"{id}: a walker heading into the hole is stopped with its centre at z = {stop:0.00} m (at the mouth, not inside)");
            int js = 0, jn = 0;
            for (float z = -.5f; z <= 1.51f; z += .5f)
            {
                jn++;
                bool a = Physics.CapsuleCast(new Vector3(-9, .45f, z), new Vector3(-9, 1.4f, z), .35f, Vector3.right, 18);
                bool b = Physics.CapsuleCast(new Vector3(9, .45f, z), new Vector3(9, 1.4f, z), .35f, Vector3.left, 18);
                if (a && b) js++;
            }
            Check(js == jn, $"{id}: a walker crossing the piece side to side is stopped at {js} of {jn} places (z = -0.5 to 1.5 m, every 0.5 m)");
            bool back = Physics.CapsuleCast(new Vector3(0, .45f, 9), new Vector3(0, 1.4f, 9), .35f, Vector3.back, out var hb, 12);
            Check(back && 9 - hb.distance > 1.5f, $"{id}: a walker coming from behind is stopped by the back wall (centre at z = {(back ? 9 - hb.distance : 0):0.00} m)");
            bool up = Physics.Raycast(new Vector3(0, .1f, .22f), Vector3.up, out var hu, 5);
            Report.Add($"INFO {id}: collision clear height in the mouth {(up ? hu.distance + .1f : 0):0.00} m");
        }

        // ------------------------------------------------------------------ renders
        static Camera cam; static RenderTexture target; static Light sun;

        static void Shots(string id, Info info)
        {
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene);
            sun = new GameObject("Sun").AddComponent<Light>(); sun.type = LightType.Directional; sun.shadows = LightShadows.Soft;
            var ground = GameObject.CreatePrimitive(PrimitiveType.Plane); ground.transform.localScale = Vector3.one * 30;
            ground.GetComponent<Renderer>().sharedMaterial = Flat("ground", new Color(.17f, .15f, .12f));
            cam = new GameObject("Review Camera").AddComponent<Camera>(); cam.nearClipPlane = .05f; cam.farClipPlane = 600;
            UnityEngine.Rendering.Universal.CameraExtensions.GetUniversalAdditionalCameraData(cam).renderPostProcessing = true;
            target = new RenderTexture(1536, 864, 24) { antiAliasing = 4 }; cam.targetTexture = target;
            // same sun and tri-light ambient as the game world (QingxiWorldBuilder.Lighting), plus a light fog for D2
            sun.transform.rotation = Quaternion.Euler(50, -35, 0); sun.intensity = 1.25f;
            RenderSettings.ambientMode = AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = new Color(.62f, .7f, .78f); RenderSettings.ambientEquatorColor = new Color(.55f, .58f, .52f); RenderSettings.ambientGroundColor = new Color(.32f, .3f, .26f);
            RenderSettings.fog = true; RenderSettings.fogMode = FogMode.Exponential; RenderSettings.fogDensity = .006f; RenderSettings.fogColor = new Color(.66f, .70f, .74f);
            cam.clearFlags = CameraClearFlags.SolidColor; cam.backgroundColor = new Color(.66f, .70f, .74f);
            var go = Place(id, info);
            var ruler = GameObject.CreatePrimitive(PrimitiveType.Capsule);
            UnityEngine.Object.DestroyImmediate(ruler.GetComponent<Collider>());
            ruler.transform.position = new Vector3(0, .875f, 0); ruler.transform.localScale = new Vector3(.42f, .875f, .42f);
            ruler.GetComponent<Renderer>().sharedMaterial = Flat("ruler", new Color(.85f, .85f, .85f));
            var lg = go.GetComponent<LODGroup>();
            lg.ForceLOD(0);
            // Blender (x, y, z) -> Unity (x, z, y) with the front (-Y) towards -Z
            if (Piece(id))
            {
                ruler.transform.position = new Vector3(-1, .875f, -2.6f);
                var fr = new Vector3(0, 1.3f, -10); var fa = new Vector3(0, .7f, 0);
                Shot(id, "front-lod0", fr, fa, 36.2f);
                if (Raw) { Shot(id, "bark-close", new Vector3(-.8f, 1.3f, -2.6f), new Vector3(-.6f, .7f, -.2f), 22.9f); return; }
                // crossing piece: seen from the obtuse side of the X (from -6.5,-7 the camera looks straight along the upper root)
                if (id == "DR03_RootCross") Shot(id, "threequarter", new Vector3(4.4f, 3.0f, -8.4f), new Vector3(-.2f, .6f, .2f), 39.6f);
                else Shot(id, "threequarter", new Vector3(-6.5f, 2.6f, -7), new Vector3(.3f, .6f, 0), 39.6f);
                Shot(id, "end", id == "DR03_RootEnd" ? new Vector3(9, 1.3f, .6f) : new Vector3(-9, 1.3f, -.6f), fa, 32.2f);
                Shot(id, "back", new Vector3(1.2f, 1.8f, 9.5f), fa, 36.2f);
                Shot(id, "bark-close", new Vector3(-.8f, 1.3f, -2.6f), new Vector3(-.6f, .7f, -.2f), 22.9f);
                for (int i = 1; i < 3; i++) { lg.ForceLOD(i); Shot(id, $"front-lod{i}", fr, fa, 36.2f); }
                lg.ForceLOD(1); Detail(go, false);
                Shot(id, "front-standard-tier-lod1-nodetail", fr, fa, 36.2f);
                Detail(go, true); lg.ForceLOD(-1);
                // in use: the end cap on the thick end of DR02 A; the crossing piece on the joint of two DR02 B
                var extra = new List<GameObject>();
                ruler.transform.position = new Vector3(2.5f, .875f, -2.2f);
                if (id == "DR03_RootEnd")
                {
                    var w = Partner(id); Snap(w, Sock(w, "Socket_Head"), Sock(go, "Socket_Wall")); extra.Add(w);
                    Shot(id, "with-wall", new Vector3(7.5f, 2.4f, -8), new Vector3(-2.5f, 1, 0), 39.6f);
                    Shot(id, "with-wall-path", new Vector3(5, 1.65f, -3.2f), new Vector3(-1, .9f, .3f), 49.4f);
                }
                else
                {
                    var iB = InfoOf("DR02_RootWall_B");
                    var w1 = Place("DR02_RootWall_B", iB); var w2 = Place("DR02_RootWall_B", iB); extra.Add(w1); extra.Add(w2);
                    Snap(w1, Sock(w1, "Socket_Tail"), Sock(go, "Socket_Joint"));
                    Snap(w2, Sock(w2, "Socket_Head"), Sock(w1, "Socket_Tail"));
                    Shot(id, "on-joint", new Vector3(-6, 2.6f, -9), new Vector3(.5f, .8f, 0), 39.6f);
                }
                foreach (var e in extra) UnityEngine.Object.DestroyImmediate(e);
                Report.Add($"INFO renders written to art/previews/d2-roots-b/{id}/unity");
                return;
            }
            if (Hollow(id))
            {
                ruler.transform.position = new Vector3(-1, .875f, -3);
                var fr = new Vector3(0, 1.3f, -8); var fa = new Vector3(0, .9f, .5f);
                Shot(id, "front-lod0", fr, fa, 36.2f);
                if (Raw) { Shot(id, "bark-close", new Vector3(-1.6f, 1.3f, -1.6f), new Vector3(-.7f, .9f, .4f), 22.9f); return; }
                Shot(id, "threequarter", new Vector3(-5, 3.0f, -5.5f), new Vector3(0, .8f, .6f), 39.6f);
                Shot(id, "eye", new Vector3(.7f, 1.6f, -3), new Vector3(-.1f, .6f, 1), 49.4f);
                Shot(id, "end", new Vector3(7.5f, 1.4f, -.3f), new Vector3(0, .9f, .6f), 36.2f);
                Shot(id, "back", new Vector3(1.5f, 2.2f, 8), new Vector3(0, .9f, .5f), 36.2f);
                Shot(id, "bark-close", new Vector3(-1.6f, 1.3f, -1.6f), new Vector3(-.7f, .9f, .4f), 22.9f);
                for (int i = 1; i < 3; i++) { lg.ForceLOD(i); Shot(id, $"front-lod{i}", fr, fa, 36.2f); }
                lg.ForceLOD(1); Detail(go, false);
                Shot(id, "front-standard-tier-lod1-nodetail", fr, fa, 36.2f);
                Detail(go, true); lg.ForceLOD(-1);
                Report.Add($"INFO renders written to art/previews/d2-roots-b/{id}/unity");
                return;
            }
            if (Wall(id))
            {
                ruler.transform.position = new Vector3(-1, .875f, -3);
                Shot(id, "front-lod0", new Vector3(0, 1.6f, -17), new Vector3(0, 1.4f, 0), 36.2f);          // 30 mm
                if (Raw) { Shot(id, "bark-close", new Vector3(-1.5f, 1.6f, -3.4f), new Vector3(-2.5f, 1.6f, -.3f), 22.9f); return; }
                Shot(id, "threequarter", new Vector3(-11, 3.2f, -12), new Vector3(.5f, 1.3f, 0), 39.6f);    // 28 mm
                Shot(id, "end", new Vector3(-16, 1.6f, -1), new Vector3(0, 1.5f, 0), 32.2f);
                Shot(id, "back", new Vector3(2, 2.2f, 16), new Vector3(0, 1.4f, 0), 36.2f);
                Shot(id, "bark-close", new Vector3(-1.5f, 1.6f, -3.4f), new Vector3(-2.5f, 1.6f, -.3f), 22.9f);
                for (int i = 1; i < 3; i++) { lg.ForceLOD(i); Shot(id, $"front-lod{i}", new Vector3(0, 1.6f, -17), new Vector3(0, 1.4f, 0), 36.2f); }
                lg.ForceLOD(1); Detail(go, false);
                Shot(id, "front-standard-tier-lod1-nodetail", new Vector3(0, 1.6f, -17), new Vector3(0, 1.4f, 0), 36.2f);
                Detail(go, true); lg.ForceLOD(-1);
                Report.Add($"INFO renders written to art/previews/d2-roots-b/{id}/unity");
                return;
            }
            Shot(id, "V2cam-lod0", new Vector3(.5f, 1.7f, -15), new Vector3(0, 1.7f, 0), 49.4f);        // 22 mm on a 36 mm sensor, 16:9, level like concept V2; same position and lens as the core team's V2 camera
            if (Raw) { Shot(id, "bark-close", new Vector3(-2.2f, 1.6f, -3.2f), new Vector3(-5.4f, 1.8f, -.9f), 22.9f); return; }
            Shot(id, "threequarter", new Vector3(-15, 4.5f, -15), new Vector3(0, 2.6f, 0), 39.6f);     // 28 mm
            Shot(id, "back", new Vector3(1, 2.5f, 24), new Vector3(0, 2.8f, 0), 32.2f);                // 35 mm
            Shot(id, "foot-west", new Vector3(-9, 1.5f, -7.5f), new Vector3(-5, 1.4f, -.5f), 32.2f);
            Shot(id, "bark-close", new Vector3(-2.2f, 1.6f, -3.2f), new Vector3(-5.4f, 1.8f, -.9f), 22.9f);   // 50 mm
            for (int i = 1; i < 3; i++) { lg.ForceLOD(i); Shot(id, $"V2cam-lod{i}", new Vector3(.5f, 1.7f, -15), new Vector3(0, 1.7f, 0), 49.4f); }
            lg.ForceLOD(1); Detail(go, false);
            Shot(id, "V2cam-standard-tier-lod1-nodetail", new Vector3(.5f, 1.7f, -15), new Vector3(0, 1.7f, 0), 49.4f);
            Detail(go, true); lg.ForceLOD(-1);
            Report.Add($"INFO renders written to art/previews/d2-roots-b/{id}/unity");
        }

        static void Shot(string id, string file, Vector3 from, Vector3 at, float fov)
        {
            cam.fieldOfView = fov; cam.transform.position = from; cam.transform.LookAt(at); cam.Render();
            RenderTexture.active = target;
            var image = new Texture2D(target.width, target.height, TextureFormat.RGB24, false);
            image.ReadPixels(new Rect(0, 0, target.width, target.height), 0, 0); image.Apply();
            File.WriteAllBytes(Path.Combine(Out(id), $"{id}-{file}{(Raw ? "-rawimport" : "")}.png"), image.EncodeToPNG());
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
