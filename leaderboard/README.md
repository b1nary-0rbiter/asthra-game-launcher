# RHYTHIA Leaderboard (Firebase)

Single leaderboard for **all** games in the showcase — the 2 main games
(projector PCs) and every mini game (any PC). Backed by **Firebase Firestore**,
hit directly from each game.

## How it works

```
  Game (Unity or Python)
    │  POST /score {player, game, score}     (Firebase REST)
    ▼
  Firestore:  players/  games/  scores/  boards/
    ▼
  Leaderboard page (web/)  — reads Firestore, shows combined ranking
```

- **Player identity = name.** First time = auto-register. Later = pick the
  name from a scroll-down menu (no re-entry).
- **Scores**: every game reports to the same Firestore collection.
- **Max points**: play *all* games. Leaderboard = **sum of best score per game**
  per player. Order of play doesn't matter; replays only improve that game's best.

## Firebase setup (one-time, ~5 min)

### 1. Create the project
1. Go to https://console.firebase.google.com → **Add project** → name it
   (e.g. `rhythia-leaderboard`) → accept defaults → **Create**.
2. From the console, grab **Project settings** (gear icon) →
   **General** → scroll to **Your apps**.

### 2. Add a web app
In *Your apps* click the **`</>`** icon → name it freely (e.g. `web-leaderboard`)
→ **Register app** → copy the block:

```js
const firebaseConfig = {
  apiKey: "...",
  authDomain: "...",
  projectId: "...",
  storageBucket: "...",
  messagingSenderId: "...",
  appId: "..."
};
```

Paste the values into the config files below.

### 3. Create Firestore
1. Left sidebar → **Build** → **Firestore Database** → **Create database**.
2. Choose **Production mode** (we set proper rules in step 5).
3. Region: pick the closest (`europe-west1`, `asia-south1`, etc.) → **Enable**.

### 4. Enable anonymous auth (so games can write without sign-in UI)
1. Left sidebar → **Build** → **Authentication** → **Get started**.
2. **Sign-in method** tab → enable **Anonymous** → **Save**.
3. (Optional) **Users** tab — you'll see anonymous users appear as games run.

### 5. Security rules (IMPORTANT)
Go to **Firestore Database → Rules tab** and replace with:

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {

    // Anyone (authenticated via Firebase) can read names for the picker.
    match /players/{player} {
      allow read: if true;
      allow write: if request.auth != null;
    }

    // Game catalog: readable by all, written by no one.
    match /games/{game} {
      allow read: if true;
      allow write: if false;
    }

    // Score submissions: authenticated games may add, never edit others'.
    match /scores/{score} {
      allow read: if true;
      allow create: if request.auth != null;
      allow update, delete: if false;
    }

    // Pre-computed rankings are readable by everyone.
    match /boards/{board} {
      allow read: if true;
      allow write: if request.auth != null;
    }
  }
}
```

Publish rules. (For a purely private event you could tighten `players` reads,
but names must be listed on every PC, so keep them public-read.)

### 6. (Optional) Seed the game catalog
Run `python/seed_games.py` once (or add docs in the console) so the leaderboard
knows the games and how many points each is worth. See that file for usage.

## Configuration

Every client needs the Firebase web config. Create
`leaderboard/firebase-config.json` (never commit it):

```json
{
  "apiKey": "… from step 2 …",
  "projectId": "rhythia-leaderboard",
  "authDomain": "rhythia-leaderboard.firebaseapp.com"
}
```

Only `apiKey` + `projectId` are strictly needed for the REST calls the clients
use; `authDomain` is used by the web page if you enable password sign-in later.

> `apiKey` is not a secret — it just identifies your project. Real security is
> the rules in step 5.

## Using it from a game

### Python (pygame fallback games)
```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "leaderboard/python"))
```
Read `leaderboard/python/rhythia_client.py` — it provides:

```python
from rhythia_client import RhythiaClient

c = RhythiaClient.from_config_file("leaderboard/firebase-config.json")

# before gameplay: select the player
player = c.pick_player()          # interactive: shows saved names (scroll) or register new

# during/after gameplay: report the score
c.report_score(player, "zombie-gun", 5700)
```

- `pick_player()` lists all registered players, prints them as a numbered
  menu, and lets the user pick one or register a new name.
- `report_score()` writes the score to Firestore. Re-submitting a *lower* score
  for the same game is ignored server-side by the board; only the best counts.

### Unity (the two main games)
Copy `leaderboard/unity/RhythiaClient.cs` into your Unity project, then:

```csharp
using Rhythia;
using UnityEngine;

public class Game : MonoBehaviour {
    RhythiaClient client;

    async void Start() {
        client = await RhythiaClient.Init("...ApiKey...", "...ProjectId...");
        // Show player list from client.GetPlayers(), let player pick / add name,
        // then:
        await client.ReportScore("kingslashrelo", "zombie-gun", 5700);
    }
}
```

`RhythiaClient.cs` is plain `UnityWebRequest` — no SDK install needed.

## The leaderboard page
Open `leaderboard/web/index.html` in a browser:

- **Player selector**: type a name or pick from the saved-names scroll menu;
  stored locally so the same PC remembers who's playing.
- **Ranking**: combined across all games — sum of each player's best score per
  game, sorted descending.
- Runs off Firestore directly (CDN Firebase JS SDK), so any PC with internet
  shows the live board. Serve it with `python3 -m http.server` or point the
  projector at it.

## Notes / gotchas
- **Internet required**: Firestore is cloud — every game PC needs network
  access to Firebase. If the venue internet is flaky, this is your biggest risk
  (good reason to still test fully on the LAN before the event).
- **Anonymous auth**: each new run of a game creates a new anonymous user. The
  *player name* is the identity, not the Firebase user — that's why the picker
  exists and why rules key off `request.auth != null` only.
- **Best-per-game logic**: pure client/query-side. Ranking reads every score and
  takes the max per (player, game). Fine up to ~thousands of submissions.