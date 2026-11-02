using System.Collections.Generic;
using UnityEngine;

namespace YunJing.HarvestMarket
{
    // Painted-in-code UI art for the sieve and the stall (no text on the herbs: the player reads the grade from the
    // leaves). Top: whole leaves, tips glowing faint cyan. Mid: whole, no glow. Low: holes and yellowing edges.
    public static class HarvestArt
    {
        static readonly Dictionary<string, Sprite> cache = new Dictionary<string, Sprite>();

        public static readonly Color LeafDark = new Color(.24f, .42f, .17f), LeafLight = new Color(.44f, .64f, .26f);
        public static readonly Color Glow = new Color(.55f, .95f, .9f), Yellow = new Color(.78f, .66f, .22f), Root = new Color(.45f, .32f, .2f);

        public static Sprite Herb(string grade)
        {
            if (cache.TryGetValue("herb-" + grade, out var s)) return s;
            const int n = 160; var px = new Color[n * n];
            void Blend(int x, int y, Color c)
            {
                if (x < 0 || y < 0 || x >= n || y >= n) return;
                int i = y * n + x; var d = px[i]; float a = c.a + d.a * (1 - c.a);
                px[i] = a <= 0 ? Color.clear : new Color((c.r * c.a + d.r * d.a * (1 - c.a)) / a, (c.g * c.a + d.g * d.a * (1 - c.a)) / a, (c.b * c.a + d.b * d.a * (1 - c.a)) / a, a);
            }
            var rng = new System.Random(7);
            // Roots and the twine band.
            for (int r = 0; r < 9; r++)
            {
                float ang = Mathf.Lerp(-1.1f, 1.1f, r / 8f) - Mathf.PI / 2;
                for (float t = 0; t < 1; t += .02f) Blend((int)(80 + Mathf.Cos(ang) * t * 22 + Mathf.Sin(t * 9 + r) * 2), (int)(30 + Mathf.Sin(ang) * t * 22), new Color(Root.r, Root.g, Root.b, .9f));
            }
            for (int y = 28; y < 62; y++) for (int x = 74; x < 87; x++) Blend(x, y, Color.Lerp(LeafDark, new Color(.35f, .5f, .2f), (x - 74) / 13f));
            // Leaves: serrated lances fanning out of the bundle.
            const int leaves = 9;
            for (int l = 0; l < leaves; l++)
            {
                float ang = Mathf.Lerp(-.62f, .62f, l / (float)(leaves - 1)) + Mathf.PI / 2, len = 78 + (l % 3) * 9 - Mathf.Abs(l - 4) * 4;
                var dir = new Vector2(Mathf.Cos(ang), Mathf.Sin(ang)); var side = new Vector2(-dir.y, dir.x);
                for (float t = 0; t <= 1; t += .004f)
                {
                    float width = Mathf.Sin(Mathf.PI * Mathf.Pow(t, .8f)) * 8f * (1 + .25f * Mathf.Sin(t * 60));   // serrated edge
                    for (float w = -width; w <= width; w += .5f)
                    {
                        var p = new Vector2(80, 60) + dir * (t * len) + side * w;
                        float edge = Mathf.Abs(w) / Mathf.Max(width, .01f);
                        var c = Color.Lerp(LeafDark, LeafLight, t * .8f + (w > 0 ? .15f : 0));
                        if (grade == "low") c = Color.Lerp(c, Yellow, Mathf.Clamp01(edge * 1.2f - .2f + t * .4f));
                        if (grade == "top" && t > .82f) c = Color.Lerp(c, Glow, (t - .82f) / .18f);
                        Blend((int)p.x, (int)p.y, c);
                    }
                }
                if (grade == "low" && l % 2 == 0)   // insect holes
                {
                    var hole = new Vector2(80, 60) + dir * (len * (.45f + .1f * (l % 3))); int r = 3 + rng.Next(2);
                    for (int y = -r; y <= r; y++) for (int x = -r; x <= r; x++) if (x * x + y * y <= r * r)
                    { int i = ((int)hole.y + y) * n + (int)hole.x + x; if (i >= 0 && i < px.Length) px[i] = Color.clear; }
                }
                if (grade == "top")   // soft halo at the tips
                {
                    var tip = new Vector2(80, 60) + dir * len;
                    for (int y = -10; y <= 10; y++) for (int x = -10; x <= 10; x++)
                    { float d = Mathf.Sqrt(x * x + y * y) / 10f; if (d < 1) Blend((int)tip.x + x, (int)tip.y + y, new Color(Glow.r, Glow.g, Glow.b, .35f * (1 - d) * (1 - d))); }
                }
            }
            return cache["herb-" + grade] = Make(px, n);
        }

