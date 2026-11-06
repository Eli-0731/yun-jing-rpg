using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.InputSystem;
using UnityEngine.UI;
using YunJing.Alchemy;
using YunJing.HarvestMarket;

namespace YunJing.CreekRepair
{
    // 修水路 test scene (work pack B-56h, section 1). Thumb or mouse: tap a silt pile to step up to it, first person, then hold (weed: drag) to dig (in on a crack and the slope comes
    // down; let go on the chant's 喲 and it moves more; neither is needed), tap a marked slot and pick a
    // piece from the cart, drag round the bronze wheel to open the gate, then the camera follows the water. Keyboard: WASD pans,
    // Tab picks the next job, Space does it (holds on the wheel), 1 2 3 pick a card, Esc closes the cards. Nothing here fails.
    public sealed class CreekRepairDirector : MonoBehaviour
    {
        [Serializable] public class PieceModel { public string id; public GameObject model, water; public Vector3 scale = Vector3.one; }
        [Serializable] class BoardSlot { public string id; public float[] pos, dir; public string @fixed; }
        [Serializable] class Board { public BoardSlot[] slots; }
        class Job { public string kind, id, name; public Vector3 at; public GameObject mark; }
        class Water { public Transform t; public Vector3 full, entry; public string kind; public float from, to, reach; public Renderer[] parts; }
        class SpotView { public string pile; public CreekSpot spot; public Vector3 world, outward; public GameObject crack; public Material mat; public float nextCrumble; }
        class WeedStrand { public Transform clump; public Vector2 from; }
        public struct SoundMark { public string name; public float at, gain; }
        [Serializable] public class FieldGate { public Vector3 at; public Transform[] parts; }
        class GateView { public Button chip; public Text text; public Image back; public Water span, after; public float[] home; public float lift, show; }

        public TextAsset contentJson, boardJson;
        public PieceModel[] pieces;
        public GameObject[] pileStages;
        public GameObject weedClump, spadeModel, ditchBend, ditchBendWater, ditchShort, ditchShortWater, ditchStraight, ditchStraightWater, ditchCross, ditchCrossWater, flumeStraight, flumeWater, celebration;
        public FieldGate[] fieldGates; public Transform planSign;
        /// The trestles under the flume, the gully they stand in (covered on the other methods) and the spare ones at the site.
        public GameObject aqueductTrestles, gullyCover, spareTrestle;
        /// What the silt uncovers: a few rough stones.
        public GameObject oldStones;
        public Material freshMat;
        public Transform[] wheelParts;
        public Transform wheel; public Transform[] gateParts; public Transform[] fieldWater; public Renderer[] fieldSoil;
        public Camera view;
        /// Test recordings only: hold the camera close so the running water can be seen.
        [NonSerialized] public bool closeUp, closeUpGlide; [NonSerialized] public Vector3 closeUpFrom, closeUpAt;
        public Material waterMat, markMat, wrongMat, soilMat, stoneMat, lineMat;

        public CreekRepairSim Sim { get; private set; }
        public string LastMessage { get; private set; } = "";
        public string LastCode { get; private set; } = "";
        public CreekStep LastStep { get; private set; }
        /// Everything played, with the time, so the test recordings can carry the same sound.
        public readonly List<SoundMark> Sounds = new List<SoundMark>();
        public float ChantClock => Time.realtimeSinceStartup - chantStart;
        public bool ChantPlaying => chantOn;
        /// Seconds until the next 喲.
        public float NextYoIn { get { float c = content.chant.cycleSeconds, d = (content.chant.yoAtSeconds - ChantClock) % c; return d < 0 ? d + c : d; } }
        public bool CardsOpen => cards != null && cards.activeSelf;
        public bool Picking => picker != null && picker.activeSelf;
        public IReadOnlyList<Button> CardButtons => cardButtons;
        public IReadOnlyList<Button> PickerButtons => pickerButtons;
        public static string SavePath => Path.Combine(Application.persistentDataPath, "creek-repair-save.json");

        CreekContent content; Board board;
        readonly List<Job> jobs = new List<Job>(); readonly List<Button> cardButtons = new List<Button>(), pickerButtons = new List<Button>();
        readonly Dictionary<string, List<Water>> water = new Dictionary<string, List<Water>>();
        readonly Dictionary<string, Transform> pileRoots = new Dictionary<string, Transform>();
        readonly List<float> gateHome = new List<float>();
        readonly List<SpotView> spots = new List<SpotView>();
        readonly Dictionary<string, List<WeedStrand>> weeds = new Dictionary<string, List<WeedStrand>>();
        readonly Dictionary<string, List<GameObject>> debris = new Dictionary<string, List<GameObject>>();
        readonly Dictionary<Mesh, Vector3[]> meshVerts = new Dictionary<Mesh, Vector3[]>();
        AudioSource chantSource, fxSource; AudioClip thudClip, slumpClip, tickClip; bool chantOn; float chantStart, lampHitUntil; int chantVoices = -1;
        Image lamp; Text lampText;
        Transform dyn, spade; LineRenderer dragLine, gapLine; GameObject cards, picker, ghostWrong;
        Text status, message, wheelHint; RectTransform wheelRing; Image mudBar; float messageUntil;
        Vector3 focus, focusTarget, panOffset; float zoom = 1, zoomTarget = 1, shake; Job cardJob; int tabIndex = -1;
        // pointer
        bool wasDown, grabbedWheel, panning; Job grabbedPile; Vector3 pressWorld, pressPile; Vector2 pressScreen, lastScreen; float pressTime, wheelAngle, spinVisual; float keyCooldown;

        void Awake()
        {
            content = JsonUtility.FromJson<CreekContent>(contentJson.text); board = JsonUtility.FromJson<Board>(boardJson.text);
            foreach (var g in gateParts) gateHome.Add(g.localPosition.y);
            foreach (var w in wheelParts) wheelHome.Add(w.localRotation);
            BuildUi(); BuildSound();
            focus = focusTarget = new Vector3(0, 0, 2.6f); PlaceCamera();
        }

        // ---- start / save ----------------------------------------------------------------------------------------
        public void Begin(string method, int partySize)
        {
            Sim = new CreekRepairSim(content, method, partySize); Rebuild(); Say(Sim.M.label + "：先清淤泥，再把水路接起來", "START");
        }

        public void SaveNow() { if (Sim != null) File.WriteAllText(SavePath, Sim.Save()); }
        public void RestoreSaved() { Sim = new CreekRepairSim(content, File.ReadAllText(SavePath)); Rebuild(); }
        void Say(string text, string code) { LastMessage = text; LastCode = code; message.text = text; message.transform.parent.gameObject.SetActive(true); messageUntil = Time.time + Mathf.Max(3f, text.Length * .14f); }

        BoardSlot Slot(string id) => board.slots.First(s => s.id == id);
        static Vector3 V(float[] p, float y = 0) => new Vector3(p[0], y, p[1]);
        PieceModel Model(string id) => pieces.First(p => p.id == id);

        public static void KeepLod0(GameObject go)
        {
            foreach (var t in go.GetComponentsInChildren<Transform>(true)) if (t.name.EndsWith("_LOD1") || t.name.EndsWith("_LOD2")) t.gameObject.SetActive(false);
        }

        // Less water in the same straight-walled channel is a lower level, not a narrower sheet floating between the walls:
        // floor 0.10, full level 0.28 at a 0.40 m stream.
        static float WaterLevel(float widthM) => (.1f + .18f * widthM / .4f) / .28f;

        GameObject Spawn(GameObject prefab, BoardSlot slot, string name)
        {
            // A one-mesh FBX carries its axis conversion as a rotation on the root, so the slot's turn and the
            // flow-direction scaling live on a holder and the model keeps its own rotation.
            var holder = new GameObject(name); holder.transform.SetParent(dyn);
            holder.transform.SetPositionAndRotation(V(slot.pos), Quaternion.LookRotation(V(slot.dir), Vector3.up));
            var go = Instantiate(prefab, holder.transform); go.name = prefab.name; KeepLod0(go);
            return holder;
        }

        void Rebuild()
        {
            if (dyn != null) Destroy(dyn.gameObject);
            dyn = new GameObject("Dynamic").transform; dyn.SetParent(transform);
            jobs.Clear(); water.Clear(); pileRoots.Clear(); beds.Clear(); spoils.Clear(); bedZone.Clear(); bedOf.Clear(); spots.Clear(); weeds.Clear(); debris.Clear(); panOffset = Vector3.zero; tabIndex = -1;
            picker.SetActive(false); cards.SetActive(false);
            var m = Sim.M; var layout = Sim.Layout();
            foreach (var slot in board.slots)
            {
                if (!string.IsNullOrEmpty(slot.@fixed) && !m.route.Any(n => n.id == slot.id)) continue;   // an old piece this method's water never reaches
                string piece = layout.TryGetValue(slot.id, out var p) ? p : slot.@fixed;
                if (!string.IsNullOrEmpty(piece)) AddPiece(slot, piece);
            }
            foreach (var e in Sim.s.patches) AddPatch(e.slot, e.piece);
            foreach (var pile in m.piles) AddPile(pile);
            foreach (var w in m.work) if (Sim.Placed(w.slot) == null) AddJob("slot", w.slot, w.name, Middle(w.slot));
            foreach (var w in m.patches) if (Sim.Patched(w.slot) == null) AddJob("patch", w.slot, w.name, Middle(w.slot));
            if (m.HasAqueduct && !Sim.s.aqueduct) AddJob("aqueduct", "aqueduct", m.aqueduct.name, Middle(m.aqueduct.slots[1].slot));
            foreach (var n in m.route) if (n.kind == "ditch") AddDitch();
            AddCanal();
            var inFlow = water.Values.SelectMany(l => l);
            foreach (var w in inFlow) { w.full = w.t.localScale; w.full.y *= WaterLevel(m.waterWidthM); }
            for (int i = 0; i < gateParts.Length; i++) SetGate(i, 0);
            foreach (var r in fieldSoil) TintSoil(r, new Color(.56f, .58f, .54f));
            viewWheel = false; digging = null; digBlend = 0; leaveAt = -1; stroking = false; bladeIn = false; load = 0; digDip = 0; heights.Clear(); HideSpade(); leaveButton.gameObject.SetActive(false);
            UpdateWater(); RetargetCamera(); RefreshStatus();
            StartChant();
        }

        readonly List<Quaternion> wheelHome = new List<Quaternion>();

        Vector3 Middle(string slot) { var s = Slot(slot); return V(s.pos) + V(s.dir) * .5f; }

        void AddPiece(BoardSlot slot, string piece)
        {
            var model = Model(piece);
            var go = Spawn(model.model, slot, $"{slot.id}_{piece}"); AddProbes(go);
            if (Sim.s.method == "restore_channel" && string.IsNullOrEmpty(slot.@fixed) && piece.StartsWith("B02")) Fresh(go, 1);
            if (Sim.s.aqueduct && flumeStraight != null && (slot.id == "L3" || slot.id == "L4"))
            {
                foreach (var r in go.GetComponentsInChildren<Renderer>()) r.enabled = false;
                if (slot.id == "L3") { var f = Instantiate(flumeStraight, dyn); f.name = "CR08_Straight"; f.transform.SetPositionAndRotation(V(slot.pos) + V(slot.dir), Quaternion.LookRotation(V(slot.dir), Vector3.up)); }
            }
            if (model.water != null)
            {
                var w = Spawn(model.water, slot, $"{slot.id}_water"); foreach (var r in w.GetComponentsInChildren<Renderer>()) r.sharedMaterial = waterMat;
                if (Sim.s.aqueduct && flumeWater != null && (slot.id == "L3" || slot.id == "L4"))
                {
                    foreach (var r in w.GetComponentsInChildren<Renderer>()) r.enabled = false;
                    if (slot.id == "L3") { var fw = Instantiate(flumeWater, w.transform); fw.name = "CR08_water"; fw.transform.localPosition = Vector3.forward; fw.transform.localRotation = Quaternion.identity; foreach (var r in fw.GetComponentsInChildren<Renderer>()) r.sharedMaterial = waterMat; }
                }
                if (!water.TryGetValue(slot.id, out var list)) water[slot.id] = list = new List<Water>();
                // this piece's walls fall away at its far end: stop the water before it stands above them
                if (piece == "B02-V05") w.transform.localScale = new Vector3(1, 1, .66f);
                list.Add(new Water { t = w.transform, kind = "piece" });
            }
        }

        void AddPatch(string slot, string piece)
        {
            var s = Slot(slot); var go = Spawn(Model(piece).model, s, $"{slot}_{piece}"); AddProbes(go); Fresh(go, 1);
            go.transform.position = new Vector3(-.3315f, .06f, 3.62f);   // board.crackMark: the outside of the wall at P4
            go.transform.rotation = Quaternion.LookRotation(Vector3.right, Vector3.up);
        }

        /// Newly laid stone: same maps through YunJing/CreekFreshLit with _Fresh set.
        void Fresh(GameObject go, float amount)
        {
            if (freshMat == null) return;
            foreach (var r in go.GetComponentsInChildren<Renderer>())
                r.materials = r.sharedMaterials.Select(old =>
                {
                    var m = new Material(freshMat);
                    if (old.HasProperty("_BaseMap")) { m.SetTexture("_BaseMap", old.GetTexture("_BaseMap")); m.SetColor("_BaseColor", old.GetColor("_BaseColor")); }
                    if (old.HasProperty("_BumpMap") && old.GetTexture("_BumpMap") != null) m.SetTexture("_BumpMap", old.GetTexture("_BumpMap"));
                    m.SetFloat("_Fresh", amount); return m;
                }).ToArray();
        }

        /// A heap in the open is round. One in a channel is squeezed between the walls, across the direction the player looks along.
        static Vector3 PileFit(CreekPile pile)
        {
            if (pile.channelWidth <= 0) return Vector3.one;
            float across = Mathf.Min(1, pile.channelWidth / (1.2f * pile.scale));
            return Mathf.Abs(pile.stand[0]) > Mathf.Abs(pile.stand[1]) ? new Vector3(1, 1, across) : new Vector3(across, 1, 1);
        }

        class Carve { public Mesh mesh; public MeshFilter filter; public Vector3[] v; public Color32[] c; public Vector2[] cut; public float[] seepTo; public bool seeping; }
        readonly Dictionary<string, Carve> carves = new Dictionary<string, Carve>();

        /// One spadeful out of this heap's own mesh: a hollow where the blade went, wet and darker, its edge pushed up a little.
        void CarveAt(string id, Vector3 at, float radius, float depth)
        {
            if (!carves.TryGetValue(id, out var cv)) return;
            var toWorld = cv.filter.transform.localToWorldMatrix; var toLocal = cv.filter.transform.worldToLocalMatrix; var root = pileRoots[id]; float floor = root.position.y + .02f, seed = at.x * 7 + at.z * 3;
            for (int i = 0; i < cv.v.Length; i++)
            {
                var w = toWorld.MultiplyPoint3x4(cv.v[i]); float dx = w.x - at.x, dz = w.z - at.z, d = Mathf.Sqrt(dx * dx + dz * dz);
                if (d > radius * 1.7f) continue;
                float r = radius * (.78f + .44f * Mathf.PerlinNoise(Mathf.Atan2(dz, dx) * 1.4f + seed, seed));
                if (d < r)
                {
                    float f = 1 - d / r; f = f * f * (3 - 2 * f);
                    w.y = Mathf.Max(floor, w.y - depth * f);
                    var old = cv.c[i]; byte Dark(byte b, float k) => (byte)Mathf.Min(b, 255 * Mathf.Lerp(1, k, Mathf.Clamp01(f * 2)));
                    cv.c[i] = new Color32(Dark(old.r, .82f), Dark(old.g, .8f), Dark(old.b, .78f), 255);
                    cv.cut[i].x = Mathf.Max(cv.cut[i].x, Mathf.Clamp01(f * 1.6f)); cv.seepTo[i] = Mathf.Max(cv.seepTo[i], Mathf.SmoothStep(0, 1, (f - .35f) / .5f));
                }
                else if (d < r * 1.45f) w.y += depth * .16f * Mathf.Sin((d - r) / (r * .45f) * Mathf.PI);
                cv.v[i] = toLocal.MultiplyPoint3x4(w);
            }
            cv.mesh.SetVertices(cv.v); cv.mesh.SetColors(cv.c); cv.mesh.SetUVs(3, cv.cut); cv.seeping = true; cv.mesh.RecalculateNormals(); cv.mesh.RecalculateBounds();
            meshVerts.Remove(cv.mesh); heights.Remove(root);
        }

        static readonly Dictionary<Mesh, Mesh> planklessMeshes = new Dictionary<Mesh, Mesh>(), slackMeshes = new Dictionary<Mesh, Mesh>();

        /// The heap is one baked mesh, so the plank goes by shape: a loose piece that is long, and not the heap itself.
        static void DropPlank(GameObject stage)
        {
            foreach (var filter in stage.GetComponentsInChildren<MeshFilter>(true))
            {
                var mesh = filter.sharedMesh;
                if (!planklessMeshes.TryGetValue(mesh, out var bare)) planklessMeshes[mesh] = bare = WithoutPlank(mesh);
                filter.sharedMesh = bare;
            }
        }

        static Mesh WithoutPlank(Mesh mesh)
        {
            var verts = mesh.vertices; var tris = mesh.triangles; var parent = new int[verts.Length]; var same = new Dictionary<Vector3Int, int>();
            int Find(int i) { while (parent[i] != i) i = parent[i] = parent[parent[i]]; return i; }
            for (int i = 0; i < verts.Length; i++)
            {
                parent[i] = i; var key = Vector3Int.RoundToInt(verts[i] * 2000);
                if (same.TryGetValue(key, out var twin)) parent[Find(i)] = Find(twin); else same[key] = i;   // the same point split along a UV seam
            }
            for (int i = 0; i < tris.Length; i += 3) { parent[Find(tris[i + 1])] = Find(tris[i]); parent[Find(tris[i + 2])] = Find(tris[i]); }
            var box = new Dictionary<int, Bounds>(); var count = new Dictionary<int, int>();
            for (int i = 0; i < verts.Length; i++)
            {
                int r = Find(i); if (!box.TryGetValue(r, out var b)) { b = new Bounds(verts[i], Vector3.zero); count[r] = 0; }
                b.Encapsulate(verts[i]); box[r] = b; count[r]++;
            }
            int heap = count.OrderByDescending(c => c.Value).First().Key; var keep = new List<int>();
            bool Plank(int r) => r != heap && Mathf.Max(box[r].size.x, box[r].size.y, box[r].size.z) > box[heap].size.x * .3f;
            for (int i = 0; i < tris.Length; i += 3) if (!Plank(Find(tris[i]))) { keep.Add(tris[i]); keep.Add(tris[i + 1]); keep.Add(tris[i + 2]); }
            var bare = Instantiate(mesh); bare.subMeshCount = 1; bare.SetTriangles(keep, 0); return bare;
        }

