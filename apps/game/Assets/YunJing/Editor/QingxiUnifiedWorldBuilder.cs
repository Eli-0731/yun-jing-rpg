using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.AI;

namespace YunJing.Editor
{
    // First integration step: retain the larger town and hunt layout, then add
    // the original listening terrace at the town entrance. Both source builders
    // and their generated scenes remain available independently.
    public static class QingxiUnifiedWorldBuilder
    {
        public const string ScenePath = "Assets/QingxiWorld/Generated/QingxiUnifiedWorld.unity";
        const string TerracePath = "Assets/YunJing/Models/QingxiListeningTerraceV1/qingxi-listening-terrace-v1.fbx";
        const string CollaboratorFolder = "Assets/YunJing/Models/CollaboratorNoviceV1/";
        const string MaterialFolder = "Assets/QingxiWorld/Generated/Materials";

        [MenuItem("Yun Jing/Generate unified Qingxi world")]
        public static void Generate()
        {
            global::QingxiWorld.Editor.QingxiWorldBuilder.BuildAndTest();
            var townTerrain = GameObject.Find("Town_Terrain");
            var player = GameObject.Find("Player_FirstPerson");
            var source = AssetDatabase.LoadAssetAtPath<GameObject>(TerracePath);
            if (townTerrain == null || player == null || source == null)
                throw new InvalidOperationException("Unified world requires the larger town, player and listening terrace source.");

            var ground = TownGround(townTerrain.transform, -20f, 14f);
            var terrace = (GameObject)PrefabUtility.InstantiatePrefab(source);
            terrace.name = "Qingxi listening terrace - town entrance";
            terrace.transform.position = new Vector3(-20f, ground, 14f);
            terrace.transform.rotation = Quaternion.Euler(0, 90, 0);
            var stone = Surface("UnifiedTerraceStone", new Color(.68f, .67f, .58f));
            var dark = Surface("UnifiedTerraceFoundation", new Color(.42f, .46f, .43f));
            var timber = Surface("UnifiedTerraceTimber", new Color(.36f, .27f, .18f));
            var bronze = Surface("UnifiedTerraceBronze", new Color(.59f, .48f, .29f));
            var plant = Surface("UnifiedTerracePlant", new Color(.34f, .46f, .26f));
            foreach (var renderer in terrace.GetComponentsInChildren<Renderer>())
            {
                var name = renderer.gameObject.name;
                renderer.sharedMaterial = name.Contains("Bamboo") || name.Contains("Flower") || name.Contains("Grass") ? plant :
                    name.Contains("Bronze") || name.Contains("Bell") ? bronze :
                    name.Contains("Timber") || name.Contains("Seat") || name.Contains("Rope") ? timber :
                    name.Contains("Foundation") ? dark : stone;
            }
            int walkableParts = 0;
            foreach (var mesh in terrace.GetComponentsInChildren<MeshFilter>())
            {
                var name = mesh.gameObject.name;
                if (!name.Contains("Foundation") && !name.Contains("Paving") && !name.Contains("EntryStep")) continue;
                var collider = mesh.gameObject.AddComponent<MeshCollider>();
                collider.sharedMesh = mesh.sharedMesh;
                walkableParts++;
            }
            if (walkableParts == 0) throw new InvalidOperationException("Listening terrace has no walkable stone meshes.");

            var approach = ConnectEntrance(player, terrace.transform.position);
            var market = ConnectMarket(player);
            var collaboratorProps = PlaceCollaboratorNoviceModels();
            var hud = new GameObject("Qingxi Designed HUD").AddComponent<YunJing.QingxiHud>();
            hud.walker = player.GetComponent<global::QingxiWorld.QingxiFirstPerson>();
            hud.uiMaterial = UiSurface();
            var foraging = player.AddComponent<YunJing.QingxiLocalForaging>();
            foraging.herbNodes = hud.walker.pointsOfInterest.Where(p => p != null && p.name.StartsWith("HerbNode_")).ToArray();
            foraging.clueNodes = hud.walker.pointsOfInterest.Where(p => p != null && p.name.StartsWith("TrailClue_")).ToArray();
            foraging.marketEntrance = GameObject.Find("Entrance_MaterialShop").transform;
            foraging.trainingSpot = GameObject.Find("Entrance_ListeningTerrace").transform;
            if (foraging.herbNodes.Length == 0 || foraging.clueNodes.Length == 0)
                throw new InvalidOperationException("Herb and clue nodes are required for the local novice activity loop.");
            hud.walker.localForaging = foraging;
            hud.foraging = foraging;
            QingxiLocalForagingSmoke.Verify();

            PlayerSettings.fullScreenMode = FullScreenMode.Windowed;
            PlayerSettings.defaultScreenWidth = 1280;
            PlayerSettings.defaultScreenHeight = 720;
            ValidateScene();
            EditorSceneManager.SaveScene(UnityEngine.SceneManagement.SceneManager.GetActiveScene(), ScenePath);
            AssetDatabase.SaveAssets();
            Debug.Log($"QINGXI_UNIFIED_GENERATED: larger town + hunt + entrance terrace, terrain={ground:F2}m, walkable terrace parts={walkableParts}, plaza-to-entrance route={approach:F1}m, collaborator props={collaboratorProps}, local herb nodes={foraging.herbNodes.Length}, clue nodes={foraging.clueNodes.Length}");
        }

