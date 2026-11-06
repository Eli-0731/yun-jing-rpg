using System;
using System.IO;
using UnityEngine;

namespace YunJing.CreekRepair
{
    // Every sound of the silt work, made from numbers so nothing is licensed or downloaded. The chant is a placeholder: a few
    // formant-synthesised voices calling 嘿 and 喲 over a wood block, one loop per chant cycle; a real recording can replace it.
    public static class CreekRepairSound
    {
        public const int Rate = 44100;

        public static AudioClip Clip(string name, float[] samples)
        {
            var clip = AudioClip.Create(name, samples.Length, 1, Rate, false); clip.SetData(samples, 0); return clip;
        }

        struct Formants { public float f1, f2, f3; public Formants(float a, float b, float c) { f1 = a; f2 = b; f3 = c; } }

        /// One voice calling one syllable: a rough glottal buzz through three resonances that glide from `from` to `to`.
        static void Syllable(float[] buffer, double start, double seconds, float pitchFrom, float pitchTo, Formants from, Formants to, float breath, System.Random rand, float gain)
        {
            int first = (int)(start * Rate), n = (int)(seconds * Rate);
            double phase = rand.NextDouble(), low = 0; var y = new double[6];
            float wobble = (float)rand.NextDouble() * 6f;
            for (int i = 0; i < n; i++)
            {
                float k = (float)i / n, time = (float)i / Rate;
                float pitch = Mathf.Lerp(pitchFrom, pitchTo, k) * (1 + .012f * Mathf.Sin(wobble + time * 34f));
                phase += pitch / Rate; if (phase >= 1) phase -= 1;
                low += (2 * phase - 1 - low) * .11;
                float noise = (float)rand.NextDouble() * 2 - 1;
                double source = low * Mathf.SmoothStep(0, 1, time / .05f) + noise * breath * Mathf.Clamp01(1 - time / .07f) + noise * .012f;
                double outp = 0;
                float[] freq = { Mathf.Lerp(from.f1, to.f1, k), Mathf.Lerp(from.f2, to.f2, k), Mathf.Lerp(from.f3, to.f3, k) }, level = { 1f, .55f, .28f }, band = { 90, 120, 170 };
                for (int f = 0; f < 3; f++)
                {
                    double r = Math.Exp(-Math.PI * band[f] / Rate), a1 = 2 * r * Math.Cos(2 * Math.PI * freq[f] / Rate), a2 = -r * r;
                    double v = a1 * y[f * 2] + a2 * y[f * 2 + 1] + (1 - r) * source;
                    y[f * 2 + 1] = y[f * 2]; y[f * 2] = v; outp += v * level[f];
                }
                float envelope = Mathf.SmoothStep(0, 1, k / .07f) * Mathf.SmoothStep(0, 1, (1 - k) / .28f);
                int at = first + i; if (at < buffer.Length) buffer[at] += (float)outp * envelope * gain;
            }
        }

        static void Block(float[] buffer, double start, float gain)
        {
            int first = (int)(start * Rate);
            for (int i = 0; i < Rate / 8 && first + i < buffer.Length; i++)
            {
                float t = (float)i / Rate;
                buffer[first + i] += gain * Mathf.Exp(-t * 38) * (Mathf.Sin(t * 1150 * Mathf.PI * 2) * .7f + Mathf.Sin(t * 1720 * Mathf.PI * 2) * .3f);
            }
        }

        static float[] Normal(float[] samples, float peak)
        {
            float top = 0.0001f; foreach (var s in samples) top = Mathf.Max(top, Mathf.Abs(s));
            for (int i = 0; i < samples.Length; i++) samples[i] *= peak / top;
            return samples;
        }