        /// Round woven sieve seen from above: split-bamboo checker, darker rim, one mended patch on the rim.
        public static Sprite Sieve()
        {
            if (cache.TryGetValue("sieve", out var s)) return s;
            const int n = 256; var px = new Color[n * n];
            for (int y = 0; y < n; y++) for (int x = 0; x < n; x++)
            {
                float dx = x - n / 2f + .5f, dy = y - n / 2f + .5f, d = Mathf.Sqrt(dx * dx + dy * dy) / (n / 2f);
                if (d > 1) continue;
                bool weave = ((x / 10) + (y / 10)) % 2 == 0;
                var c = weave ? new Color(.8f, .68f, .45f) : new Color(.72f, .6f, .38f);
                c *= 1 - .08f * Mathf.PerlinNoise(x * .05f, y * .05f);
                if (d > .9f) c = Color.Lerp(new Color(.52f, .4f, .24f), new Color(.62f, .5f, .3f), Mathf.Sin(Mathf.Atan2(dy, dx) * 40) * .5f + .5f);
                if (d > .9f && dx < -n * .3f && dy > n * .2f) c = new Color(.48f, .44f, .38f);   // mended rim
                c.a = Mathf.Clamp01((1 - d) * 60);
                px[y * n + x] = c;
            }
            return cache["sieve"] = Make(px, n);
        }

        /// Square-holed bronze coin for the result line.
        public static Sprite Coin()
        {
            if (cache.TryGetValue("coin", out var s)) return s;
            const int n = 64; var px = new Color[n * n];
            for (int y = 0; y < n; y++) for (int x = 0; x < n; x++)
            {
                float dx = x - 31.5f, dy = y - 31.5f, d = Mathf.Sqrt(dx * dx + dy * dy) / 31.5f;
                if (d > 1 || (Mathf.Abs(dx) < 7 && Mathf.Abs(dy) < 7)) continue;
                var c = Color.Lerp(new Color(.72f, .55f, .26f), new Color(.42f, .5f, .36f), Mathf.PerlinNoise(x * .15f, y * .15f) * .6f);
                if (d > .86f || (Mathf.Abs(dx) < 10 && Mathf.Abs(dy) < 10)) c *= .8f;
                c.a = 1; px[y * n + x] = c;
            }
            return cache["coin"] = Make(px, n);
        }

        /// White anti-aliased ring for the root timer (tinted and radially filled by the Image).
        public static Sprite Ring()
        {
            if (cache.TryGetValue("ring", out var s)) return s;
            const int n = 128; var px = new Color[n * n];
            for (int y = 0; y < n; y++) for (int x = 0; x < n; x++)
            {
                float d = Mathf.Sqrt((x - 63.5f) * (x - 63.5f) + (y - 63.5f) * (y - 63.5f));
                float a = Mathf.Clamp01(Mathf.Min(63.5f - d, d - 46f) + .5f);
                px[y * n + x] = new Color(1, 1, 1, a);
            }
            return cache["ring"] = Make(px, n);
        }

        static Sprite Make(Color[] px, int n)
        {
            var t = new Texture2D(n, n, TextureFormat.RGBA32, false) { wrapMode = TextureWrapMode.Clamp, filterMode = FilterMode.Bilinear };
            t.SetPixels(px); t.Apply();
            return Sprite.Create(t, new Rect(0, 0, n, n), new Vector2(.5f, .5f), 100);
        }
    }
}
