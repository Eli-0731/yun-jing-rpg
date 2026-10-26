using FishNet.Object.Prediction;
using FishNet.Transporting;
using FishNet.Utility.Template;
using UnityEngine;
using UnityEngine.InputSystem;

namespace YunJing
{
    [RequireComponent(typeof(CharacterController))]
    public sealed class Cultivator : TickNetworkBehaviour
    {
        public struct MoveData : IReplicateData
        {
            public Vector2 Direction; uint tick;
            public MoveData(Vector2 direction) { Direction = direction; tick = 0; }
            public uint GetTick() => tick; public void SetTick(uint value) => tick = value; public void Dispose() { }
        }
        public struct StateData : IReconcileData
        {
            public Vector3 Position; public Quaternion Rotation; public float Vertical; uint tick;
            public StateData(Vector3 position, Quaternion rotation, float vertical)
            { Position = position; Rotation = rotation; Vertical = vertical; tick = 0; }
            public uint GetTick() => tick; public void SetTick(uint value) => tick = value; public void Dispose() { }
        }
        public static Cultivator Local { get; private set; }
        public static Vector2 TouchInput;
        public static bool TextInputFocused;
        public static Vector2 CameraRelativeDirection(Vector2 input, Vector3 forward, Vector3 right)
        {
            forward.y = 0; right.y = 0;
            var planar = right.normalized * input.x + forward.normalized * input.y;
            return Vector2.ClampMagnitude(new Vector2(planar.x, planar.z), 1);
        }
        CharacterController controller; float vertical;
        void Awake() { controller = GetComponent<CharacterController>(); SetTickCallbacks(TickCallback.Tick | TickCallback.PostTick); }
        public override void OnStartClient()
        {
            base.OnStartClient();
            if (!IsOwner) return;
            Local = this;
            if (Camera.main != null) Camera.main.GetComponent<QingxiOrbitCamera>()?.SetTarget(transform);
        }
        public override void OnStopClient()
        {
            if (Local == this)
            {
                Local = null;
                if (Camera.main != null) Camera.main.GetComponent<QingxiOrbitCamera>()?.SetTarget(null);
            }
            base.OnStopClient();
        }
        protected override void TimeManager_OnTick()
        {
            var direction = Vector2.zero;
            if (IsOwner)
            {
                var keyboard = Keyboard.current;
                if (keyboard != null && !TextInputFocused)
                    direction = new Vector2((keyboard.dKey.isPressed ? 1 : 0) - (keyboard.aKey.isPressed ? 1 : 0), (keyboard.wKey.isPressed ? 1 : 0) - (keyboard.sKey.isPressed ? 1 : 0));
                direction += TouchInput;
                if (Camera.main != null)
                {
                    direction = CameraRelativeDirection(direction,
                        Camera.main.transform.forward, Camera.main.transform.right);
                }
            }
            Move(new MoveData(direction));
        }
        protected override void TimeManager_OnPostTick() => CreateReconcile();
        public override void CreateReconcile() => Correct(new StateData(transform.position, transform.rotation, vertical));
        [Replicate]
        void Move(MoveData data, ReplicateState state = ReplicateState.Invalid, Channel channel = Channel.Unreliable)
        {
            var input = data.Direction;
            if (!float.IsFinite(input.x) || !float.IsFinite(input.y)) input = Vector2.zero;
            input = Vector2.ClampMagnitude(input, 1);
            float dt = (float)TimeManager.TickDelta;
            vertical = controller.isGrounded ? -2 : Mathf.Max(-25, vertical - 20 * dt);
            controller.Move(new Vector3(input.x * 4, vertical, input.y * 4) * dt);
            if (input.sqrMagnitude > .001f)
            {
                var facing = Quaternion.LookRotation(new Vector3(input.x, 0, input.y));
                transform.rotation = Quaternion.RotateTowards(transform.rotation, facing, 540 * dt);
            }
        }
        [Reconcile]
        void Correct(StateData data, Channel channel = Channel.Unreliable)
        {
            controller.enabled = false;
            transform.SetPositionAndRotation(data.Position, data.Rotation);
            vertical = data.Vertical;
            controller.enabled = true;
        }
    }
}
