# Launcher

Central hub for all ASTHRA mini-games. Handles player registration (name, phone, college, semester), launches each game's executable, and opens the live leaderboard.

## Setup (event PC)

```bash
# 1. pull the repo
git clone https://github.com/b1nary-0rbiter/asthra-game-launcher.git
cd asthra-game-launcher

# 2. make sure games are built (see build/README.md)
#    each games/<name>/Build/<name>.exe must exist

# 3. edit games.json with your actual exe paths (relative to launcher/)
#    the build script does this automatically

# 4. configure Firebase (see leaderboard/README.md)
#    put your firebase-config.json in leaderboard/python/

# 5. run the launcher
python3 launcher/app.py
```

## How it works

1. **Login screen** — pick a returning player (list pulled from Firestore) or register a new one (name + phone + college + semester)
2. **Game grid** — click any game tile to launch its exe with your active player name passed via `--player`
3. **Open Leaderboard** — opens the live ranking page in your browser

The active player is saved to `launcher/active_player.json` so the same PC remembers you across game launches.

## Games config

Edit `launcher/games.json`:

```json
{
  "games": [
    {
      "id": "snake",
      "name": "Snake",
      "exe": "../games/snake/Build/snake.exe",
      "color": "#00e5a0"
    }
  ]
}
```

- `exe` is relative to the `launcher/` folder
- `color` is the tile highlight colour (hex)
- the build script updates exe paths automatically after building

## Building games

See `build/README.md`. Each game must include `unity/Editor/RhythiaBuild.cs`
in its Unity project for batch builds to work.

## Files

```
launcher/
  app.py              ← main Tkinter app (run this)
  games.json          ← game list + exe paths
  active_player.json  ← current player (auto-generated, gitignored)
  player_cache.json   ← local player cache (auto-generated, gitignored)
```