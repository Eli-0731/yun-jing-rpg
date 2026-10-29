using System.Collections.Generic;
using UnityEngine;

namespace YunJing
{
    // In-place motion for the low-detail original study avatar. The polished
    // Heroine-01 will need a skinned rig and authored animation clips.
    public sealed class QingxiNoviceMotion : MonoBehaviour
    {
        struct Part
        {
            public Transform transform;
            public Quaternion rest;
            public float side;
            public float amount;
            public bool hair;
        }

        readonly List<Part> parts = new List<Part>();
        Transform traveler;
        Vector3 previous;
        Vector3 restingLocalPosition;
        float phase;
        float motion;

        void Awake()
        {
            traveler = transform.parent;
            previous = traveler == null ? transform.position : traveler.position;
            restingLocalPosition = transform.localPosition;
            foreach (var part in GetComponentsInChildren<Transform>(true))
            {
                string name = part.name;
                bool leg = name.Contains("SK_QX13_Leg_");
                bool arm = name.Contains("SK_QX13_UpperArm_") || name.Contains("SK_QX13_Sleeve_");
                bool hair = name.Contains("SK_QX13_BackHair_") || name.Contains("SK_QX13_TempleHair_");
                if (!leg && !arm && !hair) continue;
                parts.Add(new Part { transform = part, rest = part.localRotation,
                    side = name.EndsWith("_-1") ? -1 : 1,
                    amount = leg ? .22f : arm ? -.14f : .025f, hair = hair });
            }
        }

        void LateUpdate()
        {
            if (traveler == null) return;
            float dt = Mathf.Max(Time.deltaTime, .0001f);
            Vector3 delta = traveler.position - previous;
            previous = traveler.position;
            delta.y = 0;
            float target = Mathf.Clamp01(delta.magnitude / dt / 3.5f);
            motion = Mathf.Lerp(motion, target, 1 - Mathf.Exp(-9 * dt));
            phase += dt * Mathf.Lerp(1.8f, 9.8f, motion);
            float stride = Mathf.Sin(phase) * motion;
            transform.localPosition = restingLocalPosition + Vector3.up *
                (Mathf.Abs(Mathf.Sin(phase)) * .04f * motion + Mathf.Sin(Time.time * 2) * .006f);
            foreach (var part in parts)
            {
                if (part.transform == null) continue;
                float angle = part.hair ? Mathf.Sin(Time.time * 2.7f + part.side) * part.amount
                    : stride * part.amount * part.side;
                part.transform.localRotation = part.rest * Quaternion.Euler(angle * Mathf.Rad2Deg, 0, 0);
            }
        }
    }
}
