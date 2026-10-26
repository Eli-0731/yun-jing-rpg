using System;
using UnityEditor;
using UnityEngine;

namespace YunJing.Editor
{
    public static class QingxiCameraSmoke
    {
        // Invoke in batchmode to check the generated scene and camera-relative movement.
        public static void Verify()
        {
            AssertDirection(new Vector2(0, 1), Vector3.forward, Vector3.right, new Vector2(0, 1));
            AssertDirection(new Vector2(0, 1), Vector3.right, Vector3.back, new Vector2(1, 0));
            AssertDirection(new Vector2(1, 1), Vector3.forward, Vector3.right,
                new Vector2(.7071068f, .7071068f));

            ProjectBuilder.Generate();
            var camera = Camera.main;
            var orbit = camera == null ? null : camera.GetComponent<QingxiOrbitCamera>();
            if (orbit == null)
                throw new InvalidOperationException("The generated Qingxi scene has no orbit camera");
            var standIn = new GameObject("Camera smoke target");
            standIn.transform.position = new Vector3(0, 1, -7);
            orbit.SetTarget(standIn.transform);
            if (!float.IsFinite(camera.transform.position.x) || camera.transform.position.z >= standIn.transform.position.z)
                throw new InvalidOperationException("The orbit camera did not move behind its target");
            UnityEngine.Object.DestroyImmediate(standIn);
            orbit.SetTarget(null);
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>("Assets/YunJing/Generated/Cultivator.prefab");
            if (prefab == null || prefab.GetComponent<Cultivator>() == null)
                throw new InvalidOperationException("The generated Qingxi player prefab is missing");
            Debug.Log("Qingxi camera smoke passed: camera-relative movement and scene binding");
        }

        static void AssertDirection(Vector2 input, Vector3 forward, Vector3 right, Vector2 expected)
        {
            var actual = Cultivator.CameraRelativeDirection(input, forward, right);
            if (Vector2.Distance(actual, expected) > .001f)
                throw new InvalidOperationException($"Direction {input} became {actual}, expected {expected}");
        }
    }
}
