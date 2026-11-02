using System;
using System.Collections;
using System.IO;
using UnityEngine;
using Rules = YunJing.BasicCombat.QingxiBasicCombatRules;
using FirstPerson = global::QingxiWorld.QingxiFirstPerson;

namespace YunJing.BasicCombat
{
    /// <summary>
    /// Scripted run for the evidence video: launch the test build with <c>-basicCombatDemo</c> (add <c>-capture &lt;folder&gt;</c> to write
    /// 30 fps JPG frames and quit). It feeds the same input struct the devices do, so the recording exercises the real rules,
    /// feedback and targets. Human desktop and phone recordings are still made by hand.
    /// </summary>
    [DefaultExecutionOrder(200)]
    public sealed class QingxiBasicCombatDemo : MonoBehaviour
    {
        public QingxiBasicCombat combat;
        public QingxiCombatTestTarget vine, rabbit, boar;
        Rules.Input next;
        bool attack, dodge, heavy;
        Vector2 move;
        string capture;
        int frame, hits;

        void Awake()
        {
            var args = Environment.GetCommandLineArgs();
            if (Array.IndexOf(args, "-basicCombatDemo") < 0) { enabled = false; return; }
            int ci = Array.IndexOf(args, "-capture");
            if (ci >= 0 && ci + 1 < args.Length) capture = args[ci + 1];
            Application.runInBackground = true;
            QingxiBasicCombat.ScriptedInput = Read;
            QingxiBasicCombat.Hit += (target, attack, damage) => { hits++; Debug.Log($"combat.hit {{ targetId: {target}, attackId: {attack}, damage: {damage} }}"); };
            if (capture != null) { Directory.CreateDirectory(capture); Time.captureFramerate = 30; StartCoroutine(Capture()); }
            StartCoroutine(Script());
        }

        void OnDestroy() { if (QingxiBasicCombat.ScriptedInput == (Func<Rules.Input?>)Read) QingxiBasicCombat.ScriptedInput = null; }

        Rules.Input? Read()
        {
            var t = combat.transform;
            var world = t.right * move.x + t.forward * move.y;
            var i = new Rules.Input { attack = attack, dodge = dodge, heavyHeld = heavy, moveX = world.x, moveZ = world.z };
            attack = dodge = false;
            return i;
        }

        // QingxiTouchControls zeroes FirstPerson.VirtualMove every frame when no touch is seen, so the script walks the controller itself
        void Update()
        {
            if (move.sqrMagnitude < 1e-4 || combat.Busy) return;
            var t = combat.transform;
            var cc = combat.GetComponent<CharacterController>();
            if (cc != null && cc.enabled) cc.Move((t.right * move.x + t.forward * move.y) * 3.2f * Time.deltaTime);
        }

        // recording only: a three-quarter side camera so the strikes and the vine dummy are not hidden behind the player's back
        void LateUpdate()
        {
            if (combat.cam == null) return;
            var p = combat.transform.position; var f = combat.transform.forward; var r = combat.transform.right;
            // stay on the side away from the vine dummy so the post never fills the frame
            float side = Vector3.Dot(vine.transform.position - p, r) > .3f ? -1 : 1;
            var want = p - f * 2.9f + r * side * 2.3f + Vector3.up * 2.3f;
            camPos = camInit ? Vector3.Lerp(camPos, want, 1 - Mathf.Exp(-4 * Time.unscaledDeltaTime)) : want; camInit = true;
            combat.cam.transform.position = camPos + combat.ShakeOffset;
            combat.cam.transform.rotation = Quaternion.LookRotation(p + f * 1.3f + Vector3.up * .95f - camPos);
        }
        Vector3 camPos; bool camInit;

        IEnumerator Wait(float s) { float e = 0; while (e < s) { e += Time.deltaTime; yield return null; } }

        IEnumerator Face(Transform target, float seconds)
        {
            float e = 0;
            while (e < seconds)
            {
                e += Time.deltaTime;
                var to = target.position - combat.transform.position; to.y = 0;
                float want = Mathf.Atan2(to.x, to.z) * Mathf.Rad2Deg, now = combat.transform.eulerAngles.y;
                FirstPerson.VirtualLook = new Vector2(Mathf.DeltaAngle(now, want) * .25f, 0);
                yield return null;
            }
        }

