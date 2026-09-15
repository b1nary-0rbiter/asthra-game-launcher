# Batch build

Build all Unity games in the repo from a single command.

## Prerequisites

- **Unity Editor** installed via Unity Hub (any 2021+ version)
- Each game project must have `Assets/Editor/RhythiaBuild.cs` (provided in
  `unity/Editor/` — copy it into each game's `Assets/Editor/` folder)

## Usage

```bash
# auto-detect Unity and build all games → games/<name>/Build/<name>.exe
python3 build/build_all.py

# build only specific games
python3 build/build_all.py --games snake zombie-gun

# build Linux instead of Windows
python3 build/build_all.py --linux

# list discoverable games (checks for .unity scenes + build script)
python3 build/build_all.py --list
```

## How it works

1. Scans `games/` for folders containing `.unity` scene files
2. Runs `Unity -batchmode -quit -executeMethod Rhythia.Build.BuildWindows`
3. Produces `games/<id>/Build/<id>.exe` (or `.x86_64` for Linux)
4. Updates `launcher/games.json` exe paths automatically

## Output

```
build/build_all.py
games/
  snake/
    Build/
      snake.exe        ← the built game (gitignored)
      build.log        ← Unity build log
  zombie-gun/
    Build/
      zombie-gun.exe
```

Build artifacts are gitignored — only source is committed.

## Troubleshooting

- **"no game projects found"**: ensure `games/<name>/Assets/Scenes/*.unity` exists
- **"build FAILED"**: check `games/<name>/Build/build.log` for Unity errors
- **Unity not found**: set `UNITY_PATH=/path/to/Unity` before running
- **missing RhythiaBuild.cs**: copy `unity/Editor/RhythiaBuild.cs` into the game's
  `Assets/Editor/` folder (create it if needed)