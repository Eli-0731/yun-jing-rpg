using System;
using System.Collections;
using System.Collections.Generic;
using System.Text;
using FishNet.Authenticating;
using FishNet.Broadcast;
using FishNet.Connection;
using FishNet.Managing;
using FishNet.Transporting;
using UnityEngine;
using UnityEngine.Networking;

namespace YunJing
{
    public struct TicketMessage : IBroadcast { public string Ticket; }
    [Serializable] class RedeemRequest { public string ticket, roomId = "qingxi"; }
    [Serializable] class RedeemResult { public string playerId; }
    public sealed class TicketAuthenticator : Authenticator
    {
        public override event Action<NetworkConnection, bool> OnAuthenticationResult;
        readonly HashSet<NetworkConnection> pending = new();
        readonly Dictionary<string, NetworkConnection> players = new();
        public override void InitializeOnce(NetworkManager manager)
        {
            base.InitializeOnce(manager);
            manager.ServerManager.RegisterBroadcast<TicketMessage>(Receive, false);
            manager.ClientManager.OnClientConnectionState += state => {
                if (state.ConnectionState == LocalConnectionState.Started)
                    manager.ClientManager.Broadcast(new TicketMessage { Ticket = GetComponent<GameApi>().Ticket });
            };
            manager.ServerManager.OnRemoteConnectionState += (connection, state) => {
                if (state.ConnectionState != RemoteConnectionState.Stopped) return;
                pending.Remove(connection);
                var remove = new List<string>();
                foreach (var pair in players) if (pair.Value == connection) remove.Add(pair.Key);
                foreach (var key in remove) players.Remove(key);
            };
        }
        public override void OnRemoteConnection(NetworkConnection connection)
        {
            base.OnRemoteConnection(connection);
            StartCoroutine(Timeout(connection));
        }
        IEnumerator Timeout(NetworkConnection connection)
        {
            yield return new WaitForSecondsRealtime(20);
            if (connection.IsActive && !connection.IsAuthenticated) connection.Disconnect(true);
        }
        void Receive(NetworkConnection connection, TicketMessage message, Channel channel)
        {
            if (connection.IsAuthenticated || !pending.Add(connection) || string.IsNullOrEmpty(message.Ticket) || message.Ticket.Length > 128)
            { connection.Disconnect(true); return; }
            StartCoroutine(Validate(connection, message.Ticket));
        }
        IEnumerator Validate(NetworkConnection connection, string ticket)
        {
            // Only dedicated server processes receive this environment variable. Never serialize it in an asset.
            string key = Environment.GetEnvironmentVariable("YUNJING_INTERNAL_KEY");
            if (string.IsNullOrEmpty(key)) { pending.Remove(connection); OnAuthenticationResult?.Invoke(connection, false); yield break; }
            var api = GetComponent<GameApi>();
            using var request = new UnityWebRequest(api.BaseUrl + "/v1/internal/room/redeem", "POST");
            request.uploadHandler = new UploadHandlerRaw(Encoding.UTF8.GetBytes(JsonUtility.ToJson(new RedeemRequest { ticket = ticket })));
            request.downloadHandler = new DownloadHandlerBuffer(); request.timeout = 10;
            request.SetRequestHeader("Content-Type", "application/json"); request.SetRequestHeader("X-Service-Key", key);
            yield return request.SendWebRequest();
            pending.Remove(connection);
            if (!connection.IsActive) yield break;
            if (request.result != UnityWebRequest.Result.Success) { OnAuthenticationResult?.Invoke(connection, false); yield break; }
            var player = JsonUtility.FromJson<RedeemResult>(request.downloadHandler.text).playerId;
            if (players.TryGetValue(player, out var previous) && previous != connection && previous.IsActive) previous.Disconnect(true);
            players[player] = connection;
            OnAuthenticationResult?.Invoke(connection, true);
        }
    }
}
