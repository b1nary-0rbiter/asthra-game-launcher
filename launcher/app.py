#!/usr/bin/env python3
"""
Launcher for all ASTHRA mini-games + leaderboard.
Two screens:  Login/Registration → Game grid (launch exes, open leaderboard).
Reads games.json for the game list; writes active_player.json for games to pick up.

    python3 launcher/app.py

Requires: python3, tkinter, internet for Firebase player list (falls back to
local cache from the last successful fetch).
"""
import json, os, sys, time, threading, subprocess, webbrowser
import tkinter as tk
from tkinter import ttk

ROOT = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(ROOT, "games.json")
ACTIVE  = os.path.join(ROOT, "active_player.json")
PCACHE  = os.path.join(ROOT, "player_cache.json")

# ── Firebase read (try; fail → offline cache) ───────────────────────────────

def _load_firebase_config():
    """Load Firebase config from the leaderboard folder (if present)."""
    for rel in ["../leaderboard/python/firebase-config.json", "firebase-config.json"]:
        p = os.path.join(ROOT, rel)
        if os.path.exists(p):
            with open(p) as f:
                return json.load(f)
    return None

def _anonymously_auth(cfg):
    """Get an anonymous Firebase Auth idToken via REST."""
    import urllib.request, urllib.error
    url = "https://identitytoolkit.googleapis.com/v1/accounts:signUp?key=" + cfg["apiKey"]
    body = json.dumps({"returnSecureToken": True}).encode()
    req = urllib.request.Request(url, body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=8) as r:
        return json.load(r)["idToken"]

def _fetch_players(cfg, token):
    """GET all docs in players/ collection."""
    import urllib.request
    url = ("https://firestore.googleapis.com/v1/projects/" + cfg["projectId"]
           + "/databases/(default)/documents/players?pageSize=500")
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + token})
    with urllib.request.urlopen(req, timeout=8) as r:
        data = json.load(r)
    players = []
    for doc in data.get("documents", []):
        f = doc.get("fields", {})
        players.append({
            "name":     f.get("name", {}).get("stringValue", doc["name"].rsplit("/", 1)[-1]),
            "phone":    f.get("phone", {}).get("stringValue", ""),
            "college":  f.get("college", {}).get("stringValue", ""),
            "semester": f.get("semester", {}).get("stringValue", ""),
        })
    players.sort(key=lambda p: p["name"].lower())
    return players

def fetch_registered_players():
    """Fetch from Firestore; on failure use local cache from last successful fetch."""
    try:
        cfg = _load_firebase_config()
        if not cfg:
            raise RuntimeError("no firebase config")
        token = _anonymously_auth(cfg)
        players = _fetch_players(cfg, token)
        # cache locally
        with open(PCACHE, "w") as f:
            json.dump(players, f, indent=2)
        return players
    except Exception:
        if os.path.exists(PCACHE):
            with open(PCACHE) as f:
                return json.load(f)
        return []

# ── Active player persistence ───────────────────────────────────────────────

def _save_active(player):
    with open(ACTIVE, "w") as f:
        json.dump(player, f, indent=2)

def _load_active():
    if os.path.exists(ACTIVE):
        with open(ACTIVE) as f:
            return json.load(f)
    return None

def _clear_active():
    if os.path.exists(ACTIVE):
        os.remove(ACTIVE)

# ── Write a new player to Firestore (best-effort) ──────────────────────────

def _register_player(player):
    """PUT/PATCH new player doc into Firestore, ignoring errors."""
    try:
        cfg = _load_firebase_config()
        if not cfg:
            raise RuntimeError("no firebase config")
        token = _anonymously_auth(cfg)
        import urllib.request
        doc_id = player["name"].replace("/", "_")[:40]
        payload = {"fields": {
            "name":     {"stringValue": player["name"]},
            "phone":    {"stringValue": player.get("phone", "")},
            "college":  {"stringValue": player.get("college", "")},
            "semester": {"stringValue": player.get("semester", "")},
            "createdAt":{"stringValue": str(int(time.time()))},
        }}
        url = ("https://firestore.googleapis.com/v1/projects/" + cfg["projectId"]
               + "/databases/(default)/documents/players?documentId=" + doc_id
               + "&allowMissing=true")
        req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                     headers={"Authorization": "Bearer " + token,
                                              "Content-Type": "application/json"},
                                     method="PATCH")
        urllib.request.urlopen(req, timeout=8)
    except Exception:
        pass  # offline or error → local mode; the player exists locally

