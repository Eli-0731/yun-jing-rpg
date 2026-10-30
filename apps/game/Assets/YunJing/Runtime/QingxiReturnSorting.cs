using System.Collections.Generic;
using System.Linq;

namespace YunJing
{
    // C# port of tools/qingxi-return-c/state.js (Eli-0731's return-to-village sorting rules).
    // Three fixed demonstration samples, three free destinations, undo of the latest real change.
    // Local rehearsal only: never inventory, never a commission completion (see handoff-contract.md).
    public sealed class QingxiReturnSorting
    {
        public sealed class Sample { public string id, name, source, use, symbol; }
        public sealed class Entry { public string sample, to, kind; }
        public sealed class Move { public string sample, from, to; }
        public sealed class Result { public string message, feedback; public bool changed; }

        public static readonly Sample[] Samples = {
            new Sample { id = "herb", name = "青靈草樣本", source = "溪畔淺灘", use = "辨識葉脈，或留作配伍觀察。", symbol = "草" },
            new Sample { id = "ore", name = "溪石礦樣本", source = "溪路石壁", use = "觀察石紋，或留待工坊辨材。", symbol = "石" },
            new Sample { id = "seed", name = "露珠草種樣本", source = "村外草坡", use = "保存作為種植觀察樣本。", symbol = "種" },
        };
        public static readonly (string id, string label)[] Destinations = { ("save", "保存"), ("alchemy", "留待煉製"), ("commission", "交委託（展示）") };

        // Kept for the whole run so walking into the alchemy room and back does not lose the sorting.
        public static readonly QingxiReturnSorting Session = new QingxiReturnSorting();

        public string Selected { get; private set; }
        public readonly Dictionary<string, string> Placements = Samples.ToDictionary(s => s.id, s => (string)null);
        public Move LastAction { get; private set; }
        public readonly List<Entry> Journal = new List<Entry>();
        public int Revision { get; private set; }

        public static Sample Find(string id) => Samples.FirstOrDefault(s => s.id == id);
        public static string Label(string destination) => destination == null ? "分揀桌" : Destinations.First(d => d.id == destination).label;
        static bool IsDestination(string id) => Destinations.Any(d => d.id == id);

        public Result Select(string sample)
        {
            var s = Find(sample);
            if (s == null) return new Result { message = "找不到這份樣本，請重新選擇。" };
            Selected = sample;
            return new Result { message = $"已選取{s.name}；接著選一個去向。", feedback = "table", changed = true };
        }

        public Result MoveTo(string destination)
        {
            if (Selected == null) return new Result { message = "先在桌上選一份樣本，再決定放到哪裡。", feedback = "table" };
            if (!IsDestination(destination)) return new Result { message = "這個去向尚未開放。" };
            var from = Placements[Selected];
            if (from == destination) return new Result { message = $"這份樣本已在「{Label(destination)}」，沒有新增數量。", feedback = destination };
            Placements[Selected] = destination;
            LastAction = new Move { sample = Selected, from = from, to = destination };
            Revision++;
            Record(new Entry { sample = Selected, to = destination, kind = "move" });
            return new Result { message = $"{Find(Selected).name}已選「{Label(destination)}」。", feedback = destination, changed = true };
        }

        public Result Undo()
        {
            var a = LastAction;
            if (a == null) return new Result { message = "目前沒有可以取消的選擇。" };
            Placements[a.sample] = a.from;
            LastAction = null;
            Revision++;
            Record(new Entry { sample = a.sample, to = a.from, kind = "undo" });
            return new Result { message = $"已取消{Find(a.sample).name}的最近選擇，回到{Label(a.from)}。", feedback = "table", changed = true };
        }

        void Record(Entry e) { Journal.Add(e); if (Journal.Count > 30) Journal.RemoveAt(0); }

        public int Count(string destination) => Placements.Values.Count(v => v == destination);
    }
}
