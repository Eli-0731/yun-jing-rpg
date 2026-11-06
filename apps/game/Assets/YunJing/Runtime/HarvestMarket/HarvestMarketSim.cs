using System;
using System.Collections.Generic;
using System.Linq;

namespace YunJing.HarvestMarket
{
    // Values from packages/content/harvest-market-v1.json; tests/harvest-market.test.ts fails if they drift apart.
    // Same rules as tools/harvest-market/rules.ts: pull → sort → sell, deterministic, never a loss.
    public static class HarvestContent
    {
        public const string item = "qingling-herb", stall = "Market_HerbalStall";
        public const double pullSafeSeconds = 0.8;
        public const int bundleSize = 3;
        public const int sortBonus = 1;   // a sold bundle whose every plant is the bundle grade earns this much more
        public static readonly string[] grades = { "top", "mid", "low" };   // best first
        public static readonly (string id, string label, int bundlePrice, string look)[] gradeRows =
        {
            ("top", "上品", 5, "葉子完整，葉尖微微發光"),
            ("mid", "中品", 3, "葉子完整，不發光"),
            ("low", "次品", 2, "葉子有破洞，邊緣發黃"),
        };
        public static readonly (string id, string[] plants)[] fields =
        {
            ("TY_Field01", new[] { "mid", "top", "low", "mid", "top", "mid" }),
        };
        public static readonly (int day, string item, int bonus)[] dailyDemand =
        {
            (4, "qingling-herb", 1),
        };
        public static readonly (string id, string text)[] lines =
        {
            ("mixed-lower", "這捆裡混了一株次一等的，我照實際的算給你。"),
            ("mixed-higher", "這捆裡藏了一株好的，照實算，不讓你吃虧。"),
            ("all-top", "整捆都是上品，好眼力！"),
            ("demand-bonus", "今天坊市正缺青靈草，每捆多給一點。"),
            ("kept-all", "都留著也好，煉丹、泡茶都用得上。"),
            ("thanks", "收下了。下回收成再來。"),
        };

        public static int Rank(string grade) => Array.IndexOf(grades, grade);
        public static string Label(string grade) => gradeRows[Rank(grade)].label;
        public static int Price(string grade) => gradeRows[Rank(grade)].bundlePrice;
        public static string Line(string id) => lines.First(l => l.id == id).text;
        public static string[] FieldPlants(string fieldId) => fields.First(f => f.id == fieldId).plants;
        public static int DemandBonus(int day, string forItem = item) => dailyDemand.Where(d => d.day == day && d.item == forItem).Sum(d => d.bonus);
    }

    public sealed class HerbBundle
    {
        public string bin, quality; public List<int> plants = new List<int>(); public List<string> grades = new List<string>();
        public bool sold, sorted; public int coins; public string line = "";
    }

    public sealed class HarvestSettlement
    {
        public List<HerbBundle> bundles; public int totalCoins; public List<(string quality, int quantity)> kept; public List<string> lines;
    }

    public static class HarvestRules
    {
        /// Pulling faster than pullSafeSeconds snaps the root: one grade down; the lowest grade stays.
        public static string PullGrade(string original, double seconds)
        {
            if (seconds >= HarvestContent.pullSafeSeconds) return original;
            return HarvestContent.grades[Math.Min(HarvestContent.Rank(original) + 1, HarvestContent.grades.Length - 1)];
        }

        /// Plants on the same bundle are tied in field order, bundleSize to a bundle; bundles are listed top, mid, low.
        public static List<HerbBundle> BundleUp(IList<string> plants, IList<string> bins)
        {
            var list = new List<HerbBundle>();
            foreach (var bin in HarvestContent.grades)
            {
                var mine = Enumerable.Range(0, plants.Count).Where(i => bins[i] == bin).ToList();
                for (int at = 0; at < mine.Count; at += HarvestContent.bundleSize)
                {
                    var b = new HerbBundle { bin = bin, plants = mine.Skip(at).Take(HarvestContent.bundleSize).ToList() };
                    b.grades = b.plants.Select(i => plants[i]).ToList();
                    b.quality = b.grades.OrderByDescending(HarvestContent.Rank).First();
                    list.Add(b);
                }
            }
            return list;
        }

        /// Each plant is a third of its grade's bundle price plus a third of today's bonus; a part bundle rounds up.
        public static int BundleCoins(IList<string> grades, int day)
        {
            if (grades.Count == 0) return 0;
            int bonus = HarvestContent.DemandBonus(day), sum = grades.Sum(g => HarvestContent.Price(g) + bonus);
            return (sum + HarvestContent.bundleSize - 1) / HarvestContent.bundleSize;
        }

        public static HarvestSettlement Settle(int day, List<HerbBundle> bundles, IList<bool> sell)
        {
            var lines = new List<string>();
            void Say(string id) { if (!string.IsNullOrEmpty(id) && !lines.Contains(id)) lines.Add(id); }
            for (int i = 0; i < bundles.Count; i++)
            {
                var b = bundles[i]; b.sold = sell[i];
                int bin = HarvestContent.Rank(b.bin);
                bool lower = b.grades.Any(g => HarvestContent.Rank(g) > bin), higher = b.grades.Any(g => HarvestContent.Rank(g) < bin);
                b.sorted = !lower && !higher;   // clean bundles earn the sort bonus; mixed ones are paid by real grade
                b.coins = b.sold ? BundleCoins(b.grades, day) + (b.sorted ? HarvestContent.sortBonus : 0) : 0;
                b.line = !b.sold ? "" : lower ? "mixed-lower" : higher ? "mixed-higher" : "";
            }
            var sold = bundles.Where(b => b.sold).ToList();
            if (sold.Count == 0) Say("kept-all");
            else
            {
                foreach (var b in sold) Say(b.line);
                if (sold.Any(b => b.grades.Count == HarvestContent.bundleSize && b.grades.All(g => g == "top"))) Say("all-top");
                if (HarvestContent.DemandBonus(day) > 0) Say("demand-bonus");
                Say("thanks");
            }
            var kept = HarvestContent.grades
                .Select(g => (g, bundles.Where(b => !b.sold).Sum(b => b.grades.Count(x => x == g))))
                .Where(k => k.Item2 > 0).ToList();
            return new HarvestSettlement { bundles = bundles, totalCoins = bundles.Sum(b => b.coins), kept = kept, lines = lines };
        }
    }
}
