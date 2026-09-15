#!/usr/bin/env python3
"""
Batch-build all Unity games in the repo via Unity CLI.

    python3 build/build_all.py                          # build all
    python3 build/build_all.py --games zombie-gun snake # build specific
    python3 build/build_all.py --list                   # list available games

Requires Unity Editor installed at ~/Unity/Hub/Editor/<version>/Editor/Unity
or set UNITY_PATH env var to the Unity executable.

Each game project must contain Assets/Editor/RhythiaBuild.cs (provided in
this repo under unity/Editor/). The build produces:
    games/<name>/Build/<name>.exe    (Windows 64-bit)
    games/<name>/Build/<name>.x86_64 (Linux)
"""
import argparse, glob, json, os, platform, subprocess, sys, time

ROOT   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAMES  = os.path.join(ROOT, "games")
CONFIG = os.path.join(ROOT, "launcher", "games.json")

def find_unity():
    """Auto-detect Unity Editor path."""
    env = os.environ.get("UNITY_PATH")
    if env and os.path.exists(env):
        return env
    hub = os.path.expanduser("~/Unity/Hub/Editor")
    if os.path.isdir(hub):
        versions = sorted(os.listdir(hub), reverse=True)
        for v in versions:
            for ext in ["Editor/Unity", "Editor/Unity.exe"]:
                p = os.path.join(hub, v, ext)
                if os.path.isfile(p):
                    return p
    return "Unity"  # hope it's on PATH

def discover_games():
    """Find game folders that have a .unity scene in Assets or Scenes."""
    found = []
    if not os.path.isdir(GAMES):
        return found
    for name in sorted(os.listdir(GAMES)):
        proj = os.path.join(GAMES, name)
        if not os.path.isdir(proj):
            continue
        scenes = (glob.glob(os.path.join(proj, "Assets", "Scenes", "*.unity"))
                + glob.glob(os.path.join(proj, "Assets", "**", "*.unity"), recursive=True))
        has_build_script = os.path.exists(os.path.join(proj, "Assets", "Editor", "RhythiaBuild.cs"))
        if scenes:
            found.append({"id": name, "path": proj, "scenes": len(scenes),
                          "build_script": has_build_script})
    return found

def build_game(unity, game, platform_flag="-buildWindows64Player", ext=".exe"):
    """Invoke Unity batchmode to build one game."""
    out_dir = os.path.join(game["path"], "Build")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, game["id"] + ext)
    if platform_flag == "-buildLinux64Player":
        out_path = os.path.join(out_dir, game["id"] + ".x86_64")

    log = os.path.join(out_dir, "build.log")
    cmd = [
        unity, "-batchmode", "-quit", "-nographics",
        "-projectPath", game["path"],
        "-executeMethod", "Rhythia.Build.BuildWindows",
        "-logFile", log,
    ]
    print(f"  building {game['id']} → {out_path}")
    t0 = time.time()
    r = subprocess.run(cmd, capture_output=True, timeout=600)
    elapsed = time.time() - t0
    ok = os.path.isfile(out_path) and os.path.getsize(out_path) > 1024
    if ok:
        mb = os.path.getsize(out_path) / 1024 / 1024
        print(f"  ✓ {game['id']}: {mb:.1f} MB in {elapsed:.0f}s")
    else:
        print(f"  ✗ {game['id']}: build FAILED ({elapsed:.0f}s) — check {log}")
    return ok

def update_launcher_config(built_games):
    """Overwrite launcher/games.json exe paths to point at built files."""
    if not os.path.exists(CONFIG):
        return
    with open(CONFIG) as f:
        cfg = json.load(f)
    for g in cfg.get("games", []):
        exe = os.path.join(GAMES, g["id"], "Build", g["id"] + ".exe")
        if os.path.isfile(exe):
            rel = os.path.relpath(exe, os.path.dirname(CONFIG))
            g["exe"] = rel.replace("\\", "/")
    with open(CONFIG, "w") as f:
        json.dump(cfg, f, indent=2)
    print(f"  updated {CONFIG}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true", help="list discoverable games")
    ap.add_argument("--games", nargs="*", help="game id(s) to build (default: all)")
    ap.add_argument("--linux", action="store_true", help="build Linux instead of Windows")
    args = ap.parse_args()

    games = discover_games()
    if not games:
        print("no game projects found in games/")
        sys.exit(1)

    if args.list:
        print("available games:")
        for g in games:
            marker = "✓" if g["build_script"] else "✗ no RhythiaBuild.cs"
            print(f"  {g['id']:20s} scenes={g['scenes']}  {marker}")
        sys.exit(0)

    if args.games:
        games = [g for g in games if g["id"] in args.games]
        if not games:
            print("none of those games found")
            sys.exit(1)

    missing = [g["id"] for g in games if not g["build_script"]]
    if missing:
        print("games missing RhythiaBuild.cs (copy unity/Editor/RhythiaBuild.cs into them first):")
        for m in missing:
            print(f"  - {m}")
        print()
        # continue anyway — Unity's default build settings may work

    unity = find_unity()
    print(f"Unity: {unity}")
    print(f"building {len(games)} game(s)…\n")

    ok = 0
    for g in games:
        flag = "-buildLinux64Player" if args.linux else "-buildWindows64Player"
        ext  = ".x86_64" if args.linux else ".exe"
        if build_game(unity, g, flag, ext):
            ok += 1

    print(f"\ndone: {ok}/{len(games)} built successfully")
    if ok:
        update_launcher_config(games)

if __name__ == "__main__":
    main()