        // Visual placement only. These are authored collaborator meshes converted
        // from the reviewed GLBs; no client-side reward or interaction is added.
        static int PlaceCollaboratorNoviceModels()
        {
            var townSpawn = GameObject.Find("PlayerSpawn_Town");
            var market = GameObject.Find("Entrance_MaterialShop");
            var terrain = GameObject.Find("Town_Terrain");
            var navData = AssetDatabase.LoadAssetAtPath<NavMeshData>("Assets/QingxiWorld/Generated/NavMesh_Player.asset");
            if (townSpawn == null || market == null || terrain == null || navData == null)
                throw new InvalidOperationException("Collaborator placement requires town spawn, market and terrain.");
            var root = new GameObject("CollaboratorNoviceLocations").transform;
            int count = 0;
            using (var nav = new NavScope(navData))
            {
                var locations = new[] {
                    ("village-board", "Eli-0731", townSpawn.transform.position + new Vector3(2, 0, -2), 1.8f),
                    ("training-shelter", "Johnnnny0823", townSpawn.transform.position + new Vector3(8, 0, -5), 3.0f),
                    ("return-table", "Eli-0731", market.transform.position + new Vector3(3, 0, -2), .75f),
                    ("alchemy-furnace", "joshsu54", market.transform.position + new Vector3(5, 0, -3), .92f),
                };
                foreach (var location in locations)
                {
                    var source = AssetDatabase.LoadAssetAtPath<GameObject>(CollaboratorFolder + location.Item1 + ".fbx");
                    if (source == null) throw new InvalidOperationException("Missing collaborator model: " + location.Item1);
                    if (!NavMesh.SamplePosition(location.Item3, out var spot, 5f, NavMesh.AllAreas))
                        throw new InvalidOperationException("No town walking ground near " + location.Item1);
                    var placed = (GameObject)PrefabUtility.InstantiatePrefab(source);
                    placed.name = location.Item1 + " - by " + location.Item2;
                    placed.transform.SetParent(root, true);
                    placed.transform.position = spot.position;
                    var renderers = placed.GetComponentsInChildren<Renderer>();
                    if (renderers.Length == 0) throw new InvalidOperationException("No renderer in " + location.Item1);
                    var bounds = renderers[0].bounds;
                    foreach (var renderer in renderers.Skip(1)) bounds.Encapsulate(renderer.bounds);
                    placed.transform.localScale *= location.Item4 / Mathf.Max(.001f, bounds.size.y);
                    bounds = placed.GetComponentsInChildren<Renderer>()[0].bounds;
                    foreach (var renderer in placed.GetComponentsInChildren<Renderer>().Skip(1)) bounds.Encapsulate(renderer.bounds);
                    placed.transform.position += Vector3.up * (spot.position.y - bounds.min.y);
                    count++;
                }
            }
            return count;
        }

