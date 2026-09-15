#!/usr/bin/env bash
#
# asthra-game-launcher — Contributor CLI
#
# Runs on the contributor's PC. Automates: clone/fork check, game folder
# creation, Unity project copy (skips Library/Temp/Obj/Build), README
# generation, main README table update, branch + commit + push, PR link.
#
# Usage:
#   ./contributor_cli.sh                 # normal flow (prompts everything)
#   ./contributor_cli.sh /path/to/unity  # point at your Unity project directly
#
# Requires: bash, git. Optionally: gh (for one-click PR), python3 (not required).
#
set -euo pipefail

REPO_OWNER="b1nary-0rbiter"
REPO_NAME="asthra-game-launcher"
REPO_URL="https://github.com/${REPO_OWNER}/${REPO_NAME}.git"
EXCLUDES=(Library Temp Obj Build Logs UserSettings .vs .idea .vscode *.sln *.suo *.user)
BOLD=$'\e[1m'
OFF=$'\e[0m'
GREEN=$'\e[32m'
RED=$'\e[31m'
YELLOW=$'\e[33m'

info()  { echo "${GREEN}==>${OFF} $*"; }
warn()  { echo "${YELLOW}!! ${OFF}$*"; }
die()   { echo "${RED}ERROR:${OFF} $*" >&2; exit 1; }

# ---------- git identity check ----------
if [[ -z "$(git config user.name)" || -z "$(git config user.email)" ]]; then
  die "git user.name / user.email not set. Run:
    git config --global user.name  'Your Name'
    git config --global user.email 'you@example.com'"
fi

# ---------- working dir / clone ----------
SRC_DIR="$1"
if [[ -z "$SRC_DIR" || ! -d "$SRC_DIR" ]]; then
  read -r -e -p "Path to your Unity project folder: " SRC_DIR
  [[ -n "$SRC_DIR" && -d "$SRC_DIR" ]] || die "Not a directory: $SRC_DIR"
else
  SRC_DIR="$(cd "$SRC_DIR" && pwd)"
fi
SRC_DIR="$(cd "$SRC_DIR" && pwd)"

# ---------- find repo checkout (or clone it) ----------
WORK="$(pwd)"
ROOT=""
for d in . ./* .. ../..; do
  if [[ -d "$d/.git" ]] && git -C "$d" remote get-url origin 2>/dev/null | grep -q "asthra-game-launcher"; then
    ROOT="$(cd "$d" && pwd)"; break
  fi
done
if [[ -z "$ROOT" ]]; then
  warn "No launcher repo found here; cloning to ./${REPO_NAME}"
  git clone "$REPO_URL" "$REPO_NAME" || die "Clone failed (no network?)."
  ROOT="$PWD/$REPO_NAME"
fi
info "Using repo at: $ROOT"
cd "$ROOT"

# ---------- game name slug ----------
while :; do
  read -r -p "Game name (used for folder & table, e.g. 'zombie-gun'): " GAME
  GAME="$(echo "$GAME" | tr '[:upper:]' '[:lower:]' | tr -c 'a-z0-9-' '-')"
  GAME="$(echo "$GAME" | sed 's/-\+/-/g; s/^-\+//; s/-\+$//')"
  [[ -n "$GAME" ]] && break
done
FOLDER="games/$GAME"
[[ -e "$FOLDER" ]] && die "Folder already exists: $FOLDER"

# ---------- game metadata ----------
read -r -p "Your GitHub username (for the table): " USERNAME
[[ -n "$USERNAME" ]] || USERNAME="@yourname"
read -r -p "What is the game? (1-line description): " DESC
read -r -p "Controls (how to play): " CONTROLS
read -r -p "Unity version [2022.3]: " UNITY
UNITY="${UNITY:-2022.3}"

# ---------- copy Unity project, excluding build junk ----------
info "Copying Unity project from $SRC_DIR"
mkdir -p "$FOLDER"
# copy the project's own dotfile defaults (e.g. .gitignore) if it has any
cp -a "$SRC_DIR"/.gitignore "$FOLDER"/ 2>/dev/null || true
for item in "$SRC_DIR"/* "$SRC_DIR"/.[!.]*; do
  [[ -e "$item" ]] || continue
  # never copy the source's own .git
  [[ "$(basename "$item")" == ".git" ]] && continue
  base="$(basename "$item")"
  skip=""
  for x in "${EXCLUDES[@]}"; do
    [[ "$base" == "$x" ]] && skip=1 && break
  done
  [[ -n "$skip" ]] && { warn "Skipping $base"; continue; }
  cp -a "$item" "$FOLDER"/ 2>/dev/null || true
done
# remove any build junk that got in anyway
for x in Library Temp Obj Build Logs; do
  [[ -d "$FOLDER/$x" ]] && { rm -rf "$FOLDER/$x"; warn "Removed stray $FOLDER/$x"; }
done
rm -f "$FOLDER"/*.sln "$FOLDER"/*.suo "$FOLDER"/*.user 2>/dev/null || true
# fail iff nothing landed in the folder
if [[ -z "$(ls -A "$FOLDER")" ]]; then
  warn "Nothing copied — is $SRC_DIR a Unity project?"
fi

# ---------- per-game README ----------
{
  echo "# $GAME"
  echo
  [[ -n "$DESC" ]] && echo "$DESC" && echo
  echo "## Controls"
  echo
  [[ -n "$CONTROLS" ]] && echo "$CONTROLS" || echo "TODO"
  echo
  echo "## Made by"
  echo
  echo "${USERNAME}"
} > "$FOLDER/README.md"

# ---------- add row to main README table ----------
if grep -q "| $GAME |" README.md; then
  warn "Row for '$GAME' already in table; leaving it."
else
  LINE="| $GAME | $USERNAME | $UNITY | \`$FOLDER\` |"
  # insert directly after the last table row (a line beginning with '|')
  awk -v insert="$LINE" '
    NR==1 { buf=$0; next }
    { buf=buf"\n"$0 }
    END {
      n=split(buf, lines, "\n")
      last=0
      for (i=1;i<=n;i++) if (lines[i] ~ /^\|.*\|$/) last=i
      if (last==0) { print buf"\n"insert; exit }
      for (i=1;i<=last;i++) print lines[i]
      print insert
      for (i=last+1;i<=n;i++) print lines[i]
    }' README.md > README.md.tmp && mv README.md.tmp README.md
  info "Added '$GAME' to README table"
fi

# ---------- branch + commit + push ----------
BRANCH="add-${GAME}"
git checkout -b "$BRANCH" >/dev/null 2>&1 || { git checkout -b "$BRANCH" origin/main; }
git add "$FOLDER" README.md
git commit -m "Add ${GAME} game" >/dev/null || die "Nothing to commit"
info "Committed on branch '$BRANCH'"

if git push -u origin "$BRANCH" 2>/dev/null; then
  info "Pushed. Open your PR:"
  echo "  https://github.com/${REPO_OWNER}/${REPO_NAME}/pull/new/${BRANCH}"
  if command -v gh >/dev/null 2>&1; then
    echo
    read -r -n1 -p "Open PR now with gh? [y/N] " Y
    echo
    [[ "$Y" =~ ^[Yy]$ ]] && gh pr create --fill
  fi
else
  warn "Push failed. You may need permission as a collaborator, or a fork."
  echo "   → Commit is ready locally on '$BRANCH'. Push, then open a PR."
fi

echo
info "Done. Game folder:      $FOLDER"
info "Game README:           $FOLDER/README.md"
info "Per-game rules:        see CONTRIBUTING.md"