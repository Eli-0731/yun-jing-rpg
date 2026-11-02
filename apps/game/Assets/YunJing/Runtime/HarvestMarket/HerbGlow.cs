using UnityEngine;

namespace YunJing.HarvestMarket
{
    // Drives the top-grade qingling herb's tip glow (MK02 bundle / plant, MK04 fill) as one 0–1 value, the _Glow
    // parameter of the work pack. URP Lit has no _Glow, so this scales _EmissionColor through a property block:
    // the baked Emission map holds where the tips glow, Glow sets how strongly. Glow 0 = plain leaves.
    [ExecuteAlways]
    public sealed class HerbGlow : MonoBehaviour
    {
        [Range(0, 1)] public float Glow = 1;
        public Color Tint = new Color(.18f, .8f, .7f);
        [Tooltip("Slow breathing on top of Glow; 0 = steady.")] public float Pulse = .18f;
        Renderer[] renderers; MaterialPropertyBlock block; static readonly int Emission = Shader.PropertyToID("_EmissionColor");

        void OnEnable() { renderers = GetComponentsInChildren<Renderer>(true); block = new MaterialPropertyBlock(); Apply(); }

        void Update() { Apply(); }

        public void Apply()
        {
            if (renderers == null) return;
            float k = Mathf.Clamp01(Glow) * (1 - Pulse * .5f + Pulse * .5f * Mathf.Sin(Time.time * 2.1f));
            foreach (var r in renderers)
            {
                if (r == null) continue;
                r.GetPropertyBlock(block); block.SetColor(Emission, Tint * k); r.SetPropertyBlock(block);
            }
        }
    }
}
