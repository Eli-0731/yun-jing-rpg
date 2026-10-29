// 青溪水工 B：匯入時去掉 Blender 同名物件的 .001 尾碼（所有件共用一個 .blend，空物件 SOCKET_in 會被改名成 SOCKET_in.003）。
// 玩法程式一律以 SOCKET_in／SOCKET_out／SOCKET_wheel_mount 等原名查找。
using System.Text.RegularExpressions;
using UnityEditor;
using UnityEngine;

public class WaterworksModelPostprocessor : AssetPostprocessor
{
    static readonly Regex Suffix = new Regex(@"\.\d{3}$");

    void OnPostprocessModel(GameObject root)
    {
        if (!assetPath.StartsWith("Assets/QingxiWaterworksB/")) return;
        foreach (var t in root.GetComponentsInChildren<Transform>(true))
            t.name = Suffix.Replace(t.name, "");
    }
}
