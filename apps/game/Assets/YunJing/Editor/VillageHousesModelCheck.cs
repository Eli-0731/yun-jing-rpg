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
    // Work pack 2026-11-07, part 2 (VL01-VL03 empty-house variants of the Dondon StarterHouse) and 2026-11-08 (VL04-VL05 lived-in variants), exported into art/exports/village-houses-b.
    // Imports each model into a gitignored folder, checks it against its model_info.json (size, origin, LOD levels and triangles, objects,
    // Detail_* objects, collider, four material slots: Main / Stone / Wood atlases and the roof-tile material, sockets), then walks a 1.75 m
    // CharacterController: up the three steps onto the porch and against the (closed) door; pushed at the back, left and right walls from
    // outside it stops outside; VL03: from outside the fallen right wall, up the rubble, stopped at the old wall line (nobody gets into the
    // room or stuck in the heap). VL04/VL05: walkers on the porch pushed at the drying rack, the bamboo chair and the bonsai stop at
    // their boxes in <ID>_Detail_Collision, and walk through once that collider is switched off with Detail_Small. URP captures beside a 1.75 m capsule.
    // Work pack 2026-11-09 (B-112h batch A): VH01 two-storey house, its own walks: up the entry step and against the closed door, along the
    // front under the gallery (stopped by the firewood and the jars, which have boxes in the collision mesh) and out past the eave line, and
    // pushed at the back, left and right walls from outside.
    // VH02 L-shaped courtyard house (same pack): from the lane through the open gate, across the yard, up the three steps onto the walk and
    // against the closed door; along the walk to the side wing and back to the jar; across the yard to the side wing; back out through the
    // gate; pushed at the yard walls, the main wing's back and the side wing from outside.
    // VH03 narrow long cottage (same pack): from the side path up the door step against the closed door on the long side; along the
    // east strip from the lane, stopped by the jar's box; into the shed through its open side to its west wall, and inside it up to the
    // firewood; pushed at the lane gable, the west wall, the east wall and the shed's back from outside.
    // RS01 (same pack): the Dondon inn re-textured, exported into art/exports/village-reskin-b: import, size, LODs, the four slots Main / Stone /
    // Wood / Tile, captures; no collision in the source or here, so no walks. RS02 (same pack): the Dondon smithy and materials shop, the same
    // checks, a capture of the forge and anvil (smithy) and of the porch counter (shop) in place of the inn's street side. RS03 (same pack): the Dondon sect gate, the same checks and a capture
    // looking up at the plaque and the bronze fittings from the steps.
    // RS02/RS03 collision (2026-11-10): <ID>_Collision from the build (one fitted box per part a walker can reach, rs_collision.py), walked:
    // gate: up the front steps through the middle bay and down off the back, stopped by the side-bay screens and, from the ground, by the
    // platform edge; smithy: onto the floor from the front and the open right side, stopped by the anvil stump, the forge, the back and
    // the left wall; shop: up the steps against the closed door, along the porch to the counter, pushed at the side and back walls.
    // The smithy's forge embers: <ID>_Emission.png on the Main material (_EmissionMap, HDR white x 3 as the Blender comparison render),
    // checked with two renders of the forge mouth, emission on and off: the centre must be clearly brighter with it on.
    // Writes artifacts/village-houses-unity/. Run with -executeMethod YunJing.Editor.VillageHousesModelCheck.Run
    // This is an editor batch check, not play in the game: nothing is placed in the main scene.
    public static class VillageHousesModelCheck
    {
        const string Root = "Assets/YunJing/Generated/VillageHousesB";
        static string Repo => Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", ".."));
        static string Exports(string id) => Path.Combine(Repo, "art", "exports", id.StartsWith("RS") ? "village-reskin-b" : "village-houses-b");
        static string Out => Path.Combine(Repo, "artifacts", "village-houses-unity");
        static readonly string[] Wanted = { "VL01_LongEmptyHouse", "VL02_MovedInHouse", "VL03_HalfCollapsedHouse", "VL04_DiligentFamilyHouse", "VL05_ElderlyCoupleHouse", "VH01_TwoStoreyHouse", "VH02_LCourtyardHouse", "VH03_NarrowCottage", "RS01_TownInn", "RS02_Blacksmith", "RS02_MaterialShop", "RS03_SectGate", "LT01_VillageStoneLantern" };
        static string[] Slots(string id) => id.StartsWith("LT") ? new[] { "Main" } : id.StartsWith("RS") ? new[] { "Main", "Stone", "Wood", "Tile" } : new[] { "Main", "Stone", "Wood", "RoofTiles" };
        static readonly List<string> Report = new List<string>();
        static int failed;

        [Serializable] class Budget { public int triangles, objects, objects_without_detail, materials; }
        [Serializable] class BudgetPerLod { public Budget LOD0, LOD1, LOD2; }
        [Serializable] class LodTotals { public int LOD0, LOD1, LOD2; }
        [Serializable] class DetailBox { public string prop; public float yaw; public float[] centre_xy, half_m, z; }
        [Serializable] class ModelInfo { public string version, minTier; public float[] dimensions_m, bounds_min_m, bounds_max_m; public float ground_z_m; public bool collision; public LodTotals lod_totals; public BudgetPerLod budget_per_lod; public string[] detailObjects; public DetailBox[] detail_collision_boxes; }

        static readonly Dictionary<string, ModelInfo> infos = new Dictionary<string, ModelInfo>();
        static ModelInfo Info(string id)
        {
            if (!infos.TryGetValue(id, out var i)) infos[id] = i = JsonUtility.FromJson<ModelInfo>(File.ReadAllText(Path.Combine(Exports(id), id, "model_info.json")));
            return i;
        }
        static string Fbx(string id) => $"{Root}/{id}/{id}_{Info(id).version}.fbx";
        static void Check(bool ok, string what) { Report.Add((ok ? "PASS " : "FAIL ") + what); if (!ok) failed++; }

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
            Report.Clear(); failed = 0; infos.Clear();
            UsePipeline();
            if (Directory.Exists(Out)) Directory.Delete(Out, true);
            Directory.CreateDirectory(Out);
            var ids = Wanted.Where(i => File.Exists(Path.Combine(Exports(i), i, "model_info.json"))).ToArray();
            Report.Add("INFO checked: " + string.Join(", ", ids.Select(i => $"{i} {Info(i).version}")) + "; not exported yet: " + string.Join(", ", Wanted.Except(ids)));
            foreach (var id in ids) Copy(id);
            AssetDatabase.Refresh();
            foreach (var id in ids) Configure(id);
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            Lighting();
            var ground = GameObject.CreatePrimitive(PrimitiveType.Plane); ground.name = "Placeholder_Ground"; ground.transform.localScale = new Vector3(80, 1, 20);
            ground.transform.position = new Vector3(ids.Length * 20, -.001f, 0);
            var gm = new Material(Shader.Find("Universal Render Pipeline/Lit")); gm.SetColor("_BaseColor", new Color(.3f, .29f, .24f)); gm.SetFloat("_Smoothness", 0);
            gm.SetFloat("_SpecularHighlights", 0); gm.EnableKeyword("_SPECULARHIGHLIGHTS_OFF");
            gm.SetFloat("_EnvironmentReflections", 0); gm.EnableKeyword("_ENVIRONMENTREFLECTIONS_OFF");
            ground.GetComponent<Renderer>().sharedMaterial = gm;
            for (int n = 0; n < ids.Length; n++)
            {
                var id = ids[n];
                var at = new Vector3(n * 40, -Info(id).ground_z_m, 0);
                var go = Place(id, at); Verify(id, go); Sockets(id, go);
                var foot = new Vector3(at.x, 0, at.z); feet[id] = foot;
                bool vh = id.StartsWith("VH"), rs = id.StartsWith("RS");
                bool court = id.StartsWith("VH02_"), lane = id.StartsWith("VH03_"), lt = id.StartsWith("LT");
                if (lt) LanternChecks(id, go, foot);
                else if (court) CourtWalks(id, foot);
                else if (lane) LaneWalks(id, foot);
                else if (vh) { VhDoor(id, foot); VhAlong(id, foot); VhWalls(id, foot); }
                else if (!rs) { UpTheSteps(id, foot); Walls(id, foot); }
                else if (Info(id).collision) RsWalks(id, foot);
                if (id.StartsWith("VL03_")) OverTheRubble(id, foot);
                if (id.StartsWith("VL04_")) AtTheWoodpile(id, foot);
                if (!rs && Info(id).detail_collision_boxes != null && Info(id).detail_collision_boxes.Length > 0) IntoTheProps(id, go, foot);
                var b = LodBounds(go);
                var person = Person(foot + new Vector3(-(b.extents.x + .6f), 0, -2f));
                var both = b; both.Encapsulate(person.GetComponent<Renderer>().bounds);
                float d = both.size.magnitude * 1.25f; var c = both.center;
                Shot(id + "_three_quarter", c, c + new Vector3(.75f, .45f, -.85f).normalized * d, 35);
                Shot(id + "_front", c, c + new Vector3(0, .12f, -1).normalized * d, 35);
                Shot(id + "_back_right", c, c + new Vector3(.85f, .4f, .75f).normalized * d, 35);
                person.SetActive(false);
                var on = rs ? Person(foot + new Vector3(8.3f, 0, 0)) : Person(foot + (court ? new Vector3(.1f, .4f, .8f) : lane ? new Vector3(2.15f, .125f, -.9f) : vh ? new Vector3(-.6f, .14f, -2.62f) : new Vector3(-.6f, .54f, -3.1f)));   // where the player stands at the door
                var dc = foot + (rs ? new Vector3(7.6f, 1.6f, 0) : court ? new Vector3(.6f, 1.6f, .5f) : lane ? new Vector3(1.9f, 1.3f, -1.2f) : vh ? new Vector3(0, 1.6f, -2.8f) : new Vector3(0, 1.4f, -3.2f));
                if (id.StartsWith("RS01_")) Shot(id + "_street_side", dc, dc + new Vector3(1, .25f, -.55f).normalized * 9f, 40);
                if (id.StartsWith("RS02_Blacksmith")) { var fa = foot + new Vector3(-.6f, .8f, .1f); Shot(id + "_forge_anvil", fa, fa + new Vector3(.6f, .35f, -1).normalized * 4.6f, 40); ForgeGlow(id); ForgeLight(id, go); }
                if (id.StartsWith("RS03_")) { var pq = foot + new Vector3(0, 3.6f, -.5f); Shot(id + "_plaque", pq, pq + new Vector3(.3f, -.45f, -1).normalized * 6f, 40); }
                if (id.StartsWith("RS02_MaterialShop")) { var ct = foot + new Vector3(-2.6f, 1f, -3.4f); Shot(id + "_porch_counter", ct, ct + new Vector3(.45f, .25f, -1).normalized * 4.6f, 40); }
                var porchDir = lane ? new Vector3(1, .3f, -.45f).normalized : new Vector3(.55f, .25f, -1).normalized;   // VH03: its door is on the long east side
                if (!rs && !lt) Shot(id + "_porch", dc, dc + porchDir * 6.5f, 40);
                UnityEngine.Object.DestroyImmediate(on);
                if (id.StartsWith("VL04_"))
                {
                    var wp = foot + new Vector3(4.1f, .5f, -.1f);
                    Shot(id + "_woodpile", wp, wp + new Vector3(1, .35f, -.55f).normalized * 4.2f, 40);
                    var sill = foot + new Vector3(2.2f, 1.1f, -2.86f);
                    Shot(id + "_sill_tray", sill, sill + new Vector3(.25f, .55f, -1).normalized * 1.9f, 40);
                }
                if (court)
                {
                    var yd = foot + new Vector3(-.5f, 1.2f, -1.8f);
                    Shot(id + "_yard", yd, yd + new Vector3(-.7f, .35f, -.8f).normalized * 7.5f, 45);
                    var gate = foot + new Vector3(.8f, 1.4f, -4.6f);
                    Shot(id + "_gate_from_lane", gate, gate + new Vector3(.2f, .15f, -1).normalized * 5.5f, 40);
                }
                else if (lane)
                {
                    var gab = foot + new Vector3(0, 2.2f, -3.8f);
                    Shot(id + "_lane_gable", gab, gab + new Vector3(.3f, .1f, -1).normalized * 7f, 40);
                    var sh = foot + new Vector3(.6f, 1.0f, 3.0f);
                    Shot(id + "_shed", sh, sh + new Vector3(1, .3f, .25f).normalized * 4.5f, 45);
                }
                else if (vh)
                {
                    var gal = foot + new Vector3(0, 3.5f, -2.7f);
                    Shot(id + "_gallery", gal, gal + new Vector3(.45f, -.05f, -1).normalized * 6.5f, 40);
                }
                if (id.StartsWith("VL05_"))      // Unity (x, up, z) = Blender (x, z, y)
                {
                    var corn = foot + new Vector3(0, 2.95f, -3.46f);
                    Shot(id + "_corn", corn, corn + new Vector3(.3f, -.45f, -1).normalized * 2.6f, 40);
                    var chair = foot + new Vector3(1.36f, .85f, -3.1f);
                    Shot(id + "_chair", chair, chair + new Vector3(-.35f, .3f, -1).normalized * 2.1f, 40);
                    var bon = foot + new Vector3(-1.36f, .85f, -3.0f);
                    Shot(id + "_bonsai", bon, bon + new Vector3(.4f, .3f, -1).normalized * 1.9f, 40);
                    var win = foot + new Vector3(2.35f, 2.0f, -2.6f);
                    Shot(id + "_window_patches", win, win + new Vector3(0, -.05f, -1).normalized * 2.2f, 40);
                }
                var det = go.GetComponentsInChildren<Renderer>(true).Where(r => r.name.Contains("_Detail_")).ToArray();
                if (det.Length > 0)
                {
                    foreach (var r in det) r.enabled = false;
                    Shot(id + "_porch_no_detail", dc, dc + porchDir * 6.5f, 40);
                    foreach (var r in det) r.enabled = true;
                }
                // LOD1 / LOD2 seen from the three-quarter camera (closer than where the group switches to them, so their loss shows).
                // The group is switched off for these: left on it keeps picking LOD0 at this distance and the hand-picked level renders nothing.
                var group = go.GetComponent<LODGroup>(); var lods = group.GetLODs();
                group.enabled = false;
                for (int lv = 1; lv < 3; lv++)
                {
                    for (int k = 0; k < 3; k++) foreach (var r in lods[k].renderers) r.enabled = k == lv;
                    Shot($"{id}_LOD{lv}", c, c + new Vector3(.75f, .45f, -.85f).normalized * d, 35);
                }
                for (int k = 0; k < 3; k++) foreach (var r in lods[k].renderers) r.enabled = true;
                group.enabled = true;
            }
            File.WriteAllText(Path.Combine(Out, "unity-verify-report.txt"), string.Join("\n", Report) + $"\n\nUnity {Application.unityVersion}; failed checks: {failed}; editor batch check only, not placed in the main scene, not played\n");
            Debug.Log("VILLAGE_HOUSES_" + (failed == 0 ? "PASS" : "FAIL") + "\n" + string.Join("\n", Report));
            if (failed > 0 && Application.isBatchMode) EditorApplication.Exit(1);
        }

        // InnGuestRoomBuilder: one model as this check imports it (FBX, atlases, LOD group, MeshCollider), its ground at y = at.y
        internal static GameObject PlaceForDemo(string id, Vector3 at)
        {
            UsePipeline(); infos.Clear(); Copy(id); AssetDatabase.Refresh(); Configure(id);
            return Place(id, at - new Vector3(0, Info(id).ground_z_m, 0));
        }

        static void Copy(string id)
        {
            var src = Path.Combine(Exports(id), id); var dst = Path.Combine(Repo, "apps", "game", Root, id);
            Directory.CreateDirectory(Path.Combine(dst, "Textures"));
            foreach (var old in Directory.GetFiles(dst, "*.fbx").Where(f => !f.EndsWith($"_{Info(id).version}.fbx"))) { File.Delete(old); if (File.Exists(old + ".meta")) File.Delete(old + ".meta"); }
            foreach (var file in Directory.GetFiles(src, $"{id}_{Info(id).version}.fbx").Concat(Directory.GetFiles(Path.Combine(src, "Textures"), "*.png")))
                File.Copy(file, Path.Combine(dst, file.Substring(src.Length + 1)), true);
        }

        static void Configure(string id)
        {
            var importer = AssetImporter.GetAtPath(Fbx(id)) as ModelImporter;
            if (importer == null) throw new FileNotFoundException("FBX not imported", id);
            importer.bakeAxisConversion = true; importer.isReadable = true;
            importer.materialImportMode = ModelImporterMaterialImportMode.ImportViaMaterialDescription;     // keeps the FBX slot names (M_<id>_Main ...) to map onto
            importer.materialLocation = ModelImporterMaterialLocation.InPrefab;
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
                ti.wrapMode = path.Contains("VL_RoofTiles_") ? TextureWrapMode.Repeat : TextureWrapMode.Clamp;
                ti.SaveAndReimport();
            }
        }

        static Texture2D Tex(string id, string file) => AssetDatabase.LoadAssetAtPath<Texture2D>($"{Root}/{id}/Textures/{file}");

        static string Prefix(string id, string slot) => slot == "Main" ? id : slot == "RoofTiles" ? "VL_RoofTiles" : $"{id}_{slot}";

        static Material Mat(string id, string slot)
        {
            var path = $"{Root}/{id}_{slot}.mat";
            var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (mat == null) { mat = new Material(Shader.Find("Universal Render Pipeline/Lit")); AssetDatabase.CreateAsset(mat, path); }
            var p = Prefix(id, slot);
            mat.SetTexture("_BaseMap", Tex(id, p + "_BaseColor.png")); mat.SetColor("_BaseColor", Color.white);
            mat.SetTexture("_BumpMap", Tex(id, p + "_Normal.png")); mat.EnableKeyword("_NORMALMAP");
            mat.SetTexture("_MetallicGlossMap", Tex(id, p + "_MetallicSmoothness.png")); mat.EnableKeyword("_METALLICSPECGLOSSMAP"); mat.SetFloat("_Smoothness", 1);
            var em = Tex(id, p + "_Emission.png");          // RS02 smithy: the forge embers (sRGB, as the BaseColor)
            if (em != null) { mat.SetTexture("_EmissionMap", em); mat.SetColor("_EmissionColor", Color.white * EmissionGain); mat.EnableKeyword("_EMISSION"); mat.globalIlluminationFlags = MaterialGlobalIlluminationFlags.RealtimeEmissive; }
            else { mat.SetTexture("_EmissionMap", null); mat.SetColor("_EmissionColor", Color.black); mat.DisableKeyword("_EMISSION"); mat.globalIlluminationFlags = MaterialGlobalIlluminationFlags.EmissiveIsBlack; }
            EditorUtility.SetDirty(mat); return mat;
        }

        const float EmissionGain = 3f;      // the strength the Blender comparison render lights the baked emission with

        static readonly Dictionary<string, string> unmapped = new Dictionary<string, string>();

        static GameObject Place(string id, Vector3 position)
        {
            var go = (GameObject)PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>(Fbx(id)));
            PrefabUtility.UnpackPrefabInstance(go, PrefabUnpackMode.Completely, InteractionMode.AutomatedAction);
            go.transform.position = position;
            var mats = Slots(id).ToDictionary(s => s, s => Mat(id, s));
            foreach (var r in go.GetComponentsInChildren<Renderer>(true))
            {
                if (r.name == id + "_Collision" || r.name == id + "_Detail_Collision") { r.enabled = false; continue; }
                r.sharedMaterials = r.sharedMaterials.Select(m =>
                {
                    var name = m != null ? m.name : "";
                    var slot = Slots(id).FirstOrDefault(s => name.EndsWith("_" + s));
                    if (slot == null) { unmapped[r.name] = name; slot = "Main"; }
                    return mats[slot];
                }).ToArray();
            }
            var cut = new[] { .1f, .035f, .006f };
            var group = go.GetComponent<LODGroup>(); if (group == null) group = go.AddComponent<LODGroup>();
            group.SetLODs(Enumerable.Range(0, 3).Select(i => new LOD(cut[i], go.GetComponentsInChildren<Renderer>(true).Where(r => r.name.EndsWith("_LOD" + i)).ToArray())).ToArray());
            foreach (var col in go.GetComponentsInChildren<MeshFilter>(true).Where(m => m.name == id + "_Collision" || m.name == id + "_Detail_Collision"))
                col.gameObject.AddComponent<MeshCollider>().sharedMesh = col.sharedMesh;
            return go;
        }

        static GameObject Person(Vector3 feet)
        {
            var p = GameObject.CreatePrimitive(PrimitiveType.Capsule); p.name = "Person_1.75m";
            UnityEngine.Object.DestroyImmediate(p.GetComponent<Collider>());
            p.transform.localScale = new Vector3(.45f, .875f, .45f); p.transform.position = feet + Vector3.up * .875f;
            var m = new Material(Shader.Find("Universal Render Pipeline/Lit")); m.SetColor("_BaseColor", new Color(.55f, .57f, .6f)); p.GetComponent<Renderer>().sharedMaterial = m;
            return p;
        }

        static Bounds LodBounds(GameObject go, string suffix = "_LOD0")
        {
            var rs = go.GetComponentsInChildren<Renderer>(true).Where(r => r.name.EndsWith(suffix)).ToArray();
            var b = rs[0].bounds; foreach (var r in rs) b.Encapsulate(r.bounds); return b;
        }

        static void Verify(string id, GameObject go)
        {
            var info = Info(id);
            var b = LodBounds(go); var o = go.transform.position;
            float[] want = info.dimensions_m; Vector3 size = b.size;
            float dx = Mathf.Abs(size.x - want[0]), dy = Mathf.Abs(size.z - want[1]), dz = Mathf.Abs(size.y - want[2]);
            Check(dx < .002f && dy < .002f && dz < .002f, $"{id}: imported size {size.x:F3} x {size.z:F3} x {size.y:F3} m matches model_info (max error {Mathf.Max(dx, dy, dz) * 1000:F1} mm)");
            var lo = b.min - o; var hi = b.max - o;
            float e = Mathf.Max(Mathf.Abs(lo.x - info.bounds_min_m[0]), Mathf.Abs(lo.z - info.bounds_min_m[1]), Mathf.Abs(lo.y - info.bounds_min_m[2]),
                                Mathf.Abs(hi.x - info.bounds_max_m[0]), Mathf.Abs(hi.z - info.bounds_max_m[1]), Mathf.Abs(hi.y - info.bounds_max_m[2]));
            Check(e < .002f, $"{id}: bounds about the origin {lo.x:F3}..{hi.x:F3}, {lo.z:F3}..{hi.z:F3}, {lo.y:F3}..{hi.y:F3} m equal model_info (max error {e * 1000:F1} mm)");
            Report.Add($"INFO {id}: minTier {info.minTier}");
            var lod = go.GetComponent<LODGroup>();
            Check(lod != null && lod.GetLODs().Length == 3 && lod.GetLODs().All(l => l.renderers.Length > 0), $"{id}: LODGroup with 3 filled levels");
            var mfs = go.GetComponentsInChildren<MeshFilter>(true);
            int tri(string s) => mfs.Where(m => m.name.EndsWith(s)).Sum(m => m.sharedMesh.triangles.Length / 3);
            int objs(string s) => mfs.Count(m => m.name.EndsWith(s));
            Check(tri("_LOD0") == info.lod_totals.LOD0 && tri("_LOD1") == info.lod_totals.LOD1 && tri("_LOD2") == info.lod_totals.LOD2,
                  $"{id}: imported LOD triangles {tri("_LOD0")}/{tri("_LOD1")}/{tri("_LOD2")} equal model_info {info.lod_totals.LOD0}/{info.lod_totals.LOD1}/{info.lod_totals.LOD2}");
            if (info.budget_per_lod != null && info.budget_per_lod.LOD0 != null)
            {
                var bl = new[] { info.budget_per_lod.LOD0, info.budget_per_lod.LOD1, info.budget_per_lod.LOD2 };
                Check(Enumerable.Range(0, 3).All(i => objs("_LOD" + i) == bl[i].objects), $"{id}: objects per LOD {objs("_LOD0")}/{objs("_LOD1")}/{objs("_LOD2")} equal model_info {bl[0].objects}/{bl[1].objects}/{bl[2].objects}");
            }
            var body = go.GetComponentsInChildren<Renderer>(true).FirstOrDefault(r => r.name == id + "_LOD0");
            var names = body != null ? body.sharedMaterials.Select(m => m.name).ToArray() : new string[0];
            Check(names.Length == Slots(id).Length && Slots(id).All(s => names.Contains($"{id}_{s}")),
                  $"{id}: {id}_LOD0 has the {Slots(id).Length} material slot(s) {string.Join(" / ", Slots(id))}, each mapped from its FBX slot name ({string.Join(", ", names)})");
            Check(!unmapped.Keys.Any(k => k.StartsWith(id)), $"{id}: every FBX material slot name was recognised" + (unmapped.Count > 0 ? " (unmapped: " + string.Join("; ", unmapped.Select(kv => kv.Key + "=" + kv.Value)) + ")" : ""));
            foreach (var d in info.detailObjects ?? new string[0])
                Check(Enumerable.Range(0, 3).All(i => mfs.Any(m => m.name == $"{d}_LOD{i}")), $"{id}: {d} present at LOD0/1/2 as its own object (can be switched off)");
            var col = go.GetComponentsInChildren<MeshCollider>(true).FirstOrDefault(c => c.name == id + "_Collision");
            if (!info.collision) Report.Add($"INFO {id}: no collision mesh (as its source); not walked");
            else Check(col != null && col.sharedMesh.triangles.Length > 0, $"{id}: {id}_Collision imported as MeshCollider ({(col ? col.sharedMesh.triangles.Length / 3 : 0)} triangles), renderer hidden");
            if (col != null) { var box = col.bounds; var all = b; all.Expand(.1f); Check(all.Contains(box.min) && all.Contains(box.max), $"{id}: the collider stays on the model"); }
            if (info.detail_collision_boxes != null && info.detail_collision_boxes.Length > 0)
            {
                var dcol = go.GetComponentsInChildren<MeshCollider>(true).FirstOrDefault(c => c.name == id + "_Detail_Collision");
                var dr = go.GetComponentsInChildren<Renderer>(true).FirstOrDefault(r => r.name == id + "_Detail_Collision");
                Check(dcol != null && dcol.sharedMesh.triangles.Length / 3 == 12 * info.detail_collision_boxes.Length && (dr == null || !dr.enabled),
                      $"{id}: {id}_Detail_Collision imported as its own MeshCollider ({(dcol ? dcol.sharedMesh.triangles.Length / 3 : 0)} triangles = {info.detail_collision_boxes.Length} boxes: {string.Join(", ", info.detail_collision_boxes.Select(x => x.prop))}), renderer hidden");
            }
            Check(!go.GetComponentsInChildren<Renderer>(true).Any(r => r.enabled && r.sharedMaterials.Any(m => m == null || m.shader.name.Contains("Error"))), $"{id}: no missing or error shaders");
            if (Tex(id, id + "_Emission.png") != null)
            {
                var mm = Mat(id, "Main");
                Check(mm.IsKeywordEnabled("_EMISSION") && mm.GetTexture("_EmissionMap") == Tex(id, id + "_Emission.png") && mm.GetColor("_EmissionColor").maxColorComponent >= EmissionGain - .01f,
                      $"{id}: {mm.name} emits through {id}_Emission.png (_EMISSION on, _EmissionColor x {mm.GetColor("_EmissionColor").maxColorComponent:F1})");
            }
            foreach (var t in Directory.GetFiles(Path.Combine(Repo, "apps", "game", Root, id, "Textures"), "*_BaseColor.png"))
            {
                var tex = Tex(id, Path.GetFileName(t)); if (tex != null) Report.Add($"INFO {id}: texture {tex.name} {tex.width}x{tex.height} (+ Normal, MetallicSmoothness of the same size)");
            }
        }

        static void Sockets(string id, GameObject go)
        {
            var text = File.ReadAllText(Path.Combine(Exports(id), id, "model_info.json"));
            int a = text.IndexOf("\"sockets_blender_xyz\""); if (a < 0) { Report.Add($"INFO {id}: no sockets in model_info"); return; }
            int b = text.IndexOf('{', a), e = text.IndexOf('}', b);
            var o = go.transform.position; float worst = 0; int found = 0, wanted = 0;
            foreach (var entry in text.Substring(b + 1, e - b - 1).Split(new[] { "]," }, StringSplitOptions.RemoveEmptyEntries))
            {
                var kv = entry.Split(':'); var name = kv[0].Trim().Trim('"', ' ', (char)10, (char)13);
                var v = kv[1].Replace("[", "").Replace("]", "").Split(',').Select(x => float.Parse(x.Trim(), System.Globalization.CultureInfo.InvariantCulture)).ToArray();
                wanted++;
                var t = go.GetComponentsInChildren<Transform>(true).FirstOrDefault(x => x.name == name); if (t == null) continue;
                found++; var p = t.position - o; worst = Mathf.Max(worst, Vector3.Distance(p, new Vector3(v[0], v[2], v[1])));
            }
            Check(found == wanted && worst < .002f, $"{id}: {found}/{wanted} socket empties imported at the model_info positions (max error {worst * 1000:F1} mm)");
        }

        static CharacterController Walker()
        {
            var body = new GameObject("Walker_1.75m"); var cc = body.AddComponent<CharacterController>();
            cc.height = 1.75f; cc.radius = .25f; cc.center = new Vector3(0, .875f, 0); cc.stepOffset = .3f; cc.slopeLimit = 45; cc.skinWidth = .02f;
            return cc;
        }

        static Vector2 Stroll(CharacterController cc, Vector3 o, Vector3 dir, int n)
        {
            float lo = 99, hi = -99;
            for (int f = 0; f < n; f++)
            {
                cc.Move(dir * (1.4f / 60f) + Vector3.down * (9.8f / 60f));
                var p = cc.transform.position - o;
                if (f > 20) { lo = Mathf.Min(lo, p.y); hi = Mathf.Max(hi, p.y); }
            }
            return new Vector2(lo, hi);
        }

        // from the path 1 m in front of the bottom step: up the three 0.18 m steps onto the 0.54 m porch, then against the closed door
        static void UpTheSteps(string id, Vector3 o)
        {
            Physics.SyncTransforms(); var cc = Walker();
            foreach (float x in new[] { -.6f, 0f, .6f })
            {
                cc.transform.position = o + new Vector3(x, .02f, -5.7f); Physics.SyncTransforms();
                var feet = Stroll(cc, o, Vector3.forward, 260); var end = cc.transform.position - o;
                Check(Mathf.Abs(end.y - .54f) < .04f && end.z > -3.0f && end.z < -2.61f - .2f && Mathf.Abs(end.x - x) < .15f,
                      $"{id}: walker on x {x:F1} climbs the steps onto the porch and stops at the closed door (end z {end.z:F2} m, feet {end.y:F3} m, highest {feet.y:F3} m)");
            }
            UnityEngine.Object.DestroyImmediate(cc.gameObject);
        }

        // pushed at the back, left and right walls from outside (on the ground): stops outside the wall line (2.61 / 3.61 m)
        static void Walls(string id, Vector3 o)
        {
            Physics.SyncTransforms(); var cc = Walker();
            var tests = new List<(string what, Vector3 start, Vector3 dir, Func<Vector3, bool> ok)>
            {
                ("back wall", new Vector3(-1.5f, .02f, 4.6f), Vector3.back, p => p.z > 2.61f + .2f),
                ("back wall", new Vector3(1.8f, .02f, 4.6f), Vector3.back, p => p.z > 2.61f + .2f),
                ("left wall", new Vector3(-5.6f, .02f, 0f), Vector3.right, p => p.x < -3.61f - .2f),
            };
            if (!id.StartsWith("VL03_")) tests.Add(("right wall", new Vector3(5.6f, .02f, 0f), Vector3.left, p => p.x > 3.61f + .2f));
            foreach (var t in tests)
            {
                cc.transform.position = o + t.start; Physics.SyncTransforms();
                var feet = Stroll(cc, o, t.dir, 240); var end = cc.transform.position - o;
                Check(t.ok(end), $"{id}: a walker pushed at the {t.what} from outside stops outside it (end x {end.x:F2}, z {end.z:F2} m, feet {feet.x:F3}-{feet.y:F3} m)");
            }
            UnityEngine.Object.DestroyImmediate(cc.gameObject);
        }

        // VL03: from outside the fallen right wall, three lines across the heap: up the rubble ramp, stopped at the old wall line,
        // then back down the way it came (it is not caught in the heap)
        static void OverTheRubble(string id, Vector3 o)
        {
            Physics.SyncTransforms(); var cc = Walker();
            foreach (float z in new[] { -.4f, .5f, 1.4f })
            {
                cc.transform.position = o + new Vector3(6.0f, .02f, z); Physics.SyncTransforms();
                var feet = Stroll(cc, o, Vector3.left, 260); var mid = cc.transform.position - o;
                Stroll(cc, o, Vector3.right, 260); var back = cc.transform.position - o;
                Check(mid.x > 3.61f + .2f && back.x > 5.5f && back.y < .05f,
                      $"{id}: on z {z:F1} a walker goes up the rubble, stops outside the fallen wall's line (x {mid.x:F2} m, feet up to {feet.y:F3} m) and walks back off it (x {back.x:F2} m, feet {back.y:F3} m)");
            }
            UnityEngine.Object.DestroyImmediate(cc.gameObject);
        }

        // VL04: the woodpile outside the right gable (x 3.86-4.34, z -1.52..1.32, collision top 0.78 m, higher than the 0.3 m step offset):
        // walkers pushed at it from outside on three lines stop outside it and stay on the ground (nobody climbs the logs)
        static void AtTheWoodpile(string id, Vector3 o)
        {
            Physics.SyncTransforms(); var cc = Walker();
            foreach (float z in new[] { -1.2f, 0f, 1.0f })
            {
                cc.transform.position = o + new Vector3(6.0f, .02f, z); Physics.SyncTransforms();
                var feet = Stroll(cc, o, Vector3.left, 260); var end = cc.transform.position - o;
                Check(end.x > 4.34f + .2f && feet.y < .05f,
                      $"{id}: on z {z:F1} a walker pushed at the woodpile from outside stops outside it (x {end.x:F2} m) and stays on the ground (feet {feet.x:F3}-{feet.y:F3} m)");
            }
            UnityEngine.Object.DestroyImmediate(cc.gameObject);
        }

        // VL04/VL05: on the porch (feet 0.54 m), two lines 0.1 m apart pushed level at each Detail_Small prop from its open side (the rack
        // and the bonsai from the door side, the chair from the door side too: the bench is behind it). With <ID>_Detail_Collision on the
        // walker stops with its 0.25 m capsule touching the prop's box (gap to the box 0.2-0.32 m from the capsule axis) and stays on the
        // porch floor; with that collider switched off (as with Detail_Small at low quality) the same line walks on past the prop's centre.
        static void IntoTheProps(string id, GameObject go, Vector3 o)
        {
            var dcol = go.GetComponentsInChildren<MeshCollider>(true).FirstOrDefault(c => c.name == id + "_Detail_Collision");
            if (dcol == null) { Check(false, $"{id}: no {id}_Detail_Collision to walk into"); return; }
            Physics.SyncTransforms(); var cc = Walker();
            foreach (var bx in Info(id).detail_collision_boxes)
            {
                float ca = Mathf.Cos(bx.yaw), sa = Mathf.Sin(bx.yaw), cx = bx.centre_xy[0], cy = bx.centre_xy[1];
                float gap(Vector3 q)    // distance in plan from q (relative to o; Unity x, z = Blender x, y) to the turned box
                {
                    float dx = q.x - cx, dy = q.z - cy, u = dx * ca + dy * sa, v = -dx * sa + dy * ca;
                    float ou = Mathf.Max(0, Mathf.Abs(u) - bx.half_m[0]), ov = Mathf.Max(0, Mathf.Abs(v) - bx.half_m[1]);
                    return Mathf.Sqrt(ou * ou + ov * ov);
                }
                float reachX = Mathf.Abs(bx.half_m[0] * ca) + Mathf.Abs(bx.half_m[1] * sa);   // the box's half width along x
                float side = cx < 0 ? 1 : -1;                                                // the door side: towards x = 0
                var dir = new Vector3(-side, 0, 0);
                foreach (float dz in new[] { 0f, .1f })
                {
                    var start = new Vector3(cx + side * (reachX + 1.0f), .56f, cy + dz);
                    dcol.enabled = true; cc.transform.position = o + start; Physics.SyncTransforms();
                    var feet = Stroll(cc, o, dir, 150); var end = cc.transform.position - o; float g = gap(end);
                    Check(g > .2f && g < .32f && Mathf.Abs(feet.y - .54f) < .04f && Mathf.Abs(feet.x - .54f) < .04f,
                          $"{id}: on the porch at z {start.z:F2} a walker pushed at the {bx.prop} stops at its collision box (capsule axis {g:F3} m from the box, x {end.x:F2} m) and stays on the floor (feet {feet.x:F3}-{feet.y:F3} m)");
                    dcol.enabled = false; cc.transform.position = o + start; Physics.SyncTransforms();
                    Stroll(cc, o, dir, 150); var through = cc.transform.position - o;
                    Check(side * (through.x - cx) < 0,
                          $"{id}: with {id}_Detail_Collision switched off the same walker goes on past the {bx.prop} (x {through.x:F2} m, prop centre x {cx:F2} m)");
                }
            }
            dcol.enabled = true;
            UnityEngine.Object.DestroyImmediate(cc.gameObject);
        }

        // VH01: from the path 2.4 m in front of the wall on three lines, up the 0.14 m entry step and against the closed door
        // (stone face at z -2.39 m; the walker stops on the step, about 0.27 m out from it)
        static void VhDoor(string id, Vector3 o)
        {
            Physics.SyncTransforms(); var cc = Walker();
            foreach (float x in new[] { -.6f, 0f, .6f })
            {
                cc.transform.position = o + new Vector3(x, .02f, -4.8f); Physics.SyncTransforms();
                var feet = Stroll(cc, o, Vector3.forward, 220); var end = cc.transform.position - o;
                Check(end.y > .12f && end.y < .3f && end.z > -2.8f && end.z < -2.55f && Mathf.Abs(end.x - x) < .15f,
                      $"{id}: walker on x {x:F1} steps up the entry step and stops at the closed door (end z {end.z:F2} m, feet {end.y:F3} m, highest {feet.y:F3} m)");
            }
            UnityEngine.Object.DestroyImmediate(cc.gameObject);
        }

        // VH01: under the gallery (z -2.7 m, the deck is 2.65 m up) from each end the walker keeps its feet on the ground and is stopped only by
        // the firewood (x -1.68) or the small jar (x 2.01); 0.75 m further out (z -3.45, under the eave line) it walks the whole front
        static void VhAlong(string id, Vector3 o)
        {
            Physics.SyncTransforms(); var cc = Walker();
            var tests = new List<(string what, Vector3 start, Vector3 dir, Func<Vector3, bool> ok)>
            {
                ("under the gallery from the left, to the firewood", new Vector3(-5.5f, .02f, -2.7f), Vector3.right, p => p.x < -1.68f - .2f && p.x > -1.68f - .4f),
                ("under the gallery from the right, to the small jar", new Vector3(5.5f, .02f, -2.7f), Vector3.left, p => p.x > 2.01f + .2f && p.x < 2.01f + .4f),
                ("along the front under the eave line", new Vector3(-5.5f, .02f, -3.45f), Vector3.right, p => p.x > 4.5f && Mathf.Abs(p.z + 3.45f) < .05f),
            };
            foreach (var t in tests)
            {
                cc.transform.position = o + t.start; Physics.SyncTransforms();
                var feet = Stroll(cc, o, t.dir, 600); var end = cc.transform.position - o;   // 600 frames = 14 m: the eave-line walk is 10 m
                Check(t.ok(end) && feet.y < .05f, $"{id}: a walker {t.what} (end x {end.x:F2}, z {end.z:F2} m, feet {feet.x:F3}-{feet.y:F3} m)");
            }
            UnityEngine.Object.DestroyImmediate(cc.gameObject);
        }

        // VH01: pushed at the back, left and right walls from outside: stops outside the footing (back z 2.42, sides x -/+3.32 m)
        static void VhWalls(string id, Vector3 o)
        {
            Physics.SyncTransforms(); var cc = Walker();
            var tests = new List<(string what, Vector3 start, Vector3 dir, Func<Vector3, bool> ok)>
            {
                ("back wall", new Vector3(-1.5f, .02f, 4.6f), Vector3.back, p => p.z > 2.42f + .2f),
                ("back wall", new Vector3(1.8f, .02f, 4.6f), Vector3.back, p => p.z > 2.42f + .2f),
                ("left wall", new Vector3(-5.6f, .02f, 0f), Vector3.right, p => p.x < -3.32f - .2f),
                ("right wall", new Vector3(5.6f, .02f, 0f), Vector3.left, p => p.x > 3.32f + .2f),
            };
            foreach (var t in tests)
            {
                cc.transform.position = o + t.start; Physics.SyncTransforms();
                var feet = Stroll(cc, o, t.dir, 240); var end = cc.transform.position - o;
                Check(t.ok(end) && feet.y < .05f, $"{id}: a walker pushed at the {t.what} from outside stops outside it (end x {end.x:F2}, z {end.z:F2} m, feet {feet.x:F3}-{feet.y:F3} m)");
            }
            UnityEngine.Object.DestroyImmediate(cc.gameObject);
        }

        // VH02 (Unity x, up, z = Blender x, z, y): gate opening x 0.35..1.25 in the front yard wall (face z -4.77); steps at x 0.6 from z -0.95 up to
        // the 0.4 m walk (z -0.05..1.15), closed main wing from z 1.15; side wing block x 2.65..5.45, z -4.45..1.15; jar box on the walk x -5.1..-4.4;
        // left yard wall face x -5.87; main wing back z 4.45.
        static void CourtWalks(string id, Vector3 o)
        {
            Physics.SyncTransforms(); var cc = Walker();
            var tests = new List<(string what, Vector3 start, Vector3 dir, int n, Func<Vector3, Vector2, bool> ok)>
            {
                ("from the lane through the open gate, across the yard, up the three steps onto the walk, stopped at the closed door",
                    new Vector3(.8f, .02f, -6.5f), Vector3.forward, 450, (p, f) => p.z > .8f && p.z < .95f && Mathf.Abs(p.y - .4f) < .03f),
                ("along the walk from the jar end to the side wing (passes the columns, stays on the 0.4 m walk)",
                    new Vector3(-3.8f, .42f, .75f), Vector3.right, 450, (p, f) => p.x > 2.3f && p.x < 2.45f && Mathf.Abs(f.x - .4f) < .03f && Mathf.Abs(f.y - .4f) < .03f),
                ("back along the walk, stopped by the jar's box",
                    new Vector3(2.0f, .42f, .75f), Vector3.left, 450, (p, f) => p.x > -4.4f + .2f && p.x < -4.4f + .35f && Mathf.Abs(f.x - .4f) < .03f),
                ("across the yard to the side wing's wall by its door",
                    new Vector3(-2f, .02f, -2.0f), Vector3.right, 300, (p, f) => p.x > 2.65f - .35f && p.x < 2.65f - .2f && f.y < .05f),
                ("from the yard back out through the gate to the lane",
                    new Vector3(.8f, .02f, -2f), Vector3.back, 300, (p, f) => p.z < -5.5f && f.y < .05f),
                ("pushed at the front yard wall from the lane", new Vector3(-3f, .02f, -6.5f), Vector3.forward, 200, (p, f) => p.z < -4.77f - .2f && p.z > -4.77f - .35f && f.y < .05f),
                ("pushed at the left yard wall from outside", new Vector3(-7.5f, .02f, -2f), Vector3.right, 200, (p, f) => p.x < -5.87f - .2f && p.x > -5.87f - .35f && f.y < .05f),
                ("pushed at the main wing's back from outside", new Vector3(0f, .02f, 6.5f), Vector3.back, 200, (p, f) => p.z > 4.45f + .2f && p.z < 4.45f + .35f && f.y < .05f),
                ("pushed at the side wing's right wall from outside", new Vector3(7.5f, .02f, -2f), Vector3.left, 200, (p, f) => p.x > 5.45f + .2f && p.x < 5.45f + .35f && f.y < .05f),
                ("pushed at the side wing's front gable from the lane", new Vector3(4.05f, .02f, -6.5f), Vector3.forward, 200, (p, f) => p.z < -4.45f - .2f && p.z > -4.45f - .35f && f.y < .05f),
            };
            foreach (var t in tests)
            {
                cc.transform.position = o + t.start; Physics.SyncTransforms();
                var feet = Stroll(cc, o, t.dir, t.n); var end = cc.transform.position - o;
                Check(t.ok(end, feet), $"{id}: a walker {t.what} (end x {end.x:F2}, z {end.z:F2} m, feet {feet.x:F3}-{feet.y:F3} m)");
            }
            UnityEngine.Object.DestroyImmediate(cc.gameObject);
        }

        // VH03 (Unity x, up, z = Blender x, z, y): house block on its footing x -1.95..1.95, z -3.95..2.15 (door closed, flush with the footing);
        // door step x 1.95..2.29, z -1.5..-0.3, top 0.125 m; shed open to the east: back wall z 3.88..4.05, west wall inner face x -1.58,
        // firewood stack x -1.62..1.22, z 3.33..3.88; jar box x 1.97..2.42, z -3.3..-2.8.
        static void LaneWalks(string id, Vector3 o)
        {
            Physics.SyncTransforms(); var cc = Walker();
            var tests = new List<(string what, Vector3 start, Vector3 dir, int n, Func<Vector3, Vector2, bool> ok)>
            {
                ("from the side path up the step to the closed door on the long side (stands on the 0.125 m step)",
                    new Vector3(4.5f, .02f, -.9f), Vector3.left, 300, (p, f) => p.x > 1.95f + .2f && p.x < 1.95f + .35f && Mathf.Abs(p.y - .125f) < .03f),
                ("along the east strip from the lane, stopped by the jar's box",
                    new Vector3(2.3f, .02f, -6.5f), Vector3.forward, 300, (p, f) => p.z < -3.3f - .2f && p.z > -3.3f - .35f && f.y < .05f),
                ("pushed at the lane gable from the lane", new Vector3(0f, .02f, -6.5f), Vector3.forward, 200, (p, f) => p.z < -3.95f - .2f && p.z > -3.95f - .35f && f.y < .05f),
                ("pushed at the west wall from outside", new Vector3(-4.5f, .02f, -1f), Vector3.right, 200, (p, f) => p.x < -1.95f - .2f && p.x > -1.95f - .35f && f.y < .05f),
                ("pushed at the east wall behind the door from outside", new Vector3(4.5f, .02f, 1.5f), Vector3.left, 200, (p, f) => p.x > 1.95f + .2f && p.x < 1.95f + .35f && f.y < .05f),
                ("into the shed through its open east side, across the clear floor to its west wall",
                    new Vector3(4.5f, .02f, 2.75f), Vector3.left, 300, (p, f) => p.x < -1.58f + .35f && p.x > -1.58f + .2f && f.y < .05f),
                ("inside the shed towards the back, stopped by the firewood stack",
                    new Vector3(.5f, .02f, 2.55f), Vector3.forward, 200, (p, f) => p.z < 3.33f - .2f && p.z > 3.33f - .35f && f.y < .05f),
                ("pushed at the shed's back from outside", new Vector3(0f, .02f, 6.5f), Vector3.back, 200, (p, f) => p.z > 4.05f + .2f && p.z < 4.05f + .35f && f.y < .05f),
            };
            foreach (var t in tests)
            {
                cc.transform.position = o + t.start; Physics.SyncTransforms();
                var feet = Stroll(cc, o, t.dir, t.n); var end = cc.transform.position - o;
                Check(t.ok(end, feet), $"{id}: a walker {t.what} (end x {end.x:F2}, z {end.z:F2} m, feet {feet.x:F3}-{feet.y:F3} m)");
            }
            UnityEngine.Object.DestroyImmediate(cc.gameObject);
        }

        static void Lighting()
        {
            RenderSettings.ambientMode = AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = new Color(.62f, .68f, .7f); RenderSettings.ambientEquatorColor = new Color(.45f, .44f, .38f); RenderSettings.ambientGroundColor = new Color(.2f, .18f, .14f);
            var sun = new GameObject("Sun").AddComponent<Light>(); sun.type = LightType.Directional; sun.intensity = 1.25f;
            sun.color = new Color(1, .96f, .88f); sun.transform.rotation = Quaternion.Euler(38, -30, 0); sun.shadows = LightShadows.Soft;
            var cam = new GameObject("Main Camera", typeof(Camera)).GetComponent<Camera>(); cam.tag = "MainCamera"; cam.nearClipPlane = .02f; cam.farClipPlane = 300;
            cam.clearFlags = CameraClearFlags.SolidColor; cam.backgroundColor = new Color(.74f, .82f, .84f);
            cam.GetUniversalAdditionalCameraData().renderPostProcessing = false;
        }

        // the smithy's forge mouth (Blender x -2.2..-1.4, y 0.31..1.54, z 0.66..0.85: the burning coal), seen from the front:
        // rendered with the Main material's emission on, then off; the middle of the picture must be clearly brighter with it on
        static void ForgeGlow(string id)
        {
            var mat = Mat(id, "Main"); var fire = Foot(id) + new Vector3(-1.8f, .76f, .9f); var eye = fire + new Vector3(.2f, .55f, -1).normalized * 1.9f;
            float on = Shot(id + "_forge_glow_on", fire, eye, 40, .3f);
            var keep = mat.GetColor("_EmissionColor"); mat.SetColor("_EmissionColor", Color.black); mat.DisableKeyword("_EMISSION");
            float off = Shot(id + "_forge_glow_off", fire, eye, 40, .3f);
            mat.SetColor("_EmissionColor", keep); mat.EnableKeyword("_EMISSION");
            Check(on > off * 1.25f && on - off > .03f, $"{id}: the forge embers glow: the middle of the forge-mouth picture averages {on:F3} with the emission on and {off:F3} with it off (x {on / Mathf.Max(off, 1e-4f):F2})");
        }

        // Socket_ForgeLight (2026-11-11): a warm point light hung on the socket must light the forge front and the anvil, which the
        // emission alone does not; the socket must sit inside the fire chamber, in front of the back lining and over the coal.
        static void ForgeLight(string id, GameObject go)
        {
            var s = go.GetComponentsInChildren<Transform>(true).FirstOrDefault(t => t.name == "Socket_ForgeLight");
            Check(s != null, $"{id}: Socket_ForgeLight imported"); if (s == null) return;
            var p = s.position - go.transform.position;
            Check(p.x > -2.28f && p.x < -1.32f && p.z > .28f && p.z < 1.54f && p.y > .74f && p.y < 1.30f,
                  $"{id}: Socket_ForgeLight sits in the fire chamber (x {p.x:F2}, z {p.z:F2}, {p.y:F2} m up; chamber x -2.28..-1.32, z 0.28..1.54, coal 0.74, vault top 1.30)");
            var target = Foot(id) + new Vector3(-1.2f, .7f, -.2f); var eye = target + new Vector3(.45f, .45f, -1).normalized * 3.6f;
            float off = Shot(id + "_forge_light_off", target, eye, 45, .5f);
            var l = new GameObject("ForgeLight").AddComponent<Light>(); l.type = LightType.Point; l.color = new Color(1f, .52f, .22f);
            l.range = 3f; l.intensity = 2f; l.shadows = LightShadows.None; l.transform.SetParent(s, false);
            float on = Shot(id + "_forge_light_on", target, eye, 45, .5f);
            UnityEngine.Object.DestroyImmediate(l.gameObject);
            Check(on > off * 1.08f, $"{id}: a point light on Socket_ForgeLight lights the forge front: the middle half of the picture averages {on:F3} with it, {off:F3} without (x {on / Mathf.Max(off, 1e-4f):F2})");
        }

        // LT01 (2026-11-11): the stone lantern. A walker stops at its base from the front and from the side; the flame glows through
        // the baked emission (on / off, close up in daylight); a point light hung on Socket_Light lights the chamber and the cap's
        // underside (on / off at night: sun off, ambient dimmed, both restored afterwards).
        static void LanternChecks(string id, GameObject go, Vector3 o)
        {
            Physics.SyncTransforms(); var cc = Walker();
            foreach (var (start, dir, what) in new[] { (new Vector3(0, .02f, -1.6f), Vector3.forward, "from the front"), (new Vector3(-1.6f, .02f, .1f), Vector3.right, "from the left") })
            {
                cc.transform.position = o + start; Physics.SyncTransforms();
                var f = Stroll(cc, o, dir, 200); var end = cc.transform.position - o; float stop = Vector3.Dot(end, dir);
                Check(stop > -.66f && stop < -.5f && end.y < .06f, $"{id}: a walker {what} stops at the base (end {stop:F2} m from the centre: base half-width 0.31 + capsule 0.25; feet {end.y:F3} m)");
            }
            UnityEngine.Object.DestroyImmediate(cc.gameObject);
            var s = go.GetComponentsInChildren<Transform>(true).FirstOrDefault(t => t.name == "Socket_Light");
            var sp = s != null ? s.position - go.transform.position : Vector3.zero;
            Check(s != null && Mathf.Abs(sp.y - 1.30f) < .005f && Mathf.Abs(sp.x) < .005f && Mathf.Abs(sp.z) < .005f, $"{id}: Socket_Light in the chamber centre (x {sp.x:F3}, {sp.y:F3} m up, z {sp.z:F3})");
            var mat = Mat(id, "Main"); var lamp = o + new Vector3(0, 1.27f, .02f); var eye = lamp + new Vector3(.15f, .05f, -1).normalized * 1.2f;
            float on = Shot(id + "_flame_glow_on", lamp, eye, 22, .1f);
            var keep = mat.GetColor("_EmissionColor"); mat.SetColor("_EmissionColor", Color.black); mat.DisableKeyword("_EMISSION");
            float off = Shot(id + "_flame_glow_off", lamp, eye, 22, .1f);
            mat.SetColor("_EmissionColor", keep); mat.EnableKeyword("_EMISSION");
            Check(on > off * 1.1f, $"{id}: the wick flame glows (middle of the close-up {on:F3} with the emission on, {off:F3} off, x {on / Mathf.Max(off, 1e-4f):F2})");
            if (s == null) return;
            var sun = GameObject.Find("Sun").GetComponent<Light>(); var sky = RenderSettings.ambientSkyColor; var eq = RenderSettings.ambientEquatorColor; var gr = RenderSettings.ambientGroundColor;
            sun.enabled = false; RenderSettings.ambientSkyColor = sky * .12f; RenderSettings.ambientEquatorColor = eq * .12f; RenderSettings.ambientGroundColor = gr * .12f;
            var wide = o + new Vector3(0, 1.25f, 0); var e2 = wide + new Vector3(.45f, .2f, -1).normalized * 2.4f;
            float loff = Shot(id + "_night_light_off", wide, e2, 40, .3f);
            var l = new GameObject("LanternLight").AddComponent<Light>(); l.type = LightType.Point; l.color = new Color(1f, .72f, .4f);
            l.range = 2.2f; l.intensity = .5f; l.shadows = LightShadows.None; l.transform.SetParent(s, false);     // 1.5 burnt the chamber white
            float lon = Shot(id + "_night_light_on", wide, e2, 40, .3f);
            UnityEngine.Object.DestroyImmediate(l.gameObject);
            sun.enabled = true; RenderSettings.ambientSkyColor = sky; RenderSettings.ambientEquatorColor = eq; RenderSettings.ambientGroundColor = gr;
            Check(lon > loff * 1.15f, $"{id}: at night a point light on Socket_Light lights the lantern (middle of the picture {lon:F3} with it, {loff:F3} without, x {lon / Mathf.Max(loff, 1e-4f):F2})");
        }

        static readonly Dictionary<string, Vector3> feet = new Dictionary<string, Vector3>();
        static Vector3 Foot(string id) => feet[id];

        // RS02 / RS03: walks against <ID>_Collision. Unity (x, up, z) = Blender (x, z, y). The stops were measured on the collision boxes
        // with level rays in Blender (gate steps and platform 0.16 / 0.32 / 0.48 / 0.50 m, smithy floor 0.18 m, shop porch 0.54 m) and
        // are a capsule radius (0.25 m) short of the surface hit.
        static void RsWalks(string id, Vector3 o)
        {
            Physics.SyncTransforms(); var cc = Walker();
            void Walk(string what, Vector3 start, Vector3 dir, int frames, Func<Vector3, Vector2, bool> ok)
            {
                cc.transform.position = o + start; Physics.SyncTransforms();
                var f = Stroll(cc, o, dir, frames); var end = cc.transform.position - o;
                Check(ok(end, f), $"{id}: {what} (end x {end.x:F2}, z {end.z:F2} m, feet {end.y:F3} m, {f.x:F3}-{f.y:F3} on the way)");
            }
            if (id.StartsWith("RS01_"))
            {
                // v002 stair (rs01_stair.py): ground floor 0.49, half landing 2.566 at the south wall (z -5.83), top landing 3.95 against the
                // guest-room partition (z -1.353), opening east onto the upper corridor (floor edge x -0.99); 20 risers of 0.173 m, treads 0.28 m
                Walk("walker from the street comes up the entry steps through the open front into the dining room (floor 0.49 m)", new Vector3(9f, .02f, -1.5f), Vector3.left, 150,
                     (e, f) => e.x < 6f && Mathf.Abs(e.y - .49f) < .04f);
                Walk("walker in the dining room goes up flight 1 from its foot at the north end to the half landing and stops at the south wall (z -5.83)",
                     new Vector3(-2.65f, .52f, -.6f), Vector3.back, 330, (e, f) => Mathf.Abs(e.y - 2.566f) < .05f && e.z < -5.4f && e.z > -5.7f);
                Walk("walker on the half landing turns and goes up flight 2 to the top landing and stops at the guest-room partition (z -1.353)",
                     new Vector3(-1.55f, 2.6f, -5.3f), Vector3.forward, 260, (e, f) => Mathf.Abs(e.y - 3.95f) < .04f && e.z > -1.75f && e.z < -1.45f);
                Walk("walker on the top landing walks east off it straight into the upper hall, past where the guest-room wall's free end stood (x 0.51, cut back to the partition in v002)",
                     new Vector3(-1.55f, 3.97f, -2.0f), Vector3.right, 150, (e, f) => Mathf.Abs(e.y - 3.95f) < .04f && e.x > 1.5f && f.x > 3.9f);
                Walk("walker on the upper floor walking west at the stair well is stopped by the new balustrade (x -0.95) and does not fall",
                     new Vector3(.6f, 3.97f, -4.2f), Vector3.left, 120, (e, f) => Mathf.Abs(e.y - 3.95f) < .04f && e.x > -.8f && e.x < -.5f && f.x > 3.9f);
                Walk("walker in the dining room walking west is stopped by the screen closing the space under flight 2 (x -0.99)",
                     new Vector3(1.0f, .52f, -3.0f), Vector3.left, 150, (e, f) => e.x > -.85f && e.x < -.55f && e.y < .7f);
                Walk("walker on the ground floor north of the stair walks south into flight 1's foot (x -2.65), not into the closed space beside it",
                     new Vector3(-1.55f, .52f, -.6f), Vector3.back, 120, (e, f) => e.z > -1.4f && Mathf.Abs(e.y - .49f) < .05f);
                Walk("walker in the upper hall walking east is stopped by the dado under the opened windows (x 5.44) and does not get onto the balcony",
                     new Vector3(2.0f, 3.97f, 0f), Vector3.right, 200, (e, f) => Mathf.Abs(e.y - 3.95f) < .04f && e.x > 5.0f && e.x < 5.3f && f.x > 3.9f);
                // two interior captures under a temporary warm point light per floor (the model has no lights of its own)
                var lamps = new[] { new Vector3(-.5f, 3.2f, -3f), new Vector3(-1.5f, 6.2f, -3.5f) }.Select(q =>
                {
                    var g = new GameObject("TempLamp"); var l = g.AddComponent<Light>(); l.type = LightType.Point; l.range = 9; l.intensity = 6; l.color = new Color(1f, .88f, .72f);
                    g.transform.position = o + q; return g;
                }).ToArray();
                Shot(id + "_stair_from_dining_room", o + new Vector3(-2.4f, 1.9f, -3.4f), o + new Vector3(2.6f, 2.0f, 1.2f), 60);
                Shot(id + "_top_landing_upper_floor", o + new Vector3(-1.4f, 4.4f, -3.6f), o + new Vector3(2.4f, 5.6f, -.4f), 60);
                Shot(id + "_upper_hall_open_windows", o + new Vector3(5.5f, 5.3f, .6f), o + new Vector3(1.2f, 5.5f, -2.0f), 60);
                Shot(id + "_balcony_open_shutters", o + new Vector3(5.6f, 5.0f, -1.2f), o + new Vector3(9.5f, 5.8f, 2.6f), 45);
                foreach (var g in lamps) UnityEngine.Object.DestroyImmediate(g);
            }
            else if (id.StartsWith("RS03_"))
            {
                foreach (float x in new[] { -.5f, 0f, .5f })
                    Walk($"walker on x {x:F1} climbs the three front steps onto the 0.50 m platform and walks through the middle bay past the columns (z 0.3-0.6)",
                         new Vector3(x, .02f, -4f), Vector3.forward, 230, (e, f) => Mathf.Abs(e.y - .5f) < .04f && e.z > 1.0f && Mathf.Abs(e.x - x) < .15f);
                Walk("walker on the platform walks on out of the back and down onto the ground behind", new Vector3(0, .52f, 1.2f), Vector3.forward, 120, (e, f) => e.z > 2.5f && e.y < .05f);
                foreach (float x in new[] { -2.6f, 2.6f })
                    Walk($"walker on the platform at x {x:F1} is stopped by the side bay's lattice screen (bars at z 0.38)", new Vector3(x, .55f, -1f), Vector3.forward, 120,
                         (e, f) => e.z < .2f && e.z > -.15f && Mathf.Abs(e.y - .5f) < .04f);
                foreach (float x in new[] { -3f, 3f })
                    Walk($"walker on the ground at x {x:F1} is stopped by the 0.50 m platform edge (z -1.30), higher than its 0.3 m step", new Vector3(x, .02f, -3.5f), Vector3.forward, 150,
                         (e, f) => e.z < -1.45f && e.z > -1.75f && f.y < .05f);
            }
            else if (id.StartsWith("RS02_Blacksmith"))
            {
                foreach (float x in new[] { 0f, .25f, .5f })
                    // the stump's box follows the log's lean (front face z -1.23 at x 0 to -1.12 at x 0.5, about -1.0 at x 0.9): the walker
                    // slides along it to the right a little and stays in front of it, it does not get through to the anvil
                    Walk($"walker on x {x:F2} steps onto the 0.18 m floor from the open front and is stopped in front of the anvil stump (front face z -1.23..-1.0; it slides along the slanted face, not through it)", new Vector3(x, .02f, -4f), Vector3.forward, 200,
                         (e, f) => e.z > -1.65f && e.z < -1.15f && e.x - x > -.1f && e.x - x < .6f && Mathf.Abs(e.y - .18f) < .05f);
                Walk("walker beside the quench tub is stopped by the forge front (z 0.25)", new Vector3(-1.6f, .2f, -.8f), Vector3.forward, 100, (e, f) => e.z > -.15f && e.z < .1f && Mathf.Abs(e.y - .18f) < .05f);
                Walk("walker behind the anvil is stopped by the back wall (z 2.19)", new Vector3(0, .2f, .1f), Vector3.forward, 150, (e, f) => e.z > 1.8f && e.z < 2.0f && Mathf.Abs(e.y - .18f) < .05f);
                Walk("walker is stopped by the low left wall (x -3.08)", new Vector3(-1f, .2f, -.8f), Vector3.left, 120, (e, f) => e.x < -2.7f && e.x > -2.95f && Mathf.Abs(e.y - .18f) < .05f);
                Walk("walker comes in from the open right side onto the floor, between the anvil and the workbench, up to the bellows (x -0.53)", new Vector3(5f, .02f, .6f), Vector3.left, 300,
                     (e, f) => e.x > -.45f && e.x < -.15f && Mathf.Abs(e.y - .18f) < .05f);
            }
            else if (id.StartsWith("RS02_MaterialShop"))
            {
                foreach (float x in new[] { -.35f, 0f, .45f })
                    Walk($"walker on x {x:F2} climbs the three 0.18 m steps onto the 0.54 m porch and stops at the closed door (z -2.755)", new Vector3(x, .02f, -5.6f), Vector3.forward, 240,
                         (e, f) => Mathf.Abs(e.y - .54f) < .04f && e.z > -3.15f && e.z < -2.9f && Mathf.Abs(e.x - x) < .15f);
                Walk("walker on the porch is stopped by the counter (x -1.44)", new Vector3(-.6f, .56f, -3.2f), Vector3.left, 100, (e, f) => e.x > -1.3f && e.x < -1.1f && Mathf.Abs(e.y - .54f) < .04f);
                // the walls stand on a stone footing that runs out to x -3.80 / 3.80 and z 2.80 and is higher than the 0.3 m step offset
                // (the wall face above it is at x -3.575 / 3.575, z 2.60): the walker stays on the ground outside the footing
                Walk("walker pushed at the left wall from outside stops outside its stone footing (x -3.80)", new Vector3(-6f, .02f, 0), Vector3.right, 200, (e, f) => e.x < -3.98f && e.x > -4.2f && f.y < .05f);
                Walk("walker pushed at the right wall from outside stops outside its stone footing (x 3.80)", new Vector3(6f, .02f, 0), Vector3.left, 200, (e, f) => e.x > 3.98f && e.x < 4.2f && f.y < .05f);
                Walk("walker pushed at the back wall from outside stops outside its stone footing (z 2.80)", new Vector3(0, .02f, 4.6f), Vector3.back, 200, (e, f) => e.z > 2.98f && e.z < 3.25f && f.y < .05f);
            }
            UnityEngine.Object.DestroyImmediate(cc.gameObject);
        }

        static void Shot(string file, Vector3 target, Vector3 eye, float fov = 40) => Shot(file, target, eye, fov, 0);

        // renders and saves; returns the mean of the middle `frac` of the picture (sRGB 0..1), or 0 when frac is 0
        static float Shot(string file, Vector3 target, Vector3 eye, float fov, float frac)
        {
            var cam = Camera.main; var rt = new RenderTexture(1600, 900, 24, RenderTextureFormat.ARGB32) { antiAliasing = 4 };
            cam.transform.position = eye; cam.transform.LookAt(target); cam.fieldOfView = fov; cam.targetTexture = rt; cam.Render();
            RenderTexture.active = rt; var tex = new Texture2D(1600, 900, TextureFormat.RGB24, false); tex.ReadPixels(new Rect(0, 0, 1600, 900), 0, 0); tex.Apply();
            File.WriteAllBytes(Path.Combine(Out, file + ".png"), tex.EncodeToPNG());
            float mean = 0;
            if (frac > 0)
            {
                int w = (int)(1600 * frac), h = (int)(900 * frac); var px = tex.GetPixels(800 - w / 2, 450 - h / 2, w, h);
                mean = px.Average(c => (c.r + c.g + c.b) / 3f);
            }
            UnityEngine.Object.DestroyImmediate(tex);
            RenderTexture.active = null; cam.targetTexture = null; rt.Release(); Report.Add("SHOT " + file);
            return mean;
        }
    }
}
