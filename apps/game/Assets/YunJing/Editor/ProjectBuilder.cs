using System;
using System.IO;
using FishNet.Component.Spawning;
using FishNet.Managing;
using FishNet.Managing.Object;
using FishNet.Managing.Transporting;
using FishNet.Object;
using FishNet.Transporting.Tugboat;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace YunJing.Editor
{
    public static class ProjectBuilder
    {
        const string Root = "Assets/YunJing/Generated";
        const string Scene = Root + "/Qingxi.unity";
        static Material Material(string name, Color color)
        {
            string path = Root + "/" + name + ".mat";
            var material = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (material == null) { material = new Material(Shader.Find("Universal Render Pipeline/Lit")); AssetDatabase.CreateAsset(material, path); }
            material.color = color; EditorUtility.SetDirty(material); return material;
        }
        static GameObject Box(string name, Vector3 position, Vector3 scale, Material material)
        {
            var obj = GameObject.CreatePrimitive(PrimitiveType.Cube); obj.name = name;
            obj.transform.position = position; obj.transform.localScale = scale;
            obj.GetComponent<Renderer>().sharedMaterial = material; return obj;
        }
        // Static art preview only: farming state is still presented by the API panel.
        static GameObject EstateModel(string asset, string name, Vector3 position, Vector3 colliderSize)
        {
            return IrrigationAssets.Place(asset, name, position, colliderSize);
        }
        [MenuItem("Yun Jing/Generate Qingxi development scene")]
        public static void Generate()
        {
            Directory.CreateDirectory(Root); AssetDatabase.Refresh();
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var renderer = AssetDatabase.LoadAssetAtPath<UniversalRendererData>(Root + "/Renderer.asset");
            if (renderer == null) { renderer = ScriptableObject.CreateInstance<UniversalRendererData>(); AssetDatabase.CreateAsset(renderer, Root + "/Renderer.asset"); }
            var pipeline = AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>(Root + "/URP.asset");
            if (pipeline == null) { pipeline = UniversalRenderPipelineAsset.Create(renderer); AssetDatabase.CreateAsset(pipeline, Root + "/URP.asset"); }
            pipeline.renderScale = 1; pipeline.shadowDistance = 35;
            GraphicsSettings.defaultRenderPipeline = pipeline; QualitySettings.renderPipeline = pipeline;
            var grass = Material("Moss", new Color(.23f, .35f, .28f));
            var stone = Material("Stone", new Color(.48f, .48f, .39f));
            var soil = Material("Earth", new Color(.26f, .20f, .13f));
            var plaster = Material("Plaster", new Color(.78f, .73f, .58f));
            var roof = Material("Roof", new Color(.13f, .23f, .24f));
            var water = Material("Water", new Color(.18f, .44f, .46f));
            Box("Courtyard ground", new Vector3(0,-.3f,0), new Vector3(30,.6f,26), grass);
            Box("Stone path", new Vector3(0,.02f,0), new Vector3(3,.1f,23), stone);
            Box("West wall", new Vector3(-14,1,0), new Vector3(.5f,2,26), stone);
            Box("East wall", new Vector3(14,1,0), new Vector3(.5f,2,26), stone);
            Box("North wall", new Vector3(0,1,12), new Vector3(28,2,.5f), stone);
            Box("Restored stream", new Vector3(8,.08f,0), new Vector3(1.3f,.15f,22), water);
            Box("Bridge", new Vector3(8,.3f,-3), new Vector3(4,.4f,2), stone);
            for (int i=0; i<4; i++) EstateModel("spirit-bed", "Spirit plot " + i,
                new Vector3(-6 + i%2*3,0,-5 + i/2*4), new Vector3(2.4f,.3f,3.2f));
            EstateModel("cistern", "Irrigation cistern (art preview)", new Vector3(-10,0,-5), new Vector3(2,1.1f,2));
            EstateModel("water-channel", "Irrigation channel (art preview)", new Vector3(-10,0,-2.8f), new Vector3(.6f,.24f,2));
            for (int i=0; i<2; i++)
            {
                float x = -7 + i*14;
                Box("House", new Vector3(x,1.6f,8), new Vector3(5,3.2f,4), plaster);
                var r = Box("Roof", new Vector3(x,3.6f,8), new Vector3(6,.5f,5), roof); r.transform.rotation = Quaternion.Euler(0,0,6);
                Box("Door", new Vector3(x,1,5.98f), new Vector3(1.2f,2,.1f), roof);
            }
            Box("Broken array", new Vector3(10,.4f,5), new Vector3(2,.8f,2), stone);
            Box("Lotus bed", new Vector3(10,.15f,-6), new Vector3(2,.3f,2), soil);
            Box("Beast sanctuary", new Vector3(-10,.3f,1), new Vector3(3,.6f,3), soil);
            var furnace = GameObject.CreatePrimitive(PrimitiveType.Cylinder); furnace.name = "Alchemy furnace";
            furnace.transform.position = new Vector3(-5,1,4); furnace.GetComponent<Renderer>().sharedMaterial = roof;
            var sun = new GameObject("Morning sun").AddComponent<Light>(); sun.type = LightType.Directional; sun.intensity = 1.5f;
            sun.transform.rotation = Quaternion.Euler(48,-30,0); sun.shadows = LightShadows.Soft;
            RenderSettings.ambientLight = new Color(.55f,.62f,.63f); RenderSettings.fog = true;
            RenderSettings.fogColor = new Color(.65f,.73f,.72f); RenderSettings.fogDensity = .012f;
            var camera = new GameObject("Main Camera", typeof(Camera), typeof(AudioListener)).GetComponent<Camera>(); camera.tag = "MainCamera";
            camera.transform.position = new Vector3(0,14,-19); camera.transform.LookAt(Vector3.zero); camera.farClipPlane=150;
            var actor = new GameObject("Cultivator"); actor.transform.position = new Vector3(0,1,-7);
            var capsule = GameObject.CreatePrimitive(PrimitiveType.Capsule); capsule.transform.SetParent(actor.transform,false);
            UnityEngine.Object.DestroyImmediate(capsule.GetComponent<Collider>()); capsule.transform.localPosition = Vector3.up;
            capsule.GetComponent<Renderer>().sharedMaterial = Material("Robe", new Color(.35f,.66f,.60f));
            var controller = actor.AddComponent<CharacterController>(); controller.height=2; controller.center=Vector3.up; controller.radius=.35f;
            var nob = actor.AddComponent<NetworkObject>(); actor.AddComponent<Cultivator>();
            var serialized = new SerializedObject(nob); serialized.FindProperty("_enablePrediction").boolValue = true;
            serialized.ApplyModifiedPropertiesWithoutUndo();
            var prefab = PrefabUtility.SaveAsPrefabAsset(actor, Root + "/Cultivator.prefab"); UnityEngine.Object.DestroyImmediate(actor);
            var prefabs = AssetDatabase.LoadAssetAtPath<DefaultPrefabObjects>(Root + "/Spawnables.asset");
            if (prefabs == null) { prefabs = ScriptableObject.CreateInstance<DefaultPrefabObjects>(); AssetDatabase.CreateAsset(prefabs, Root + "/Spawnables.asset"); }
            prefabs.AddObject(prefab.GetComponent<NetworkObject>(), true); EditorUtility.SetDirty(prefabs);
            var services = new GameObject("Qingxi services"); var tugboat = services.AddComponent<Tugboat>();
            services.AddComponent<TransportManager>().Transport = tugboat;
            var manager = services.AddComponent<NetworkManager>(); manager.SpawnablePrefabs = prefabs;
            services.AddComponent<GameApi>(); services.AddComponent<TicketAuthenticator>(); services.AddComponent<QingxiClient>();
            services.AddComponent<PlayerSpawner>().SetPlayerPrefab(prefab.GetComponent<NetworkObject>());
            PlayerSettings.companyName = "YunJing"; PlayerSettings.productName = "雲境 · 青溪開發版";
            PlayerSettings.defaultInterfaceOrientation = UIOrientation.LandscapeLeft;
            // This sample is loopback-only; production must use HTTPS and disable insecure HTTP.
            PlayerSettings.insecureHttpOption = InsecureHttpOption.DevelopmentOnly;
            var settings = new SerializedObject(AssetDatabase.LoadAllAssetsAtPath("ProjectSettings/ProjectSettings.asset")[0]);
            settings.FindProperty("activeInputHandler").intValue = 1; settings.ApplyModifiedPropertiesWithoutUndo();
            EditorSceneManager.SaveScene(scene, Scene);
            EditorBuildSettings.scenes = new[] { new EditorBuildSettingsScene(Scene,true) };
            AssetDatabase.SaveAssets();
        }
        public static void BuildWindows() => Build(BuildTarget.StandaloneWindows64,"../../artifacts/windows/YunJing.exe");
        public static void BuildAndroid() => Build(BuildTarget.Android,"../../artifacts/android/YunJing.apk");
        public static void BuildLinuxServer() => Build(BuildTarget.StandaloneLinux64,"../../artifacts/linux/YunJing",true);
        static void Build(BuildTarget target, string path, bool server=false)
        {
            if (!File.Exists(Scene)) Generate();
            Directory.CreateDirectory(Path.GetDirectoryName(path));
            var options = new BuildPlayerOptions { scenes = new[] { Scene }, target = target, locationPathName = path, options = BuildOptions.Development };
            if (server) options.subtarget = (int)StandaloneBuildSubtarget.Server;
            BuildReport report = BuildPipeline.BuildPlayer(options);
            if (report.summary.result != BuildResult.Succeeded) throw new Exception("Build failed: " + report.summary.result);
        }
    }
}
