// 青溪水工 B：沿路線傳遞的水路。水只從水源（溪流）進來，依序往下游灌：
//   - 每件的水面分成數段（依水流先後），前一段灌滿才開始灌下一段；上游斷水就依各段時間退水。
//   - 閘門（GateController）：閘門後面那一段要閘門打開才有水；關上後下游退乾，閘門前保持積水。
//   - 田地（FieldWeirController）：入水口 → 田面（由溝底漲到堰頂）→ 出水口；
//     疊板卡滿時田面保水、出水口不出水；疊板降下後才從出水口放水，斷水時田面會退乾（needsRelease）。
// 不含水面物件的件（S02 河床、B06 水車）直接把上游狀態傳下去。
using System.Collections.Generic;
using UnityEngine;

public class WaterNetwork : MonoBehaviour
{
    [System.Serializable]
    public class Segment
    {
        public string name;
        public Transform[] waters;
        public float fillSeconds = 0.8f;
        public bool fieldWater;                     // 交給 FieldWeirController.SetFill
        public bool holds;                          // 斷水後保持（被堰擋住的田面）
        public bool needsRelease;                   // 疊板降下（FieldWeirController 不在卡滿）且田面有水才有水
        public float level;
        public Vector3[] basePos;
    }

    [System.Serializable]
    public class Node
    {
        public string id;
        public bool source;
        public GateController gate;
        public int gateBefore = -1;                 // 這一段在閘門下游（需要閘門打開）
        public FieldWeirController field;
        public List<Segment> segments = new List<Segment>();
    }

    public List<Node> nodes = new List<Node>();
    public float drop = 0.12f;                      // 沒水時水面往下藏的距離（m），灌水時由下往上浮出

    void Start() => ResetDry();
    void Update() => Step(Time.deltaTime);

    // 只有水源有水、其他全乾（初始狀態）
    public void ResetDry()
    {
        foreach (var n in nodes)
            foreach (var s in n.segments)
            {
                if (s.basePos == null || s.basePos.Length != s.waters.Length)
                {
                    s.basePos = new Vector3[s.waters.Length];
                    for (int i = 0; i < s.waters.Length; i++)
                        s.basePos[i] = s.waters[i].parent.InverseTransformPoint(s.waters[i].position);
                }
                s.level = n.source ? 1f : 0f;
            }
        Apply();
    }

    public void Step(float dt)
    {
        bool upstream = false;
        foreach (var n in nodes)
        {
            if (n.source)
            {
                upstream = true;
                continue;
            }
            if (n.gate != null && !Application.isPlaying) n.gate.Step(dt);
            bool prevFull = upstream;
            for (int k = 0; k < n.segments.Count; k++)
            {
                var s = n.segments[k];
                bool target = prevFull && (k != n.gateBefore || (n.gate != null && n.gate.IsOpen));
                bool released = n.field != null && !n.field.Holding;
                if (s.needsRelease) target = released && n.field.fill > 0.01f;
                bool holds = s.holds && !released;                 // 疊板降下後田面不再保水
                if (target || !holds)
                    s.level = Mathf.MoveTowards(s.level, target ? 1f : 0f, dt / Mathf.Max(s.fillSeconds, 0.01f));
                prevFull = s.level >= 0.999f;
            }
            if (n.segments.Count > 0) upstream = prevFull;
        }
        Apply();
    }

    void Apply()
    {
        foreach (var n in nodes)
            foreach (var s in n.segments)
            {
                if (s.fieldWater)
                {
                    if (n.field != null) n.field.SetFill(s.level);
                    continue;
                }
                for (int i = 0; i < s.waters.Length; i++)
                {
                    var t = s.waters[i];
                    t.gameObject.SetActive(s.level > 0.01f);
                    t.position = t.parent.TransformPoint(s.basePos[i]) + Vector3.down * ((1f - s.level) * drop);
                }
            }
    }

    public Node Find(string id, int occurrence = 0)
    {
        foreach (var n in nodes)
            if (n.id == id && occurrence-- == 0) return n;
        return null;
    }
}
