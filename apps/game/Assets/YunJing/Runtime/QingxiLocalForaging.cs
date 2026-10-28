using System;
using System.Collections.Generic;
using QingxiWorld;
using UnityEngine;

namespace YunJing
{
    // A local, disposable play rehearsal. No persistent inventory, currency or API calls.
    public sealed class QingxiLocalForaging : MonoBehaviour
    {
        public Transform[] herbNodes;
        public Transform marketEntrance;
        public float herbRegrowSeconds = 60f;

        readonly Dictionary<Transform, float> harvestedUntil = new Dictionary<Transform, float>();
        public int Herbs { get; private set; }
        public int Rabbits { get; private set; }
        public int PracticeStones { get; private set; }
        public int Trades { get; private set; }
        public string LastMessage { get; private set; } = "沿溪探索，按 F 與靈草、山兔或坊市互動";
        public event Action Changed;

        static float Distance(Vector3 a, Vector3 b) =>
            Vector2.Distance(new Vector2(a.x, a.z), new Vector2(b.x, b.z));

        public string Prompt(Vector3 playerPosition)
        {
            foreach (var herb in herbNodes ?? Array.Empty<Transform>())
                if (herb != null && Distance(playerPosition, herb.position) <= 2.4f)
                    return harvestedUntil.TryGetValue(herb, out var until) && Time.time < until
                        ? "靈草正在再生" : "F 採集靈草";
            foreach (var rabbit in FindObjectsByType<QingxiRabbit>(FindObjectsSortMode.None))
                if (!rabbit.IsCaught && Distance(playerPosition, rabbit.transform.position) <= 2.2f)
                    return "F 抓取山兔";
            if (marketEntrance != null && Distance(playerPosition, marketEntrance.position) <= 3f)
                return Herbs + Rabbits > 0 ? "F 在坊市交換採獵物" : "坊市：先去採草或尋找山兔";
            return "沿溪尋找靈草、山兔與坊市";
        }

        public bool TryInteract(Vector3 playerPosition, out string message) =>
            TryInteractAt(playerPosition, Time.time, out message);

        // Explicit time permits deterministic Editor checks without changing the system clock.
        public bool TryInteractAt(Vector3 playerPosition, float now, out string message)
        {
            foreach (var herb in herbNodes ?? Array.Empty<Transform>())
            {
                if (herb == null || Distance(playerPosition, herb.position) > 2.4f) continue;
                if (harvestedUntil.TryGetValue(herb, out var until) && now < until)
                {
                    message = "這株靈草正在再生";
                    return false;
                }
                harvestedUntil[herb] = now + herbRegrowSeconds;
                Herbs++;
                return Complete("採到一株靈草（本機試玩）", out message);
            }

            foreach (var rabbit in FindObjectsByType<QingxiRabbit>(FindObjectsSortMode.None))
            {
                if (Distance(playerPosition, rabbit.transform.position) > 2.2f ||
                    !rabbit.TryCatch(playerPosition, 2.2f)) continue;
                Rabbits++;
                return Complete("抓到一隻山兔（本機試玩）", out message);
            }

            if (marketEntrance != null && Distance(playerPosition, marketEntrance.position) <= 3f)
            {
                if (Herbs + Rabbits == 0)
                {
                    message = "先帶靈草或山兔回坊市";
                    return false;
                }
                PracticeStones += Herbs * 2 + Rabbits * 3;
                Herbs = 0;
                Rabbits = 0;
                Trades++;
                return Complete("已在坊市交換；練習靈石只在本次試玩有效", out message);
            }
            message = "附近沒有可互動的靈草、山兔或坊市";
            return false;
        }

        bool Complete(string result, out string message)
        {
            LastMessage = result;
            message = result;
            Changed?.Invoke();
            return true;
        }
    }
}
