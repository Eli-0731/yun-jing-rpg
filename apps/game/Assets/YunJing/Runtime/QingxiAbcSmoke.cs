using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using QingxiWorld;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace YunJing
{
    // Opt-in check of a built Qingxi scene (--abc-smoke): walks the player through the three
    // collaborator zones, the alchemy-room door and back. Local rehearsal only; writes a report and quits.
    public sealed class QingxiAbcSmoke : MonoBehaviour
    {
        readonly List<string> results = new List<string>();
        bool passed = true;
        static bool running;   // the reloaded village scene carries its own copy of this component

        IEnumerator Start()
        {
            // --abc-smoke on the command line, or ?abc-smoke in the browser (WebGL/PWA build).
            bool requested = Array.IndexOf(Environment.GetCommandLineArgs(), "--abc-smoke") >= 0 || Application.absoluteURL.Contains("abc-smoke");
            if (running || !requested) yield break;
            running = true;
            Application.targetFrameRate = 60;
            DontDestroyOnLoad(gameObject);
            yield return new WaitForSecondsRealtime(1f);
            var home = SceneManager.GetActiveScene().name;
            var walker = QingxiFirstPerson.Current;
            var foraging = walker.GetComponent<QingxiLocalForaging>();
            var stations = walker.GetComponent<QingxiAbcStations>();
            var forest = FindFirstObjectByType<QingxiForestEncounter>();
            var body = walker.GetComponent<CharacterController>();

            // The village stands on a Unity Terrain: its collider must hold the walker up in the built player.
            var terrain = Terrain.activeTerrain;
            var groundCollider = terrain != null ? terrain.GetComponent<TerrainCollider>() : null;
            var groundRay = Physics.RaycastAll(new Vector3(0, 60, -22), Vector3.down, 200f, ~0, QueryTriggerInteraction.Ignore).FirstOrDefault(h => h.collider is TerrainCollider);
            bool groundHit = groundRay.collider != null;
            Debug.Log($"[QingxiAbcSmoke] terrain={(terrain != null ? terrain.name : "none")} collider={(groundCollider != null ? groundCollider.enabled.ToString() : "none")} data={(groundCollider != null && groundCollider.terrainData != null ? groundCollider.terrainData.heightmapResolution.ToString() : "none")} ray={groundHit} {(groundHit ? groundRay.collider.name + " y=" + groundRay.point.y.ToString("0.00") : "")}");
            if (terrain != null) Check($"terrain collider holds the ground (ray hit {(groundHit ? groundRay.collider.name : "nothing")})", groundHit && groundRay.collider is TerrainCollider);

            // C: sorting table opens and keeps a choice.
            Spot(walker, "回村分揀桌");
            yield return Frames(10);
            bool sortingOpened = false; stations.SortingRequested += () => sortingOpened = true;
            Check("return prompt", (foraging.Prompt(walker.transform.position) ?? "").Contains("分揀"));
            foraging.TryInteract(walker.transform.position, out _);
            Check("return table opens sorting", sortingOpened);
            QingxiReturnSorting.Session.Select("herb"); QingxiReturnSorting.Session.MoveTo("save");
            walker.SetMenuOpen(false);

            // A: walking up the rabbit trail must draw a readable tell (alert -> windup) from the rabbit.
            Spot(walker, "林地遭遇");
            yield return Frames(20);
            Check("forest zone active", forest.PlayerInside);
            var burrow = forest.transform.TransformPoint(new Vector3((float)forest.Rules.world.burrow.x, 0, (float)forest.Rules.world.burrow.z));
            var seen = new HashSet<string>();
            for (float until = Time.realtimeSinceStartup + 15f; Time.realtimeSinceStartup < until && !seen.Contains("windup");)
            {
                var to = burrow - walker.transform.position; to.y = 0;
                if (to.magnitude > 3.6f) body.Move(to.normalized * 3.2f * Time.deltaTime + Vector3.down * .5f * Time.deltaTime);
                seen.Add(forest.Rules.rabbit.state);
                yield return null;
            }
            Check($"rabbit alert then windup (seen {string.Join("/", seen)}, {Vector3.Distance(walker.transform.position, burrow):F1} m from burrow)", seen.Contains("alert") && seen.Contains("windup"));
            forest.ReturnToSafePoint();
            yield return Frames(10);
            Check("back at the A09 safe point", forest.Rules.InSafeZone());
            var data = QingxiAbcZoneData.Parse(forest.zoneData.text);
            var ladder = forest.transform.TransformPoint(new Vector3(data.forest.platform.ladder.x, 0, data.forest.platform.ladder.z));
            Teleport(walker, ladder);
            yield return Frames(5);
            foraging.TryInteract(walker.transform.position, out _);
            Check("climb the A10 watch platform", forest.Climbed && forest.Rules.InSafeZone());
            foraging.TryInteract(walker.transform.position, out _);
            Check("climb down again", !forest.Climbed && body.enabled);

            // Gather one herb so the trip through the alchemy room can prove the counts come back.
            Teleport(walker, foraging.herbNodes[0].position);
            yield return Frames(5);
            foraging.TryInteract(walker.transform.position, out _);
            int herbs = foraging.Herbs;
            Check("herb gathered", herbs == 1);
            yield return Frames(2);
            var herbVisual = foraging.herbNodes[0].GetComponent<QingxiHerbVisual>();
            Check("herb switches to its harvested model", herbVisual != null && herbVisual.post.activeSelf && !herbVisual.pre.activeSelf);

            // The herbal stall is the market; only read the prompt so the herb count stays for the carry check.
            if (foraging.marketEntrance != null)
            {
                Teleport(walker, foraging.marketEntrance.position);
                yield return Frames(5);
                Check("market stall offers trade", (foraging.Prompt(walker.transform.position) ?? "").Contains("交換"));
            }

            // A: Johnnnny0823's training posts start his drills and give movement back afterwards.
            var training = stations.training;
            if (training != null)
            {
                Teleport(walker, training.qiPost.position + training.qiPost.forward * -1.1f);
                yield return Frames(5);
                Check("qi post offers breathing", (foraging.Prompt(walker.transform.position) ?? "").Contains("引氣呼吸"));
                foraging.TryInteract(walker.transform.position, out _);
                Check("breathing drill starts and holds the walker", training.Breath != null && training.Frozen);
                yield return Frames(30);
                Check("breathing guide advances", training.Breath != null && training.Breath.Elapsed > -1.4);
                training.End();
                Teleport(walker, training.blockPost.position + training.blockPost.forward * -1.1f);
                yield return Frames(5);
                Check("agility post offers blocking", (foraging.Prompt(walker.transform.position) ?? "").Contains("武技格擋"));
                foraging.TryInteract(walker.transform.position, out _);
                Check("block drill starts", training.Block != null && training.Block.strikes.Count == 12);
                training.End();
                Check("walker free after the drill", !training.Frozen && walker.enabled);
            }

            // B: the door loads joshsu54's AlchemyRoom scene; Backspace / the button returns to the door.
            Spot(walker, "溪畔丹房");
            yield return Frames(5);
            var door = stations.alchemyDoor.position;
            foraging.TryInteract(walker.transform.position, out _);
            yield return new WaitForSecondsRealtime(2f);
            Check("alchemy room loaded", SceneManager.GetActiveScene().name == QingxiAbcStations.AlchemyScene && FindFirstObjectByType<QingxiSceneReturn>() != null);
            Check("alchemy workshop present", GameObject.Find("AlchemyServices") != null);
            FindFirstObjectByType<QingxiSceneReturn>().Leave();
            yield return new WaitForSecondsRealtime(2f);
            walker = QingxiFirstPerson.Current;
            foraging = walker.GetComponent<QingxiLocalForaging>();
            Check("back in " + home, SceneManager.GetActiveScene().name == home);
            Check($"returned to the alchemy door (at {walker.transform.position}, door {door})", Vector3.Distance(walker.transform.position, door) < 1.5f);
            Check("rehearsal counts carried", foraging.Herbs == herbs);
            Check("sorting kept", QingxiReturnSorting.Session.Placements["herb"] == "save");

            // Lodging: the house door fades into the interior scene; the exit door brings the player back out.
            stations = walker.GetComponent<QingxiAbcStations>();
            if (stations.lodgingDoor != null)
            {
                var lodgingDoor = stations.lodgingDoor.position;
                Teleport(walker, lodgingDoor);
                yield return Frames(5);
                Check("lodging door prompt", (foraging.Prompt(walker.transform.position) ?? "").Contains("借住處"));
                foraging.TryInteract(walker.transform.position, out _);
                yield return new WaitForSecondsRealtime(2.5f);
                walker = QingxiFirstPerson.Current;
                var inside = walker != null ? walker.GetComponent<QingxiAbcStations>() : null;
                Check("lodging interior loaded", SceneManager.GetActiveScene().name == QingxiAbcStations.LodgingScene && inside != null && inside.exitDoor != null);
                if (inside != null && inside.exitDoor != null)
                {
                    var indoorForaging = walker.GetComponent<QingxiLocalForaging>();
                    Check("counts carried indoors", indoorForaging.Herbs == herbs);
                    Teleport(walker, inside.bed.position + Vector3.right * 1.3f);
                    yield return Frames(5);
                    Check("bed offers rest", (indoorForaging.Prompt(walker.transform.position) ?? "").Contains("歇息"));
                    Teleport(walker, inside.chest.position + Vector3.left * 1.1f);
                    yield return Frames(5);
                    Check("chest can be opened", (indoorForaging.Prompt(walker.transform.position) ?? "").Contains("儲物箱"));
                    Teleport(walker, inside.training.qiPost.position + Vector3.back * .9f);
                    yield return Frames(5);
                    Check("cushion offers breathing", (indoorForaging.Prompt(walker.transform.position) ?? "").Contains("蒲團"));
                    Teleport(walker, inside.exitDoor.position);
                    yield return Frames(5);
                    indoorForaging.TryInteract(walker.transform.position, out _);
                    yield return new WaitForSecondsRealtime(2.5f);
                    walker = QingxiFirstPerson.Current;
                    foraging = walker.GetComponent<QingxiLocalForaging>();
                    Check($"back outside the lodging (at {walker.transform.position}, door {lodgingDoor})", SceneManager.GetActiveScene().name == home && Vector3.Distance(walker.transform.position, lodgingDoor) < 1.5f);
                    Check("counts carried back out", foraging.Herbs == herbs);
                }
            }

            var report = $"QINGXI_ABC_SMOKE {(passed ? "PASS" : "FAIL")}: " + string.Join("; ", results);
            Debug.Log(report);
            File.WriteAllText(Path.Combine(Application.persistentDataPath, "abc-smoke.txt"), report);
            Application.Quit(passed ? 0 : 1);
        }

        void Check(string what, bool ok) { results.Add((ok ? "ok " : "FAILED ") + what); passed &= ok; }

        static IEnumerator Frames(int n) { for (int i = 0; i < n; i++) yield return null; }

        static void Spot(QingxiFirstPerson walker, string name)
        {
            var index = Array.IndexOf(walker.spotNames, name);
            if (index < 0) throw new InvalidOperationException("No teleport spot " + name);
            walker.Teleport(index);
        }

        static void Teleport(QingxiFirstPerson walker, Vector3 position)
        {
            var body = walker.GetComponent<CharacterController>();
            body.enabled = false; walker.transform.position = position + Vector3.up * .1f; body.enabled = true;
        }
    }
}
