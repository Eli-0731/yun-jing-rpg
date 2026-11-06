// 青溪水工 B：F01 灌溉田地出水口疊板閘與田面水位連動。
// 平時疊板升到頂（堰頂 0.30）卡滿擋水，出水口不出水；要放水時轉手輪把整疊降下，水從板頂溢流。
// 規則與 Blender model_info.states 相同：
//   堰頂 crest_z 0.10–0.30 m（水面標準 0.28）；堰板沿上移 crest_z − 0.28；
//   手輪每圈 2.5 cm（每 1 cm 轉 144°），繞自身中心的垂直軸轉；
//   田面水 WATER_F01_field 高度＝crest_z；crest_z < 0.125 改顯示 WATER_F01_field_low（只剩溝底積水）。
// 掛在 F01 實例根物件上；水面子物件（F01_water.fbx）掛在 F01 底下時才會連動水位。
using UnityEngine;

[ExecuteAlways]
public class FieldWeirController : MonoBehaviour
{
    public const float WaterZ = 0.28f;
    public const float MinCrest = 0.10f;
    public const float MaxCrest = 0.30f;
    public const float LowSwitch = 0.125f;
    public const float PitchPerTurn = 0.025f;

    [Range(MinCrest, MaxCrest)] public float crestZ = MaxCrest;
    [Range(0f, 1f)] public float fill = 1f;        // 田面蓄水量：0＝乾、1＝滿到堰頂（WaterNetwork 控制；單獨使用時保持 1）

    // 基準姿態（堰頂 0.28 時、F01 根物件座標）只擷取一次，之後每次都從基準重算，不會累積誤差
    [SerializeField, HideInInspector] bool captured;
    [SerializeField, HideInInspector] Vector3 weirPos0;
    [SerializeField, HideInInspector] Vector3 wheelPos0;
    [SerializeField, HideInInspector] Quaternion wheelRot0 = Quaternion.identity;
    [SerializeField, HideInInspector] Vector3 wheelPivot0;
    [SerializeField, HideInInspector] Vector3 fieldPos0;

    Transform weir, wheel, field, fieldLow;

    public float WeirOffset => Mathf.Clamp(crestZ, MinCrest, MaxCrest) - WaterZ;
    public float WheelTurns => WeirOffset / PitchPerTurn;
    public bool Holding => crestZ >= MaxCrest - 0.005f;          // 疊板卡滿：不出水
    public bool FieldWaterVisible => fill > 0.01f && crestZ >= LowSwitch;
    public bool FieldLowVisible => fill > 0.01f && crestZ < LowSwitch;
    // 田面水高相對標準水面的位移：滿水時＝堰頂，蓄水量不足時由溝底（0.10）往上漲
    public float FieldOffset => WeirOffset - (1f - fill) * (Mathf.Clamp(crestZ, MinCrest, MaxCrest) - MinCrest);
    public Transform Weir => weir;
    public Transform Wheel => wheel;
    public Transform FieldWater => field;
    public Transform FieldLowWater => fieldLow;

    public static readonly (string name, float crest)[] Presets =
        { ("full", MaxCrest), ("half", 0.19f), ("drain", MinCrest) };

    void OnEnable() => Apply();
    void OnValidate() => Apply();

    void Find()
    {
        foreach (var t in GetComponentsInChildren<Transform>(true))
        {
            var n = t.name;
            if (n == "weir" || n.EndsWith("_weir")) weir = t;
            else if (n == "weir_wheel" || n.EndsWith("_weir_wheel")) wheel = t;
            else if (n.EndsWith("_field_low")) fieldLow = t;
            else if (n.StartsWith("WATER_") && n.EndsWith("_field")) field = t;
        }
    }

    // 水面子物件是之後才掛上的：重新擷取。基準姿態＝模型的建模位置（堰頂 0.28），擷取後回到卡滿
    public void Recapture()
    {
        captured = false;
        crestZ = WaterZ;
        Apply();
        crestZ = MaxCrest;
        Apply();
    }

    public void Apply()
    {
        Find();
        if (weir == null || wheel == null) return;
        if (!captured)
        {
            weirPos0 = transform.InverseTransformPoint(weir.position);
            wheelPos0 = transform.InverseTransformPoint(wheel.position);
            wheelRot0 = Quaternion.Inverse(transform.rotation) * wheel.rotation;
            var r = wheel.GetComponent<Renderer>();
            wheelPivot0 = transform.InverseTransformPoint(r != null ? r.bounds.center : wheel.position);
            if (field != null) fieldPos0 = transform.InverseTransformPoint(field.position);
            captured = true;
        }
        // 根物件可能帶匯入姿態（x 軸 −90°），根座標的「上」不一定朝上：位移與手輪轉軸都用世界上方
        var up = Vector3.up * WeirOffset;
        weir.position = transform.TransformPoint(weirPos0) + up;
        var spin = Quaternion.AngleAxis(WheelTurns * 360f, Vector3.up);
        var pivot = transform.TransformPoint(wheelPivot0);
        wheel.position = pivot + spin * (transform.TransformPoint(wheelPos0) - pivot);
        wheel.rotation = spin * transform.rotation * wheelRot0;
        if (field != null)
        {
            field.position = transform.TransformPoint(fieldPos0) + Vector3.up * FieldOffset;
            field.gameObject.SetActive(FieldWaterVisible);
        }
        if (fieldLow != null) fieldLow.gameObject.SetActive(FieldLowVisible);
    }

    public void SetFill(float f)
    {
        f = Mathf.Clamp01(f);
        if (Mathf.Approximately(f, fill)) return;
        fill = f;
        Apply();
    }

    public void SetCrest(float z)
    {
        crestZ = Mathf.Clamp(z, MinCrest, MaxCrest);
        Apply();
    }
}
