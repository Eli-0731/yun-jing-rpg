using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

namespace YunJing.Editor
{
    // A small novice village for reviewing the collaborators' complete deliveries without the
    // larger world's terrain, trees and buildings in the way:
    //   south  village gate (spawn)          centre  plaza, Eli-0731's notice board and return corner (C)
    //   west   joshsu54's alchemy corner (B), door into his AlchemyRoom scene
    //   east   Johnnnny0823's training yard  north   Johnnnny0823's forest rabbit encounter (A)
    // The ground is a continuous terrain from tools/qingxi-terrain/novice-village.json (QingxiVillageTerrain);
    // every zone stands on a flat pad and everything else is dropped onto the terrain height.
    // The herb markers are graybox placeholders and are named so.
    public static class QingxiNoviceVillageBuilder
    {
        public const string ScenePath = "Assets/YunJing/Generated/QingxiNoviceVillage.unity";
        const string AlchemyScenePath = "Assets/YunJing/Generated/AlchemyRoom.unity";
        const string MaterialFolder = "Assets/QingxiWorld/Generated/Materials/Collaborators";
        static Terrain terrain;
        static QingxiVillageTerrain.Layout layout;
        const string GatheringModels = "Assets/YunJing/Models/GatheringB";   // copied from art/exports, gitignored

        static Vector3 At(float x, float z) => new Vector3(x, QingxiVillageTerrain.Ground(terrain, x, z), z);
        static Vector3 At(Vector3 p) => At(p.x, p.z);

