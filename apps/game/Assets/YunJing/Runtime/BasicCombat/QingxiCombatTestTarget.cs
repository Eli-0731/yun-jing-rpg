using UnityEngine;

namespace YunJing.BasicCombat
{
    /// <summary>
    /// Feel-test target for the basic combat scene only: takes hits, flashes white, slides back by the knockback, wobbles, and can
    /// play its legacy hit clip. With <see cref="strikesBack"/> (the A12 vine dummy) it winds up and swipes the player on a timer so
    /// the dodge i-frames can be tested. It does not touch the rabbit or boar encounter rules.
    /// </summary>
    public sealed class QingxiCombatTestTarget : MonoBehaviour, ICombatTarget
    {
        public string id = "target";
        public float radius = .35f;
        public float maxHp = 120;
        public bool canSlide = true;          // posts stay planted; animals slide back
        public Transform wobble;              // pivot that tilts on hit (posts)
        public Animation legacy;              // optional: rabbit / boar clips
        public string hitClip, idleClip;
        [Header("Strikes back (A12 vine dummy)")]
        public bool strikesBack;
        public float strikeEvery = 3.2f, telegraph = .55f, strikeReach = 2.4f, strikePush = .9f;

        float hp, flash, telegraphT = -1, nextStrike;
        Vector3 tilt, tiltVel, slideVel, home;
        Renderer[] renderers;
        MaterialPropertyBlock mpb;
        static readonly int EmissionColor = Shader.PropertyToID("_EmissionColor"), BaseColor = Shader.PropertyToID("_BaseColor");
        public float Hp => hp;
        public int HitsTaken { get; private set; }
        public int StrikesLanded { get; private set; }
        public int StrikesDodged { get; private set; }
        /// <summary>0..1 while the vine dummy winds up its swipe, -1 otherwise.</summary>
        public float TelegraphProgress => telegraphT < 0 ? -1 : telegraphT / telegraph;

        public string CombatId => id;
        public Vector3 CombatPosition => transform.position;
        public float CombatRadius => radius;
        public bool CombatAlive => true;      // feel test: never dies, resets its bar instead

        void Awake()
        {
            hp = maxHp; home = transform.position;
            renderers = GetComponentsInChildren<Renderer>();
            mpb = new MaterialPropertyBlock();
            nextStrike = Time.time + strikeEvery;
        }

        void OnEnable() => CombatTargets.Add(this);
        void OnDisable() => CombatTargets.Remove(this);

        public void TakeCombatHit(CombatHit hit)
        {
            HitsTaken++;
            hp -= hit.damage;
            if (hp <= 0) hp = maxHp;
            flash = 1;
            var axis = Vector3.Cross(Vector3.up, hit.direction);
            tiltVel += axis * (hit.heavy ? 320 : 170);
            if (canSlide && hit.knockback > 0) slideVel += hit.direction * hit.knockback * 6f;
            if (legacy != null && !string.IsNullOrEmpty(hitClip) && legacy[hitClip] != null)
            {
                legacy.Stop(); legacy.Play(hitClip);
                if (!string.IsNullOrEmpty(idleClip) && legacy[idleClip] != null) legacy.PlayQueued(idleClip);
            }
            if (strikesBack && telegraphT >= 0 && hit.heavy) telegraphT = -1;   // a heavy staggers the swipe
        }

        void Update()
        {
            float dt = Time.deltaTime;
            tiltVel += (-tilt * 200f - tiltVel * 10f) * dt;
            tilt += tiltVel * dt;
            if (wobble != null) wobble.localRotation = Quaternion.Euler(tilt);
            if (slideVel.sqrMagnitude > 1e-4)
            {
                transform.position += slideVel * dt;
                slideVel = Vector3.MoveTowards(slideVel, Vector3.zero, dt * 18f);
            }
            else if ((transform.position - home).sqrMagnitude > .0004f)
                transform.position = Vector3.MoveTowards(transform.position, home, dt * .6f);   // walk back to the mark between rounds
            flash = Mathf.MoveTowards(flash, 0, dt / .12f);
            if (strikesBack) StrikeLoop();
            float glow = Mathf.Max(flash, telegraphT >= 0 ? .35f + .35f * Mathf.Sin(Time.time * 30) : 0);
            foreach (var r in renderers)
            {
                if (r == null) continue;
                r.GetPropertyBlock(mpb);
                var c = telegraphT >= 0 && flash < .5f ? new Color(1f, .45f, .2f) : Color.white;
                mpb.SetColor(EmissionColor, c * glow * 1.6f);
                r.SetPropertyBlock(mpb);
                foreach (var m in r.sharedMaterials) if (m != null && glow > 0) m.EnableKeyword("_EMISSION");
            }
        }

        void StrikeLoop()
        {
            var player = QingxiBasicCombat.Current;
            if (player == null) return;
            Vector3 to = player.transform.position - transform.position; to.y = 0;
            if (telegraphT < 0)
            {
                if (Time.time >= nextStrike && to.magnitude < strikeReach + 1.2f) telegraphT = 0;
                return;
            }
            telegraphT += Time.deltaTime;
            tilt = Vector3.Lerp(tilt, -Vector3.Cross(Vector3.up, to.normalized) * 14, Time.deltaTime * 8);   // lean back before the swipe
            if (telegraphT < telegraph) return;
            telegraphT = -1;
            nextStrike = Time.time + strikeEvery;
            tiltVel += Vector3.Cross(Vector3.up, to.normalized) * 420;
            if (to.magnitude > strikeReach) return;
            if (player.ReceiveStrike(id, to.normalized * strikePush)) StrikesLanded++; else StrikesDodged++;
        }
    }
}