        void AddPile(CreekPile pile)
        {
            var root = new GameObject(pile.id).transform; root.SetParent(dyn); root.position = V(pile.pos); root.localScale = PileFit(pile);
            pileRoots[pile.id] = root;
            foreach (var stage in pileStages)
            {
                var st = Instantiate(stage, root); st.transform.localPosition = Vector3.zero; st.transform.localScale = Vector3.one * .6f * pile.scale; st.name = stage.name;
                st.transform.localRotation = Quaternion.Euler(0, 205 + Mathf.Atan2(-pile.stand[0], -pile.stand[1]) * Mathf.Rad2Deg, 0) * st.transform.localRotation;   // the walking plank goes round the back, the face to where the player stands is bare mud
                if (pile.kind == "hard") Crust(st);
                DropPlank(st);   // a bright board across every heap only got in the way of seeing the mud
            }
            var heap = root.Find(pileStages[0].name).GetComponentInChildren<MeshFilter>(true); var own = Instantiate(heap.sharedMesh); Slacken(own, pile.channelWidth > 0 ? 10 : 3); heap.sharedMesh = own;
            var carved = new MaterialPropertyBlock(); var heapLook = heap.GetComponent<Renderer>(); heapLook.GetPropertyBlock(carved); carved.SetFloat("_Carved", 1); heapLook.SetPropertyBlock(carved);
            if (pile.kind == "weed") { var weedMud = new Material(heapLook.sharedMaterial); weedMud.SetTexture("_BaseMap", MudTexture()); weedMud.SetTexture("_BumpMap", Texture2D.normalTexture); weedMud.SetTextureScale("_BaseMap", Vector2.one * 3); weedMud.SetColor("_BaseColor", Color.white); weedMud.SetFloat("_Bounce", pile.channelWidth > 0 ? .55f : .12f); heapLook.sharedMaterial = weedMud; }
            if (pile.kind != "weed") MakeBed(pile, root, heap); else carves[pile.id] = new Carve { mesh = own, filter = heap, v = own.vertices, c = Enumerable.Repeat(new Color32(255, 255, 255, 255), own.vertexCount).ToArray(), cut = new Vector2[own.vertexCount], seepTo = new float[own.vertexCount] };
            var rand = new System.Random(pile.id.GetHashCode() ^ 77);
            for (int i = 0; i < pile.stones; i++)
            {
                var stone = Instantiate(oldStones, root); stone.name = "Stone_" + i; var fit = PileFit(pile); stone.transform.localScale = new Vector3(.16f / fit.x, .16f, .16f / fit.z);
                stone.transform.localPosition = new Vector3((float)(rand.NextDouble() - .5) * .9f * pile.scale, 0, (float)(rand.NextDouble() - .5) * .7f * pile.scale);
                if (bedZone.TryGetValue(pile.id, out var inZone))
                {
                    // spread along the whole bed, each in its own stretch, so they come up one at a time as the mud goes
                    float u = (i + .2f + .6f * (float)rand.NextDouble()) / pile.stones, across = (float)(rand.NextDouble() - .5) * .8f; var world = pile.channelWidth > 0 ? new Vector3(Mathf.Lerp(inZone.xMin, inZone.xMax, inZone.width > inZone.height ? u : across + .5f), 0, Mathf.Lerp(inZone.yMin, inZone.yMax, inZone.width > inZone.height ? across + .5f : u)) : root.position + Quaternion.Euler(0, u * 360, 0) * Vector3.forward * (.12f + .3f * (float)rand.NextDouble()) * pile.scale;
                    stone.transform.position = new Vector3(world.x, root.position.y, world.z);
                }
                stone.transform.localRotation = Quaternion.Euler(0, (float)rand.NextDouble() * 180, 0);
                stoneHeight[stone.transform] = stone.GetComponentInChildren<Renderer>().bounds.size.y;
                var smear = new MaterialPropertyBlock(); smear.SetColor("_BaseColor", new Color(.56f, .5f, .42f));   // these have been under mud for years
                foreach (var r in stone.GetComponentsInChildren<Renderer>()) r.SetPropertyBlock(smear);
                stone.SetActive(false);
            }
            foreach (var spot in pile.spots)
            {
                var world = root.position + new Vector3(spot.pos[0], 0, spot.pos[1]);
                var view = new SpotView { pile = pile.id, spot = spot, world = world, outward = new Vector3(spot.pos[0], 0, spot.pos[1]).normalized, nextCrumble = Time.time + 1 };
                spots.Add(view);
                if (Sim.Spent(pile.id, spot))
                {
                    if (Sim.Left(pile.id) > 0 && !beds.ContainsKey(pile.id)) { var slab = Slab(pile, view); slab.transform.position = world + view.outward * .3f; slab.transform.localScale = Vector3.Scale(new Vector3(.42f * pile.scale, .14f, .42f * pile.scale), PileFit(pile)); }
                    if (spot.reveal == "stone") RevealStone(view, true);
                    continue;
                }
                view.mat = new Material(lineMat); view.mat.SetColor("_BaseColor", new Color(.05f, .036f, .026f)); view.crack = new GameObject("Crack_" + pile.id + "_" + spot.id, typeof(MeshFilter), typeof(MeshRenderer)); view.crack.transform.SetParent(root, false);
                var lip = new Material(lineMat); lip.SetColor("_BaseColor", new Color(.3f, .24f, .18f));
                view.crack.GetComponent<MeshRenderer>().sharedMaterials = new[] { view.mat, lip };
            }
            if (pile.kind == "weed") AddWeed(pile, root);
            var job = AddJob("pile", pile.id, "淤泥", V(pile.pos)); job.mark.SetActive(false);
            UpdatePile(pile.id);
        }

        readonly Dictionary<string, CreekMudBed> beds = new Dictionary<string, CreekMudBed>(), spoils = new Dictionary<string, CreekMudBed>(); readonly Dictionary<string, Rect> bedZone = new Dictionary<string, Rect>(); readonly Dictionary<Transform, CreekMudBed> bedOf = new Dictionary<Transform, CreekMudBed>();

        /// Soft and hard mud is a real bed the spade moves: wall to wall along a stretch of channel, or the shape of the modelled heap on open ground.
        void MakeBed(CreekPile pile, Transform root, MeshFilter heap)
        {
            var mat = new Material(heap.GetComponent<Renderer>().sharedMaterial); mat.SetTexture("_BaseMap", MudTexture()); mat.SetTexture("_BumpMap", Texture2D.normalTexture); mat.SetTextureScale("_BaseMap", Vector2.one); mat.SetTextureOffset("_BaseMap", Vector2.zero);   // the heap's own texture is an atlas of its baked surface, and tiled over a grid it reads as cobbles
            mat.SetColor("_BaseColor", (pile.kind == "hard" ? new Color(1.25f, 1.16f, 1.02f) : Color.white) * (pile.channelWidth > 0 ? .62f : .8f)); mat.SetFloat("_Smoothness", pile.kind == "hard" ? .1f : .32f); mat.SetFloat("_Bounce", pile.channelWidth > 0 ? .85f : .2f); var heaped = new Material(mat); heaped.SetColor("_BaseColor", new Color(.66f, .64f, .62f)); heaped.SetFloat("_Bounce", 0); var at = root.position + Vector3.up * .012f; CreekMudBed bed; Rect zone;
            if (pile.channelWidth > 0)
            {
                // the plug: the more mud in it, the longer it is, reaching back towards where the player stands
                float length = pile.plugLength > 0 ? pile.plugLength : Mathf.Clamp(.16f * pile.mass, .75f, .95f), w = pile.channelWidth; var back = new Vector3(pile.stand[0], 0, pile.stand[1]).normalized; bool alongZ = Mathf.Abs(back.z) > Mathf.Abs(back.x);
                var middle = at + back * (length - .75f) / 2; float margin = .34f, seed = pile.id.GetHashCode() % 97, thick = Mathf.Clamp(.8f / length, 1, 1.35f);   // a short plug stands taller
                bed = new CreekMudBed("Mud_" + pile.id, dyn, mat, middle, alongZ ? w : length + margin * 2, alongZ ? length + margin * 2 : w, .02f, .9f);
                bed.Profile((x, z) =>
                {
                    float along = alongZ ? z - middle.z : x - middle.x, side = alongZ ? x - middle.x : z - middle.z;
                    float end = Mathf.SmoothStep(0, 1, Mathf.Clamp01((length / 2 + .06f - Mathf.Abs(along)) / .24f));
                    float lumps = Mathf.PerlinNoise(x * 3.1f + seed, z * 3.1f) * .09f + Mathf.PerlinNoise(x * 11 + seed, z * 11) * .03f + Mathf.PerlinNoise(x * 37, z * 37 + seed) * .012f;
                    return end * thick * (.135f + lumps - .03f * Mathf.Abs(side) / (w / 2));
                });
                bed.Rest();
                float room = w / 2 - .15f; zone = alongZ ? new Rect(middle.x - room, middle.z - length / 2, room * 2, length) : new Rect(middle.x - length / 2, middle.z - room, length, room * 2);
            }
            else
            {
                float size = 2.1f * pile.scale;
                bed = new CreekMudBed("Mud_" + pile.id, dyn, mat, at, size, size, .022f, .9f);
                bed.Stamp(heap.sharedMesh, heap.transform.localToWorldMatrix);
                float room = .86f * pile.scale; zone = new Rect(at.x - room, at.z - room, room * 2, room * 2);
            }
            bed.Stains = true; beds[pile.id] = bed; bedOf[root] = bed; bedZone[pile.id] = zone;
            spoils[pile.id] = new CreekMudBed("Spoil_" + pile.id, dyn, heaped, root.position + Vector3.up * .004f, 3.4f * Mathf.Max(1, pile.scale), 3.4f * Mathf.Max(1, pile.scale), .035f, .9f);
            spoils[pile.id].Slump = .6f;
            if (pile.channelWidth > 0) { float wallTo = pile.channelWidth / 2 + .14f; spoils[pile.id].Block(Mathf.Abs(pile.stand[1]) > Mathf.Abs(pile.stand[0]) ? new Rect(root.position.x - wallTo, root.position.z - 5, wallTo * 2, 10) : new Rect(root.position.x - 5, root.position.z - wallTo, 10, wallTo * 2)); }
            float gone = 1 - (float)(Sim.Left(pile.id) / Sim.PileMass(pile.mass)); if (gone > 0) { bed.AlreadyGone(gone); for (int i = 0; i < 24; i++) SpoilLands(pile, spoils[pile.id], root.position, i % 2 == 0 ? 1 : -1, bed.StartVolume * gone / 24); }
            if (gone >= 1) bed.go.SetActive(false);
        }

        CreekMudBed gully;
        /// The hole in the ground the raised flume crosses: earth banks falling to a lumpy floor, not a box.
        void MakeGully()
        {
            var at = gullyCover.transform.position; var size = gullyCover.transform.localScale; const float Depth = 1.5f; at.y = -Depth;
            var earth = new Material(soilMat); earth.SetTexture("_BaseMap", MudTexture()); earth.SetTextureScale("_BaseMap", Vector2.one); earth.SetColor("_BaseColor", new Color(1.05f, .96f, .84f)); earth.SetFloat("_Smoothness", .05f);
            gully = new CreekMudBed("Gully", dyn, earth, at, size.x, size.z, .05f, .9f);
            gully.Profile((x, z) =>
            {
                float rim = Mathf.Min(Mathf.Min(x - at.x + size.x / 2, at.x + size.x / 2 - x), Mathf.Min(z - at.z + size.z / 2, at.z + size.z / 2 - z));
                float down = Mathf.SmoothStep(0, 1, Mathf.Clamp01(rim / (.7f + .55f * Mathf.PerlinNoise(x * 1.7f + 41, z * 1.7f + 3))));
                return Mathf.Lerp(Depth, .03f + .16f * Mathf.PerlinNoise(x * 2.6f + 13, z * 2.6f + 29), down);
            });
            gully.Tick(0); gully.mesh.bounds = new Bounds(at + Vector3.up * Depth / 2, new Vector3(size.x + .2f, Depth + .4f, size.z + .2f));
        }

        static Texture2D mudTexture;
        /// Wet silt: dark, blotched, flecked with grit. Tiles without a seam because every octave wraps.
        static Texture2D MudTexture()
        {
            if (mudTexture != null) return mudTexture;
            const int Size = 256; mudTexture = new Texture2D(Size, Size, TextureFormat.RGB24, true) { name = "WetMud", wrapMode = TextureWrapMode.Repeat, filterMode = FilterMode.Trilinear, anisoLevel = 4 }; var rand = new System.Random(19);
            float[] Octave(int cells) { var g = new float[cells * cells]; for (int i = 0; i < g.Length; i++) g[i] = (float)rand.NextDouble(); return g; }
            int[] sizes = { 4, 9, 20, 48, 110 }; float[] weight = { .34f, .28f, .2f, .12f, .06f }; var grids = sizes.Select(Octave).ToArray(); var px = new Color[Size * Size];
            for (int y = 0; y < Size; y++) for (int x = 0; x < Size; x++)
            {
                float v = 0;
                for (int o = 0; o < sizes.Length; o++)
                {
                    int c = sizes[o]; float fx = x * c / (float)Size, fy = y * c / (float)Size; int ix = (int)fx, iy = (int)fy; fx = Mathf.SmoothStep(0, 1, fx - ix); fy = Mathf.SmoothStep(0, 1, fy - iy);
                    float Cell(int a, int b) => grids[o][(b % c) * c + a % c];
                    v += weight[o] * Mathf.Lerp(Mathf.Lerp(Cell(ix, iy), Cell(ix + 1, iy), fx), Mathf.Lerp(Cell(ix, iy + 1), Cell(ix + 1, iy + 1), fx), fy);
                }
                float grit = rand.NextDouble() < .012 ? (float)rand.NextDouble() * .1f : 0;
                var tone = Color.Lerp(new Color(.17f, .125f, .085f), new Color(.36f, .275f, .19f), Mathf.Clamp01((v - .28f) * 2.3f));
                px[y * Size + x] = tone + new Color(grit, grit * .9f, grit * .75f);
            }
            mudTexture.SetPixels(px); mudTexture.Apply(true, true); return mudTexture;
        }

        void SpoilLands(CreekPile pile, CreekMudBed spoil, Vector3 from, float way, float volume) => spoil.Land(SpoilSpot(pile, from, new Vector3(way, 0, way)), volume, .17f);

        /// Where a heave comes down: past the wall it went over, or further out along the way it was thrown.
        Vector3 SpoilSpot(CreekPile pile, Vector3 from, Vector3 way)
        {
            var root = pileRoots[pile.id].position; var dir = Flat(way).sqrMagnitude > .001f ? Flat(way).normalized : Vector3.right;
            if (pile.channelWidth <= 0) return Flat(from) + dir * UnityEngine.Random.Range(.42f, .72f) * pile.scale + Vector3.Cross(Vector3.up, dir) * UnityEngine.Random.Range(-.16f, .16f);
            bool alongZ = Mathf.Abs(pile.stand[1]) > Mathf.Abs(pile.stand[0]); var across = alongZ ? Vector3.right : Vector3.forward; var axis = alongZ ? Vector3.forward : Vector3.right;
            float side = Vector3.Dot(way, across), offset = Vector3.Dot(from - root, across); float sign = Mathf.Abs(side) > .03f ? Mathf.Sign(side) : offset != 0 ? Mathf.Sign(offset) : 1;
            return Flat(root) + across * sign * (pile.channelWidth / 2 + UnityEngine.Random.Range(.46f, .68f)) + axis * (Vector3.Dot(from - root, axis) + UnityEngine.Random.Range(-.2f, .2f));
        }

        /// Wet mud does not stand in ridges, least of all squeezed between two walls: each point eases towards the points round it.
        static void Slacken(Mesh mesh, int rounds)
        {
            var v = mesh.vertices; var tris = mesh.triangles; var same = new Dictionary<Vector3Int, int>(); var id = new int[v.Length];
            for (int i = 0; i < v.Length; i++) { var key = Vector3Int.RoundToInt(v[i] * 2000); if (!same.TryGetValue(key, out id[i])) { same[key] = same.Count; id[i] = same[key]; } }
            var at = new Vector3[same.Count]; for (int i = 0; i < v.Length; i++) at[id[i]] = v[i];
            var near = new HashSet<int>[at.Length]; for (int i = 0; i < near.Length; i++) near[i] = new HashSet<int>();
            for (int i = 0; i < tris.Length; i += 3) for (int k = 0; k < 3; k++) { int a = id[tris[i + k]], b = id[tris[i + (k + 1) % 3]]; near[a].Add(b); near[b].Add(a); }
            float low = v.Min(p => p.y), lip = low + (v.Max(p => p.y) - low) * .04f;
            for (int r = 0; r < rounds; r++)
            {
                var next = (Vector3[])at.Clone();
                for (int i = 0; i < at.Length; i++)
                {
                    if (at[i].y < lip || near[i].Count == 0) continue;   // the foot stays on the ground
                    var sum = Vector3.zero; foreach (var n in near[i]) sum += at[n];
                    next[i] = Vector3.Lerp(at[i], sum / near[i].Count, .6f);
                }
                at = next;
            }
            for (int i = 0; i < v.Length; i++) v[i] = at[id[i]];
            mesh.vertices = v; mesh.RecalculateNormals(); mesh.RecalculateBounds();
        }

        /// Crusted mud: the same mud, paler and drier.
        static void Crust(GameObject go)
        {
            var block = new MaterialPropertyBlock(); block.SetColor("_BaseColor", new Color(.66f, .58f, .47f));
            foreach (var r in go.GetComponentsInChildren<Renderer>(true)) r.SetPropertyBlock(block);
        }

        /// Strands hanging off the mud towards the bank, so the way they lie says which way to pull.
        void AddWeed(CreekPile pile, Transform root)
        {
            var list = weeds[pile.id] = new List<WeedStrand>(); var rand = new System.Random(pile.id.GetHashCode() ^ 311);
            var pull = new Vector2(pile.pull[0], pile.pull[1]); var across = new Vector2(-pull.y, pull.x); var fit = PileFit(pile);
            for (int i = 0; i < 8; i++)
            {
                var clump = Instantiate(weedClump, root).transform; clump.name = "Weed_" + i;
                // tufts on the slope facing the pull, clear of the crack on the near side and small enough that the mud under them still shows; all of them leaning the way they have to come out
                var from = across * (.12f - (i + (float)rand.NextDouble()) / 8 * .44f) + pull * ((float)rand.NextDouble() * .24f + .08f);
                float size = .3f + (float)rand.NextDouble() * .2f; var yaw = Mathf.Atan2(pull.x, pull.y) * Mathf.Rad2Deg + (float)(rand.NextDouble() - .5) * 34;
                clump.rotation = Quaternion.Euler(0, yaw, 0) * clump.rotation; clump.localScale = new Vector3(size / fit.x, size, size / fit.z);
                list.Add(new WeedStrand { clump = clump, from = from });
            }
        }

        const int HeightCells = 40; const float HeightCell = .08f;

        /// Height of what is showing of this pile at a world x, z: the highest vertex nearby, read from a grid rebuilt when the pile changes.
        float SurfaceY(Transform root, Vector3 at)
        {
            if (bedOf.TryGetValue(root, out var bed)) { float depth = bed.DepthAt(at); return bed.floorY + (depth > CreekMudBed.Hidden ? depth : 0); }
            int x = Mathf.FloorToInt((at.x - root.position.x) / HeightCell) + HeightCells / 2, z = Mathf.FloorToInt((at.z - root.position.z) / HeightCell) + HeightCells / 2;
            if (x < 0 || z < 0 || x >= HeightCells - 1 || z >= HeightCells - 1) return 0;
            if (!heights.TryGetValue(root, out var grid)) heights[root] = grid = BuildHeights(root);
            float fx = (at.x - root.position.x) / HeightCell + HeightCells / 2 - x, fz = (at.z - root.position.z) / HeightCell + HeightCells / 2 - z;
            return Mathf.Lerp(Mathf.Lerp(grid[z * HeightCells + x], grid[z * HeightCells + x + 1], fx), Mathf.Lerp(grid[(z + 1) * HeightCells + x], grid[(z + 1) * HeightCells + x + 1], fx), fz);
        }

