using System.Collections.Generic;
using UnityEngine;

namespace YunJing
{
    // Johnnnny0823's synthesized training-yard sounds (tools/training-yard-demo/audio.mjs), rendered once into
    // AudioClips so they also play in the browser build: wood clack for a clean block, padded thud when hit,
    // rhythm tick, clear chime, and a breath drone whose brightness follows the player's qi. No audio files.
    public sealed class QingxiTrainingSfx : MonoBehaviour
    {
        const int Rate = 44100;
        const float Master = .55f;
        static AudioClip clack, thud, tickLow, tickHigh, airDark, airBright, tone;
        static readonly Dictionary<int, AudioClip> chimes = new Dictionary<int, AudioClip>();

        AudioSource shots, dark, bright, hum;
        float qi, sync, level;
        bool breathing;

        void Awake()
        {
            shots = Source(false);
            dark = Source(true); bright = Source(true); hum = Source(true);
            if (clack == null) Build();
            dark.clip = airDark; bright.clip = airBright; hum.clip = tone;
        }

        AudioSource Source(bool loop)
        {
            var s = gameObject.AddComponent<AudioSource>();
            s.playOnAwake = false; s.loop = loop; s.spatialBlend = 0; s.volume = 0;
            return s;
        }

        public void Clack(float strength = 1) => shots.PlayOneShot(clack, Master * strength);
        public void Thud() => shots.PlayOneShot(thud, Master);
        public void Tick(bool high) => shots.PlayOneShot(high ? tickHigh : tickLow, Master);

        public void Chime(float pitch = 1)
        {
            int key = Mathf.RoundToInt(pitch * 100);
            if (!chimes.TryGetValue(key, out var clip)) chimes[key] = clip = Render("chime", 1.2f, t =>
                Decay(t, .004f, .22f, 1.1f) * Sin(880 * pitch, t) + Decay(t, .004f, .12f, 1.1f) * Sin(1320 * pitch, t) + Decay(t, .004f, .06f, 1.1f) * Sin(1760 * pitch, t));
            shots.PlayOneShot(clip, Master);
        }

        public void BreathStart()
        {
            if (breathing) return;
            breathing = true; level = 0;
            foreach (var s in new[] { dark, bright, hum }) { s.volume = 0; s.Play(); }
        }

        public void BreathSet(float qiValue, float syncValue) { qi = qiValue; sync = syncValue; }

        public void BreathStop() => breathing = false;

        void Update()
        {
            // Smooth like setTargetAtTime in the web version; fade out after BreathStop.
            level = Mathf.MoveTowards(level, breathing ? 1 : 0, Time.unscaledDeltaTime * 4);
            float air = (.05f + qi * .16f) * level * Master * 2.2f;
            dark.volume = Mathf.Lerp(dark.volume, air * (1 - qi), Time.unscaledDeltaTime * 10);
            bright.volume = Mathf.Lerp(bright.volume, air * qi, Time.unscaledDeltaTime * 10);
            hum.volume = Mathf.Lerp(hum.volume, (.02f + sync * .06f) * level * Master * 2.2f, Time.unscaledDeltaTime * 5);
            hum.pitch = Mathf.Lerp(hum.pitch, (98 + qi * 49) / 110f, Time.unscaledDeltaTime * 5);
            if (!breathing && level <= 0 && dark.isPlaying) { dark.Stop(); bright.Stop(); hum.Stop(); }
        }

        // ------------------------------------------------------------------ synthesis
        static float Sin(float f, float t) => Mathf.Sin(2 * Mathf.PI * f * t);

        // Linear attack to the peak, then an exponential fall to -80 dB over the release (the web version's
        // exponentialRampToValueAtTime from 0.0001).
        static float Decay(float t, float attack, float peak, float release)
        {
            if (t < attack) return peak * t / attack;
            float u = (t - attack) / release;
            return u >= 1 ? 0 : peak * Mathf.Pow(.0001f / peak, u);
        }

        static AudioClip Render(string name, float seconds, System.Func<float, float> sample)
        {
            var data = new float[Mathf.CeilToInt(seconds * Rate)];
            for (int i = 0; i < data.Length; i++) data[i] = Mathf.Clamp(sample(i / (float)Rate), -1, 1);
            var clip = AudioClip.Create("QingxiTraining_" + name, data.Length, 1, Rate, false);
            clip.SetData(data, 0);
            return clip;
        }

        // White noise through a one-pole low-pass at the given cut-off.
        static float[] Noise(int length, float cutoff, int seed)
        {
            var random = new System.Random(seed);
            float a = 1 - Mathf.Exp(-2 * Mathf.PI * cutoff / Rate), y = 0;
            var data = new float[length];
            for (int i = 0; i < length; i++) { y += a * ((float)random.NextDouble() * 2 - 1 - y); data[i] = y; }
            return data;
        }

        static void Build()
        {
            // Band-passed noise (difference of two low-passes around 1.8 kHz) plus a falling 220→90 Hz knock.
            var hi = Noise(Rate / 6, 3200, 1); var lo = Noise(Rate / 6, 900, 1);
            clack = Render("clack", .15f, t =>
            {
                int i = Mathf.Min(hi.Length - 1, (int)(t * Rate));
                float knock = 220 * Mathf.Pow(90f / 220, Mathf.Min(1, t / .1f));
                return Decay(t, .002f, .9f, .08f) * (hi[i] - lo[i]) * 3f + Decay(t, .002f, .5f, .12f) * Mathf.Sin(2 * Mathf.PI * knock * t);
            });
            thud = Render("thud", .3f, t => Decay(t, .004f, .8f, .22f) * Mathf.Sin(2 * Mathf.PI * (120 * Mathf.Pow(45f / 120, Mathf.Min(1, t / .2f))) * t));
            float Triangle(float f, float t) { float p = f * t % 1; return 4 * Mathf.Abs(p - .5f) - 1; }
            tickLow = Render("tick", .08f, t => Decay(t, .002f, .18f, .05f) * Triangle(990, t));
            tickHigh = Render("tick_high", .08f, t => Decay(t, .002f, .18f, .05f) * Triangle(1320, t));
            // Breath loops: dark (~300 Hz) and bright (~1.6 kHz) air, crossfaded by qi, and a low hum.
            var darkAir = Noise(Rate * 2, 300, 7); var brightAir = Noise(Rate * 2, 1600, 9);
            airDark = Render("air_dark", 2, t => darkAir[Mathf.Min(darkAir.Length - 1, (int)(t * Rate))] * 4f);
            airBright = Render("air_bright", 2, t => brightAir[Mathf.Min(brightAir.Length - 1, (int)(t * Rate))] * 1.6f);
            tone = Render("hum", 1, t => Sin(110, t) * .8f);   // 110 whole cycles: loops without a click
        }
    }
}