        /// The sh of 咻: breath through the teeth.
        static void Hiss(float[] buffer, double start, double seconds, System.Random rand, float gain)
        {
            int first = (int)(start * Rate), n = (int)(seconds * Rate); float low = 0;
            for (int i = 0; i < n && first + i < buffer.Length; i++)
            {
                float k = (float)i / n, noise = (float)rand.NextDouble() * 2 - 1; low += (noise - low) * .45f;
                buffer[first + i] += (noise - low) * gain * Mathf.Sin(k * Mathf.PI);
            }
        }

        /// A low drum under a wooden knock, to carry the beat.
        static void Beat(float[] buffer, double start, float drum, float wood)
        {
            int first = (int)(start * Rate);
            for (int i = 0; i < Rate * 2 / 5 && first + i < buffer.Length; i++)
            {
                float t = (float)i / Rate;
                buffer[first + i] += drum * Mathf.Exp(-t * 9) * Mathf.Sin(t * Mathf.Lerp(88, 64, Mathf.Clamp01(t * 8)) * Mathf.PI * 2)
                    + wood * Mathf.Exp(-t * 52) * (Mathf.Sin(t * 760 * Mathf.PI * 2) * .7f + Mathf.Sin(t * 1240 * Mathf.PI * 2) * .3f);
            }
        }

        /// Open air: a couple of soft echoes that wrap round, so the loop has no seam.
        static float[] Room(float[] dry)
        {
            var wet = (float[])dry.Clone(); int n = dry.Length;
            foreach (var (delay, gain) in new[] { (.083f, .22f), (.131f, .17f), (.197f, .11f), (.281f, .07f) })
            {
                int d = (int)(delay * Rate); float low = 0;
                for (int i = 0; i < n; i++) { low += (dry[i] - low) * .35f; wet[(i + d) % n] += low * gain; }
            }
            return wet;
        }

        /// One loop: 嘿 at the top of the cycle, 咻 at yoAt, sung by a loose group. A bigger party is more voices, not a different tune.
        public static float[] Chant(float cycle, float yoAt, int partySize)
        {
            var buffer = new float[Mathf.RoundToInt(cycle * Rate)]; var rand = new System.Random(1701);
            int voices = 5 + 2 * (partySize - 1);
            for (int v = 0; v < voices; v++)
            {
                float tune = 1 + (v - (voices - 1) / 2f) * .016f, late = (float)rand.NextDouble() * .045f, g = .75f + (float)rand.NextDouble() * .25f;
                // 嘿: short and low, 咻: answering a fourth up, falling away
                Syllable(buffer, .02 + late, .3, 132 * tune, 146 * tune, new Formants(560, 1750, 2500), new Formants(380, 2150, 2750), .5f, rand, g);
                Hiss(buffer, yoAt - .07 + late, .1, rand, .035f * g);
                Syllable(buffer, yoAt + .02 + late, .62, 178 * tune, 150 * tune, new Formants(300, 2200, 2800), new Formants(360, 820, 2450), .08f, rand, g);
            }
            Normal(buffer, .55f);
            Beat(buffer, .0, .34f, .1f); Beat(buffer, yoAt, .46f, .16f);
            return Normal(Room(buffer), .8f);
        }

