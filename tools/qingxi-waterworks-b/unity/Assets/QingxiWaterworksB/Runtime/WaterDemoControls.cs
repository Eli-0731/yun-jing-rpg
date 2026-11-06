// 青溪水工 B：demo 鍵盤操作（舊版 Input Manager）。
//   G：開／關 B05 閘門　↑／↓：升降 F01 疊板　R：全部退乾、閘門關回
//   1／2／3：鏡頭切換（整條水路／F01 疊板閘／B01 取水口）
// （專案未啟用 IMGUI 模組，畫面上不顯示說明）
using UnityEngine;

public class WaterDemoControls : MonoBehaviour
{
    public GateController gate;
    public FieldWeirController weir;
    public WaterNetwork network;
    public float crestSpeed = 0.05f;               // 疊板升降速度（m/s）
    public Camera cam;
    public Vector3[] cameraPositions;
    public Vector3[] cameraTargets;

    public int CameraIndex { get; private set; }

    void Update()
    {
        if (Input.GetKeyDown(KeyCode.G) && gate != null) gate.open = !gate.open;
        if (weir != null)
        {
            float d = (Input.GetKey(KeyCode.UpArrow) ? 1f : 0f) - (Input.GetKey(KeyCode.DownArrow) ? 1f : 0f);
            if (d != 0f) weir.SetCrest(weir.crestZ + d * crestSpeed * Time.deltaTime);
        }
        if (Input.GetKeyDown(KeyCode.R) && network != null)
        {
            if (gate != null) gate.SetOpen(false, true);
            if (weir != null) weir.SetCrest(FieldWeirController.MaxCrest);
            network.ResetDry();
        }
        if (Input.GetKeyDown(KeyCode.Alpha1)) SelectCamera(0);
        if (Input.GetKeyDown(KeyCode.Alpha2)) SelectCamera(1);
        if (Input.GetKeyDown(KeyCode.Alpha3)) SelectCamera(2);
    }

    public void SelectCamera(int i)
    {
        if (cam == null || cameraPositions == null || i >= cameraPositions.Length) return;
        CameraIndex = i;
        cam.transform.position = cameraPositions[i];
        cam.transform.LookAt(cameraTargets[i]);
    }
}
