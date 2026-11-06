using System.Collections.Generic;
using UnityEngine;

namespace YunJing.BasicCombat
{
    /// <summary>One resolved hit, as raised by the rules (combat.hit { targetId, attackId, damage }) plus what the target needs to react.</summary>
    public struct CombatHit
    {
        public string targetId, attackId;
        public float damage, knockback, hitStop;
        public Vector3 direction;   // world, flat, from the attacker toward the target
        public bool heavy;
    }

    /// <summary>Anything the basic combat can hit. Register while enabled; the combat reads position and radius on its ground plane.</summary>
    public interface ICombatTarget
    {
        string CombatId { get; }
        Vector3 CombatPosition { get; }
        float CombatRadius { get; }
        bool CombatAlive { get; }
        void TakeCombatHit(CombatHit hit);
    }

    public static class CombatTargets
    {
        static readonly List<ICombatTarget> all = new List<ICombatTarget>();
        public static IReadOnlyList<ICombatTarget> All => all;
        public static void Add(ICombatTarget t) { if (!all.Contains(t)) all.Add(t); }
        public static void Remove(ICombatTarget t) => all.Remove(t);
    }
}
