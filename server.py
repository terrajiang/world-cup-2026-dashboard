from __future__ import annotations

import json
import re
import ssl
import urllib.error
import urllib.request
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from world_cup_data import GROUPS, PLAYER_STATS, seed_payload


ROOT = Path(__file__).resolve().parent
CACHE = ROOT / "world_cup_cache.json"
STANDINGS_URL = "https://www.sbnation.com/soccer/1117905/world-cup-standings-updated-full-list-of-teams"


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def load_data():
    if CACHE.exists():
        with CACHE.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if "playerStats" not in data:
            data["playerStats"] = []
        existing = {(row.get("player"), row.get("team")) for row in data["playerStats"]}
        for row in PLAYER_STATS:
            if (row["player"], row["team"]) not in existing:
                data["playerStats"].append(row)
        if "playerStatsNote" not in data or data["playerStatsNote"].startswith("Seeded player stats"):
            data["playerStatsNote"] = "Player stats include every player currently available in the local stats feed. Goals are partially populated from public match reports; assists and cards need an official feed or manual entry."
        save_data(data)
        return data
    data = seed_payload()
    save_data(data)
    return data


def save_data(data):
    with CACHE.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)


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
        data["lastUpdated"] = utc_now()
        data["sourceNote"] = "Refresh reached the standings source, but no group tables could be parsed. Cached data is still shown."
        save_data(data)
        return data

    data["lastUpdated"] = utc_now()
    data["sourceNote"] = f"Refreshed {changed} group table(s) from SB Nation standings. Scores remain locally editable."
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
            if path == "/api/reset":
                data = seed_payload()
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
