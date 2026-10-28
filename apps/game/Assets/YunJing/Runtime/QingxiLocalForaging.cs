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
        public Transform[] clueNodes;
        public Transform marketEntrance;
        public Transform trainingSpot;
        public QingxiAbcStations abc;
        public float herbRegrowSeconds = 60f;

        readonly Dictionary<Transform, float> harvestedUntil = new Dictionary<Transform, float>();
        readonly HashSet<Transform> observedClues = new HashSet<Transform>();
        public int Herbs { get; private set; }
        public int Rabbits { get; private set; }
        public int PracticeStones { get; private set; }
        public int Trades { get; private set; }
        public int Insights { get; private set; }
        public int PracticePellets { get; private set; }
        public int ObservedClues => observedClues.Count;
        int basicPracticeCount;
        public string LastMessage { get; private set; } = "沿溪探索，按 F 與靈草、山兔或坊市互動";
        public event Action Changed;

        static float Distance(Vector3 a, Vector3 b) =>
            Vector2.Distance(new Vector2(a.x, a.z), new Vector2(b.x, b.z));

        public string Prompt(Vector3 playerPosition)
        {
            var station = abc != null ? abc.Prompt(playerPosition) : null;
            if (station != null) return station;
            foreach (var herb in herbNodes ?? Array.Empty<Transform>())
                if (herb != null && Distance(playerPosition, herb.position) <= 2.4f)
                    return harvestedUntil.TryGetValue(herb, out var until) && Time.time < until
                        ? "靈草正在再生" : "F 採集靈草";
            foreach (var clue in clueNodes ?? Array.Empty<Transform>())
                if (clue != null && Distance(playerPosition, clue.position) <= 2.4f)
                    return observedClues.Contains(clue) ? "已記下這處線索" : "F 觀察此處線索";
            foreach (var rabbit in FindObjectsByType<QingxiRabbit>(FindObjectsSortMode.None))
                if (!rabbit.IsCaught && Distance(playerPosition, rabbit.transform.position) <= 2.2f)
                    return "F 抓取山兔";
            if (marketEntrance != null && Distance(playerPosition, marketEntrance.position) <= 3f)
                return "F 交換材料  ·  E 用兩株靈草煉調息散";
            if (trainingSpot != null && Distance(playerPosition, trainingSpot.position) <= 3f)
                return "F 練習引氣訣  ·  E 服用調息散";
            return "探索線索、採藥、追兔，或回聽風台練氣";
        }

        public bool TryInteract(Vector3 playerPosition, out string message) =>
            TryInteractAt(playerPosition, Time.time, out message);

        // Explicit time permits deterministic Editor checks without changing the system clock.
        public bool TryInteractAt(Vector3 playerPosition, float now, out string message)
        {
            if (abc != null && abc.TryInteract(playerPosition, out message)) return Complete(message, out message);
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

            foreach (var clue in clueNodes ?? Array.Empty<Transform>())
            {
                if (clue == null || Distance(playerPosition, clue.position) > 2.4f) continue;
                if (!observedClues.Add(clue))
                {
                    message = "這處線索已記在旅途手札";
                    return false;
                }
                return Complete("發現新線索；回聽風台可試著參悟", out message);
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
            if (trainingSpot != null && Distance(playerPosition, trainingSpot.position) <= 3f)
            {
                if (basicPracticeCount > observedClues.Count)
                {
                    message = "已參悟目前線索；再去探索，或服用調息散";
                    return false;
                }
                basicPracticeCount++;
                Insights++;
                return Complete("完成一次引氣訣練習，得到一點本機領悟", out message);
            }
            message = "附近沒有可互動的靈草、山兔或坊市";
            return false;
        }

        public bool TrySecondary(Vector3 playerPosition, out string message)
        {
            if (marketEntrance != null && Distance(playerPosition, marketEntrance.position) <= 3f)
            {
                if (Herbs < 2) { message = "煉製調息散需要兩株靈草"; return false; }
                Herbs -= 2;
                PracticePellets++;
                return Complete("煉成一份調息散（本機試玩）", out message);
            }
            if (trainingSpot != null && Distance(playerPosition, trainingSpot.position) <= 3f)
            {
                if (PracticePellets == 0) { message = "沒有調息散；可先練習引氣訣"; return false; }
                PracticePellets--;
                Insights += 2;
                return Complete("服用調息散，獲得兩點本機領悟", out message);
            }
            message = "這裡沒有煉製或服用操作";
            return false;
        }

        // Rehearsal counts survive a visit to the alchemy room (a separate scene) within one run only.
        sealed class Carried { public int herbs, rabbits, stones, trades, insights, pellets, practice; public string[] clues; }
        static Carried carried;

        public void Carry() => carried = new Carried { herbs = Herbs, rabbits = Rabbits, stones = PracticeStones, trades = Trades,
            insights = Insights, pellets = PracticePellets, practice = basicPracticeCount,
            clues = Array.ConvertAll(Array.FindAll(clueNodes ?? Array.Empty<Transform>(), c => c != null && observedClues.Contains(c)), c => c.name) };

        public void RestoreCarried()
        {
            if (carried == null) return;
            Herbs = carried.herbs; Rabbits = carried.rabbits; PracticeStones = carried.stones; Trades = carried.trades;
            Insights = carried.insights; PracticePellets = carried.pellets; basicPracticeCount = carried.practice;
            foreach (var clue in clueNodes ?? Array.Empty<Transform>())
                if (clue != null && Array.IndexOf(carried.clues, clue.name) >= 0) observedClues.Add(clue);
            carried = null;
            Complete("離開丹房，回到青溪街上", out _);
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