        float[] BuildHeights(Transform root)
        {
            var grid = new float[HeightCells * HeightCells];
            foreach (var f in root.GetComponentsInChildren<MeshFilter>())
            {
                if (!f.name.EndsWith("_LOD0") || !f.sharedMesh.isReadable) continue;
                bool stone = false; for (var t = f.transform; t != root; t = t.parent) stone |= t.name.StartsWith("Stone_");
                if (stone) continue;   // a stone is seated by this height, it must not lift it
                if (!meshVerts.TryGetValue(f.sharedMesh, out var verts)) meshVerts[f.sharedMesh] = verts = f.sharedMesh.vertices;
                var m = f.transform.localToWorldMatrix;
                for (int i = 0; i < verts.Length; i++)
                {
                    var w = m.MultiplyPoint3x4(verts[i]);
                    int cx = Mathf.FloorToInt((w.x - root.position.x) / HeightCell) + HeightCells / 2, cz = Mathf.FloorToInt((w.z - root.position.z) / HeightCell) + HeightCells / 2;
                    for (int dz = -1; dz <= 1; dz++) for (int dx = -1; dx <= 1; dx++)   // the surface is sparse: each vertex speaks for the cells around it
                    {
                        int x = cx + dx, z = cz + dz; if (x < 0 || z < 0 || x >= HeightCells || z >= HeightCells) continue;
                        if (w.y > grid[z * HeightCells + x]) grid[z * HeightCells + x] = w.y;
                    }
                }
            }
            return grid;
        }

        /// Lays this pile's crack marks and weed back on its surface.
        void Drape(string id, float k)
        {
            var root = pileRoots[id];
            foreach (var view in spots.Where(v => v.pile == id && v.crack != null))
            {
                bool on = k > 0 && SurfaceY(root, view.world) > .015f;
                view.crack.SetActive(on);
                if (on) view.crack.GetComponent<MeshFilter>().sharedMesh = CrackMesh(root, view);
            }
            if (!weeds.TryGetValue(id, out var list)) return;
            int keep = Mathf.CeilToInt(list.Count * k);
            for (int i = 0; i < list.Count; i++)
            {
                var strand = list[i]; strand.clump.gameObject.SetActive(i < keep); if (i >= keep) continue;
                var at = root.position + new Vector3(strand.from.x, 0, strand.from.y); at.y = SurfaceY(root, at) - .012f; strand.clump.position = at;
            }
        }

        /// A jagged split across the slope: dark inside, with paler torn lips either side, and a short branch.
        Mesh CrackMesh(Transform root, SpotView view)
        {
            var across = Vector3.Cross(Vector3.up, view.outward);
            var verts = new List<Vector3>(); var colors = new List<Color>(); var tris = new List<int>();
            void Ribbon(Vector3 start, Vector3 dir, float length, float width, int n, int seed, float lip, Color tone)
            {
                var rand = new System.Random(view.pile.GetHashCode() ^ view.spot.id.GetHashCode() ^ seed);
                int first = verts.Count; var p = start;
                for (int i = 0; i <= n; i++)
                {
                    float k = (float)i / n, w = width * Mathf.Sin(Mathf.Lerp(.12f, 1, Mathf.Min(k, 1 - k) * 2) * Mathf.PI / 2) * .5f; var side = Vector3.Cross(Vector3.up, dir).normalized;
                    var off = p - root.position; var heapFit = PileFit(Sim.Pile(view.pile)); float heapSize = .54f * Sim.Pile(view.pile).scale; if ((off.x * off.x) / (heapSize * heapSize * heapFit.x * heapFit.x) + (off.z * off.z) / (heapSize * heapSize * heapFit.z * heapFit.z) > .7f) w = 0;   // no split past the edge of the heap
                    var a = p + side * (lip + w); var b = p + side * (lip - w);
                    a.y = SurfaceY(root, a) + .012f + (lip == 0 ? .004f : 0); b.y = SurfaceY(root, b) + .012f + (lip == 0 ? .004f : 0);
                    verts.Add(root.InverseTransformPoint(a)); verts.Add(root.InverseTransformPoint(b)); colors.Add(tone); colors.Add(tone);
                    p += dir * (length / n) + view.outward * (float)(rand.NextDouble() - .5) * .1f;
                    if (i < n) { int v = first + i * 2; tris.AddRange(new[] { v, v + 1, v + 2, v + 1, v + 3, v + 2 }); }
                }
            }
            var pale = new Color(1, 1, 1); var dark = new Color(.06f, .04f, .025f); float k = Sim.Pile(view.pile).scale * (Sim.Pile(view.pile).channelWidth > 0 ? .75f : 1);   // a smaller heap, a shorter split
            Ribbon(view.world - across * .2f * k, across, .38f * k, .006f, 8, 1, .012f, pale);
            Ribbon(view.world - across * .2f * k, across, .38f * k, .006f, 8, 1, -.012f, pale);
            Ribbon(view.world - across * .2f * k, across, .38f * k, .016f, 8, 1, 0, dark);
            Ribbon(view.world + across * .06f * k, (across + view.outward).normalized, .08f * k, .007f, 3, 2, 0, dark);
            Ribbon(view.world - across * .1f * k, (view.outward - across).normalized, .06f * k, .006f, 3, 3, 0, dark);
            var mesh = new Mesh { name = "Crack" }; mesh.SetVertices(verts); mesh.SetTriangles(tris, 0); mesh.RecalculateBounds(); return BakeTone(mesh, colors);
        }

        /// The unlit line material has one colour, so the lips are split into a second submesh.
        Mesh BakeTone(Mesh mesh, List<Color> colors)
        {
            var t = mesh.triangles; var darkTris = new List<int>(); var paleTris = new List<int>();
            for (int i = 0; i < t.Length; i += 3) (colors[t[i]].r > .5f ? paleTris : darkTris).AddRange(new[] { t[i], t[i + 1], t[i + 2], t[i], t[i + 2], t[i + 1] });   // both faces: a mirrored or steep slope must not cull it
            mesh.subMeshCount = 2; mesh.SetTriangles(darkTris, 0); mesh.SetTriangles(paleTris, 1); return mesh;
        }

        /// Clear_silt's earth ditch from the mouth of R1 to the field inlet at (0, 6): left, half a metre, left, half a metre, right.
        /// Each piece hangs from a holder at its entrance port; a left turn is the bend mirrored, so the water still runs downstream.
        void AddDitch()
        {
            var inBend = new Vector3(-.3879f, 0, -.8682f); var inShort = new Vector3(0, 0, -.25f);
            var plan = new[] { (bend: true, mirror: true), (bend: false, mirror: false), (bend: true, mirror: true), (bend: false, mirror: false), (bend: true, mirror: false) };
            float total = plan.Sum(p => p.bend ? 2f : .5f), run = 0;
            var at = new Vector3(1.75f, 0, 1.75f); var head = Vector3.right; var list = new List<Water>();
            Transform Hang(GameObject prefab, Vector3 port, bool mirror, string name)
            {
                var holder = new GameObject(name).transform; holder.SetParent(dyn); holder.SetPositionAndRotation(at, Quaternion.LookRotation(head, Vector3.up));
                if (mirror) holder.localScale = new Vector3(-1, 1, 1);
                var go = Instantiate(prefab, holder); go.name = prefab.name; go.transform.localPosition = -port; KeepLod0(go);
                return holder;
            }
            for (int i = 0; i < plan.Length; i++)
            {
                var (bend, mirror) = plan[i];
                Hang(bend ? ditchBend : ditchShort, bend ? inBend : inShort, mirror, "CR06_" + i);
                var w = Hang(bend ? ditchBendWater : ditchShortWater, bend ? inBend : inShort, mirror, "CR06_water_" + i);
                foreach (var r in w.GetComponentsInChildren<Renderer>()) r.sharedMaterial = waterMat;
                float length = bend ? 2 : .5f; list.Add(new Water { t = w, kind = "ditch", from = run / total, to = (run + length) / total }); run += length;
                var side = Vector3.Cross(Vector3.up, head) * (mirror ? -1 : 1);
                if (bend) { at += head * 1.25f + side * 1.25f; head = side; } else at += head * .5f;
            }
            water["ditch"] = list;
        }

        /// The canal: a crossing at the end of every method's route, then west, east and north to a gate in front of each field's inlet.
        void AddCanal()
        {
            Transform Hang(GameObject prefab, Vector3 port, Vector3 at, Vector3 head, bool mirror, string name)
            {
                var holder = new GameObject(name).transform; holder.SetParent(dyn); holder.SetPositionAndRotation(at, Quaternion.LookRotation(head, Vector3.up));
                if (mirror) holder.localScale = new Vector3(-1, 1, 1);
                var go = Instantiate(prefab, holder); go.name = prefab.name; go.transform.localPosition = -port; KeepLod0(go);
                return holder;
            }
            var list = new List<Water>(); var inBend = new Vector3(-.3879f, 0, -.8682f); var inShort = new Vector3(0, 0, -.25f); var inStraight = new Vector3(0, 0, -1); var inCross = new Vector3(0, 0, -.75f);
            const float Total = 6.75f;
            void Piece(GameObject body, GameObject wet, Vector3 port, Vector3 at, Vector3 head, bool mirror, string name, float run, float length)
            {
                Hang(body, port, at, head, mirror, name);
                var w = Hang(wet, port, at, head, mirror, name + "_water"); foreach (var r in w.GetComponentsInChildren<Renderer>()) r.sharedMaterial = waterMat;
                list.Add(new Water { t = w, kind = "ditch", from = run / Total, to = (run + length) / Total });
            }
            Piece(ditchCross, ditchCrossWater, inCross, new Vector3(0, 0, 6), Vector3.forward, false, "Canal_Cross", 0, .75f);
            foreach (var side in new[] { -1f, 1f })
            {
                var head = Vector3.right * side;
                Piece(ditchStraight, ditchStraightWater, inStraight, new Vector3(side * .75f, 0, 6.75f), head, false, "Canal_A" + side, .75f, 2);
                Piece(ditchStraight, ditchStraightWater, inStraight, new Vector3(side * 2.75f, 0, 6.75f), head, false, "Canal_B" + side, 2.75f, 2);
                Piece(ditchBend, ditchBendWater, inBend, new Vector3(side * 4.75f, 0, 6.75f), head, side > 0, "Canal_Bend" + side, 4.75f, 2);
            }
            Piece(ditchShort, ditchShortWater, inShort, new Vector3(0, 0, 7.5f), Vector3.forward, false, "Canal_North", .75f, 5.5f);
            water["canal"] = list;
            for (int i = 0; i < fieldGates.Length; i++)
            {
                var at = fieldGates[i].at; var view = gateViews[i]; float level = (float)Sim.Gate(content.distribution.gates[i].id).level;
                Hang(ditchShort, inShort, new Vector3(at.x, 0, 8.5f), Vector3.forward, false, "Canal_Inlet" + i);
                Water Wet(float z, string name) { var w = Hang(ditchShortWater, inShort, new Vector3(at.x, 0, z), Vector3.forward, false, name); foreach (var r in w.GetComponentsInChildren<Renderer>()) r.sharedMaterial = waterMat; var full = w.localScale; full.y *= WaterLevel(Sim.M.waterWidthM); w.gameObject.SetActive(false); return new Water { t = w, kind = "gate", full = full }; }
                view.span = Wet(8, "Gate_water" + i); view.after = Wet(8.5f, "Inlet_water" + i); view.lift = level; view.show = level > 0 ? 1 : 0;
            }
        }

        Job AddJob(string kind, string id, string name, Vector3 at)
        {
            var mark = GameObject.CreatePrimitive(PrimitiveType.Cube); Destroy(mark.GetComponent<Collider>()); mark.name = "Mark_" + id; mark.transform.SetParent(dyn);
            mark.GetComponent<Renderer>().sharedMaterial = markMat; mark.transform.position = at + Vector3.up * .22f;
            mark.transform.localScale = new Vector3(.62f, .42f, .9f);
            if (kind == "slot" || kind == "patch" || kind == "aqueduct") mark.transform.rotation = kind == "aqueduct" ? Quaternion.identity : Quaternion.LookRotation(V(Slot(id == "aqueduct" ? "P1" : id).dir));
            if (kind == "aqueduct") mark.transform.localScale = new Vector3(.62f, .42f, 2.6f);
            var job = new Job { kind = kind, id = id, name = name, at = at, mark = mark }; jobs.Add(job); return job;
        }

        void Finish(Job job) { Destroy(job.mark); jobs.Remove(job); RetargetCamera(); RefreshStatus(); SaveNow(); }

        void UpdatePile(string id)
        {
            var pile = Sim.Pile(id); var root = pileRoots[id]; float k = (float)(Sim.Left(id) / Sim.PileMass(pile.mass)), dug = pile.stones * (1 - k); int i = 0;
            UpdatePile(id, k);
            foreach (Transform c in root)
            {
                if (!c.name.StartsWith("Stone_")) continue;
                // a stone's back shows first, and it stands clear only when the mud round it has gone
                if (bedOf.ContainsKey(root)) { c.gameObject.SetActive(true); stoneGoal.Remove(c); i++; continue; }   // they lie on the floor, and the mud coming off is what shows them
                float show = Mathf.Clamp01(dug - i + .7f); i++;
                float goal = pile.channelWidth > 0 ? 0 : Mathf.Max(0, SurfaceY(root, c.position) - stoneHeight[c] * (1.05f - show * .3f));   // a heap squeezed between walls has no room to carry one
                if (show > 0 && !c.gameObject.activeSelf) c.localPosition = new Vector3(c.localPosition.x, goal - .05f, c.localPosition.z);
                c.gameObject.SetActive(show > 0); stoneGoal[c] = goal;
            }
            Drape(id, k);
        }

        readonly Dictionary<Transform, float> stoneGoal = new Dictionary<Transform, float>(), stoneHeight = new Dictionary<Transform, float>();

        /// What goes on after the blade has left: water creeps into the hollows, and stones work their way out of the mud.
        void UpdateCuts()
        {
            foreach (var cv in carves.Values)
            {
                if (!cv.seeping || cv.mesh == null) continue;
                bool more = false; float step = Time.deltaTime / 6;
                for (int i = 0; i < cv.cut.Length; i++) if (cv.cut[i].y < cv.seepTo[i]) { cv.cut[i].y = Mathf.Min(cv.seepTo[i], cv.cut[i].y + step); more = true; }
                cv.mesh.SetUVs(3, cv.cut); cv.seeping = more;
            }
            foreach (var pair in stoneGoal)
            {
                if (pair.Key == null) continue;
                var p = pair.Key.localPosition; p.y = Mathf.MoveTowards(p.y, pair.Value, Time.deltaTime * .16f); pair.Key.localPosition = p;
            }
        }

        /// Shows the pile at k of its mud.
        void UpdatePile(string id, float k)
        {
            var pile = Sim.Pile(id); var root = pileRoots[id]; float size = .6f * pile.scale; heights.Remove(root);
            // one heap all the way down: it slumps as the mud goes, and CarveAt takes the rest out where the spade went
            int stage = k <= 0 || bedOf.ContainsKey(root) ? -1 : 0, n = 0;
            foreach (Transform c in root) if (c.name.StartsWith("Pile_")) { c.gameObject.SetActive(n == stage); float wide = size * (.78f + .22f * k); c.localScale = new Vector3(wide, size * (.5f + .5f * k), wide); n++; }
        }

        IEnumerator Sink(string id, float from, float seconds)
        {
            float t = 0, to = (float)(Sim.Left(id) / Sim.PileMass(Sim.Pile(id).mass));
            while (t < seconds && pileRoots.ContainsKey(id))
            {
                t += Time.deltaTime; float k = Mathf.Clamp01(t / seconds);
                UpdatePile(id, Mathf.Lerp(from, to, 1 - (1 - k) * (1 - k))); yield return null;
            }
            if (pileRoots.ContainsKey(id)) UpdatePile(id);
        }

        void RefreshStatus()
        {
            if (Sim == null) { status.text = ""; return; }
            double total = Sim.M.piles.Sum(p => Sim.PileMass(p.mass));
            mudBar.fillAmount = (float)(1 - Sim.SiltLeft / total);
            string line = Sim.WorkDone ? (Sim.GateOpen ? (Sim.s.done ? "水進田了" : Sim.CanalFull ? "水到配水渠了：閘門隨時可以調" : "水路通水中") : "工程完成：設好閘門，再去轉閘輪") : $"淤泥還有 {Math.Ceiling(Sim.SiltLeft)} 鏟　接渠還有 {Sim.WorkLeft} 段";
            status.text = $"{Sim.M.label}\n{line}";
        }

        // ---- screen positions (the playtest finger uses these, a thumb sees the same things) -----------------------
        public Vector2 PileScreen(string id) => view.WorldToScreenPoint(pileRoots[id].position + Vector3.up * .15f);
        public Vector2 WorldScreen(Vector3 world) => view.WorldToScreenPoint(world);
        public Vector2 JobScreen(string id) => view.WorldToScreenPoint(jobs.First(j => j.id == id && j.kind != "pile").at + Vector3.up * .3f);
        /// The holder sits on B06's flange at the gate post; the rim people grab is on the shaft's outer end.
        Vector3 WheelRim => wheel.transform.position + Vector3.right * .3f;
        public Vector2 WheelScreen => view.WorldToScreenPoint(WheelRim + Vector3.up * .2f);
        public Vector3 PileWorld(string id) => pileRoots[id].position;

        // ---- input -------------------------------------------------------------------------------------------------
        static bool ReadPointer(out Vector2 at)
        {
            var t = Touchscreen.current;
            if (t != null && t.primaryTouch.press.isPressed) { at = t.primaryTouch.position.ReadValue(); return true; }
            var m = Mouse.current;
            if (m != null && m.leftButton.isPressed) { at = m.position.ReadValue(); return true; }
            at = default; return false;
        }

        bool OverUi(Vector2 at)
        {
            if (EventSystem.current == null) return false;
            var hits = new List<RaycastResult>(); EventSystem.current.RaycastAll(new PointerEventData(EventSystem.current) { position = at }, hits);
            return hits.Count > 0;
        }

        bool GroundPoint(Vector2 screen, out Vector3 world)
        {
            var ray = view.ScreenPointToRay(screen); var plane = new Plane(Vector3.up, new Vector3(0, groundY, 0));
            if (plane.Raycast(ray, out float d)) { world = ray.GetPoint(d); return true; }
            world = default; return false;
        }

