using UnityEngine;

namespace YunJing
{
    // Procedural stand-in art for the jade/paper/ink UI (docs/art/ui-ux-direction-v1.md) until the drawn sprites
    // from Codex C6 arrive: a jade disc with depth (lighter rim facet, darker lower half, a glint top-right), rings,
    // a soft glow and a rounded strip. Generated once, so the browser download does not grow.
    public static class QingxiUiArt
    {
        public static readonly Color JadeDeep = new Color(.23f, .47f, .42f), JadeLight = new Color(.62f, .85f, .79f),
            JadeGlow = new Color(.5f, .88f, .83f), Ink = new Color(.07f, .1f, .095f, .78f), Gold = new Color(.86f, .73f, .45f),
            Mist = new Color(.93f, .95f, .95f), Paper = new Color(.95f, .925f, .875f, .94f);

        static Texture2D jade, ring, soft, strip;

        public static Texture2D Jade => jade != null ? jade : jade = MakeJade(256);
        public static Texture2D Ring => ring != null ? ring : ring = MakeRing(256, 118, 6);
        public static Texture2D Soft => soft != null ? soft : soft = MakeSoft(128);
        public static Texture2D Strip => strip != null ? strip : strip = MakeStrip(48, 22);

        static Texture2D New(int size) => new Texture2D(size, size, TextureFormat.RGBA32, false) { wrapMode = TextureWrapMode.Clamp };

        static Texture2D MakeJade(int size)
        {
            var t = New(size); var px = new Color[size * size]; float c = size / 2f - .5f, r = size / 2f - 2;
            for (int y = 0; y < size; y++)
                for (int x = 0; x < size; x++)
                {
                    float dx = (x - c) / r, dy = (y - c) / r, d = Mathf.Sqrt(dx * dx + dy * dy);
                    float a = Mathf.Clamp01((1 - d) * r);                       // anti-aliased edge
                    float body = Mathf.InverseLerp(-1, 1, dy);                    // lighter toward the top
                    var col = Color.Lerp(JadeDeep, JadeLight, body * .75f + .1f);
                    float rim = Mathf.SmoothStep(0, 1, Mathf.InverseLerp(.80f, .95f, d)) * (1 - Mathf.InverseLerp(.97f, 1f, d));
                    col = Color.Lerp(col, Mist, rim * .55f);                      // bright facet around the edge
                    float glint = Mathf.Exp(-((dx - .38f) * (dx - .38f) + (dy - .42f) * (dy - .42f)) * 40);
                    col = Color.Lerp(col, Color.white, glint * .7f);
                    float inner = Mathf.Exp(-d * d * 3) * .18f;                   // milky glow inside the stone
                    col = Color.Lerp(col, JadeGlow, inner);
                    col.a = a * .92f;
                    px[y * size + x] = col;
                }
            t.SetPixels(px); t.Apply(); return t;
        }

        static Texture2D MakeRing(int size, float radius, float stroke)
        {
            var t = New(size); var px = new Color32[size * size]; float c = size / 2f - .5f;
            for (int y = 0; y < size; y++)
                for (int x = 0; x < size; x++)
                {
                    float d = Mathf.Sqrt((x - c) * (x - c) + (y - c) * (y - c));
                    px[y * size + x] = new Color32(255, 255, 255, (byte)(Mathf.Clamp01(stroke / 2 + .5f - Mathf.Abs(d - radius)) * 255));
                }
            t.SetPixels32(px); t.Apply(); return t;
        }

        static Texture2D MakeSoft(int size)
        {
            var t = New(size); var px = new Color32[size * size]; float c = size / 2f - .5f;
            for (int y = 0; y < size; y++)
                for (int x = 0; x < size; x++)
                {
                    float d = Mathf.Sqrt((x - c) * (x - c) + (y - c) * (y - c)) / (size / 2f);
                    px[y * size + x] = new Color32(255, 255, 255, (byte)(Mathf.Pow(Mathf.Clamp01(1 - d), 2) * 255));
                }
            t.SetPixels32(px); t.Apply(); return t;
        }

        static Texture2D MakeStrip(int size, float radius)
        {
            var t = New(size); var px = new Color[size * size];
            for (int y = 0; y < size; y++)
                for (int x = 0; x < size; x++)
                {
                    float qx = Mathf.Max(Mathf.Abs(x + .5f - size / 2f) - (size / 2f - radius), 0), qy = Mathf.Max(Mathf.Abs(y + .5f - size / 2f) - (size / 2f - radius), 0);
                    float d = Mathf.Sqrt(qx * qx + qy * qy) - radius;
                    px[y * size + x] = new Color(1, 1, 1, Mathf.Clamp01(.5f - d));
                }
            t.SetPixels(px); t.Apply(); return t;
        }

        public static void Draw(Rect r, Texture tex, Color colour)
        {
            var old = GUI.color; GUI.color = colour; GUI.DrawTexture(r, tex); GUI.color = old;
        }

        // A strip that keeps its round ends at any width (9-slice).
        public static void Sliced(Rect r, Color colour, int border = 20)
        {
            if (Event.current.type != EventType.Repaint) return;
            var old = GUI.color; GUI.color = colour;
            new GUIStyle { normal = { background = Strip }, border = new RectOffset(border, border, border, border) }.Draw(r, false, false, false, false);
            GUI.color = old;
        }

        public static Rect Circle(Vector2 centre, float diameter) => new Rect(centre.x - diameter / 2, centre.y - diameter / 2, diameter, diameter);
    }
}