        /// One spadeful, by kind of mud: the edge cutting in, the weight of it coming away, then bits landing.
        public static float[] Dig(string kind, int take)
        {
            var buffer = new float[Rate * 7 / 10]; var rand = new System.Random(211 + take * 37 + kind.Length * 1009);
            float pitch = 1 + (take - 1) * .09f; bool weed = kind == "weed", hard = kind == "hard";
            float low = 0, mid = 0, high = 0;
            for (int i = 0; i < buffer.Length; i++)
            {
                float t = (float)i / Rate, noise = (float)rand.NextDouble() * 2 - 1;
                low += (noise - low) * .035f * pitch; mid += (noise - mid) * .16f * pitch; high = noise - mid;
                if (weed)
                {
                    // fibres tearing: a rough rip that thins out
                    float grain = Mathf.Abs(Mathf.Sin(t * 210 * pitch + Mathf.Sin(t * 37) * 4)) > .72f ? 1 : .15f;
                    buffer[i] = (high * .55f + mid * .9f) * grain * Mathf.SmoothStep(0, 1, t / .03f) * Mathf.Exp(-t * 7);
                }
                else
                {
                    float cut = high * (hard ? .5f : .22f) * Mathf.Exp(-t * (hard ? 42 : 60));
                    float body = low * (hard ? 1.5f : 2.6f) * Mathf.SmoothStep(0, 1, t / .012f) * Mathf.Exp(-t * (hard ? 20 : 12));
                    float thump = Mathf.Sin(t * Mathf.Lerp(92, 58, Mathf.Clamp01(t * 6)) * pitch * Mathf.PI * 2) * .5f * Mathf.Exp(-t * 24);
                    float suck = hard ? 0 : mid * .35f * Mathf.Exp(-Mathf.Pow((t - .09f) / .035f, 2));
                    buffer[i] = cut + body + thump + suck;
                }
            }
            // bits landing after it, small and uneven
            for (int c = 0; c < (hard ? 7 : weed ? 2 : 4); c++)
            {
                int at = (int)((.16 + rand.NextDouble() * .38) * Rate); float g = (hard ? .16f : .1f) + (float)rand.NextDouble() * .12f, ring = (hard ? 620 : 240) + (float)rand.NextDouble() * 180;
                for (int i = 0; i < Rate / 22 && at + i < buffer.Length; i++) { float t = (float)i / Rate; buffer[at + i] += g * Mathf.Exp(-t * 95) * Mathf.Sin(t * ring * Mathf.PI * 2); }
            }
            int tail = Rate / 20; for (int i = 0; i < tail; i++) buffer[buffer.Length - 1 - i] *= (float)i / tail;
            return Normal(buffer, .8f);
        }

        /// The blade working its way in while the button is held: a low grit that builds.
        public static float[] Press()
        {
            var buffer = new float[Rate * 3 / 2]; var rand = new System.Random(77); float low = 0, mid = 0;
            for (int i = 0; i < buffer.Length; i++)
            {
                float t = (float)i / Rate, noise = (float)rand.NextDouble() * 2 - 1;
                low += (noise - low) * .03f; mid += (noise - mid) * .2f;
                float grit = .55f + .45f * Mathf.Sin(t * 41 + Mathf.Sin(t * 13) * 3);
                buffer[i] = (low * 1.6f + (noise - mid) * .05f * grit + mid * .12f * grit) * Mathf.SmoothStep(0, 1, t / .08f) * Mathf.Lerp(.5f, 1, Mathf.Clamp01(t / .8f));
            }
            return Normal(buffer, .4f);
        }

        /// The spade going through wet mud.
        public static float[] Thud()
        {
            var buffer = new float[Rate / 3]; var rand = new System.Random(5); float low = 0, wet = 0;
            for (int i = 0; i < buffer.Length; i++)
            {
                float t = (float)i / Rate, noise = (float)rand.NextDouble() * 2 - 1;
                low += (noise - low) * .05f; wet += (noise - wet) * .3f;
                buffer[i] = Mathf.Sin(t * Mathf.Lerp(78, 46, t * 3) * Mathf.PI * 2) * Mathf.Exp(-t * 15) + low * 1.6f * Mathf.Exp(-t * 11) + wet * .22f * Mathf.Exp(-t * 26);
            }
            return Normal(buffer, .8f);
        }

