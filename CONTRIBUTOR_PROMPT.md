# CONTRIBUTOR PROMPT — give this to your AI agent

You are an AI coding agent helping build a **mini-game** for the ASTHRA 2026
tech fest (RHYTHIA). The game runs on a Windows event PC and is launched from a
local hub called the ASTHRA Launcher.

Your job is ONLY to build the game itself. Do NOT worry about (and do NOT build,
do NOT touch, do NOT research):

- The leaderboard
- Firebase / databases / the internet
- The ASTHRA Launcher app
- Git, GitHub, pull requests, or pushing code
- Player registration, accounts, or logins
- Any networking, API calls, or web servers

Everything you are told NOT to touch above is already handled by the fest team.
Another agent will integrate your game after you are done. That integration ONLY
requires the three points listed below — get those right and you're done.

---

## Deliverable

A complete, playable game in a folder, using **one** of these stacks:

1. **Unity** — a full Unity project (Assets/, ProjectSettings/, Packages/)
2. **Python + pygame** — a single `.py` game file + a `requirements.txt`

Choose the one you are capable of. If you choose Unity, you can use the Unity
engine freely (sprites, scenes, physics, UI, audio).

## What the game must do

- Be a small, polished, single-session arcade-style mini game (one round = one play)
- Be playable entirely with keyboard and/or mouse on a Windows PC at a fest booth
- Have a clear start, a clear "game over" moment, and a final score
- Run standalone (no assets or services downloaded at runtime)
- Look sharp: dark futuristic theme, readable UI, no placeholder white textures
  (use simple geometry, gradients, or a consistent palette)
- Vanilla / zero external packages. Unity store assets, paid plugins, or pip
  modules beyond pygame are NOT allowed — keep it dependency-free
- No internet, no licensing, no accounts

## The THREE integration points (critical — follow exactly)

Another agent will add the leaderboard wiring in these three places. Make them
easy to find by naming everything exactly as specified:

1. **Game over moment**
   - Create a public method or event named **`GameOver`** that fires once when
     the game ends. In Unity: a public method on your main manager script
     (e.g. `public void GameOver()`). In pygame: a function `def game_over():`.
   - The score MUST be readable at that exact moment from a public integer
     called **`Score`** (Unity: `public int Score;` on the same script).
   - Call/raise `GameOver` AFTER the final score is already set. Do not reset
     the score after game over.

2. **Player name input (CLI argument)**
   - The player's identity is passed to your game as a command-line argument:
     `--player <NAME>`
   - Read it at startup and store it in a public string called **`PlayerName`**
     (Unity) or a global `player_name` (pygame). If the argument is missing,
     fall back to the window title only — do NOT show your own name-entry UI.
   - In Unity: `string[] args = System.Environment.GetCommandLineArgs();` then
     find `--player` and take the next value.

3. **No exit without cleanup**
   - Do NOT build or reference any of the excluded topics above. Your game must
     never refuse to run offline.

## What the integration agent will add (for your awareness only)

```csharp
// Unity — added after GameOver() fires, using your Score and PlayerName:
RhythiaClient.Instance.ReportScore(PlayerName, "YOUR-GAME-ID", Score);
```

```python
# pygame — added in game_over():
c.report_score(player_name, "YOUR-GAME-ID", score)
```

Your job: make sure `GameOver` and `Score` (Unity) or `game_over` / `score` /
`player_name` (pygame) exist exactly as named and are already public when the
game ends.

## Rules

- Zero-dependency, offline, one-click run
- Keep it under ~10 minutes per play session
- Dark/neon aesthetic, monospace fonts OK
- No copyrighted art or audio
- If something isn't specified, use your best judgement — don't ask questions

## When you are done

- Put Unity project (or `.py` + `requirements.txt`) in a single folder named
  with the game's id, e.g. `my-game/`
- Write a short `README.md` in that folder: game name, controls, how to run
  (Unity: open folder → File → Build; pygame: `pip install pygame && python game.py`)
- State clearly: "Integration points ready: GameOver + Score + --player implemented"
- Do NOT compress to a weird archive — a normal folder or .zip is fine

You are done when the game is playable, the three integration points exist with
those exact names, and the README is written. Do not add anything else.