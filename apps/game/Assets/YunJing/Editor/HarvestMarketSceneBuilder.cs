using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using YunJing.HarvestMarket;

namespace YunJing.Editor
{
    // Work pack 02-B test scene: a 2.6 × 3.4 m field slot (TY_Field01) and B's herb stall, built from the MK01–MK04
    // exports in art/exports/harvest-market-b and HerbalStall v002 (Socket_Scale). Ground, field soil and the
    // keeper-height post are graybox and named Placeholder_*. Everything lands in gitignored folders.
    public static class HarvestMarketSceneBuilder
    {
        const string Scene = "Assets/YunJing/Generated/HarvestMarket.unity";
        const string Root = "Assets/YunJing/Generated/HarvestMarket";
        const string Models = "Assets/YunJing/Models/HarvestMarketB";
        static string Repo => Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", ".."));
        static string Exports => Path.Combine(Repo, "art", "exports", "harvest-market-b");
        static string StallSrc => Path.Combine(Repo, "art", "incoming", "dondon", "HerbalStall", "v002");
        static readonly string[] Ids = { "MK01_Steelyard", "MK02_HarvestSieve", "MK03_PriceBoard", "MK04_BackBasket" };
        static readonly List<string> Report = new List<string>();

        [Serializable] class ModelInfo { public float[] dimensions_m; }

        // Generated/URP.asset is git-ignored and ProjectBuilder only assigns it when it creates it: assign it every run,
        // so a checkout with the committed (pipeline-less) GraphicsSettings does not render URP shaders magenta.
        static void UsePipeline()
        {
            var pipeline = AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>("Assets/YunJing/Generated/URP.asset");
            if (pipeline == null) { ProjectBuilder.Generate(); pipeline = AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>("Assets/YunJing/Generated/URP.asset"); }
            if (GraphicsSettings.defaultRenderPipeline != pipeline) GraphicsSettings.defaultRenderPipeline = pipeline;
            if (QualitySettings.renderPipeline != pipeline) QualitySettings.renderPipeline = pipeline;
        }

