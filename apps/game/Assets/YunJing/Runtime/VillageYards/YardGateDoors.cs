using System.Collections.Generic;
using System.Linq;
using UnityEngine;

namespace YunJing.VillageYards
{
    // Opening and closing for the CW02 yard gate (work pack 2026-11-11 B-40h). Put it on the root of a placed CW02_A_GateOpen
    // (art/exports/village-yards-b/CW02_A_GateOpen): that export has the doors turned open and its static collision leaves the doorway free.
    //
    // Setup():
    //  - a pivot is made at Socket_HingeL / Socket_HingeR and every LOD of Detail_DoorL / Detail_DoorR is parented to it, so all LODs turn together;
    //  - each pivot gets a kinematic Rigidbody and a BoxCollider fitted to its LOD0 leaf (the leaf blocks walkers in any position);
    //  - the two open-leaf blocks in the exported static collision are taken out of the MeshCollider (they stand where the open leaves are,
    //    and would be invisible walls once the doors close).
    // Open() / Close() / Toggle() swing both leaves (about 0.8 s). A leaf that would close into a CharacterController stops where it is
    // until the way is clear (IsBlocked), so nobody is shut inside a door.
    // Nothing here reads input: the core team wires Toggle() to the player's interaction key when placing the gate.
    // The FBX must import with Read/Write enabled (isReadable), so the collision mesh can be read.
    public sealed class YardGateDoors : MonoBehaviour
    {
        [Tooltip("Start with the doors shut (the export itself has them open).")] public bool startOpen = false;
        [Tooltip("Seconds for a full swing.")] public float swingSeconds = .8f;
        [Tooltip("A closing leaf stops this far (m) before a CharacterController in its way.")] public float stopMargin = .08f;
        // CW02 sizes (Blender cw_gate.py): post inner face 0.67 m, door plane y -0.08, leaf 0.666 m wide, threshold top 0.12 m.
        // Used only to find the open-leaf blocks in the exported collision mesh (local x, up, z = Blender x, z, y).
        const float Inner = .67f, DoorZ = -.08f, LeafW = .666f, ThresholdTop = .12f;

        class Leaf
        {
            public Transform pivot; public BoxCollider box; public Quaternion closed, open; public float t, target; public bool blocked;
        }

        readonly List<Leaf> leaves = new List<Leaf>();
        bool ready;
        public int RemovedCollisionTriangles { get; private set; }
        public bool IsOpen => leaves.Count > 0 && leaves.All(l => l.target > .5f);
        public bool IsMoving => leaves.Any(l => Mathf.Abs(l.t - l.target) > 1e-4f);
        public bool IsBlocked => leaves.Any(l => l.blocked);
        /// 0 = shut, 1 = fully open (the average of the two leaves).
        public float Openness => leaves.Count == 0 ? 0 : leaves.Average(l => l.t);

        void Awake() { Setup(); }

        public void Setup()
        {
            if (ready) return;
            ready = true;
            var all = GetComponentsInChildren<Transform>(true);
            foreach (var (side, letter) in new[] { (-1, "L"), (1, "R") })
            {
                var hinge = all.FirstOrDefault(t => t.name.StartsWith("Socket_Hinge" + letter));
                var parts = all.Where(t => t.name.Contains("_Detail_Door" + letter + "_LOD")).ToArray();
                if (hinge == null || parts.Length == 0) { Debug.LogWarning($"YardGateDoors: no Socket_Hinge{letter} or Detail_Door{letter} under {name}"); continue; }
                var pivot = new GameObject("Door" + letter + "_Pivot").transform;
                pivot.SetParent(transform, false); pivot.position = hinge.position; pivot.rotation = transform.rotation;
                foreach (var p in parts) p.SetParent(pivot, true);
                // where the leaf points now (open in the export) and where it points shut: towards the middle of the gate
                var lod0 = parts.FirstOrDefault(p => p.name.EndsWith("_LOD0")) ?? parts[0];
                var r0 = lod0.GetComponent<Renderer>();
                Vector3 now = Flat(r0.bounds.center - pivot.position);
                Vector3 shutDir = Flat(transform.TransformDirection(Vector3.right * -side));
                float openAngle = Vector3.SignedAngle(shutDir, now, transform.up);
                var leaf = new Leaf { pivot = pivot, open = pivot.rotation, closed = Quaternion.AngleAxis(-openAngle, transform.up) * pivot.rotation };
                // the collider is fitted with the leaf shut, in the pivot's own frame
                pivot.rotation = leaf.closed;
                var b = LocalBounds(pivot, r0);
                var rb = pivot.gameObject.AddComponent<Rigidbody>(); rb.isKinematic = true; rb.useGravity = false; rb.interpolation = RigidbodyInterpolation.None;
                leaf.box = pivot.gameObject.AddComponent<BoxCollider>(); leaf.box.center = b.center; leaf.box.size = b.size;
                leaf.t = leaf.target = startOpen ? 1 : 0;
                pivot.rotation = Quaternion.Slerp(leaf.closed, leaf.open, leaf.t);
                leaves.Add(leaf);
            }
            RemovedCollisionTriangles = StripOpenLeafBlocks();
            Physics.SyncTransforms();
        }

