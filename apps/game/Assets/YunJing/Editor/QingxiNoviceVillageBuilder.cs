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
    // A small, flat novice village for reviewing the collaborators' complete deliveries without the
    // larger world's terrain, trees and buildings in the way:
    //   south  village gate (spawn)          centre  plaza, Eli-0731's notice board and return corner (C)
    //   west   joshsu54's alchemy corner (B), door into his AlchemyRoom scene
    //   east   Johnnnny0823's training yard  north   Johnnnny0823's forest rabbit encounter (A)
    // Ground, paths and the herb markers are graybox placeholders and are named so.
    public static class QingxiNoviceVillageBuilder
    {
        public const string ScenePath = "Assets/YunJing/Generated/QingxiNoviceVillage.unity";
        const string AlchemyScenePath = "Assets/YunJing/Generated/AlchemyRoom.unity";
        const string MaterialFolder = "Assets/QingxiWorld/Generated/Materials/Collaborators";

        [MenuItem("Yun Jing/Generate Qingxi novice village")]
        public static void Generate()
        {
            QingxiUrpUpgrade.EnsurePipeline();
            Directory.CreateDirectory(MaterialFolder);
            Directory.CreateDirectory(Path.GetDirectoryName(ScenePath));
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var village = new GameObject("QingxiNoviceVillage").transform;
            Lighting(village);
            Ground(village);

            var player = Player(village, new Vector3(0, 0, -22));
            var zones = QingxiCollaboratorZonesBuilder.PlaceAt(player,
                new Vector3(0, 0, 24), 0,                         // A: shelter (local -z) faces the plaza
                new Vector3(-15, 0, -2), Facing(new Vector3(-15, 0, -2), Vector3.zero),
                new Vector3(5.5f, 0, -1), Facing(new Vector3(5.5f, 0, -1), Vector3.zero));
            foreach (var zone in new[] { zones.forest, zones.alchemy, zones.ret }) zone.SetParent(village, true);

            var yard = TrainingYard(village, zones);
            var signs = Signs(village, zones);
            var herbs = Herbs(village);
            Scenery(village);

            var walker = player.GetComponent<global::QingxiWorld.QingxiFirstPerson>();
            var spots = new (string name, Vector3 at, Vector3 look)[] {
                ("村口", new Vector3(0, 0, -22), Vector3.zero),
                ("小廣場", new Vector3(0, 0, -6), new Vector3(0, 0, 10)),
                ("溪畔丹房", zones.alchemyDoor.position, zones.alchemy.position),
                ("演武區", yard.position + new Vector3(-4, 0, 0), yard.position),
                ("林地遭遇", zones.forest.Find("SafePoint_A09").position, zones.forest.Find("RabbitBurrow_A02").position),
                ("回村分揀桌", zones.returnTable.position, zones.ret.position),
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
            foraging.trainingSpot = yard;
            var stations = player.AddComponent<QingxiAbcStations>();
            stations.alchemyDoor = zones.alchemyDoor; stations.returnTable = zones.returnTable;
            stations.forest = zones.encounter; stations.walker = walker;
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
            Debug.Log($"QINGXI_NOVICE_VILLAGE_GENERATED: collaborator models={zones.models}, spots={spots.Length}, herbs={herbs.Length}, clues={foraging.clueNodes.Length}, URP copies={converted}\n" + string.Join("\n", zones.report));
            PrepareAlchemyRoom();
        }

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

        static void Ground(Transform village)
        {
            var grass = Surface("VillageGround_Placeholder", new Color(.38f, .5f, .3f));
            var dirt = Surface("VillagePath_Placeholder", new Color(.52f, .44f, .32f));
            var stone = Surface("VillagePlaza_Placeholder", new Color(.62f, .6f, .54f));
            var ground = GameObject.CreatePrimitive(PrimitiveType.Plane);
            ground.name = "Ground_Placeholder (graybox)"; ground.transform.SetParent(village, false);
            ground.transform.localScale = new Vector3(10, 1, 10);   // 100 x 100 m
            ground.GetComponent<Renderer>().sharedMaterial = grass;
            Slab(village, "Path_GateToForest_Placeholder", new Vector3(0, 0, 0), new Vector3(3, .04f, 46), dirt);
            Slab(village, "Path_Plaza_West_Placeholder", new Vector3(-7, 0, -2), new Vector3(14, .04f, 2.6f), dirt);
            Slab(village, "Path_Plaza_East_Placeholder", new Vector3(7, 0, -2), new Vector3(14, .04f, 2.6f), dirt);
            var plaza = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
            plaza.name = "Plaza_Placeholder (graybox)"; plaza.transform.SetParent(village, false);
            plaza.transform.localPosition = new Vector3(0, .03f, -2); plaza.transform.localScale = new Vector3(11, .03f, 11);
            plaza.GetComponent<Renderer>().sharedMaterial = stone;
            UnityEngine.Object.DestroyImmediate(plaza.GetComponent<Collider>());
            // Keep the traveller inside the review village.
            foreach (var (x, z, w, d) in new[] { (0f, 45f, 90f, 1f), (0f, -45f, 90f, 1f), (45f, 0f, 1f, 90f), (-45f, 0f, 1f, 90f) })
            {
                var wall = new GameObject("Boundary"); wall.transform.SetParent(village, false);
                wall.transform.localPosition = new Vector3(x, 2, z);
                wall.AddComponent<BoxCollider>().size = new Vector3(w, 4, d);
            }
        }

        static void Slab(Transform parent, string name, Vector3 at, Vector3 size, Material material)
        {
            var slab = GameObject.CreatePrimitive(PrimitiveType.Cube);
            slab.name = name; slab.transform.SetParent(parent, false);
            slab.transform.localPosition = at + Vector3.up * size.y / 2; slab.transform.localScale = size;
            slab.GetComponent<Renderer>().sharedMaterial = material;
            UnityEngine.Object.DestroyImmediate(slab.GetComponent<Collider>());
        }

        static GameObject Player(Transform village, Vector3 spawn)
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
        static Transform TrainingYard(Transform village, QingxiCollaboratorZonesBuilder.Result result)
        {
            var yard = new GameObject("CollaboratorZone_A_TrainingYard (Johnnnny0823)").transform;
            yard.SetParent(village, false); yard.position = new Vector3(15, 0, -2);
            yard.rotation = Quaternion.Euler(0, Facing(yard.position, Vector3.zero), 0);
            QingxiCollaboratorZonesBuilder.PlaceTrainingProp("training-shelter", yard, new Vector3(0, 0, 4), 180, result);
            QingxiCollaboratorZonesBuilder.PlaceTrainingProp("qi-striking-post", yard, new Vector3(-2.2f, 0, .5f), 0, result);
            QingxiCollaboratorZonesBuilder.PlaceTrainingProp("agility-post", yard, new Vector3(0, 0, .2f), 0, result);
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
                var model = QingxiCollaboratorZonesBuilder.PlaceConverted(QingxiCollaboratorZonesBuilder.SignModels, p.Item1, root, p.Item2, p.Item3, result);
                var marker = new GameObject("TrailClue_" + p.Item1).transform;
                marker.SetParent(root, false); marker.localPosition = p.Item2 + Quaternion.Euler(0, p.Item3, 0) * new Vector3(0, 0, -1.2f);
                return marker;
            }).ToArray();
        }

        // Placeholder herb clumps for the local foraging loop; no herb model has been delivered yet.
        static Transform[] Herbs(Transform village)
        {
            var leaf = Surface("VillageHerb_Placeholder", new Color(.32f, .62f, .38f));
            var root = new GameObject("HerbNodes_Placeholder (graybox)").transform; root.SetParent(village, false);
            return new[] { new Vector3(-8, 0, 12), new Vector3(8.5f, 0, 11), new Vector3(-11, 0, 4) }.Select((at, i) =>
            {
                var node = new GameObject($"HerbNode_0{i + 1}").transform; node.SetParent(root, false); node.localPosition = at;
                for (int k = 0; k < 5; k++)
                {
                    var blade = GameObject.CreatePrimitive(PrimitiveType.Capsule);
                    blade.name = "Placeholder_HerbBlade"; blade.transform.SetParent(node, false);
                    blade.transform.localPosition = Quaternion.Euler(0, k * 72, 0) * new Vector3(.14f, .2f, 0);
                    blade.transform.localRotation = Quaternion.Euler(18, k * 72, 0); blade.transform.localScale = new Vector3(.08f, .22f, .04f);
                    blade.GetComponent<Renderer>().sharedMaterial = leaf;
                    UnityEngine.Object.DestroyImmediate(blade.GetComponent<Collider>());
                }
                return node;
            }).ToArray();
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
            tree.transform.SetParent(parent, false); tree.transform.localPosition = at;
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
            if (!File.Exists(ScenePath) || !File.Exists(AlchemyScenePath)) throw new InvalidOperationException("Generate the novice village in a previous Editor process.");
            QingxiUrpUpgrade.EnsurePipeline();
            PlayerSettings.productName = "雲境 · 青溪新手村";
            string path = "../../artifacts/windows-novice-village/YunJingNoviceVillage.exe";
            Directory.CreateDirectory(Path.GetDirectoryName(path));
            var report = BuildPipeline.BuildPlayer(new BuildPlayerOptions {
                scenes = new[] { ScenePath, AlchemyScenePath }, target = BuildTarget.StandaloneWindows64,
                locationPathName = path, options = BuildOptions.None
            });
            if (report.summary.result != BuildResult.Succeeded) throw new InvalidOperationException("Novice village Windows build failed.");
            Debug.Log("QINGXI_NOVICE_VILLAGE_WINDOWS_BUILT: " + Path.GetFullPath(path));
        }
    }
}