        [MenuItem("Yun Jing/Generate harvest market (02-B)")]
        public static void Generate()
        {
            Report.Clear();
            UsePipeline();
            Directory.CreateDirectory(Path.Combine(Repo, "apps", "game", Root)); CopyExports(); AssetDatabase.Refresh(); ConfigureImports();
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var world = new GameObject("HarvestMarket").transform;

            var ground = Box(world, "Placeholder_Ground", new Vector3(0, -.05f, 0), new Vector3(16, .1f, 12), Flat("Graybox_Grass", new Color(.36f, .45f, .26f), .1f));
            Box(world, "Placeholder_Path", new Vector3(0, .002f, -1.2f), new Vector3(6.5f, .01f, 1.4f), Flat("Graybox_Path", new Color(.55f, .48f, .37f), .1f));

            // --- field: A's TY01 slot stand-in, 2.6 × 3.4 m of tilled soil with the harvest panel at its centre
            var fieldAt = new Vector3(-3.4f, 0, .6f);
            Box(world, "Placeholder_FieldSoil_TY01", fieldAt + new Vector3(0, .03f, 0), new Vector3(2.6f, .06f, 3.4f), Flat("Graybox_Soil", new Color(.3f, .22f, .15f), .05f));
            // Two raised planting ridges, one per herb column (±0.65 m), so the herbs grow out of a bed, not a flat slab.
            const float ridge = .05f;
            foreach (var x in new[] { -.65f, .65f })
            {
                var bed = Box(world, $"Placeholder_FieldRidge_{(x < 0 ? "L" : "R")}", fieldAt + new Vector3(x, .06f + ridge / 2, 0), new Vector3(.74f, ridge, 3.2f), Flat("Graybox_SoilRidge", new Color(.34f, .25f, .17f), .05f));
                UnityEngine.Object.DestroyImmediate(bed.GetComponent<Collider>());
            }
            var fieldGo = new GameObject("TY_Field01"); fieldGo.transform.SetParent(world); fieldGo.transform.position = fieldAt + new Vector3(0, .06f + ridge, 0);
            var field = fieldGo.AddComponent<QingxiHarvestPanel>();
            field.soilMat = Flat("Soil_Loose", new Color(.27f, .19f, .12f), .12f);
            field.topPlant = HerbPrefab("top"); field.midPlant = HerbPrefab("mid"); field.lowPlant = HerbPrefab("low");

            var mk02 = Place("MK02_HarvestSieve", "MK02_SieveAndBundles", world, fieldAt + new Vector3(2.0f, 0, -2.1f), 200);
            foreach (var t in mk02.GetComponentsInChildren<Transform>(true).Where(t => t.name.Contains("_Plant"))) t.gameObject.SetActive(false); // the plants live in the field
            Glow(mk02, "_BundleTop");
            var mk04 = Place("MK04_BackBasket", "MK04_Basket", world, fieldAt + new Vector3(-1.75f, 0, -1.9f), 160);
            StandOnGround(mk04);   // origin is on the strap face (Socket_Back); lift the feet onto the ground

            // --- sort station beside the field: the real MK02 sieve on an indigo cloth, three small sieves (MK02 at
            // 0.62×, 36 cm) as the top / mid / low trays, each with an MK03 demand tag lying in front as its name plate
            var stationAt = fieldAt + new Vector3(2.95f, 0, .75f);
            var station = new GameObject("SortStation").transform; station.SetParent(world); station.position = stationAt;
            Box(station, "SortCloth", stationAt + new Vector3(.05f, .004f, .1f), new Vector3(3.2f, .008f, 2.6f), Linen());
            field.sortSieve = PieceCopy("MK02_HarvestSieve", "", "Sort_Sieve", station, new Vector3(-.3f, .008f, .02f)).transform;
            PieceCopy("MK02_HarvestSieve", "_Litter", "Sort_SieveLitter", station, new Vector3(-.3f, .008f, .02f));   // same origin as the sieve; the trays stay clean
            string[] bins = { "top", "mid", "low" };
            for (int k = 0; k < 3; k++)
            {
                var at = new Vector3(.38f, .008f, .36f - k * .36f);
                var tray = PieceCopy("MK02_HarvestSieve", "", "Sort_Tray_" + bins[k], station, at); tray.transform.localScale = Vector3.one * .62f;
                var box = tray.AddComponent<BoxCollider>(); box.center = new Vector3(0, .06f, 0); box.size = new Vector3(.66f, .2f, .66f);   // 41 cm drop area
                field.trays[k] = tray.transform;
                var tag = PieceCopy("MK03_PriceBoard", "_PlateDemand", "Sort_Tag_" + bins[k], station, at + new Vector3(-.255f, .012f, .055f));
                tag.transform.localRotation = Quaternion.Euler(90, 0, 0);   // lying face up, peg end away from the player
                field.tags[k] = tag.transform;
            }

            // --- stall: HerbalStall v002, MK01 hung on Socket_Scale, MK03 board beside the counter
            var stall = PlaceStall(world, new Vector3(3.0f, 0, 1.4f), 0);   // stall front (Blender -Y) is -Z here, toward the camera
            var socket = Find(stall.transform, "Socket_Scale");
            var mk01 = Place("MK01_Steelyard", "MK01_Steelyard", stall.transform, Vector3.zero, 180);   // MK fronts import as +Z
            var hook = Find(mk01.transform, "SOCKET_hook");
            mk01.transform.position += socket.position - hook.position;
            var hookLocal = mk01.transform.InverseTransformPoint(Find(mk01.transform, "SOCKET_hook").position);
            Report.Add($"MK01 SOCKET_hook local {hookLocal} (Blender -0.256,0,0.584 → B2U {B2U(new Vector3(-.256f, 0, .584f))})");
            if ((hookLocal - B2U(new Vector3(-.256f, 0, .584f))).magnitude > .005f) throw new InvalidDataException("MK FBX axis mapping is off: SOCKET_hook " + hookLocal);
            Report.Add($"MK01 hook→Socket_Scale gap {(Find(mk01.transform, "SOCKET_hook").position - socket.position).magnitude * 1000:0.0} mm");
            var weight = WeightSlide(mk01);
            var mk03 = Place("MK03_PriceBoard", "MK03_PriceBoard", world, stall.transform.TransformPoint(S2U(new Vector3(-2.0f, -.55f, 0))), 15);   // face the player at the stall front (195 showed the blank back)
            foreach (var n in new[] { "_CoinString", "_LooseCoins", "_Purse" })
                foreach (var t in mk03.GetComponentsInChildren<Transform>(true).Where(t => t.name.Contains(n))) t.gameObject.SetActive(false);
            var coinString = CoinPrefab();
            var counter = Marker("CoinDrop", stall.transform, S2U(new Vector3(-.25f, -.5f, 1.078f)));
            var purse = PieceCopy("MK03_PriceBoard", "_Purse", "MK03_Purse", stall.transform, S2U(new Vector3(.75f, -.5f, 1.078f)));
            var loose = PieceCopy("MK03_PriceBoard", "_LooseCoins", "MK03_LooseCoins", stall.transform, S2U(new Vector3(.55f, -.52f, 1.078f)));

            var sellGo = new GameObject("Market_HerbalStall_Sell"); sellGo.transform.SetParent(world);
            var sell = sellGo.AddComponent<QingxiMarketSellPanel>();
            sell.scaleWeight = weight; sell.weightMin = 0; sell.weightMax = .5f; sell.coinDrop = counter.transform; sell.coinStringPrefab = coinString;
            // What is being weighed: one MK02 bundle per grade, hidden until the sold bundles drop into the MK01 pan.
            // SOCKET_pan is where the cords hang from; the bundles lie in the bowl, so use the Pan mesh bounds.
            var panBowl = Bounds(mk01.GetComponentsInChildren<Transform>(true).First(t => t.name == "MK01_Steelyard_Pan" && t.GetComponent<LODGroup>() != null).gameObject, "_LOD0");
            var panLoad = new GameObject("PanLoad").transform; panLoad.SetParent(mk01.transform, false);
            panLoad.SetPositionAndRotation(new Vector3(panBowl.center.x, panBowl.min.y, panBowl.center.z), stall.transform.rotation);
            var panBins = new[] { ("top", "_BundleTop"), ("mid", "_BundleMid"), ("low", "_BundleLow") };
            for (int k = 0; k < 3; k++)
            {
                var b = PieceCopy("MK02_HarvestSieve", panBins[k].Item2, "Pan_Bundle_" + panBins[k].Item1, panLoad, Vector3.zero);
                b.transform.localRotation = Quaternion.Euler(0, (k - 1) * 18, 90); b.transform.localScale = Vector3.one * .55f;   // lying across the bowl
                var lay = Bounds(b, "_LOD0");   // centre it in the bowl, resting a little above the bowl floor, stacked by grade
                b.transform.position += new Vector3(panBowl.center.x - lay.center.x, panBowl.min.y + .012f + k * .012f - lay.min.y, panBowl.center.z - lay.center.z);
                Report.Add($"Pan bundle {panBins[k].Item1}: {lay.size.x:0.00}×{lay.size.y:0.00}×{lay.size.z:0.00} m in a {panBowl.size.x:0.00} m pan");
                b.SetActive(false); sell.panBundles[k] = b;
            }

            // --- a 1.75 m post where the keeper stands, only for scale in screenshots (no NPC)
            var post = GameObject.CreatePrimitive(PrimitiveType.Capsule); post.name = "Placeholder_Keeper175"; post.transform.SetParent(stall.transform, false);
            post.transform.localPosition = S2U(new Vector3(-.2f, .3f, .875f)); post.transform.localScale = new Vector3(.45f, .875f, .45f);
            UnityEngine.Object.DestroyImmediate(post.GetComponent<Collider>()); post.GetComponent<Renderer>().sharedMaterial = Flat("Graybox_Keeper", new Color(.62f, .58f, .52f), .1f);

            // --- camera: two framed views (field, stall), moved by the playtest / harvest flow
            var cameraGo = new GameObject("Main Camera", typeof(Camera), typeof(AudioListener), typeof(HarvestCameraRig));
            cameraGo.tag = "MainCamera"; var camera = cameraGo.GetComponent<Camera>(); camera.nearClipPlane = .05f; camera.farClipPlane = 80; camera.fieldOfView = 50;
            camera.GetUniversalAdditionalCameraData().renderPostProcessing = true;
            var rig = cameraGo.GetComponent<HarvestCameraRig>();
            var fieldView = View("View_Field", world, fieldAt + new Vector3(0, 3.6f, -3.3f), fieldAt + new Vector3(0, 0, .25f));
            var stallView = View("View_Stall", world, stall.transform.position + new Vector3(-.15f, 1.85f, -2.7f), stall.transform.position + new Vector3(-.15f, 1.3f, 0));
            var sortView = View("View_Sort", world, stationAt + new Vector3(.06f, 1.24f, -.7f), stationAt + new Vector3(.06f, 0, -.04f));
            // weighing close-up: leans in over the counter so the counterweight and the coin string fill the frame
            var weighLook = Vector3.Lerp(weight.position, counter.transform.position, .5f) + Vector3.up * .12f;   // beam low enough that the stars and reading clear the top strip
            var weighView = View("View_Weigh", world, weighLook + new Vector3(0, .5f, -1.3f), weighLook);
            rig.views = new[] { fieldView, stallView, sortView, weighView }; field.rig = rig; field.sortView = 2;
            sell.rig = rig; sell.weighView = 3; sell.steelyard = mk01.transform; sell.hook = Find(mk01.transform, "SOCKET_hook");
            cameraGo.transform.SetPositionAndRotation(fieldView.position, fieldView.rotation);
            field.view = camera;
            BuildLighting(world);

            var services = new GameObject("HarvestServices");
            var test = services.AddComponent<HarvestMarketPlaytest>(); test.field = field; test.stall = sell; test.rig = rig;

            PlayerSettings.companyName = "YunJing"; PlayerSettings.productName = "YunJing Harvest 02B";   // ASCII: the player data path and crash folder use it
            if (!EditorSceneManager.SaveScene(scene, Scene)) throw new IOException("Could not save " + Scene);
            AssetDatabase.SaveAssets();
            Directory.CreateDirectory(Path.Combine(Repo, "artifacts"));
            File.WriteAllText(Path.Combine(Repo, "artifacts", "harvest-market-build.txt"), string.Join("\n", Report));
            Debug.Log("HARVEST_SCENE_GENERATED " + Scene + "\n" + string.Join("\n", Report));
        }

