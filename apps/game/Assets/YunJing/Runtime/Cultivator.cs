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
            public Vector3 Position; public float Vertical; uint tick;
            public StateData(Vector3 position, float vertical) { Position = position; Vertical = vertical; tick = 0; }
            public uint GetTick() => tick; public void SetTick(uint value) => tick = value; public void Dispose() { }
        }
        public static Cultivator Local { get; private set; }
        public static Vector2 TouchInput;
        public static bool TextInputFocused;
        CharacterController controller; float vertical;
        void Awake() { controller = GetComponent<CharacterController>(); SetTickCallbacks(TickCallback.Tick | TickCallback.PostTick); }
        public override void OnStartClient() { base.OnStartClient(); if (IsOwner) Local = this; }
        public override void OnStopClient() { if (Local == this) Local = null; base.OnStopClient(); }
        protected override void TimeManager_OnTick()
        {
            var direction = Vector2.zero;
            if (IsOwner)
            {
                var keyboard = Keyboard.current;
                if (keyboard != null && !TextInputFocused)
                    direction = new Vector2((keyboard.dKey.isPressed ? 1 : 0) - (keyboard.aKey.isPressed ? 1 : 0), (keyboard.wKey.isPressed ? 1 : 0) - (keyboard.sKey.isPressed ? 1 : 0));
                direction += TouchInput;
            }
            Move(new MoveData(direction));
        }
        protected override void TimeManager_OnPostTick() => CreateReconcile();
        public override void CreateReconcile() => Correct(new StateData(transform.position, vertical));
        [Replicate]
        void Move(MoveData data, ReplicateState state = ReplicateState.Invalid, Channel channel = Channel.Unreliable)
        {
            var input = data.Direction;
            if (!float.IsFinite(input.x) || !float.IsFinite(input.y)) input = Vector2.zero;
            input = Vector2.ClampMagnitude(input, 1);
            float dt = (float)TimeManager.TickDelta;
            vertical = controller.isGrounded ? -2 : Mathf.Max(-25, vertical - 20 * dt);
            controller.Move(new Vector3(input.x * 4, vertical, input.y * 4) * dt);
        }
        [Reconcile]
        void Correct(StateData data, Channel channel = Channel.Unreliable)
        {
            controller.enabled = false; transform.position = data.Position; vertical = data.Vertical; controller.enabled = true;
        }
        void LateUpdate()
        {
            if (!IsOwner || Camera.main == null) return;
            var camera = Camera.main.transform;
            camera.position = Vector3.Lerp(camera.position, transform.position + new Vector3(0, 8, -10), 1 - Mathf.Exp(-7 * Time.deltaTime));
            camera.LookAt(transform.position + Vector3.up);
        }
    }
}
