// 青溪水工 B：古水路修復的 Unity 可玩場景（Scenes/WaterworksPuzzle.unity，由 Editor/WaterworksPuzzleBuild 產生）。
// 只做畫面與輸入；所有規則都在 WaterworksRules.cs（與網頁版 src/waterworks-core.mjs 逐案比對過）。
// 完工結果只存在本機記憶體，標示「本機演示 · 非正式結果」，不入正式背包，見 ../../../../CONTRACT.md。
//
// 操作與網頁版相同：
//   滑鼠：點槽位選取、右鍵拆掉、左鍵拖曳轉視角、滾輪縮放；右側面板的按鈕都可以點。
//   鍵盤：方向鍵／Tab 換槽位、1–0 與 - 放段件（P4 選補石）、Del 拆、G 開關閘、Q/W/E 處理方向、
//         Enter 完工（版面沒變時重送同一請求）、Esc 關結果卡、Ctrl+Z 撤回、Ctrl+Y／Ctrl+Shift+Z 重做、C 切換特寫。
//   觸控：點選、單指拖曳轉視角、雙指縮放（Windows 觸控訊息；本專案沒有觸控裝置實測過）。
//
// 錄影：QingxiWaterworks.exe -qxOut <資料夾> -qxFree <秒數> [-qxObs full|partial|none]
//   每 0.1 秒存一張畫面（JPG），每個操作寫一行 events.jsonl，ui_map.json 持續更新槽位與按鈕的螢幕座標（給按鍵／滑鼠驅動程式用）。
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using QingxiWaterworksB;
using UnityEngine;

public class WaterworksPuzzle : MonoBehaviour
{
    [Header("由 WaterworksPuzzleBuild 填入")]
    public TextAsset boardJson, catalogJson, fixtureJson;
    public List<string> libraryIds = new List<string>();
    public List<GameObject> libraryTemplates = new List<GameObject>();
    public Camera cam;
    public FieldWeirController weir;
    public Transform fieldInlet, fieldOutlet;
    public GameObject[] pegs = new GameObject[3];          // restore_channel, protect_nursery, clear_silt
    public Material waterFlow, waterStill, overlay, fade, standard;

    static readonly string[] PALETTE = { "B02", "B02-V03", "B02-V04", "B05", "B03", "B03-V04", "B03-V02", "B03-V03", "B04-V02", "B04", "B02-V05" };
    static readonly string[] PATCHES = { "B07", "B07-V02", "B07-V03" };
    static readonly string[] KEYS = { "1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-" };
    static readonly KeyCode[] KEYCODES = { KeyCode.Alpha1, KeyCode.Alpha2, KeyCode.Alpha3, KeyCode.Alpha4, KeyCode.Alpha5, KeyCode.Alpha6, KeyCode.Alpha7, KeyCode.Alpha8, KeyCode.Alpha9, KeyCode.Alpha0, KeyCode.Minus };
    static readonly (KeyCode key, string choice, string hint)[] CHOICE_KEYS =
        { (KeyCode.Q, "clear_silt", "三通分流進回流溝"), (KeyCode.W, "restore_channel", "走原本舊渠、補破槽"), (KeyCode.E, "protect_nursery", "繞開育幼區 80 cm 外") };
    static readonly Dictionary<string, string> LEVEL = new Dictionary<string, string> { { "risk", "有風險" }, { "safe", "安全" }, { "unknown", "未知" }, { "dry", "沒有流水" } };
    static readonly Dictionary<string, string> SILT = new Dictionary<string, string> { { "slowing", "淤積拖慢水量" }, { "remaining", "仍有淤積（未經過）" }, { "cleared", "已清淤" }, { "unknown", "未知" } };
    static readonly Dictionary<string, string> CRACK = new Dictionary<string, string> { { "patched", "已補好" }, { "leaking", "漏水" }, { "bypassed", "水沒經過" }, { "unknown", "未知" } };
    const float PanelW = 440f;

    // ------------------------------------------------------------ state
    WwCtx ctx;
    WwSession S;
    string obsKey = "full";
    string selected = "P2";
    WwPreview view;
    WwResult lastResult;
    bool cardOpen, cardReplay;
    List<WwCompare> compare;
    string toastText; float toastT; bool toastBad;
    float fieldShown;
    bool closeUp;

    class WaterMesh { public Renderer r; public Vector3 basePos; public float level, target, speed; public string name; }
    class SlotView
    {
        public WwSlot slot; public GameObject group; public LineRenderer outline; public MeshRenderer arrow;
        public GameObject piece; public string pieceId; public List<WaterMesh> waters = new List<WaterMesh>();
        public GateController gate; public Transform wheel; public float lastOffset;
    }
    readonly Dictionary<string, SlotView> slotViews = new Dictionary<string, SlotView>();
    GameObject patchView; string patchId;
    Transform portRoot, piecesRoot;
    GameObject silt, crackMark, tracks, drainWater;
    Material nurseryRingMat, drainMat, spillMat;
    readonly List<(Vector3 world, string text, Color fg, Color bg, int size)> labels = new List<(Vector3, string, Color, Color, int)>();
    readonly List<(Transform t, Material m, Color c)> pulses = new List<(Transform, Material, Color)>();

    // camera (orbit)
    Vector3 camTarget; float camYaw, camPitch, camDist;
    Vector3 goalTarget; float goalDist;
    Vector3 homeTarget; float homeDist, homeYaw, homePitch;

    // ------------------------------------------------------------ coordinates: Blender (x, y, z-up) -> Unity (x, z, y)
    static Vector3 B(double x, double y, double z = 0) => new Vector3((float)x, (float)z, (float)y);
    static Quaternion Yaw(double[] d) => Quaternion.Euler(0f, -(float)(WaterworksRules.YawOf(d) * Mathf.Rad2Deg), 0f);

    // ------------------------------------------------------------ setup
    void Awake()
    {
        ctx = WwCtx.Load(boardJson.text, catalogJson.text, fixtureJson.text);
        var args = System.Environment.GetCommandLineArgs();
        var oi = System.Array.IndexOf(args, "-qxObs");
        if (oi >= 0 && oi + 1 < args.Length && ctx.observationSets.Has(args[oi + 1])) obsKey = args[oi + 1];
        S = WaterworksRules.NewSession(ctx, ctx.observationSets[obsKey]);
        piecesRoot = new GameObject("Pieces").transform;
        portRoot = new GameObject("PortMarks").transform;
        BuildWorld();
        // 預設鏡頭對照網頁版：位置 b2t(1.8, -4.4, 11.6)、看向 b2t(-0.5, 4.0)
        camTarget = goalTarget = B(-0.5, 4.0);
        var off = B(1.8, -4.4, 11.6) - camTarget;
        camDist = goalDist = off.magnitude;
        camPitch = Mathf.Asin(off.y / camDist) * Mathf.Rad2Deg;
        camYaw = Mathf.Atan2(off.x, off.z) * Mathf.Rad2Deg;
        homeTarget = camTarget; homeDist = camDist; homeYaw = camYaw; homePitch = camPitch;
    }

    void Start()
    {
        if (weir != null) { weir.SetCrest(FieldWeirController.MaxCrest); weir.SetFill(0f); }
        Refresh();
        StartRecorderIfAsked();
    }

    Material Mat(Color c) { var m = new Material(standard) { color = c }; m.SetFloat("_Glossiness", 0.1f); return m; }
    Material Overlay(Color c) { var m = new Material(overlay) { color = c }; return m; }
    GameObject Prim(PrimitiveType t, Transform parent, Vector3 pos, Vector3 scale, Material m, string name)
    {
        var g = GameObject.CreatePrimitive(t);
        g.name = name;
        Destroy(g.GetComponent<Collider>());
        g.transform.SetParent(parent, false);
        g.transform.localPosition = pos; g.transform.localScale = scale;
        g.GetComponent<Renderer>().sharedMaterial = m;
        return g;
    }
    GameObject Flat(double[] r, double z, Material m, string name, Transform parent = null)
    {
        var g = Prim(PrimitiveType.Cube, parent ?? transform, B((r[0] + r[2]) / 2, (r[1] + r[3]) / 2, z), new Vector3((float)(r[2] - r[0]), 0.004f, (float)(r[3] - r[1])), m, name);
        return g;
    }
    LineRenderer Line(Transform parent, Vector3[] pts, Color c, float w, bool loop)
    {
        var g = new GameObject("line");
        g.transform.SetParent(parent, false);
        var lr = g.AddComponent<LineRenderer>();
        lr.useWorldSpace = false; lr.loop = loop; lr.positionCount = pts.Length; lr.SetPositions(pts);
        lr.widthMultiplier = w; lr.sharedMaterial = Overlay(c);
        lr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off; lr.receiveShadows = false;
        lr.alignment = LineAlignment.TransformZ;
        g.transform.localRotation = Quaternion.Euler(90f, 0f, 0f);   // 局部 (x, y, 0) 落在水平面（父物件的 x、z），線段面朝上
        return lr;
    }