        // Blender metres (x right, y back, z up; front -Y) → Unity local under a bakeAxisConversion FBX root.
        // Checked against the imported Socket_Scale in Generate's report.
        static Vector3 B2U(Vector3 b) => new Vector3(b.x, b.z, -b.y);   // MK exports: front (Blender -Y) imports as +Z
        // HerbalStall v001/v002 came out of Blender's default FBX export (root rotated -90° X, no axis bake):
        // under the stall wrapper a Blender point lands at (x, z, y). Checked against Socket_Scale in PlaceStall.
        static Vector3 S2U(Vector3 b) => new Vector3(b.x, b.z, b.y);

        // ---------------------------------------------------------------- imports

        static void CopyExports()
        {
            foreach (var id in Ids)
            {
                var src = Path.Combine(Exports, id); var dst = Path.Combine(Repo, "apps", "game", Models, id);
                if (!File.Exists(Path.Combine(src, "validation.json"))) throw new FileNotFoundException("Run the Blender build first", Path.Combine(src, "validation.json"));
                Directory.CreateDirectory(Path.Combine(dst, "Textures"));
                foreach (var file in Directory.GetFiles(src, "*.fbx").Concat(Directory.GetFiles(Path.Combine(src, "Textures"), "*.png")).Append(Path.Combine(src, "model_info.json")))
                    Copy(file, Path.Combine(dst, file.Substring(src.Length + 1)));
            }
            Copy(Path.Combine(StallSrc, "HerbalStall_v002.fbx"), Path.Combine(Repo, "apps", "game", Models, "HerbalStall", "HerbalStall_v002.fbx"));
        }