        [MenuItem("Yun Jing/Generate Qingxi novice village")]
        public static void Generate()
        {
            QingxiUrpUpgrade.EnsurePipeline();
            // All village input (walker, encounter, drills, HUD, touch) uses the Input System package. With the
            // legacy-only handler (0) Keyboard.current and Mouse.current are null and nothing responds, in the
            // Windows player and the browser alike. Takes effect from the next Editor process (the build step).
            var settings = new SerializedObject(AssetDatabase.LoadAllAssetsAtPath("ProjectSettings/ProjectSettings.asset")[0]);
            settings.FindProperty("activeInputHandler").intValue = 1; settings.ApplyModifiedPropertiesWithoutUndo();
            AssetDatabase.SaveAssets();
            Directory.CreateDirectory(MaterialFolder);
            Directory.CreateDirectory(Path.GetDirectoryName(ScenePath));
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var village = new GameObject("QingxiNoviceVillage").transform;
            Lighting(village);
            terrain = QingxiVillageTerrain.Create(village);
            layout = QingxiVillageTerrain.Load();
            Physics.SyncTransforms();
            Boundary(village);

            var player = Player(village, At(0, -22));
            var zones = QingxiCollaboratorZonesBuilder.PlaceAt(player,
                At(0, 24), 0,                                     // A: shelter (local -z) faces the plaza
                At(-15, -2), Facing(new Vector3(-15, 0, -2), Vector3.zero),
                // C: north-east of the plaza, clear of the road to the training yard (z = -2).
                At(5.5f, 2.2f), Facing(new Vector3(5.5f, 0, 2.2f), Vector3.zero));
            foreach (var zone in new[] { zones.forest, zones.alchemy, zones.ret }) zone.SetParent(village, true);

            var yard = TrainingYard(village, zones);
            var signs = Signs(village, zones);
            var herbs = Herbs(village);
            var placed = Placements(village);
            Scenery(village);

            var walker = player.GetComponent<global::QingxiWorld.QingxiFirstPerson>();
            var spots = new (string name, Vector3 at, Vector3 look)[] {
                ("村口", At(0, -22), Vector3.zero),
                ("小廣場", At(0, -6), new Vector3(0, 0, 10)),
                ("溪畔丹房", zones.alchemyDoor.position, zones.alchemy.position),
                ("演武區", yard.position + new Vector3(-4, 0, 0), yard.position),
                ("林地遭遇", zones.forest.Find("SafePoint_A09").position, zones.forest.Find("RabbitBurrow_A02").position),
                ("回村分揀桌", zones.returnTable.position, zones.ret.position),
                ("坊市", At(-6, -14), At(-11, -15)),
                ("藥田", At(-18, -21), At(-25, -24)),
            };
            walker.spotNames = spots.Select(s => s.name).ToArray();
            walker.spotPositions = spots.Select(s => s.at).ToArray();
            walker.spotYaws = spots.Select(s => Mathf.Atan2(s.look.x - s.at.x, s.look.z - s.at.z) * Mathf.Rad2Deg).ToArray();
            walker.pointsOfInterest = signs.Concat(herbs).Concat(new[] { yard, zones.alchemyDoor, zones.returnTable }).ToArray();

            var hud = new GameObject("Qingxi Designed HUD").AddComponent<QingxiHud>();
            hud.walker = walker;
            hud.uiMaterial = UiMaterial();
            var foraging = player.AddComponent<QingxiLocalForaging>();
            foraging.herbNodes = herbs;
            foraging.clueNodes = signs.Skip(1).ToArray();   // Q02-Q04 are Eli-0731's clue signs; Q01 is the notice board
            foraging.trainingSpot = shelterSpot;
            // The herbal stall is the market: herbs and rabbits trade for practice stones there (local only).
            var market = new GameObject("MarketEntrance_HerbalStall").transform;
            market.SetParent(village, false); market.position = At(-7.5f, -14.5f);
            foraging.marketEntrance = market;
            foreach (var visual in herbs.Select(h => h.GetComponent<QingxiHerbVisual>()).Where(v => v != null)) visual.foraging = foraging;
            var stations = player.AddComponent<QingxiAbcStations>();
            stations.alchemyDoor = zones.alchemyDoor; stations.returnTable = zones.returnTable;
            stations.forest = zones.encounter; stations.walker = walker;
            var training = player.AddComponent<QingxiTrainingPractice>();
            training.qiPost = qiPost; training.blockPost = blockPost; training.walker = walker;
            stations.training = training;
            // The lodging's front door (west side, facing the road) leads into its interior scene.
            var lodgingDoor = new GameObject("LodgingDoor_StarterHouse").transform;
            lodgingDoor.SetParent(village, false); lodgingDoor.position = At(11.8f, -19.5f); lodgingDoor.rotation = Quaternion.Euler(0, 90, 0);
            stations.lodgingDoor = lodgingDoor;
            var touch = player.AddComponent<QingxiTouchControls>();
            touch.forest = zones.encounter; touch.training = training;
            var trainingParity = QingxiTrainingPracticeSmoke.Verify();
            foraging.abc = stations;
            walker.localForaging = foraging;
            hud.foraging = foraging; hud.forest = zones.encounter; hud.stations = stations;
            new GameObject("Qingxi ABC build smoke (--abc-smoke)").AddComponent<QingxiAbcSmoke>();

            var converted = QingxiUrpUpgrade.UpgradeSceneMaterials();
            PlayerSettings.fullScreenMode = FullScreenMode.Windowed;
            PlayerSettings.defaultScreenWidth = 1280;
            PlayerSettings.defaultScreenHeight = 720;
            EditorSceneManager.SaveScene(UnityEngine.SceneManagement.SceneManager.GetActiveScene(), ScenePath);
            AssetDatabase.SaveAssets();
            Debug.Log($"QINGXI_NOVICE_VILLAGE_GENERATED: collaborator models={zones.models}, placements={placed}, spots={spots.Length}, herbs={herbs.Length}, clues={foraging.clueNodes.Length}, URP copies={converted}, {trainingParity}\n" + string.Join("\n", zones.report));
            PrepareAlchemyRoom();
            QingxiLodgingInteriorBuilder.Generate();
        }

        static string[] Scenes => new[] { ScenePath, AlchemyScenePath, QingxiLodgingInteriorBuilder.ScenePath };

        static float Facing(Vector3 from, Vector3 target)
        {
            var toward = target - from;   // the zone's local -z (entrance side) points at the target
            return Mathf.Atan2(-toward.x, -toward.z) * Mathf.Rad2Deg;
        }