    void BuildWorld()
    {
        var Z = ctx.board;
        var root = transform;
        // 育幼區：地面、外圈（顏色＝風險）、低竹籬（遠側留口）、玩具球
        Flat(Z.nurseryRect, 0.02, Mat(new Color32(0xcd, 0xbb, 0x92, 255)), "Nursery");
        nurseryRingMat = new Material(fade) { color = new Color(0.55f, 0.55f, 0.55f, 0.55f) };
        Flat(new[] { Z.nurseryRect[0] - 0.12, Z.nurseryRect[1] - 0.12, Z.nurseryRect[2] + 0.12, Z.nurseryRect[3] + 0.12 }, 0.012, nurseryRingMat, "NurseryRing");
        var post = Mat(new Color32(0x8a, 0x73, 0x48, 255));
        double x0 = Z.nurseryRect[0], y0 = Z.nurseryRect[1], x1 = Z.nurseryRect[2], y1 = Z.nurseryRect[3];
        var fence = new GameObject("NurseryFence").transform; fence.SetParent(root, false);
        var posts = new List<(double, double)>();
        for (var x = x0; x <= x1 + 1e-6; x += 0.25) { posts.Add((x, y0)); posts.Add((x, y1)); }
        for (var y = y0 + 0.25; y < y1 - 1e-6; y += 0.25) posts.Add((x0, y));
        foreach (var (x, y) in posts) Prim(PrimitiveType.Cylinder, fence, B(x, y, 0.25), new Vector3(0.055f, 0.25f, 0.055f), post, "post");
        foreach (var (a, b) in new[] { ((x0, y0), (x1, y0)), ((x0, y1), (x1, y1)), ((x0, y0), (x0, y1)) })
            foreach (var z in new[] { 0.2, 0.42 })
            {
                var len = System.Math.Sqrt((b.Item1 - a.Item1) * (b.Item1 - a.Item1) + (b.Item2 - a.Item2) * (b.Item2 - a.Item2));
                var rail = Prim(PrimitiveType.Cube, fence, B((a.Item1 + b.Item1) / 2, (a.Item2 + b.Item2) / 2, z), new Vector3((float)len, 0.03f, 0.03f), post, "rail");
                rail.transform.localRotation = Quaternion.Euler(0f, -(float)(System.Math.Atan2(b.Item2 - a.Item2, b.Item1 - a.Item1) * Mathf.Rad2Deg), 0f);
            }
        foreach (var (x, y, c) in new[] { (1.4, 3.75, new Color32(0xc4, 0x5a, 0x3c, 255)), (2.1, 3.55, new Color32(0x3c, 0x7f, 0xc4, 255)), (1.9, 4.0, new Color32(0xd8, 0xb5, 0x3c, 255)) })
            Prim(PrimitiveType.Sphere, fence, B(x, y, 0.1), Vector3.one * 0.16f, Mat(c), "ball");
        // 孩子的腳印（nursery_tracks）
        tracks = new GameObject("Tracks"); tracks.transform.SetParent(root, false);
        var foot = Mat(new Color32(0x6b, 0x52, 0x36, 255));
        for (int i = 0; i < 9; i++) Prim(PrimitiveType.Cylinder, tracks.transform, B(0.72 - i * 0.07, 3.55 + (i % 2) * 0.09 + i * 0.02, 0.026), new Vector3(0.063f, 0.002f, 0.117f), foot, "foot");
        // 回流溝
        Flat(Z.drainRect, 0.012, Mat(new Color32(0x4c, 0x5a, 0x52, 255)), "Drain");
        spillMat = new Material(fade) { color = new Color32(0x5d, 0x9f, 0xae, 165) };
        drainMat = new Material(fade) { color = new Color32(0x7d, 0x6a, 0x46, 0) };
        drainWater = Flat(new[] { Z.drainRect[0] + 0.08, Z.drainRect[1] + 0.08, Z.drainRect[2] - 0.08, Z.drainRect[3] - 0.08 }, 0.03, drainMat, "DrainWater");
        // 淤泥（P1）與裂縫記號（P4 西牆）
        silt = Prim(PrimitiveType.Cube, root, B(0, 0.5, 0.145), new Vector3(0.4f, 0.09f, 1.0f), Mat(new Color32(0x6e, 0x5a, 0x3c, 255)), "Silt");
        crackMark = new GameObject("CrackMark"); crackMark.transform.SetParent(root, false);
        crackMark.transform.localPosition = B(Z.crackMarkPos[0] - 0.01, Z.crackMarkPos[1], 0.18);
        var red = new Material(standard) { color = new Color32(0xb3, 0x26, 0x1e, 255) };
        var zig = new[] { (-0.12, 0.0), (-0.05, 0.02), (0.0, -0.015), (0.06, 0.02), (0.12, 0.0) };
        for (int i = 0; i + 1 < zig.Length; i++)
        {
            var a = new Vector3(0, (float)zig[i].Item2, (float)zig[i].Item1); var b = new Vector3(0, (float)zig[i + 1].Item2, (float)zig[i + 1].Item1);
            var seg = Prim(PrimitiveType.Cylinder, crackMark.transform, (a + b) / 2, new Vector3(0.024f, (b - a).magnitude / 2, 0.024f), red, "crack");
            seg.transform.localRotation = Quaternion.FromToRotation(Vector3.up, b - a);
        }
        // 槽位框、箭頭與點選範圍
        foreach (var s in Z.slots)
        {
            var g = new GameObject("Slot_" + s.id);
            g.transform.SetParent(root, false);
            g.transform.localPosition = B(s.pos[0], s.pos[1], 0.03);
            g.transform.localRotation = Yaw(s.dir);
            var outline = Line(g.transform, new[] { new Vector3(-0.3f, 0, 0), new Vector3(0.3f, 0, 0), new Vector3(0.3f, 0.92f, 0), new Vector3(-0.3f, 0.92f, 0) }, Color.white, 0.03f, true);
            var arrow = new GameObject("arrow");
            arrow.transform.SetParent(g.transform, false);
            arrow.transform.localPosition = new Vector3(0, 0.02f, 0.2f);
            var mesh = new Mesh { vertices = new[] { new Vector3(-0.09f, 0, -0.11f), new Vector3(0, 0, 0.11f), new Vector3(0.09f, 0, -0.11f) }, triangles = new[] { 0, 1, 2 }, colors = new[] { Color.white, Color.white, Color.white } };
            arrow.AddComponent<MeshFilter>().sharedMesh = mesh;
            var ar = arrow.AddComponent<MeshRenderer>(); ar.sharedMaterial = Overlay(Color.white);
            var hit = new GameObject("hit"); hit.transform.SetParent(g.transform, false);
            hit.transform.localPosition = new Vector3(0, 0.25f, 0.5f);
            var bc = hit.AddComponent<BoxCollider>(); bc.size = new Vector3(0.8f, 0.5f, 1.0f);
            hit.AddComponent<WaterworksSlotHit>().slot = s.id;
            slotViews[s.id] = new SlotView { slot = s, group = g, outline = outline, arrow = ar };
        }
    }

    GameObject Template(string id) { var i = libraryIds.IndexOf(id); return i < 0 ? null : libraryTemplates[i]; }

    GameObject Spawn(string id, Vector3 pos, Quaternion rot)
    {
        var t = Template(id);
        var g = Instantiate(t, piecesRoot);
        g.name = id;
        g.transform.SetPositionAndRotation(pos, rot);
        g.SetActive(true);
        return g;
    }

