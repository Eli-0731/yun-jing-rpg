// 青溪水工 B：B05 閘門（閘板上下）。規則與 Blender model_info.states 相同：
//   closed：閘板在槽底（偏移 0，模型預設）；open：閘板上提 0.32 m。
//   閘板離底 8 cm 起才算放水（WaterNetwork 依 IsOpen 決定下游有沒有水）。
using UnityEngine;

[ExecuteAlways]
public class GateController : MonoBehaviour
{
    public const float OpenOffset = 0.32f;
    public const float PassOffset = 0.08f;

    public bool open;
    public float speed = 0.2f;                     // 閘板升降速度（m/s）

    [SerializeField, HideInInspector] bool captured;
    [SerializeField, HideInInspector] Vector3 gatePos0;

    Transform gate;

    public float Offset { get; private set; }
    public bool IsOpen => Offset >= PassOffset;
    public Transform Gate => gate;

    void OnEnable()
    {
        Offset = open ? OpenOffset : 0f;
        ApplyPose();
    }

    void Update()
    {
        if (Application.isPlaying) Step(Time.deltaTime);
    }

    public void Step(float dt)
    {
        Offset = Mathf.MoveTowards(Offset, open ? OpenOffset : 0f, speed * dt);
        ApplyPose();
    }

    public void SetOpen(bool value, bool instant = false)
    {
        open = value;
        if (instant) Offset = open ? OpenOffset : 0f;
        ApplyPose();
    }

    void ApplyPose()
    {
        if (gate == null)
            foreach (var t in GetComponentsInChildren<Transform>(true))
                if (t.name == "gate" || t.name.EndsWith("_gate")) gate = t;
        if (gate == null) return;
        if (!captured)
        {
            gatePos0 = transform.InverseTransformPoint(gate.position);
            captured = true;
        }
        gate.position = transform.TransformPoint(gatePos0) + Vector3.up * Offset;   // 世界上方（根物件可能帶匯入姿態）
    }
}