        // ------------------------------------------------------------------ ground, light, player
        static void Lighting(Transform village)
        {
            var sun = new GameObject("Sun").AddComponent<Light>();
            sun.transform.SetParent(village, false);
            sun.type = LightType.Directional; sun.intensity = 1.15f; sun.shadows = LightShadows.Soft; sun.color = new Color(1f, .95f, .86f);
            sun.transform.rotation = Quaternion.Euler(48, -35, 0);
            RenderSettings.sun = sun;
            RenderSettings.ambientMode = AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = new Color(.62f, .7f, .78f); RenderSettings.ambientEquatorColor = new Color(.55f, .58f, .52f); RenderSettings.ambientGroundColor = new Color(.32f, .3f, .26f);
            RenderSettings.fog = true; RenderSettings.fogMode = FogMode.Linear; RenderSettings.fogColor = new Color(.74f, .8f, .82f);
            RenderSettings.fogStartDistance = 45; RenderSettings.fogEndDistance = 110;
        }

        // Keep the traveller inside the review village; tall enough for the hills at the edge.
        static void Boundary(Transform village)
        {
            foreach (var (x, z, w, d) in new[] { (0f, 45f, 90f, 1f), (0f, -45f, 90f, 1f), (45f, 0f, 1f, 90f), (-45f, 0f, 1f, 90f) })
            {
                var wall = new GameObject("Boundary"); wall.transform.SetParent(village, false);
                wall.transform.localPosition = new Vector3(x, 5, z);
                wall.AddComponent<BoxCollider>().size = new Vector3(w, 12, d);
            }
        }

        internal static GameObject Player(Transform village, Vector3 spawn)
        {
            var player = new GameObject("Player_FirstPerson");
            player.transform.SetParent(village, false);
            player.transform.position = spawn + Vector3.up * .05f;
            var cc = player.AddComponent<CharacterController>(); cc.radius = .35f; cc.height = 1.4f; cc.center = Vector3.up * .7f; cc.slopeLimit = 35; cc.stepOffset = .3f; cc.skinWidth = .03f;
            var camGo = new GameObject("PlayerCamera") { tag = "MainCamera" }; camGo.transform.SetParent(player.transform, false); camGo.transform.localPosition = Vector3.up * 1.2f;
            var cam = camGo.AddComponent<Camera>(); cam.fieldOfView = 70; cam.nearClipPlane = .05f; cam.farClipPlane = 400; camGo.AddComponent<AudioListener>();
            // Original novice study mesh (saved AI three-view first); a walk-through avatar, not Heroine-01.
            var body = (GameObject)PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>("Assets/QingxiWorld/Models/ArtV001/NoviceCultivatorV1.fbx"));
            body.name = "Body_NoviceCultivatorV1"; body.transform.SetParent(player.transform, false);
            body.AddComponent<QingxiNoviceMotion>();
            var fp = player.AddComponent<global::QingxiWorld.QingxiFirstPerson>(); fp.cam = cam; fp.body = body;
            return player;
        }

        // ------------------------------------------------------------------ collaborator pieces outside the three kits
        static Transform qiPost, blockPost, shelterSpot;

        static Transform TrainingYard(Transform village, QingxiCollaboratorZonesBuilder.Result result)
        {
            var yard = new GameObject("CollaboratorZone_A_TrainingYard (Johnnnny0823)").transform;
            yard.SetParent(village, false); yard.position = At(15, -2);
            yard.rotation = Quaternion.Euler(0, Facing(yard.position, Vector3.zero), 0);
            QingxiCollaboratorZonesBuilder.PlaceTrainingProp("training-shelter", yard, new Vector3(0, 0, 4), 180, result);
            // His two posts run his drills (QingxiTrainingPractice); the core group's 引氣訣 moves under the shelter.
            qiPost = QingxiCollaboratorZonesBuilder.PlaceTrainingProp("qi-striking-post", yard, new Vector3(-2.2f, 0, .5f), 0, result).transform;
            blockPost = QingxiCollaboratorZonesBuilder.PlaceTrainingProp("agility-post", yard, new Vector3(0, 0, .2f), 0, result).transform;
            shelterSpot = new GameObject("TrainingSpot_Shelter").transform;
            shelterSpot.SetParent(yard, false); shelterSpot.localPosition = new Vector3(0, 0, 4.2f);
            QingxiCollaboratorZonesBuilder.PlaceTrainingProp("engraved-training-stone", yard, new Vector3(2.4f, 0, .4f), 200, result);
            QingxiCollaboratorZonesBuilder.PlaceTrainingProp("weapon-rack", yard, new Vector3(4, 0, 3), 270, result);
            QingxiCollaboratorZonesBuilder.PlaceTrainingProp("training-banner", yard, new Vector3(-3.8f, 0, -2.2f), 0, result);
            return yard;
        }