        static void Copy(string from, string to)
        {
            Directory.CreateDirectory(Path.GetDirectoryName(to));
            if (!File.Exists(to) || File.ReadAllBytes(to).Length != new FileInfo(from).Length || !File.ReadAllBytes(to).SequenceEqual(File.ReadAllBytes(from))) File.Copy(from, to, true);
        }

        static void ConfigureImports()
        {
            foreach (var id in Ids)
            {
                Model(id, $"{Models}/{id}/{id}_v001.fbx", false);
                foreach (var tex in Directory.GetFiles(Path.Combine(Repo, "apps", "game", Models, id, "Textures"), "*.png"))
                {
                    var path = $"{Models}/{id}/Textures/{Path.GetFileName(tex)}";
                    var ti = AssetImporter.GetAtPath(path) as TextureImporter; if (ti == null) continue;
                    bool normal = path.EndsWith("_Normal.png"), data = normal || path.EndsWith("_MetallicSmoothness.png") || path.EndsWith("_Roughness.png") || path.EndsWith("_Metallic.png");
                    var type = normal ? TextureImporterType.NormalMap : TextureImporterType.Default;
                    if (ti.textureType != type || ti.sRGBTexture == data || ti.maxTextureSize != 2048)
                    { ti.textureType = type; ti.sRGBTexture = !data; ti.maxTextureSize = 2048; ti.mipmapEnabled = true; ti.SaveAndReimport(); }
                }
            }
            Model("HerbalStall", $"{Models}/HerbalStall/HerbalStall_v002.fbx", true);
        }

        static void Model(string id, string path, bool keepMaterials)
        {
            var importer = AssetImporter.GetAtPath(path) as ModelImporter;
            if (importer == null) throw new FileNotFoundException("FBX not imported", path);
            var mode = keepMaterials ? ModelImporterMaterialImportMode.ImportViaMaterialDescription : ModelImporterMaterialImportMode.None;
            bool dirty = !importer.bakeAxisConversion || importer.materialImportMode != mode || importer.importAnimation;
            importer.bakeAxisConversion = true; importer.materialImportMode = mode;
            importer.importAnimation = false; importer.importCameras = false; importer.importLights = false; importer.addCollider = false;
            if (dirty) importer.SaveAndReimport();
        }

        static Material ModelMaterial(string id)
        {
            var path = $"{Root}/{id}.mat";
            var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (mat == null) { mat = new Material(Shader.Find("Universal Render Pipeline/Lit")); AssetDatabase.CreateAsset(mat, path); }
            string tex(string ch) => $"{Models}/{id}/Textures/{id}_{ch}.png";
            mat.SetTexture("_BaseMap", AssetDatabase.LoadAssetAtPath<Texture2D>(tex("BaseColor"))); mat.SetColor("_BaseColor", Color.white);
            var normal = AssetDatabase.LoadAssetAtPath<Texture2D>(tex("Normal"));
            if (normal != null) { mat.SetTexture("_BumpMap", normal); mat.EnableKeyword("_NORMALMAP"); }
            var ms = AssetDatabase.LoadAssetAtPath<Texture2D>(tex("MetallicSmoothness"));
            if (ms != null) { mat.SetTexture("_MetallicGlossMap", ms); mat.EnableKeyword("_METALLICSPECGLOSSMAP"); mat.SetFloat("_Smoothness", 1); }
            var emissive = AssetDatabase.LoadAssetAtPath<Texture2D>(tex("Emission"));
            if (emissive != null)
            {
                mat.SetTexture("_EmissionMap", emissive); mat.SetColor("_EmissionColor", Color.black); mat.EnableKeyword("_EMISSION");
                mat.globalIlluminationFlags = MaterialGlobalIlluminationFlags.RealtimeEmissive;
            }
            EditorUtility.SetDirty(mat); return mat;
        }

        // ---------------------------------------------------------------- placing

        static GameObject Place(string id, string name, Transform parent, Vector3 position, float yaw)
        {
            var source = AssetDatabase.LoadAssetAtPath<GameObject>($"{Models}/{id}/{id}_v001.fbx");
            var model = (GameObject)PrefabUtility.InstantiatePrefab(source); model.name = name;
            PrefabUtility.UnpackPrefabInstance(model, PrefabUnpackMode.Completely, InteractionMode.AutomatedAction);
            model.transform.SetParent(parent, false); model.transform.localPosition = position; model.transform.localRotation = Quaternion.Euler(0, yaw, 0);
            var mat = ModelMaterial(id);
            foreach (var r in model.GetComponentsInChildren<Renderer>(true)) { r.sharedMaterials = Enumerable.Repeat(mat, r.sharedMaterials.Length).ToArray(); r.shadowCastingMode = ShadowCastingMode.On; }
            Lods(model);
            var info = JsonUtility.FromJson<ModelInfo>(File.ReadAllText(Path.Combine(Exports, id, "model_info.json")));
            var b = Bounds(model, "_LOD0");
            var want = new Vector3(info.dimensions_m[0], info.dimensions_m[2], info.dimensions_m[1]);
            var got = Quaternion.Inverse(model.transform.rotation) * b.size; got = new Vector3(Mathf.Abs(got.x), Mathf.Abs(got.y), Mathf.Abs(got.z));
            Report.Add($"{id}: imported LOD0 {b.size.x:0.###}×{b.size.y:0.###}×{b.size.z:0.###} m world AABB; height {b.size.y:0.###} (model_info {want.y:0.###})");
            if (Mathf.Abs(b.size.y - want.y) > .01f) throw new InvalidDataException($"{id} imported height {b.size.y} does not match model_info {want.y}");
            return model;
        }

