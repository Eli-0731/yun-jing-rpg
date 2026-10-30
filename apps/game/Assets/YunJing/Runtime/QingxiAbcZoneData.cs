using System;
using System.Linq;
using UnityEngine;

namespace YunJing
{
    // Shape of Assets/YunJing/Data/QingxiAbcZones.json, written by tools/qingxi-main-scene/build-data.mjs.
    [Serializable]
    public sealed class QingxiAbcZoneData
    {
        [Serializable] public sealed class Point { public float x, z, r; public int wearAt; }
        [Serializable] public sealed class Ladder { public float x, z; }
        [Serializable] public sealed class Platform { public float x, z, deck; public Ladder ladder; }
        [Serializable] public sealed class ForestItem { public string id; public float x, y, z, rot; public bool terrain, floor, hidden; public string dummy; }
        [Serializable] public sealed class ForestWorld { public Point burrow, safe, start, respawn; public Point[] cover, walls, safeZones, dummies; }
        [Serializable] public sealed class Command { public int tick; public float[] m, f; public int[] b; public string a; public bool d, r; }
        [Serializable] public sealed class ExpectedEvent { public float t; public string type, state, reason, kind; public int hp; }
        [Serializable] public sealed class Final { public string outcome, rabbitState; public float playerX, playerZ; public int playerHp, rabbitHp; }
        [Serializable] public sealed class Scenario { public string name, style; public bool faceRabbit; public int ticks; public Command[] commands; public ExpectedEvent[] events; public Final final; }
        [Serializable] public sealed class Forest { public ForestItem[] layout; public Platform platform; public ForestWorld world; public Scenario[] parity; }
        [Serializable] public sealed class KitItem { public string id, folder; public float x, y, z, yawDeg, rot; }
        [Serializable] public sealed class Table { public float x, y, z, width, depth; }
        [Serializable] public sealed class Alchemy { public KitItem[] layout; public Table table; public Point door; }
        [Serializable] public sealed class Return { public KitItem[] layout; public Point table; }

        public Forest forest; public Alchemy alchemy; public Return ret;

        public static QingxiAbcZoneData Parse(string json) => JsonUtility.FromJson<QingxiAbcZoneData>(json);

        public QingxiForestEncounterRules.World ToRulesWorld()
        {
            QingxiForestEncounterRules.Circle C(Point p) => new QingxiForestEncounterRules.Circle(p.x, p.z, p.r, p.wearAt);
            var w = forest.world;
            return new QingxiForestEncounterRules.World
            {
                burrow = C(w.burrow), safe = C(w.safe), start = C(w.start), respawn = w.respawn != null ? C(w.respawn) : (QingxiForestEncounterRules.Circle?)null,
                cover = (w.cover ?? new Point[0]).Select(C).ToList(), walls = (w.walls ?? new Point[0]).Select(C).ToList(),
                safeZones = (w.safeZones ?? new Point[0]).Select(C).ToList(), dummies = (w.dummies ?? new Point[0]).Select(C).ToList(),
            };
        }
    }
}
