using System.Collections;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace YunJing
{
    // K5: streams the novice world's neighbouring blocks around the village. Each block is its own scene (built by
    // QingxiBlockBuilder); it loads additively when the player comes within LoadAt metres of its area and unloads
    // beyond UnloadAt, so the browser only holds what is near. The village scene stays the active scene (its sun,
    // sky and fog light every block).
    public sealed class QingxiBlockStreamer : MonoBehaviour
    {
        [System.Serializable]
        public class Block { public string id, scene; public Rect area; }

        public Block[] blocks = new Block[0];
        public float LoadAt = 45, UnloadAt = 90;
        public static QingxiBlockStreamer Current { get; private set; }

        readonly System.Collections.Generic.HashSet<string> busy = new System.Collections.Generic.HashSet<string>();

        void Awake() { Current = this; }

        public bool IsLoaded(string id)
        {
            foreach (var b in blocks) if (b.id == id) return SceneManager.GetSceneByName(b.scene).isLoaded;
            return false;
        }

        static float Distance(Rect r, Vector3 p)
        {
            float dx = Mathf.Max(r.xMin - p.x, 0, p.x - r.xMax), dz = Mathf.Max(r.yMin - p.z, 0, p.z - r.yMax);
            return Mathf.Sqrt(dx * dx + dz * dz);
        }

        IEnumerator Start()
        {
            var wait = new WaitForSeconds(.5f);
            while (true)
            {
                var walker = QingxiWorld.QingxiFirstPerson.Current;
                if (walker != null)
                    foreach (var b in blocks)
                    {
                        if (busy.Contains(b.id) || !Application.CanStreamedLevelBeLoaded(b.scene)) continue;
                        float d = Distance(b.area, walker.transform.position);
                        bool loaded = SceneManager.GetSceneByName(b.scene).isLoaded;
                        if (!loaded && d < LoadAt) StartCoroutine(Change(b, true));
                        else if (loaded && d > UnloadAt) StartCoroutine(Change(b, false));
                    }
                yield return wait;
            }
        }

        IEnumerator Change(Block b, bool load)
        {
            busy.Add(b.id);
            var op = load ? SceneManager.LoadSceneAsync(b.scene, LoadSceneMode.Additive) : SceneManager.UnloadSceneAsync(b.scene);
            if (op != null) yield return op;
            Debug.Log($"QINGXI_BLOCK {(load ? "loaded" : "unloaded")} {b.id}");
            busy.Remove(b.id);
        }
    }
}
