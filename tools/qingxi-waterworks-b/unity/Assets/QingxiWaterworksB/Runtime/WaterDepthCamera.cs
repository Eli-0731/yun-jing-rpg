// 青溪水工 B：讓攝影機輸出深度貼圖，Qingxi/WaterFlow 才算得出水厚（淺處淡出、岸邊泡沫、折射遮擋）。
using UnityEngine;

[ExecuteAlways, RequireComponent(typeof(Camera))]
public class WaterDepthCamera : MonoBehaviour
{
    void OnEnable() => GetComponent<Camera>().depthTextureMode |= DepthTextureMode.Depth;
}