        // One LODGroup per exported group: the FBX carries <group>_LOD0/1/2 siblings.
        static void Lods(GameObject model)
        {
            float[] cut = { .25f, .08f, .015f };
            var whole = model.GetComponent<LODGroup>(); if (whole != null) UnityEngine.Object.DestroyImmediate(whole);   // Unity's auto LODGroup spans every group
            var groups = model.GetComponentsInChildren<Renderer>(true).Where(r => r.name.Contains("_LOD"))
                .GroupBy(r => r.name.Substring(0, r.name.LastIndexOf("_LOD", StringComparison.Ordinal)));
            foreach (var g in groups)
            {
                var levels = new List<LOD>();
                for (int i = 0; i < 3; i++) { var rs = g.Where(r => r.name.EndsWith("_LOD" + i)).ToArray(); if (rs.Length > 0) levels.Add(new LOD(cut[i], rs)); }
                if (levels.Count < 2) continue;
                var host = new GameObject(g.Key); host.transform.SetParent(g.First().transform.parent, false);
                foreach (var r in g) r.transform.SetParent(host.transform, true);
                var group = host.AddComponent<LODGroup>(); group.SetLODs(levels.ToArray()); group.RecalculateBounds();
            }
        }

        static GameObject PlaceStall(Transform parent, Vector3 at, float yaw)
        {
            var source = AssetDatabase.LoadAssetAtPath<GameObject>($"{Models}/HerbalStall/HerbalStall_v002.fbx");
            // v001/v002 were exported with Blender's default FBX axes: the root node keeps a -90° X rotation that turns
            // Z-up into Y-up. Keep it, and place / turn the stall through a wrapper instead.
            var stall = new GameObject("Market_HerbalStall"); stall.transform.SetParent(parent, false);
            stall.transform.position = at; stall.transform.rotation = Quaternion.Euler(0, yaw, 0);
            var model = (GameObject)PrefabUtility.InstantiatePrefab(source); model.name = "HerbalStall_v002";
            PrefabUtility.UnpackPrefabInstance(model, PrefabUnpackMode.Completely, InteractionMode.AutomatedAction);
            model.transform.SetParent(stall.transform, false);
            var lit = Shader.Find("Universal Render Pipeline/Lit");
            foreach (var r in stall.GetComponentsInChildren<Renderer>())
                foreach (var m in r.sharedMaterials) if (m != null && m.shader != lit) Report.Add($"HerbalStall material {m.name} uses {m.shader.name}");
            var c = stall.AddComponent<BoxCollider>(); c.center = new Vector3(.23f, .54f, 0); c.size = new Vector3(2.75f, 1.08f, 1.2f);
            var socket = Find(stall.transform, "Socket_Scale");
            var local = stall.transform.InverseTransformPoint(socket.position);
            Report.Add($"HerbalStall v002 Socket_Scale local {local.x:0.###},{local.y:0.###},{local.z:0.###} (Blender 0.45,-0.649,2.005 → expected {S2U(new Vector3(.45f, -.649f, 2.005f))})");
            if ((local - S2U(new Vector3(.45f, -.649f, 2.005f))).magnitude > .005f) throw new InvalidDataException($"Socket_Scale not where Blender put it: axis mapping is off. local {local.x:0.####},{local.y:0.####},{local.z:0.####} scale {stall.transform.lossyScale} children {string.Join(",", stall.transform.Cast<Transform>().Select(t => t.name + "@" + t.localPosition + "/" + t.localEulerAngles + "/" + t.localScale))}");
            return stall;
        }

        // The counterweight slides along the beam, from SOCKET_weight_rest towards SOCKET_weight_max: put it under a
        // transform whose local X is that direction, so the sell panel's localPosition.x is metres along the beam.
        static Transform WeightSlide(GameObject mk01)
        {
            var rest = Find(mk01.transform, "SOCKET_weight_rest"); var max = Find(mk01.transform, "SOCKET_weight_max");
            var axis = new GameObject("WeightAxis").transform; axis.SetParent(mk01.transform, false);
            axis.position = rest.position; axis.rotation = Quaternion.FromToRotation(Vector3.right, (max.position - rest.position).normalized);
            var slide = new GameObject("WeightSlide").transform; slide.SetParent(axis, false);
            var weight = mk01.GetComponentsInChildren<Transform>(true).First(t => t.name == "MK01_Steelyard_Weight");
            weight.SetParent(slide, true);
            Report.Add($"MK01 weight travel {(max.position - rest.position).magnitude:0.###} m along the beam");
            return slide;
        }

        static void StandOnGround(GameObject go) { var b = Bounds(go, "_LOD0"); go.transform.position += Vector3.up * -b.min.y; }

        static void Glow(GameObject model, string piece, float value = 1)
        {
            foreach (var t in model.GetComponentsInChildren<Transform>(true).Where(t => t.name.EndsWith(piece) && t.GetComponent<LODGroup>() != null))
                t.gameObject.AddComponent<HerbGlow>().Glow = value;
        }