    // ------------------------------------------------------------ rules -> scene
    void SyncModels()
    {
        foreach (var s in ctx.board.slots)
        {
            var id = s.fixedPiece ?? S.design.placed.Get(s.id);
            var v = slotViews[s.id];
            if (v.pieceId == id) continue;
            if (v.piece != null) Destroy(v.piece);
            v.piece = null; v.pieceId = id; v.waters.Clear(); v.gate = null; v.wheel = null;
            if (id == null) continue;
            v.piece = Spawn(id, B(s.pos[0], s.pos[1]), Yaw(s.dir));
            var water = v.piece.GetComponentsInChildren<Transform>(true).FirstOrDefault(t => t.name == id + "_water");
            if (water != null)
                foreach (var r in water.GetComponentsInChildren<MeshRenderer>(true))
                {
                    v.waters.Add(new WaterMesh { r = r, basePos = r.transform.position, name = r.name });
                    r.enabled = false;
                }
            v.gate = v.piece.GetComponentInChildren<GateController>(true);
            if (v.gate != null) { v.gate.SetOpen(S.design.gates.Get(s.id, false), true); v.lastOffset = v.gate.Offset; }
            v.wheel = v.piece.GetComponentsInChildren<Transform>(true).FirstOrDefault(t => t.name.EndsWith("_wheel") || t.name == "wheel");
        }
        var want = S.design.patches.Get(ctx.board.crackSlot);
        if (want != patchId)
        {
            if (patchView != null) Destroy(patchView);
            patchView = null; patchId = want;
            if (want != null) patchView = Spawn(want, B(ctx.board.crackMarkPos[0], ctx.board.crackMarkPos[1], ctx.board.crackMarkZ), Yaw(new double[] { 1, 0 }));
        }
    }

    // 段件哪幾片水面有水：依水面名稱（閘門上下游、三通左右支）
    string WaterState(string slotId, string n, WwEval ev)
    {
        if (!ev.wet.Has(slotId)) return null;
        var flowing = ev.flow.Get(slotId, 0) > 1e-6;
        string Branch(string port)
        {
            var e = ev.edges.Get(slotId)?.FirstOrDefault(x => x.port.name == port);
            if (e == null) return null;
            if (e.to != null && ev.inst.Has(e.to)) return ev.wet.Has(e.to) ? (ev.flow.Get(e.to, 0) > 1e-6 ? "flow" : "still") : null;
            return flowing ? "flow" : null;
        }
        if (n.EndsWith("downstream")) return flowing ? "flow" : null;
        if (n.EndsWith("upstream")) return flowing ? "flow" : "still";
        if (n.EndsWith("to_left")) return Branch("out_left");
        if (n.EndsWith("to_right")) return Branch("out_right");
        return flowing ? "flow" : "still";
    }

    void Refresh()
    {
        SyncModels();
        view = WaterworksRules.Preview(ctx, S);
        var ev = view.ev; var m = ev.metrics;
        labels.Clear();
        var issueSlots = new HashSet<string>(ev.issues.Where(i => i.blocking).Select(i => i.slot));
        var nextSlots = new HashSet<string>(ev.issues.Where(i => i.code == "EMPTY_NEXT").Select(i => i.next));
        foreach (var s in ctx.board.slots)
        {
            var v = slotViews[s.id];
            bool filled = v.pieceId != null, sel = s.id == selected;
            var c = sel ? new Color32(0xff, 0xd2, 0x4a, 255) : nextSlots.Contains(s.id) ? new Color32(0xff, 0x8f, 0x6b, 255) : issueSlots.Contains(s.id) ? new Color32(0xff, 0x6b, 0x5b, 255) : new Color32(255, 255, 255, 255);
            Color cc = c; cc.a = filled ? 0.95f : 0.75f;
            v.outline.sharedMaterial.color = cc; v.arrow.sharedMaterial.color = c;
            v.outline.enabled = sel || !filled || issueSlots.Contains(s.id); v.arrow.enabled = !filled;
            var txt = filled ? $"{s.id}·{v.pieceId}{(s.fixedPiece != null ? "舊" : "")}" : s.id;
            labels.Add((B(s.pos[0] + s.dir[0] * 0.5, s.pos[1] + s.dir[1] * 0.5, filled ? 1.0 : 0.45), txt,
                sel ? new Color32(0x7a, 0x4b, 0x00, 255) : issueSlots.Contains(s.id) ? new Color32(0xa2, 0x41, 0x2f, 255) : new Color32(0x23, 0x21, 0x1d, 255),
                sel ? new Color32(0xff, 0xe7, 0x9a, 240) : new Color32(246, 242, 232, 235), sel ? 17 : 14));
            foreach (var w in v.waters)
            {
                var st = WaterState(s.id, w.name, ev);
                w.target = st != null ? 1 : 0;
                w.r.sharedMaterial = st == "still" ? waterStill : waterFlow;
                w.speed = st == "flow" ? 0.3f + 0.7f * (float)ev.flow.Get(s.id, 0) : 0f;
            }
            if (v.gate != null) v.gate.open = S.design.gates.Get(s.id, false);
        }
        // 斷開接口：脈動圈＋標籤；有流水的斷口畫出漫出的水灘
        foreach (Transform t in portRoot) Destroy(t.gameObject);
        pulses.Clear();
        foreach (var i in ev.issues)
        {
            if (i.port == null) continue;
            var p = ev.inst[i.slot].ports.First(x => x.name == i.port);
            var g = new GameObject("port_" + i.slot + "_" + i.port); g.transform.SetParent(portRoot, false);
            g.transform.localPosition = B(p.pos[0], p.pos[1], 0.42);
            var pts = Enumerable.Range(0, 32).Select(k => new Vector3(Mathf.Cos(k * Mathf.PI / 16) * 0.19f, Mathf.Sin(k * Mathf.PI / 16) * 0.19f, 0)).ToArray();
            Color rc = i.blocking ? new Color32(0xff, 0x3b, 0x2f, 230) : new Color32(0xe0, 0xb0, 0x40, 230);
            var lr = Line(g.transform, pts, rc, 0.06f, true);
            pulses.Add((g.transform, lr.sharedMaterial, rc));
            labels.Add((B(p.pos[0], p.pos[1], 0.7), i.blocking ? $"{i.slot}「{i.port}」斷開" : i.code == "GATE_END" ? $"{i.slot} 閘外未接" : $"{i.slot}「{i.port}」未接", Color.white,
                i.blocking ? new Color32(170, 40, 30, 235) : new Color32(140, 110, 30, 235), 14));
            if (i.blocking && ev.flow.Get(i.slot, 0) > 1e-6)
                Prim(PrimitiveType.Cylinder, portRoot, B(p.pos[0] + p.dir[0] * 0.35, p.pos[1] + p.dir[1] * 0.35, 0.03), new Vector3(0.9f, 0.004f, 0.9f), spillMat, "spill");
        }
        // 世界狀態
        var B0 = ctx.board;
        bool Knows(string id) => S.obs.Contains(id);
        silt.SetActive(!S.ledger.siltCleared && Knows(B0.siltObs));
        crackMark.SetActive(Knows(B0.crackObs) && m.crack != "patched");
        tracks.SetActive(Knows(B0.nurseryObs));
        var unk = new[] { (B0.siltObs, B(0.55, 0.5, 0.75), "silt"), (B0.crackObs, B(-0.65, 3.6, 0.75), "crack"), (B0.nurseryObs, B(1.75, 3.2, 0.75), "nursery") };
        foreach (var (obs, pos, id) in unk)
            if (!Knows(obs) && !(id == "silt" && S.ledger.siltCleared)) labels.Add((pos, "？未調查", new Color32(0x6b, 0x54, 0x14, 255), new Color32(244, 236, 210, 242), 15));
        var lv = m.nurseryLevel;
        Color ring = lv == "risk" ? new Color32(0xd2, 0x40, 0x2f, 255) : lv == "safe" ? new Color32(0x3f, 0x9a, 0x6e, 255) : lv == "unknown" ? new Color32(0xc9, 0xa4, 0x3a, 255) : new Color32(0x9a, 0x94, 0x8a, 255);
        ring.a = 0.6f; nurseryRingMat.color = ring;
        var nr = B0.nurseryRect; var fr = B0.fieldRect; var dr = B0.drainRect;
        labels.Add((B((nr[0] + nr[2]) / 2, (nr[1] + nr[3]) / 2, 0.9), $"育幼區 · {LEVEL[lv]}{(m.nurseryGap != null && lv != "dry" ? $" {WaterworksRules.Num(WaterworksRules.JsRound(m.nurseryGap.Value * 100))} cm" : "")}",
            lv == "risk" ? new Color32(0xa2, 0x41, 0x2f, 255) : lv == "safe" ? new Color32(0x24, 0x49, 0x3f, 255) : lv == "unknown" ? new Color32(0x6b, 0x54, 0x14, 255) : new Color32(0x55, 0x55, 0x55, 255), new Color32(246, 242, 232, 235), 17));
        labels.Add((B((fr[0] + fr[2]) / 2, fr[3] - 0.35, 0.9), $"村田 · 進水 {m.villageSupply}%{(ev.unknowns.Count > 0 && m.villageSupply > 0 ? "（預估）" : "")}", new Color32(0x24, 0x49, 0x3f, 255), new Color32(246, 242, 232, 235), 17));
        labels.Add((B((dr[0] + dr[2]) / 2, (dr[1] + dr[3]) / 2, 0.9), m.drainFlow > 0 ? $"回流溝 · 泥水 {m.drainFlow}%" : "回流溝（流回溪）", new Color32(0x23, 0x21, 0x1d, 255), new Color32(246, 242, 232, 235), 14));
        var pegChoices = new[] { "restore_channel", "protect_nursery", "clear_silt" };
        for (int k = 0; k < 3; k++) if (pegs[k] != null) pegs[k].SetActive(S.ledger.completed.Any(c => c.outcomeId == WaterworksRules.CHOICES[pegChoices[k]].outcomeId));
    }

