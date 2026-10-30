using System;
using UnityEngine;

namespace YunJing
{
    // K23: the two spirit fields behind the newcomer's own house (the territory). F on an empty field plants
    // (青靈草 first, 淨水蓮 if only lotus seeds are left), F on a ripe one harvests. Online the server owns the
    // plots (plant / harvest actions, plots 0 and 1); offline a local copy keeps the yard playable, with the
    // same growth times. The sprouts grow with the remaining time and glow when ripe.
    public sealed class QingxiTerritoryFields : MonoBehaviour
    {
        [Serializable]
        public class Field
        {
            public Transform bed;
            public Transform crop;   // sprouts, scaled from seedling to ripe; a "RipeGlow" child shows when ripe
        }

        public Field[] fields = new Field[0];
        const float Reach = 2.0f;
        static readonly (string id, string label, string seed, double seconds)[] Crops =
        {
            ("qingling", "青靈草", "qingling-seed", 1800), ("lotus", "淨水蓮", "lotus-seed", 14400),
        };

        // Server clock, carried forward from the last snapshot.
        int seenVersion = -1; double serverAt; float capturedAt;
        double Now
        {
            get
            {
                if (!QingxiServerLink.Online) return DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
                var state = QingxiServerLink.Current.api.State;
                if (state.version != seenVersion) { seenVersion = state.version; serverAt = state.serverTime; capturedAt = Time.realtimeSinceStartup; }
                return serverAt + (Time.realtimeSinceStartup - capturedAt) * 1000.0;
            }
        }

        struct Planting { public bool planted; public string crop; public double readyAt; }

        // Online: what the server says, or for a few seconds what was just sent (still in the queue). A refused
        // action therefore never leaves a phantom crop. Offline: the local copy in PlayerPrefs.
        readonly Planting[] pending = new Planting[4]; readonly float[] pendingUntil = new float[4];

        Planting Get(int index)
        {
            if (QingxiServerLink.Online || (QingxiServerLink.Current != null && QingxiServerLink.Current.Connecting))
            {
                if (Time.realtimeSinceStartup < pendingUntil[index]) return pending[index];
                var plots = QingxiServerLink.Online ? QingxiServerLink.Current.api.State.player.plots : null;
                if (plots != null) foreach (var p in plots) if (p.index == index) return new Planting { planted = true, crop = p.crop, readyAt = p.readyAt };
                if (QingxiServerLink.Online) return default;
            }
            try
            {
                var crop = PlayerPrefs.GetString($"yj.field.{index}.crop", "");
                if (crop.Length == 0) return default;
                return new Planting { planted = true, crop = crop, readyAt = double.Parse(PlayerPrefs.GetString($"yj.field.{index}.ready", "0")) };
            }
            catch { return default; }
        }

        void SetLocal(int index, string crop, double readyAt)
        {
            pending[index] = new Planting { planted = !string.IsNullOrEmpty(crop), crop = crop, readyAt = readyAt };
            pendingUntil[index] = Time.realtimeSinceStartup + 8;
            try
            {
                PlayerPrefs.SetString($"yj.field.{index}.crop", crop ?? "");
                PlayerPrefs.SetString($"yj.field.{index}.ready", readyAt.ToString("R"));
                PlayerPrefs.Save();
            }
            catch { }
        }

        static (string id, string label, string seed, double seconds) Crop(string id) { foreach (var c in Crops) if (c.id == id) return c; return Crops[0]; }

        int Nearest(Vector3 position)
        {
            for (int i = 0; i < fields.Length; i++)
                if (fields[i].bed != null && Vector2.Distance(new Vector2(position.x, position.z), new Vector2(fields[i].bed.position.x, fields[i].bed.position.z)) <= Reach) return i;
            return -1;
        }

        int Seeds(string seed)
        {
            if (QingxiServerLink.Online) return QingxiServerLink.Current.Quantity(seed);
            try { return PlayerPrefs.GetInt("yj.seeds." + seed, seed == "qingling-seed" ? 3 : 2); } catch { return 0; }
        }

        static string Remaining(double ms)
        {
            var span = TimeSpan.FromMilliseconds(Math.Max(0, ms));
            return span.TotalHours >= 1 ? $"{(int)span.TotalHours} 時 {span.Minutes} 分" : span.TotalMinutes >= 1 ? $"{span.Minutes} 分 {span.Seconds} 秒" : $"{span.Seconds} 秒";
        }

        public string Prompt(Vector3 position)
        {
            int i = Nearest(position); if (i < 0) return null;
            var p = Get(i);
            if (!p.planted)
            {
                var c = Seeds("qingling-seed") > 0 ? Crops[0] : Crops[1];
                return $"F 在靈田種下{c.label}（種子 {Seeds(c.seed)}）";
            }
            var crop = Crop(p.crop);
            double left = p.readyAt - Now;
            return left <= 0 ? $"F 收成{crop.label}" : $"{crop.label}生長中・還要 {Remaining(left)}";
        }

        public bool TryInteract(Vector3 position, out string message)
        {
            message = null;
            int i = Nearest(position); if (i < 0) return false;
            var p = Get(i);
            if (!p.planted)
            {
                var c = Seeds("qingling-seed") > 0 ? Crops[0] : Seeds("lotus-seed") > 0 ? Crops[1] : default;
                if (c.id == null) { message = "沒有種子了：向補給商人買，或到外面採集"; return true; }
                SetLocal(i, c.id, Now + c.seconds * 1000);
                if (!QingxiServerLink.Online) try { PlayerPrefs.SetInt("yj.seeds." + c.seed, Seeds(c.seed) - 1); } catch { }
                QingxiServerLink.Current?.Submit(new GameAction { kind = "plant", plot = i, crop = c.id });
                message = $"種下{c.label}。{Remaining(c.seconds * 1000)}後可以收成";
                return true;
            }
            var crop = Crop(p.crop);
            if (p.readyAt > Now) { message = $"{crop.label}還在長，再等 {Remaining(p.readyAt - Now)}"; return true; }
            SetLocal(i, "", 0);
            QingxiServerLink.Current?.Submit(new GameAction { kind = "harvest", plot = i });
            message = $"收成{crop.label}。土壤底下，好像有什麼輕輕動了一下";
            return true;
        }

        void Update()
        {
            double now = Now;
            for (int i = 0; i < fields.Length; i++)
            {
                var f = fields[i]; if (f.crop == null) continue;
                var p = Get(i);
                f.crop.gameObject.SetActive(p.planted);
                if (!p.planted) continue;
                double total = Crop(p.crop).seconds * 1000;
                float grown = Mathf.Clamp01(1f - (float)((p.readyAt - now) / total));
                float s = Mathf.Lerp(.25f, 1f, grown);
                f.crop.localScale = new Vector3(1, s, 1);
                var glow = f.crop.Find("RipeGlow");
                if (glow != null) glow.gameObject.SetActive(grown >= 1f);
            }
        }
    }
}
