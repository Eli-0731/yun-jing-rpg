using System.Collections.Generic;
using UnityEngine;

namespace YunJing
{
    // 機緣 (K4): hidden finds scattered through the world. None is marked on the map; each shows only a faint
    // glint of spirit motes when the player is within about 14 m, brighter as they come closer. F at the glint
    // reveals it: a seal-stamped card with a short passage, and an entry in the travel journal. Found finds stay
    // found: settled by the server through QingxiServerLink when online (K7), remembered on the device offline.
    public sealed class QingxiFortunes : MonoBehaviour
    {
        [System.Serializable]
        public class Fortune
        {
            public string id, title, passage, reward;
            public Vector3 position;
        }

        const float Reach = 2.2f, Visible = 14f;
        public Fortune[] fortunes = new Fortune[0];
        public Material glowDot;   // additive soft dot (the training glow material)

        readonly List<ParticleSystem> glints = new List<ParticleSystem>();
        Fortune shown;
        float shownAt;

        public static QingxiFortunes Current { get; private set; }
        public int Found { get { int n = 0; foreach (var f in fortunes) if (IsFound(f)) n++; return n; } }
        // Found if the server has it (when online) or this device remembers it (offline, or not yet replayed).
        public static bool IsFound(Fortune f) => IsFoundLocally(f) || (QingxiServerLink.Current != null && QingxiServerLink.Current.HasFortune(f.id));
        public static bool IsFoundLocally(Fortune f) { try { return PlayerPrefs.GetInt("yj.fortune." + f.id, 0) == 1; } catch { return false; } }

        void Awake() { Current = this; }

        void Start()
        {
            foreach (var f in fortunes) glints.Add(Glint(f));
        }

        ParticleSystem Glint(Fortune f)
        {
            if (glowDot == null) return null;
            var go = new GameObject("FortuneGlint " + f.id);
            go.transform.SetParent(transform, false);
            go.transform.position = f.position + Vector3.up * .5f;
            var ps = go.AddComponent<ParticleSystem>();
            ps.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);
            var main = ps.main;
            main.loop = true; main.startLifetime = 2.2f; main.startSpeed = .12f; main.startSize = .06f;
            main.maxParticles = 24; main.simulationSpace = ParticleSystemSimulationSpace.World;
            main.startColor = new Color(.62f, 1f, .88f, .9f);
            main.gravityModifier = -.02f;
            var emission = ps.emission; emission.rateOverTime = 8;
            var shape = ps.shape; shape.shapeType = ParticleSystemShapeType.Sphere; shape.radius = .35f;
            var fade = ps.colorOverLifetime; fade.enabled = true;
            var g = new Gradient();
            g.SetKeys(new[] { new GradientColorKey(Color.white, 0), new GradientColorKey(Color.white, 1) },
                new[] { new GradientAlphaKey(0, 0), new GradientAlphaKey(1, .3f), new GradientAlphaKey(0, 1) });
            fade.color = g;
            var r = go.GetComponent<ParticleSystemRenderer>();
            r.sharedMaterial = glowDot; r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            ps.Play();
            return ps;
        }

        void Update()
        {
            var walker = QingxiWorld.QingxiFirstPerson.Current;
            if (walker == null) return;
            for (int i = 0; i < fortunes.Length && i < glints.Count; i++)
            {
                var ps = glints[i];
                if (ps == null) continue;
                bool found = IsFound(fortunes[i]);
                float d = Flat(walker.transform.position, fortunes[i].position);
                // Invisible from afar, a faint shimmer within 14 m, full at arm's length; gone once found.
                float strength = found ? 0 : Mathf.Clamp01(1 - (d - Reach) / (Visible - Reach));
                var emission = ps.emission; emission.rateOverTime = strength * 10;
            }
        }

        static float Flat(Vector3 a, Vector3 b) => Vector2.Distance(new Vector2(a.x, a.z), new Vector2(b.x, b.z));

        Fortune Near(Vector3 position)
        {
            foreach (var f in fortunes) if (!IsFound(f) && Flat(position, f.position) <= Reach) return f;
            return null;
        }

