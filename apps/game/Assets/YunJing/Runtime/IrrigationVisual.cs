using UnityEngine;

namespace YunJing
{
    // Presentation only. These controls do not grant crops or change server state.
    // A future private-estate controller can drive them from a verified snapshot.
    public sealed class IrrigationVisual : MonoBehaviour
    {
        public GameObject[] Foliage = new GameObject[0];
        public GameObject[] Water = new GameObject[0];
        public void ShowPlants(bool visible)
        {
            foreach (var part in Foliage) if (part != null) part.SetActive(visible);
        }
        public void ShowWater(bool visible)
        {
            foreach (var part in Water) if (part != null) part.SetActive(visible);
        }
        [ContextMenu("Preview/Empty bed")] void Empty() => ShowPlants(false);
        [ContextMenu("Preview/Planted bed")] void Planted() => ShowPlants(true);
        [ContextMenu("Preview/Dry channel")] void Dry() => ShowWater(false);
        [ContextMenu("Preview/Filled channel")] void Filled() => ShowWater(true);
    }
}
