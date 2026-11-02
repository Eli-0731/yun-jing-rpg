using UnityEngine;

namespace YunJing
{
    // The encounter's simple feedback: the charge line on the ground, dark mist rising off the boar, falling pine needles,
    // the camera shake and the placeholder sounds. Everything is made in code from one material
    // (Resources/QingxiZhuoBoar/ZhuoFx) so the core team's scene needs no setup. No audio files.
    public sealed class QingxiZhuoBoarFx : MonoBehaviour
    {
        const int LinePoints = 10;
        static readonly Color LineSoft = new Color(.72f, .28f, .42f, .16f), LineFixed = new Color(.86f, .3f, .3f, .34f),
            Mist = new Color(.17f, .09f, .24f, .78f);
        static Texture2D softTex, lineTex;
        static AudioClip breath;

        LineRenderer line;
        ParticleSystem mist, needles;
        QingxiTrainingSfx sfx;
        AudioSource shots;
        Material fx;
        float shakeUntil, shakeStrength;

        void Awake()
        {
            fx = Resources.Load<Material>("QingxiZhuoBoar/ZhuoFx");
            if (fx == null) { Debug.LogWarning("Resources/QingxiZhuoBoar/ZhuoFx missing"); return; }
            MakeTextures();
            MakeLine();
            mist = Particles("ZhuoMist", 240);
            var m = mist.main;
            m.startLifetime = new ParticleSystem.MinMaxCurve(1.1f, 2f); m.startSpeed = new ParticleSystem.MinMaxCurve(.25f, .6f);
            m.startSize = new ParticleSystem.MinMaxCurve(.18f, .42f); m.startColor = Mist; m.gravityModifier = -.05f;
            m.startRotation = new ParticleSystem.MinMaxCurve(0, 6.28f);
            var shape = mist.shape; shape.enabled = true; shape.shapeType = ParticleSystemShapeType.Box; shape.scale = new Vector3(.5f, .5f, 1.1f);
            var fade = mist.colorOverLifetime; fade.enabled = true; fade.color = Fade(Color.white);
            var grow = mist.sizeOverLifetime; grow.enabled = true; grow.size = new ParticleSystem.MinMaxCurve(1, AnimationCurve.Linear(0, .6f, 1, 1.5f));
            needles = Particles("PineNeedles", 120);
            var n = needles.main;
            n.startLifetime = new ParticleSystem.MinMaxCurve(1.2f, 2.4f); n.startSpeed = new ParticleSystem.MinMaxCurve(.1f, .7f);
            n.startSize = new ParticleSystem.MinMaxCurve(.03f, .07f); n.gravityModifier = .22f;
            var nShape = needles.shape; nShape.enabled = true; nShape.shapeType = ParticleSystemShapeType.Sphere; nShape.radius = 1.1f;
            var nFade = needles.colorOverLifetime; nFade.enabled = true; nFade.color = Fade(Color.white);
            sfx = gameObject.AddComponent<QingxiTrainingSfx>();
            shots = gameObject.AddComponent<AudioSource>(); shots.playOnAwake = false; shots.spatialBlend = 0;
            if (breath == null) breath = MakeBreath();
        }

        static Gradient Fade(Color c)
        {
            var g = new Gradient();
            g.SetKeys(new[] { new GradientColorKey(c, 0), new GradientColorKey(c, 1) }, new[] { new GradientAlphaKey(0, 0), new GradientAlphaKey(1, .18f), new GradientAlphaKey(0, 1) });
            return g;
        }

        ParticleSystem Particles(string name, int max)
        {
            var go = new GameObject(name); go.transform.SetParent(transform, false);
            var p = go.AddComponent<ParticleSystem>();
            p.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);
            var m = p.main; m.loop = true; m.playOnAwake = false; m.maxParticles = max; m.simulationSpace = ParticleSystemSimulationSpace.World;
            var e = p.emission; e.rateOverTime = 0;
            var r = go.GetComponent<ParticleSystemRenderer>();
            r.sharedMaterial = fx;
            r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off; r.receiveShadows = false;
            var block = new MaterialPropertyBlock(); block.SetTexture("_BaseMap", softTex); r.SetPropertyBlock(block);
            p.Play();
            return p;
        }

        void MakeLine()
        {
            var go = new GameObject("ChargeLine"); go.transform.SetParent(transform, false);
            go.transform.rotation = Quaternion.Euler(90, 0, 0);    // lie flat: the line's face looks along the transform's z
            line = go.AddComponent<LineRenderer>();
            line.useWorldSpace = true; line.alignment = LineAlignment.TransformZ; line.positionCount = LinePoints;
            line.textureMode = LineTextureMode.Stretch; line.numCapVertices = 0;
            line.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off; line.receiveShadows = false;
            line.sharedMaterial = fx;
            var block = new MaterialPropertyBlock(); block.SetTexture("_BaseMap", lineTex); line.SetPropertyBlock(block);
            line.enabled = false;
        }

