// RhythiaClient.cs — Firestore-backed leaderboard client for Unity games.
// Pure UnityWebRequest, NO Firebase SDK required.
//
// Usage:
//   var client = new RhythiaClient("API_KEY", "PROJECT_ID");
//   Player name flow (before gameplay):
//       client.GetPlayers(names => {
//           // UI: show scroll menu of `names`, or type a new one...
//           client.RegisterPlayer(name);
//       });
//   After gameplay:
//       client.ReportScore(name, "zombie-gun", 5700);
//
// Requires: internet + Firebase set up per leaderboard/README.md.
// Anonymous sign-in is used once so Firestore accepts writes.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;

namespace Rhythia
{
    public class RhythiaClient
    {
        const string AuthUrl = "https://identitytoolkit.googleapis.com/v1/accounts:signUp";

        readonly string apiKey;
        readonly string projectId;
        string idToken;

        public RhythiaClient(string apiKey, string projectId)
        {
            this.apiKey = apiKey;
            this.projectId = projectId;
        }

        string FirestoreBase =>
            "https://firestore.googleapis.com/v1/projects/" + projectId +
            "/databases/(default)/documents";

        // ---------- auth (anonymous sign-in) ----------

        IEnumerator EnsureToken()
        {
            if (!string.IsNullOrEmpty(idToken)) yield break;
            using (var www = new UnityWebRequest(AuthUrl + "?key=" + apiKey, "POST"))
            {
                www.uploadHandler = new UploadHandlerRaw(Encoding.UTF8.GetBytes("{\"returnSecureToken\":true}"));
                www.downloadHandler = new DownloadHandlerBuffer();
                www.SetRequestHeader("Content-Type", "application/json");
                yield return www.SendWebRequest();
                if (www.result != UnityWebRequest.Result.Success)
                    throw new Exception("Rhythia auth failed: " + www.error);
                idToken = Json.Get(www.downloadHandler.text, "idToken");
            }
        }

        // ---------- players ----------

        /// <summary>Fetch and sort the registered player names.</summary>
        public IEnumerator GetPlayers(Action<List<string>> onDone)
        {
            yield return EnsureToken();
            var names = new List<string>();
            using (var www = new UnityWebRequest(FirestoreBase + "/players?pageSize=1000", "GET")
            {
                downloadHandler = new DownloadHandlerBuffer()
            })
            {
                www.SetRequestHeader("Authorization", "Bearer " + idToken);
                yield return www.SendWebRequest();
                if (www.result == UnityWebRequest.Result.Success)
                    names.AddRange(Json.CollectStringValues(www.downloadHandler.text, "player"));
            }
            names.Sort(StringComparer.Ordinal);
            onDone(names);
        }

        /// <summary>Idempotent register. Safe to call on an existing player.</summary>
        public IEnumerator RegisterPlayer(string name, Action<bool> onDone = null)
        {
            yield return EnsureToken();
            name = TrimTo(name, 30);
            string docId = Uri.EscapeDataString(name);
            string payload = "{\"fields\":{\"name\":{\"stringValue\":\"" + Json.Escape(name) +
                             "\"},\"createdAt\":{\"stringValue\":\"" + UnixNow() + "\"}}}";
            using (var www = new UnityWebRequest(FirestoreBase + "/players?documentId=" + docId +
                                                 "&allowMissing=true", "PATCH")
            {
                uploadHandler = new UploadHandlerRaw(Encoding.UTF8.GetBytes(payload)),
                downloadHandler = new DownloadHandlerBuffer()
            })
            {
                www.SetRequestHeader("Content-Type", "application/json");
                www.SetRequestHeader("Authorization", "Bearer " + idToken);
                yield return www.SendWebRequest();
                // Any response = done; an existing player simply 404s on a re-PATCH.
                onDone?.Invoke(true);
            }
        }

        // ---------- scores ----------

        public IEnumerator ReportScore(string player, string game, double score,
                                       Action<bool> onDone = null)
        {
            yield return EnsureToken();
            string payload =
                "{\"fields\":{" +
                "\"player\":{\"stringValue\":\"" + Json.Escape(player) + "\"}," +
                "\"game\":{\"stringValue\":\"" + Json.Escape(game) + "\"}," +
                "\"score\":{\"doubleValue\":" + score.ToString("R", System.Globalization.CultureInfo.InvariantCulture) + "}," +
                "\"ts\":{\"stringValue\":\"" + UnixNow() + "\"}" +
                "}}";
            using (var www = new UnityWebRequest(FirestoreBase + "/scores", "POST")
            {
                uploadHandler = new UploadHandlerRaw(Encoding.UTF8.GetBytes(payload)),
                downloadHandler = new DownloadHandlerBuffer()
            })
            {
                www.SetRequestHeader("Content-Type", "application/json");
                www.SetRequestHeader("Authorization", "Bearer " + idToken);
                yield return www.SendWebRequest();
                onDone?.Invoke(www.result == UnityWebRequest.Result.Success);
            }
        }

        // ---------- helpers ----------

        static string UnixNow()
        {
            return ((long)(DateTime.UtcNow - new DateTime(1970, 1, 1)).TotalSeconds).ToString();
        }

        static string TrimTo(string s, int max)
        {
            s = (s ?? "").Trim();
            return s.Length <= max ? s : s.Substring(0, max);
        }
    }

    /// <summary>Minimal JSON helpers for the Firestore payloads we use.</summary>
    static class Json
    {
        /// <summary>Read a top-level string field:  {"field":{"stringValue":"..."}}</summary>
        public static string Get(string text, string field)
        {
            string key = "\"" + field + "\"";
            int idx = text.IndexOf(key, StringComparison.Ordinal);
            if (idx < 0) return null;
            int s = text.IndexOf("stringValue", idx + key.Length, StringComparison.Ordinal);
            int q1 = text.IndexOf('"', s);
            if (q1 < 0) return null;
            int q2 = text.IndexOf('"', q1 + 1);
            if (q2 < 0) return null;
            return text.Substring(q1 + 1, q2 - q1 - 1);
        }

        /// <summary>Collect every {"stringValue": ...} whose field name matches.</summary>
        public static List<string> CollectStringValues(string text, string field)
        {
            var list = new List<string>();
            string pattern = "\"" + field + "\":{\"stringValue\":\"";
            int i = 0;
            while (true)
            {
                int start = text.IndexOf(pattern, i, StringComparison.Ordinal);
                if (start < 0) break;
                int valStart = start + pattern.Length;
                int valEnd = text.IndexOf('"', valStart);
                if (valEnd < 0) break;
                list.Add(text.Substring(valStart, valEnd - valStart));
                i = valEnd;
            }
            return list;
        }

        public static string Escape(string s)
        {
            return (s ?? "").Replace("\\", "\\\\").Replace("\"", "\\\"");
        }
    }
}