        static Transform[] Signs(Transform village, QingxiCollaboratorZonesBuilder.Result result)
        {
            var root = new GameObject("VillageSigns (Eli-0731)").transform; root.SetParent(village, false);
            var places = new[] {
                ("Q01", new Vector3(2.6f, 0, -12f), 0f),      // notice board at the plaza approach
                ("Q02", new Vector3(10.5f, 0, -6.5f), -60f),  // clue toward the training yard
                ("Q03", new Vector3(2.4f, 0, 9.5f), 180f),    // clue on the forest path
                ("Q04", new Vector3(-10.5f, 0, -6.5f), 60f),  // clue toward the alchemy corner
            };
            return places.Select(p =>
            {
                var model = QingxiCollaboratorZonesBuilder.PlaceConverted(QingxiCollaboratorZonesBuilder.SignModels, p.Item1, root, At(p.Item2), p.Item3, result);
                var marker = new GameObject("TrailClue_" + p.Item1).transform;
                marker.SetParent(root, false); marker.localPosition = At(p.Item2 + Quaternion.Euler(0, p.Item3, 0) * new Vector3(0, 0, -1.2f));
                return marker;
            }).ToArray();
        }

        // Herb nodes for the local foraging loop use joshsu54's gathering kit (QX_SpiritHerb_*): the "pre"
        // model until harvested, the "post" model until it regrows (QingxiHerbVisual).
        static Transform[] Herbs(Transform village)
        {
            CopyGathering();
            var root = new GameObject("HerbNodes (joshsu54 gathering kit)").transform; root.SetParent(village, false);
            return layout.herbs.Select(h =>
            {
                var node = new GameObject(h.id).transform; node.SetParent(root, false); node.localPosition = At(h.x, h.z);
                var visual = node.gameObject.AddComponent<QingxiHerbVisual>();
                visual.pre = HerbModel(h.kind, "pre", node);
                visual.post = HerbModel(h.kind, "post", node);
                visual.post.SetActive(false);
                return node;
            }).ToArray();
        }

        static GameObject HerbModel(string kind, string state, Transform node)
        {
            string key = $"QX_SpiritHerb_{kind}_{state}";
            var source = AssetDatabase.LoadAssetAtPath<GameObject>($"{GatheringModels}/{kind}/{key}.fbx");
            if (source == null) throw new FileNotFoundException("Gathering kit herb missing", key);
            var model = (GameObject)PrefabUtility.InstantiatePrefab(source);
            model.name = key + " - by joshsu54";
            model.transform.SetParent(node, false);
            var material = GatheringMaterial(kind, key);
            foreach (var r in model.GetComponentsInChildren<Renderer>()) r.sharedMaterials = Enumerable.Repeat(material, r.sharedMaterials.Length).ToArray();
            return model;
        }

