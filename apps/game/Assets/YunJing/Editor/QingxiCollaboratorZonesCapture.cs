using System.IO;
using System.Linq;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

namespace YunJing.Editor
{
    // Review renders of the generated novice village. Needs a graphics device (run Unity in
    // -batchmode without -nographics). Output: artifacts/qingxi-novice-village/*.png
    public static class QingxiCollaboratorZonesCapture
    {
        // Novice village review: an overview, the player's view from the gate and each zone.
        public static void CaptureVillage()
        {
            EditorSceneManager.OpenScene(QingxiNoviceVillageBuilder.ScenePath);
            var dir = Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", "..", "artifacts", "qingxi-novice-village"));
            Directory.CreateDirectory(dir);
            var camera = new GameObject("Review Camera").AddComponent<Camera>();
            camera.fieldOfView = 50; camera.nearClipPlane = .05f; camera.farClipPlane = 400;
            var target = new RenderTexture(1600, 900, 24) { antiAliasing = 4 };
            camera.targetTexture = target;
            void Shot(string file, Vector3 from, Vector3 at)
            {
                camera.transform.position = from; camera.transform.LookAt(at); camera.Render();
                RenderTexture.active = target;
                var image = new Texture2D(target.width, target.height, TextureFormat.RGB24, false);
                image.ReadPixels(new Rect(0, 0, target.width, target.height), 0, 0); image.Apply();
                File.WriteAllBytes(Path.Combine(dir, file + ".png"), image.EncodeToPNG());
                RenderTexture.active = null; Object.DestroyImmediate(image);
            }
            Shot("00-overview", new Vector3(0, 46, -46), new Vector3(0, 0, 2));
            Shot("01-gate-view", new Vector3(0, 1.7f, -25), new Vector3(0, 1.2f, 0));
            Shot("02-plaza-return-C", new Vector3(1.5f, 3.2f, -8), new Vector3(5.5f, .5f, -1));
            Shot("03-alchemy-B", new Vector3(-8, 4.5f, -6), new Vector3(-15, .6f, -2));
            Shot("04-training-yard", new Vector3(8, 5, -8), new Vector3(15, 1, -1));
            Shot("05-forest-A", new Vector3(0, 9, 4), new Vector3(0, 0, 20));
            Shot("06-forest-A-close", new Vector3(-4, 2.2f, 13), new Vector3(1, .6f, 22));
            Debug.Log($"QINGXI_VILLAGE_CAPTURED to {dir} (pipeline: {(GraphicsSettings.currentRenderPipeline != null ? GraphicsSettings.currentRenderPipeline.name : "built-in")})");
        }
    }
}