        // Field herbs: one prefab per grade cut from MK02's Plant<Grade> group, pivot at the root tips.
        static GameObject HerbPrefab(string grade)
        {
            var piece = "_Plant" + char.ToUpper(grade[0]) + grade.Substring(1);
            var go = PieceCopy("MK02_HarvestSieve", piece, "Herb_" + grade, null, Vector3.zero);
            if (grade == "top") go.AddComponent<HerbGlow>();
            var path = $"{Root}/Herb_{grade}.prefab";
            var prefab = PrefabUtility.SaveAsPrefabAsset(go, path); UnityEngine.Object.DestroyImmediate(go);
            return prefab;
        }

        static GameObject CoinPrefab()
        {
            var go = PieceCopy("MK03_PriceBoard", "_CoinString", "MK03_CoinString", null, Vector3.zero);
            var prefab = PrefabUtility.SaveAsPrefabAsset(go, $"{Root}/MK03_CoinString.prefab"); UnityEngine.Object.DestroyImmediate(go);
            return prefab;
        }

        // A single exported group (its LOD0–2 meshes and LODGroup) lifted out of a model, with its own pivot at the origin.
        static GameObject PieceCopy(string id, string piece, string name, Transform parent, Vector3 local)
        {
            var model = Place(id, "tmp_" + id, null, Vector3.zero, 0);
            var host = model.GetComponentsInChildren<Transform>(true).First(t => t.name == id + piece && t.GetComponent<LODGroup>() != null);
            var go = new GameObject(name); if (parent != null) go.transform.SetParent(parent, false);
            go.transform.localPosition = local;
            host.SetParent(go.transform, false); host.localPosition = Vector3.zero; host.localRotation = Quaternion.identity;
            foreach (Transform lod in host) lod.localPosition = Vector3.zero;
            UnityEngine.Object.DestroyImmediate(model);
            return go;
        }

        static Transform Find(Transform root, string name) =>
            root.GetComponentsInChildren<Transform>(true).FirstOrDefault(t => t.name == name) ?? throw new InvalidDataException($"{root.name} has no {name}");

        static Bounds Bounds(GameObject go, string suffix)
        {
            var rs = go.GetComponentsInChildren<Renderer>().Where(r => r.name.EndsWith(suffix)).ToArray();
            if (rs.Length == 0) rs = go.GetComponentsInChildren<Renderer>();
            var b = rs[0].bounds; foreach (var r in rs) b.Encapsulate(r.bounds); return b;
        }

        static GameObject Marker(string name, Transform parent, Vector3 local) { var go = new GameObject(name); go.transform.SetParent(parent, false); go.transform.localPosition = local; return go; }

        static Transform View(string name, Transform parent, Vector3 eye, Vector3 target)
        {
            var t = new GameObject(name).transform; t.SetParent(parent); t.position = eye; t.rotation = Quaternion.LookRotation(target - eye); return t;
        }

        static Material Flat(string name, Color color, float smooth = .2f)
        {
            var path = $"{Root}/{name}.mat"; var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (mat == null) { mat = new Material(Shader.Find("Universal Render Pipeline/Lit")); AssetDatabase.CreateAsset(mat, path); }
            mat.SetColor("_BaseColor", color); mat.SetFloat("_Smoothness", smooth); EditorUtility.SetDirty(mat); return mat;
        }

        // Indigo homespun for the sort cloth: uneven threads both ways, a fine over-under weave, a little fading.
        // Tiles every 50 cm (4 mm threads, slubs a few threads wide so they still read at arm's length); written once to Generated/ as a PNG so the player build packs it like any texture.
        static Material Linen()
        {
            var path = $"{Root}/SortCloth_Linen.png";
            if (AssetDatabase.LoadAssetAtPath<Texture2D>(path) == null)
            {
                const int N = 512; var rnd = new System.Random(7); var tex = new Texture2D(N, N, TextureFormat.RGB24, false);
                float[] warp = new float[N / 4], weft = new float[N / 4];
                for (int i = 0; i < N / 4; i++) { warp[i] = (Mathf.PerlinNoise(i / 5f, .3f) - .5f) * .3f + (float)(rnd.NextDouble() - .5) * .08f; weft[i] = (Mathf.PerlinNoise(.7f, i / 5f) - .5f) * .3f + (float)(rnd.NextDouble() - .5) * .08f; }
                var px = new Color[N * N]; var indigo = new Color(.16f, .19f, .27f);
                for (int y = 0; y < N; y++) for (int x = 0; x < N; x++)
                {
                    bool over = ((x / 4) + (y / 4)) % 2 == 0;   // 4 px threads, plain weave
                    float v = 1 + (over ? warp[x / 4] : weft[y / 4]) + (over ? .06f : -.06f);
                    v += Mathf.PerlinNoise(x / 96f, y / 96f) * .14f - .07f;   // soft fading
                    px[y * N + x] = indigo * v;
                }
                tex.SetPixels(px); tex.Apply();
                File.WriteAllBytes(Path.Combine(Repo, "apps", "game", path), tex.EncodeToPNG()); UnityEngine.Object.DestroyImmediate(tex);
                AssetDatabase.ImportAsset(path);
            }
            var mat = Flat("SortCloth", Color.white, .05f);
            mat.SetTexture("_BaseMap", AssetDatabase.LoadAssetAtPath<Texture2D>(path)); mat.SetTextureScale("_BaseMap", new Vector2(6.4f, 5.2f));   // 3.2 × 2.6 m / 0.5 m
            EditorUtility.SetDirty(mat); return mat;
        }

