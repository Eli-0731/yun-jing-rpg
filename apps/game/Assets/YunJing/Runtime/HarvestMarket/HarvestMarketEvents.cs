using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

namespace YunJing.HarvestMarket
{
    // The two events the panels end with. The core team wires them to the server's planting and shop ledger;
    // nothing here talks to the network. Payloads match work pack 02-B 1.6 field for field.
    public static class HarvestMarketEvents
    {
        [Serializable] public class PlantQuality { public string quality; }
        [Serializable] public class HarvestCompleted { public string fieldId; public PlantQuality[] plants; }
        [Serializable] public class SoldBundle { public string quality; public bool sold; public int coins; }
        [Serializable] public class MarketSold { public int day; public SoldBundle[] bundles; public int totalCoins; }

        public const string HarvestCompletedName = "harvest.completed", MarketSoldName = "market.sold";
        /// (event name, JSON payload). Subscribe here; the playtest also records every emission.
        public static event Action<string, string> Emitted;
        public static readonly List<(string name, string json)> Log = new List<(string, string)>();

        public static void EmitHarvest(string fieldId, IEnumerable<string> plants)
        {
            var e = new HarvestCompleted { fieldId = fieldId, plants = plants.Select(q => new PlantQuality { quality = q }).ToArray() };
            Emit(HarvestCompletedName, JsonUtility.ToJson(e));
        }

        public static void EmitSold(int day, HarvestSettlement s)
        {
            var e = new MarketSold { day = day, totalCoins = s.totalCoins, bundles = s.bundles.Select(b => new SoldBundle { quality = b.quality, sold = b.sold, coins = b.coins }).ToArray() };
            Emit(MarketSoldName, JsonUtility.ToJson(e));
        }

        static void Emit(string name, string json)
        {
            Log.Add((name, json));
            Debug.Log($"HARVEST_EVENT {name} {json}");
            Emitted?.Invoke(name, json);
        }
    }

    /// What the player carries from the field to the stall, and what they kept afterwards (local drill copy; the
    /// server inventory is the core team's). Bundles keep each plant's real grade.
    public static class HarvestCarry
    {
        public static int Day = 4;
        public static string FieldId = "TY_Field01";
        public static List<HerbBundle> Bundles = new List<HerbBundle>();
        public static readonly Dictionary<string, int> Kept = new Dictionary<string, int>();
        public static int Coins;
        /// The first sale is weighed by hand (it teaches the steelyard); after that 秤 balances itself unless the player drags.
        public static int Weighings;
        public static void Reset() { Bundles = new List<HerbBundle>(); Kept.Clear(); Coins = 0; Weighings = 0; }
    }
}