    // ------------------------------------------------------------ actions (mirrors main.js act())
    WwResult Act(string type, string slot = null, string piece = null, string choice = null, bool? open = null, string via = "key")
    {
        WwResult r = null;
        string note = null;
        switch (type)
        {
            case "select": selected = slot; break;
            case "undo": r = WaterworksRules.Undo(S); break;
            case "redo": r = WaterworksRules.Redo(S); break;
            case "place": case "remove": case "patch": case "unpatch": case "gate":
                r = WaterworksRules.Act(ctx, S, new WwAction { type = type, slot = slot ?? selected, piece = piece, open = open }); break;
            case "choose": r = WaterworksRules.Act(ctx, S, new WwAction { type = "choose", choice = S.design.choice == choice ? null : choice }); break;
            case "clear": r = WaterworksRules.Act(ctx, S, new WwAction { type = "clear" }); cardOpen = false; break;
            case "closecard": cardOpen = false; break;
            case "obs":
                obsKey = choice; S = WaterworksRules.NewSession(ctx, ctx.observationSets[obsKey]); cardOpen = false; lastResult = null;
                Toast($"換成線索組「{choice}」：重新開始（本機帳本歸零）"); break;
            case "complete":
            {
                var rid = WaterworksRules.RequestIdFor(S);
                var res = WaterworksRules.Complete(ctx, S, rid);
                note = rid;
                if (!res.ok)
                {
                    Toast(res.problems != null ? "還不能完工：\n" + string.Join("\n", res.problems.Take(3).Select(p => "・" + p.message)) : res.message, true);
                    Log(type, slot, piece, choice, via, false, res.code, rid);
                    Refresh();
                    return res;
                }
                S = res.session; lastResult = res;
                cardOpen = true; cardReplay = res.replayed;
                compare = WaterworksRules.CompareDirections(ctx, S);
                if (res.replayed) Toast($"同一請求 {rid} 重送：回傳原收據，材料沒有再扣");
                Log(type, slot, piece, choice, via, true, res.replayed ? "REPLAYED" : "COMPLETED", rid);
                Refresh();
                return res;
            }
        }
        if (r != null) { if (!r.ok) Toast(r.message, true); else S = r.session; }
        Log(type, type == "select" ? slot : (slot ?? (type == "place" || type == "remove" || type == "patch" || type == "unpatch" || type == "gate" ? selected : null)), piece, choice, via, r?.ok ?? true, r?.code, note);
        Refresh();
        return r;
    }
    void Toast(string text, bool bad = false) { toastText = text; toastBad = bad; toastT = bad ? 4.5f : 3f; }

    // 最近的槽位（中心落在那個方向；平面軸：上＝北），與 main.js step() 相同
    void Step(double[] dir)
    {
        double[] C(WwSlot s) => new[] { s.pos[0] + s.dir[0] * 0.5, s.pos[1] + s.dir[1] * 0.5 };
        var here = C(ctx.board.slots.First(s => s.id == selected));
        string best = null; double bd = double.PositiveInfinity;
        foreach (var s in ctx.board.slots)
        {
            if (s.id == selected) continue;
            var p = C(s); double dx = p[0] - here[0], dy = p[1] - here[1], along = dx * dir[0] + dy * dir[1];
            if (along <= 0.05) continue;
            var score = along + 2 * System.Math.Abs(dx * dir[1] - dy * dir[0]);
            if (score < bd) { bd = score; best = s.id; }
        }
        if (best != null) Act("select", best);
    }

    void PressPalette(int i, string via)
    {
        var sel = ctx.board.slots.First(s => s.id == selected);
        if (sel.old && selected == ctx.board.crackSlot) { if (i < PATCHES.Length) Act("patch", piece: PATCHES[i], via: via); }
        else if (sel.fixedPiece == null && i < PALETTE.Length) Act("place", piece: PALETTE[i], via: via);
    }

    // ------------------------------------------------------------ input
    Vector2 downPos, lastMouse; int downButton = -1; bool dragging;
    float lastTouchTime = -10f;
    Vector2 touchStart; bool touchDrag; float pinchDist;
    int touchTaps, touchDrags, touchPinches;

    bool OverPanel(Vector2 screen)
    {
        if (screen.x > Screen.width - PanelW) return true;
        if (cardOpen && CardRect().Contains(new Vector2(screen.x, Screen.height - screen.y))) return true;
        return false;
    }

    string SlotAt(Vector2 screen, bool preferFilled = false)
    {
        var ray = cam.ScreenPointToRay(screen);
        var hits = Physics.RaycastAll(ray, 100f);
        var best = hits.Where(h => h.collider.GetComponent<WaterworksSlotHit>() != null)
            .OrderBy(h => preferFilled && slotViews[h.collider.GetComponent<WaterworksSlotHit>().slot].pieceId == null ? 1 : 0).ThenBy(h => h.distance).FirstOrDefault();
        return best.collider != null ? best.collider.GetComponent<WaterworksSlotHit>().slot : null;
    }

    void Update()
    {
        if (deferred.Count > 0) { var list = deferred.ToList(); deferred.Clear(); foreach (var a in list) a(); }
        bool ctrl = Input.GetKey(KeyCode.LeftControl) || Input.GetKey(KeyCode.RightControl);
        bool shift = Input.GetKey(KeyCode.LeftShift) || Input.GetKey(KeyCode.RightShift);
        if (ctrl && Input.GetKeyDown(KeyCode.Z)) Act(shift ? "redo" : "undo");
        else if (ctrl && Input.GetKeyDown(KeyCode.Y)) Act("redo");
        else if (!ctrl && !Input.GetKey(KeyCode.LeftAlt))
        {
            if (Input.GetKeyDown(KeyCode.UpArrow)) Step(new double[] { 0, 1 });
            if (Input.GetKeyDown(KeyCode.DownArrow)) Step(new double[] { 0, -1 });
            if (Input.GetKeyDown(KeyCode.LeftArrow)) Step(new double[] { -1, 0 });
            if (Input.GetKeyDown(KeyCode.RightArrow)) Step(new double[] { 1, 0 });
            if (Input.GetKeyDown(KeyCode.Tab))
            {
                var i = ctx.board.slots.FindIndex(s => s.id == selected); var n = ctx.board.slots.Count;
                Act("select", ctx.board.slots[(i + (shift ? -1 : 1) + n) % n].id);
            }
            for (int k = 0; k < KEYCODES.Length; k++) if (Input.GetKeyDown(KEYCODES[k])) PressPalette(k, "key");
            if (Input.GetKeyDown(KeyCode.Delete) || Input.GetKeyDown(KeyCode.Backspace)) Act(ctx.board.slots.First(s => s.id == selected).old ? "unpatch" : "remove");
            if (Input.GetKeyDown(KeyCode.G)) Act("gate");
            foreach (var (key, choice, _) in CHOICE_KEYS) if (Input.GetKeyDown(key)) Act("choose", choice: choice);
            if (Input.GetKeyDown(KeyCode.Return) || Input.GetKeyDown(KeyCode.KeypadEnter)) Act("complete");
            if (Input.GetKeyDown(KeyCode.Escape)) Act("closecard");
            if (Input.GetKeyDown(KeyCode.F12)) endRequested = true;   // 錄影提早結束（驅動程式用）
            if (Input.GetKeyDown(KeyCode.C))
            {
                closeUp = !closeUp;
                if (!closeUp) { goalTarget = homeTarget; goalDist = homeDist; camYaw = homeYaw; camPitch = homePitch; }   // 回到總覽鏡頭 Log("camera", selected, null, closeUp ? "close" : "overview", "key", true, null, null);
            }
        }

        HandleTouch();
        if (Time.unscaledTime - lastTouchTime > 0.5f) HandleMouse();

        // camera follow
        if (closeUp) { goalTarget = B(SlotCenter(selected)[0], SlotCenter(selected)[1], 0.2); goalDist = 4.2f; }
        camTarget = Vector3.Lerp(camTarget, goalTarget, 1f - Mathf.Exp(-6f * Time.deltaTime));
        camDist = Mathf.Lerp(camDist, goalDist, 1f - Mathf.Exp(-6f * Time.deltaTime));
        ApplyCamera();
        Animate(Time.deltaTime);
        if (toastT > 0) toastT -= Time.deltaTime;
    }

