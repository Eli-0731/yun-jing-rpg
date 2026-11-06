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
    // Work pack B-48h, first batch (TE01 terraces, TE02 tea bushes, TE03 stair / path / stepping stones).
    // Imports art/exports/tea-terraces-b into a gitignored folder, checks every model against its model_info.json, then lays out
    // art/exports/tea-terraces-b/assembly/farm-assembly.json and walks a 1.75 m CharacterController through it (paths, joints,
    // all eight stairs, both ends, the breaches, two bends), measures the joints by ray, and takes URP captures.
    // Writes artifacts/tea-terraces-unity/. Run with -executeMethod YunJing.Editor.TeaTerracesModelCheck.Run
    // Scripted walking is an aid only: it does not replace a person walking it with keyboard and mouse.
    public static class TeaTerracesModelCheck
    {
        const string Root = "Assets/YunJing/Generated/TeaTerracesB";
        const int SeamLayer = 30;
        static string Repo => Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", ".."));
        static string Exports => Path.Combine(Repo, "art", "exports", "tea-terraces-b");
        static string Out => Path.Combine(Repo, "artifacts", "tea-terraces-unity");
        static readonly string[] Ids = { "TE01_StraightA", "TE01_StraightB", "TE01_InnerBend", "TE01_OuterBend", "TE01_End", "TE01_Broken",
            "TE02_Round", "TE02_Wide", "TE02_Tall", "TE03_Stair", "TE03_Path", "TE03_Stepping",
            "TE01_GentleOuter", "TE01_GentleInner", "TE01_StraightB_H08", "TE01_StraightB_H12", "TE01_End_H08", "TE01_End_H12" };
        static readonly List<string> Report = new List<string>();
        static int failed;
        static CharacterController cc;

        [Serializable] class ModelInfo { public float[] dimensions_m, bounds_min_m, bounds_max_m, size_limit_m; public string minTier; public LodTotals lod_totals; }
        [Serializable] class LodTotals { public int LOD0, LOD1, LOD2; }
        [Serializable] class Placement { public string id; public float[] position_m; public float rotation_z_deg; public bool mirror_x; public int row; }
        [Serializable] class Assembly { public Placement[] pieces; public int rows; }

        // the exported version of each model (v002 for the TE01 pieces with the ridge and ditch), from its model_info.json
        static readonly Dictionary<string, string> ver = new Dictionary<string, string>();
        static string Ver(string id)
        {
            if (!ver.TryGetValue(id, out var v))
            {
                var txt = File.ReadAllText(Path.Combine(Exports, id, "model_info.json")); int at = txt.IndexOf("\"version\""); v = "v001";
                if (at >= 0) { int q1 = txt.IndexOf('"', txt.IndexOf(':', at) + 1), q2 = txt.IndexOf('"', q1 + 1); v = txt.Substring(q1 + 1, q2 - q1 - 1); }
                ver[id] = v;
            }
            return v;
        }
        static string Fbx(string id) => $"{Root}/{id}/{id}_{Ver(id)}.fbx";

        // TE01 v002 tread profile (te_terrace.field_profile): a flat-topped planting ridge under the bush line, a runoff ditch at the back
        const float RidgeD = 2.95f, RidgeHalf = .60f, RidgeH = .18f, RidgeTop = .45f, DitchD = 3.74f, DitchHalf = .20f, DitchH = .12f;
        static float Profile(float d)
        {
            float t = Mathf.Abs(d - RidgeD) / RidgeHalf, u = Mathf.Clamp01((1 - t) / (1 - RidgeTop)), z = RidgeH * u * u * (3 - 2 * u);
            t = Mathf.Abs(d - DitchD) / DitchHalf; if (t < 1) z -= DitchH * Mathf.Pow(Mathf.Cos(t * Mathf.PI / 2), 2);
            return z;
        }
        static readonly float RG = 8f / (Mathf.PI / 6);   // gentle bend wall radius
        static Vector2 Rot(Vector2 v, float deg) { float a = deg * Mathf.Deg2Rad, c = Mathf.Cos(a), s = Mathf.Sin(a); return new Vector2(c * v.x - s * v.y, s * v.x + c * v.y); }
        // tread point (s along the wall, d behind the front edge) of a TE01 piece in its own axes; bends enter like a straight's left end
        static Vector2 Local(string kind, float s, float d)
        {
            if (kind == "outer") { float a = -Mathf.PI / 2 + s / RG, r = RG - d; return new Vector2(-4 + r * Mathf.Cos(a), -2 + RG + r * Mathf.Sin(a)); }
            if (kind == "inner") { float a = Mathf.PI / 2 - s / RG, r = RG + d; return new Vector2(-4 + r * Mathf.Cos(a), -2 - RG + r * Mathf.Sin(a)); }
            return new Vector2(s - 4, -2 + d);
        }
        struct Link { public string id, kind; public Vector2 origin; public float yaw; }
        static readonly List<Link> chain = new List<Link>();
        static readonly List<(Link l, int row, float z, float rise)> heights = new List<(Link, int, float, float)>();

        static void Check(bool ok, string what) { Report.Add((ok ? "PASS " : "FAIL ") + what); if (!ok) failed++; }
        // Blender (x, y, z) -> Unity (x, z, y)
        static Vector3 U(float x, float y, float z) => new Vector3(x, z, y);
        static float Front(int row) => -18f + 4 * row;

        static void UsePipeline()
        {
            var pipeline = AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>("Assets/YunJing/Generated/URP.asset");
            if (pipeline == null) { ProjectBuilder.Generate(); pipeline = AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>("Assets/YunJing/Generated/URP.asset"); }
            if (GraphicsSettings.defaultRenderPipeline != pipeline) GraphicsSettings.defaultRenderPipeline = pipeline;
            if (QualitySettings.renderPipeline != pipeline) QualitySettings.renderPipeline = pipeline;
            pipeline.shadowDistance = 60;
        }

        public static void Run()
        {
            Report.Clear(); failed = 0;
            UsePipeline();
            if (Directory.Exists(Out)) Directory.Delete(Out, true);
            Directory.CreateDirectory(Out);
            foreach (var id in Ids) Copy(id);
            AssetDatabase.Refresh();
            foreach (var id in Ids) Configure(id);
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            Lighting();
            // each model on its own, far from the assembly
            var single = new Dictionary<string, GameObject>();
            Report.Add("INFO versions: " + string.Join(", ", Ids.Select(i => $"{i} {Ver(i)}")));
            for (int i = 0; i < Ids.Length; i++) { single[Ids[i]] = Place(Ids[i], new Vector3(200 + i % 4 * 16, 0, 200 + i / 4 * 16), 0, false); Verify(Ids[i], single[Ids[i]]); }
            foreach (var id in Ids.Where(i => i.StartsWith("TE02"))) Wind(id, single[id]);
            foreach (var id in Ids) Sockets(id, single[id]);
            // the 40 x 40 m sample
            var asm = JsonUtility.FromJson<Assembly>(File.ReadAllText(Path.Combine(Exports, "assembly", "farm-assembly.json")));
            var placed = new List<(Placement p, GameObject go)>();
            foreach (var p in asm.pieces) placed.Add((p, Place(p.id, U(p.position_m[0], p.position_m[1], p.position_m[2]), p.rotation_z_deg, p.mirror_x)));
            Report.Add($"INFO assembly: {placed.Count} pieces from farm-assembly.json");
            var ground = GameObject.CreatePrimitive(PrimitiveType.Plane); ground.name = "Placeholder_Ground"; ground.transform.localScale = new Vector3(30, 1, 30); ground.transform.position = new Vector3(0, 0, -40);
            ground.GetComponent<Renderer>().sharedMaterial = GroundMat();
            // bends, joined to straights away from the sample
            var bend = new List<GameObject> {
                Place("TE01_StraightA", U(100, 0, 0), 0, false), Place("TE01_OuterBend", U(108, 2, 0), 0, false),
                Place("TE01_StraightB", U(100, -30, 0), 0, false), Place("TE01_InnerBend", U(108, -32, 0), 0, false) };
            GentleChain(); HeightRows();
            Physics.SyncTransforms();
            Seams(placed, asm.rows);
            Walks(asm, placed);
            Capture(placed, single, bend);
            Showcase();
            File.WriteAllText(Path.Combine(Out, "unity-verify-report.txt"), string.Join("\n", Report) + $"\n\nUnity {Application.unityVersion}; failed checks: {failed}; walking is a scripted CharacterController, not a person\n");
            Debug.Log("TEA_TERRACES_" + (failed == 0 ? "PASS" : "FAIL") + "\n" + string.Join("\n", Report));
            if (failed > 0 && Application.isBatchMode) EditorApplication.Exit(1);
        }

        static void Copy(string id)
        {
            var src = Path.Combine(Exports, id); var dst = Path.Combine(Repo, "apps", "game", Root, id);
            if (!Directory.Exists(src)) throw new DirectoryNotFoundException(src);
            Directory.CreateDirectory(Path.Combine(dst, "Textures"));
            foreach (var old in Directory.GetFiles(dst, "*.fbx").Where(f => !f.EndsWith($"_{Ver(id)}.fbx"))) { File.Delete(old); if (File.Exists(old + ".meta")) File.Delete(old + ".meta"); }
            foreach (var file in Directory.GetFiles(src, $"{id}_{Ver(id)}.fbx").Concat(Directory.GetFiles(Path.Combine(src, "Textures"), "*.png")))
                File.Copy(file, Path.Combine(dst, file.Substring(src.Length + 1)), true);
        }

        static void Configure(string id)
        {
            var importer = AssetImporter.GetAtPath(Fbx(id)) as ModelImporter;
            if (importer == null) throw new FileNotFoundException("FBX not imported", id);
            importer.bakeAxisConversion = true; importer.materialImportMode = ModelImporterMaterialImportMode.None; importer.isReadable = true;
            importer.importAnimation = false; importer.importCameras = false; importer.importLights = false; importer.addCollider = false;
            importer.importNormals = ModelImporterNormals.Import;
            importer.SaveAndReimport();
            foreach (var tex in Directory.GetFiles(Path.Combine(Repo, "apps", "game", Root, id, "Textures"), "*.png"))
            {
                var path = $"{Root}/{id}/Textures/{Path.GetFileName(tex)}";
                var ti = AssetImporter.GetAtPath(path) as TextureImporter; if (ti == null) continue;
                bool normal = path.EndsWith("_Normal.png");
                bool data = path.EndsWith("_MetallicSmoothness.png") || path.EndsWith("_Roughness.png") || path.EndsWith("_Metallic.png");
                ti.textureType = normal ? TextureImporterType.NormalMap : TextureImporterType.Default;
                ti.sRGBTexture = !normal && !data; ti.maxTextureSize = 4096;
                if (path.EndsWith("TE02_LeafCards_BaseColor.png")) { ti.alphaSource = TextureImporterAlphaSource.FromInput; ti.alphaIsTransparency = true; ti.mipMapsPreserveCoverage = true; ti.alphaTestReferenceValue = .5f; }
                ti.SaveAndReimport();
            }
        }

        static Texture2D Tex(string id, string file) => AssetDatabase.LoadAssetAtPath<Texture2D>($"{Root}/{id}/Textures/{file}");

        static Material Mat(string id)
        {
            var path = $"{Root}/{id}.mat";
            var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (mat == null) { mat = new Material(Shader.Find("Universal Render Pipeline/Lit")); AssetDatabase.CreateAsset(mat, path); }
            mat.SetTexture("_BaseMap", Tex(id, id + "_BaseColor.png")); mat.SetColor("_BaseColor", Color.white);
            mat.SetTexture("_BumpMap", Tex(id, id + "_Normal.png")); mat.EnableKeyword("_NORMALMAP");
            mat.SetTexture("_MetallicGlossMap", Tex(id, id + "_MetallicSmoothness.png")); mat.EnableKeyword("_METALLICSPECGLOSSMAP"); mat.SetFloat("_Smoothness", 1);
            EditorUtility.SetDirty(mat); return mat;
        }

        // TE02 leaf cards: URP Lit, alpha clipped at 0.5, both faces drawn
        static Material LeafMat(string id)
        {
            var path = $"{Root}/{id}_LeafCards.mat";
            var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (mat == null) { mat = new Material(Shader.Find("Universal Render Pipeline/Lit")); AssetDatabase.CreateAsset(mat, path); }
            mat.SetTexture("_BaseMap", Tex(id, "TE02_LeafCards_BaseColor.png")); mat.SetColor("_BaseColor", Color.white);
            mat.SetTexture("_BumpMap", Tex(id, "TE02_LeafCards_Normal.png")); mat.EnableKeyword("_NORMALMAP");
            mat.SetFloat("_AlphaClip", 1); mat.SetFloat("_Cutoff", .5f); mat.EnableKeyword("_ALPHATEST_ON");
            mat.SetFloat("_Cull", (float)CullMode.Off); mat.SetFloat("_Smoothness", .3f); mat.SetFloat("_Metallic", 0);
            mat.SetOverrideTag("RenderType", "TransparentCutout"); mat.renderQueue = (int)RenderQueue.AlphaTest;
            EditorUtility.SetDirty(mat); return mat;
        }

        static Material groundMat;
        static Material GroundMat()
        {
            if (groundMat != null) return groundMat;
            groundMat = new Material(Shader.Find("Universal Render Pipeline/Lit")); groundMat.SetColor("_BaseColor", new Color(.2f, .15f, .1f)); groundMat.SetFloat("_Smoothness", .05f);
            return groundMat;
        }

        static GameObject Place(string id, Vector3 position, float rotZ, bool mirror)
        {
            var go = (GameObject)PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>(Fbx(id)));
            PrefabUtility.UnpackPrefabInstance(go, PrefabUnpackMode.Completely, InteractionMode.AutomatedAction);
            go.transform.position = position; go.transform.rotation = Quaternion.Euler(0, -rotZ, 0);
            if (mirror) go.transform.localScale = new Vector3(-1, 1, 1);
            var mat = Mat(id); var leaf = id.StartsWith("TE02") ? LeafMat(id) : null;
            foreach (var r in go.GetComponentsInChildren<Renderer>(true))
            {
                if (r.name == id + "_Collision") { r.enabled = false; continue; }
                var m = r.name.Contains("_Leaves_LOD") ? leaf : mat;
                r.sharedMaterials = Enumerable.Repeat(m, r.sharedMaterials.Length).ToArray();
            }
            if (go.GetComponent<LODGroup>() == null)
            {
                float[] cut = id.StartsWith("TE01") ? new[] { .2f, .06f, .01f } : new[] { .12f, .04f, .008f };
                go.AddComponent<LODGroup>().SetLODs(Enumerable.Range(0, 3).Select(i => new LOD(cut[i], go.GetComponentsInChildren<Renderer>(true).Where(r => r.name.EndsWith("_LOD" + i)).ToArray())).ToArray());
            }
            var col = go.GetComponentsInChildren<MeshFilter>(true).FirstOrDefault(m => m.name == id + "_Collision");
            if (col != null) col.gameObject.AddComponent<MeshCollider>().sharedMesh = col.sharedMesh;
            return go;
        }

        // Two rows of the 30 degree contour chain at x 146..: StraightA | GentleOuter | StraightB (turned 30) | GentleInner | StraightA.
        // The next piece's origin = exit front corner + rot(heading) (4, 2); row 1 is the same chain at (0, +4, +1).
        static void GentleChain()
        {
            chain.Clear();
            var o = new Vector2(150, 0); float yaw = 0;
            foreach (var (id, kind) in new[] { ("TE01_StraightA", "straight"), ("TE01_GentleOuter", "outer"), ("TE01_StraightB", "straight"), ("TE01_GentleInner", "inner"), ("TE01_StraightA", "straight") })
            {
                chain.Add(new Link { id = id, kind = kind, origin = o, yaw = yaw });
                var corner = o + Rot(Local(kind, 8, 0), yaw); yaw += kind == "outer" ? 30 : kind == "inner" ? -30 : 0; o = corner + Rot(new Vector2(4, 2), yaw);
            }
            for (int r = 0; r < 2; r++) foreach (var l in chain) Place(l.id, U(l.origin.x, l.origin.y + 4 * r, r), l.yaw, false);
            var info = File.ReadAllText(Path.Combine(Exports, "TE01_GentleOuter", "model_info.json"));
            var ex = chain[0].origin + Rot(Local("straight", 8, 0), 0); var g1 = chain[1].origin + Rot(Local("outer", 0, 0), 0);
            Check((ex - g1).magnitude < 1e-4f, $"gentle chain: GentleOuter's entry corner meets the straight's right corner ({g1.x:F4}, {g1.y:F4})");
            Report.Add($"INFO gentle chain origins: {string.Join(" | ", chain.Select(l => $"{l.id} ({l.origin.x:F3}, {l.origin.y:F3}) yaw {l.yaw:F0}"))}");
        }

        // Three stacked rows of different wall height: rise 0.8 (H08), 1.0, 1.2 (H12); each row StraightB, StraightB, End; row origin z = soil of the row below.
        static void HeightRows()
        {
            heights.Clear(); float z = 0;
            var rows = new[] { ("_H08", .8f), ("", 1f), ("_H12", 1.2f) };
            for (int r = 0; r < rows.Length; r++)
            {
                var (tag, rise) = rows[r];
                for (int i = 0; i < 3; i++)
                {
                    var id = (i < 2 ? "TE01_StraightB" : "TE01_End") + tag; var o = new Vector2(150 + 8 * i, 60 + 4 * r);
                    heights.Add((new Link { id = id, kind = "straight", origin = o, yaw = 0 }, r, z, rise));
                    Place(id, U(o.x, o.y, z), 0, false);
                }
                z += rise;
            }
        }

        static void GentleAndHeightWalks()
        {
            // along the path line (d 1.15) of both gentle rows: straight, round the outer bend, along the 30 degree run, round the inner bend, straight
            for (int r = 0; r < 2; r++)
            {
                var pts = new List<Vector3>();
                for (int ci = 0; ci < chain.Count; ci++)
                    for (float s = ci == 0 ? 1 : 0; s <= (ci == chain.Count - 1 ? 7.01f : 8.01f); s += .5f)
                    { var l = chain[ci]; var q = l.origin + Rot(Local(l.kind, s, 1.15f), l.yaw); pts.Add(U(q.x, q.y + 4 * r, r + 1)); }
                Walk($"gentle row {r} along the path line through both 30 degree bends", r + .97f, r + 1.12f, pts.ToArray());
            }
            // across the tread of the last straight: from the path up over the ridge crown and down into the ditch
            var last = chain[chain.Count - 1]; Vector3 T(float d) { var q = last.origin + Rot(Local("straight", 4, d), 0); return U(q.x, q.y, 1); }
            var over = Walk("gentle row 0 from the path over the ridge crown and down its back", .85f, 1.25f, T(1.15f), T(2.95f), T(3.45f));
            Check(over.high > 1.15f, $"the walker climbs the ridge crown (feet up to {over.high:F3} m, crown 1.18) without stepping over the stepOffset");
            // each height row end to end, across both joints and onto the End
            foreach (var g in heights.GroupBy(h => h.row))
            {
                var h0 = g.First(); float soil = h0.z + h0.rise; Vector3 A(float x) => U(x, h0.l.origin.y - 2 + 1.15f, soil);
                Walk($"height row {g.Key} (rise {h0.rise} m) along the path line, across both joints onto the End", soil - .03f, soil + .12f, A(147), A(163));   // End level part: s < 1.4
            }
        }

        // The contour showcase from showcase-layout.json at Blender (0, -300, 0), in the morning light: golden sun, blue-violet shadows, fog;
        // captures and a first-person walkthrough with a CharacterController along walkthrough_route_m (frames for an mp4).
        [Serializable] class Showcase_ { public Placement[] pieces; public int rows; public float[] walkthrough_route_flat_m, hill_front_line_flat_xy; }
        static void Showcase()
        {
            var path = Path.Combine(Exports, "showcase", "showcase-layout.json");
            if (!File.Exists(path)) { Check(false, "showcase-layout.json exists"); return; }
            var text = File.ReadAllText(path); var doc = JsonUtility.FromJson<Showcase_>(text);
            const float OY = -300;
            foreach (var p in doc.pieces) Place(p.id, U(p.position_m[0], p.position_m[1] + OY, p.position_m[2]), p.rotation_z_deg, p.mirror_x);
            Report.Add($"INFO showcase: {doc.pieces.Length} pieces from showcase-layout.json at Blender y {OY}");
            float x0 = doc.pieces.Min(p => p.position_m[0]) - 160, x1 = doc.pieces.Max(p => p.position_m[0]) + 160, y1 = doc.pieces.Max(p => p.position_m[1]) + 260;
            // placeholder hillside (not part of the kit): 1 m up per 4 m back from row 0's front line, levelling off at 12 m
            var fl = doc.hill_front_line_flat_xy;
            float HillZ(float x, float y)
            {
                float yf = fl[1];
                if (x >= fl[fl.Length - 2]) yf = fl[fl.Length - 1];
                else for (int k = 2; k < fl.Length; k += 2) if (fl[k] >= x) { yf = x <= fl[0] ? fl[1] : Mathf.Lerp(fl[k - 1], fl[k + 1], (x - fl[k - 2]) / (fl[k] - fl[k - 2])); break; }
                return Mathf.Min((y - yf - 2) / 4 - .3f, 12);
            }
            var hill = new GameObject("Placeholder_Hill", typeof(MeshFilter), typeof(MeshRenderer)); var mesh = new Mesh();
            var v = new List<Vector3>(); var tri = new List<int>(); const int NX = 200, NY = 120; float yy0 = -120;
            for (int j = 0; j <= NY; j++) for (int i = 0; i <= NX; i++) { float x = Mathf.Lerp(x0, x1, i / (float)NX), y = Mathf.Lerp(yy0, y1, j / (float)NY); v.Add(U(x, y + OY, HillZ(x, y))); }
            for (int j = 0; j < NY; j++) for (int i = 0; i < NX; i++) { int a = j * (NX + 1) + i; tri.AddRange(new[] { a, a + NX + 1, a + 1, a + 1, a + NX + 1, a + NX + 2 }); }
            mesh.indexFormat = IndexFormat.UInt32; mesh.SetVertices(v); mesh.SetTriangles(tri, 0); mesh.RecalculateNormals(); hill.GetComponent<MeshFilter>().sharedMesh = mesh;
            var hm = new Material(Shader.Find("Universal Render Pipeline/Lit")); hm.SetColor("_BaseColor", new Color(.16f, .17f, .08f)); hm.SetFloat("_Smoothness", .05f);
            hill.GetComponent<MeshRenderer>().sharedMaterial = hm; hill.AddComponent<MeshCollider>().sharedMesh = mesh;
            // far ridgelines, seen only through the fog
            var far = new Material(Shader.Find("Universal Render Pipeline/Lit")); far.SetColor("_BaseColor", new Color(.30f, .36f, .42f)); far.SetFloat("_Smoothness", 0);
            var R = new System.Random(3);
            for (int k = 0; k < 8; k++)
            {
                var s = GameObject.CreatePrimitive(PrimitiveType.Sphere); UnityEngine.Object.DestroyImmediate(s.GetComponent<Collider>());
                float a = Mathf.Deg2Rad * (35 + 110 * (float)R.NextDouble()), rr = 180 * (.85f + .4f * (float)R.NextDouble()), h = 30 + 40 * (float)R.NextDouble();
                s.transform.position = U(20 + rr * Mathf.Cos(a), y1 - 60 + OY + rr * Mathf.Sin(a), -4); s.transform.localScale = new Vector3(h * 4.4f, h * 2, h * 3.2f);
                s.GetComponent<Renderer>().sharedMaterial = far;
            }
            // morning light (art direction: low warm sun, warm rim, blue-violet shadows, pale sky, thin mist)
            var sun = UnityEngine.Object.FindObjectsByType<Light>(FindObjectsSortMode.None).First(l => l.type == LightType.Directional);
            sun.color = new Color(1f, .8f, .58f); sun.intensity = 1.9f; sun.transform.rotation = Quaternion.Euler(16, 50, 0); sun.shadows = LightShadows.Soft; sun.shadowStrength = .85f;
            var rim = new GameObject("Rim_Fill").AddComponent<Light>(); rim.type = LightType.Directional; rim.color = new Color(.72f, .74f, 1f); rim.intensity = .35f; rim.shadows = LightShadows.None; rim.transform.rotation = Quaternion.Euler(30, 230, 0);
            RenderSettings.ambientMode = AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = new Color(.47f, .55f, .74f); RenderSettings.ambientEquatorColor = new Color(.62f, .55f, .48f); RenderSettings.ambientGroundColor = new Color(.18f, .16f, .2f);
            RenderSettings.fog = true; RenderSettings.fogMode = FogMode.Exponential; RenderSettings.fogDensity = .006f; RenderSettings.fogColor = new Color(.84f, .84f, .86f);
            var cam = Camera.main; cam.backgroundColor = new Color(.86f, .8f, .72f); cam.farClipPlane = 600;
            Physics.SyncTransforms();
            Vector3 S(float x, float y, float z) => U(x, y + OY, z);
            float cx = (doc.pieces.Min(p => p.position_m[0]) + doc.pieces.Max(p => p.position_m[0])) / 2;
            Shot("showcase_aerial", S(cx + 4, 12, 4), S(cx - 30, -48, 34), 42);
            Shot("showcase_from_below", S(cx - 2, 14, 6), S(cx + 18, -24, 2.2f), 55);
            Shot("showcase_walk_row2", S(6, 10.6f, 3.2f), S(-14, 7.15f, 4.6f), 65);
            Shot("showcase_bend_close", S(4, 14.5f, 4), S(6, 6, 4.6f), 55);
            // first-person walkthrough: a 1.75 m CharacterController along the route, the camera at eye height 1.6 m looking 3 m ahead
            var flat = doc.walkthrough_route_flat_m;
            if (flat == null || flat.Length < 6) { Check(false, "showcase-layout.json has walkthrough_route_flat_m"); return; }
            var route = Enumerable.Range(0, flat.Length / 3).Select(i => S(flat[3 * i], flat[3 * i + 1], flat[3 * i + 2])).ToList();
            var frames = Path.Combine(Out, "walkthrough_frames"); Directory.CreateDirectory(frames); Directory.CreateDirectory(Path.Combine(Out, "walks"));
            cc = new GameObject("WalkProbe", typeof(CharacterController)).GetComponent<CharacterController>();
            cc.height = 1.75f; cc.radius = .3f; cc.center = Vector3.up * .875f; cc.stepOffset = .3f; cc.slopeLimit = 45; cc.skinWidth = .02f;
            cc.enabled = false; cc.transform.position = route[0] + Vector3.up * 4; cc.enabled = true; Physics.SyncTransforms();
            for (int i = 0; i < 200; i++) cc.Move(Vector3.down * .05f);
            const int W = 1280, H = 720; var rt = new RenderTexture(W, H, 24, RenderTextureFormat.ARGB32) { antiAliasing = 4 }; var tex = new Texture2D(W, H, TextureFormat.RGB24, false);
            cam.fieldOfView = 62; int frame = 0, leg = 1, stuck = 0; Vector3 look = route[1] - route[0]; look.y = 0; look.Normalize(); float lowest = 99, highest = -99; bool reached = true;
            while (leg < route.Count && frame < 2400)
            {
                var goal = route[leg]; var d = goal - cc.transform.position; d.y = 0;
                if (d.magnitude < .2f) { leg++; continue; }
                var before = cc.transform.position;
                for (int k = 0; k < 2; k++) cc.Move(d.normalized * .03f + Vector3.down * .06f);
                if ((cc.transform.position - before).magnitude < .005f) { if (++stuck > 60) { reached = false; break; } } else stuck = 0;
                var p = cc.transform.position; lowest = Mathf.Min(lowest, p.y - (route[Mathf.Min(leg, route.Count - 1)].y)); highest = Mathf.Max(highest, p.y);
                // look ahead along the route, eased so the head turns smoothly through the bends
                var ahead = route[Mathf.Min(leg + 4, route.Count - 1)] - p; ahead.y = 0; if (ahead.sqrMagnitude > .01f) look = Vector3.Slerp(look, ahead.normalized, .06f);
                cam.transform.position = p + Vector3.up * 1.6f; cam.transform.rotation = Quaternion.LookRotation(look + Vector3.down * .12f);
                cam.targetTexture = rt; cam.Render(); RenderTexture.active = rt; tex.ReadPixels(new Rect(0, 0, W, H), 0, 0); tex.Apply();
                File.WriteAllBytes(Path.Combine(frames, $"frame_{frame:D5}.jpg"), tex.EncodeToJPG(92)); frame++;
            }
            RenderTexture.active = null; cam.targetTexture = null; rt.Release(); UnityEngine.Object.DestroyImmediate(tex);
            var end = cc.transform.position; float wantEnd = 4 + 0;
            Check(reached && leg >= route.Count && Mathf.Abs(end.y - (wantEnd)) < .15f,
                $"showcase walkthrough: a 1.75 m CharacterController walks row 2, climbs the stair, follows row 3 through both 30 degree bends to the right end: {(reached && leg >= route.Count ? "reached" : $"STUCK at leg {leg} of {route.Count}")} ({end.x:F2}, {end.y:F2}, {end.z:F2}), {frame} frames");
            File.WriteAllText(Path.Combine(Out, "walkthrough.json"), $"{{\"frames\":{frame},\"fps\":30,\"size\":[{W},{H}],\"reached\":{(reached && leg >= route.Count ? "true" : "false")},\"waypoints\":{route.Count},\"end\":[{end.x:F3},{end.y:F3},{end.z:F3}]}}");
            UnityEngine.Object.DestroyImmediate(cc.gameObject);
        }

        static Bounds LodBounds(GameObject go, string suffix = "_LOD0")
        {
            var rs = go.GetComponentsInChildren<Renderer>(true).Where(r => r.name.EndsWith(suffix)).ToArray();
            var b = rs[0].bounds; foreach (var r in rs) b.Encapsulate(r.bounds); return b;
        }

        static void Verify(string id, GameObject go)
        {
            var info = JsonUtility.FromJson<ModelInfo>(File.ReadAllText(Path.Combine(Exports, id, "model_info.json")));
            var b = LodBounds(go); var o = go.transform.position;
            float[] want = info.dimensions_m; Vector3 size = b.size;
            float dx = Mathf.Abs(size.x - want[0]), dy = Mathf.Abs(size.z - want[1]), dz = Mathf.Abs(size.y - want[2]);
            Check(dx < .002f && dy < .002f && dz < .002f, $"{id}: imported size {size.x:F3} x {size.z:F3} x {size.y:F3} m matches model_info (max error {Mathf.Max(dx, dy, dz) * 1000:F1} mm)");
            var lo = b.min - o; var hi = b.max - o;
            float e = Mathf.Max(Mathf.Abs(lo.x - info.bounds_min_m[0]), Mathf.Abs(lo.z - info.bounds_min_m[1]), Mathf.Abs(lo.y - info.bounds_min_m[2]),
                                Mathf.Abs(hi.x - info.bounds_max_m[0]), Mathf.Abs(hi.z - info.bounds_max_m[1]), Mathf.Abs(hi.y - info.bounds_max_m[2]));
            Check(e < .002f, $"{id}: bounds about the origin {lo.x:F3}..{hi.x:F3}, {lo.z:F3}..{hi.z:F3}, {lo.y:F3}..{hi.y:F3} m equal model_info (origin as designed, max error {e * 1000:F1} mm)");
            Check(Mathf.Abs(lo.y) < .002f, $"{id}: base on the origin height (min y {lo.y:F4})");
            Report.Add($"INFO {id}: minTier {info.minTier}");
            var lod = go.GetComponent<LODGroup>();
            Check(lod != null && lod.GetLODs().Length == 3, $"{id}: LODGroup with 3 levels");
            int tri(string s) => go.GetComponentsInChildren<MeshFilter>(true).Where(m => m.name.EndsWith(s)).Sum(m => m.sharedMesh.triangles.Length / 3);
            Check(tri("_LOD0") == info.lod_totals.LOD0 && tri("_LOD1") == info.lod_totals.LOD1 && tri("_LOD2") == info.lod_totals.LOD2,
                  $"{id}: imported LOD triangles {tri("_LOD0")}/{tri("_LOD1")}/{tri("_LOD2")} equal model_info {info.lod_totals.LOD0}/{info.lod_totals.LOD1}/{info.lod_totals.LOD2}");
            var col = go.GetComponentsInChildren<MeshCollider>(true).FirstOrDefault(c => c.name == id + "_Collision");
            Check(col != null && col.sharedMesh.triangles.Length > 0, $"{id}: {id}_Collision imported as MeshCollider ({(col ? col.sharedMesh.triangles.Length / 3 : 0)} triangles), renderer hidden");
            if (col != null)
            {
                var box = col.bounds; var all = b; all.Expand(.1f);
                Check(all.Contains(box.min) && all.Contains(box.max), $"{id}: the collider stays on the model");
            }
            Check(!go.GetComponentsInChildren<Renderer>(true).Any(r => r.enabled && r.sharedMaterial != null && r.sharedMaterial.shader.name.Contains("Error")), $"{id}: no error shaders");
        }

        static void Wind(string id, GameObject go)
        {
            foreach (var mf in go.GetComponentsInChildren<MeshFilter>(true).Where(m => m.name.Contains("_LOD")))
            {
                var c = mf.sharedMesh.colors;
                Check(c.Length == mf.sharedMesh.vertexCount, $"{mf.name}: vertex colour Wind on every vertex ({c.Length} of {mf.sharedMesh.vertexCount})");
                if (c.Length == 0) continue;
                Report.Add($"INFO {mf.name}: wind R {c.Min(x => x.r):F2}..{c.Max(x => x.r):F2}, phase G {c.Min(x => x.g):F2}..{c.Max(x => x.g):F2}, height B {c.Min(x => x.b):F2}..{c.Max(x => x.b):F2}");
            }
            var root = go.GetComponentsInChildren<MeshFilter>(true).First(m => m.name == id + "_LOD0").sharedMesh.colors;
            var leaves = go.GetComponentsInChildren<MeshFilter>(true).First(m => m.name == id + "_Leaves_LOD0").sharedMesh.colors;
            Check(root.Min(x => x.r) < .02f && leaves.Max(x => x.r) > .95f, $"{id}: wind weight 0 at the root, 1 on the outer leaves (linear, not sRGB-shifted)");
            var leafMat = go.GetComponentsInChildren<Renderer>(true).First(r => r.name == id + "_Leaves_LOD0").sharedMaterial;
            Check(leafMat.IsKeywordEnabled("_ALPHATEST_ON") && leafMat.GetFloat("_Cull") == 0, $"{id}: leaf cards alpha clipped, both faces");
        }

        static void Sockets(string id, GameObject go)
        {
            var info = File.ReadAllText(Path.Combine(Exports, id, "model_info.json"));
            int n = 0, good = 0;
            foreach (var t in go.GetComponentsInChildren<Transform>(true).Where(t => t.name.StartsWith("Socket_")))
            {
                n++;
                var key = "\"" + t.name.Split('.')[0] + "\": [";
                int at = info.IndexOf(key, info.IndexOf("sockets_blender_xyz")); if (at < 0) continue;
                var nums = info.Substring(at + key.Length, info.IndexOf(']', at) - at - key.Length).Split(',').Select(s => float.Parse(s.Trim(), System.Globalization.CultureInfo.InvariantCulture)).ToArray();
                if ((t.position - go.transform.position - U(nums[0], nums[1], nums[2])).magnitude < .002f) good++;
            }
            if (n > 0) Check(good == n, $"{id}: {good} of {n} sockets where model_info puts them");
        }

        // The joints: rays straight down onto the LOD0 render meshes just either side of every connector plane; heights must agree within 2 mm and nothing may fall through.
        static void Seams(List<(Placement p, GameObject go)> placed, int rows)
        {
            var added = new List<MeshCollider>();
            // every TE01 LOD0 render mesh except the single models at x >= 190: the sample, the 90 degree bends, the gentle chain, the height rows
            foreach (var mf in UnityEngine.Object.FindObjectsByType<MeshFilter>(FindObjectsSortMode.None).Where(m => m.name.StartsWith("TE01") && m.name.EndsWith("_LOD0") && m.transform.position.x < 190 && m.GetComponent<MeshCollider>() == null))
            { var c = mf.gameObject.AddComponent<MeshCollider>(); c.sharedMesh = mf.sharedMesh; mf.gameObject.layer = SeamLayer; added.Add(c); }
            Physics.SyncTransforms();
            int mask = 1 << SeamLayer;
            float? Z(float x, float y) => Physics.Raycast(new Vector3(x, 30, y), Vector3.down, out var h, 60, mask) ? h.point.y : (float?)null;
            float worst = 0; int holes = 0, n = 0; var lines = new List<string>();
            int off = 0;
            // a connector line: front corner (Blender x, y) and wall heading in degrees; samples across the path, up the ridge and into the ditch
            void JointAt(string what, Vector2 corner, float heading, float soil, float maxD = 4)
            {
                var t = Rot(Vector2.right, heading); var nrm = new Vector2(-t.y, t.x);
                foreach (var d in new[] { .8f, 1.3f, 1.8f, 2.3f, 2.6f, 2.95f, 3.3f, 3.6f, 3.74f, 3.85f })
                {
                    if (d > maxD) continue;
                    var q = corner + nrm * d; var pa = q - t * .003f; var pb = q + t * .003f;
                    var a = Z(pa.x, pa.y); var b = Z(pb.x, pb.y); var m = Z(q.x, q.y); n++;
                    if (a == null || b == null || m == null) { holes++; lines.Add($"{what} d {d:F2}: hole"); continue; }
                    float diff = Mathf.Abs(a.Value - b.Value); worst = Mathf.Max(worst, diff);
                    float want = soil + Profile(d);
                    if (Mathf.Abs(m.Value - want) > .03f) off++;
                    if (diff > .002f || Mathf.Abs(m.Value - want) > .03f) lines.Add($"{what} d {d:F2}: {a:F4} | {b:F4} (centre {m:F4}, profile {want:F4})");
                }
            }
            void Joint(string what, float x, float y0, float soil) => JointAt(what, new Vector2(x, y0), 0, soil);
            for (int k = 0; k < rows; k++) foreach (var x in new[] { -12f, -4f, 4f, 12f }) Joint($"row {k} x {x}", x, Front(k), k + 1);
            Joint("straight to outer bend", 104, -2, 1); Joint("straight to inner bend", 104, -32, 1);
            int nLines = rows * 4 + 2;
            // the gentle chain, both rows: every joint, the turned ones across the 30 degree connector
            for (int r = 0; r < 2; r++)
                for (int i = 1; i < chain.Count; i++)
                {
                    var prev = chain[i - 1]; var corner = prev.origin + Rot(Local(prev.kind, 8, 0), prev.yaw) + new Vector2(0, 4 * r);
                    float heading = prev.yaw + (prev.kind == "outer" ? 30 : prev.kind == "inner" ? -30 : 0);
                    JointAt($"gentle row {r}: {prev.id} | {chain[i].id}", corner, heading, r + 1, r == 0 && Mathf.Abs(heading) > 1 ? 3.35f : 4); nLines++;
                }
            // the height rows (rise 0.8, 1.0, 1.2): the joints inside each row
            for (int i = 1; i < heights.Count; i++)
                if (heights[i].row == heights[i - 1].row) { var h = heights[i - 1]; JointAt($"height row {h.row} (rise {h.rise}): {h.l.id} | {heights[i].l.id}", h.l.origin + new Vector2(4, -2), 0, h.z + h.rise); nLines++; }
            Check(holes == 0 && worst <= .002f, $"joints: {n} ray pairs across {nLines} connector lines, largest step {worst * 1000:F2} mm (limit 2), {holes} holes");
            Check(off == 0, $"joints: the soil at every sample follows the v002 profile (path, ridge +0.18 m, ditch -0.12 m) within 3 cm ({off} off)");
            foreach (var l in lines.Take(30)) Report.Add("  " + l);
            foreach (var c in added) UnityEngine.Object.DestroyImmediate(c);
            foreach (var go in UnityEngine.Object.FindObjectsByType<MeshFilter>(FindObjectsSortMode.None).Where(m => m.gameObject.layer == SeamLayer)) go.gameObject.layer = 0;
            Physics.SyncTransforms();
        }

        struct WalkResult { public bool reached; public float low, high, fall, rise; public Vector3 end; public string touch; }

        static WalkResult Walk(string what, float expectLow, float expectHigh, params Vector3[] path) => Walk(what, expectLow, expectHigh, true, path);

        static WalkResult Walk(string what, float expectLow, float expectHigh, bool mustReach, params Vector3[] path)
        {
            cc.enabled = false; cc.transform.position = path[0] + Vector3.up * .9f; cc.enabled = true; Physics.SyncTransforms();
            for (int i = 0; i < 80; i++) cc.Move(Vector3.down * .05f);
            var r = new WalkResult { reached = true, low = cc.transform.position.y, high = cc.transform.position.y, touch = "none" };
            var trace = new List<string>(); var along = new List<Vector2>(); float run = 0; var last = cc.transform.position;
            for (int leg = 1; leg < path.Length && r.reached; leg++)
            {
                var goal = path[leg]; int steps = 0;
                while (true)
                {
                    var d = goal - cc.transform.position; d.y = 0;
                    if (d.magnitude < .12f) break;
                    if (++steps > 3000) { r.reached = false; break; }
                    var flags = cc.Move(d.normalized * .035f + Vector3.down * .06f); var p = cc.transform.position;
                    r.low = Mathf.Min(r.low, p.y); r.high = Mathf.Max(r.high, p.y);
                    run += new Vector2(p.x - last.x, p.z - last.z).magnitude; last = p; along.Add(new Vector2(run, p.y));
                    if (steps % 4 == 0) trace.Add($"[{p.x:F3},{p.y:F3},{p.z:F3},{(int)flags}]");
                }
            }
            r.end = cc.transform.position;
            // no falling and no climbing walls: within any 0.3 m of horizontal travel the feet may not drop more than 0.25 m or rise more than stepOffset (a riser is 0.167; a collapse bank reaches ~41 deg)
            for (int i = 0, j = 0; i < along.Count; i++)
            {
                while (j < along.Count && along[j].x - along[i].x <= .3f) j++;
                for (int k = i + 1; k < j; k++) { float dy = along[k].y - along[i].y; r.fall = Mathf.Max(r.fall, -dy); r.rise = Mathf.Max(r.rise, dy); }
            }
            File.WriteAllText(Path.Combine(Out, "walks", $"walk-{what.Replace(" ", "_").Replace(",", "").Replace("/", "-")}.json"),
                $"{{\"walk\":\"{what}\",\"reached\":{(r.reached ? "true" : "false")},\"feet_low\":{r.low:F4},\"feet_high\":{r.high:F4},\"radius\":{cc.radius},\"height\":{cc.height},\"stepOffset\":{cc.stepOffset},\"slopeLimit\":{cc.slopeLimit},\"largest_drop_per_0_3m\":{r.fall:F4},\"largest_rise_per_0_3m\":{r.rise:F4},\"trace\":[{string.Join(",", trace)}]}}");
            if (mustReach) Check(r.reached && r.low >= expectLow && r.high <= expectHigh && r.fall <= .25f && r.rise <= cc.stepOffset,
                $"walk {what}: {(r.reached ? "reached" : "STUCK at")} ({r.end.x:F2}, {r.end.y:F2}, {r.end.z:F2}), feet {r.low:F3}..{r.high:F3} m (expected {expectLow:F2}..{expectHigh:F2}), largest drop {r.fall:F3} / rise {r.rise:F3} m per 0.3 m (limits drop 0.25, rise = stepOffset {cc.stepOffset:F2})");
            return r;
        }

        static void Walks(Assembly asm, List<(Placement p, GameObject go)> placed)
        {
            Directory.CreateDirectory(Path.Combine(Out, "walks"));
            cc = new GameObject("WalkProbe", typeof(CharacterController)).GetComponent<CharacterController>();
            cc.height = 1.75f; cc.radius = .3f; cc.center = Vector3.up * .875f; cc.stepOffset = .3f; cc.slopeLimit = 45; cc.skinWidth = .02f;
            Vector3 P(float x, int row, float d) => U(x, Front(row) + d, 0);
            Vector3 At(float x, int row, float d) { var v = P(x, row, d); v.y = row + 1; return v; }
            // 1. along the path line of three rows, end to end across both inner joints (x -4 and 4) and the outer ones (x -12, 12)
            foreach (var row in new[] { 1, 4, 7 })
            {
                bool breach = asm.pieces.Any(p => p.row == row && p.id == "TE01_Broken");
                Walk($"row {row} along the path line x -13 to 13{(breach ? " (through the slumped breach)" : "")}", row + (breach ? .3f : .97f), row + 1.12f, At(-13, row, 1.15f), At(13, row, 1.15f));
            }
            // 2. between the path and the bushes, across a breach and its slumped bank
            Walk("row 3 at d 1.9 through the breach of the left Broken piece", 3 + .4f, 3 + 1.12f, At(-13, 3, 1.9f), At(-3, 3, 1.9f));
            // 3. the whole hill: every stair in turn, from row 0 to row 8
            var stairs = asm.pieces.Where(p => p.id == "TE03_Stair").OrderBy(p => p.row).ToArray();
            var route = new List<Vector3> { U(stairs[0].position_m[0] + 2, -21.4f, 0), U(stairs[0].position_m[0], -21.4f, 0) };
            foreach (var s in stairs) { if (s.row > 0) route.Add(At(s.position_m[0], s.row - 1, 1.15f)); route.Add(At(s.position_m[0], s.row, 1.15f)); }
            var climb = Walk($"front strip to row 8 up all {stairs.Length} stairs", -.03f, 9.12f, route.ToArray());
            Check(Mathf.Abs(climb.end.y - 9f) < .1f, $"the climb ends on row 8 soil ({climb.end.y:F2} m, soil 9.00)");
            foreach (var s in stairs.Skip(1).Take(3))
                Walk($"down the stair into row {s.row}", s.row - .03f, s.row + 1.12f, At(s.position_m[0], s.row, 1.2f), At(s.position_m[0], s.row - 1, .9f));
            // 4. the ends: row 0 runs down to the strip at both sides (the left one mirrored), row 5 runs down to row 4's level
            Walk("row 0 right End down to the ground", -.03f, 1.12f, At(13, 0, 2), U(21.5f, Front(0) + 2, 0));
            Walk("row 0 left End (mirrored) down to the ground", -.03f, 1.12f, At(-13, 0, 2), U(-21.5f, Front(0) + 2, 0));
            var e5 = Walk("row 5 right End to its low tip", 4.97f, 6.12f, At(13, 5, 2), new Vector3(19.7f, 0, Front(5) + 2));
            Check(e5.end.y < 5.15f, $"row 5 End tip comes down to {e5.end.y:F2} m (row 4 soil 5.00)");
            // 5. stepping stones on row 0, end to end
            foreach (var s in asm.pieces.Where(p => p.id == "TE03_Stepping"))
                Walk($"over the stepping stones at x {s.position_m[0]}", .97f, 1.15f, At(s.position_m[0] - 1.3f, 0, 1.15f), At(s.position_m[0] + 1.3f, 0, 1.15f));
            // 6. a bush stops the walker: from the path straight at the trunk
            var bush = asm.pieces.First(p => p.id.StartsWith("TE02") && p.row == 2);
            var bc = U(bush.position_m[0], bush.position_m[1], bush.position_m[2] + 0);
            var hit = Walk($"from the path into a {bush.id}", 2.97f, 3.12f, false, At(bush.position_m[0], 2, 1.15f), bc);
            var gap = Vector2.Distance(new Vector2(hit.end.x, hit.end.z), new Vector2(bc.x, bc.z));
            Check(!hit.reached && gap > .6f && gap < .8f && hit.high < 3.12f, $"{bush.id}: the walker stops {gap:F2} m from the trunk (collision radius 0.42 + capsule 0.30), feet never above {hit.high:F3} m");
            // 7. bends: along the tread centre line round both quarter circles, from the straight
            var outer = new List<Vector3> { U(97, 0, 1) }; var inner = new List<Vector3> { U(97, -30, 1) };
            for (int i = 0; i <= 9; i++)
            {
                float a = -Mathf.PI / 2 + i * Mathf.PI / 18; outer.Add(U(104 + 6 * Mathf.Cos(a), 6 + 6 * Mathf.Sin(a), 1));
                float b = Mathf.PI / 2 - i * Mathf.PI / 18; inner.Add(U(104 + 6 * Mathf.Cos(b), -36 + 6 * Mathf.Sin(b), 1));
            }
            Walk("straight into the outer bend and round it", .97f, 1.12f, outer.ToArray());
            Walk("straight into the inner bend and round it", .97f, 1.12f, inner.ToArray());
            GentleAndHeightWalks();
            UnityEngine.Object.DestroyImmediate(cc.gameObject);
        }

        static void Lighting()
        {
            RenderSettings.ambientMode = AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = new Color(.62f, .68f, .7f); RenderSettings.ambientEquatorColor = new Color(.45f, .44f, .38f); RenderSettings.ambientGroundColor = new Color(.2f, .18f, .14f);
            var sun = new GameObject("Sun").AddComponent<Light>(); sun.type = LightType.Directional; sun.intensity = 1.25f;
            sun.color = new Color(1, .96f, .88f); sun.transform.rotation = Quaternion.Euler(38, -30, 0); sun.shadows = LightShadows.Soft;
            var cam = new GameObject("Main Camera", typeof(Camera)).GetComponent<Camera>(); cam.tag = "MainCamera"; cam.nearClipPlane = .05f; cam.farClipPlane = 300;
            cam.clearFlags = CameraClearFlags.SolidColor; cam.backgroundColor = new Color(.74f, .82f, .84f);
            cam.GetUniversalAdditionalCameraData().renderPostProcessing = false;
        }

        static void Shot(string file, Vector3 target, Vector3 eye, float fov = 40)
        {
            var cam = Camera.main; var rt = new RenderTexture(1600, 900, 24, RenderTextureFormat.ARGB32) { antiAliasing = 4 };
            cam.transform.position = eye; cam.transform.LookAt(target); cam.fieldOfView = fov; cam.targetTexture = rt; cam.Render();
            RenderTexture.active = rt; var tex = new Texture2D(1600, 900, TextureFormat.RGB24, false); tex.ReadPixels(new Rect(0, 0, 1600, 900), 0, 0); tex.Apply();
            File.WriteAllBytes(Path.Combine(Out, file + ".png"), tex.EncodeToPNG()); UnityEngine.Object.DestroyImmediate(tex);
            RenderTexture.active = null; cam.targetTexture = null; rt.Release(); Report.Add("SHOT " + file);
        }

        static void Capture(List<(Placement p, GameObject go)> placed, Dictionary<string, GameObject> single, List<GameObject> bend)
        {
            foreach (var kv in single)
            {
                var b = LodBounds(kv.Value); float d = Mathf.Max(b.size.magnitude * 1.25f, 2.2f); var c = b.center;
                Shot(kv.Key + "_three_quarter", c, c + new Vector3(.7f, .45f, -.85f).normalized * d, 35);
                Shot(kv.Key + "_front", c, c + new Vector3(0, .12f, -1) * d, 35);
            }
            // the sample
            Shot("assembly_aerial", new Vector3(0, 3, -2), new Vector3(24, 34, -46), 45);
            Shot("assembly_walk_row2", At2(4, 2, 2.6f, 2.9f), At2(-11.5f, 2, 1.15f, 3 + 1.6f), 60);
            Shot("assembly_stairs_from_row1", At2(-1.5f, 3, 1f, 4.4f), At2(-6.5f, 1, 1.0f, 2 + 1.6f), 55);
            Shot("assembly_joint_x-4_row3_wall", U(-4, Front(3) + .1f, 3.5f), U(-3.2f, Front(3) - 2.2f, 3 + 1.5f), 50);
            Shot("assembly_left_end_mirrored", U(-16, Front(1) + 2, 1.6f), U(-23, Front(1) - 5, 4.5f), 50);
            Shot("assembly_breach_row1", U(2, Front(1) + 1, 1.6f), U(3.5f, Front(1) - 3.2f, 1 + 1.6f), 55);
            Shot("assembly_bushes_close", At2(-6, 4, 2.95f, 5.4f), At2(-8.5f, 4, .9f, 5 + 1.6f), 50);
            Shot("bends_outer", U(104, 2, 1), U(96, -10, 7), 50);
            Shot("bends_inner", U(104, -32, 1), U(96, -42, 7), 50);
            Flicker();
        }

        static Vector3 At2(float x, int row, float d, float h) => U(x, Front(row) + d, h);

        // A surface fighting another one flips colour and back as the camera turns a hair: count pixels that go A, B, A over three frames.
        static void Flicker()
        {
            const int W = 960, H = 540, Frames = 20;
            var cam = Camera.main; var rt = new RenderTexture(W, H, 24, RenderTextureFormat.ARGB32); var tex = new Texture2D(W, H, TextureFormat.RGB24, false);
            foreach (var (name, target, eye) in new[] { ("row 3 wall at the x -4 joint", U(-4, Front(3) + .1f, 3.5f), U(-3.2f, Front(3) - 2.2f, 4.5f)), ("stair into row 2", U(5.5f, Front(2) - 1, 2.4f), U(8, Front(2) - 4, 3.4f)), ("bush row 4", At2(-6, 4, 2.95f, 5.4f), At2(-8.5f, 4, .9f, 6.6f)) })
            {
                var look = new float[Frames][]; var off = eye - target;
                for (int i = 0; i < Frames; i++)
                {
                    cam.transform.position = target + Quaternion.Euler(0, i * .1f, 0) * off; cam.transform.LookAt(target); cam.fieldOfView = 45; cam.targetTexture = rt; cam.Render();
                    RenderTexture.active = rt; tex.ReadPixels(new Rect(0, 0, W, H), 0, 0); tex.Apply(); look[i] = tex.GetPixels().Select(c => c.r * .2126f + c.g * .7152f + c.b * .0722f).ToArray();
                }
                RenderTexture.active = null; cam.targetTexture = null; int worst = 0, all = 0;
                for (int i = 0; i + 2 < Frames; i++)
                {
                    int n = 0;
                    for (int k = 0; k < look[i].Length; k++) if (Mathf.Abs(look[i][k] - look[i + 1][k]) > .2f && Mathf.Abs(look[i][k] - look[i + 2][k]) < .05f) n++;
                    worst = Mathf.Max(worst, n); all += n;
                }
                Report.Add($"FLICKER {name}: A-B-A pixels per frame mean {all / (float)(Frames - 2):0.0}, worst {worst}, of {W * H}");
            }
            UnityEngine.Object.DestroyImmediate(tex); rt.Release();
        }
    }
}
