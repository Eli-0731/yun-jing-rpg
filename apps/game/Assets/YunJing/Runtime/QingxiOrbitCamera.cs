using UnityEngine;
using UnityEngine.InputSystem;

namespace YunJing
{
    // Local presentation only. Movement and rewards remain server-authoritative.
    public sealed class QingxiOrbitCamera : MonoBehaviour
    {
        [SerializeField] float distance = 6.5f;
        [SerializeField] float minDistance = 3.5f;
        [SerializeField] float maxDistance = 9f;
        [SerializeField] float pitch = 19f;
        [SerializeField] float yaw;
        [SerializeField] float mouseSensitivity = .18f;
        [SerializeField] float touchSensitivity = .12f;
        [SerializeField] LayerMask obstacles = ~0;

        Transform target;
        Vector3 focus;
        bool hasFocus;

        public void SetTarget(Transform value)
        {
            target = value;
            if (target == null) { hasFocus = false; return; }
            focus = target.position + Vector3.up * 1.45f;
            hasFocus = true;
            ApplyPosition(true);
        }

        void Update()
        {
            if (target == null) return;
            var mouse = Mouse.current;
            if (mouse != null)
            {
                if (mouse.rightButton.isPressed && !Cultivator.TextInputFocused)
                {
                    var delta = mouse.delta.ReadValue();
                    yaw += delta.x * mouseSensitivity;
                    pitch -= delta.y * mouseSensitivity;
                }
                distance -= mouse.scroll.ReadValue().y * .008f;
            }
            var touchscreen = Touchscreen.current;
            if (touchscreen != null)
            {
                foreach (var touch in touchscreen.touches)
                {
                    if (!touch.press.isPressed || touch.position.ReadValue().x < Screen.width * .5f) continue;
                    var delta = touch.delta.ReadValue();
                    yaw += delta.x * touchSensitivity;
                    pitch -= delta.y * touchSensitivity;
                }
            }
            pitch = Mathf.Clamp(pitch, -15f, 65f);
            distance = Mathf.Clamp(distance, minDistance, maxDistance);
        }

        void LateUpdate()
        {
            if (target == null) return;
            var desiredFocus = target.position + Vector3.up * 1.45f;
            focus = hasFocus ? Vector3.Lerp(focus, desiredFocus, 1 - Mathf.Exp(-12f * Time.deltaTime)) : desiredFocus;
            hasFocus = true;
            ApplyPosition(false);
        }

        void ApplyPosition(bool immediate)
        {
            var backward = Quaternion.Euler(pitch, yaw, 0) * Vector3.back;
            float allowedDistance = distance;
            foreach (var hit in Physics.SphereCastAll(focus, .22f, backward, distance, obstacles, QueryTriggerInteraction.Ignore))
            {
                if (target != null && hit.collider.transform.IsChildOf(target)) continue;
                allowedDistance = Mathf.Min(allowedDistance, Mathf.Max(.45f, hit.distance - .12f));
            }
            var desiredPosition = focus + backward * allowedDistance;
            transform.position = immediate ? desiredPosition :
                Vector3.Lerp(transform.position, desiredPosition, 1 - Mathf.Exp(-15f * Time.deltaTime));
            transform.rotation = Quaternion.LookRotation(focus - transform.position, Vector3.up);
        }
    }
}