    double[] SlotCenter(string id) { var s = ctx.board.slots.First(x => x.id == id); return new[] { s.pos[0] + s.dir[0] * 0.5, s.pos[1] + s.dir[1] * 0.5 }; }

    void HandleMouse()
    {
        Vector2 mp = Input.mousePosition;
        for (int b = 0; b < 2; b++)
            if (Input.GetMouseButtonDown(b) && !OverPanel(mp)) { downPos = mp; downButton = b; dragging = false; }
        if (downButton >= 0 && Input.GetMouseButton(downButton))
        {
            var d = mp - downPos;
            if (!dragging && d.magnitude > 8f) { dragging = true; Log("orbit_start", null, null, null, "mouse", true, null, null); }
            if (dragging && downButton == 0) Orbit((mp - lastMouse) * 0.12f);   // 用游標位移（驅動程式的 SetCursorPos 也算）
        }
        if (downButton >= 0 && Input.GetMouseButtonUp(downButton))
        {
            if (!dragging)
            {
                var slot = SlotAt(mp, downButton == 1);
                if (slot != null) { if (downButton == 1) Act("remove", slot, via: "mouse"); else Act("select", slot, via: "mouse"); }
            }
            else Log("orbit_end", null, null, null, "mouse", true, null, null);
            downButton = -1; dragging = false;
        }
        lastMouse = mp;
        var wheel = Input.mouseScrollDelta.y;
        if (Mathf.Abs(wheel) > 0.01f && !OverPanel(mp)) { goalDist = Mathf.Clamp(goalDist * Mathf.Pow(0.9f, wheel), 3.5f, 18f); Log("zoom", null, null, goalDist.ToString("0.0", CultureInfo.InvariantCulture), "mouse", true, null, null); }
    }

    void HandleTouch()
    {
        if (Input.touchCount == 0) return;
        lastTouchTime = Time.unscaledTime;
        if (Input.touchCount == 1)
        {
            var t = Input.GetTouch(0);
            if (t.phase == TouchPhase.Began) { touchStart = t.position; touchDrag = false; }
            else if (t.phase == TouchPhase.Moved)
            {
                if (!touchDrag && (t.position - touchStart).magnitude > 12f && !OverPanel(touchStart)) { touchDrag = true; touchDrags++; Log("touch_orbit", null, null, null, "touch", true, null, null); }
                if (touchDrag) Orbit(t.deltaPosition * 0.12f);
            }
            else if (t.phase == TouchPhase.Ended && !touchDrag && !OverPanel(t.position))
            {
                var slot = SlotAt(t.position);
                touchTaps++;
                if (slot != null) Act("select", slot, via: "touch");
                else Log("touch_tap", null, null, null, "touch", true, null, null);
            }
        }
        else if (Input.touchCount == 2)
        {
            var a = Input.GetTouch(0); var b = Input.GetTouch(1);
            var dist = (a.position - b.position).magnitude;
            if (a.phase == TouchPhase.Began || b.phase == TouchPhase.Began) { pinchDist = dist; touchPinches++; Log("touch_pinch", null, null, null, "touch", true, null, null); }
            else if (pinchDist > 1f) { goalDist = Mathf.Clamp(goalDist * pinchDist / Mathf.Max(1f, dist), 3.5f, 18f); pinchDist = dist; }
        }
    }

    void Orbit(Vector2 d)
    {
        camYaw += d.x * 3f;
        camPitch = Mathf.Clamp(camPitch - d.y * 3f, 14f, 86f);
    }

    void ApplyCamera()
    {
        cam.rect = new Rect(0, 0, 1f - PanelW / Screen.width, 1);
        var rot = Quaternion.Euler(camPitch, camYaw + 180f, 0f);
        cam.transform.position = camTarget - rot * Vector3.forward * camDist;
        cam.transform.LookAt(camTarget);
    }

    float time;
    void Animate(float dt)
    {
        time += dt;
        foreach (var v in slotViews.Values)
        {
            foreach (var w in v.waters)
            {
                w.level = Mathf.Lerp(w.level, w.target, 1f - Mathf.Exp(-5f * dt));
                w.r.enabled = w.level > 0.02f;
                w.r.transform.position = w.basePos + Vector3.up * (w.level - 1f) * 0.1f;
            }
            if (v.gate != null && v.wheel != null)
            {
                var d = v.gate.Offset - v.lastOffset;
                if (Mathf.Abs(d) > 1e-5f) v.wheel.Rotate(Vector3.up, d / 0.22f * 360f, Space.World);
                v.lastOffset = v.gate.Offset;
            }
        }
        var supply = view != null ? view.ev.metrics.villageSupply / 100f : 0f;
        fieldShown = Mathf.Lerp(fieldShown, supply, 1f - Mathf.Exp(-1.5f * dt));
        if (weir != null) weir.SetFill(fieldShown < 0.03f ? 0f : fieldShown);
        if (fieldInlet != null) fieldInlet.gameObject.SetActive(supply > 0);
        if (fieldOutlet != null) fieldOutlet.gameObject.SetActive(false);   // 疊板卡滿：出水口不出水
        var dc = drainMat.color; dc.a = Mathf.Lerp(dc.a, view != null && view.ev.metrics.drainFlow > 0 ? 0.85f : 0f, 1f - Mathf.Exp(-3f * dt)); drainMat.color = dc;
        foreach (var (t, m, c) in pulses) { var cc = c; cc.a = 0.55f + 0.4f * Mathf.Sin(time * 6f); m.color = cc; }
    }

    // ------------------------------------------------------------ IMGUI panel
    Font font;
    Texture2D white;
    GUIStyle sH2, sBody, sDim, sBtn, sBtnOn, sIssue, sLabel, sToast, sCard;
    Vector2 scroll;
    readonly Dictionary<string, Rect> buttonRects = new Dictionary<string, Rect>();

