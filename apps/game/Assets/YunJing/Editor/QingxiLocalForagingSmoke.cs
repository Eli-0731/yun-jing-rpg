using System;
using System.Reflection;
using QingxiWorld;
using UnityEngine;

namespace YunJing.Editor
{
    public static class QingxiLocalForagingSmoke
    {
        public static void Verify()
        {
            var root = new GameObject("Local foraging smoke");
            try
            {
                var herb = new GameObject("HerbNode_Smoke").transform;
                herb.SetParent(root.transform);
                herb.position = new Vector3(10000, 0, 10000);
                var market = new GameObject("Entrance_MaterialShop_Smoke").transform;
                market.SetParent(root.transform);
                market.position = new Vector3(10010, 0, 10000);
                var clue = new GameObject("TrailClue_Smoke").transform;
                clue.SetParent(root.transform);
                clue.position = new Vector3(10030, 0, 10000);
                var training = new GameObject("Entrance_ListeningTerrace_Smoke").transform;
                training.SetParent(root.transform);
                training.position = new Vector3(10040, 0, 10000);
                var loop = root.AddComponent<QingxiLocalForaging>();
                loop.herbNodes = new[] { herb };
                loop.clueNodes = new[] { clue };
                loop.marketEntrance = market;
                loop.trainingSpot = training;

                if (!loop.TryInteractAt(herb.position, 0, out _) || loop.Herbs != 1)
                    throw new InvalidOperationException("Local herb harvest did not register.");
                if (loop.TryInteractAt(herb.position, 1, out _) || loop.Herbs != 1)
                    throw new InvalidOperationException("Local herb could be harvested twice before regrowth.");
                if (!loop.TryInteractAt(market.position, 2, out _) || loop.Herbs != 0 ||
                    loop.PracticeStones != 2 || loop.Trades != 1)
                    throw new InvalidOperationException("Local market exchange did not consume the herb exactly once.");
                if (loop.TryInteractAt(market.position, 3, out _) || loop.PracticeStones != 2)
                    throw new InvalidOperationException("Empty local market exchange produced practice stones.");
                if (!loop.TryInteractAt(herb.position, 61, out _) || loop.Herbs != 1)
                    throw new InvalidOperationException("Local herb did not regrow after its cooldown.");
                var rabbitObject = GameObject.CreatePrimitive(PrimitiveType.Sphere);
                rabbitObject.transform.SetParent(root.transform);
                rabbitObject.transform.position = new Vector3(10020, 0, 10000);
                var rabbit = rabbitObject.AddComponent<QingxiRabbit>();
                typeof(QingxiRabbit).GetMethod("Start", BindingFlags.Instance | BindingFlags.NonPublic)
                    ?.Invoke(rabbit, null);
                if (!loop.TryInteractAt(rabbit.transform.position, 62, out _) || loop.Rabbits != 1 || !rabbit.IsCaught)
                    throw new InvalidOperationException("Local rabbit catch did not register.");
                if (loop.TryInteractAt(rabbit.transform.position, 63, out _) || loop.Rabbits != 1)
                    throw new InvalidOperationException("Caught local rabbit was counted twice.");
                if (!loop.TryInteractAt(market.position, 64, out _) || loop.Herbs != 0 ||
                    loop.Rabbits != 0 || loop.PracticeStones != 7 || loop.Trades != 2)
                    throw new InvalidOperationException("Mixed local herb and rabbit exchange was incorrect.");
                if (!loop.TryInteractAt(training.position, 65, out _) || loop.Insights != 1 ||
                    loop.TryInteractAt(training.position, 66, out _))
                    throw new InvalidOperationException("Basic breathing practice could be claimed repeatedly without a clue.");
                if (!loop.TryInteractAt(clue.position, 67, out _) || loop.ObservedClues != 1 ||
                    loop.TryInteractAt(clue.position, 68, out _))
                    throw new InvalidOperationException("Clue discovery was not unique.");
                if (!loop.TryInteractAt(training.position, 69, out _) || loop.Insights != 2)
                    throw new InvalidOperationException("New clue did not unlock another practice insight.");
                if (loop.TrySecondary(market.position, out _))
                    throw new InvalidOperationException("Crafting without two herbs succeeded.");
                if (!loop.TryInteractAt(herb.position, 121, out _) ||
                    !loop.TryInteractAt(herb.position, 181, out _) || loop.Herbs != 2 ||
                    !loop.TrySecondary(market.position, out _) || loop.Herbs != 0 || loop.PracticePellets != 1)
                    throw new InvalidOperationException("Herb refinement did not consume exactly two herbs.");
                if (!loop.TrySecondary(training.position, out _) || loop.PracticePellets != 0 || loop.Insights != 4 ||
                    loop.TrySecondary(training.position, out _))
                    throw new InvalidOperationException("Using a practice pellet did not consume it exactly once.");
                Debug.Log("QINGXI_LOCAL_FORAGING_SMOKE_PASS: herb, rabbit, clue, breathing, refinement, market and duplicate guards.");
            }
            finally { UnityEngine.Object.DestroyImmediate(root); }
        }
    }
}
