using System.Collections.Generic;
using UnityEngine;

namespace YunJing
{
    // Marks what the sick boar can run into on day 3: its colliders set the size the rules see. A pine (leanDegrees > 0) leans,
    // shakes and sheds needles when struck, with its pale scar opened through the material's _Scar. Objects named
    // D3_BoarTree_01..03 get this component from QingxiZhuoBoarEncounter even if nobody added it.
    public sealed class BoarObstacle : MonoBehaviour
    {
        public static readonly List<BoarObstacle> All = new List<BoarObstacle>();
        static readonly int ScarId = Shader.PropertyToID("_Scar");

        public float leanDegrees;
        public Color needleColour = new Color(.52f, .6f, .3f);

        public float Radius { get; private set; }
        public Vector3 Centre { get; private set; }
        public bool Struck { get; private set; }

        Quaternion rest; Vector3 axis; float strikeAt = -100, scar;
        Renderer[] renderers; MaterialPropertyBlock block;

        void Awake()
        {
            rest = transform.rotation;
            renderers = GetComponentsInChildren<Renderer>();
            block = new MaterialPropertyBlock();
            Measure();
        }

        void OnEnable() { if (!All.Contains(this)) All.Add(this); }
        void OnDisable() { All.Remove(this); }

        void Measure()
        {
            var found = false; var total = new Bounds(transform.position, Vector3.zero);
            foreach (var c in GetComponentsInChildren<Collider>())
            {
                if (c.isTrigger) continue;
                if (!found) { total = c.bounds; found = true; } else total.Encapsulate(c.bounds);
            }
            Centre = found ? total.center : transform.position;
            Radius = found ? Mathf.Max(total.extents.x, total.extents.z) : .2f;
        }

        public void Strike(Vector3 boarPosition, QingxiZhuoBoarFx fx)
        {
            if (leanDegrees <= 0) return;
            var away = transform.position - boarPosition; away.y = 0;
            if (!Struck && away.sqrMagnitude > 1e-4f) axis = Vector3.Cross(Vector3.up, away.normalized);
            Struck = true;
            strikeAt = Time.time;
            if (fx != null) fx.Needles(transform.position, needleColour);
        }

        void Update()
        {
            if (!Struck) return;
            float t = Time.time - strikeAt;
            if (t > 4 && scar >= .999f) return;
            // A damped swing that settles at the lean.
            float angle = leanDegrees * (1 - Mathf.Exp(-3.5f * t) * Mathf.Cos(13f * t));
            transform.rotation = Quaternion.AngleAxis(angle, axis) * rest;
            scar = Mathf.MoveTowards(scar, 1, Time.deltaTime * 6);
            foreach (var r in renderers)
            {
                if (r == null) continue;
                r.GetPropertyBlock(block);
                block.SetFloat(ScarId, scar);
                r.SetPropertyBlock(block);
            }
        }
    }
}