    void Styles()
    {
        if (font != null) return;
        font = Font.CreateDynamicFontFromOSFont(new[] { "Microsoft JhengHei", "Microsoft JhengHei UI", "Microsoft YaHei", "Arial" }, 14);
        white = Texture2D.whiteTexture;
        GUI.skin.font = font;
        sBody = new GUIStyle(GUI.skin.label) { font = font, fontSize = 13, wordWrap = true, richText = true };
        sBody.normal.textColor = new Color32(0x23, 0x21, 0x1d, 255);
        sH2 = new GUIStyle(sBody) { fontSize = 15, fontStyle = FontStyle.Bold };
        sDim = new GUIStyle(sBody) { fontSize = 12 }; sDim.normal.textColor = new Color32(0x6a, 0x65, 0x5c, 255);
        sBtn = new GUIStyle(GUI.skin.button) { font = font, fontSize = 12, wordWrap = true, richText = true, alignment = TextAnchor.MiddleLeft, padding = new RectOffset(6, 6, 4, 4) };
        foreach (var st in new[] { sBtn.normal, sBtn.hover, sBtn.active, sBtn.focused }) st.textColor = Color.white;
        sBtnOn = new GUIStyle(sBtn); sBtnOn.normal.textColor = sBtnOn.hover.textColor = new Color32(0xff, 0xe0, 0x80, 255); sBtnOn.fontStyle = FontStyle.Bold;
        sIssue = new GUIStyle(sBody) { fontSize = 12, padding = new RectOffset(6, 6, 4, 4) };
        sLabel = new GUIStyle(sBody) { alignment = TextAnchor.MiddleCenter, fontStyle = FontStyle.Bold, wordWrap = false };
        sToast = new GUIStyle(sBody) { fontSize = 14, alignment = TextAnchor.MiddleCenter, padding = new RectOffset(12, 12, 8, 8) };
        sToast.normal.textColor = Color.white;
        sCard = new GUIStyle(sBody) { fontSize = 13 };
    }

    readonly List<System.Action> deferred = new List<System.Action>();
    void Defer(System.Action a) => deferred.Add(a);

    void Box(Rect r, Color c) { var o = GUI.color; GUI.color = c; GUI.DrawTexture(r, white); GUI.color = o; }

    bool Button(string name, string text, bool on = false, bool enabled = true, params GUILayoutOption[] opts)
    {
        var old = GUI.enabled; GUI.enabled = enabled;
        var clicked = GUILayout.Button(text, on ? sBtnOn : sBtn, opts);
        if (Event.current.type == EventType.Repaint) { var r = GUILayoutUtility.GetLastRect(); var p = GUIUtility.GUIToScreenPoint(r.position); buttonRects[name] = new Rect(p, r.size); }
        GUI.enabled = old;
        return clicked;
    }

    string MatName(string k) => ctx.board.materialNames.Get(k) ?? k;
    string CostText(OMap<int> c) => c == null || c.Count == 0 ? "無" : string.Join("、", c.Select(kv => $"{MatName(kv.Key)} {kv.Value}"));
    static string Hex(Color32 c) => $"#{c.r:x2}{c.g:x2}{c.b:x2}";
    string LvColor(string lv) => lv == "risk" ? "#b8402c" : lv == "safe" ? "#2e7d5b" : lv == "unknown" ? "#8a6a14" : "#666666";

    void OnGUI()
    {
        Styles();
        if (view == null) return;
        // world labels
        foreach (var (world, text, fg, bg, size) in labels)
        {
            var sp = cam.WorldToScreenPoint(world);
            if (sp.z <= 0) continue;
            sLabel.fontSize = size; sLabel.normal.textColor = fg;
            var sz = sLabel.CalcSize(new GUIContent(text));
            var r = new Rect(sp.x - sz.x / 2 - 7, Screen.height - sp.y - sz.y / 2 - 3, sz.x + 14, sz.y + 6);
            if (r.xMax > Screen.width - PanelW) continue;
            Box(r, bg);
            GUI.Label(r, text, sLabel);
        }
        DrawPanel();
        if (cardOpen && lastResult?.receipt != null) DrawCard();
        if (toastT > 0 && !string.IsNullOrEmpty(toastText))
        {
            var w = Screen.width - PanelW;
            var h = sToast.CalcHeight(new GUIContent(toastText), w - 120);
            var r = new Rect(60, Screen.height - h - 24, w - 120, h);
            Box(r, toastBad ? new Color32(150, 40, 30, 235) : new Color32(30, 60, 50, 235));
            GUI.Label(r, toastText, sToast);
        }
    }

