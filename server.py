from __future__ import annotations

import json
import re
import ssl
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from world_cup_data import GROUPS, PLAYER_STATS, SEED_STANDINGS, seed_payload


ROOT = Path(__file__).resolve().parent
CACHE = ROOT / "world_cup_cache.json"
IMAGE_PATH = ROOT / "world_cup_2026_group_standings.png"
IMAGE_SCRIPT = ROOT / "make_world_cup_standings_image.py"
BUNDLED_PYTHON = Path("/Users/terra/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3")
STANDINGS_URL = "https://www.sbnation.com/soccer/1117905/world-cup-standings-updated-full-list-of-teams"
VERIFIED_GROUPS = {"D", "E", "F"}
VERIFIED_MATCH_SCORES = {
    ("D", "Türkiye", "United States"): (3, 2, "FT"),
    ("D", "Paraguay", "Australia"): (0, 0, "FT"),
    ("E", "Curaçao", "Côte d'Ivoire"): (0, 2, "FT"),
    ("E", "Ecuador", "Germany"): (2, 1, "FT"),
    ("F", "Tunisia", "Netherlands"): (1, 3, "FT"),
    ("F", "Japan", "Sweden"): (1, 1, "FT"),
}
PLAYER_STATS_NOTE = "Player stats were checked against June 26 Golden Boot reports. Goals are updated for reported leaders; assists are only filled where a reliable report listed them, and cards still require an official feed."


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def load_data():
    if CACHE.exists():
        with CACHE.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if "playerStats" not in data:
            data["playerStats"] = []
        apply_verified_overrides(data)
        save_data(data)
        return data
    data = seed_payload()
    save_data(data)
    return data


def save_data(data):
    data["imagePath"] = "/world_cup_2026_group_standings.png"
    with CACHE.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)


def clone_rows(rows):
    return [dict(row) for row in rows]


def merge_player_stats(data):
    current = {(row.get("player"), row.get("team")): row for row in data.get("playerStats", [])}
    merged = []
    for row in PLAYER_STATS:
        merged.append({**current.pop((row["player"], row["team"]), {}), **row})
    merged.extend(current.values())
    data["playerStats"] = merged
    data["playerStatsNote"] = PLAYER_STATS_NOTE


def apply_verified_overrides(data):
    for group in VERIFIED_GROUPS:
        data["groups"][group] = clone_rows(SEED_STANDINGS[group])
    for match in data.get("matches", []):
        key = (match.get("group"), match.get("home"), match.get("away"))
        if key in VERIFIED_MATCH_SCORES:
            home_score, away_score, status = VERIFIED_MATCH_SCORES[key]
            match["homeScore"] = home_score
            match["awayScore"] = away_score
            match["status"] = status
    merge_player_stats(data)


def write_dynamic_snapshot(data):
    snapshot = {
        "lastUpdated": data.get("lastUpdated"),
        "sourceNote": data.get("sourceNote"),
        "groups": data.get("groups", {}),
        "matches": data.get("matches", []),
        "playerStats": data.get("playerStats", []),
        "playerStatsNote": data.get("playerStatsNote", ""),
    }
    (ROOT / "world_cup_dynamic_snapshot.json").write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")


def update_project_data_files(data):
    # Keep a source-controlled snapshot beside the Python seed module so refreshes are visible in the repo.
    write_dynamic_snapshot(data)


def generate_standings_image(data=None):
    if data is None:
        data = load_data()
    save_data(data)
    python = BUNDLED_PYTHON if BUNDLED_PYTHON.exists() else Path(sys.executable)
    result = subprocess.run(
        [str(python), str(IMAGE_SCRIPT)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout or "Image generator failed").strip())
    data["imagePath"] = "/world_cup_2026_group_standings.png"
    save_data(data)
    return data


def recalculate_from_matches(data):
    table = {
        group: {
            team: {"team": team, "played": 0, "won": 0, "drawn": 0, "lost": 0, "gf": 0, "ga": 0, "gd": 0, "pts": 0, "status": "contending"}
            for team in teams
        }
        for group, teams in GROUPS.items()
    }

    for match in data["matches"]:
        if match.get("homeScore") is None or match.get("awayScore") is None:
            continue
        group = match["group"]
        home = table[group][match["home"]]
        away = table[group][match["away"]]
        hs = int(match["homeScore"])
        ass = int(match["awayScore"])

        home["played"] += 1
        away["played"] += 1
        home["gf"] += hs
        home["ga"] += ass
        away["gf"] += ass
        away["ga"] += hs
        if hs > ass:
            home["won"] += 1
            away["lost"] += 1
            home["pts"] += 3
        elif hs < ass:
            away["won"] += 1
            home["lost"] += 1
            away["pts"] += 3
        else:
            home["drawn"] += 1
            away["drawn"] += 1
            home["pts"] += 1
            away["pts"] += 1

    for group, teams in table.items():
        rows = []
        for row in teams.values():
            row["gd"] = row["gf"] - row["ga"]
            rows.append(row)
        rows.sort(key=lambda row: (row["pts"], row["gd"], row["gf"]), reverse=True)
        for idx, row in enumerate(rows):
            row["status"] = "third" if idx == 2 else "contending"
            if row["played"] == 3 and idx < 2:
                row["status"] = "advanced"
            if row["played"] == 3 and idx == 3:
                row["status"] = "eliminated"
        data["groups"][group] = rows
    data["lastUpdated"] = utc_now()
    data["sourceNote"] = "Local score edits recalculated standings by points, goal difference, then goals for."