        void Update()
        {
            AnimateMarks();
            if (Time.time > messageUntil && message != null) message.transform.parent.gameObject.SetActive(false);
            if (Sim != null)
            {
                HandlePointer(); HandleKeys(); UpdateChant(); UpdateCracks();
                if (Sim.GateOpen && !Sim.s.done)
                {
                    int before = Sim.s.reached.Count, moves = Sim.s.gateLog.Count;
                    Sim.AdvanceFlow(Time.deltaTime); WaterSound(1);
                    for (int i = moves; i < Sim.s.gateLog.Count; i++) if (Sim.s.gateLog[i].by == "villager" && Sim.s.gateLog[i].level > 0) { var g = Sim.GateData(Sim.s.gateLog[i].gate); Say($"遠處傳來號子，{g.label}的閘門提起來了", "VILLAGER_GATE"); Play(farChantClip, "far_chant", .3f); }
                    if (Sim.s.reached.Count != before || Sim.s.gateLog.Count != moves) { RefreshStatus(); SaveNow(); if (Sim.s.done) { Say(Sim.s.together ? "三塊田一起灌滿了" : "三塊田都灌滿了", "DONE"); WaterSound(.45f); } }
                    RetargetCamera();
                }
                UpdateWater(); UpdateWheelRing(); UpdateGateUi();
                if (leaveAt > 0 && Time.time >= leaveAt) LeaveDig();
            }
            PlaceCamera(); UpdateSpade(); UpdateCuts();
            foreach (var pair in beds) { if (Sim != null && Sim.Left(pair.Key) <= 0) pair.Value.Drain(Time.deltaTime); pair.Value.Tick(Time.deltaTime); }
            foreach (var pair in spoils) pair.Value.Tick(Time.deltaTime);
        }

        void HandlePointer()
        {
            bool down = ReadPointer(out var at);
            if (down && !wasDown) Press(at);
            else if (down && wasDown) Hold(at);
            else if (!down && wasDown) Release(lastScreen);
            wasDown = down; if (down) lastScreen = at;
        }

        void Press(Vector2 at)
        {
            grabbedPile = null; grabbedWheel = false; panning = false; pressScreen = at; pressTime = Time.time;
            pressedPile = null; groundY = .2f;
            if (OverUi(at) || CardsOpen) { pressScreen = new Vector2(-9999, 0); return; }
            if (digging != null)
            {
                pressScreen = new Vector2(-9999, 0);
                if (Sim.Left(digging.id) <= 0) return;
                bool bedHere = beds.ContainsKey(digging.id);
                if (!PilePoint(at, digging.id, out pressWorld)) { if (!bedHere) return; groundY = pileRoots[digging.id].position.y + .1f; if (!GroundPoint(at, out pressWorld)) return; }
                if (Vector3.Distance(Flat(digging.at), Flat(pressWorld)) > (bedHere ? 2.4f : 1.2f)) return;
                pressScreen = at; groundY = pressWorld.y; grabbedPile = digging; digTarget = pressWorld; pressPile = pileRoots[digging.id].position; lastStroke = Time.time;
                if (bedHere) { stroking = true; bladeIn = false; bladeSpeed = 0; load = 0; } else dragLine.enabled = true;
                return;
            }
            // the wheel is beside the first silt: a press on a pile still left is a dig, not a turn
            bool onPile = GroundPoint(at, out var pressed) && jobs.Any(j => j.kind == "pile" && Sim.Left(j.id) > 0 && Vector3.Distance(Flat(j.at), Flat(pressed)) < .45f);
            float toWheel = (at - WheelScreen).magnitude * 1080f / Screen.height;
            if (toWheel < 60 || (!onPile && toWheel < 170))
            {
                grabbedWheel = true; wheelAngle = Mathf.Atan2(at.y - WheelScreen.y, at.x - WheelScreen.x) * Mathf.Rad2Deg;
                var r = Sim.WorkDone ? default : Sim.TurnWheel(30);
                if (!Sim.WorkDone) { Say(r.message, r.code); grabbedWheel = false; }
                return;
            }
            if (!GroundPoint(at, out pressWorld)) return;
            Job best = null; float bestD = .8f;
            foreach (var j in jobs.Where(j => j.kind == "pile" && Sim.Left(j.id) > 0))
            {
                float d = Vector3.Distance(Flat(j.at), Flat(pressWorld));
                if (d < bestD) { bestD = d; best = j; }
            }
            pressedPile = best; pressedPileD = bestD;
        }

        void Hold(Vector2 at)
        {
            if (grabbedWheel)
            {
                float a = Mathf.Atan2(at.y - WheelScreen.y, at.x - WheelScreen.x) * Mathf.Rad2Deg;
                float delta = Mathf.DeltaAngle(a, wheelAngle); wheelAngle = a;   // clockwise on screen opens
                if (Mathf.Abs(delta) > .01f) TurnBy(delta);
                return;
            }
            if (!GroundPoint(at, out var world)) return;
            if (grabbedPile != null)
            {
                digTarget = world;
                if (stroking) return;
                var mud = Sim.Mud(Sim.Pile(grabbedPile.id).kind);
                dragLine.material.SetColor("_BaseColor", Vector3.Distance(Flat(world), Flat(pressWorld)) >= mud.minDragM ? AlchemyUi.Jade : new Color(.85f, .62f, .25f));
            }
            else if (digging == null && (at - pressScreen).magnitude > 24 && pressScreen.x > -9000)
            {
                panning = true;
                if (GroundPoint(lastScreen, out var prev)) panOffset += Flat(prev - world);
            }
        }

        void Release(Vector2 at)
        {
            if (grabbedWheel) { grabbedWheel = false; return; }
            if (pressScreen.x < -9000) return;
            bool tap = (at - pressScreen).magnitude < 24 && Time.time - pressTime < .6f;
            if (tap && !panning && digging == null)
            {
                var job = NearestWork(at);
                // whichever the thumb is nearer: a mark can sit right beside a pile
                if (pressedPile != null && (job == null || pressedPileD < Vector3.Distance(Flat(job.at), Flat(pressWorld)))) { EnterDig(pressedPile); return; }
                if (job != null) { OpenJob(job); return; }
            }
            if (stroking) EndStroke();
            else if (grabbedPile != null && GroundPoint(at, out var world))
            {
                var way = Flat(world) - Flat(pressWorld);
                DoScoop(grabbedPile.id, way.magnitude, Time.time - pressTime, new double[] { pressWorld.x - pressPile.x, pressWorld.z - pressPile.z }, new double[] { way.x, way.z });
            }
            grabbedPile = null; groundY = .2f; if (dragLine != null) dragLine.enabled = false;
        }

        /// Where a thumb lands on the mud as it is showing now, walking down the ray until it goes under the surface.
        bool PilePoint(Vector2 screen, string id, out Vector3 world)
        {
            var ray = view.ScreenPointToRay(screen); var root = pileRoots[id];
            if (ray.direction.y < -.01f)
            {
                float d = Mathf.Max(0, (ray.origin.y - 1.6f) / -ray.direction.y);
                for (int i = 0; i < 120; i++, d += .03f)
                {
                    var p = ray.GetPoint(d); if (p.y < .02f) break;
                    if (p.y <= SurfaceY(root, p)) { world = p; return true; }
                }
            }
            groundY = .2f; return GroundPoint(screen, out world);
        }

        // ---- first person at a pile ------------------------------------------------------------------------------------
        /// The player steps up to the pile: the camera comes down to eye height just short of it, the spade in hand.
        void EnterDig(Job job)
        {
            digging = job; leaveAt = -1; focusTarget = job.at; panOffset = Vector3.zero;
            var pile = Sim.Pile(job.id); var root = pileRoots[job.id].position;
            var back = new Vector3((float)pile.stand[0], 0, (float)pile.stand[1]).normalized;   // the open side of this pile
            // from well back, looking down the long way: the mud fills the frame, and a spade this far from the eye runs out of the frame instead of waving in front of it
            var middle = bedZone.TryGetValue(job.id, out var zone) ? new Vector3(zone.center.x, root.y, zone.center.y) : root; float across = !bedZone.ContainsKey(job.id) ? 1.2f : pile.channelWidth > 0 ? Mathf.Max(zone.width, zone.height) : 1.5f * pile.scale; digPan = Vector3.zero; digPanTo = Vector3.zero;
            digEye = middle + (back * .56f + Vector3.up * .83f).normalized * (1.05f + 1.05f * (pile.channelWidth > 0 ? Mathf.Min(across, 1.1f) : across));
            digLook = Quaternion.LookRotation(middle + Vector3.up * .08f - digEye, Vector3.up); digRight = digLook * Vector3.right;
            digRest = middle + back * across * .74f + digRight * (pile.channelWidth > 0 ? 0 : .3f * pile.scale); bladeAt = digRest; digTarget = digRest; openWay = Vector3.zero; bladeLift = 0; hover = .1f; 
            ShowOccluders(); HideOccluders(digEye, middle, across);
            ShowSpade(digRest); leaveButton.gameObject.SetActive(true);
            foreach (var j in jobs) j.mark.SetActive(false);   // a mark this close is a sheet of glass in front of the eye
        }

        readonly List<Renderer> occluders = new List<Renderer>();
        /// A timber or a stack that stands above the channel between the eye and the mud would be a wall across the frame: it steps aside until the player stands up. Nothing low is touched.
        void HideOccluders(Vector3 eye, Vector3 middle, float across)
        {
            var aims = new[] { middle, middle + digRight * .2f, middle - digRight * .2f, middle + Flat(digLook * Vector3.up).normalized * across * .5f, middle - Flat(digLook * Vector3.up).normalized * across * .5f };
            foreach (var r in FindObjectsByType<MeshRenderer>(FindObjectsSortMode.None))
            {
                if (!r.enabled || r.transform.IsChildOf(spade != null ? spade : view.transform) || r.bounds.max.y < middle.y + .55f || beds.Values.Concat(spoils.Values).Any(b => r.gameObject == b.go)) continue;
                bool hit = false;
                foreach (var aim in aims) { for (float t = .05f; t < .95f && !hit; t += .03f) { var p = Vector3.Lerp(eye, aim, t); hit = p.y > middle.y + .55f && r.bounds.Contains(p); } if (hit) break; }
                if (hit) { r.enabled = false; occluders.Add(r); }
            }
        }
        void ShowOccluders() { foreach (var r in occluders) if (r != null) r.enabled = true; occluders.Clear(); }

        public void EnterDig(string pile) => EnterDig(jobs.First(j => j.kind == "pile" && j.id == pile));

        public void LeaveDig()
        {
            ShowOccluders(); digging = null; leaveAt = -1; grabbedPile = null; stroking = false; bladeIn = false; load = 0; digDip = 0; groundY = .2f; HideSpade(); leaveButton.gameObject.SetActive(false); RetargetCamera();
            foreach (var j in jobs) j.mark.SetActive(j.kind != "pile");
        }

        /// The blade rides the mud and lags behind the thumb by how heavy this mud is; the shaft runs back to a hand just out of frame.
        void UpdateSpade()
        {
            if (digging == null || spade == null) return;
            var pile = Sim.Pile(digging.id); var root = pileRoots[digging.id]; var mud = Sim.Mud(pile.kind); beds.TryGetValue(digging.id, out var bed);
            var target = grabbedPile != null ? digTarget : digRest;
            if (bed != null) { var zone = bedZone[digging.id]; target.x = Mathf.Clamp(target.x, zone.xMin, zone.xMax); target.z = Mathf.Clamp(target.z, zone.yMin, zone.yMax); }
            else if (pile.channelWidth > 0)
            {
                // the blade stays between the walls, wherever the finger goes
                var centre = root.position; float room = pile.channelWidth / 2 - .15f;
                if (Mathf.Abs(pile.stand[0]) > Mathf.Abs(pile.stand[1])) target.z = Mathf.Clamp(target.z, centre.z - room, centre.z + room);
                else target.x = Mathf.Clamp(target.x, centre.x - room, centre.x + room);
            }
            var flat = Flat(bladeAt); var next = flat; bladeGoal = Flat(target);
            if (bed != null && stroking)
            {
                // the arms: an empty blade comes quickly, a full one barely moves, and it takes a moment to get going and to stop
                bool lighter = chantOn && Sim.IsOnBeat(ChantClock);
                float want = bladeIn ? mud.bladeSpeedMps * (lighter ? 1.3f : 1) / (1 + mud.loadDrag * load * load) : 4;
                bladeSpeed = Mathf.MoveTowards(bladeSpeed, want, Time.deltaTime * (!bladeIn ? 30 : want < bladeSpeed ? 5 : 1.6f));
                next = Vector3.MoveTowards(flat, Flat(target), bladeSpeed * Time.deltaTime);
                if (!bladeIn) { if ((next - Flat(target)).sqrMagnitude < .0004f) { bladeIn = true; bed.BeginStroke(); bladeSpeed = 0; strokeRun = 0; StrokeLanded(pile); } }
                else if ((next - flat).sqrMagnitude > 1e-8f) Scrape(bed, pile, mud, flat, next);
            }
            else next = Vector3.Lerp(flat, Flat(target), Mathf.Clamp01(Time.deltaTime * (bed != null ? 2.2f : grabbedPile != null ? mud.followRate : 5)));
            lastBladeSpeed = (next - flat).magnitude / Mathf.Max(Time.deltaTime, .001f); bladeAt = next;
            bool touching = bed != null ? stroking && bladeIn : grabbedPile != null;
            hover = Mathf.MoveTowards(hover, touching ? .018f : .11f, Time.deltaTime * (touching ? 1.4f : .5f));
            bladeLift = Mathf.MoveTowards(bladeLift, 0, Time.deltaTime / .4f);
            var cam = view.transform; bool walled = pile.channelWidth > 0; var homeward = new Vector3(pile.stand[0], 0, pile.stand[1]);
            homeward = walled ? (Mathf.Abs(homeward.x) > Mathf.Abs(homeward.z) ? new Vector3(Mathf.Sign(homeward.x), 0, 0) : new Vector3(0, 0, Mathf.Sign(homeward.z))) : OpenWay(bladeAt, Flat(cam.position - bladeAt).normalized);
            float under = Mathf.Max(SurfaceY(root, bladeAt), Mathf.Max(SurfaceY(root, bladeAt + homeward * .12f) - .03f, SurfaceY(root, bladeAt + homeward * .22f) - .05f));   // the blade lies on the mud, not in it
            if (walled) foreach (var side in new[] { -SpadeHalf, 0, SpadeHalf }) foreach (var along in new[] { -.03f, .06f, .14f, .22f, .3f }) under = Mathf.Max(under, Mathf.Max(FloorAt(bladeAt + digRight * side + homeward * along, under), spade.gameObject.activeSelf ? FloorAt(bladeAt + spade.right * side + homeward * along, under) : under));   // nor in the stone: the floor is not one height
            var tip = bladeAt + Vector3.up * (under + hover + .2f * Mathf.Sin(bladeLift * Mathf.PI));
            // the weight comes up through the arms and the eye drops with it
            float dipTo = stroking && bladeIn ? .012f + .05f * Mathf.Min(1, load) : 0; digDip = Mathf.Lerp(digDip, dipTo, Mathf.Clamp01(Time.deltaTime * (dipTo > digDip ? 4 : 9)));
            if (!spade.gameObject.activeSelf) spade.gameObject.SetActive(true);
            // held the way a person holds one: the shaft comes from the player's side, along the channel where there are walls, as low as the mud lets it; the blade is set at an angle to the shaft and never turns about it, so it lies on the mud and shows its face from above
            var wallSide = Mathf.Abs(homeward.x) > Mathf.Abs(homeward.z) ? Vector3.forward : Vector3.right; var wallCentre = bedZone.TryGetValue(pile.id, out var wallZone) ? new Vector3(wallZone.center.x, 0, wallZone.center.y) : root.position; float wallRoom = pile.channelWidth / 2 - .05f;
            var seat = tip; var shaft = Vector3.up;
            void Pose(float at)
            {
                float tilt = at * Mathf.Deg2Rad; shaft = ShaftDir(homeward, at, walled); var turn = Quaternion.LookRotation(Vector3.up * Mathf.Cos(tilt) - Flat(shaft).normalized * Mathf.Sin(tilt), shaft);
                seat = tip; spade.SetPositionAndRotation(seat - turn * Vector3.Scale(bentTip, spade.localScale), turn);
                if (!walled) return;
                // swung out to the side, the back of the blade would cut into the wall: the whole blade slides in by that much
                var heel = spade.TransformPoint(0, bentTip.y + bladeReach, 0); var across = spade.right * SpadeHalf; float over = 0;
                foreach (var p in new[] { tip + across, tip - across, heel + across, heel - across }) { float d = Vector3.Dot(p - wallCentre, wallSide); if (Mathf.Abs(d) > wallRoom && Mathf.Abs(d) - wallRoom > Mathf.Abs(over)) over = d - Mathf.Sign(d) * wallRoom;
                    // and a bend's inner wall stands closer than the channel's width says
                    var mid = p - wallSide * d; if (Mathf.Abs(d) > .01f && Physics.Raycast(mid, wallSide * Mathf.Sign(d), out var wall, Mathf.Abs(d) + .02f, 1 << ProbeLayer)) { float past = Mathf.Abs(d) - (wall.distance - .02f); if (past > Mathf.Abs(over)) over = Mathf.Sign(d) * past; } }
                seat = tip - wallSide * over; spade.position -= wallSide * over;
            }
            bool Blocked(float at) { Pose(at); var heel = spade.TransformPoint(0, bentTip.y + bladeReach, 0); for (float along = .05f; along < 1f; along += .08f) { var p = heel + shaft * along; if (SurfaceY(root, p) > p.y) return true; } return ProbeHits(heel, heel + shaft * 1.4f); }
            float lean = BladeBend, clear = BladeBend;
            for (float d = .06f; d < 1.2f; d += .08f) { float rise = SurfaceY(root, tip + homeward * d) + .025f - tip.y; if (rise > 0) lean = Mathf.Max(lean, Mathf.Atan2(rise, d) * Mathf.Rad2Deg); }
            while (clear < ShaftSteepest && Blocked(clear)) clear += 3;   // whatever stands in the shaft's way, it goes over, and never through on the way there
            clear = Mathf.Min(clear, ShaftSteepest);
            bladeLean = bladeLean <= 0 ? Mathf.Max(lean, clear) : Mathf.Max(clear, Mathf.MoveTowards(bladeLean, Mathf.Max(lean, clear), Time.deltaTime * 130));
            Pose(bladeLean);
            // swung round, or dug beside a piece rather than in one, the blade no longer lies along any channel: whatever of the stone floor is under it where it really is, it rides over
            {
                var bladeEnd = spade.TransformPoint(0, bentTip.y + bladeReach, 0); float ride = 0;
                for (float along = 0; along <= 1.001f; along += .125f) for (float across = -1; across <= 1.001f; across += .5f)
                { var p = Vector3.Lerp(seat, bladeEnd, along) + spade.right * SpadeHalf * across; float rise = FloorAt(p, p.y) - p.y; if (rise < .08f) ride = Mathf.Max(ride, rise); }   // higher than that is the top of a wall, which the slide above has dealt with
                if (ride > 0) { spade.position += Vector3.up * (ride + .004f); seat += Vector3.up * (ride + .004f); }
                // nor does an edge of it go on through a wall that crosses the channel where the piece ends, seen from either side of the wall: the blade stops short of it
                var side_ = spade.right * SpadeHalf;
                for (int pass = 0; pass < 3; pass++)
                {
                    bladeEnd = spade.TransformPoint(0, bentTip.y + bladeReach, 0); var back = Vector3.zero;
                    foreach (var (from, to) in new[] { (seat + side_, bladeEnd + side_), (bladeEnd + side_, seat + side_), (seat - side_, bladeEnd - side_), (bladeEnd - side_, seat - side_), (seat + side_, seat - side_), (seat - side_, seat + side_) })
                    {
                        var way = to - from; float nearest = way.magnitude;
                        bool hitWall = false;
                        foreach (var hit in Physics.RaycastAll(from, way, way.magnitude, 1 << ProbeLayer))
                        {
                            var shown = hit.collider.transform.parent != null ? hit.collider.transform.parent.GetComponent<Renderer>() : null;
                            if (shown != null && shown.enabled && hit.distance <= nearest) { nearest = hit.distance; hitWall = true; }
                        }
                        if (hitWall) { float past = way.magnitude - nearest; var push = Flat(way).normalized * (nearest < past ? nearest + .012f : -(past + .012f)); if (push.sqrMagnitude > back.sqrMagnitude) back = push; }
                    }
                    if (back == Vector3.zero) break;
                    spade.position += back; seat += back;
                }
            }
            MeasureSpade(pile, root, seat, shaft);
            if (dragLine.enabled)
            {
                // drawn part way to the eye, so the mound can't hide it
                dragLine.startWidth = dragLine.endWidth = .004f;
                dragLine.SetPosition(0, Vector3.Lerp(cam.position, pressWorld, .4f)); dragLine.SetPosition(1, Vector3.Lerp(cam.position, tip, .4f));
            }
        }