        /// A whole face of mud letting go: a long low rush with clods landing in it.
        public static float[] Slump()
        {
            var buffer = new float[Rate * 3 / 2]; var rand = new System.Random(9); float low = 0;
            for (int i = 0; i < buffer.Length; i++)
            {
                float t = (float)i / Rate, noise = (float)rand.NextDouble() * 2 - 1;
                low += (noise - low) * Mathf.Lerp(.09f, .025f, t / 1.5f);
                buffer[i] = low * 4f * Mathf.SmoothStep(0, 1, t / .06f) * Mathf.Exp(-t * 2.6f) + Mathf.Sin(t * 52 * Mathf.PI * 2) * .9f * Mathf.Exp(-t * 5);
            }
            var thud = Thud();
            for (int c = 0; c < 9; c++)
            {
                int at = (int)((.08 + rand.NextDouble() * .85) * Rate); float g = .25f + (float)rand.NextDouble() * .4f;
                for (int i = 0; i < thud.Length && at + i < buffer.Length; i++) buffer[at + i] += thud[i] * g;
            }
            return Normal(buffer, .92f);
        }

        /// Water running in a shallow channel: a soft rush with a slow swell and a few bubbles. Its ends fade into each other, so it loops.
        public const float WaterSeconds = 4;
        public static float[] Water()
        {
            int n = (int)(WaterSeconds * Rate), fade = Rate / 2; var rand = new System.Random(41); var dry = new float[n + fade];
            float low = 0, band = 0;
            for (int i = 0; i < dry.Length; i++)
            {
                float t = (float)i / Rate, white = (float)rand.NextDouble() * 2 - 1;
                low += (white - low) * .12f; band += (low - band) * .02f;
                dry[i] = (low - band) * (.75f + .25f * Mathf.Sin(t * 1.9f) * Mathf.Sin(t * .7f + 1));
            }
            for (int b = 0; b < 26; b++)
            {
                int at = rand.Next(dry.Length - Rate / 8); float pitch = 380 + (float)rand.NextDouble() * 520, g = .08f + (float)rand.NextDouble() * .12f;
                for (int i = 0; i < Rate / 8; i++) { float t = (float)i / Rate; dry[at + i] += g * Mathf.Exp(-t * 32) * Mathf.Sin(t * (pitch + 900 * t) * Mathf.PI * 2); }
            }
            var buffer = new float[n];
            for (int i = 0; i < n; i++) buffer[i] = dry[i];
            for (int i = 0; i < fade; i++) { float k = (float)i / fade; buffer[i] = dry[i] * k + dry[n + i] * (1 - k); }
            return Normal(buffer, .8f);
        }

        /// A stone of the old channel bed coming clear.
        public static float[] Tick()
        {
            var buffer = new float[Rate / 10];
            for (int i = 0; i < buffer.Length; i++)
            {
                float t = (float)i / Rate;
                buffer[i] = Mathf.Exp(-t * 70) * (Mathf.Sin(t * 1900 * Mathf.PI * 2) * .6f + Mathf.Sin(t * 2950 * Mathf.PI * 2) * .4f);
            }
            return Normal(buffer, .5f);
        }

        public static void Add(float[] mix, float[] sound, double atSeconds, float gain)
        {
            int first = (int)(atSeconds * Rate);
            for (int i = 0; i < sound.Length; i++) { int at = first + i; if (at >= 0 && at < mix.Length) mix[at] += sound[i] * gain; }
        }

        /// 16-bit mono WAV, for putting sound on the test recordings.
        public static void WriteWav(string path, float[] samples)
        {
            using (var w = new BinaryWriter(File.Create(path)))
            {
                w.Write(System.Text.Encoding.ASCII.GetBytes("RIFF")); w.Write(36 + samples.Length * 2); w.Write(System.Text.Encoding.ASCII.GetBytes("WAVEfmt "));
                w.Write(16); w.Write((short)1); w.Write((short)1); w.Write(Rate); w.Write(Rate * 2); w.Write((short)2); w.Write((short)16);
                w.Write(System.Text.Encoding.ASCII.GetBytes("data")); w.Write(samples.Length * 2);
                foreach (var s in samples) w.Write((short)(Mathf.Clamp(s, -1f, 1f) * 32767));
            }
        }
    }
}
