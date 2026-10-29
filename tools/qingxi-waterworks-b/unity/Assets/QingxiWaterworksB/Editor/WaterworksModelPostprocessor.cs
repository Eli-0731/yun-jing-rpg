// 青溪水工 B：匯入時去掉 Blender 同名物件的 .001 尾碼（所有件共用一個 .blend，空物件 SOCKET_in 會被改名成 SOCKET_in.003）。
// 玩法程式一律以 SOCKET_in／SOCKET_out／SOCKET_wheel_mount 等原名查找。
// v002：每件 FBX 內含 LOD0（原名）與 _LOD1／_LOD2 簡化網格，這裡在根物件建 LODGroup，否則三層會同時顯示。
// LOD0 保留原名，閘板、疊板等以名稱查找的部件不受影響；部件的 LOD 網格掛在該部件底下，隨部件一起動。
using System.Linq;
using System.Text.RegularExpressions;
using UnityEditor;
using UnityEngine;

public class WaterworksModelPostprocessor : AssetPostprocessor
{
    static readonly Regex Suffix = new Regex(@"\.\d{3}$");
    // 螢幕高度比例門檻：近看 LOD0、中距離 LOD1、遠處 LOD2，再遠剔除；手機實測後再調
    static readonly float[] Heights = { 0.30f, 0.10f, 0.012f };

    void OnPostprocessModel(GameObject root)
    {
        if (!assetPath.StartsWith("Assets/QingxiWaterworksB/")) return;
        foreach (var t in root.GetComponentsInChildren<Transform>(true))
            t.name = Suffix.Replace(t.name, "");
        var rs = root.GetComponentsInChildren<Renderer>(true);
        var lod1 = rs.Where(r => r.name.EndsWith("_LOD1")).ToArray();
        var lod2 = rs.Where(r => r.name.EndsWith("_LOD2")).ToArray();
        if (lod1.Length == 0 && lod2.Length == 0) return;
        var lod0 = rs.Except(lod1).Except(lod2).ToArray();
        var group = root.GetComponent<LODGroup>();           // Unity 物件的假 null 不能用 ??
        if (group == null) group = root.AddComponent<LODGroup>();
        group.SetLODs(new[]
        {
            new LOD(Heights[0], lod0),
            new LOD(Heights[1], lod1.Length > 0 ? lod1 : lod0),
            new LOD(Heights[2], lod2.Length > 0 ? lod2 : lod1),
        });
        group.RecalculateBounds();
    }
}