        /// Raised high, a shaft along the channel would run straight at the eye; it swings out to the right hand once it stands above the walls.
        Vector3 ShaftDir(Vector3 homeward, float lean, bool walled)
        {
            var ground = homeward; if (walled) { float yaw = 24 * Mathf.Deg2Rad * Mathf.Clamp01((lean - 30) / 18); ground = (homeward * Mathf.Cos(yaw) + digRight * Mathf.Sin(yaw)).normalized; }
            return ground * Mathf.Cos(lean * Mathf.Deg2Rad) + Vector3.up * Mathf.Sin(lean * Mathf.Deg2Rad);
        }
        const float ShaftSteepest = 62;

        /// The stone or timber under this point, if it stands above `least`.
        float FloorAt(Vector3 at, float least) => Physics.Raycast(new Vector3(at.x, least + .3f, at.z), Vector3.down, out var hit, .3f, 1 << ProbeLayer) ? hit.point.y : least;

        /// Towards the player, or the nearest way round to it with nothing standing in the way of the shaft; turned to, not jumped to.
        Vector3 OpenWay(Vector3 from, Vector3 want)
        {
            var clear = want;
            foreach (var a in new[] { 0, 20, -20, 40, -40, 60, -60, 80, -80, 100, -100 })
            {
                var way = Quaternion.AngleAxis(a, Vector3.up) * want;
                if (!Physics.Raycast(from + way * .22f + Vector3.up * .12f, (way + Vector3.up * .67f).normalized, 1.1f, 1 << ProbeLayer)) { clear = way; break; }
            }
            openWay = openWay == Vector3.zero ? clear : Vector3.RotateTowards(openWay, clear, Time.deltaTime * 2.2f, 0);
            return openWay;
        }
        Vector3 openWay;

        /// How close the spade came to going through something, measured on the blade's corners and along the shaft, not guessed from the picture.
        void MeasureSpade(CreekPile pile, Transform root, Vector3 tip, Vector3 shaft)
        {
            var heel = spade.TransformPoint(0, bentTip.y + bladeReach, 0); var across = spade.right * SpadeHalf;
            if (pile.channelWidth > 0)
            {
                var side = Mathf.Abs(pile.stand[0]) > Mathf.Abs(pile.stand[1]) ? Vector3.forward : Vector3.right; var centre = bedZone.TryGetValue(pile.id, out var zone) ? new Vector3(zone.center.x, 0, zone.center.y) : root.position;
                foreach (var p in new[] { tip + across, tip - across, heel + across, heel - across })
                    SpadeGap = Mathf.Min(SpadeGap, pile.channelWidth / 2 - Mathf.Abs(Vector3.Dot(p - centre, side)));
            }
            for (float along = .05f; along < 1f; along += .08f) { var p = heel + shaft * along; SpadeBuried = Mathf.Max(SpadeBuried, SurfaceY(root, p) - p.y); }
            Probe(tip + across, tip - across); Probe(tip + across, heel + across); Probe(tip - across, heel - across);
            // only what the eye sees: past the edge of the frame the shaft is in the hands
            float seen = 0; while (seen < 1.4f) { var vp = view.WorldToViewportPoint(heel + shaft * (seen + .05f)); if (vp.z <= 0 || vp.x < 0 || vp.x > 1 || vp.y < 0 || vp.y > 1) break; seen += .05f; }
            if (seen > 0) Probe(heel, heel + shaft * seen);
        }
        /// The solid things the spade has passed through, by name: every modelled piece carries a mesh the builder laid on its own layer for this.
        void Probe(Vector3 a, Vector3 b)
        {
            foreach (var pair in new[] { (a, b), (b, a) })
                foreach (var hit in Physics.RaycastAll(pair.Item1, pair.Item2 - pair.Item1, (pair.Item2 - pair.Item1).magnitude, 1 << ProbeLayer))
                {
                    var shown = hit.collider.transform.parent != null ? hit.collider.transform.parent.GetComponent<Renderer>() : null;
                    if (shown != null && shown.enabled && SpadeHits.Add(shown.name)) Debug.Log($"CREEK spade through {shown.name} digging {digging?.id} at {hit.point} from {pair.Item1} to {pair.Item2} normal {hit.normal} seat {spade.position}");
                }
        }
        /// Whether a shown solid lies between two points, from either side of its surface.
        bool ProbeHits(Vector3 a, Vector3 b)
        {
            foreach (var pair in new[] { (a, b), (b, a) })
                foreach (var hit in Physics.RaycastAll(pair.Item1, pair.Item2 - pair.Item1, (pair.Item2 - pair.Item1).magnitude, 1 << ProbeLayer))
                {
                    var shown = hit.collider.transform.parent != null ? hit.collider.transform.parent.GetComponent<Renderer>() : null;
                    if (shown != null && shown.enabled) return true;
                }
            return false;
        }
        /// Pieces laid while playing get the same as the ones the builder laid.
        static void AddProbes(GameObject go)
        {
            foreach (var f in go.GetComponentsInChildren<MeshFilter>(true))
            {
                if (f.sharedMesh == null || !f.sharedMesh.isReadable || f.name.Contains("LOD1") || f.name.Contains("LOD2") || f.name.ToLowerInvariant().Contains("water")) continue;
                var probe = new GameObject("SpadeProbe") { layer = ProbeLayer }; probe.transform.SetParent(f.transform, false); probe.AddComponent<MeshCollider>().sharedMesh = f.sharedMesh;
            }
        }
        /// Whether the probes are there at all, so a clean run means something.
        public bool ProbeSees(Vector3 a, Vector3 b) => Physics.Raycast(a, b - a, (b - a).magnitude, 1 << ProbeLayer);
        public const int ProbeLayer = 2;
        public readonly HashSet<string> SpadeHits = new HashSet<string>();
        /// The least room left between the spade and a channel wall, and the deepest the shaft has gone into mud, since the player stepped up.
        public float SpadeGap { get; private set; } = 9; public float SpadeBuried { get; private set; }
        const float SpadeHalf = .0975f, BladeBend = 24; float bladeLean, bladeReach; Vector3 bentTip;
        Vector3 bladeGoal, digPan, digPanTo; bool stroking, bladeIn; float bladeSpeed, lastBladeSpeed, load, hover = .1f; Vector3 bladeWay = Vector3.forward; readonly HashSet<Transform> clinked = new HashSet<Transform>();
        const float BladeHalf = .105f, FinishedAt = .82f, SmallestHeave = .0005f, FullStroke = .3f; float strokeRun;
        /// How full the blade is, 1 is about one mass unit of this pile; how fast it is really going; how far it has fallen behind the thumb.
        public float BladeLoad => load; public float BladeSpeed => lastBladeSpeed; public bool BladeIn => bladeIn; public float BladeLag => Vector3.Distance(Flat(bladeAt), bladeGoal); public bool CameraSettled => digBlend <= 0;
        public int HiddenWhileDigging => occluders.Count;
        public CreekMudBed Bed(string id) => beds.TryGetValue(id, out var b) ? b : null;
        public CreekMudBed Spoil(string id) => spoils.TryGetValue(id, out var b) ? b : null;
        public Rect BedZone(string id) => bedZone[id];
        /// Old stones the mud has come off of, seen by what is really left on top of them.
        public int StonesClear(string id)
        {
            var root = pileRoots[id]; var bed = beds[id]; int n = 0;
            foreach (Transform c in root) if (c.name.StartsWith("Stone_") && bed.DepthAt(c.position) < stoneHeight[c] * .75f) n++;
            return n;
        }

        float Capacity(CreekPile pile, CreekMudBed bed) => bed.StartVolume / pile.mass * .8f;

        void StrokeLanded(CreekPile pile) { clinked.Clear(); var take = $"dig_{pile.kind}{digTake++ % 3}"; Play(digClips[take], take, .3f); shake = Mathf.Max(shake, .004f); lastStroke = Time.time; }

        /// One frame of the blade through the mud.
        void Scrape(CreekMudBed bed, CreekPile pile, CreekMudKind mud, Vector3 from, Vector3 to)
        {
            Vector2 a = new Vector2(from.x, from.z), b = new Vector2(to.x, to.z);
            var way = (to - from).normalized; bladeWay = Vector3.Slerp(bladeWay, way, Mathf.Clamp01(Time.deltaTime * 12)); var dir = new Vector2(bladeWay.x, bladeWay.z).normalized; if (dir == Vector2.zero) dir = (b - a).normalized;
            strokeRun += (b - a).magnitude;
            bed.Sweep(a, b, pile.channelWidth > 0 ? BladeHalf : BladeHalf * 1.5f, mud.biteM); bed.Slide(b, .24f, 4);
            load = bed.Bow(b) / Capacity(pile, bed); lastStroke = Time.time;
            if (load > .35f) shake = Mathf.Max(shake, .0022f * Mathf.Min(1, load));   // the shaft trembles under a full blade
            var root = pileRoots[pile.id];
            foreach (Transform c in root)
            {
                if (!c.name.StartsWith("Stone_") || clinked.Contains(c) || Vector3.Distance(Flat(c.position), to) > .1f || bed.DepthAt(c.position) > stoneHeight[c]) continue;
                clinked.Add(c); Play(tickClip, "tick", .35f); shake = Mathf.Max(shake, .012f); bladeSpeed *= .35f;   // iron on old stone: it catches
            }
            // a weak spot lets go as the blade goes through it
            var rel = new double[] { to.x - root.position.x, to.z - root.position.z };
            if (Sim.SpotAt(pile.id, rel) != null) ReportMud(pile.id, rel, 0, to, way);
        }

        void EndStroke()
        {
            var id = grabbedPile.id; var pile = Sim.Pile(id); var bed = beds[id]; stroking = false;
            if (!bladeIn) return;
            bladeIn = false; var at = new Vector2(bladeAt.x, bladeAt.z); float carried = bed.Bow(at), smallest = Mathf.Max(SmallestHeave, bed.StartVolume / pile.mass * .4f);
            if (Sim.Left(id) > 0 && (carried >= smallest || strokeRun >= FullStroke))
            {
                float gone = carried >= smallest ? bed.Heave(at) : 0, least = strokeRun >= FullStroke ? bed.StartVolume / pile.mass * .35f : 0; bladeLift = 1;
                if (gone < least) { bed.Thin(least - gone); gone = least; }
                ReportMud(id, null, gone, bladeAt, bladeWay);
            }
            bed.Settle(at);   // wet mud does not keep the edges of a cut: what stands proud sags back in
            load = 0;
            if (pile.channelWidth > 0) { var zone = bedZone[id]; var deepest = bed.Deepest(zone); digPanTo = Flat(deepest) - new Vector3(zone.center.x, 0, zone.center.y); float room = Mathf.Max(0, Mathf.Max(zone.width, zone.height) - 1.1f) / 2; digPanTo = Vector3.ClampMagnitude(digPanTo, 9); digPanTo = new Vector3(Mathf.Abs(pile.stand[0]) > Mathf.Abs(pile.stand[1]) ? Mathf.Clamp(digPanTo.x, -room, room) : 0, 0, Mathf.Abs(pile.stand[1]) > Mathf.Abs(pile.stand[0]) ? Mathf.Clamp(digPanTo.z, -room, room) : 0); }
        }

        /// The bed says how much has left, and the rules hear it. Past nine tenths the last skin is not worth chasing round the floor.
        void ReportMud(string id, double[] at, float gone, Vector3 from, Vector3 way)
        {
            var pile = Sim.Pile(id); var bed = beds[id]; double total = Sim.PileMass(pile.mass); var hit = Sim.SpotAt(id, at);
            bool beat = gone > 0 && chantOn && Sim.IsOnBeat(ChantClock);
            double mass = bed.Progress >= FinishedAt ? Sim.Left(id) : Math.Max(0, Sim.Left(id) - (1 - bed.Progress / FinishedAt) * total);
            var r = Sim.Scrape(id, Math.Round(mass, 3), at, beat); LastStep = r; LastCode = r.code;
            if (!r.ok && hit == null && gone <= 0) return;
            if (r.code == "SLUMPED")
            {
                Say(r.message, r.code);
                var spotView = spots.First(v => v.pile == id && v.spot == hit); if (spotView.crack != null) { Destroy(spotView.crack); spotView.crack = null; }
                float share = hit.slump * Sim.s.partySize / (float)total * bed.StartVolume;
                bed.Thin(share - bed.Remove(new Vector2(spotView.world.x, spotView.world.z), .36f * pile.scale, share));
                StartCoroutine(Heaved(pile, spotView.world, from - spotView.world + spotView.outward, share, 1, false)); if (hit.reveal == "stone") RevealStone(spotView, false);
                Play(slumpClip, "slump", 1); shake = .06f; Buzz();
                if (bed.Progress >= FinishedAt && Sim.Left(id) > 0) Sim.Scrape(id, Sim.Left(id));
            }
            if (gone > 0)
            {
                float full = Mathf.Clamp01(gone / Capacity(pile, bed));
                StartCoroutine(Heaved(pile, from, way, gone, full, beat));
                var take = $"dig_{pile.kind}{digTake++ % 3}"; Play(digClips[take], take, .45f + full * .4f + (beat ? .15f : 0)); shake = Mathf.Max(shake, (beat ? .02f : .008f) + .012f * full);
                if (beat) { lampHitUntil = Time.time + .4f; lampText.text = "合拍"; }
            }
            lastStroke = Time.time; UpdatePile(id);
            if (Sim.Left(id) <= 0) PileCleared(id);
            RefreshStatus(); SaveNow();
        }

        /// A heave: heavy lumps go up off the blade, come down past the wall or out to the side, and add to the heap there.
        IEnumerator Heaved(CreekPile pile, Vector3 from, Vector3 way, float volume, float full, bool beat)
        {
            int count = 6 + Mathf.RoundToInt(full * 9) + (beat ? 3 : 0); var spoil = spoils[pile.id]; float each = volume / count, apex = pile.channelWidth > 0 ? .55f : .3f + .15f * full;
            var bits = new List<Transform>(); var start = new List<Vector3>(); var end = new List<Vector3>(); var delay = new List<float>(); var spin = new List<Vector3>();
            for (int i = 0; i < count; i++)
            {
                var bit = Clod("MudBit", (i < count / 3 ? UnityEngine.Random.Range(.05f, .08f) : UnityEngine.Random.Range(.018f, .04f)) * (.7f + .5f * full)); bit.gameObject.SetActive(false); bits.Add(bit);
                start.Add(from + Vector3.up * (SurfaceY(pileRoots[pile.id], from) + .06f) + UnityEngine.Random.insideUnitSphere * .05f);
                var land = SpoilSpot(pile, from, way); land.y = spoil.SurfaceAt(land); end.Add(land);
                delay.Add(.05f + UnityEngine.Random.Range(0, .1f)); spin.Add(UnityEngine.Random.onUnitSphere * UnityEngine.Random.Range(90f, 260f));
            }
            const float Flight = .46f; float t = 0; var landed = new bool[count];
            while (t < Flight + .2f)
            {
                t += Time.deltaTime;
                for (int i = 0; i < count; i++)
                {
                    float k = Mathf.Clamp01((t - delay[i]) / Flight); if (k <= 0 || landed[i]) continue;
                    bits[i].gameObject.SetActive(true); var p = Vector3.Lerp(start[i], end[i], k); p.y = Mathf.Lerp(start[i].y, end[i].y, k * k) + Mathf.Sin(Mathf.Min(k * 1.2f, 1) * Mathf.PI) * apex;
                    bits[i].position = p; bits[i].Rotate(spin[i] * Time.deltaTime, Space.World);
                    if (k >= 1) { landed[i] = true; spoil.Land(end[i], each, UnityEngine.Random.Range(.13f, .2f)); Destroy(bits[i].gameObject); }   // it is part of the heap now
                }
                yield return null;
            }
            foreach (var b in bits) if (b != null) Destroy(b.gameObject);
        }

        /// No thumb: the keyboard's stroke goes through the deepest mud left, towards the near wall or outward, and lets go when full.
        IEnumerator KeyStroke(string id)
        {
            var pile = Sim.Pile(id); var bed = beds[id]; var zone = bedZone[id]; var from = bed.Deepest(zone); var mid = new Vector3(zone.center.x, from.y, zone.center.y);
            var back = new Vector3(pile.stand[0], 0, pile.stand[1]).normalized; var to = pile.channelWidth > 0 ? from + back * .5f * (Vector3.Dot(from - mid, back) > 0 ? -1 : 1) : from + (Flat(from - mid).sqrMagnitude > .001f ? Flat(from - mid).normalized : back) * .55f;
            grabbedPile = digging; pressWorld = from; digTarget = from; stroking = true; bladeIn = false; bladeSpeed = 0; load = 0;
            float t = 0; while (!bladeIn && t < .6f) { t += Time.deltaTime; yield return null; }
            digTarget = to; t = 0;
            while (t < 2.4f && load < .9f && Vector3.Distance(Flat(bladeAt), Flat(to)) > .02f) { t += Time.deltaTime; yield return null; }
            EndStroke(); grabbedPile = null;
        }

        Job NearestWork(Vector2 at)
        {
            Job best = null; float bestD = 150 * Screen.height / 1080f;
            foreach (var j in jobs.Where(j => j.kind != "pile"))
            {
                float d = (at - (Vector2)view.WorldToScreenPoint(j.at + Vector3.up * .3f)).magnitude;
                if (d < bestD) { bestD = d; best = j; }
            }
            return best;
        }

        public void DoScoop(string id, float dragM, float seconds, double[] at = null, double[] dir = null)
        {
            var pile = Sim.Pile(id); float before = (float)(Sim.Left(id) / Sim.PileMass(pile.mass));
            var hit = Sim.SpotAt(id, at); var r = Sim.Scoop(id, dragM, seconds, at, dir, chantOn && Sim.IsOnBeat(ChantClock));
            Landed(id, pile, before, hit, r, dir, null);
        }