        IEnumerator Approach(Transform target, float stopAt, float maxSeconds)
        {
            float e = 0;
            while (e < maxSeconds)
            {
                var to = target.position - combat.transform.position; to.y = 0;
                if (to.magnitude <= stopAt) break;
                float want = Mathf.Atan2(to.x, to.z) * Mathf.Rad2Deg, now = combat.transform.eulerAngles.y;
                FirstPerson.VirtualLook = new Vector2(Mathf.DeltaAngle(now, want) * .25f, 0);
                move = new Vector2(0, 1);
                e += Time.deltaTime;
                yield return null;
            }
            move = Vector2.zero;
        }

        IEnumerator Chain(float gap1 = .33f, float gap2 = .36f)
        {
            attack = true; yield return Wait(gap1);
            attack = true; yield return Wait(gap2);
            attack = true; yield return Wait(.95f);
        }

        IEnumerator Script()
        {
            yield return Wait(1f);
            // 1. the vine dummy: full chain, then a held heavy
            yield return Approach(vine.transform, 1.6f, 4f);
            yield return Face(vine.transform, .3f);
            yield return Chain();
            heavy = true; yield return Wait(1.0f); heavy = false; yield return Wait(1.0f);
            // 2. the vine dummy swipes back: take one on purpose, then dodge the next one late in its wind-up (i-frames) and punish
            yield return Approach(vine.transform, 1.6f, 2f);
            yield return Face(vine.transform, .2f);
            float guard = 0;
            while (vine.StrikesLanded + vine.StrikesDodged < 1 && guard < 8) { guard += Time.deltaTime; yield return null; }
            yield return Wait(.4f);
            yield return Approach(vine.transform, 1.6f, 2f);
            guard = 0;
            while (vine.TelegraphProgress < .7f && guard < 8) { guard += Time.deltaTime; yield return null; }
            dodge = true; yield return Wait(.45f);
            yield return Approach(vine.transform, 1.6f, 2f);
            yield return Chain();
            // 3. press too early (windup) to show the dropped input, then a correct chain
            attack = true; yield return Wait(.05f); attack = true; yield return Wait(.5f);
            // 4. rabbit and boar: chain into a dodge-cancel, heavy on the boar
            yield return Approach(rabbit.transform, 1.5f, 3f);
            yield return Face(rabbit.transform, .3f);
            attack = true; yield return Wait(.33f); attack = true; yield return Wait(.3f);
            move = new Vector2(-1, -0.3f); dodge = true; yield return Wait(.15f); move = Vector2.zero; yield return Wait(.5f);
            yield return Approach(boar.transform, 1.9f, 4f);
            yield return Face(boar.transform, .3f);
            heavy = true; yield return Wait(1.3f); heavy = false; yield return Wait(1.0f);
            yield return Chain();
            yield return Wait(1f);
            Debug.Log($"BASIC_COMBAT_DEMO_SUMMARY hits vine={vine.HitsTaken} rabbit={rabbit.HitsTaken} boar={boar.HitsTaken} " +
                      $"vineStrikes landed={vine.StrikesLanded} dodged={vine.StrikesDodged} totalHits={hits}");
            if (capture != null) Application.Quit();
        }

        IEnumerator Capture()
        {
            var eof = new WaitForEndOfFrame();
            Texture2D tex = null;
            while (true)
            {
                yield return eof;
                // the project does not ship the ScreenCapture module, so read the back buffer directly
                if (tex == null || tex.width != Screen.width || tex.height != Screen.height) tex = new Texture2D(Screen.width, Screen.height, TextureFormat.RGB24, false);
                tex.ReadPixels(new Rect(0, 0, Screen.width, Screen.height), 0, 0, false);
                tex.Apply(false);
                File.WriteAllBytes(Path.Combine(capture, $"f{frame:D5}.jpg"), tex.EncodeToJPG(90));
                if (++frame > 30 * 60) Application.Quit();
            }
        }
    }
}