# ── GUI ─────────────────────────────────────────────────────────────────────

FONT        = ("Courier New", 11)
FONT_TITLE  = ("Courier New", 18, "bold")
FONT_SMALL  = ("Courier New", 9)
BG          = "#0a0c10"
FG          = "#e0e6ee"
SURF        = "#141820"
ACCENT      = "#00e5a0"
BORDER      = "#1e2630"

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ASTHRA Launcher")
        self.configure(bg=BG)
        self.geometry("820x520")
        self.resizable(False, False)
        self.player = _load_active()
        self.games  = self._load_games()
        self._players_cache = []
        self._shown_games = False
        self.after(200, self._boot)

    def _load_games(self):
        with open(CONFIG) as f:
            return json.load(f).get("games", [])

    def _boot(self):
        if self.player:
            self._show_games()
        else:
            self._show_login()

    # ── Login / Register screen ──────────────────────────────────────────

    def _show_login(self):
        self._clear()
        frame = tk.Frame(self, bg=BG, padx=40, pady=30)
        frame.pack(fill="both", expand=True)
        tk.Label(frame, text="ASTHRA GAMES", font=FONT_TITLE,
                 bg=BG, fg=ACCENT).pack(pady=(0, 20))
        tk.Label(frame, text="Select a player or register a new one:",
                 font=FONT_SMALL, bg=BG, fg="#4a5468").pack(anchor="w")

        # registered list
        list_frame = tk.Frame(frame, bg=SURF, bd=1, relief="solid")
        list_frame.pack(fill="x", pady=(8, 12))
        tk.Label(list_frame, text="REGISTERED PLAYERS", font=FONT_SMALL,
                 bg=SURF, fg="#4a5468").pack(anchor="w", padx=8, pady=(6, 2))
        self._lb = tk.Listbox(list_frame, bg=BG, fg=FG, font=FONT,
                              selectbackground=ACCENT, selectforeground="#071009",
                              height=6, activestyle="none", bd=0,
                              highlightthickness=0, relief="flat")
        self._lb.pack(fill="x", padx=6, pady=(0, 6))
        self._load_player_list()

        # fields
        fields = [("Name *", "name"), ("Phone", "phone"),
                  ("College", "college"), ("Semester", "semester")]
        self._fields = {}
        for label, key in fields:
            row = tk.Frame(frame, bg=BG)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=label, font=FONT_SMALL, bg=BG, fg="#4a5468",
                     width=10, anchor="w").pack(side="left")
            ent = tk.Entry(row, bg=SURF, fg=FG, font=FONT, insertbackground=FG,
                           relief="flat", bd=4)
            ent.pack(side="left", fill="x", expand=True, padx=(0, 0))
            self._fields[key] = ent

        # buttons
        btn_frame = tk.Frame(frame, bg=BG)
        btn_frame.pack(fill="x", pady=(14, 0))
        tk.Button(btn_frame, text="Login as selected", bg=ACCENT, fg="#071009",
                  font=FONT, relief="flat", activebackground="#00c88d",
                  command=self._login_selected).pack(side="left", padx=(0, 8))
        tk.Button(btn_frame, text="Register new player", bg=BORDER, fg=FG,
                  font=FONT, relief="flat", activebackground="#2a3242",
                  command=self._register_new).pack(side="left")

        # status
        self._status = tk.Label(frame, text="", font=FONT_SMALL,
                                bg=BG, fg="#ff6b35", anchor="w")
        self._status.pack(fill="x", pady=(12, 0))

    def _load_player_list(self):
        self._lb.delete(0, tk.END)
        def _fetch():
            self._players_cache = fetch_registered_players()
            self.after(0, self._populate_lb)
        threading.Thread(target=_fetch, daemon=True).start()
        # immediate local cache pop
        if os.path.exists(PCACHE):
            with open(PCACHE) as f:
                self._players_cache = json.load(f)
            self._populate_lb()

    def _populate_lb(self):
        self._lb.delete(0, tk.END)
        for p in self._players_cache:
            label = p["name"]
            if p.get("college"):
                label += f"  ({p['college']})"
            self._lb.insert(tk.END, label)

    def _selected_player(self):
        sel = self._lb.curselection()
        if not sel:
            return None
        idx = sel[0]
        return self._players_cache[idx] if idx < len(self._players_cache) else None

    def _login_selected(self):
        p = self._selected_player()
        if not p:
            self._status.config(text="Select a player from the list first.")
            return
        self.player = p
        _save_active(p)
        self._show_games()

    def _register_new(self):
        name = self._fields["name"].get().strip()
        if not name:
            self._status.config(text="Name is required.")
            return
        self.player = {
            "name":     name,
            "phone":    self._fields["phone"].get().strip(),
            "college":  self._fields["college"].get().strip(),
            "semester": self._fields["semester"].get().strip(),
        }
        _save_active(self.player)
        threading.Thread(target=_register_player, args=(self.player,), daemon=True).start()
        self._show_games()

    # ── Games screen ─────────────────────────────────────────────────────

    def _show_games(self):
        if self._shown_games:
            return
        self._shown_games = True
        self._clear()

        frame = tk.Frame(self, bg=BG, padx=40, pady=24)
        frame.pack(fill="both", expand=True)

        # header
        hdr = tk.Frame(frame, bg=BG)
        hdr.pack(fill="x", pady=(0, 16))
        tk.Label(hdr, text="ASTHRA GAMES", font=FONT_TITLE,
                 bg=BG, fg=ACCENT).pack(side="left")
        player_str = self.player["name"]
        if self.player.get("college"):
            player_str += f"  •  {self.player['college']}"
        tk.Label(hdr, text=player_str, font=FONT_SMALL,
                 bg=BG, fg="#4a5468").pack(side="right")

        # game grid
        grid = tk.Frame(frame, bg=BG)
        grid.pack(fill="both", expand=True)
        cols = max(2, (len(self.games) + 1) // 2)
        grid.columnconfigure(list(range(cols)), weight=1, uniform="g")
        for i, g in enumerate(self.games):
            row_i, col_i = divmod(i, cols)
            color = g.get("color", ACCENT)
            cell = tk.Frame(grid, bg=SURF, bd=1, relief="solid", cursor="hand2")
            cell.grid(row=row_i, column=col_i, padx=6, pady=6, sticky="nsew")
            tk.Label(cell, text=g.get("name", g["id"]).upper(),
                     font=("Courier New", 14, "bold"), bg=SURF, fg=color,
                     pady=18).pack()
            exe = os.path.join(ROOT, g.get("exe", ""))
            status = "ready" if os.path.exists(exe) else "not built"
            tk.Label(cell, text=status, font=FONT_SMALL, bg=SURF,
                     fg="#4a5468" if status == "ready" else "#ff4d6d").pack()
            cell.bind("<Button-1>", lambda e, _e=exe, _g=g: self._launch(_e, _g))

        # bottom bar
        bot = tk.Frame(frame, bg=BG)
        bot.pack(fill="x", pady=(14, 0))
        tk.Button(bot, text="Open Leaderboard", bg=BORDER, fg=FG,
                  font=FONT, relief="flat", activebackground="#2a3242",
                  command=self._open_leaderboard).pack(side="left")
        tk.Button(bot, text="Logout", bg=BORDER, fg="#ff4d6d",
                  font=FONT, relief="flat", activebackground="#2a1010",
                  command=self._logout).pack(side="right")

        self._log_label = tk.Label(bot, text="", font=FONT_SMALL,
                                   bg=BG, fg="#4a5468")
        self._log_label.pack(side="left", padx=14)

    def _launch(self, exe_path, game):
        if not os.path.exists(exe_path):
            self._log(f"build not found: {exe_path}", err=True)
            return
        cmd = [exe_path, "--player", self.player["name"],
               "--phone",    self.player.get("phone", ""),
               "--college",  self.player.get("college", ""),
               "--semester", self.player.get("semester", "")]
        self._log(f"launching {game.get('name', game['id'])}…")
        try:
            subprocess.Popen(cmd, cwd=os.path.dirname(exe_path))
        except Exception as e:
            self._log(str(e), err=True)

    def _open_leaderboard(self):
        cfg = os.path.join(ROOT, "..", "leaderboard", "web", "index.html")
        cfg = os.path.normpath(cfg)
        if os.path.exists(cfg):
            webbrowser.open("file://" + cfg)
        else:
            webbrowser.open("https://github.com/b1nary-0rbiter/asthra-game-launcher/tree/main/leaderboard/web")

    def _logout(self):
        self.player = None
        self._shown_games = False
        _clear_active()
        self._show_login()

    def _log(self, msg, err=False):
        if hasattr(self, "_log_label"):
            self._log_label.config(text=msg, fg="#ff4d6d" if err else "#4a5468")

    # ── helpers ───────────────────────────────────────────────────────────

    def _clear(self):
        for w in self.winfo_children():
            w.destroy()

# ── entry point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    App().mainloop()