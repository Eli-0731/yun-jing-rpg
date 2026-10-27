using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace YunJing.Editor
{
    // First integration step: retain the larger town and hunt layout, then add
    // the original listening terrace at the town entrance. Both source builders
    // and their generated scenes remain available independently.
    public static class QingxiUnifiedWorldBuilder
    {
        public const string ScenePath = "Assets/QingxiWorld/Generated/QingxiUnifiedWorld.unity";
        const string TerracePath = "Assets/YunJing/Models/QingxiListeningTerraceV1/qingxi-listening-terrace-v1.fbx";
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

            PlayerSettings.fullScreenMode = FullScreenMode.Windowed;
            PlayerSettings.defaultScreenWidth = 1280;
            PlayerSettings.defaultScreenHeight = 720;
            ValidateScene();
            EditorSceneManager.SaveScene(UnityEngine.SceneManagement.SceneManager.GetActiveScene(), ScenePath);
            AssetDatabase.SaveAssets();
            Debug.Log($"QINGXI_UNIFIED_GENERATED: larger town + hunt + entrance terrace, terrain={ground:F2}m, walkable terrace parts={walkableParts}");
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

        static void ValidateScene()
        {
            if (GameObject.Find("Town") == null || GameObject.Find("HuntArea_rotated180") == null ||
                GameObject.Find("Qingxi listening terrace - town entrance") == null ||
                GameObject.Find("Player_FirstPerson") == null)
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