        void Landed(string id, CreekPile pile, float before, CreekSpot hit, CreekStep r, double[] dir, double[] wentIn)
        {
            LastStep = r;
            if (r.code == "TOO_SHORT" || r.code == "HURRIED" || r.code == "TANGLED" || r.code == "SLUMPED") Say(r.message, r.code); else LastCode = r.code;
            if (!r.ok) return;
            var from = digging != null ? bladeAt : pileRoots[id].position; var end = from + (dir != null ? new Vector3((float)dir[0], 0, (float)dir[1]).normalized : digRight);
            bladeLift = 1;
            if (r.onBeat) { lampHitUntil = Time.time + .4f; lampText.text = "合拍"; }
            if (r.code == "SLUMPED")
            {
                var view = spots.First(v => v.pile == id && v.spot == hit);
                if (view.crack != null) { Destroy(view.crack); view.crack = null; }
                CarveAt(id, view.world, .3f * pile.scale, .13f);
                StartCoroutine(SlumpDown(pile, view)); StartCoroutine(Sink(id, before, .5f));
                Play(slumpClip, "slump", 1); lastStroke = Time.time; shake = .1f; Buzz();
            }
            else
            {
                float force = Mathf.Clamp01((float)r.moved);
                float bite = (.2f + .08f * force) * Mathf.Sqrt(pile.scale);
                // a thrown spadeful leaves a groove from where the blade went in, the way it was hauled; a pulled weed from where the drag ended, back
                var along = dir != null ? new Vector3((float)dir[0], 0, (float)dir[1]).normalized : Vector3.zero; var cut = wentIn != null ? pileRoots[id].position + new Vector3((float)wentIn[0], 0, (float)wentIn[1]) : from;
                Vector3? leaves = null; if (wentIn != null) { end = cut + along; from = cut; }
                CarveAt(id, cut, bite, .05f + .07f * force + (r.onBeat ? .02f : 0));
                if (dir != null) CarveAt(id, cut + along * bite * (wentIn != null ? .7f : -.7f), bite * .8f, .035f + .04f * force);
                float haul = wentIn != null ? Mathf.Min(.7f, new Vector2((float)dir[0], (float)dir[1]).magnitude) * .5f : 0; int clods = 7 + Mathf.RoundToInt(force * 8) + (r.onBeat ? 5 : 0);
                StartCoroutine(MudFlies(from, end, clods, .42f + force * .4f + haul + (r.onBeat ? .22f : 0), pile, false, leaves));
                if (r.code == "SPILLED") StartCoroutine(MudFlies(from, end, clods, .16f, pile, true, leaves));   // the other half just falls off the blade
                StartCoroutine(Sink(id, before, .22f));
                var take = $"dig_{pile.kind}{digTake++ % 3}"; Play(digClips[take], take, .5f + force * .35f + (r.onBeat ? .15f : 0)); lastStroke = Time.time; shake = r.onBeat ? .028f : .012f + .008f * force;
            }
            if (Sim.Left(id) <= 0) PileCleared(id);
            RefreshStatus(); SaveNow();
        }

        void PileCleared(string id)
        {
            var job = jobs.FirstOrDefault(j => j.kind == "pile" && j.id == id); if (job != null) Finish(job);
            if (debris.TryGetValue(id, out var slabs)) { foreach (var slab in slabs) StartCoroutine(SinkAway(slab)); debris.Remove(id); }
            Play(tickClip, "tick", .6f); if (DiggingPile(id)) leaveAt = Time.time + 1.2f;
            if (Sim.SiltLeft <= 0) { StopChant(); Say("淤泥清完了，舊石頭都露出來了", "SILT_DONE"); }
            else Say("這堆清完了，舊石頭露出來", "PILE_DONE");
        }

        Mesh clodMesh; Material clodMat;
        float digDip; public Vector3 LastThrow { get; private set; }
        Job digging, pressedPile; float pressedPileD; Vector3 lastEye; Quaternion lastLook; Button leaveButton; float digBlend, leaveAt = -1, bladeLift, groundY = .2f; Vector3 digEye, digRight, digRest, digTarget, bladeAt; Quaternion digLook;
        public bool Digging => digging != null; public bool DiggingPile(string id) => digging != null && digging.id == id; public bool FirstPersonNow => digging != null && digBlend >= 1; public Button LeaveButton => leaveButton;
        public float PileSurface(string id, Vector3 at) => SurfaceY(pileRoots[id], at);
        public Vector2 PileStand(string id) { var p = Sim.Pile(id); return new Vector2(p.stand[0], p.stand[1]).normalized; }
        readonly Dictionary<Transform, float[]> heights = new Dictionary<Transform, float[]>();

        /// A rounded ball with soft bumps, its UVs wrapped round so the mud texture shows.
        static Mesh Ball(string name, int across, int up, float big, float small, float grain)
        {
            var rand = new System.Random(31); var ring = new List<Vector3>(); var uv = new List<Vector2>(); var t = new List<int>();
            for (int j = 0; j <= up; j++) for (int i = 0; i <= across; i++)
            {
                float a = (i % across) * Mathf.PI * 2 / across, b = j * Mathf.PI / up;
                ring.Add(new Vector3(Mathf.Cos(a) * Mathf.Sin(b), Mathf.Cos(b) * .8f, Mathf.Sin(a) * Mathf.Sin(b)) * (.54f + big * Mathf.Sin(3 * a + 1) * Mathf.Sin(2 * b) + small * Mathf.Sin(5 * a + b * 3) * Mathf.Sin(b) + (float)rand.NextDouble() * grain * Mathf.Sin(b)));
                uv.Add(new Vector2((float)i / across * .6f, (float)j / up * .3f));
            }
            for (int j = 0; j < up; j++) for (int i = 0; i < across; i++)
            {
                int a = j * (across + 1) + i, d = a + across + 1;
                t.AddRange(new[] { a, a + 1, d + 1, a, d + 1, d });   // shared corners: soft wet lumps, seen from close
            }
            var mesh = new Mesh { name = name }; mesh.SetVertices(ring); mesh.SetUVs(0, uv); mesh.SetTriangles(t, 0); mesh.RecalculateNormals(); mesh.RecalculateTangents(); mesh.RecalculateBounds();
            // the first and last column are one line round the back: same normal, or a crease shows
            var n = mesh.normals; for (int j = 0; j <= up; j++) { int a = j * (across + 1), z = a + across; n[a] = n[z] = (n[a] + n[z]).normalized; }
            mesh.normals = n; return mesh;
        }

        /// A rough soft lump, shared by every flying bit of mud.
        Transform Clod(string name, float size)
        {
            if (clodMesh == null)
            {
                clodMesh = Ball("Clod", 12, 8, .13f, .09f, .05f);
                clodMat = new Material(soilMat); clodMat.SetColor("_BaseColor", new Color(.13f, .1f, .073f)); clodMat.SetFloat("_Smoothness", .32f);
            }
            var go = new GameObject(name, typeof(MeshFilter), typeof(MeshRenderer)); go.GetComponent<MeshFilter>().sharedMesh = clodMesh; go.GetComponent<MeshRenderer>().sharedMaterial = clodMat;
            go.transform.localScale = new Vector3(size * UnityEngine.Random.Range(.9f, 1.5f), size * UnityEngine.Random.Range(.55f, 1f), size * UnityEngine.Random.Range(.9f, 1.3f)); go.transform.rotation = UnityEngine.Random.rotation;
            return go.transform;
        }

        /// Heavy wet lumps: they leave the blade late, fall hard, flatten where they land and stay a while.
        IEnumerator MudFlies(Vector3 from, Vector3 to, int count, float reach, CreekPile pile, bool falls = false, Vector3? leaves = null)
        {
            var root = pileRoots[pile.id]; bool inChannel = pile.channelWidth > 0; const float floor = .012f; float apex = .16f * (.6f + reach);
            var along = Flat(to - from); along = along.sqrMagnitude > .01f ? along.normalized : Vector3.right;
            var aside = Vector3.Cross(Vector3.up, along); float spread = .22f;
            // inside the channel it goes up over a wall and onto the ground beyond, the way a spade really clears a ditch
            if (inChannel && !falls) { var axis = new Vector3(pile.stand[0], 0, pile.stand[1]).normalized; along = Vector3.Cross(Vector3.up, axis); if (Vector3.Dot(along, to - from) < 0) along = -along; aside = axis; spread = .26f; reach = pile.channelWidth + reach * .55f; apex = .62f; }
            if (falls) { apex = .04f; spread = .1f; } else LastThrow = along;
            var bits = new List<Transform>(); var start = new List<Vector3>(); var end = new List<Vector3>(); var delay = new List<float>(); var spin = new List<Vector3>(); var size = new List<Vector3>();
            for (int i = 0; i < count; i++)
            {
                var bit = Clod("MudBit", i < count / 4 ? UnityEngine.Random.Range(.035f, .055f) : UnityEngine.Random.Range(.014f, .032f)); bits.Add(bit); size.Add(bit.localScale); bit.gameObject.SetActive(false);
                start.Add((leaves ?? from) + UnityEngine.Random.insideUnitSphere * .05f);
                var land = from + along * reach * UnityEngine.Random.Range(.45f, 1.1f) + aside * UnityEngine.Random.Range(-spread, spread); land.y = Mathf.Max(floor, SurfaceY(root, land)); end.Add(land);
                delay.Add(UnityEngine.Random.Range(0, .09f)); spin.Add(UnityEngine.Random.onUnitSphere * UnityEngine.Random.Range(90f, 260f));
            }
            const float Flight = .48f; float t = 0;
            while (t < Flight + .1f)
            {
                t += Time.deltaTime;
                for (int i = 0; i < bits.Count; i++)
                {
                    float k = Mathf.Clamp01((t - delay[i]) / Flight); if (k <= 0) continue;
                    bits[i].gameObject.SetActive(true);
                    var p = Vector3.Lerp(start[i], end[i], k); p.y = Mathf.Lerp(start[i].y, end[i].y, k * k) + Mathf.Sin(Mathf.Min(k * 1.25f, 1) * Mathf.PI) * apex;
                    bits[i].position = p;
                    if (k < 1) bits[i].Rotate(spin[i] * Time.deltaTime, Space.World); else { bits[i].rotation = Quaternion.Euler((i * 29) % 40 - 20, i * 47, (i * 17) % 30 - 15); bits[i].localScale = new Vector3(size[i].x * 1.1f, size[i].y * .78f, size[i].z * 1.1f); }
                }
                yield return null;
            }
            yield return new WaitForSeconds(5f);
            t = 0; var lying = bits.Select(b => b.localScale).ToArray();
            while (t < .6f) { t += Time.deltaTime; for (int i = 0; i < bits.Count; i++) if (bits[i] != null) bits[i].localScale = lying[i] * Mathf.Clamp01(1 - t / .6f); yield return null; }
            foreach (var b in bits) if (b != null) Destroy(b.gameObject);
        }

        /// A low slab of the same mud model.
        GameObject Slab(CreekPile pile, SpotView view)
        {
            var slab = Instantiate(pileStages[2], dyn); slab.name = "Slump_" + view.pile + "_" + view.spot.id;
            foreach (var f in slab.GetComponentsInChildren<MeshFilter>(true))
            {
                if (!slackMeshes.TryGetValue(f.sharedMesh, out var slack)) { slack = Instantiate(f.sharedMesh); Slacken(slack, 6); slackMeshes[f.sharedMesh] = slack; }
                f.sharedMesh = slack;
            }
            if (pile.kind == "hard") Crust(slab);
            if (!debris.TryGetValue(view.pile, out var list)) debris[view.pile] = list = new List<GameObject>();
            list.Add(slab); return slab;
        }

        /// The slope above the crack lets go: it slides out past the spot and stays there as a low spill.
        IEnumerator SlumpDown(CreekPile pile, SpotView view)
        {
            var slab = Slab(pile, view); var root = pileRoots[view.pile].position;
            Vector3 start = view.world - view.outward * .22f + Vector3.up * .16f, end = view.world + view.outward * .3f;
            Vector3 big = Vector3.Scale(new Vector3(.5f * pile.scale, .5f, .5f * pile.scale), PileFit(pile)), flat = Vector3.Scale(new Vector3(.42f * pile.scale, .14f, .42f * pile.scale), PileFit(pile));
            StartCoroutine(MudFlies(view.world, view.world + view.outward, 16, 1.1f, pile));
            if (view.spot.reveal == "stone") RevealStone(view, false);
            float t = 0;
            while (t < .6f && slab != null)
            {
                t += Time.deltaTime; float k = Mathf.Clamp01(t / .6f), ease = k * k * (3 - 2 * k);
                slab.transform.position = Vector3.Lerp(start, end, ease); slab.transform.localScale = Vector3.Lerp(big, flat, ease);
                yield return null;
            }
        }

        IEnumerator SinkAway(GameObject go)
        {
            float t = 0; var from = go.transform.localScale;
            while (t < .4f && go != null) { t += Time.deltaTime; go.transform.localScale = Vector3.Lerp(from, new Vector3(from.x, 0, from.z), t / .4f); yield return null; }
            if (go != null) Destroy(go);
        }

        /// The old stone that was jammed in the mud rolls out with the slump and stays.
        void RevealStone(SpotView view, bool now)
        {
            var stone = Instantiate(oldStones, dyn); stone.name = "Freed_Stone_" + view.pile; var home = view.world + view.outward * .5f;
            stone.transform.position = home; stone.transform.localScale = Vector3.one * .34f;
            if (!now) StartCoroutine(RollOut(stone.transform, view.world, home));
        }

        IEnumerator RollOut(Transform stone, Vector3 from, Vector3 to)
        {
            float t = 0; var turn = Vector3.Cross(Vector3.up, Flat(to - from)).normalized;
            while (t < .7f && stone != null)
            {
                t += Time.deltaTime; float k = Mathf.Clamp01(t / .7f);
                stone.position = Vector3.Lerp(from, to, 1 - (1 - k) * (1 - k)) + Vector3.up * Mathf.Sin(k * Mathf.PI) * .1f;
                stone.Rotate(turn, Time.deltaTime * 420 * (1 - k), Space.World); yield return null;
            }
        }

        // ---- the chant and the look of a crack -----------------------------------------------------------------------
        void BuildSound()
        {
            if (FindAnyObjectByType<AudioListener>() == null) view.gameObject.AddComponent<AudioListener>();
            chantSource = gameObject.AddComponent<AudioSource>(); chantSource.loop = true; chantSource.playOnAwake = false; chantSource.spatialBlend = 0;
            farChantClip = CreekRepairSound.Clip("FarChant", CreekRepairSound.Chant(content.chant.cycleSeconds, content.chant.yoAtSeconds, 1));
            fxSource = gameObject.AddComponent<AudioSource>(); fxSource.playOnAwake = false; fxSource.spatialBlend = 0;
            pressSource = gameObject.AddComponent<AudioSource>(); pressSource.playOnAwake = false; pressSource.spatialBlend = 0; pressSource.clip = CreekRepairSound.Clip("Press", CreekRepairSound.Press());
            foreach (var kind in new[] { "soft", "hard", "weed" }) for (int t = 0; t < 3; t++) digClips[$"dig_{kind}{t}"] = CreekRepairSound.Clip($"Dig_{kind}{t}", CreekRepairSound.Dig(kind, t));
            thudClip = CreekRepairSound.Clip("Thud", CreekRepairSound.Thud()); slumpClip = CreekRepairSound.Clip("Slump", CreekRepairSound.Slump()); tickClip = CreekRepairSound.Clip("Tick", CreekRepairSound.Tick());
        }

        AudioSource waterSource, pressSource; float waterGain; bool pressHeard; int digTake;
        readonly Dictionary<string, AudioClip> digClips = new Dictionary<string, AudioClip>();

        /// Runs from the first water until the end, quieter once the fields are full.
        void WaterSound(float gain)
        {
            if (waterSource == null)
            {
                waterSource = gameObject.AddComponent<AudioSource>(); waterSource.loop = true; waterSource.spatialBlend = 0; waterSource.clip = CreekRepairSound.Clip("Water", CreekRepairSound.Water()); waterSource.Play();
            }
            if (gain == waterGain) return;
            waterGain = gain; waterSource.volume = gain * .55f; Sounds.Add(new SoundMark { name = "water", at = Time.realtimeSinceStartup, gain = waterSource.volume });
        }

        void Play(AudioClip clip, string name, float gain) { fxSource.PlayOneShot(clip, gain); Sounds.Add(new SoundMark { name = name, at = Time.realtimeSinceStartup, gain = gain }); }

        void Buzz()
        {
#if UNITY_ANDROID || UNITY_IOS
            Handheld.Vibrate();
#endif
        }

        void StartChant()
        {
            if (Sim.SiltLeft <= 0) { chantSource.Stop(); chantOn = false; lamp.gameObject.SetActive(false); return; }
            if (chantVoices != Sim.s.partySize) { chantVoices = Sim.s.partySize; chantSource.clip = CreekRepairSound.Clip("Chant", CreekRepairSound.Chant(content.chant.cycleSeconds, content.chant.yoAtSeconds, chantVoices)); }
            chantStart = Time.realtimeSinceStartup; chantSource.time = 0; chantSource.volume = 0; chantSource.Play(); chantOn = true;
        }

        void StopChant() { chantOn = false; }

        const float ChantLinger = 3.5f; float lastStroke = -100; bool chantHeard;

        void UpdateChant()
        {
            bool heard = chantOn && digging != null && Time.time - lastStroke < ChantLinger;
            if (heard != chantHeard)
            {
                chantHeard = heard; float cycleNow = content.chant.cycleSeconds;
                Sounds.Add(new SoundMark { name = heard ? "chant_on" : "chant_off", at = Time.realtimeSinceStartup + (heard ? cycleNow - ChantClock % cycleNow : 0), gain = 1 });
            }
            float want = heard ? .5f : 0;
            chantSource.volume = Mathf.MoveTowards(chantSource.volume, want, Time.deltaTime * (chantOn ? 1.5f : .8f));
            if (!chantOn && chantSource.isPlaying && chantSource.volume <= 0) chantSource.Stop();
            // the blade dragging through mud: louder the more it carries, silent when it stops
            bool grinding = stroking && bladeIn;
            if (grinding != pressHeard)
            {
                pressHeard = grinding; Sounds.Add(new SoundMark { name = grinding ? "press_on" : "press_off", at = Time.realtimeSinceStartup, gain = .55f });
                if (grinding) { pressSource.loop = true; pressSource.Play(); } else pressSource.Stop();
            }
            if (grinding) pressSource.volume = Mathf.Lerp(pressSource.volume, Mathf.Min(1, lastBladeSpeed * 2.2f) * (.3f + .5f * Mathf.Min(1, load)), Mathf.Clamp01(Time.deltaTime * 14));
            lamp.gameObject.SetActive(chantOn && !CardsOpen);
            if (!chantOn) return;
            float cycle = content.chant.cycleSeconds, phase = ChantClock % cycle, toYo = Mathf.Abs(phase - content.chant.yoAtSeconds);
            bool yo = toYo <= content.chant.windowSeconds, hei = phase < .3f || phase > cycle - .1f;
            if (Time.time >= lampHitUntil) lampText.text = yo ? "咻" : hei ? "嘿" : "";
            float glow = Time.time < lampHitUntil ? 1 : yo ? .7f : hei ? .3f : 0;
            lamp.color = Color.Lerp(new Color(.08f, .07f, .05f, 0), new Color(.35f, .72f, .58f, .92f), glow);
            float size = 1 + glow * .14f; lamp.transform.localScale = new Vector3(size, size, 1);
        }

