using UnityEngine;
using UnityEngine.InputSystem;

namespace YunJing
{
    // Only the local walkthrough scene uses this controller. It has no API or inventory access.
    [RequireComponent(typeof(CharacterController))]
    public sealed class QingxiWalkthroughController : MonoBehaviour
    {
        CharacterController body;
        Vector3 entrance;
        Vector2 touchMove;
        float vertical;
        bool touchRun, queuedJump;
        public bool ScriptedWalkthrough { get; set; }

        void Awake()
        {
            body = GetComponent<CharacterController>();
            entrance = transform.position;
        }

        void Start()
        {
            Cultivator.TextInputFocused = false;
            Camera.main?.GetComponent<QingxiOrbitCamera>()?.SetTarget(transform);
        }

        void Update()
        {
            if (ScriptedWalkthrough) return;
            var input = touchMove;
            bool run = touchRun, jump = queuedJump;
            queuedJump = false;
            var keys = Keyboard.current;
            if (keys != null)
            {
                input += new Vector2((keys.dKey.isPressed ? 1 : 0) - (keys.aKey.isPressed ? 1 : 0),
                    (keys.wKey.isPressed ? 1 : 0) - (keys.sKey.isPressed ? 1 : 0));
                run |= keys.leftShiftKey.isPressed;
                jump |= keys.spaceKey.wasPressedThisFrame;
                if (keys.rKey.wasPressedThisFrame) ReturnToEntrance();
            }
            Step(input, run, jump, Mathf.Min(Time.deltaTime, .05f));
        }

        public void Step(Vector2 input, bool run, bool jump, float dt)
        {
            if (body == null || !float.IsFinite(dt) || dt <= 0) return;
            if (!float.IsFinite(input.x) || !float.IsFinite(input.y)) input = Vector2.zero;
            input = Vector2.ClampMagnitude(input, 1);
            var camera = Camera.main;
            if (camera != null) input = Cultivator.CameraRelativeDirection(input, camera.transform.forward, camera.transform.right);
            if (body.isGrounded)
            {
                if (vertical < 0) vertical = -2f;
                if (jump) vertical = Mathf.Sqrt(2f * 20f * 1.15f);
            }
            vertical = Mathf.Max(-25f, vertical - 20f * dt);
            var motion = new Vector3(input.x, 0, input.y);
            body.Move((motion * (run ? 6.2f : 4f) + Vector3.up * vertical) * dt);
            if (motion.sqrMagnitude > .001f)
                transform.rotation = Quaternion.RotateTowards(transform.rotation, Quaternion.LookRotation(motion), 540f * dt);
            if (transform.position.y < -10f) ReturnToEntrance();
        }

        public void ReturnToEntrance()
        {
            body.enabled = false;
            transform.SetPositionAndRotation(entrance, Quaternion.identity);
            body.enabled = true;
            vertical = 0;
            Camera.main?.GetComponent<QingxiOrbitCamera>()?.SetTarget(transform);
        }

        void OnGUI()
        {
            float scale = Mathf.Clamp(Screen.height / 720f, .7f, 1.5f);
            var previousMatrix = GUI.matrix;
            GUI.matrix = Matrix4x4.Scale(Vector3.one * scale);
            float height = Screen.height / scale;
            GUI.Box(new Rect(16, 16, 460, 72), "QINGXI - LOCAL WORLD WALKTHROUGH\nWASD: move | Shift: run | Space: jump | R: return\nRight mouse / right-side drag: look | Wheel: zoom");
            GUI.Label(new Rect(24, 90, 420, 28), "Explore only - no account, rewards or saved progress");
            touchMove = Vector2.zero;
            float y = height - 145;
            if (GUI.RepeatButton(new Rect(74, y, 54, 48), "W")) touchMove.y++;
            if (GUI.RepeatButton(new Rect(16, y + 52, 54, 48), "A")) touchMove.x--;
            if (GUI.RepeatButton(new Rect(74, y + 52, 54, 48), "S")) touchMove.y--;
            if (GUI.RepeatButton(new Rect(132, y + 52, 54, 48), "D")) touchMove.x++;
            touchRun = GUI.RepeatButton(new Rect(200, y + 52, 70, 48), "Run");
            if (GUI.Button(new Rect(200, y, 70, 48), "Jump")) queuedJump = true;
            GUI.matrix = previousMatrix;
        }
    }
}