        static GameObject Box(Transform parent, string name, Vector3 pos, Vector3 size, Material mat)
        {
            var go = GameObject.CreatePrimitive(PrimitiveType.Cube); go.name = name; go.transform.SetParent(parent, false);
            go.transform.position = pos; go.transform.localScale = size; go.GetComponent<Renderer>().sharedMaterial = mat; return go;
        }

        static void BuildLighting(Transform world)
        {
            RenderSettings.ambientMode = AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = new Color(.62f, .68f, .7f); RenderSettings.ambientEquatorColor = new Color(.45f, .44f, .38f); RenderSettings.ambientGroundColor = new Color(.2f, .18f, .14f);
            RenderSettings.fog = true; RenderSettings.fogMode = FogMode.Linear; RenderSettings.fogStartDistance = 18; RenderSettings.fogEndDistance = 60; RenderSettings.fogColor = new Color(.78f, .83f, .8f);
            var cam = Camera.main; if (cam != null) { cam.clearFlags = CameraClearFlags.SolidColor; cam.backgroundColor = new Color(.74f, .82f, .82f); }
            var sun = new GameObject("Sun").AddComponent<Light>(); sun.type = LightType.Directional; sun.intensity = 1.25f; sun.transform.SetParent(world);
            sun.color = new Color(1, .94f, .84f); sun.transform.rotation = Quaternion.Euler(48, -35, 0); sun.shadows = LightShadows.Soft;
            var profilePath = $"{Root}/HarvestVolume.asset";
            var profile = AssetDatabase.LoadAssetAtPath<VolumeProfile>(profilePath);
            if (profile == null) { profile = ScriptableObject.CreateInstance<VolumeProfile>(); AssetDatabase.CreateAsset(profile, profilePath); }
            if (!profile.TryGet<Bloom>(out var bloom)) bloom = profile.Add<Bloom>(true);
            bloom.intensity.Override(.6f); bloom.threshold.Override(1.0f); bloom.scatter.Override(.6f);
            if (!profile.TryGet<Tonemapping>(out var tone)) tone = profile.Add<Tonemapping>(true);
            tone.mode.Override(TonemappingMode.ACES);
            if (!profile.TryGet<ColorAdjustments>(out var color)) color = profile.Add<ColorAdjustments>(true);
            color.postExposure.Override(.3f); color.saturation.Override(8);
            EditorUtility.SetDirty(profile);
            var volume = new GameObject("Post volume").AddComponent<Volume>(); volume.isGlobal = true; volume.sharedProfile = profile; volume.transform.SetParent(world);
        }

        // ---------------------------------------------------------------- batch entry points

        [Serializable] class Kept { public string item, quality; public int quantity; }
        [Serializable] class FixBundle { public string bin, quality, line; public string[] grades; public bool sold, sorted; public int coins; }
        [Serializable] class FixCase { public string name, fieldId; public int day; public double[] pullSeconds; public string[] bins, plants, lines; public bool[] sell; public FixBundle[] bundles; public int totalCoins; public Kept[] kept; }
        [Serializable] class Fixture { public FixCase[] cases; }

        /// Replays every case of tests/fixtures/harvest-market-trace.json (written by the TS rules) through the C# port.
        public static void VerifySim()
        {
            var fixture = JsonUtility.FromJson<Fixture>(File.ReadAllText(Path.Combine(Repo, "tests", "fixtures", "harvest-market-trace.json")));
            if (fixture.cases == null || fixture.cases.Length == 0) throw new InvalidDataException("empty fixture");
            foreach (var c in fixture.cases)
            {
                var original = HarvestContent.FieldPlants(c.fieldId);
                var plants = original.Select((g, i) => HarvestRules.PullGrade(g, c.pullSeconds[i])).ToList();
                if (!plants.SequenceEqual(c.plants)) throw new InvalidDataException($"{c.name}: plants {string.Join(",", plants)} != {string.Join(",", c.plants)}");
                var bundles = HarvestRules.BundleUp(plants, c.bins);
                var s = HarvestRules.Settle(c.day, bundles, c.sell);
                if (s.bundles.Count != c.bundles.Length) throw new InvalidDataException($"{c.name}: {s.bundles.Count} bundles != {c.bundles.Length}");
                for (int i = 0; i < c.bundles.Length; i++)
                {
                    var a = s.bundles[i]; var e = c.bundles[i];
                    if (a.bin != e.bin || a.quality != e.quality || a.sold != e.sold || a.sorted != e.sorted || a.coins != e.coins || (a.line ?? "") != (e.line ?? "") || !a.grades.SequenceEqual(e.grades))
                        throw new InvalidDataException($"{c.name} bundle {i}: {a.bin}/{a.quality}/{a.sold}/{a.sorted}/{a.coins}/{a.line} != {e.bin}/{e.quality}/{e.sold}/{e.sorted}/{e.coins}/{e.line}");
                }
                if (s.totalCoins != c.totalCoins) throw new InvalidDataException($"{c.name}: total {s.totalCoins} != {c.totalCoins}");
                if (!s.lines.SequenceEqual(c.lines)) throw new InvalidDataException($"{c.name}: lines {string.Join(",", s.lines)} != {string.Join(",", c.lines)}");
                var kept = s.kept.Select(k => $"{k.quality}x{k.quantity}"); var want = (c.kept ?? new Kept[0]).Select(k => $"{k.quality}x{k.quantity}");
                if (!kept.SequenceEqual(want)) throw new InvalidDataException($"{c.name}: kept {string.Join(",", kept)} != {string.Join(",", want)}");
            }
            Debug.Log($"HARVEST_SIM_PARITY_PASS {fixture.cases.Length} cases");
        }