        static Material GatheringMaterial(string kind, string key)
        {
            var path = $"{MaterialFolder}/{key}_URP.mat";
            var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (mat == null) { mat = new Material(Shader.Find("Universal Render Pipeline/Lit")); AssetDatabase.CreateAsset(mat, path); }
            string tex = $"{GatheringModels}/{kind}/textures/{key}_";
            var baseColor = AssetDatabase.LoadAssetAtPath<Texture2D>(tex + "BaseColor.png");
            if (baseColor == null) throw new FileNotFoundException("Gathering kit texture missing", tex + "BaseColor.png");
            mat.SetTexture("_BaseMap", baseColor); mat.SetColor("_BaseColor", Color.white); mat.SetFloat("_Smoothness", .15f);
            var normal = AssetDatabase.LoadAssetAtPath<Texture2D>(tex + "Normal.png");
            if (normal != null) { mat.SetTexture("_BumpMap", normal); mat.EnableKeyword("_NORMALMAP"); }
            var emission = AssetDatabase.LoadAssetAtPath<Texture2D>(tex + "Emission.png");
            if (emission != null) { mat.SetTexture("_EmissionMap", emission); mat.SetColor("_EmissionColor", Color.white * .6f); mat.EnableKeyword("_EMISSION"); }
            EditorUtility.SetDirty(mat);
            return mat;
        }

        // Copy the two herb kinds (pre/post FBX and textures) from art/exports into the gitignored model folder.
        static void CopyGathering()
        {
            string repo = Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", ".."));
            foreach (var kind in layout.herbs.Select(h => h.kind).Distinct())
            {
                var src = Path.Combine(repo, "art/exports/qingxi-gathering-visual-kit-v1", "QX_SpiritHerb_" + kind, "v001");
                var dst = Path.Combine(repo, "apps/game", GatheringModels, kind);
                foreach (var (from, to, pattern) in new[] { (src, dst, "*.fbx"), (Path.Combine(src, "textures"), Path.Combine(dst, "textures"), "*.png") })
                {
                    Directory.CreateDirectory(to);
                    foreach (var file in Directory.GetFiles(from, pattern))
                    {
                        if (new FileInfo(file).Length < 1024) throw new InvalidOperationException("Git LFS pointer instead of asset; run git lfs pull: " + file);
                        var target = Path.Combine(to, Path.GetFileName(file));
                        if (!File.Exists(target) || new FileInfo(target).Length != new FileInfo(file).Length) File.Copy(file, target, true);
                    }
                }
            }
            AssetDatabase.Refresh();
            foreach (var guid in AssetDatabase.FindAssets("t:Model", new[] { GatheringModels }))
            {
                var importer = (ModelImporter)AssetImporter.GetAtPath(AssetDatabase.GUIDToAssetPath(guid));
                if (importer.bakeAxisConversion && importer.materialImportMode == ModelImporterMaterialImportMode.None) continue;
                importer.bakeAxisConversion = true; importer.importAnimation = false; importer.importCameras = false; importer.importLights = false;
                importer.materialImportMode = ModelImporterMaterialImportMode.None;
                importer.SaveAndReimport();
            }
            foreach (var guid in AssetDatabase.FindAssets("t:Texture2D", new[] { GatheringModels }))
            {
                var path = AssetDatabase.GUIDToAssetPath(guid);
                var ti = (TextureImporter)AssetImporter.GetAtPath(path);
                bool normal = path.EndsWith("_Normal.png"), linear = normal || path.EndsWith("_Roughness.png");
                var type = normal ? TextureImporterType.NormalMap : TextureImporterType.Default;
                if (ti.textureType == type && ti.sRGBTexture == !linear && ti.maxTextureSize == 1024) continue;
                ti.textureType = type; ti.sRGBTexture = !linear; ti.maxTextureSize = 1024; ti.SaveAndReimport();
            }
        }

