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
            if (running || Array.IndexOf(Environment.GetCommandLineArgs(), "--abc-smoke") < 0) yield break;
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
            Check("returned to the alchemy door", Vector3.Distance(walker.transform.position, door) < 1.5f);
            Check("rehearsal counts carried", foraging.Herbs == herbs);
            Check("sorting kept", QingxiReturnSorting.Session.Placements["herb"] == "save");

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