        // The line drapes over the ground; width and direction come from the rules. Pale while it can still turn, stronger once fixed.
        public void ShowLine(Vector3 from, Vector3 dir, float length, float width, bool isFixed, System.Func<Vector3, float> ground)
        {
            if (line == null) return;
            line.enabled = true;
            line.widthMultiplier = width;
            for (int i = 0; i < LinePoints; i++)
            {
                var p = from + dir * (length * i / (LinePoints - 1));
                p.y = ground(p) + .04f;
                line.SetPosition(i, p);
            }
            var c = isFixed ? LineFixed : Color.Lerp(LineSoft, LineFixed, .25f + .25f * Mathf.Sin(Time.time * 9));
            line.startColor = c; line.endColor = new Color(c.r, c.g, c.b, c.a * .55f);
        }

        public void HideLine() { if (line != null) line.enabled = false; }

        // Wisps while it is still sick; thick while being cleansed.
        public void MistAt(Vector3 at, Quaternion rotation, float rate)
        {
            if (mist == null) return;
            mist.transform.SetPositionAndRotation(at, rotation);
            var e = mist.emission; e.rateOverTime = rate;
        }

        public void MistBurst(int count) { if (mist != null) mist.Emit(count); }

        public void Needles(Vector3 treeBase, Color colour)
        {
            if (needles == null) return;
            needles.transform.position = treeBase + Vector3.up * 3.2f;
            var m = needles.main; m.startColor = colour;
            needles.Emit(70);
        }

        public void Shake(float seconds, float strength) { shakeUntil = Time.time + seconds; shakeStrength = strength; }

        public void Thud() { if (sfx != null) sfx.Thud(); }
        public void Clack() { if (sfx != null) sfx.Clack(); }
        public void Breath() { if (shots != null && breath != null) shots.PlayOneShot(breath, .7f); }

        // After QingxiFirstPerson placed the camera this frame.
        void LateUpdate()
        {
            if (Time.time >= shakeUntil || Camera.main == null) return;
            float k = (shakeUntil - Time.time) * shakeStrength * 6;
            var cam = Camera.main.transform;
            cam.position += cam.right * (Mathf.PerlinNoise(Time.time * 41, 1) - .5f) * k + cam.up * (Mathf.PerlinNoise(2, Time.time * 47) - .5f) * k;
        }

        static void MakeTextures()
        {
            if (softTex != null) return;
            const int S = 64;
            softTex = new Texture2D(S, S, TextureFormat.RGBA32, false) { wrapMode = TextureWrapMode.Clamp, name = "ZhuoSoft" };
            lineTex = new Texture2D(8, S, TextureFormat.RGBA32, false) { wrapMode = TextureWrapMode.Clamp, name = "ZhuoLine" };
            for (int y = 0; y < S; y++)
                for (int x = 0; x < S; x++)
                {
                    float dx = (x + .5f) / S * 2 - 1, dy = (y + .5f) / S * 2 - 1, r = Mathf.Sqrt(dx * dx + dy * dy);
                    float n = Mathf.PerlinNoise(x * .14f, y * .14f);
                    softTex.SetPixel(x, y, new Color(1, 1, 1, Mathf.SmoothStep(0, 1, 1 - r) * (.55f + .45f * n)));
                }
            for (int y = 0; y < S; y++)
                for (int x = 0; x < 8; x++)
                {
                    // Across the width (y): soft edges and a brighter rim so the 1.2 m reads as a lane, not a smear.
                    float v = Mathf.Abs((y + .5f) / S * 2 - 1);
                    float a = Mathf.SmoothStep(1, 0, Mathf.InverseLerp(.9f, 1, v)) * (.55f + .45f * Mathf.SmoothStep(.7f, .9f, v));
                    lineTex.SetPixel(x, y, new Color(1, 1, 1, a));
                }
            softTex.Apply(); lineTex.Apply();
        }

        // Placeholder for the soft "hoo" when the dark qi leaves: filtered noise under a slow swell.
        static AudioClip MakeBreath()
        {
            const int Rate = 44100; int n = Rate * 9 / 10;
            var data = new float[n];
            var rnd = new System.Random(3);
            float low = 0;
            for (int i = 0; i < n; i++)
            {
                float t = i / (float)n, env = Mathf.Sin(Mathf.Clamp01(t * 1.1f) * Mathf.PI);
                low += ((float)rnd.NextDouble() * 2 - 1 - low) * Mathf.Lerp(.11f, .03f, t);
                data[i] = low * env * env * 1.3f;
            }
            var clip = AudioClip.Create("ZhuoBreath", n, 1, Rate, false);
            clip.SetData(data, 0);
            return clip;
        }
    }
}
