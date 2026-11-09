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
    // Work pack 2026-11-08 (B-40h): FP01-FP05 forest dirt path kit, exported into art/exports/forest-paths-b.
    // Imports each piece into a gitignored folder and checks it against its model_info.json (size, LOD triangles, collider, sockets), then
    // chains the 40 m sample in the order of FP_Assembly_40m/assembly_walk.json (each piece's Socket_Path_W on the previous piece's
    // Socket_Path_E, facing back into it: the same rule as assemble_40m.py), checks every joint of the chained colliders for a step, and
    // walks the chain with a CharacterController set up like the game's player (ProjectBuilder: height 2 m, radius 0.35 m, default step
    // offset 0.3 m and slope limit 45 deg) on three lines (0.24 m left of, on and 0.24 m right of the centre line), steering along each
    // piece's centre line from socket to socket. URP captures. Writes artifacts/forest-paths-unity/.
    // Editor batch check only: nothing is placed in the main scene and nothing is played.
    // Run with -executeMethod YunJing.Editor.ForestPathsModelCheck.Run (the environment variable FP_EXPORTS overrides where the exports are read).
    public static class ForestPathsModelCheck
    {
        const string Root = "Assets/YunJing/Generated/ForestPathsB";
        static string Repo => Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", ".."));
        static string Exports { get { var e = Environment.GetEnvironmentVariable("FP_EXPORTS"); return string.IsNullOrEmpty(e) ? Path.Combine(Repo, "art", "exports", "forest-paths-b") : e; } }
        static string Out => Path.Combine(Repo, "artifacts", "forest-paths-unity");
        static readonly List<string> Report = new List<string>();
        static int failed;
        const float Speed = 1.4f, Dt = 1f / 60f;

        [Serializable] class LodTotals { public int LOD0, LOD1, LOD2; }
        [Serializable] class ModelInfo { public string version, minTier; public float[] dimensions_m, bounds_min_m, bounds_max_m; public bool collision; public LodTotals lod_totals; public string[] detailObjects; }
        [Serializable] class Assembly { public string[] sequence; public float length_m, rise_m; }

        static readonly Dictionary<string, ModelInfo> infos = new Dictionary<string, ModelInfo>();
        static ModelInfo Info(string id)
        {
            if (!infos.TryGetValue(id, out var i)) infos[id] = i = JsonUtility.FromJson<ModelInfo>(File.ReadAllText(Path.Combine(Exports, id, "model_info.json")));
            return i;
        }
        static string Fbx(string id) => $"{Root}/{id}/{id}_{Info(id).version}.fbx";
        static void Check(bool ok, string what) { Report.Add((ok ? "PASS " : "FAIL ") + what); if (!ok) failed++; }

        public static void Run()
        {
            Report.Clear(); failed = 0; infos.Clear();
            var pipeline = AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>("Assets/YunJing/Generated/URP.asset");
            if (pipeline == null) { ProjectBuilder.Generate(); pipeline = AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>("Assets/YunJing/Generated/URP.asset"); }
            if (GraphicsSettings.defaultRenderPipeline != pipeline) GraphicsSettings.defaultRenderPipeline = pipeline;
            if (QualitySettings.renderPipeline != pipeline) QualitySettings.renderPipeline = pipeline;
            pipeline.shadowDistance = 80;
            if (Directory.Exists(Out)) Directory.Delete(Out, true);
            Directory.CreateDirectory(Out);

            var asm = JsonUtility.FromJson<Assembly>(File.ReadAllText(Path.Combine(Exports, "FP_Assembly_40m", "assembly_walk.json")));
            var ids = Directory.GetDirectories(Exports, "FP0*").Select(Path.GetFileName).Where(i => File.Exists(Path.Combine(Exports, i, "model_info.json"))).OrderBy(i => i).ToArray();
            Report.Add("INFO exports: " + Exports);
            Report.Add("INFO pieces: " + string.Join(", ", ids.Select(i => $"{i} {Info(i).version}")));
            foreach (var id in ids) Copy(id);
            AssetDatabase.Refresh();
            foreach (var id in ids) Configure(id);

            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            Lighting();
            // every piece on its own, side by side, for the import checks
            for (int n = 0; n < ids.Length; n++)
            {
                var go = Place(ids[n]); go.transform.position = new Vector3(-30 - n * 10, 0, -40);
                Verify(ids[n], go);
            }
            // the 40 m sample, chained socket to socket
            var chain = new List<GameObject>(); var route = new List<Vector3>(); var pieceAt = new List<int>(); var joints = new List<(Vector3 p, Vector3 t, string a, string b)>();
            Vector3 eP = Vector3.zero, eOut = Vector3.forward;
            for (int k = 0; k < asm.sequence.Length; k++)
            {
                var id = asm.sequence[k]; var go = Place(id); go.name = $"{k:00}_{id}";
                var (w, wOut, e, _) = Ends(go);
                if (k > 0)
                {
                    // turn about the vertical until W faces back into the previous piece, then put W on E
                    float yaw = Vector3.SignedAngle(Flat(wOut), -Flat(eOut), Vector3.up);
                    go.transform.rotation = Quaternion.AngleAxis(yaw, Vector3.up) * go.transform.rotation;
                    Physics.SyncTransforms();
                    go.transform.position += eP - Ends(go).w;
                    Physics.SyncTransforms();
                    joints.Add((eP, -Flat(eOut).normalized, asm.sequence[k - 1], id));
                }
                var ends = Ends(go); var cl = CentreLine(go);
                for (int s = k == 0 ? 0 : 1; s < cl.Count; s++) { route.Add(cl[s]); pieceAt.Add(k); }
                eP = ends.e; eOut = ends.eOut; chain.Add(go);
            }
            Physics.SyncTransforms();
            float length = 0; for (int i = 1; i < route.Count; i++) length += Vector3.Distance(Flat(route[i - 1]), Flat(route[i]));
            float rise = route[route.Count - 1].y - route[0].y;
            Check(Mathf.Abs(rise - asm.rise_m) < .02f && Mathf.Abs(length - asm.length_m) < .5f,
                  $"chained in Unity in the order {string.Join(" > ", asm.sequence)}: centre line {length:F2} m, rise {rise:F3} m (Blender assembly: {asm.length_m} m, {asm.rise_m} m)");
            Joints(joints);
            foreach (float off in new[] { -.24f, 0f, .24f }) Walk(route, pieceAt, asm.sequence, off);
            Shots(chain, route);

            File.WriteAllText(Path.Combine(Out, "unity-verify-report.txt"), string.Join("\n", Report) + $"\n\nUnity {Application.unityVersion}; failed checks: {failed}; editor batch check only, not placed in the main scene, not played\n");
            Debug.Log("FOREST_PATHS_" + (failed == 0 ? "PASS" : "FAIL") + "\n" + string.Join("\n", Report));
            if (failed > 0 && Application.isBatchMode) EditorApplication.Exit(1);
        }

        static Vector3 Flat(Vector3 v) => new Vector3(v.x, 0, v.z);

        // the two sockets and the horizontal direction each one points out of the piece (the socket axis closest to the way out)
        static (Vector3 w, Vector3 wOut, Vector3 e, Vector3 eOut) Ends(GameObject go)
        {
            var ts = go.GetComponentsInChildren<Transform>(true);
            var W = ts.First(t => t.name.StartsWith("Socket_Path_W")); var E = ts.First(t => t.name.StartsWith("Socket_Path_E"));
            Vector3 guessW = Flat(W.position - E.position).normalized, guessE = -guessW;
            Vector3 Axis(Transform t, Vector3 guess) => new[] { t.forward, -t.forward, t.right, -t.right, t.up, -t.up }.Select(Flat).OrderByDescending(d => Vector3.Dot(d.normalized, guess)).First().normalized;
            return (W.position, Axis(W, guessW), E.position, Axis(E, guessE));
        }

        // the centre line from W to E every 5 cm: a cubic Bezier with the sockets' end tangents (a circular arc for the curves, a straight
        // line for the rest), height straight from W to E (the slope and the steps run straight)
        static List<Vector3> CentreLine(GameObject go)
        {
            var ends = Ends(go);
            Vector3 t0 = -Flat(ends.wOut).normalized, t1 = Flat(ends.eOut).normalized;
            Vector3 a = Flat(ends.w), b = Flat(ends.e); float chord = (b - a).magnitude;
            float th = Vector3.Angle(t0, t1) * Mathf.Deg2Rad;
            float h = th < 1e-3f ? chord / 3 : 4f / 3f * Mathf.Tan(th / 4) * chord / (2 * Mathf.Sin(th / 2));
            Vector3 p1 = a + t0 * h, p2 = b - t1 * h;
            int seg = Mathf.CeilToInt(chord / .05f); var pts = new List<Vector3>();
            for (int s = 0; s <= seg; s++)
            {
                float u = s / (float)seg, v = 1 - u;
                var q = v * v * v * a + 3 * v * v * u * p1 + 3 * v * u * u * p2 + u * u * u * b;
                q.y = Mathf.Lerp(ends.w.y, ends.e.y, u); pts.Add(q);
            }
            return pts;
        }

        static void Copy(string id)
        {
            var src = Path.Combine(Exports, id); var dst = Path.Combine(Repo, "apps", "game", Root, id);
            Directory.CreateDirectory(Path.Combine(dst, "Textures"));
            foreach (var file in Directory.GetFiles(src, $"{id}_{Info(id).version}.fbx").Concat(Directory.GetFiles(Path.Combine(src, "Textures"), "*.png")))
                File.Copy(file, Path.Combine(dst, file.Substring(src.Length + 1)), true);
        }

        static void Configure(string id)
        {
            var importer = AssetImporter.GetAtPath(Fbx(id)) as ModelImporter;
            if (importer == null) throw new FileNotFoundException("FBX not imported", id);
            importer.bakeAxisConversion = true; importer.isReadable = true;
            importer.materialImportMode = ModelImporterMaterialImportMode.ImportViaMaterialDescription; importer.materialLocation = ModelImporterMaterialLocation.InPrefab;
            importer.importAnimation = false; importer.importCameras = false; importer.importLights = false; importer.addCollider = false;
            importer.importNormals = ModelImporterNormals.Import;
            importer.SaveAndReimport();
            foreach (var tex in Directory.GetFiles(Path.Combine(Repo, "apps", "game", Root, id, "Textures"), "*.png"))
            {
                var path = $"{Root}/{id}/Textures/{Path.GetFileName(tex)}";
                var ti = AssetImporter.GetAtPath(path) as TextureImporter; if (ti == null) continue;
                bool normal = path.EndsWith("_Normal.png"), data = path.EndsWith("_MetallicSmoothness.png") || path.EndsWith("_Roughness.png") || path.EndsWith("_Metallic.png");
                ti.textureType = normal ? TextureImporterType.NormalMap : TextureImporterType.Default;
                ti.sRGBTexture = !normal && !data; ti.maxTextureSize = 4096; ti.wrapMode = TextureWrapMode.Clamp;
                ti.SaveAndReimport();
            }
        }

        static Material Mat(string id)
        {
            var path = $"{Root}/{id}.mat";
            var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (mat == null) { mat = new Material(Shader.Find("Universal Render Pipeline/Lit")); AssetDatabase.CreateAsset(mat, path); }
            Texture2D T(string s) => AssetDatabase.LoadAssetAtPath<Texture2D>($"{Root}/{id}/Textures/{id}_{s}.png");
            mat.SetTexture("_BaseMap", T("BaseColor")); mat.SetColor("_BaseColor", Color.white);
            var n = T("Normal"); if (n != null) { mat.SetTexture("_BumpMap", n); mat.EnableKeyword("_NORMALMAP"); }
            var ms = T("MetallicSmoothness"); if (ms != null) { mat.SetTexture("_MetallicGlossMap", ms); mat.EnableKeyword("_METALLICSPECGLOSSMAP"); mat.SetFloat("_Smoothness", 1); }
            EditorUtility.SetDirty(mat); return mat;
        }

        static GameObject Place(string id)
        {
            var go = (GameObject)PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>(Fbx(id)));
            PrefabUtility.UnpackPrefabInstance(go, PrefabUnpackMode.Completely, InteractionMode.AutomatedAction);
            var mat = Mat(id);
            foreach (var r in go.GetComponentsInChildren<Renderer>(true))
            {
                if (r.name == id + "_Collision") { r.enabled = false; continue; }
                r.sharedMaterials = Enumerable.Repeat(mat, r.sharedMaterials.Length).ToArray();
            }
            var cut = new[] { .1f, .035f, .006f };
            var group = go.GetComponent<LODGroup>(); if (group == null) group = go.AddComponent<LODGroup>();
            group.SetLODs(Enumerable.Range(0, 3).Select(i => new LOD(cut[i], go.GetComponentsInChildren<Renderer>(true).Where(r => r.name.EndsWith("_LOD" + i)).ToArray())).ToArray());
            var col = go.GetComponentsInChildren<MeshFilter>(true).FirstOrDefault(m => m.name == id + "_Collision");
            if (col != null) col.gameObject.AddComponent<MeshCollider>().sharedMesh = col.sharedMesh;
            return go;
        }

        static void Verify(string id, GameObject go)
        {
            var info = Info(id); var o = go.transform.position;
            var rs = go.GetComponentsInChildren<Renderer>(true).Where(r => r.name.EndsWith("_LOD0")).ToArray();
            var b = rs[0].bounds; foreach (var r in rs) b.Encapsulate(r.bounds);
            float[] want = info.dimensions_m; var size = b.size;
            float err = Mathf.Max(Mathf.Abs(size.x - want[0]), Mathf.Abs(size.z - want[1]), Mathf.Abs(size.y - want[2]));
            Check(err < .002f, $"{id}: imported LOD0 size {size.x:F3} x {size.z:F3} x {size.y:F3} m matches model_info (max error {err * 1000:F1} mm)");
            var mfs = go.GetComponentsInChildren<MeshFilter>(true);
            int tri(string s) => mfs.Where(m => m.name.EndsWith(s)).Sum(m => m.sharedMesh.triangles.Length / 3);
            if (info.lod_totals != null && info.lod_totals.LOD0 > 0)
                Check(tri("_LOD0") == info.lod_totals.LOD0 && tri("_LOD1") == info.lod_totals.LOD1 && tri("_LOD2") == info.lod_totals.LOD2,
                      $"{id}: imported LOD triangles {tri("_LOD0")}/{tri("_LOD1")}/{tri("_LOD2")} equal model_info {info.lod_totals.LOD0}/{info.lod_totals.LOD1}/{info.lod_totals.LOD2}");
            var lod = go.GetComponent<LODGroup>();
            Check(lod.GetLODs().All(l => l.renderers.Length > 0), $"{id}: LODGroup with 3 filled levels");
            foreach (var d in info.detailObjects ?? new string[0])
                Check(Enumerable.Range(0, 3).All(i => mfs.Any(m => m.name == $"{d}_LOD{i}")), $"{id}: {d} present at LOD0/1/2 as its own object (can be switched off)");
            var col = go.GetComponentsInChildren<MeshCollider>(true).FirstOrDefault(c => c.name == id + "_Collision");
            Check(info.collision && col != null && col.sharedMesh.triangles.Length > 0, $"{id}: {id}_Collision imported as MeshCollider ({(col ? col.sharedMesh.triangles.Length / 3 : 0)} triangles), renderer hidden");
            var (w, wOut, e, eOut) = Ends(go);
            Report.Add($"INFO {id}: Socket_Path_W at ({w.x - o.x:F3}, {w.z - o.z:F3}, {w.y - o.y:F3}), Socket_Path_E at ({e.x - o.x:F3}, {e.z - o.z:F3}, {e.y - o.y:F3}) m (Blender x, y, z); turn {Vector3.SignedAngle(-wOut, eOut, Vector3.up):F1} deg");
            // the collider is under the whole walking strip: rays down every 25 cm along the centre line, across +-0.6 m, all find it
            Physics.SyncTransforms();
            int miss = 0, rays = 0; var cl = CentreLine(go);
            for (int i = 2; i < cl.Count - 2; i += 5)
            {
                var side = Vector3.Cross(Vector3.up, Flat(cl[i + 1] - cl[i - 1])).normalized;
                foreach (float x in new[] { -.6f, -.3f, 0f, .3f, .6f })
                {
                    rays++; if (!Physics.Raycast(cl[i] + side * x + Vector3.up * 3, Vector3.down, out var hit, 8) || hit.collider != col) miss++;
                }
            }
            Check(miss == 0, $"{id}: rays down over the walking strip (every 25 cm along the centre line, across +-0.6 m) all land on its collider ({rays - miss}/{rays})");
        }

        // at each joint, the chained colliders meet without a step: heights 2 cm before and 2 cm after the joint, across +-0.6 m
        static void Joints(List<(Vector3 p, Vector3 t, string a, string b)> joints)
        {
            foreach (var j in joints)
            {
                var side = Vector3.Cross(Vector3.up, j.t).normalized; float worst = 0;
                foreach (float x in new[] { -.6f, -.3f, 0f, .3f, .6f })
                {
                    var c = j.p + side * x;
                    bool h1 = Physics.Raycast(c - j.t * .02f + Vector3.up * 3, Vector3.down, out var r1, 8), h2 = Physics.Raycast(c + j.t * .02f + Vector3.up * 3, Vector3.down, out var r2, 8);
                    worst = !(h1 && h2) ? 99 : Mathf.Max(worst, Mathf.Abs(r1.point.y - r2.point.y));
                }
                Check(worst <= .002f + .04f * Mathf.Tan(17 * Mathf.Deg2Rad), $"joint {j.a} > {j.b}: collider height 2 cm either side of the joint differs by {worst * 1000:F1} mm (at most the slope over 4 cm plus 2 mm)");
            }
        }

        static CharacterController Player()
        {
            // as ProjectBuilder sets up the game's player (height 2, radius 0.35, centre 1 m; step offset and slope limit left at Unity's 0.3 m / 45 deg)
            var p = new GameObject("Player_like_walker"); var cc = p.AddComponent<CharacterController>();
            cc.height = 2; cc.center = Vector3.up; cc.radius = .35f;
            return cc;
        }

        // walk the whole chain on a line `off` metres right of the centre line, steering 0.6 m ahead along it
        static void Walk(List<Vector3> route, List<int> pieceAt, string[] seq, float off)
        {
            var line = new List<Vector3>();
            for (int i = 0; i < route.Count; i++)
            {
                var t = Flat(route[Mathf.Min(i + 1, route.Count - 1)] - route[Mathf.Max(i - 1, 0)]).normalized;
                line.Add(route[i] + Vector3.Cross(Vector3.up, t) * off);
            }
            Physics.SyncTransforms(); var cc = Player();
            Physics.Raycast(line[0] + Vector3.up * 3, Vector3.down, out var g0, 8);
            cc.transform.position = g0.point + Vector3.up * .02f; Physics.SyncTransforms();
            int idx = 0, frames = 0, maxFrames = Mathf.CeilToInt(route.Count * .05f / Speed / Dt * 2.5f), stuck = 0, worstStuck = 0;
            float worstSide = 0, below = 0, above = 0, airborne = 0; string worstSideAt = "", aboveAt = "";
            var trace = new List<string>();
            while (frames++ < maxFrames)
            {
                var pos = cc.transform.position;
                int best = idx; float bd = 1e9f;
                for (int i = idx; i < Mathf.Min(idx + 40, line.Count); i++) { float d = (Flat(line[i]) - Flat(pos)).sqrMagnitude; if (d < bd) { bd = d; best = i; } }
                idx = best;
                if (idx >= line.Count - 2 && Mathf.Sqrt(bd) < .25f) break;
                var target = line[Mathf.Min(idx + 12, line.Count - 1)];
                var dir = Flat(target - pos).normalized;
                var before = Flat(pos);
                cc.Move(dir * Speed * Dt + Vector3.down * 9.8f * Dt);
                pos = cc.transform.position;
                stuck = (Flat(pos) - before).magnitude < Speed * Dt * .25f ? stuck + 1 : 0; worstStuck = Mathf.Max(worstStuck, stuck);
                if (Mathf.Sqrt(bd) > worstSide) { worstSide = Mathf.Sqrt(bd); worstSideAt = seq[pieceAt[idx]]; }
                if (!cc.isGrounded) airborne += Dt;
                if (Physics.Raycast(pos + Vector3.up * .5f, Vector3.down, out var hit, 3))
                {
                    float gap = pos.y - cc.skinWidth - hit.point.y;      // the controller keeps its skin width (0.08 m by default) off the ground
                    below = Mathf.Min(below, gap); if (gap > above) { above = gap; aboveAt = seq[pieceAt[idx]] + $" at ({pos.x:F2}, {pos.y:F3}, {pos.z:F2}), collider {hit.point.y:F3}, route idx {idx}/{line.Count}"; }
                }
                else below = -9;
                if (frames % 15 == 0) trace.Add($"[{pos.x:F3},{pos.y:F3},{pos.z:F3}]");
            }
            var end = cc.transform.position; var last = line[line.Count - 1];
            Physics.Raycast(line[line.Count - 3] + Vector3.up * 3, Vector3.down, out var gl, 8);
            float colliderRise = gl.point.y - g0.point.y;
            float endGap = (Flat(end) - Flat(last)).magnitude, rise = end.y - cc.skinWidth - g0.point.y;
            File.WriteAllText(Path.Combine(Out, $"walk-trace-{off:+0.00;-0.00;0.00}.json"), $"{{\"offset_m\":{off},\"radius\":{cc.radius},\"height\":{cc.height},\"stepOffset\":{cc.stepOffset},\"slopeLimit\":{cc.slopeLimit},\"seconds\":{frames * Dt:F2},\"trace\":[{string.Join(",", trace)}]}}");
            Check(endGap < .3f && Mathf.Abs(rise - colliderRise) < .02f && Mathf.Abs(colliderRise - (route[route.Count - 1].y - route[0].y)) < .02f,
                  $"walk on the line {off:+0.00;-0.00;0.00} m: the player-sized walker gets from the start of FP01 to the top of FP05 ({frames * Dt:F1} s, ends {endGap:F2} m from the last socket, feet rose {rise:F3} m; the collider under the line rises {colliderRise:F3} m)");
            Check(worstStuck * Dt < .5f, $"walk on the line {off:+0.00;-0.00;0.00} m: never held up (longest time almost not moving {worstStuck * Dt:F2} s)");
            Check(worstSide < .3f, $"walk on the line {off:+0.00;-0.00;0.00} m: stays on its line (furthest {worstSide:F2} m off it, at {worstSideAt})");
            Check(below > -.03f && above <= cc.stepOffset, $"walk on the line {off:+0.00;-0.00;0.00} m: feet (less the {cc.skinWidth:F2} m skin width) never sink into the collider (lowest {below * 1000:F0} mm) or hang over it by more than the {cc.stepOffset:F2} m step offset (highest {above:F3} m, {aboveAt}); not grounded {airborne:F2} s in all");
            UnityEngine.Object.DestroyImmediate(cc.gameObject);
        }

        static void Lighting()
        {
            RenderSettings.ambientMode = AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = new Color(.62f, .68f, .7f); RenderSettings.ambientEquatorColor = new Color(.45f, .44f, .38f); RenderSettings.ambientGroundColor = new Color(.2f, .18f, .14f);
            var sun = new GameObject("Sun").AddComponent<Light>(); sun.type = LightType.Directional; sun.intensity = 1.25f;
            sun.color = new Color(1, .96f, .88f); sun.transform.rotation = Quaternion.Euler(42, -30, 0); sun.shadows = LightShadows.Soft;
            var cam = new GameObject("Main Camera", typeof(Camera)).GetComponent<Camera>(); cam.tag = "MainCamera"; cam.nearClipPlane = .02f; cam.farClipPlane = 400;
            cam.clearFlags = CameraClearFlags.SolidColor; cam.backgroundColor = new Color(.74f, .82f, .84f);
            cam.GetUniversalAdditionalCameraData().renderPostProcessing = false;
        }

        static GameObject Figure(Vector3 feet)
        {
            var p = GameObject.CreatePrimitive(PrimitiveType.Capsule); p.name = "Player_size_2m";
            UnityEngine.Object.DestroyImmediate(p.GetComponent<Collider>());
            p.transform.localScale = new Vector3(.7f, 1f, .7f); p.transform.position = feet + Vector3.up;
            var m = new Material(Shader.Find("Universal Render Pipeline/Lit")); m.SetColor("_BaseColor", new Color(.85f, .85f, .85f)); p.GetComponent<Renderer>().sharedMaterial = m;
            return p;
        }

        static void Shots(List<GameObject> chain, List<Vector3> route)
        {
            var all = new Bounds(route[0], Vector3.zero); foreach (var q in route) all.Encapsulate(q);
            var figs = new List<GameObject>();
            foreach (float u in new[] { .12f, .35f, .55f, .8f, .97f })
            {
                var q = route[Mathf.RoundToInt(u * (route.Count - 1))];
                if (Physics.Raycast(q + Vector3.up * 3, Vector3.down, out var hit, 8)) figs.Add(Figure(hit.point));
            }
            var c = all.center; float d = all.size.magnitude * .85f;
            Shot("fp_chain_overview", c, c + new Vector3(-.55f, .75f, -.6f).normalized * d, 40);
            Shot("fp_chain_top", c, c + new Vector3(0, 1, -.05f).normalized * d * 1.05f, 40);
            foreach (var (name, u, back) in new[] { ("fp_root_crossing", .32f, 6f), ("fp_slope", .78f, 7f), ("fp_log_steps", .95f, 5.5f) })
            {
                int i = Mathf.RoundToInt(u * (route.Count - 1)); var q = route[i] + Vector3.up * .8f;
                var t = Flat(route[Mathf.Min(i + 5, route.Count - 1)] - route[Mathf.Max(i - 5, 0)]).normalized;
                Shot(name, q, q - t * back + Vector3.Cross(Vector3.up, t) * 2.2f + Vector3.up * 2.2f, 45);
            }
            foreach (var f in figs) UnityEngine.Object.DestroyImmediate(f);
        }

        static void Shot(string file, Vector3 target, Vector3 eye, float fov = 40)
        {
            var cam = Camera.main; var rt = new RenderTexture(1600, 900, 24, RenderTextureFormat.ARGB32) { antiAliasing = 4 };
            cam.transform.position = eye; cam.transform.LookAt(target); cam.fieldOfView = fov; cam.targetTexture = rt; cam.Render();
            RenderTexture.active = rt; var tex = new Texture2D(1600, 900, TextureFormat.RGB24, false); tex.ReadPixels(new Rect(0, 0, 1600, 900), 0, 0); tex.Apply();
            File.WriteAllBytes(Path.Combine(Out, file + ".png"), tex.EncodeToPNG()); UnityEngine.Object.DestroyImmediate(tex);
            RenderTexture.active = null; cam.targetTexture = null; rt.Release(); Report.Add("SHOT " + file);
        }
    }
}