        void UpdateCracks()
        {
            float beat = Mathf.Pow(.5f + .5f * Mathf.Cos(ChantClock * Mathf.PI * 2 / content.chant.cycleSeconds), 3);
            foreach (var view in spots)
            {
                if (view.crack == null || !view.crack.activeSelf) continue;
                view.mat.SetColor("_BaseColor", Color.Lerp(new Color(.055f, .036f, .02f), new Color(.17f, .115f, .065f), beat));
                if (Time.time >= view.nextCrumble) { view.nextCrumble = Time.time + 2.1f + (float)(view.world.x % .4f); StartCoroutine(Crumble(view)); }
            }
        }

        /// A little mud keeps trickling out of a crack: the sign the slope is ready to come down.
        IEnumerator Crumble(SpotView view)
        {
            var bits = new List<Transform>(); var root = pileRoots.TryGetValue(view.pile, out var r) ? r : null; if (root == null) yield break;
            float top = SurfaceY(root, view.world);
            for (int i = 0; i < 3; i++) bits.Add(Clod("Crumble", UnityEngine.Random.Range(.03f, .055f)));
            var offs = bits.Select(_ => Vector3.Scale(UnityEngine.Random.insideUnitSphere, new Vector3(.12f, 0, .12f))).ToArray(); float t = 0;
            while (t < .7f)
            {
                t += Time.deltaTime; float k = Mathf.Clamp01(t / .7f);
                for (int i = 0; i < bits.Count; i++) bits[i].position = view.world + offs[i] + view.outward * (.03f + k * .2f) + Vector3.up * (Mathf.Lerp(top + .03f, .02f, k * k));
                yield return null;
            }
            foreach (var b in bits) Destroy(b.gameObject);
        }

        void ShowSpade(Vector3 at)
        {
            if (spade == null)
            {
                if (spadeModel != null) { spade = Instantiate(spadeModel).transform; spade.localScale *= .78f; BendBlade(LengthenShaft(spade)); foreach (var r in spade.GetComponentsInChildren<Renderer>()) foreach (var m in r.materials) { if (m.HasProperty("_Smoothness")) m.SetFloat("_Smoothness", .2f); if (m.HasProperty("_Bounce")) m.SetFloat("_Bounce", .12f); } }
                else
                {
                    spade = new GameObject("Placeholder_Spade").transform;
                    var blade = GameObject.CreatePrimitive(PrimitiveType.Cube); Destroy(blade.GetComponent<Collider>()); blade.transform.SetParent(spade, false); blade.transform.localScale = new Vector3(.22f, .02f, .3f); blade.GetComponent<Renderer>().sharedMaterial = stoneMat;
                    var shaft = GameObject.CreatePrimitive(PrimitiveType.Cube); Destroy(shaft.GetComponent<Collider>()); shaft.transform.SetParent(spade, false); shaft.transform.localPosition = new Vector3(0, .4f, -.35f); shaft.transform.localRotation = Quaternion.Euler(-40, 0, 0); shaft.transform.localScale = new Vector3(.035f, 1.1f, .035f);
                }
            }
            spade.gameObject.SetActive(true); spade.position = Flat(at);
        }

        /// The camera stands back from the mud, further than the spade is long: the plain middle of the shaft is drawn out, so the grip stays below the frame.
        static float LengthenShaft(Transform spade)
        {
            float top = 0; var meshes = spade.GetComponentsInChildren<MeshFilter>(true);
            foreach (var f in meshes) { if (!f.sharedMesh.isReadable) { Debug.LogWarning("CREEK spade mesh not readable: " + f.name); return 0; } foreach (var p in f.sharedMesh.vertices) top = Mathf.Max(top, spade.InverseTransformPoint(f.transform.TransformPoint(p)).y); }
            float from = top * .3f, to = top * .52f, extra = top * 1.2f;
            foreach (var f in meshes)
            {
                var own = Instantiate(f.sharedMesh); var v = own.vertices;
                for (int i = 0; i < v.Length; i++)
                {
                    var p = spade.InverseTransformPoint(f.transform.TransformPoint(v[i]));
                    if (p.y > from) p.y += extra * Mathf.Clamp01((p.y - from) / (to - from));
                    v[i] = f.transform.InverseTransformPoint(spade.TransformPoint(p));
                }
                own.vertices = v; own.RecalculateBounds(); f.sharedMesh = own;
            }
            return from;
        }

        /// A spade's blade sits at an angle to its shaft. The set models it in line, and from up here an in-line blade is seen end on, as a stick.
        void BendBlade(float shaftFrom)
        {
            var meshes = spade.GetComponentsInChildren<MeshFilter>(true); float heel = 0;
            foreach (var f in meshes) foreach (var v in f.sharedMesh.vertices) { var p = spade.InverseTransformPoint(f.transform.TransformPoint(v)); if (p.y < shaftFrom && Mathf.Abs(p.x) > .06f) heel = Mathf.Max(heel, p.y); }
            if (heel <= 0) return;
            float a = BladeBend * Mathf.Deg2Rad; var bend = Quaternion.AngleAxis(-BladeBend, Vector3.right);
            foreach (var f in meshes)
            {
                var own = f.sharedMesh; var v = own.vertices; var n = own.normals;
                for (int i = 0; i < v.Length; i++)
                {
                    var p = spade.InverseTransformPoint(f.transform.TransformPoint(v[i]));
                    if (p.y >= heel) continue;
                    v[i] = f.transform.InverseTransformPoint(spade.TransformPoint(new Vector3(0, heel, 0) + bend * (p - new Vector3(0, heel, 0))));
                    if (i < n.Length) n[i] = f.transform.InverseTransformDirection(spade.TransformDirection(bend * spade.InverseTransformDirection(f.transform.TransformDirection(n[i]))));
                }
                own.vertices = v; own.normals = n; own.RecalculateBounds();
            }
            bentTip = new Vector3(0, heel * (1 - Mathf.Cos(a)), heel * Mathf.Sin(a)); bladeReach = heel * Mathf.Cos(a);
        }

        void HideSpade() { if (spade != null) spade.gameObject.SetActive(false); if (dragLine != null) dragLine.enabled = false; }

        void HandleKeys()
        {
            var k = Keyboard.current; if (k == null) return;
            Vector3 pan = Vector3.zero;
            if (k.aKey.isPressed || k.leftArrowKey.isPressed) pan.x -= 1; if (k.dKey.isPressed || k.rightArrowKey.isPressed) pan.x += 1;
            if (k.wKey.isPressed || k.upArrowKey.isPressed) pan.z += 1; if (k.sKey.isPressed || k.downArrowKey.isPressed) pan.z -= 1;
            if (digging == null) panOffset += pan * Time.deltaTime * 4;
            if (CardsOpen)
            {
                if (k.digit1Key.wasPressedThisFrame && cardButtons.Count > 0) cardButtons[0].onClick.Invoke();
                if (k.digit2Key.wasPressedThisFrame && cardButtons.Count > 1) cardButtons[1].onClick.Invoke();
                if (k.digit3Key.wasPressedThisFrame && cardButtons.Count > 2) cardButtons[2].onClick.Invoke();
                if (k.escapeKey.wasPressedThisFrame) cards.SetActive(false);
                return;
            }
            if (digging != null && k.escapeKey.wasPressedThisFrame) { LeaveDig(); return; }
            if (planPanel.activeSelf) { if (k.escapeKey.wasPressedThisFrame || k.pKey.wasPressedThisFrame) ShowPlan(false); return; }
            if (Sim.WorkDone)
            {
                var keys = new[] { k.digit1Key, k.digit2Key, k.digit3Key };
                for (int i = 0; i < keys.Length; i++) if (keys[i].wasPressedThisFrame) PressGate(content.distribution.gates[i].id);
                if (k.pKey.wasPressedThisFrame) { ShowPlan(true); return; }
                if (k.gKey.wasPressedThisFrame) ToggleView();
                if (k.spaceKey.wasPressedThisFrame && !Sim.GateOpen && !viewWheel) ToggleView();
            }
            var open = jobs.Where(j => j.kind != "pile" || Sim.Left(j.id) > 0).ToList();
            if (digging == null && k.tabKey.wasPressedThisFrame && open.Count > 0)
            {
                tabIndex = (tabIndex + 1) % open.Count; focusTarget = open[tabIndex].at; panOffset = Vector3.zero; Say(open[tabIndex].name, "TAB");
            }
            if (open.Count == 0 && Sim.WorkDone && k.spaceKey.isPressed) TurnBy(180 * Time.deltaTime);
            else if (k.spaceKey.wasPressedThisFrame && open.Count > 0 && Time.time > keyCooldown)
            {
                keyCooldown = Time.time + .35f;
                var j = digging ?? open[Mathf.Clamp(tabIndex, 0, open.Count - 1)];
                if (j.kind == "pile" && digging == null) EnterDig(j);
                else if (j.kind == "pile")
                {
                    var pile = Sim.Pile(j.id);
                    if (pile.kind != "weed") { if (!stroking) StartCoroutine(KeyStroke(j.id)); return; }
                    // no thumb to aim with: a drag on the 喲 goes in at the pile's next crack
                    var next = chantOn && Sim.IsOnBeat(ChantClock) ? pile.spots.FirstOrDefault(o => !Sim.Spent(j.id, o)) : null;
                    bladeAt = pileRoots[j.id].position + (next != null ? new Vector3((float)next.pos[0], 0, (float)next.pos[1]) : Vector3.zero);
                    var at = next != null ? new double[] { next.pos[0], next.pos[1] } : null;
                    DoScoop(j.id, Sim.Mud(pile.kind).fullDragM, 1, at);
                }
                else OpenJob(j);
            }
        }

        void TurnBy(float degrees)
        {
            if (degrees <= 0) { if (degrees < -2) { var w = Sim.TurnWheel(degrees); if (!w.ok) Say(w.message, w.code); } return; }
            bool before = Sim.GateOpen;
            var r = Sim.TurnWheel(degrees);
            if (!r.ok) { Say(r.message, r.code); return; }
            spinVisual += degrees; for (int i = 0; i < wheelParts.Length; i++) wheelParts[i].localRotation = wheelHome[i] * Quaternion.AngleAxis(spinVisual, Vector3.right);
            float open = (float)(Sim.s.wheelDegrees / content.flow.wheelDegrees);
            for (int i = 0; i < gateParts.Length; i++) SetGate(i, open);
            if (Sim.GateOpen && !before) { viewWheel = false; Say(r.message, r.code); RefreshStatus(); SaveNow(); }
        }

        void SetGate(int i, float open) { var p = gateParts[i].localPosition; p.y = gateHome[i] + .3f * open; gateParts[i].localPosition = p; }

        // ---- join ---------------------------------------------------------------------------------------------------
        void OpenJob(Job job)
        {
            if (job.kind == "aqueduct") { var r = Sim.BuildAqueduct(); Say(r.message, r.code); if (r.ok) { foreach (var g in Sim.M.aqueduct.slots) StartCoroutine(Drop(Slot(g.slot), g.piece)); Finish(job); } return; }
            cardJob = job;
            foreach (Transform c in cards.transform) Destroy(c.gameObject);
            cardButtons.Clear();
            var options = job.kind == "slot"
                ? Sim.M.work.First(w => w.slot == job.id).options.Select(o => o.piece).ToArray()
                : new[] { Sim.M.patches.First(w => w.slot == job.id).piece, Sim.M.patches.First(w => w.slot == job.id).wrong };
            // not always the right one first
            int shift = Math.Abs(job.id.GetHashCode()) % options.Length;
            options = options.Skip(shift).Concat(options.Take(shift)).ToArray();
            float w0 = 420, gap = 26, x = -(options.Length - 1) * (w0 + gap) / 2;
            foreach (var piece in options)
            {
                var p = piece;
                var b = HarvestUi.Button("Card_" + piece, cards.transform, PieceName(piece), () => Choose(p), new Vector2(.5f, .5f), new Vector2(x, 0), new Vector2(w0, 120), AlchemyUi.Bamboo, 30);
                ((RectTransform)b.transform).pivot = new Vector2(.5f, .5f); ((RectTransform)b.transform).anchoredPosition = new Vector2(x, 0);
                cardButtons.Add(b); x += w0 + gap;
            }
            cards.SetActive(true);
        }

        public Button CardFor(string piece) => cardButtons.First(b => b.name == "Card_" + piece);
        public static string PieceName(string id) => PieceNames.TryGetValue(id, out var n) ? n : id;
        static readonly Dictionary<string, string> PieceNames = new Dictionary<string, string>
        {
            { "B02", "完整短直槽" }, { "B02-V03", "半截舊直槽" }, { "B02-V04", "半段短渠頭" }, { "B02-V05", "排水流嘴" }, { "B03", "中彎槽（右）" }, { "B03-V02", "寬彎槽（右）" },
            { "B03-V03", "急彎槽（左）" }, { "B03-V04", "中彎槽（左）" }, { "B05", "青銅滑動閘段" }, { "B07", "修補石鞍" }, { "B07-V02", "轉角修補石" },
        };

        void Choose(string piece)
        {
            var job = cardJob; cards.SetActive(false);
            var r = job.kind == "slot" ? Sim.Place(job.id, piece) : Sim.Patch(job.id, piece);
            Say(r.message, r.code);
            if (r.ok)
            {
                if (job.kind == "slot") StartCoroutine(Drop(Slot(job.id), piece)); else AddPatch(job.id, piece);
                Finish(job);
            }
            else if (job.kind == "slot") StartCoroutine(ShowGap(job, piece));
        }

        IEnumerator Drop(BoardSlot slot, string piece)
        {
            AddPiece(slot, piece);
            var go = dyn.Find($"{slot.id}_{piece}"); var home = go.position; float t = 0;
            if (water.TryGetValue(slot.id, out var list)) { foreach (var w in list) { w.full = w.t.localScale; w.full.y *= WaterLevel(Sim.M.waterWidthM); } UpdateWater(); }
            while (t < .4f) { t += Time.deltaTime; float k = Mathf.Clamp01(t / .4f); go.position = home + Vector3.up * (1 - k * k) * .9f; yield return null; }
            go.position = home; shake = .03f;
        }

        IEnumerator ShowGap(Job job, string piece)
        {
            var slot = Slot(job.id); var option = Sim.M.work.First(w => w.slot == job.id).options.First(o => o.piece == piece);
            if (ghostWrong != null) Destroy(ghostWrong);
            ghostWrong = Spawn(Model(piece).model, slot, "WrongPiece");
            foreach (var r in ghostWrong.GetComponentsInChildren<Renderer>()) r.sharedMaterials = Enumerable.Repeat(wrongMat, r.sharedMaterials.Length).ToArray();
            gapLine.enabled = true; gapLine.SetPosition(0, V(option.from, .36f)); gapLine.SetPosition(1, V(option.to, .36f));
            focusTarget = job.at; panOffset = Vector3.zero;
            var mine = ghostWrong; yield return new WaitForSeconds(3.2f);
            if (ghostWrong == mine) { Destroy(ghostWrong); gapLine.enabled = false; }
            RetargetCamera();
        }

        // ---- water ---------------------------------------------------------------------------------------------------
        static void TintSoil(Renderer r, Color c) { foreach (var m in r.materials) if (m.name.Contains("field_soil")) m.color = c; }

        /// Water objects showing right now; the playtest checks this is zero until the gate opens.
        public int WaterShowing => water.Values.SelectMany(l => l).Count(w => w.t.gameObject.activeInHierarchy) + fieldWater.Count(f => f.gameObject.activeInHierarchy);

        void UpdateWater()
        {
            double at = 0, flow = Sim.s.flowM;
            foreach (var n in Sim.M.route)
            {
                float k = Mathf.Clamp01((float)((flow - at) / n.lengthM)); at += n.lengthM;
                if (!water.TryGetValue(n.id, out var list)) continue;
                foreach (var w in list)
                {
                    if (w.kind == "ditch") Reveal(w, (k - w.from) / (w.to - w.from)); else Reveal(w, k);
                }
            }
            bool arrived = Sim.CanalFull;
            for (int i = 0; i < fieldGates.Length; i++)
            {
                var g = content.distribution.gates[i]; var st = Sim.Gate(g.id); var view = gateViews[i]; float k = (float)(st.fill / g.fieldM);
                // the board comes up slowly, and the water follows it through
                view.lift = Mathf.MoveTowards(view.lift, (float)st.level, Time.deltaTime * .6f);
                for (int p = 0; p < fieldGates[i].parts.Length; p++) { var local = fieldGates[i].parts[p].localPosition; local.y = view.home[p] + .3f * view.lift; fieldGates[i].parts[p].localPosition = local; }
                view.show = Mathf.MoveTowards(view.show, arrived && st.level > 0 ? 1 : 0, Time.deltaTime * .7f);
                if (view.span != null) { Reveal(view.span, arrived ? .45f + .55f * Mathf.Clamp01(view.show * 2) : 0); Reveal(view.after, (view.show - .5f) * 2); }
                var f = fieldWater[i]; f.gameObject.SetActive(k > 0); var s = f.localScale; s.y = Mathf.Lerp(BedLevel / (.28f * WaterLevel(Sim.M.waterWidthM)), 1, k) * fieldHome(i) * WaterLevel(Sim.M.waterWidthM); f.localScale = s;
                Spread(i, k);
                TintSoil(fieldSoil[i], Color.Lerp(new Color(.56f, .58f, .54f), new Color(.38f, .39f, .37f), k));
            }
            // old pieces off this method's route stay dry
            foreach (var pair in water) if (!Sim.M.route.Any(n => n.id == pair.Key)) foreach (var w in pair.Value) w.t.gameObject.SetActive(false);
            if (celebration != null) celebration.SetActive(Sim.s.done);
            if (aqueductTrestles != null) aqueductTrestles.SetActive(Sim.s.aqueduct);
            if (spareTrestle != null) spareTrestle.SetActive(!Sim.s.aqueduct);
            if (gullyCover != null) gullyCover.SetActive(!Sim.M.HasAqueduct);
            Shader.SetGlobalFloat("_CreekNursery", Sim.M.HasAqueduct ? 1 : 0);
            if (Sim.M.HasAqueduct && gullyCover != null && (gully == null || gully.go == null)) MakeGully();
        }

        readonly Dictionary<int, float> fieldScale = new Dictionary<int, float>();
        float fieldHome(int i) { if (!fieldScale.TryGetValue(i, out var s)) fieldScale[i] = s = fieldWater[i].localScale.y; return s; }

        /// Shows a water mesh as far as the front has come. It keeps its shape, so round a bend it stays between the banks.
        void Reveal(Water w, float k)
        {
            k = Mathf.Clamp01(k); w.t.gameObject.SetActive(k > 0); if (k <= 0) return;
            w.t.localScale = w.full;
            if (w.parts == null)
            {
                w.parts = w.t.GetComponentsInChildren<Renderer>(); w.entry = w.t.position;
                foreach (var r in w.parts) foreach (var cx in new[] { r.bounds.min.x, r.bounds.max.x }) foreach (var cz in new[] { r.bounds.min.z, r.bounds.max.z })
                    w.reach = Mathf.Max(w.reach, new Vector2(cx - w.entry.x, cz - w.entry.z).magnitude);
            }
            var block = new MaterialPropertyBlock(); block.SetVector("_Reveal", new Vector4(w.entry.x, 0, w.entry.z, k >= 1 ? 100000 : k * w.reach));
            foreach (var r in w.parts) r.SetPropertyBlock(block);
        }

