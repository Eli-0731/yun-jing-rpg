using System;
using System.Collections;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;
using YunJing.Alchemy;

namespace YunJing
{
    [Serializable] public class Session { public string token; public string refreshToken; }
    [Serializable] public class Birth { public string tier, label, constitution; public string[] roots; public int apertures; public float efficiency; }
    [Serializable] public class Stack { public string item; public int quantity, potency; public bool bound; }
    [Serializable] public class Plot { public int index; public string crop; public double readyAt; }
    [Serializable] public class Job { public string id, recipe; public double readyAt; public bool claimed; }
    [Serializable] public class Journey { public double createdAt, selectionAt, assessedAt; public string manual, housing; }
    [Serializable] public class Player { public string id, name, sect, path; public int realm, body, qi, apertures; public string[] roots, clues, milestones; public Stack[] inventory; public Plot[] plots; public Job[] jobs; public Journey journey; public AlchemyState alchemy; }
    [Serializable] public class World { public int channel, required, waterQuality; public bool sanctuary; }
    [Serializable] public class Snapshot { public Player player; public Birth birth; public bool birthAssigned; public World world; public double serverTime; public int version; public AlchemyView alchemy; }
    [Serializable] public class RoomTicket { public string ticket, roomId, host; public ushort port; }
    [Serializable] public class ErrorBody { public string message; }
    [Serializable] public class GameAction { public string kind, node, clue, crop, recipe, job, sect, route, discipline, item; public int plot, quantity; public bool useCompanion;
        public string offer; public int packs, fuel, potency; public AlchemyHerbLock[] herbs; public AlchemyEvent[] log; }
    [Serializable] class ActionRequest { public string requestId; public GameAction action; }
    [Serializable] class AliasRequest { public string alias; }
    [Serializable] class RefreshRequest { public string refreshToken; }

    public sealed class GameApi : MonoBehaviour
    {
        public string BaseUrl = "http://127.0.0.1:4310";
        public Snapshot State { get; private set; }
        public Session Session { get; private set; }
        public string Status { get; private set; } = "Local development client";
        public bool Busy { get; private set; }
        public string Ticket { get; private set; }
        string pending;
        float nextPoll;
        public bool HasPending => pending != null;
        public string LastError { get; private set; }
        Action<bool, string> pendingDone;
        void Update()
        {
            if (Session != null && !Busy && Time.unscaledTime >= nextPoll)
            { nextPoll = Time.unscaledTime + 5; StartCoroutine(RefreshState()); }
        }
        public void Login(string alias)
        {
            if (!Busy) StartCoroutine(LoginRoutine(alias));
        }
        IEnumerator LoginRoutine(string alias)
        {
            Busy = true;
            yield return Send("/v1/auth/local", JsonUtility.ToJson(new AliasRequest { alias = alias }), false,
                json => { Session = JsonUtility.FromJson<Session>(json); pending = null; });
            if (Session != null) yield return ReadState();
            Busy = false;
        }
        IEnumerator RefreshState() { Busy = true; yield return ReadState(); Busy = false; }
        IEnumerator ReadState() { yield return Send("/v1/me", null, true, Apply); }
        void Apply(string json) { State = JsonUtility.FromJson<Snapshot>(json); Status = "Saved · revision " + State.version; }
        public void Act(GameAction action) => Act(action, null);
        /// done(success, error) fires once the request settles; a refused call (busy, no session) reports false at once.
        /// A network failure keeps the same request ID pending for Retry, and done waits for that retry.
        public void Act(GameAction action, Action<bool, string> done)
        {
            if (Busy || Session == null || pending != null) { done?.Invoke(false, Busy ? "BUSY" : "NO_SESSION"); return; }
            pendingDone = done;
            pending = JsonUtility.ToJson(new ActionRequest { requestId = Guid.NewGuid().ToString(), action = action });
            StartCoroutine(Submit());
        }
        public void Retry() { if (!Busy && pending != null) StartCoroutine(Submit()); }
        public void Refresh(Action done = null) { if (!Busy && Session != null) StartCoroutine(RefreshThen(done)); }
        IEnumerator RefreshThen(Action done) { yield return RefreshState(); done?.Invoke(); }
        IEnumerator Submit()
        {
            Busy = true; bool ok = false;
            yield return Send("/v1/actions", pending, true, json => { Apply(json); pending = null; ok = true; },
                status => { if (status >= 400 && status < 500 && status != 401) pending = null; });
            Busy = false;
            if (ok || pending == null) { var done = pendingDone; pendingDone = null; LastError = ok ? null : Status; done?.Invoke(ok, LastError); }
        }
        public void Join(Action<RoomTicket> ready)
        {
            if (!Busy && Session != null) StartCoroutine(JoinRoutine(ready));
        }
        IEnumerator JoinRoutine(Action<RoomTicket> ready)
        {
            Busy = true;
            yield return Send("/v1/room/ticket", "{}", true, json => {
                var ticket = JsonUtility.FromJson<RoomTicket>(json); Ticket = ticket.ticket; ready(ticket);
            });
            Busy = false;
        }
        IEnumerator Send(string path, string body, bool authenticated, Action<string> success, Action<long> failure = null, bool retryAuth = true)
        {
            using var request = new UnityWebRequest(BaseUrl + path, body == null ? "GET" : "POST");
            request.downloadHandler = new DownloadHandlerBuffer(); request.timeout = 15;
            if (body != null) { request.uploadHandler = new UploadHandlerRaw(Encoding.UTF8.GetBytes(body)); request.SetRequestHeader("Content-Type", "application/json"); }
            if (authenticated && Session != null) request.SetRequestHeader("Authorization", "Bearer " + Session.token);
            yield return request.SendWebRequest();
            if (request.responseCode == 401 && authenticated && retryAuth && Session != null)
            {
                bool refreshed = false;
                yield return Send("/v1/auth/refresh", JsonUtility.ToJson(new RefreshRequest { refreshToken = Session.refreshToken }), false,
                    json => { Session = JsonUtility.FromJson<Session>(json); refreshed = true; });
                if (refreshed) { yield return Send(path, body, true, success, failure, false); yield break; }
            }
            if (request.result == UnityWebRequest.Result.Success) success(request.downloadHandler.text);
            else
            {
                var error = request.downloadHandler.text;
                try { error = JsonUtility.FromJson<ErrorBody>(error)?.message ?? request.error; } catch { error = request.error; }
                Status = error + (pending != null ? " · retry keeps the same request ID" : "");
                failure?.Invoke(request.responseCode);
            }
        }
    }
}