        static float ConnectEntrance(GameObject player, Vector3 terraceCenter)
        {
            var source = AssetDatabase.LoadAssetAtPath<NavMeshData>("Assets/QingxiWorld/Generated/NavMesh_Player.asset");
            if (source == null) throw new InvalidOperationException("Larger-town player NavMesh is missing.");
            var walker = player.GetComponent<global::QingxiWorld.QingxiFirstPerson>();
            if (walker == null) throw new InvalidOperationException("Larger-town local traveler is missing.");
            var townSpawn = GameObject.Find("PlayerSpawn_Town");
            if (townSpawn == null) throw new InvalidOperationException("Larger-town plaza spawn is missing.");

            using (var nav = new NavScope(source))
            {
                if (!NavMesh.SamplePosition(townSpawn.transform.position, out var start, 2f, NavMesh.AllAreas))
                    throw new InvalidOperationException("Plaza spawn is outside the player NavMesh.");
                NavMeshPath bestPath = null;
                Vector3 entry = Vector3.zero;
                float bestLength = float.MaxValue;
                // The terrace is a reused FBX with several stairs. Search the
                // surrounding walkable town ground rather than assuming its pivot
                // marks the entrance or teleporting the player into masonry.
                foreach (var offset in new[] {
                    new Vector3(0, 0, -5), new Vector3(-5, 0, 0),
                    new Vector3(5, 0, 0), new Vector3(0, 0, 5)
                })
                {
                    var candidate = terraceCenter + offset;
                    if (!NavMesh.SamplePosition(candidate, out var end, 2f, NavMesh.AllAreas)) continue;
                    var path = new NavMeshPath();
                    if (!NavMesh.CalculatePath(start.position, end.position, NavMesh.AllAreas, path) ||
                        path.status != NavMeshPathStatus.PathComplete) continue;
                    float length = 0;
                    for (int i = 1; i < path.corners.Length; i++)
                        length += Vector3.Distance(path.corners[i - 1], path.corners[i]);
                    if (length >= bestLength) continue;
                    bestPath = path; bestLength = length; entry = end.position;
                }
                if (bestPath == null) throw new InvalidOperationException("No complete walking route from the plaza to the listening terrace approach.");

                var overlay = GameObject.Find("RouteTest_Lines");
                if (overlay != null)
                {
                    var route = new GameObject("Plaza_to_ListeningTerrace_Approach");
                    route.transform.SetParent(overlay.transform, false);
                    var line = route.AddComponent<LineRenderer>();
                    line.positionCount = bestPath.corners.Length;
                    line.SetPositions(bestPath.corners.Select(p => p + Vector3.up * .25f).ToArray());
                    line.startWidth = line.endWidth = .35f;
                    line.sharedMaterial = Surface("UnifiedTerraceRouteDebug", new Color(.18f, .66f, .73f));
                }

                var point = new GameObject("Entrance_ListeningTerrace");
                point.transform.position = entry;
                walker.spotNames = walker.spotNames.Concat(new[] { "聽風台入口" }).ToArray();
                walker.spotPositions = walker.spotPositions.Concat(new[] { entry }).ToArray();
                var look = terraceCenter - entry;
                walker.spotYaws = walker.spotYaws.Concat(new[] { Mathf.Atan2(look.x, look.z) * Mathf.Rad2Deg }).ToArray();
                walker.pointsOfInterest = walker.pointsOfInterest.Concat(new[] { point.transform }).ToArray();
                return bestLength;
            }
        }

        static float ConnectMarket(GameObject player)
        {
            var source = AssetDatabase.LoadAssetAtPath<NavMeshData>("Assets/QingxiWorld/Generated/NavMesh_Player.asset");
            var entrance = GameObject.Find("Entrance_ListeningTerrace");
            var townAssets = GameObject.Find("TownAssets");
            var shop = townAssets == null ? null : townAssets.transform.Cast<Transform>()
                .FirstOrDefault(t => t.name == "MaterialShop");
            var box = shop == null ? null : shop.GetComponent<BoxCollider>();
            var walker = player.GetComponent<global::QingxiWorld.QingxiFirstPerson>();
            if (source == null || entrance == null || box == null || walker == null)
                throw new InvalidOperationException("Cannot connect listening terrace to the existing material shop.");

            using (var nav = new NavScope(source))
            {
                if (!NavMesh.SamplePosition(entrance.transform.position, out var start, 2f, NavMesh.AllAreas))
                    throw new InvalidOperationException("Listening terrace entry is outside the player NavMesh.");
                var center = shop.TransformPoint(box.center);
                center.y = shop.position.y;
                var radius = Mathf.Max(box.size.x, box.size.z) * shop.lossyScale.x / 2f + 1.5f;
                NavMeshPath bestPath = null;
                Vector3 marketEntry = Vector3.zero;
                float bestLength = float.MaxValue;
                for (int i = 0; i < 16; i++)
                {
                    var probe = center + Quaternion.Euler(0, i * 22.5f, 0) * Vector3.forward * radius;
                    if (!NavMesh.SamplePosition(probe, out var end, 2f, NavMesh.AllAreas)) continue;
                    var path = new NavMeshPath();
                    if (!NavMesh.CalculatePath(start.position, end.position, NavMesh.AllAreas, path) ||
                        path.status != NavMeshPathStatus.PathComplete) continue;
                    float length = 0;
                    for (int j = 1; j < path.corners.Length; j++)
                        length += Vector3.Distance(path.corners[j - 1], path.corners[j]);
                    if (length >= bestLength) continue;
                    bestPath = path; bestLength = length; marketEntry = end.position;
                }
                if (bestPath == null)
                    throw new InvalidOperationException("No complete walking route from the listening terrace to the material shop.");

                var marker = new GameObject("Entrance_MaterialShop");
                marker.transform.position = marketEntry;
                walker.pointsOfInterest = walker.pointsOfInterest.Concat(new[] { marker.transform }).ToArray();
                var overlay = GameObject.Find("RouteTest_Lines");
                if (overlay != null)
                {
                    var route = new GameObject("ListeningTerrace_to_MaterialShop");
                    route.transform.SetParent(overlay.transform, false);
                    var line = route.AddComponent<LineRenderer>();
                    line.positionCount = bestPath.corners.Length;
                    line.SetPositions(bestPath.corners.Select(p => p + Vector3.up * .25f).ToArray());
                    line.startWidth = line.endWidth = .25f;
                    line.sharedMaterial = Surface("UnifiedMarketRouteDebug", new Color(.8f, .62f, .3f));
                }
                return bestLength;
            }
        }

