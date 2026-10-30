using UnityEngine;

namespace YunJing
{
    // Shows joshsu54's gathering-kit herb in its "pre" state until the local foraging loop marks the
    // node harvested, then the "post" state until it regrows. Visual only; the count stays in QingxiLocalForaging.
    public sealed class QingxiHerbVisual : MonoBehaviour
    {
        public QingxiLocalForaging foraging;
        public GameObject pre, post;
        bool? shown;

        void Update()
        {
            if (foraging == null || pre == null || post == null) return;
            bool harvested = foraging.IsHarvested(transform);
            if (shown == harvested) return;
            shown = harvested;
            pre.SetActive(!harvested);
            post.SetActive(harvested);
        }
    }
}