        public string Prompt(Vector3 position) => Near(position) != null ? "F 細看那點微光" : null;

        public bool TryInteract(Vector3 position, out string message)
        {
            message = null;
            var f = Near(position);
            if (f == null) return false;
            Reveal(f);
            message = $"機緣・{f.title}（{Found}／{fortunes.Length}）";
            return true;
        }

        public void Reveal(Fortune f)
        {
            try { PlayerPrefs.SetInt("yj.fortune." + f.id, 1); PlayerPrefs.Save(); } catch { }
            QingxiServerLink.Current?.Submit(new GameAction { kind = "discover-fortune", fortune = f.id });
            shown = f; shownAt = Time.time;
        }

        // Journal lines: found finds by title, the rest as a count only (no spoilers).
        public string JournalText()
        {
            var lines = new List<string> { $"機緣　{Found}／{fortunes.Length}" };
            foreach (var f in fortunes) if (IsFound(f)) lines.Add($"・{f.title}：{f.reward}");
            if (Found < fortunes.Length) lines.Add("還有一些，藏在你沒細看的地方。");
            return string.Join("\n", lines);
        }

        // ------------------------------------------------------------------ the seal card
        GUIStyle titleStyle, bodyStyle, sealStyle, smallStyle;
        static Texture2D paper, seal;

        void OnGUI()
        {
            if (shown == null) return;
            float age = Time.time - shownAt;
            if (age > 6f) { shown = null; return; }
            QingxiFonts.ApplyImgui();
            if (titleStyle == null)
            {
                titleStyle = new GUIStyle { font = QingxiFonts.Title, fontSize = 30, fontStyle = FontStyle.Bold, alignment = TextAnchor.UpperLeft, normal = { textColor = new Color(.11f, .12f, .12f) } };
                bodyStyle = new GUIStyle { font = QingxiFonts.Ui, fontSize = 16, wordWrap = true, alignment = TextAnchor.UpperLeft, normal = { textColor = new Color(.24f, .26f, .25f) } };
                smallStyle = new GUIStyle(bodyStyle) { fontSize = 13, normal = { textColor = new Color(.42f, .36f, .25f) } };
                sealStyle = new GUIStyle { font = QingxiFonts.Title, fontSize = 22, fontStyle = FontStyle.Bold, alignment = TextAnchor.MiddleCenter, normal = { textColor = new Color(.98f, .93f, .86f) } };
                paper = Solid(new Color(.95f, .925f, .875f, .96f)); seal = Solid(new Color(.70f, .23f, .18f, 1));
            }
            float scale = Mathf.Clamp(Screen.height / 720f, .7f, 2f);
            var previous = GUI.matrix;
            GUI.matrix = Matrix4x4.Scale(Vector3.one * scale);
            float w = Screen.width / scale;
            // Fade in 0.3 s, hold, fade out over the last second; the seal lands with a small drop.
            float alpha = Mathf.Clamp01(age / .3f) * Mathf.Clamp01((6f - age) / 1f);
            var old = GUI.color; GUI.color = new Color(1, 1, 1, alpha);
            var card = new Rect(w / 2 - 250, 120, 500, 170);
            GUI.DrawTexture(card, paper);
            float drop = Mathf.Lerp(-14, 0, Mathf.Clamp01((age - .25f) / .18f));
            var sealRect = new Rect(card.xMax - 92, card.y + 22 + drop, 64, 64);
            GUI.DrawTexture(sealRect, seal);
            GUI.Label(sealRect, "機緣", sealStyle);
            GUI.Label(new Rect(card.x + 28, card.y + 22, 360, 40), shown.title, titleStyle);
            GUI.Label(new Rect(card.x + 28, card.y + 70, 380, 64), shown.passage, bodyStyle);
            GUI.Label(new Rect(card.x + 28, card.y + 136, 440, 22), $"得：{shown.reward}　　已記入旅途手札（{Found}／{fortunes.Length}）", smallStyle);
            GUI.color = old;
            GUI.matrix = previous;
        }

        static Texture2D Solid(Color c)
        {
            var t = new Texture2D(1, 1); t.SetPixel(0, 0, c); t.Apply(); return t;
        }
    }
}