        sealed class NavScope : IDisposable
        {
            readonly NavMeshDataInstance instance;
            public NavScope(NavMeshData data) { instance = NavMesh.AddNavMeshData(data); }
            public void Dispose() { if (instance.valid) instance.Remove(); }
        }

        static float TownGround(Transform terrain, float x, float z)
        {
            Physics.SyncTransforms();
            var hit = Physics.RaycastAll(new Vector3(x, 200, z), Vector3.down, 400)
                .Where(h => h.collider.transform.IsChildOf(terrain))
                .OrderBy(h => h.distance).FirstOrDefault();
            if (hit.collider == null) throw new InvalidOperationException("No larger-town terrain under entrance terrace.");
            return hit.point.y;
        }

        static Material Surface(string name, Color color)
        {
            string path = MaterialFolder + "/" + name + ".mat";
            var material = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (material == null)
            {
                var shader = Shader.Find("Universal Render Pipeline/Lit");
                if (shader == null) throw new InvalidOperationException("URP Lit shader unavailable.");
                material = new Material(shader);
                AssetDatabase.CreateAsset(material, path);
            }
            material.SetColor("_BaseColor", color);
            EditorUtility.SetDirty(material);
            return material;
        }

        static Material UiSurface()
        {
            string path = MaterialFolder + "/UnifiedHudUI.mat";
            var result = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (result != null) return result;
            var shader = Shader.Find("UI/Default");
            if (shader == null) throw new InvalidOperationException("Unity UI/Default shader unavailable.");
            result = new Material(shader);
            AssetDatabase.CreateAsset(result, path);
            return result;
        }

        static void ValidateScene()
        {
            if (GameObject.Find("Town") == null || GameObject.Find("HuntArea_rotated180") == null ||
                GameObject.Find("Qingxi listening terrace - town entrance") == null ||
                GameObject.Find("Entrance_MaterialShop") == null ||
                GameObject.Find("Player_FirstPerson") == null ||
                GameObject.Find("Qingxi Designed HUD") == null ||
                GameObject.Find("CollaboratorNoviceLocations") == null)
                throw new InvalidOperationException("Unified world is missing its town, hunt, terrace or local traveler.");
        }

        public static void BuildWindows()
        {
            if (!File.Exists(ScenePath)) throw new InvalidOperationException("Generate unified scene in a previous Editor process.");
            EditorSceneManager.OpenScene(ScenePath);
            ValidateScene();
            string path = "../../artifacts/windows-unified-world/YunJingUnifiedWorld.exe";
            Directory.CreateDirectory(Path.GetDirectoryName(path));
            var report = BuildPipeline.BuildPlayer(new BuildPlayerOptions {
                scenes = new[] { ScenePath }, target = BuildTarget.StandaloneWindows64,
                locationPathName = path, options = BuildOptions.None
            });
            if (report.summary.result != BuildResult.Succeeded) throw new InvalidOperationException("Unified Windows build failed.");
            Debug.Log("QINGXI_UNIFIED_WINDOWS_BUILT: " + Path.GetFullPath(path));
        }
    }
}