        // Buildings and props from the layout data: each stands on its pad at the terrain height and keeps
        // its FBX root rotation (Z-up exports carry an import rotation); only the yaw is added.
        static int Placements(Transform village)
        {
            var root = new GameObject("VillagePlacements (novice-village.json)").transform; root.SetParent(village, false);
            foreach (var p in layout.placements)
            {
                var source = AssetDatabase.LoadAssetAtPath<GameObject>(p.model);
                if (source == null) throw new FileNotFoundException("Village placement model missing (Git LFS pulled?)", p.model);
                var model = (GameObject)PrefabUtility.InstantiatePrefab(source);
                model.name = $"{p.id} - {p.author}";
                model.transform.SetParent(root, false);
                model.transform.localRotation = Quaternion.Euler(0, p.yaw, 0) * source.transform.localRotation;
                model.transform.localPosition = At(p.x, p.z);
                // Rest the visual base on the ground even when the FBX origin is not at the base.
                var renderers = model.GetComponentsInChildren<Renderer>();
                if (renderers.Length == 0) throw new InvalidDataException("No renderer in " + p.model);
                var b = renderers[0].bounds; foreach (var r in renderers) b.Encapsulate(r.bounds);
                model.transform.position += Vector3.up * (At(p.x, p.z).y - b.min.y);
                if (p.collider == "box")
                {
                    b = renderers[0].bounds; foreach (var r in renderers) b.Encapsulate(r.bounds);
                    var box = model.AddComponent<BoxCollider>();
                    box.center = model.transform.InverseTransformPoint(b.center);
                    var size = model.transform.InverseTransformVector(b.size);
                    box.size = new Vector3(Mathf.Abs(size.x), Mathf.Abs(size.y), Mathf.Abs(size.z));
                }
            }
            return layout.placements.Length;
        }

        // Existing reviewed environment pieces (CollaboratorWorldV1) framing the village edge.
        static void Scenery(Transform village)
        {
            var root = new GameObject("VillageEdgeTrees (CollaboratorWorldV1)").transform; root.SetParent(village, false);
            var pine = AssetDatabase.LoadAssetAtPath<GameObject>("Assets/YunJing/Models/CollaboratorWorldV1/CommonPine_v001.fbx");
            var bamboo = AssetDatabase.LoadAssetAtPath<GameObject>("Assets/YunJing/Models/CollaboratorWorldV1/BambooClump_v001.fbx");
            if (pine == null || bamboo == null) throw new InvalidOperationException("CollaboratorWorldV1 pine/bamboo models missing");
            var random = new System.Random(29);
            int n = 0;
            for (float angle = 0; angle < 360; angle += 15)
            {
                var r = 30 + (float)random.NextDouble() * 8;
                var at = Quaternion.Euler(0, angle, 0) * new Vector3(0, 0, r);
                if (Mathf.Abs(at.x) < 11 && at.z < 0) continue;   // keep the village gate approach open
                // ...and every pad, road and herb clear (the layout grew into the old ring).
                if (QingxiVillageTerrain.PadDistance(layout, at.x, at.z, out _) < 3f || QingxiVillageTerrain.RoadDistance(layout, at.x, at.z, out _) < 3f
                    || layout.herbs.Any(h => Vector2.Distance(new Vector2(h.x, h.z), new Vector2(at.x, at.z)) < 4f)) continue;
                Tree(n++ % 3 == 0 ? bamboo : pine, root, at, n % 3 == 0 ? 4.5f : 9f + (float)random.NextDouble() * 3, (float)random.NextDouble() * 360);
            }
            // a darker stand of pines behind the forest encounter
            foreach (var x in new[] { -13f, -10f, 10f, 13f, -6f, 6f })
                Tree(pine, root, new Vector3(x, 0, 30 + Mathf.Abs(x) * .3f), 10f, x * 31);
        }

        static void Tree(GameObject source, Transform parent, Vector3 at, float height, float yaw)
        {
            var tree = (GameObject)PrefabUtility.InstantiatePrefab(source);
            // Keep the FBX root's own axis rotation; only add the yaw.
            // Sink the trunk base slightly so it never shows a gap on sloped ground.
            tree.transform.SetParent(parent, false); tree.transform.localPosition = At(at) + Vector3.down * .15f;
            tree.transform.localRotation = Quaternion.Euler(0, yaw, 0) * source.transform.localRotation;
            var renderers = tree.GetComponentsInChildren<Renderer>();
            var b = renderers[0].bounds; foreach (var r in renderers) b.Encapsulate(r.bounds);
            tree.transform.localScale *= height / Mathf.Max(.01f, b.size.y);
        }

