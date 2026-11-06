using UnityEngine;

namespace YunJing
{
    // Keeps a world-space label (planned-slot names in the novice village) turned toward the camera, upright,
    // so it never reads mirrored from behind.
    public sealed class QingxiBillboard : MonoBehaviour
    {
        void LateUpdate()
        {
            var cam = Camera.main;
            if (cam == null) return;
            var away = transform.position - cam.transform.position; away.y = 0;
            if (away.sqrMagnitude > .0001f) transform.rotation = Quaternion.LookRotation(away);
        }
    }
}
