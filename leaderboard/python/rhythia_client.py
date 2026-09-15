#!/usr/bin/env python3
"""
rhythia_client.py — Firestore-backed leaderboard client for RHYTHIA games.

Zero-dependency (stdlib only: urllib). Use from any Python/pygame game:

    from rhythia_client import RhythiaClient

    c = RhythiaClient.from_config_file("../firebase-config.json")
    player = c.pick_player()              # saved-name scroll menu or register
    c.report_score(player, "zombie-gun", 5700)

Firebase REST endpoints used (no Firebase SDK needed):
  - anonymous sign-in:  identitytoolkit.googleapis.com/v1/accounts:signUp
  - firestore:          firestore.googleapis.com/v1/projects/{pid}/databases/(default)/documents
Requires: internet + a Firebase project set up per leaderboard/README.md.
"""

import json
import os
import time
import urllib.request
import urllib.parse
import urllib.error

FIREBASE_AUTH_URL = "https://identitytoolkit.googleapis.com/v1/accounts:signUp"


class RhythiaClient:
    """Minimal REST client for the shared leaderboard."""

    def __init__(self, api_key, project_id):
        self.api_key = api_key
        self.project_id = project_id
        self._id_token = None

    # ---------- construction ----------

    @classmethod
    def from_config_file(cls, path="firebase-config.json"):
        with open(path) as f:
            cfg = json.load(f)
        return cls(cfg["apiKey"], cfg["projectId"])

    # ---------- auth ----------

    def _firestore(self):
        """Anonymous-signed Firestore REST URL prefix (lazy)."""
        if not self._id_token:
            body = json.dumps({"returnSecureToken": True}).encode()
            url = FIREBASE_AUTH_URL + "?key=" + self.api_key
            with urllib.request.urlopen(urllib.request.Request(url, body, {"Content-Type": "application/json"})) as r:
                self._id_token = json.load(r)["idToken"]
        return ("https://firestore.googleapis.com/v1/projects/" + self.project_id +
                "/databases/(default)/documents"), {"Authorization": "Bearer " + self._id_token}

    @staticmethod
    def _get(url, headers):
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as r:
            return json.load(r)

    @staticmethod
    def _post(url, headers, payload):
        req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                     headers={**headers, "Content-Type": "application/json"})
        with urllib.request.urlopen(req) as r:
            return json.load(r)

    @staticmethod
    def _patch(url, headers, payload):
        req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                     headers={**headers, "Content-Type": "application/json"},
                                     method="PATCH")
        with urllib.request.urlopen(req) as r:
            return json.load(r)

    # ---------- players ----------

    def get_players(self):
        """Return sorted list of registered player names."""
        base, h = self._firestore()
        try:
            data = self._get(base + "/players?pageSize=1000", h)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return []
            raise
        names = []
        for doc in data.get("documents", []):
            names.append(doc["fields"].get("name", {}).get("stringValue", doc["name"].rsplit("/", 1)[-1]))
        return sorted(names)

    def register_player(self, name):
        """Idempotently register a player (already exists = fine)."""
        name = name.strip()[:30]
        if not name:
            raise ValueError("name must not be empty")
        base, h = self._firestore()
        doc_id = urllib.parse.quote(name, safe="")
        payload = {"fields": {"name": {"stringValue": name}, "createdAt": {"stringValue": str(int(time.time()))}}}
        url = f"{base}/players?documentId={doc_id}&allowMissing=true"
        try:
            self._patch(url, h, payload)   # create-if-missing
        except urllib.error.HTTPError:
            pass                            # already registered -> fine
        return name

    def pick_player(self, prompt="Select player"):
        """Interactive picker: scroll menu of saved names, or register a new one.

        Returns the chosen player name.
        """
        players = self.get_players()
        print(f"\n  {prompt}")
        if players:
            print("  (type a number, or a NEW name to register)")
            for i, p in enumerate(players, 1):
                print(f"    {i:3d}) {p}")
        else:
            print("  (no saved players yet — enter your name to register)")
        while True:
            choice = input("  > ").strip()
            if choice:
                try:
                    idx = int(choice)
                    if 1 <= idx <= len(players):
                        return self.register_player(players[idx - 1])
                except ValueError:
                    pass
                return self.register_player(choice)

    # ---------- scores ----------

    def report_score(self, player, game_id, score):
        """Write a score submission. Only the best per (player, game) counts."""
        if not isinstance(score, (int, float)):
            raise TypeError("score must be a number")
        base, h = self._firestore()
        payload = {
            "fields": {
                "player":   {"stringValue": player},
                "game":     {"stringValue": game_id},
                "score":    {"doubleValue": float(score)},
                "ts":       {"stringValue": str(int(time.time()))},
            }
        }
        try:
            self._post(base + "/scores", h, payload)
        except urllib.error.HTTPError as e:
            # Rules disallow edits; a collision shouldn't happen with auto IDs.
            raise RuntimeError("score rejected: " + str(e)) from e

    def get_scores(self):
        """Return list of {player, game, score} raw submissions (best computed by caller)."""
        base, h = self._firestore()
        try:
            data = self._get(base + "/scores?pageSize=1000", h)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return []
            raise
        out = []
        for doc in data.get("documents", []):
            f = doc["fields"]
            out.append({
                "player": f["player"]["stringValue"],
                "game":   f["game"]["stringValue"],
                "score":  f["score"].get("doubleValue", f["score"].get("integerValue", 0)),
            })
        return out

    # ---------- leaderboard ----------

    def get_leaderboard(self):
        """Compute combined ranking: sum of best score per (player, game), desc.

        Returns list of dicts: {player, total, games: {game: best}}.
        """
        best = {}
        for s in self.get_scores():
            key = (s["player"], s["game"])
            if key not in best or s["score"] > best[key]:
                best[key] = s["score"]
        rows = {}
        for (player, game), score in best.items():
            rows.setdefault(player, {}).setdefault("games", {})[game] = score
        result = []
        for player, data in rows.items():
            games = data["games"]
            result.append({"player": player, "total": round(sum(games.values())),
                           "games": games})
        return sorted(result, key=lambda r: r["total"], reverse=True)


# ---------- CLI smoke test ----------
#   python3 rhythia_client.py [config.json]
if __name__ == "__main__":
    cfg = sys.argv[1] if len(sys.argv) > 1 else "firebase-config.json"
    c = RhythiaClient.from_config_file(cfg)
    print("Players:", c.get_players())
    print("Leaderboard:", c.get_leaderboard())