        const float SpreadShare = .6f, SpreadReach = 6.5f, BedLevel = .105f;
        readonly Dictionary<int, Renderer[]> fieldParts = new Dictionary<int, Renderer[]>();

        /// A field wets from where the water comes in: first a front creeping along the furrows, then the level comes up behind it.
        void Spread(int field, float k)
        {
            if (!fieldParts.TryGetValue(field, out var parts)) fieldParts[field] = parts = fieldWater[field].GetComponentsInChildren<Renderer>();
            var entry = new Vector3(fieldGates[field].at.x, 0, 9);
            var block = new MaterialPropertyBlock(); block.SetVector("_Reveal", new Vector4(entry.x, 0, entry.z, k >= SpreadShare ? 100000 : k / SpreadShare * SpreadReach));
            foreach (var r in parts) r.SetPropertyBlock(block);
        }

        public Vector3 WaterHead => HeadPosition();

        Vector3 HeadPosition()
        {
            double at = 0; var r = Sim.M.route; double f = Sim.s.flowM;
            for (int i = 0; i < r.Length; i++)
            {
                if (f <= at + r[i].lengthM || i == r.Length - 1)
                {
                    var a = V(r[i].pos); var b = i + 1 < r.Length ? V(r[i + 1].pos) : a;
                    return Vector3.Lerp(a, b, Mathf.Clamp01((float)((f - at) / r[i].lengthM)));
                }
                at += r[i].lengthM;
            }
            return V(r[0].pos);
        }

        // ---- camera --------------------------------------------------------------------------------------------------
        void RetargetCamera()
        {
            if (Sim == null) return;
            if (Sim.GateOpen)
            {
                bool atCanal = Sim.s.reached.Contains("canal");
                focusTarget = atCanal ? GatesFocus : HeadPosition(); zoomTarget = atCanal ? GatesZoom : 1.15f;
                if (Sim.s.done) { focusTarget = new Vector3(0, 0, 10); zoomTarget = 2.5f; }
                return;
            }
            if (Sim.WorkDone) { focusTarget = viewWheel ? WheelRim : GatesFocus; zoomTarget = viewWheel ? .85f : GatesZoom; panOffset = Vector3.zero; return; }
            zoomTarget = 1.15f;
            var near = jobs.Where(j => j.kind != "pile" || Sim.Left(j.id) > 0).OrderBy(j => (Flat(j.at) - Flat(focusTarget)).sqrMagnitude).FirstOrDefault();
            if (near != null) focusTarget = near.at;
        }

        void PlaceCamera()
        {
            if (closeUp)
            {
                var wanted = Quaternion.LookRotation(closeUpAt - closeUpFrom, Vector3.up); float glide = closeUpGlide ? Mathf.Clamp01(Time.deltaTime * 1.3f) : 1;
                view.transform.SetPositionAndRotation(Vector3.Lerp(view.transform.position, closeUpFrom, glide), Quaternion.Slerp(view.transform.rotation, wanted, glide));
                view.fieldOfView = Mathf.Lerp(view.fieldOfView, 42, glide);
                return;
            }
            focus = Vector3.Lerp(focus, focusTarget + panOffset, Mathf.Clamp01(Time.deltaTime * 2.2f));
            zoom = Mathf.Lerp(zoom, zoomTarget, Mathf.Clamp01(Time.deltaTime * 1.4f));
            var pos = focus + new Vector3(.9f, 3.5f, -3.4f) * zoom;
            var look = Quaternion.LookRotation(focus + Vector3.up * .15f - pos, Vector3.up);
            digBlend = Mathf.MoveTowards(digBlend, digging != null ? 1 : 0, Time.deltaTime / .7f);
            if (digging != null) { if (!stroking) digPan = Vector3.Lerp(digPan, digPanTo, Mathf.Clamp01(Time.deltaTime * 1.6f)); lastEye = digEye + digPan; lastLook = digLook; }
            if (digBlend > 0) { float b = Mathf.SmoothStep(0, 1, digBlend); pos = Vector3.Lerp(pos, lastEye, b); look = Quaternion.Slerp(look, lastLook, b); }
            view.fieldOfView = Mathf.Lerp(42, 33, Mathf.SmoothStep(0, 1, digBlend));
            // close to the mud the far shadow range only wastes the shadow map, and its steps show
            if (UnityEngine.Rendering.GraphicsSettings.currentRenderPipeline is UnityEngine.Rendering.Universal.UniversalRenderPipelineAsset urp) urp.shadowDistance = Mathf.Lerp(34, 9, digBlend);
            if (digDip > .001f) { pos += Vector3.down * digDip; look *= Quaternion.Euler(digDip * 25, 0, 0); }
            if (shake > .001f) { pos += UnityEngine.Random.insideUnitSphere * shake; shake *= Mathf.Pow(.002f, Time.deltaTime); }
            view.transform.SetPositionAndRotation(pos, look);
        }

        // ---- ui ------------------------------------------------------------------------------------------------------
        void AnimateMarks()
        {
            float pulse = .5f + .5f * Mathf.Sin(Time.time * 3);
            if (markMat != null) markMat.SetColor("_BaseColor", new Color(.42f, .86f, .72f, .14f + .2f * pulse));
        }

        // ---- gates --------------------------------------------------------------------------------------------------
        static readonly Vector3 GatesFocus = new Vector3(0, 0, 6.9f); const float GatesZoom = 2.6f;
        bool viewWheel; readonly List<GateView> gateViews = new List<GateView>(); Button viewButton, planChip, planClose; GameObject planPanel; AudioClip farChantClip;
        public Button GateChip(int i) => gateViews[i].chip;
        public Button ViewButton => viewButton; public Button PlanChip => planChip; public Button PlanClose => planClose;
        public bool PlanOpen => planPanel.activeSelf; public bool ViewingWheel => viewWheel;

        public void PressGate(string id)
        {
            var r = Sim.FieldFull(id) ? new CreekStep { ok = false, code = "FIELD_FULL", message = Sim.GateData(id).label + "已經滿了" } : Sim.CycleGate(id);
            Say(r.message, r.code);
            if (r.ok) { Play(tickClip, "tick", .6f); RefreshStatus(); SaveNow(); }
        }

        void ToggleView() { viewWheel = !viewWheel; RetargetCamera(); }
        void ShowPlan(bool show) => planPanel.SetActive(show);

        void UpdateGateUi()
        {
            bool work = Sim.WorkDone && !closeUp && digging == null && !Sim.s.done && !planPanel.activeSelf; float unit = Screen.height / 1080f;
            for (int i = 0; i < gateViews.Count; i++)
            {
                var v = gateViews[i]; var g = content.distribution.gates[i]; var st = Sim.Gate(g.id);
                v.chip.gameObject.SetActive(work && !viewWheel);
                if (!v.chip.gameObject.activeSelf) continue;
                v.chip.transform.position = (Vector2)view.WorldToScreenPoint(fieldGates[i].at + Vector3.up * .9f) + new Vector2(0, 60 * unit);
                v.text.text = $"{g.label} {(st.level == 0 ? "關" : st.level < 1 ? "半開" : "全開")}　{st.fill / g.fieldM:P0}";
                v.back.color = st.level == 0 ? AlchemyUi.BambooDark : st.level < 1 ? AlchemyUi.Bamboo : AlchemyUi.Jade;
            }
            bool setting = Sim.WorkDone && !Sim.GateOpen && !closeUp && digging == null && !planPanel.activeSelf;
            viewButton.gameObject.SetActive(setting); if (setting) viewButton.GetComponentInChildren<Text>().text = viewWheel ? "看閘門" : "去轉閘輪";
            planChip.gameObject.SetActive(work && !viewWheel);
            if (planChip.gameObject.activeSelf) planChip.transform.position = (Vector2)view.WorldToScreenPoint(planSign.position + Vector3.up * 1.1f) + new Vector2(0, 50 * unit);
        }

        void BuildGateUi(Transform canvas)
        {
            gateViews.Clear();
            for (int i = 0; i < fieldGates.Length; i++)
            {
                var id = content.distribution.gates[i].id;
                var b = HarvestUi.Button("Gate_" + id, canvas, "", () => PressGate(id), new Vector2(0, 0), Vector2.zero, new Vector2(300, 92), AlchemyUi.BambooDark, 30);
                ((RectTransform)b.transform).pivot = new Vector2(.5f, .5f); b.gameObject.SetActive(false);
                gateViews.Add(new GateView { chip = b, text = b.GetComponentInChildren<Text>(), back = b.GetComponent<Image>(), home = fieldGates[i].parts.Select(p => p.localPosition.y).ToArray() });
            }
            viewButton = HarvestUi.Button("GateViewToggle", canvas, "去轉閘輪", ToggleView, new Vector2(1, 0), new Vector2(-24, 24), new Vector2(260, 100), AlchemyUi.Bamboo, 32);
            ((RectTransform)viewButton.transform).pivot = new Vector2(1, 0); ((RectTransform)viewButton.transform).anchoredPosition = new Vector2(-24, 24); viewButton.gameObject.SetActive(false);
            planChip = HarvestUi.Button("PlanSign", canvas, "分水牌", () => ShowPlan(true), new Vector2(0, 0), Vector2.zero, new Vector2(170, 80), AlchemyUi.Bamboo, 28);
            ((RectTransform)planChip.transform).pivot = new Vector2(.5f, .5f); planChip.gameObject.SetActive(false);

            // what the sign shows. The words live here on the screen; the model carries none.
            var panel = AlchemyUi.Panel("PlanPanel", canvas, new Vector2(.5f, .5f), new Vector2(.5f, .5f), new Vector2(-560, -320), new Vector2(560, 320), new Color(.1f, .09f, .07f, .94f));
            planPanel = panel.gameObject;
            var title = HarvestUi.Label("PlanTitle", panel.transform, "分水牌", 40, TextAnchor.UpperCenter, Color.white); ((RectTransform)title.transform).offsetMin = new Vector2(20, 20); ((RectTransform)title.transform).offsetMax = new Vector2(-20, -18);
            Image Bar(string name, float x0, float y0, float x1, float y1, Color c) { var i = AlchemyUi.Panel(name, panel.transform, new Vector2(.5f, .5f), new Vector2(.5f, .5f), new Vector2(x0, y0), new Vector2(x1, y1), c); i.raycastTarget = false; return i; }
            var earth = new Color(.31f, .23f, .15f); var furrow = new Color(.2f, .145f, .09f);
            Bar("PlanCanal", -360, -22, 360, -10, AlchemyUi.Jade); Bar("PlanInflow", -6, -96, 6, -22, AlchemyUi.Jade);
            var order = new[] { 1, 0, 2 };   // west, middle, east, as they lie
            for (int c = 0; c < 3; c++)
            {
                var g = content.distribution.gates[order[c]]; float x = -360 + c * 360, w = 150 + g.fieldM * 26;
                Bar("PlanField", x - w / 2, 62, x + w / 2, 222, earth);
                for (int f = 0; f < 5; f++) { float fx = x - w / 2 + w * (f + .5f) / 5; Bar("PlanFurrow", fx - w * .05f, 76, fx + w * .05f, 208, furrow); }
                Bar("PlanStem", x - 6, -10, x + 6, 20, AlchemyUi.Jade); Bar("PlanStemIn", x - 6, 46, x + 6, 62, new Color(AlchemyUi.Jade.r, AlchemyUi.Jade.g, AlchemyUi.Jade.b, g.planLevel));
                Bar("PlanGateBack", x - 62, 20, x + 62, 46, AlchemyUi.BambooDark); Bar("PlanGateOpen", x - 62, 20, x - 62 + 124 * g.planLevel, 46, AlchemyUi.Jade);
                var label = AlchemyUi.Rect("PlanLabel", panel.transform, new Vector2(.5f, .5f), new Vector2(.5f, .5f), new Vector2(x - 150, 92), new Vector2(x + 150, 192));
                var line = HarvestUi.Label("PlanLabelText", label, $"{g.label}\n{(g.planLevel < 1 ? "半開" : "全開")}", 34, TextAnchor.MiddleCenter, Color.white); line.raycastTarget = false;
            }
            var noteRoot = AlchemyUi.Rect("PlanNote", panel.transform, new Vector2(.5f, .5f), new Vector2(.5f, .5f), new Vector2(-520, -210), new Vector2(520, -105));
            var note = HarvestUi.Label("PlanNoteText", noteRoot, "照這樣開，三塊田會一起灌滿。\n不照著開也一樣都會灌滿，放水時還能再調。", 28, TextAnchor.MiddleCenter, Color.white); note.raycastTarget = false;
            planClose = HarvestUi.Button("PlanClose", panel.transform, "收起", () => ShowPlan(false), new Vector2(.5f, 0), new Vector2(0, 24), new Vector2(220, 84), AlchemyUi.Bamboo, 30);
            ((RectTransform)planClose.transform).pivot = new Vector2(.5f, 0); ((RectTransform)planClose.transform).anchoredPosition = new Vector2(0, 24);
            planPanel.SetActive(false);
        }

        void UpdateWheelRing()
        {
            bool show = Sim.WorkDone && !Sim.GateOpen && viewWheel;
            wheelRing.gameObject.SetActive(show);
            if (!show) return;
            RectTransformUtility.ScreenPointToLocalPointInRectangle((RectTransform)wheelRing.parent, WheelScreen, null, out var local);
            wheelRing.localPosition = local + new Vector2(0, 190);   // above the wheel, not on it
            wheelHint.text = $"順時針轉\n{Sim.s.wheelDegrees / content.flow.wheelDegrees:P0}";
        }

        void BuildUi()
        {
            var canvas = HarvestUi.Canvas("CreekCanvas", 20); canvas.transform.SetParent(transform);
            var top = AlchemyUi.Panel("StatusPanel", canvas.transform, new Vector2(0, 1), new Vector2(0, 1), new Vector2(24, -148), new Vector2(620, -24), AlchemyUi.Bamboo);
            status = HarvestUi.Label("Status", top.transform, "", 30, TextAnchor.UpperLeft, AlchemyUi.Ink);
            ((RectTransform)status.transform).offsetMin = new Vector2(20, 22); ((RectTransform)status.transform).offsetMax = new Vector2(-20, -10);
            var barBack = AlchemyUi.Panel("MudBack", top.transform, new Vector2(0, 0), new Vector2(1, 0), new Vector2(20, 8), new Vector2(-20, 22), AlchemyUi.BambooDark);
            mudBar = AlchemyUi.Panel("MudBar", barBack.transform, Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero, AlchemyUi.Jade);
            mudBar.type = Image.Type.Filled; mudBar.fillMethod = Image.FillMethod.Horizontal; mudBar.fillAmount = 0; mudBar.sprite = null;
            var msg = AlchemyUi.Panel("MessagePanel", canvas.transform, new Vector2(.5f, 1), new Vector2(.5f, 1), new Vector2(-330, -140), new Vector2(760, -24), AlchemyUi.Shade);
            message = HarvestUi.Label("Message", msg.transform, "", 32, TextAnchor.MiddleCenter, Color.white); msg.gameObject.SetActive(false);
            ((RectTransform)message.transform).offsetMin = new Vector2(16, 6); ((RectTransform)message.transform).offsetMax = new Vector2(-16, -6);
            var cardRoot = AlchemyUi.Rect("Cards", canvas.transform, new Vector2(.5f, 0), new Vector2(.5f, 0), new Vector2(-700, 40), new Vector2(700, 180));
            cards = cardRoot.gameObject; cards.SetActive(false);
            var ring = AlchemyUi.Panel("WheelRing", canvas.transform, new Vector2(.5f, .5f), new Vector2(.5f, .5f), new Vector2(-90, -60), new Vector2(90, 60), new Color(.08f, .07f, .05f, .35f));
            wheelRing = (RectTransform)ring.transform; ring.raycastTarget = false;
            wheelHint = HarvestUi.Label("WheelHint", wheelRing, "", 28, TextAnchor.MiddleCenter, Color.white); wheelHint.raycastTarget = false; ring.gameObject.SetActive(false);
            dragLine = Line("DragLine", .05f); dragLine.enabled = false; gapLine = Line("GapLine", .05f); gapLine.material.SetColor("_BaseColor", AlchemyUi.Cinnabar); gapLine.enabled = false;
            BuildGateUi(canvas.transform);
            picker = BuildPicker(canvas.transform);
            leaveButton = HarvestUi.Button("LeaveDig", canvas.transform, "起身", LeaveDig, new Vector2(1, 1), new Vector2(-24, -24), new Vector2(170, 96), AlchemyUi.BambooDark, 32);
            ((RectTransform)leaveButton.transform).pivot = new Vector2(1, 1); ((RectTransform)leaveButton.transform).anchoredPosition = new Vector2(-24, -24); leaveButton.gameObject.SetActive(false);
            lamp = AlchemyUi.Panel("ChantLamp", canvas.transform, new Vector2(.5f, 0), new Vector2(.5f, 0), new Vector2(-70, 28), new Vector2(70, 118), new Color(.08f, .07f, .05f, .45f)); lamp.raycastTarget = false;
            lampText = HarvestUi.Label("ChantText", lamp.transform, "", 46, TextAnchor.MiddleCenter, Color.white); lampText.raycastTarget = false; lamp.gameObject.SetActive(false);
        }

        LineRenderer Line(string name, float width)
        {
            var l = new GameObject(name).AddComponent<LineRenderer>(); l.transform.SetParent(transform); l.positionCount = 2; l.startWidth = l.endWidth = width;
            l.material = new Material(lineMat); return l;
        }

        GameObject BuildPicker(Transform parent)
        {
            var root = AlchemyUi.Panel("Picker", parent, new Vector2(.5f, .5f), new Vector2(.5f, .5f), new Vector2(-520, -320), new Vector2(520, 250), AlchemyUi.Bamboo);
            var title = HarvestUi.Label("Title", root.transform, "測試入口：修法由對話決定，這裡只為了試玩", 28, TextAnchor.UpperCenter, AlchemyUi.Ink);
            ((RectTransform)title.transform).offsetMin = new Vector2(20, 20); ((RectTransform)title.transform).offsetMax = new Vector2(-20, -24);
            float y = 90;
            foreach (var id in new[] { "clear_silt", "restore_channel", "protect_nursery" })
            {
                var m = id; var b = HarvestUi.Button("Pick_" + id, root.transform, content.Method(id).label, () => Begin(m, 1), new Vector2(.5f, .5f), new Vector2(0, y), new Vector2(560, 96), AlchemyUi.Jade, 32);
                ((RectTransform)b.transform).pivot = new Vector2(.5f, .5f); ((RectTransform)b.transform).anchoredPosition = new Vector2(0, y);
                pickerButtons.Add(b); y -= 112;
            }
            if (File.Exists(SavePath) && JsonUtility.FromJson<CreekState>(File.ReadAllText(SavePath)).version == content.version)
            {
                var b = HarvestUi.Button("Resume", root.transform, "繼續上次", RestoreSaved, new Vector2(.5f, .5f), new Vector2(0, y), new Vector2(560, 96), AlchemyUi.BambooDark, 30);
                ((RectTransform)b.transform).pivot = new Vector2(.5f, .5f); ((RectTransform)b.transform).anchoredPosition = new Vector2(0, y);
            }
            return root.gameObject;
        }

        static Vector3 Flat(Vector3 v) => new Vector3(v.x, 0, v.z);
    }
}
