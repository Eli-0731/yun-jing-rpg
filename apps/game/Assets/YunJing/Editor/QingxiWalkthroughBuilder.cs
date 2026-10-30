using System;
using System.IO;
using FishNet.Managing;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace YunJing.Editor
{
    public static class QingxiWalkthroughBuilder
    {
        public const string ScenePath = "Assets/YunJing/Generated/QingxiWorldWalkthrough.unity";

        [MenuItem("Yun Jing/Generate local Qingxi walkthrough")]
        public static void Generate()
        {
            QingxiWorldBuilder.Generate();
            // Make a separate local scene. The network development scene remains rebuildable as before.
            var services = GameObject.Find("Qingxi services");
            if (services != null) UnityEngine.Object.DestroyImmediate(services);
            var actor = new GameObject("Local walkthrough traveler");
            actor.transform.position = new Vector3(0, 1, -7);
            var body = actor.AddComponent<CharacterController>();
            body.height = 1.75f; body.center = Vector3.up * .875f; body.radius = .30f;
            body.stepOffset = .28f; body.slopeLimit = 45; body.skinWidth = .03f;
            var visual = GameObject.CreatePrimitive(PrimitiveType.Capsule);
            visual.name = "Temporary traveler silhouette";
            visual.transform.SetParent(actor.transform, false);
            visual.transform.localPosition = Vector3.up * .875f;
            visual.transform.localScale = new Vector3(.6f, .875f, .6f);
            UnityEngine.Object.DestroyImmediate(visual.GetComponent<Collider>());
            visual.GetComponent<Renderer>().sharedMaterial = AssetDatabase.LoadAssetAtPath<Material>("Assets/YunJing/Generated/Robe.mat");
            actor.AddComponent<QingxiWalkthroughController>();
            actor.AddComponent<QingxiWalkthroughSmoke>();
            Camera.main.GetComponent<QingxiOrbitCamera>().SetTarget(actor.transform);
            PlayerSettings.fullScreenMode = FullScreenMode.Windowed;
            PlayerSettings.defaultScreenWidth = 1280; PlayerSettings.defaultScreenHeight = 720;
            EditorSceneManager.SaveScene(UnityEngine.SceneManagement.SceneManager.GetActiveScene(), ScenePath);
            ValidateScene();
            AssetDatabase.SaveAssets();
            Debug.Log("QINGXI_WALKTHROUGH_GENERATED: local scene, camera, traveler and world present; no account services.");
        }

        static void ValidateScene()
        {
            if (UnityEngine.Object.FindAnyObjectByType<NetworkManager>() != null || UnityEngine.Object.FindAnyObjectByType<GameApi>() != null)
                throw new InvalidOperationException("Local walkthrough must not contain network or account services.");
            if (UnityEngine.Object.FindAnyObjectByType<QingxiWalkthroughController>() == null || Camera.main == null)
                throw new InvalidOperationException("Walkthrough player or camera missing.");
            if (GameObject.Find("Qingxi listening terrace") == null || GameObject.Find("Qingxi stone bridge") == null)
                throw new InvalidOperationException("Walkthrough world landmarks missing.");
        }

        public static void BuildWindows()
        {
            // Generate in a previous Editor process: changing the active input
            // backend and building immediately can mismatch URP serialized layouts.
            if (!File.Exists(ScenePath)) throw new InvalidOperationException("Generate the walkthrough in a separate Editor process before building.");
            EditorSceneManager.OpenScene(ScenePath);
            ValidateScene();
            string path = "../../artifacts/windows-walkthrough/YunJingWalkthrough.exe";
            Directory.CreateDirectory(Path.GetDirectoryName(path));
            var report = BuildPipeline.BuildPlayer(new BuildPlayerOptions {
                scenes = new[] { ScenePath }, target = BuildTarget.StandaloneWindows64,
                // No development profiler connection: this walkthrough needs no network access.
                locationPathName = path, options = BuildOptions.None
            });
            if (report.summary.result != BuildResult.Succeeded) throw new InvalidOperationException("Walkthrough build failed.");
            Debug.Log("QINGXI_WALKTHROUGH_WINDOWS_BUILT: " + Path.GetFullPath(path));
        }
    }
}