        public void Open() { Setup(); foreach (var l in leaves) l.target = 1; }
        public void Close() { Setup(); foreach (var l in leaves) l.target = 0; }
        public void Toggle() { if (IsOpen) Close(); else Open(); }

        /// Jump to a state without the swing (for placing a gate shut or open in a scene).
        public void SetOpenImmediate(bool open)
        {
            Setup();
            foreach (var l in leaves) { l.t = l.target = open ? 1 : 0; l.blocked = false; l.pivot.rotation = Quaternion.Slerp(l.closed, l.open, l.t); }
            Physics.SyncTransforms();
        }

        void Update() { Step(Time.deltaTime); }

        /// Advance the swing by dt seconds (Update calls it; the editor check calls it directly).
        public void Step(float dt)
        {
            if (!ready) return;
            float rate = dt / Mathf.Max(.05f, swingSeconds);
            foreach (var l in leaves)
            {
                l.blocked = false;
                if (Mathf.Abs(l.t - l.target) < 1e-4f) continue;
                float next = Mathf.MoveTowards(l.t, l.target, rate);
                var rot = Quaternion.Slerp(l.closed, l.open, Smooth(next));
                // closing into someone: stay where the leaf is
                if (next < l.t && HitsCharacter(l, rot)) { l.blocked = true; continue; }
                l.t = next; l.pivot.rotation = rot;
            }
        }

        bool HitsCharacter(Leaf l, Quaternion rot)
        {
            var c = l.pivot.position + rot * Vector3.Scale(l.box.center, l.pivot.lossyScale);
            // padded: the PhysX overlap against a CharacterController capsule only reported it once the leaf was about 5 cm into its
            // radius (measured in the editor check), so the leaf looks ahead by this margin and stops before it touches
            var half = Vector3.Scale(l.box.size, l.pivot.lossyScale) * .5f + Vector3.one * stopMargin;
            foreach (var hit in Physics.OverlapBox(c, half, rot, ~0, QueryTriggerInteraction.Ignore))
                if (hit is CharacterController) return true;
            return false;
        }

        // The export's static collision has one block per open leaf (x on the hinge side, from the door plane 0.67 m into the yard,
        // threshold top to lintel). Take out every triangle whose three corners are all inside one of those two blocks.
        int StripOpenLeafBlocks()
        {
            var mc = GetComponentsInChildren<MeshCollider>(true).FirstOrDefault(m => m.name.EndsWith("_Collision"));
            if (mc == null || mc.sharedMesh == null) return 0;
            var src = mc.sharedMesh; var v = src.vertices; var tris = src.triangles;
            bool inBlock(Vector3 p) => Mathf.Abs(p.x) > Inner - .075f && Mathf.Abs(p.x) < Inner + .075f && p.y > ThresholdTop - .005f
                                       && p.z > DoorZ - .005f && p.z < DoorZ + LeafW + .04f;
            var keep = new List<int>(tris.Length); int removed = 0;
            for (int i = 0; i < tris.Length; i += 3)
            {
                var a = v[tris[i]]; var b = v[tris[i + 1]]; var c = v[tris[i + 2]];
                if (inBlock(a) && inBlock(b) && inBlock(c) && Mathf.Sign(a.x) == Mathf.Sign(b.x) && Mathf.Sign(b.x) == Mathf.Sign(c.x)) { removed++; continue; }
                keep.Add(tris[i]); keep.Add(tris[i + 1]); keep.Add(tris[i + 2]);
            }
            if (removed == 0) return 0;
            var m = new Mesh { name = src.name + "_GateDoorsRemoved" };
            m.vertices = v; m.triangles = keep.ToArray(); m.RecalculateBounds(); m.RecalculateNormals();
            mc.sharedMesh = m;
            return removed;
        }

        static float Smooth(float t) => t * t * (3 - 2 * t);
        static Vector3 Flat(Vector3 d) { d.y = 0; return d.normalized; }

        static Bounds LocalBounds(Transform frame, Renderer r)
        {
            var mf = r.GetComponent<MeshFilter>(); var mesh = mf.sharedMesh; var b = new Bounds(); bool first = true;
            foreach (var p in mesh.vertices)
            {
                var q = frame.InverseTransformPoint(r.transform.TransformPoint(p));
                if (first) { b = new Bounds(q, Vector3.zero); first = false; } else b.Encapsulate(q);
            }
            return b;
        }
    }
}
