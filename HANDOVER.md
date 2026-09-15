# ASTHRA Game Launcher — Handover (read me first)

You are the new owner/manager of the mini-games + leaderboard for the ASTHRA fest
(Sep 17, SJCET Pala). This document tells you exactly what you do. Contributors
do almost nothing — you run the project.

---

## 1. The two repos

| Repo | What it is | Who owns it |
|------|-----------|-------------|
| `github.com/b1nary-0rbiter/asthra-game-launcher` | mini-games + launcher + leaderboard + build tooling | `b1nary-0rbiter` (you'll manage invites from this account) |
| `github.com/b1nary-0rbiter/Rhythia` | the two MAIN games (separate project) | `b1nary-0rbiter` |

You work mostly in `asthra-game-launcher`.

---

## 2. What contributors must do (their ENTIRE job)

1. Build their own game in Unity (or pygame for Python games).
2. Give you the project — their own GitHub repo link, or a `.zip` / Google Drive.
3. Done. They do NOT need to know git, leadersboards, Firebase, or the launcher.

If a contributor wants to push to the repo themselves (only if they're comfortable):
add them at GitHub → repo → **Settings → Collaborators**. Otherwise they just
send you the files.

## 3. Your job per game

For every game you receive:

1. **Get their project** into `games/<name>/` in the launcher repo.
   (They pushed → `git pull`. They sent a link/zip → clone/download and copy it in.)
2. **Wire the leaderboard into their game code.** One file is already in each
   game folder: `Assets/RhythiaClient.cs` (don't delete it). You must add TWO
   things inside their scripts:
   - read the player name the launcher passes: `--player <name>` CLI arg
   - at game over, call `RhythiaClient.report_score(playerName, "<game-id>", finalScore)`
3. **Build the exe:**
   ```bash
   python3 build/build_all.py --games <name>
   ```
   (needs the game's `Assets/Editor/RhythiaBuild.cs` present, which the scaffold provides)
4. **Test:** run the exe, play, confirm the score lands on the leaderboard page.
5. **Keep `Library/ Temp/ Obj/ Build/` and `firebase-config.*` OUT of git.**
   The `.gitignore` already blocks them — don't force-add them.

## 4. Leaderboard / Firebase (yours, one-time)

Full step-by-step is in `leaderboard/README.md`. Short version:

1. Create a Firebase project at console.firebase.google.com
2. Enable **Firestore** + **Anonymous auth**
3. Copy `leaderboard/web/firebase-config.js.example` → `firebase-config.js` and
   `leaderboard/python/firebase-config.json.example` → `firebase-config.json`,
   paste your project's web config (API key, project id, app id) into both.
4. Apply the Firestore security rules from `leaderboard/README.md`.
5. `python3 leaderboard/python/seed_games.py`
6. On every event PC the `firebase-config.*` files must exist where the launcher
   expects them.

## 5. Event day

1. On a PC with Unity: `python3 build/build_all.py` → builds every game exe.
2. Assign stations: edit `launcher/pc.json` on each PC so it only shows that
   station's game(s), e.g. `{ "onlyGames": ["nova-drift"] }`.
3. Start the launcher: `python3 launcher/app.py`.
4. Players register (name/phone/college/semester) once → logged-in state saved.
   Games the station runs will report their scores automatically.

## 6. Current state at handover

- ✅ Done: repo scaffold, leaderboard backend + Python/Unity/web clients,
  batch-build tooling, launcher app, `games/nova-drift/` placeholder slot
  (Nova Drift contributor: @Dintodj).
- 🔲 Pending on you: receive game projects from contributors, wire each game's
  `report_score`, create the Firebase project + configs, test builds, station
  assignment (`pc.json`), event-day dry run.

## 7. Gotchas

- `RhythiaClient.cs` alone does nothing until the game actually calls
  `report_score` at game over — that call is the whole leaderboard.
- Pygame games use `leaderboard/python/rhythia_client.py` instead of the C# client.
- Offline/event PCs without internet: the launcher still logs players in from
  cache, but **scores need internet** to reach Firestore.
- Never commit `firebase-config.*` or private keys.

---

Questions → check the repo's `README.md`, `leaderboard/README.md`,
`build/README.md`, `launcher/README.md`, and `CONTRIBUTING.md` in order.