# Nova Drift

Mini game for the ASTHRA Launcher.

> Replace this section — add your game: what it is, how to play, controls.

## Requirements (before pushing)

- [ ] Unity project lives here (Assets/, ProjectSettings/, Packages/)
- [ ] `Assets/Editor/RhythiaBuild.cs` present (batch builds)
- [ ] `Assets/RhythiaClient.cs` present (leaderboard reporting)
- [ ] Reads player CLI args: `--player <name> --phone <phone> --college <college> --semester <sem>`
- [ ] Calls `report_score(player, "nova-drift", finalScore)` on game over
- [ ] Builds via `python3 build/build_all.py --games nova-drift`
- [ ] No `Library/ Temp/ Obj/ Build/` committed; `.meta` files committed
- [ ] No `firebase-config.*` committed