        public static void Verify()
        {
            VerifySim(); Generate();
            UsePipeline();
            EditorSceneManager.OpenScene(Scene, OpenSceneMode.Single);
            var field = UnityEngine.Object.FindFirstObjectByType<QingxiHarvestPanel>(); var sell = UnityEngine.Object.FindFirstObjectByType<QingxiMarketSellPanel>();
            if (field == null || sell == null || sell.scaleWeight == null || sell.coinStringPrefab == null || field.topPlant == null) throw new InvalidDataException("scene wiring incomplete");
            Debug.Log("HARVEST_VERIFY_PASS");
        }

        /// In-engine close-ups of every MK model in the generated scene (URP, scene lights, LODGroups active):
        /// artifacts/harvest-unity-shots/<name>.png at 1280×720. Run after Generate.
        public static void CaptureModels()
        {
            UsePipeline();
            EditorSceneManager.OpenScene(Scene, OpenSceneMode.Single);
            var cam = Camera.main; var dir = Path.Combine(Repo, "artifacts", "harvest-unity-shots"); Directory.CreateDirectory(dir);
            var rt = new RenderTexture(1280, 720, 24, RenderTextureFormat.ARGB32) { antiAliasing = 4 };
            void Shot(string file, GameObject target, Vector3 offset, float fov = 35)
            {
                var b = Bounds(target, "_LOD0"); var c = b.center;
                cam.transform.position = c + offset; cam.transform.LookAt(c); cam.fieldOfView = fov; cam.targetTexture = rt;
                cam.Render(); RenderTexture.active = rt;
                var tex = new Texture2D(1280, 720, TextureFormat.RGB24, false); tex.ReadPixels(new Rect(0, 0, 1280, 720), 0, 0); tex.Apply();
                File.WriteAllBytes(Path.Combine(dir, file + ".png"), tex.EncodeToPNG()); UnityEngine.Object.DestroyImmediate(tex);
                RenderTexture.active = null; cam.targetTexture = null;
                Report.Add($"shot {file}");
            }
            GameObject Find(string n) => GameObject.Find(n) ?? throw new InvalidDataException("no " + n);
            Shot("MK01_on_stall", Find("MK01_Steelyard"), new Vector3(.35f, .05f, -1.25f));
            Shot("MK02_sieve_bundles", Find("MK02_SieveAndBundles"), new Vector3(.4f, 1.0f, -1.5f));
            Shot("MK03_board", Find("MK03_PriceBoard"), new Vector3(.25f, .2f, -1.3f));
            Shot("MK03_purse_coins", Find("MK03_Purse"), new Vector3(.15f, .25f, -.55f));
            Shot("MK04_basket", Find("MK04_Basket"), new Vector3(.7f, .45f, -1.1f));
            var field = UnityEngine.Object.FindFirstObjectByType<QingxiHarvestPanel>();
            var herbs = new GameObject("CaptureHerbs");
            foreach (var (g, x) in new[] { ("top", -.3f), ("mid", 0f), ("low", .3f) })
            {
                var h = (GameObject)PrefabUtility.InstantiatePrefab(field.PlantPrefab(g)); h.transform.SetParent(herbs.transform); h.transform.position = new Vector3(x, 0, -4.5f);
            }
            Shot("MK02_plants_top_mid_low", herbs, new Vector3(0, .25f, -1.0f), 30);
            UnityEngine.Object.DestroyImmediate(herbs);
            Debug.Log("HARVEST_CAPTURE_PASS " + dir);
        }

        // uGUI shaders are not referenced by any material asset, so player builds strip them.
        static void IncludeUiShaders()
        {
            var settings = new SerializedObject(AssetDatabase.LoadAllAssetsAtPath("ProjectSettings/GraphicsSettings.asset")[0]);
            var list = settings.FindProperty("m_AlwaysIncludedShaders");
            foreach (var name in new[] { "UI/Default", "Sprites/Default", "Universal Render Pipeline/Unlit" })
            {
                var shader = Shader.Find(name); if (shader == null) continue;
                bool present = false; for (int i = 0; i < list.arraySize; i++) if (list.GetArrayElementAtIndex(i).objectReferenceValue == shader) present = true;
                if (!present) { list.InsertArrayElementAtIndex(list.arraySize); list.GetArrayElementAtIndex(list.arraySize - 1).objectReferenceValue = shader; }
            }
            settings.ApplyModifiedPropertiesWithoutUndo(); AssetDatabase.SaveAssets();
        }

        public static void BuildWindows()
        {
            VerifySim(); Generate(); IncludeUiShaders();
            var path = Path.Combine(Repo, "artifacts", "harvest-windows", "YunJingHarvest.exe");
            Directory.CreateDirectory(Path.GetDirectoryName(path));
            var options = new BuildPlayerOptions { scenes = new[] { Scene }, target = BuildTarget.StandaloneWindows64, locationPathName = path, options = BuildOptions.Development };
            var report = BuildPipeline.BuildPlayer(options);
            if (report.summary.result != BuildResult.Succeeded) throw new Exception("Build failed: " + report.summary.result);
            Debug.Log("HARVEST_BUILD_PASS " + path + " " + report.summary.totalSize + " bytes");
        }
    }
}