    void DrawPanel()
    {
        var area = new Rect(Screen.width - PanelW, 0, PanelW, Screen.height);
        Box(area, new Color32(246, 242, 232, 255));
        GUILayout.BeginArea(new Rect(area.x + 8, 6, PanelW - 16, Screen.height - 12));
        scroll = GUILayout.BeginScrollView(scroll);
        var ev = view.ev; var m = ev.metrics; var d = S.design; var sel = ctx.board.slots.First(s => s.id == selected);
        var L = S.ledger; var rid = WaterworksRules.RequestIdFor(S); var done = L.receipts.ContainsKey(rid);
        GUILayout.BeginHorizontal();
        if (Button("undo", "↶ 撤回 Ctrl+Z", false, S.past.Count > 0)) Defer(() => Act("undo", via: "mouse"));
        if (Button("redo", "↷ 重做 Ctrl+Y", false, S.future.Count > 0)) Defer(() => Act("redo", via: "mouse"));
        if (Button("clear", "清空重排", false, d.placed.Count > 0 || d.patches.Count > 0)) Defer(() => Act("clear", via: "mouse"));
        GUILayout.EndHorizontal();
        if (Button("complete", done ? "<b>已完工 · 再按一次（重送同一請求）</b>" : view.ready ? "<b>完工（Enter）</b>" : "完工（Enter）· 還有問題沒解決", view.ready || done, view.ready || done, GUILayout.Height(30))) Defer(() => Act("complete", via: "mouse"));
        GUILayout.Label($"請求編號 {rid}", sDim);
        GUILayout.Label(ctx.board.title, sH2);
        GUILayout.BeginHorizontal();
        GUILayout.Label("線索組", sDim, GUILayout.Width(44));
        foreach (var k in ctx.observationSets.Keys)
            if (Button("obs:" + k, k == "full" ? "完整線索" : k == "partial" ? "只找到破槽" : "沒有線索", k == obsKey)) Defer(() => Act("obs", choice: k, via: "mouse"));
        GUILayout.EndHorizontal();
        GUILayout.Label(string.Join("  ", ctx.observationLabels.Select(kv => S.obs.Contains(kv.Key) ? $"<b>【{kv.Value}】</b>" : $"<color=#a09a90>【{kv.Value}·缺】</color>")), sBody);

        GUILayout.Label($"{selected} 槽位 <size=12><color=#6a655c>入口 {WaterworksRules.FmtPos(sel.pos)} 朝{WaterworksRules.DirName(sel.dir)}</color></size>", sH2);
        if (sel.fixedPiece != null)
        {
            GUILayout.Label($"{sel.fixedPiece} {ctx.pieces[sel.fixedPiece].name}（{sel.label}）", sBody);
            if (selected == ctx.board.siltSlot) GUILayout.Label(S.ledger.siltCleared ? "已清淤。" : S.obs.Contains("silt_buildup") ? "淤了一半深，水量只剩六成；選「先清淤」方向可以排掉。" : "淤積程度沒有調查。", sDim);
            if (sel.old && selected == ctx.board.crackSlot)
            {
                GUILayout.Label("補石（B07 家族，依裂口形狀）", sBody);
                GUILayout.BeginHorizontal();
                for (int i = 0; i < PATCHES.Length; i++)
                {
                    var id = PATCHES[i]; var on = d.patches.Get(selected) == id;
                    var left = ctx.board.pieceStock.Get(id, 0) - (on ? 0 : d.patches.Values.Count(x => x == id));
                    if (Button("patch:" + id, $"[{KEYS[i]}] <b>{id}</b>\n<size=10>{ctx.pieces[id].name}</size>", on, left > 0 || on, GUILayout.Width((PanelW - 44) / 3), GUILayout.Height(36))) Defer(() => Act("patch", piece: id, via: "mouse"));
                }
                GUILayout.EndHorizontal();
                if (d.patches.Has(selected) && Button("unpatch", "拆下補石（Del）")) Defer(() => Act("unpatch", via: "mouse"));
            }
        }
        else
        {
            var fits = new HashSet<string>(WaterworksRules.FitsFor(ctx, sel));
            var placed = d.placed.Get(selected);
            for (int i = 0; i < PALETTE.Length; i += 3)
            {
                GUILayout.BeginHorizontal();
                for (int j = i; j < Mathf.Min(i + 3, PALETTE.Length); j++)
                {
                    var id = PALETTE[j]; var p = ctx.pieces[id]; var on = placed == id;
                    var left = ctx.board.pieceStock.Get(id, 0) - d.placed.Values.Count(x => x == id);
                    var kind = WaterworksRules.KIND_LABEL[p.kind] + (p.side != null ? (p.side == "left" ? "·左" : "·右") : "");
                    if (Button("place:" + id, $"[{KEYS[j]}] <b>{id}</b>{(fits.Contains(id) ? " <color=#8fe0b0>✓</color>" : "")}\n<size=10>{kind} · 剩 {left}</size>", on, left > 0 || on, GUILayout.Width((PanelW - 44) / 3), GUILayout.Height(34)))
                        Defer(() => Act("place", piece: id, via: "mouse"));
                }
                GUILayout.EndHorizontal();
            }
            GUILayout.BeginHorizontal();
            if (placed != null && Button("remove", $"拆掉 {placed}（Del／右鍵）")) Defer(() => Act("remove", via: "mouse"));
            if (placed != null && ctx.pieces[placed].kind == "gate" && Button("gate", d.gates.Get(selected, false) ? "閘門開著 · 按 G 關" : "閘門關著 · 按 G 開", d.gates.Get(selected, false))) Defer(() => Act("gate", via: "mouse"));
            GUILayout.EndHorizontal();
        }

        GUILayout.BeginHorizontal();
        foreach (var (key, choice, hint) in CHOICE_KEYS)
            if (Button("choose:" + choice, $"<b>{WaterworksRules.CHOICES[choice].label}</b>\n<size=10>{key} · {hint}</size>", d.choice == choice, true, GUILayout.Width((PanelW - 44) / 3), GUILayout.Height(36))) Defer(() => Act("choose", choice: choice, via: "mouse"));
        GUILayout.EndHorizontal();

        var meter = GUILayoutUtility.GetRect(PanelW - 40, 8);
        Box(meter, new Color32(0xdd, 0xd6, 0xc6, 255));
        Box(new Rect(meter.x, meter.y, meter.width * Mathf.Clamp01(m.villageSupply / 100f), meter.height), new Color32(0x3f, 0x8f, 0xa8, 255));
        GUILayout.Label($"<b>村田 {m.villageSupply}%</b>{(ev.unknowns.Count > 0 && m.villageSupply > 0 ? "（預估，未計未知風險）" : "")}{(m.drainFlow > 0 ? $" · 回流溝 {m.drainFlow}%" : "")}{(m.spill > 0 ? $" · <color=#b8402c><b>漫出 {m.spill}%</b></color>" : "")} · 育幼區 <color={LvColor(m.nurseryLevel)}><b>{LEVEL[m.nurseryLevel]}</b>{(m.nurseryGap != null && m.nurseryLevel != "dry" ? $"（{WaterworksRules.Num(WaterworksRules.JsRound(m.nurseryGap.Value * 100))} cm）" : "")}</color>", sBody);
        GUILayout.Label($"淤積 {SILT[m.silt]} · P4 破槽 {CRACK[m.crack]} · 花費 {CostText(view.cost)}", sDim);
        if (view.ready && d.choice != null) IssueBox($"<b>可以完工：{WaterworksRules.CHOICES[d.choice].label}</b>", new Color32(0xd6, 0xec, 0xdf, 255));
        foreach (var i in ev.issues) IssueBox($"{(i.blocking ? "✖" : "ⓘ")} {i.message}\n<b>修法：</b>{i.fix}", i.blocking ? new Color32(0xf6, 0xd9, 0xd2, 255) : new Color32(0xec, 0xe6, 0xd6, 255));
        foreach (var p in view.problems.Where(p => !ev.issues.Any(i => i.code == p.code && i.message == p.message))) IssueBox("・" + p.message, new Color32(0xec, 0xe6, 0xd6, 255));
        foreach (var u in ev.unknowns) IssueBox($"！未知風險：{u.text}", new Color32(0xf4, 0xec, 0xd2, 255));
        GUILayout.Label("本機展示材料（不入正式背包）：" + string.Join(" · ", L.stock.Select(kv => $"{MatName(kv.Key)} {kv.Value}")), sDim);
        GUILayout.Label($"本機貢獻 {L.contribution} · 完工 {L.completed.Count} 次{(L.completed.Count > 0 ? "：" + string.Join("、", L.completed.Select(c => $"#{c.seq} {c.outcomeId}")) : "")}", sDim);
        foreach (var kv in ctx.observationTexts) if (S.obs.Contains(kv.Key)) GUILayout.Label("線索 · " + kv.Value, sDim);
        GUILayout.Label("滑鼠：點槽位選取、右鍵拆、拖曳轉視角、滾輪縮放 · 鍵盤：方向鍵/Tab 換槽、1–0/- 放件、Del 拆、G 閘、Q/W/E 方向、Enter 完工、Esc 關卡片、C 特寫", sDim);
        GUILayout.EndScrollView();
        GUILayout.EndArea();
    }

    void IssueBox(string text, Color bg)
    {
        var c = new GUIContent(text);
        var r = GUILayoutUtility.GetRect(c, sIssue, GUILayout.Width(PanelW - 40));
        Box(r, bg);
        GUI.Label(r, c, sIssue);
    }

    Rect CardRect() { var w = Mathf.Min(660f, Screen.width - PanelW - 40); return new Rect((Screen.width - PanelW - w) / 2, 40, w, Screen.height - 120); }

    void DrawCard()
    {
        var r = lastResult.receipt; var o = r.outcome;
        var rect = CardRect();
        Box(new Rect(rect.x - 2, rect.y - 2, rect.width + 4, rect.height + 4), new Color32(0x3a, 0x35, 0x2c, 255));
        Box(rect, new Color32(250, 247, 239, 252));
        GUILayout.BeginArea(new Rect(rect.x + 14, rect.y + 10, rect.width - 28, rect.height - 20));
        var lv = new Dictionary<string, string> { { "risk", "有風險" }, { "safe", "安全" }, { "dry", "沒有流水" } };
        GUILayout.Label($"{(cardReplay ? "重送：回傳同一張收據" : "完工")} · {WaterworksRules.CHOICES[o.choice].label}", sH2);
        GUILayout.Label($"結果 {o.outcomeId} · 請求 {r.requestId} · 本機演示，不入正式背包", sDim);
        GUILayout.BeginHorizontal();
        var tw = GUILayout.Width((rect.width - 44) / 3);
        GUILayout.Label($"村田\n<size=20><b>{o.villageSupply}%</b></size>\n{o.villageText}", sCard, tw);
        GUILayout.Label($"育幼區\n<size=20><b><color={LvColor(o.nursery)}>{lv[o.nursery]}</color></b></size>\n{o.nurseryText}", sCard, tw);
        GUILayout.Label($"淤積／破槽\n<size=20><b>{SILT[o.silt]}</b></size>\nP4：{CRACK[o.crack]}", sCard, tw);
        GUILayout.EndHorizontal();
        foreach (var t in o.discovered) GUILayout.Label($"<color=#8a6a14><b>完工後發現：</b>{t}</color>", sCard);
        GUILayout.Label($"{(cardReplay ? "<color=#2e7d5b><b>同一請求再送一次：材料沒有再扣、貢獻沒有再加。</b></color>" : "")}扣除：{CostText(r.consumed)} · 本機貢獻 +{r.contribution}", sCard);
        GUILayout.Space(4);
        GUILayout.Label("三個方向的取捨（參考擺法、同一份線索與目前淤積狀態）", sH2);
        GUILayout.Label("<b>方向            村田今天   育幼區     淤積                 花費</b>", sCard);
        foreach (var c in compare)
            GUILayout.Label($"{(c.choice == o.choice ? "▶ " : "　")}{WaterworksRules.CHOICES[c.choice].label}（{c.title}）  <b>{c.villageSupply}%</b>  <color={LvColor(c.nursery)}>{lv[c.nursery]}</color>  {SILT[c.silt]}  {CostText(c.cost)}", sCard);
        GUILayout.FlexibleSpace();
        GUILayout.BeginHorizontal();
        if (Button("closecard", "繼續規劃（Esc）")) Defer(() => Act("closecard", via: "mouse"));
        if (Button("card:complete", "再按一次完工（Enter）")) Defer(() => Act("complete", via: "mouse"));
        GUILayout.EndHorizontal();
        GUILayout.EndArea();
    }

    // ------------------------------------------------------------ recording / logs
    string outDir;
    bool endRequested;
    StreamWriter events;
    float recStart;

    void Log(string type, string slot, string piece, string choice, string via, bool ok, string code, string requestId)
    {
        if (events == null) return;
        var sb = new StringBuilder("{");
        sb.Append($"\"t\":{(Time.realtimeSinceStartup - recStart).ToString("0.00", CultureInfo.InvariantCulture)},\"action\":{MiniJson.Quote(type)},\"via\":{MiniJson.Quote(via)}");
        if (slot != null) sb.Append($",\"slot\":{MiniJson.Quote(slot)}");
        if (piece != null) sb.Append($",\"piece\":{MiniJson.Quote(piece)}");
        if (choice != null) sb.Append($",\"arg\":{MiniJson.Quote(choice)}");
        sb.Append($",\"ok\":{(ok ? "true" : "false")}");
        if (code != null) sb.Append($",\"code\":{MiniJson.Quote(code)}");
        if (requestId != null) sb.Append($",\"requestId\":{MiniJson.Quote(requestId)}");
        // 動作之後的狀態在下一次 Refresh 才算出：這裡記錄動作前的指標；完整狀態在 frames.jsonl
        events.WriteLine(sb.Append("}").ToString());
        events.Flush();
    }

    string StateJson(float t)
    {
        var m = view.ev.metrics;
        var sb = new StringBuilder("{");
        sb.Append($"\"t\":{t.ToString("0.00", CultureInfo.InvariantCulture)},\"obs\":{MiniJson.Quote(obsKey)},\"selected\":{MiniJson.Quote(selected)}");
        sb.Append($",\"placed\":{{{string.Join(",", S.design.placed.Select(kv => $"{MiniJson.Quote(kv.Key)}:{MiniJson.Quote(kv.Value)}"))}}}");
        sb.Append($",\"patches\":{{{string.Join(",", S.design.patches.Select(kv => $"{MiniJson.Quote(kv.Key)}:{MiniJson.Quote(kv.Value)}"))}}}");
        sb.Append($",\"gates\":{{{string.Join(",", S.design.gates.Select(kv => $"{MiniJson.Quote(kv.Key)}:{(kv.Value ? "true" : "false")}"))}}}");
        sb.Append($",\"choice\":{(S.design.choice == null ? "null" : MiniJson.Quote(S.design.choice))}");
        sb.Append($",\"villageSupply\":{m.villageSupply},\"drainFlow\":{m.drainFlow},\"spill\":{m.spill},\"nursery\":{MiniJson.Quote(m.nurseryLevel)},\"silt\":{MiniJson.Quote(m.silt)},\"crack\":{MiniJson.Quote(m.crack)}");
        sb.Append($",\"issues\":[{string.Join(",", view.ev.issues.Select(i => MiniJson.Quote(i.code + ":" + i.slot + (i.port != null ? ":" + i.port : ""))))}]");
        sb.Append($",\"problems\":[{string.Join(",", view.problems.Select(p => MiniJson.Quote(p.code)))}],\"ready\":{(view.ready ? "true" : "false")}");
        sb.Append($",\"requestId\":{MiniJson.Quote(WaterworksRules.RequestIdFor(S))},\"completed\":{S.ledger.completed.Count},\"stock\":{{{string.Join(",", S.ledger.stock.Select(kv => $"{MiniJson.Quote(kv.Key)}:{kv.Value}"))}}}");
        sb.Append($",\"card\":{(cardOpen ? "true" : "false")},\"closeUp\":{(closeUp ? "true" : "false")},\"camDist\":{camDist.ToString("0.00", CultureInfo.InvariantCulture)}");
        sb.Append($",\"touchCount\":{Input.touchCount},\"touchTaps\":{touchTaps},\"touchDrags\":{touchDrags},\"touchPinches\":{touchPinches}");
        sb.Append($",\"fieldFill\":{(weir != null ? weir.fill : 0f).ToString("0.000", CultureInfo.InvariantCulture)}");
        return sb.Append("}").ToString();
    }

    void StartRecorderIfAsked()
    {
        var args = System.Environment.GetCommandLineArgs();
        var i = System.Array.IndexOf(args, "-qxOut");
        if (i < 0 || i + 1 >= args.Length) return;
        outDir = args[i + 1];
        Directory.CreateDirectory(outDir);
        recStart = Time.realtimeSinceStartup;
        events = new StreamWriter(Path.Combine(outDir, "events.jsonl"), false, new UTF8Encoding(false));
        var f = System.Array.IndexOf(args, "-qxFree");
        float seconds = f >= 0 && f + 1 < args.Length ? float.Parse(args[f + 1], CultureInfo.InvariantCulture) : 60f;
        StartCoroutine(Record(seconds));
    }

    IEnumerator Record(float seconds)
    {
        Application.targetFrameRate = 60;
        var frames = new StreamWriter(Path.Combine(outDir, "frames.jsonl"), false, new UTF8Encoding(false)) { AutoFlush = true };
        float next = 0f, nextMap = 0f; int n = 0;
        var dts = new List<float>();
        while (true)
        {
            float t = Time.realtimeSinceStartup - recStart;
            if (t > seconds || endRequested) break;
            dts.Add(Time.unscaledDeltaTime * 1000f);
            if (t >= nextMap) { WriteUiMap(); nextMap = t + 0.25f; }
            if (t >= next)
            {
                yield return new WaitForEndOfFrame();
                var tex = new Texture2D(Screen.width, Screen.height, TextureFormat.RGB24, false);
                tex.ReadPixels(new Rect(0, 0, Screen.width, Screen.height), 0, 0);
                tex.Apply();
                File.WriteAllBytes(Path.Combine(outDir, $"f{n:00000}.jpg"), tex.EncodeToJPG(88));
                Destroy(tex);
                frames.WriteLine(StateJson(t).TrimEnd('}') + $",\"frame\":{n}}}");
                n++;
                next += 0.1f;
            }
            yield return null;
        }
        frames.Close();
        var s = dts.Skip(30).OrderBy(x => x).ToList();
        File.WriteAllText(Path.Combine(outDir, "run_summary.json"),
            $"{{\"frames\":{n},\"seconds\":{(Time.realtimeSinceStartup - recStart).ToString("0.0", CultureInfo.InvariantCulture)},\"ended_by\":\"{(endRequested ? "F12" : "timer")}\",\"resolution\":[{Screen.width},{Screen.height}],\"unity\":{MiniJson.Quote(Application.unityVersion)},\"gpu\":{MiniJson.Quote(SystemInfo.graphicsDeviceName)}," +
            $"\"frame_ms_avg_while_recording\":{(s.Count > 0 ? s.Average() : 0).ToString("0.0", CultureInfo.InvariantCulture)},\"frame_ms_p95_while_recording\":{(s.Count > 0 ? s[(int)(s.Count * 0.95f)] : 0).ToString("0.0", CultureInfo.InvariantCulture)}," +
            $"\"final\":{StateJson(Time.realtimeSinceStartup - recStart)}}}\n", new UTF8Encoding(false));
        events.Close(); events = null;
        Application.Quit();
    }

    void WriteUiMap()
    {
        var sb = new StringBuilder("{\"screen\":[" + Screen.width + "," + Screen.height + "],\"slots\":{");
        sb.Append(string.Join(",", ctx.board.slots.Select(s =>
        {
            var c = SlotCenter(s.id);
            var sp = cam.WorldToScreenPoint(B(c[0], c[1], 0.15));
            return $"{MiniJson.Quote(s.id)}:[{Mathf.RoundToInt(sp.x)},{Mathf.RoundToInt(Screen.height - sp.y)}]";
        })));
        sb.Append("},\"buttons\":{");
        sb.Append(string.Join(",", buttonRects.Select(kv => $"{MiniJson.Quote(kv.Key)}:[{Mathf.RoundToInt(kv.Value.center.x)},{Mathf.RoundToInt(kv.Value.center.y)}]")));
        sb.Append("},\"selected\":" + MiniJson.Quote(selected) + ",\"card\":" + (cardOpen ? "true" : "false") + "}");
        var path = Path.Combine(outDir, "ui_map.json");
        try
        {
            File.WriteAllText(path + ".tmp", sb.ToString());
            if (File.Exists(path)) File.Delete(path);
            File.Move(path + ".tmp", path);
        }
        catch (IOException) { }   // 驅動程式正在讀：下一輪（0.25 秒後）再寫
    }
}