        static Material Surface(string name, Color color)
        {
            var path = $"{MaterialFolder}/{name}_URP.mat";
            var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (mat == null) { mat = new Material(Shader.Find("Universal Render Pipeline/Lit")); AssetDatabase.CreateAsset(mat, path); }
            mat.SetColor("_BaseColor", color); mat.SetFloat("_Smoothness", .08f);
            EditorUtility.SetDirty(mat);
            return mat;
        }

        static Material UiMaterial()
        {
            var path = MaterialFolder + "/VillageHudUI.mat";
            var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (mat == null) { mat = new Material(Shader.Find("UI/Default")); AssetDatabase.CreateAsset(mat, path); }
            return mat;
        }

        // ------------------------------------------------------------------ alchemy room link and build
        static void PrepareAlchemyRoom()
        {
            var productName = PlayerSettings.productName;
            AlchemyRoomBuilder.Generate();
            PlayerSettings.productName = productName;
            var scene = EditorSceneManager.OpenScene(AlchemyScenePath);
            new GameObject("Qingxi Return Door").AddComponent<QingxiSceneReturn>();
            if (!EditorSceneManager.SaveScene(scene, AlchemyScenePath)) throw new InvalidOperationException("Could not save " + AlchemyScenePath);
            Debug.Log("QINGXI_ALCHEMY_ROOM_LINKED: " + AlchemyScenePath);
        }

        public static void BuildWindows()
        {
            if (Scenes.Any(s => !File.Exists(s))) throw new InvalidOperationException("Generate the novice village in a previous Editor process.");
            QingxiUrpUpgrade.EnsurePipeline();
            PlayerSettings.productName = "雲境 · 青溪新手村";
            string path = "../../artifacts/windows-novice-village/YunJingNoviceVillage.exe";
            Directory.CreateDirectory(Path.GetDirectoryName(path));
            var report = BuildPipeline.BuildPlayer(new BuildPlayerOptions {
                scenes = Scenes, target = BuildTarget.StandaloneWindows64,
                locationPathName = path, options = BuildOptions.None
            });
            if (report.summary.result != BuildResult.Succeeded) throw new InvalidOperationException("Novice village Windows build failed.");
            Debug.Log("QINGXI_NOVICE_VILLAGE_WINDOWS_BUILT: " + Path.GetFullPath(path));
        }

        // Browser build with Unity's PWA template (web manifest, service worker, installable). Gzip with the
        // decompression fallback so any static server can host it; run tools/qingxi-webgl/serve.mjs to try it.
        public static void BuildWebGL()
        {
            if (Scenes.Any(s => !File.Exists(s))) throw new InvalidOperationException("Generate the novice village in a previous Editor process.");
            QingxiUrpUpgrade.EnsurePipeline();
            PlayerSettings.productName = "雲境 · 青溪新手村";
            PlayerSettings.WebGL.template = "APPLICATION:PWA";
            PlayerSettings.WebGL.compressionFormat = WebGLCompressionFormat.Gzip;
            PlayerSettings.WebGL.decompressionFallback = true;
            PlayerSettings.WebGL.dataCaching = true;
            PlayerSettings.WebGL.exceptionSupport = WebGLExceptionSupport.ExplicitlyThrownExceptionsOnly;
            PlayerSettings.WebGL.initialMemorySize = 256;
            PlayerSettings.runInBackground = true;
            string path = "../../artifacts/webgl-novice-village";
            Directory.CreateDirectory(path);
            var report = BuildPipeline.BuildPlayer(new BuildPlayerOptions {
                scenes = Scenes, target = BuildTarget.WebGL, locationPathName = path, options = BuildOptions.None
            });
            if (report.summary.result != BuildResult.Succeeded)
                throw new InvalidOperationException("Novice village WebGL build failed: " + string.Join("; ", report.steps.SelectMany(s => s.messages).Where(m => m.type == LogType.Error).Select(m => m.content).Take(5)));
            Debug.Log($"QINGXI_NOVICE_VILLAGE_WEBGL_BUILT: {Path.GetFullPath(path)} ({report.summary.totalSize / 1048576f:0.0} MB, {report.summary.totalTime.TotalMinutes:0.0} min)");
        }
    }
}
