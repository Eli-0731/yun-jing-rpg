using System.Collections;
using UnityEngine;

namespace YunJing.HarvestMarket
{
    /// Fixed views of the test scene (field, stall, sort station, weighing close-up) with a smooth move between them.
    /// Own file: a scene-serialised MonoBehaviour must live in a file of its name, or the player cannot load the scene.
    public sealed class HarvestCameraRig : MonoBehaviour
    {
        public Transform[] views;
        public IEnumerator MoveTo(int view, float seconds) => MoveTo(views[view].position, views[view].rotation, seconds);

        public IEnumerator MoveTo(Vector3 position, Quaternion rotation, float seconds)
        {
            Vector3 p0 = transform.position; Quaternion r0 = transform.rotation; float t = 0;
            while (t < seconds)
            {
                t += Time.deltaTime; float k = Mathf.SmoothStep(0, 1, t / seconds);
                transform.SetPositionAndRotation(Vector3.Lerp(p0, position, k), Quaternion.Slerp(r0, rotation, k));
                yield return null;
            }
            transform.SetPositionAndRotation(position, rotation);
        }

        /// A short decaying shake (a snapped root); the pose is restored afterwards.
        public static IEnumerator Shake(Transform cam, float seconds, float meters)
        {
            var home = cam.localPosition;
            for (float t = 0; t < seconds; t += Time.deltaTime)
            {
                cam.localPosition = home + Random.insideUnitSphere * meters * (1 - t / seconds);
                yield return null;
            }
            cam.localPosition = home;
        }
    }
}
