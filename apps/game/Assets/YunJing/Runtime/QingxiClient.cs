using System;
using System.Linq;
using FishNet.Managing;
using FishNet.Transporting;
using UnityEngine;

namespace YunJing
{
    public sealed class QingxiClient : MonoBehaviour
    {
        GameApi api; NetworkManager network; string alias = "traveler-a"; Vector2 scroll; bool headless;
        void Start()
        {
            api = GetComponent<GameApi>(); network = GetComponent<NetworkManager>();
            network.TimeManager.SetTickRate(30);
            network.ServerManager.SetAuthenticator(GetComponent<TicketAuthenticator>());
            var transport = network.TransportManager.Transport;
            transport.SetPort(7770); transport.SetMaximumClients(12);
            transport.SetServerBindAddress("127.0.0.1", IPAddressType.IPv4);
            headless = Application.isBatchMode || Environment.GetCommandLineArgs().Contains("--server");
            if (headless) network.ServerManager.StartConnection();
        }
        void Button(string label, string kind, Action<GameAction> configure = null)
        {
            if (!GUILayout.Button(label, GUILayout.Height(32))) return;
            var action = new GameAction { kind = kind }; configure?.Invoke(action); api.Act(action);
        }
        void OnGUI()
        {
            if (headless || api == null) return;
            Cultivator.TextInputFocused = !string.IsNullOrEmpty(GUI.GetNameOfFocusedControl());
            float scale = Mathf.Max(1, Screen.height / 900f);
            GUI.matrix = Matrix4x4.Scale(Vector3.one * scale);
            GUILayout.BeginArea(new Rect(16, 16, 350, Screen.height / scale - 200), GUI.skin.box);
            GUILayout.Label("YUN JING · QINGXI / DEVELOPMENT");
            GUILayout.Label(api.Status);
            GUI.enabled = !api.Busy;
            if (api.Session == null)
            {
                GUI.SetNextControlName("alias"); alias = GUILayout.TextField(alias, 24);
                if (GUILayout.Button("Enter local identity")) { GUI.FocusControl(null); api.Login(alias); }
            }
            else
            {
                if (!network.ClientManager.Started && GUILayout.Button("Join dedicated Qingxi server"))
                    api.Join(ticket => { network.TransportManager.Transport.SetClientAddress(ticket.host); network.TransportManager.Transport.SetPort(ticket.port); network.ClientManager.StartConnection(); });
                GUILayout.Label(network.ClientManager.Started ? "Connected · WASD / touch arrows" : "API ready · room server disconnected");
                if (api.HasPending && GUILayout.Button("Retry pending operation")) api.Retry();
                GUI.enabled = !api.Busy && !api.HasPending;
                scroll = GUILayout.BeginScrollView(scroll);
                var state = api.State;
                if (state != null)
                {
                    GUILayout.Label(state.player.name + " · " + (state.birth?.label ?? (state.birthAssigned ? "Talent assigned; assessment pending" : "Birth not allocated")));
                    if (!state.birthAssigned && (state.birth == null || string.IsNullOrEmpty(state.birth.tier))) Button("Allocate birth ONCE", "birth");
                    else
                    {
                        GUILayout.Label($"Body {state.player.body} / Qi {state.player.qi} · Realm {state.player.realm}");
                        if (state.player.journey != null)
                        {
                            double days = Math.Max(0, (state.player.journey.selectionAt - state.serverTime) / 86400000);
                            GUILayout.Label($"Selection unlock: {days:F2} real days remaining (offline counts)");
                            if (days <= 0 && (state.birth == null || string.IsNullOrEmpty(state.birth.tier))) Button("Assess talent at the plaza", "appraise");
                            Button("Practice Qi primer", "practice-basic", a => a.discipline = "qi");
                            Button("Practice basic martial arts", "practice-basic", a => a.discipline = "body");
                        }
                        GUILayout.Label($"Channel {state.world.channel}/{state.world.required} · Water {state.world.waterQuality}");
                        foreach (var clue in new[] { "broken-array", "dry-lotus", "beast-nest" })
                            if (!state.player.clues.Contains(clue)) Button("Investigate " + clue, "investigate", a => a.clue = clue);
                        Button("Collect stone", "gather", a => a.node = "quarry");
                        Button("Collect seeds", "gather", a => a.node = "seed-bank");
                        Button("Contribute 3 stone", "contribute", a => a.quantity = 3);
                        Button("Claim channel contribution", "claim-project");
                        for (int i = 0; i < 4; i++)
                        {
                            int index = i; var plot = state.player.plots.FirstOrDefault(p => p.index == index);
                            if (plot == null)
                            {
                                Button($"Plot {i + 1}: Qingling", "plant", a => { a.plot = index; a.crop = "qingling"; });
                                Button($"Plot {i + 1}: Lotus", "plant", a => { a.plot = index; a.crop = "lotus"; });
                            }
                            else Button($"Harvest {i + 1}: {plot.crop}", "harvest", a => a.plot = index);
                        }
                        Button("Brew body bath", "craft", a => a.recipe = "body-bath");
                        Button("Brew water purifier", "craft", a => a.recipe = "water-purifier");
                        foreach (var job in state.player.jobs.Where(j => !j.claimed)) Button("Claim " + job.recipe, "claim-craft", a => a.job = job.id);
                        Button("Join Xuanyue (body)", "enroll", a => a.sect = "xuanyue");
                        Button("Join Taixuan (spell)", "enroll", a => a.sect = "taixuan");
                        Button("Practice", "practice"); Button("Use medicinal bath", "bathe"); Button("Awaken acquired root", "awaken");
                        Button("Restore ecology", "resolve", a => a.route = "ecology");
                        Button("Coexist with beasts", "resolve", a => a.route = "coexist");
                        Button("Complete first trial", "breakthrough");
                        foreach (var item in state.player.inventory) GUILayout.Label($"{item.item} ×{item.quantity}" + (item.bound ? " [bound]" : ""));
                    }
                }
                GUILayout.EndScrollView();
            }
            GUI.enabled = true; GUILayout.EndArea();
            if (Cultivator.Local != null)
            {
                // Keep the movement pad on the left; the right half is the touch-look area.
                float x = 20, y = Screen.height / scale - 160;
                var direction = Vector2.zero;
                if (GUI.RepeatButton(new Rect(x + 55, y, 55, 45), "↑")) direction.y++;
                if (GUI.RepeatButton(new Rect(x, y + 50, 55, 45), "←")) direction.x--;
                if (GUI.RepeatButton(new Rect(x + 55, y + 50, 55, 45), "↓")) direction.y--;
                if (GUI.RepeatButton(new Rect(x + 110, y + 50, 55, 45), "→")) direction.x++;
                Cultivator.TouchInput = direction;
            }
        }
    }
}