def strip_html(html):
    html = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.I)
    html = re.sub(r"<style[\s\S]*?</style>", " ", html, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", text)


def fetch_text(url):
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 WorldCupLocal/1.0"})
    context = ssl._create_unverified_context()
    with urllib.request.urlopen(request, timeout=12, context=context) as response:
        return response.read().decode("utf-8", errors="replace")


def try_refresh_from_web(data):
    html = fetch_text(STANDINGS_URL)
    text = strip_html(html)
    changed = 0

    for group, teams in GROUPS.items():
        start = text.find(f"Group {group} standings")
        if start == -1:
            continue
        end_candidates = [text.find(f"Group {chr(ord(group) + 1)} standings", start + 1)] if group != "L" else []
        end_candidates += [text.find(f"Group {group} schedule", start + 1), text.find("Who advances", start + 1)]
        end_candidates = [item for item in end_candidates if item != -1]
        chunk = text[start : min(end_candidates) if end_candidates else start + 1800]
        rows = []
        for team in teams:
            safe = re.escape(team)
            match = re.search(rf"{safe}\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*([+-]?\d+)\s+(\d+)", chunk)
            if not match:
                continue
            won, drawn, lost, gf, ga, gd, pts = map(int, match.groups())
            rows.append(
                {
                    "team": team,
                    "played": won + drawn + lost,
                    "won": won,
                    "drawn": drawn,
                    "lost": lost,
                    "gf": gf,
                    "ga": ga,
                    "gd": gd,
                    "pts": pts,
                    "status": "contending",
                }
            )
        if len(rows) == 4:
            rows.sort(key=lambda row: (row["pts"], row["gd"], row["gf"]), reverse=True)
            for idx, row in enumerate(rows):
                row["status"] = "third" if idx == 2 else "contending"
                if row["played"] == 3 and idx < 2:
                    row["status"] = "advanced"
                if row["played"] == 3 and idx == 3:
                    row["status"] = "eliminated"
            data["groups"][group] = rows
            changed += 1

    if changed == 0:
        apply_verified_overrides(data)
        data["lastUpdated"] = utc_now()
        data["sourceNote"] = "Refresh reached the standings source, but no group tables could be parsed. Verified Group D/E/F corrections and checked player-stat leaders are still applied."
        update_project_data_files(data)
        generate_standings_image(data)
        save_data(data)
        return data

    apply_verified_overrides(data)
    data["lastUpdated"] = utc_now()
    data["sourceNote"] = f"Refreshed {changed} group table(s) from SB Nation, then validated Group D/E/F with June 26 corrections. Scores remain locally editable."
    update_project_data_files(data)
    generate_standings_image(data)
    save_data(data)
    return data


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw) if raw else {}

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/data":
            self.send_json(load_data())
            return
        if path == "/":
            self.path = "/index.html"
        super().do_GET()

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            if path == "/api/refresh":
                data = load_data()
                self.send_json(try_refresh_from_web(data))
                return
            if path == "/api/generate-image":
                data = generate_standings_image(load_data())
                self.send_json(data)
                return
            if path == "/api/update-match":
                body = self.read_json()
                data = load_data()
                match_id = body.get("id")
                for match in data["matches"]:
                    if match["id"] == match_id:
                        match["homeScore"] = None if body.get("homeScore") in ("", None) else int(body["homeScore"])
                        match["awayScore"] = None if body.get("awayScore") in ("", None) else int(body["awayScore"])
                        match["status"] = body.get("status") or match["status"]
                        break
                else:
                    self.send_json({"error": f"Unknown match id: {match_id}"}, status=404)
                    return
                recalculate_from_matches(data)
                save_data(data)
                self.send_json(data)
                return
        except (urllib.error.URLError, TimeoutError, RuntimeError) as exc:
            data = load_data()
            data["lastUpdated"] = utc_now()
            data["sourceNote"] = f"Online refresh unavailable ({exc}). Cached data is still shown."
            save_data(data)
            self.send_json(data)
            return
        except Exception as exc:
            self.send_json({"error": str(exc)}, status=500)
            return
        self.send_json({"error": "Not found"}, status=404)


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 8080), Handler)
    print("World Cup dashboard: http://127.0.0.1:8080/")
    server.serve_forever()
