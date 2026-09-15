#!/usr/bin/env python3
"""
seed_games.py — populate the `games` catalog in Firestore.

The leaderboard uses games/ only to *validate* that every game was played
(sum of best per game == max points). Run once after Firebase setup:

    python3 seed_games.py firebase-config.json

Add/remove game ids here to match the ids your games call report_score with.
"""
import json
import sys

from rhythia_client import RhythiaClient

GAMES = [
    # (game_id, display name, max possible points)
    ("zombie-gun", "Zombie Gun", 5000),
    ("rhythia-main", "Rhythia (main)", 5000),
    # mini games — add as they join the launcher repo
    ("snake", "Snake", 1000),
]


def main():
    cfg = sys.argv[1] if len(sys.argv) > 1 else "firebase-config.json"
    c = RhythiaClient.from_config_file(cfg)
    base, headers = c._firestore()

    for game_id, name, max_points in GAMES:
        doc_id = game_id
        payload = {"fields": {
            "id":   {"stringValue": game_id},
            "name": {"stringValue": name},
            "max":  {"doubleValue": float(max_points)},
        }}
        url = f"{base}/games?documentId={doc_id}&allowMissing=true"
        try:
            import urllib.request
            req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                         headers={**headers, "Content-Type": "application/json"},
                                         method="PATCH")
            urllib.request.urlopen(req)
            print("ok:", game_id)
        except Exception as e:
            print("fail:", game_id, e)


if __name__ == "__main__":
    main()