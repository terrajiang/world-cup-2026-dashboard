from __future__ import annotations

import json
import re
import ssl
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import date, datetime, time, timedelta, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

from world_cup_data import GROUPS, PLAYER_STATS, SEED_STANDINGS, seed_payload


ROOT = Path(__file__).resolve().parent
CACHE = ROOT / "world_cup_cache.json"
IMAGE_PATH = ROOT / "world_cup_2026_group_standings.png"
IMAGE_SCRIPT = ROOT / "make_world_cup_standings_image.py"
BUNDLED_PYTHON = Path("/Users/terra/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3")
STANDINGS_URL = "https://www.sbnation.com/soccer/1117905/world-cup-standings-updated-full-list-of-teams"
PLAYER_STATS_URL = "https://www.sbnation.com/fifa-world-cup/1118693/world-cup-2026-golden-boot-standings"
VERIFIED_GROUPS = {"D", "E", "F"}
PACIFIC_TZ = ZoneInfo("America/Los_Angeles")
LIVE_WINDOW_MINUTES = 150
VERIFIED_MATCH_SCORES = {
    ("D", "Türkiye", "United States"): (3, 2, "FT"),
    ("D", "Paraguay", "Australia"): (0, 0, "FT"),
    ("E", "Curaçao", "Côte d'Ivoire"): (0, 2, "FT"),
    ("E", "Ecuador", "Germany"): (2, 1, "FT"),
    ("F", "Tunisia", "Netherlands"): (1, 3, "FT"),
    ("F", "Japan", "Sweden"): (1, 1, "FT"),
}
PLAYER_STATS_NOTE = "Player goals and assists refresh from the Golden Boot table. Yellow and red cards stay at 0 until a reliable card feed is connected."
MATCH_TIMES_PACIFIC = {
    ("A", "Mexico", "South Africa"): "12:00 PM PST",
    ("A", "South Korea", "Czechia"): "5:00 PM PST",
    ("A", "Czechia", "South Africa"): "9:00 AM PST",
    ("A", "Mexico", "South Korea"): "5:00 PM PST",
    ("A", "South Africa", "South Korea"): "5:00 PM PST",
    ("A", "Mexico", "Czechia"): "5:00 PM PST",
    ("B", "Canada", "Bosnia and Herzegovina"): "12:00 PM PST",
    ("B", "Qatar", "Switzerland"): "9:00 AM PST",
    ("B", "Switzerland", "Bosnia and Herzegovina"): "12:00 PM PST",
    ("B", "Canada", "Qatar"): "3:00 PM PST",
    ("B", "Switzerland", "Canada"): "12:00 PM PST",
    ("B", "Bosnia and Herzegovina", "Qatar"): "12:00 PM PST",
    ("C", "Brazil", "Morocco"): "12:00 PM PST",
    ("C", "Scotland", "Haiti"): "3:00 PM PST",
    ("C", "Morocco", "Scotland"): "12:00 PM PST",
    ("C", "Brazil", "Haiti"): "3:00 PM PST",
    ("C", "Morocco", "Haiti"): "3:00 PM PST",
    ("C", "Brazil", "Scotland"): "3:00 PM PST",
    ("D", "United States", "Paraguay"): "5:00 PM PST",
    ("D", "Australia", "Türkiye"): "9:00 AM PST",
    ("D", "United States", "Australia"): "9:00 AM PST",
    ("D", "Paraguay", "Türkiye"): "5:00 PM PST",
    ("D", "Türkiye", "United States"): "5:00 PM PST",
    ("D", "Paraguay", "Australia"): "5:00 PM PST",
    ("E", "Germany", "Curaçao"): "12:00 PM PST",
    ("E", "Côte d'Ivoire", "Ecuador"): "5:00 PM PST",
    ("E", "Germany", "Côte d'Ivoire"): "12:00 PM PST",
    ("E", "Ecuador", "Curaçao"): "5:00 PM PST",
    ("E", "Curaçao", "Côte d'Ivoire"): "12:00 PM PST",
    ("E", "Ecuador", "Germany"): "12:00 PM PST",
    ("F", "Netherlands", "Japan"): "3:00 PM PST",
    ("F", "Sweden", "Tunisia"): "8:00 PM PST",
    ("F", "Netherlands", "Sweden"): "9:00 AM PST",
    ("F", "Tunisia", "Japan"): "9:00 AM PST",
    ("F", "Tunisia", "Netherlands"): "3:00 PM PST",
    ("F", "Japan", "Sweden"): "3:00 PM PST",
    ("G", "Belgium", "Egypt"): "12:00 PM PST",
    ("G", "Iran", "New Zealand"): "5:00 PM PST",
    ("G", "Belgium", "Iran"): "3:00 PM PST",
    ("G", "New Zealand", "Egypt"): "8:00 PM PST",
    ("G", "New Zealand", "Belgium"): "8:00 PM PST",
    ("G", "Egypt", "Iran"): "8:00 PM PST",
    ("H", "Spain", "Cabo Verde"): "9:00 AM PST",
    ("H", "Saudi Arabia", "Uruguay"): "3:00 PM PST",
    ("H", "Spain", "Saudi Arabia"): "12:00 PM PST",
    ("H", "Uruguay", "Cabo Verde"): "5:00 PM PST",
    ("H", "Cabo Verde", "Saudi Arabia"): "5:00 PM PST",
    ("H", "Uruguay", "Spain"): "5:00 PM PST",
    ("I", "France", "Senegal"): "9:00 AM PST",
    ("I", "Norway", "Iraq"): "12:00 PM PST",
    ("I", "France", "Iraq"): "12:00 PM PST",
    ("I", "Norway", "Senegal"): "3:00 PM PST",
    ("I", "Norway", "France"): "12:00 PM PST",
    ("I", "Senegal", "Iraq"): "12:00 PM PST",
    ("J", "Argentina", "Algeria"): "5:00 PM PST",
    ("J", "Austria", "Jordan"): "9:00 AM PST",
    ("J", "Argentina", "Austria"): "9:00 AM PST",
    ("J", "Algeria", "Jordan"): "5:00 PM PST",
    ("J", "Algeria", "Austria"): "7:00 PM PST",
    ("J", "Jordan", "Argentina"): "7:00 PM PST",
    ("K", "Portugal", "DR Congo"): "12:00 PM PST",
    ("K", "Colombia", "Uzbekistan"): "8:00 PM PST",
    ("K", "Portugal", "Uzbekistan"): "12:00 PM PST",
    ("K", "Colombia", "DR Congo"): "8:00 PM PST",
    ("K", "Colombia", "Portugal"): "4:30 PM PST",
    ("K", "DR Congo", "Uzbekistan"): "4:30 PM PST",
    ("L", "England", "Croatia"): "3:00 PM PST",
    ("L", "Ghana", "Panama"): "5:00 PM PST",
    ("L", "England", "Ghana"): "3:00 PM PST",
    ("L", "Croatia", "Panama"): "5:00 PM PST",
    ("L", "Panama", "England"): "2:00 PM PST",
    ("L", "Croatia", "Ghana"): "2:00 PM PST",
}
KNOCKOUT_TIMES_PACIFIC = {
    "R32-1": "12:00 PM PST",
    "R32-2": "5:00 PM PST",
    "R32-3": "12:00 PM PST",
    "R32-4": "5:00 PM PST",
    "R32-5": "12:00 PM PST",
    "R32-6": "5:00 PM PST",
    "R32-7": "9:00 AM PST",
    "R32-8": "12:00 PM PST",
    "R32-9": "5:00 PM PST",
    "R32-10": "9:00 AM PST",
    "R32-11": "12:00 PM PST",
    "R32-12": "5:00 PM PST",
    "R32-13": "9:00 AM PST",
    "R32-14": "12:00 PM PST",
    "R32-15": "3:00 PM PST",
    "R32-16": "5:00 PM PST",
    "R16-1": "12:00 PM PST",
    "R16-2": "5:00 PM PST",
    "R16-3": "12:00 PM PST",
    "R16-4": "5:00 PM PST",
    "R16-5": "12:00 PM PST",
    "R16-6": "5:00 PM PST",
    "R16-7": "12:00 PM PST",
    "R16-8": "5:00 PM PST",
    "QF-1": "12:00 PM PST",
    "QF-2": "5:00 PM PST",
    "QF-3": "12:00 PM PST",
    "QF-4": "5:00 PM PST",
    "SF-1": "5:00 PM PST",
    "SF-2": "5:00 PM PST",
    "3P": "12:00 PM PST",
    "Final": "12:00 PM PST",
}
LIVE_MATCH_SOURCES = {
    ("G", "New Zealand", "Belgium"): "https://www.theguardian.com/football/live/2026/jun/26/new-zealand-v-belgium-world-cup-2026-live-updates",
    ("G", "Egypt", "Iran"): "https://www.theguardian.com/football/live/2026/jun/26/egypt-v-iran-world-cup-2026-live-updates",
    ("H", "Cabo Verde", "Saudi Arabia"): "https://www.theguardian.com/football/live/2026/jun/26/cabo-verde-v-saudi-arabia-world-cup-2026-live-updates",
    ("H", "Uruguay", "Spain"): "https://www.theguardian.com/football/live/2026/jun/26/uruguay-v-spain-world-cup-2026-live-updates",
    ("I", "Norway", "France"): "https://www.theguardian.com/football/live/2026/jun/26/norway-v-france-world-cup-2026-live-updates",
    ("I", "Senegal", "Iraq"): "https://www.theguardian.com/football/live/2026/jun/26/senegal-v-iraq-world-cup-2026-live-updates",
    ("J", "Algeria", "Austria"): "https://www.theguardian.com/football/live/2026/jun/27/algeria-v-austria-world-cup-2026-live-updates",
    ("J", "Jordan", "Argentina"): "https://www.theguardian.com/football/live/2026/jun/27/jordan-v-argentina-world-cup-2026-live-updates",
    ("K", "Colombia", "Portugal"): "https://www.theguardian.com/football/live/2026/jun/27/colombia-v-portugal-world-cup-2026-live-updates",
    ("K", "DR Congo", "Uzbekistan"): "https://www.theguardian.com/football/live/2026/jun/27/dr-congo-v-uzbekistan-world-cup-2026-live-updates",
    ("L", "Panama", "England"): "https://www.theguardian.com/football/live/2026/jun/27/panama-v-england-world-cup-2026-live-updates",
    ("L", "Croatia", "Ghana"): "https://www.theguardian.com/football/live/2026/jun/27/croatia-v-ghana-world-cup-2026-live-updates",
}


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def pacific_now():
    return datetime.now(PACIFIC_TZ)


def load_data():
    if CACHE.exists():
        with CACHE.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if "playerStats" not in data:
            data["playerStats"] = []
            merge_player_stats(data)
        apply_verified_overrides(data)
        apply_match_times(data)
        save_data(data)
        return data
    data = seed_payload()
    apply_match_times(data)
    save_data(data)
    return data


def save_data(data):
    apply_match_times(data)
    data["imagePath"] = "/world_cup_2026_group_standings.png"
    with CACHE.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)


def clone_rows(rows):
    return [dict(row) for row in rows]


def merge_player_stats(data, source_rows=None):
    current = {(row.get("player"), row.get("team")): row for row in data.get("playerStats", [])}
    source = source_rows or PLAYER_STATS
    merged = []
    for row in source:
        prior = current.pop((row["player"], row["team"]), {})
        merged.append(
            {
                **row,
                "yellowCards": prior.get("yellowCards", row.get("yellowCards", 0)),
                "redCards": prior.get("redCards", row.get("redCards", 0)),
            }
        )
    data["playerStats"] = merged
    data["playerStatsNote"] = PLAYER_STATS_NOTE


def apply_match_times(data):
    for match in data.get("matches", []):
        key = (match.get("group"), match.get("home"), match.get("away"))
        if key in MATCH_TIMES_PACIFIC:
            match["timePst"] = MATCH_TIMES_PACIFIC[key]
    for match in data.get("knockout", []):
        slot = match.get("slot")
        if slot in KNOCKOUT_TIMES_PACIFIC:
            match["timePst"] = KNOCKOUT_TIMES_PACIFIC[slot]


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
    apply_match_times(data)


def parse_guardian_live_score(text, home, away):
    full_time_patterns = [
        rf"(?:FULL TIME|Full-time!?|Full time):?\s*{re.escape(home)}\s+(\d+)\s*[-–]\s*(\d+)\s+{re.escape(away)}",
        rf"(?:FULL TIME|Full-time!?|Full time):?\s*{re.escape(away)}\s+(\d+)\s*[-–]\s*(\d+)\s+{re.escape(home)}",
    ]
    for pattern in full_time_patterns:
        match = re.search(pattern, text, flags=re.I)
        if not match:
            continue
        first, second = map(int, match.groups())
        if re.search(rf"{re.escape(home)}\s+\d+\s*[-–]\s*\d+\s+{re.escape(away)}", match.group(0), flags=re.I):
            return first, second, "FT"
        return second, first, "FT"

    score_patterns = [
        rf"{re.escape(home)}\s+(\d+)\s*[-–]\s*(\d+)\s+{re.escape(away)}",
        rf"{re.escape(away)}\s+(\d+)\s*[-–]\s*(\d+)\s+{re.escape(home)}",
    ]
    for pattern in score_patterns:
        match = re.search(pattern, text, flags=re.I)
        if not match:
            continue
        first, second = map(int, match.groups())
        if pattern.startswith(re.escape(home)):
            return first, second, "Live"
        return second, first, "Live"
    return None


def parse_pacific_time(label):
    match = re.search(r"(\d{1,2}):(\d{2})\s*(AM|PM)", label or "", flags=re.I)
    if not match:
        return None
    hour = int(match.group(1)) % 12
    minute = int(match.group(2))
    if match.group(3).upper() == "PM":
        hour += 12
    return time(hour, minute)


def match_kickoff_pacific(match):
    kickoff_time = parse_pacific_time(match.get("timePst"))
    if not kickoff_time or not match.get("date"):
        return None
    try:
        kickoff_date = date.fromisoformat(match["date"])
    except ValueError:
        return None
    return datetime.combine(kickoff_date, kickoff_time, tzinfo=PACIFIC_TZ)


def is_match_in_live_window(match, now=None):
    kickoff = match_kickoff_pacific(match)
    if not kickoff:
        return False
    now = now or pacific_now()
    return kickoff <= now <= kickoff + timedelta(minutes=LIVE_WINDOW_MINUTES)


def apply_live_score_updates(data, now=None):
    changed = 0
    now = now or pacific_now()
    for match in data.get("matches", []):
        key = (match.get("group"), match.get("home"), match.get("away"))
        if key not in LIVE_MATCH_SOURCES:
            continue
        if match.get("status") == "FT":
            continue
        in_window = is_match_in_live_window(match, now)
        is_today = match.get("date") == now.date().isoformat()
        if not in_window and not is_today and match.get("status") != "Live":
            continue
        before = (match.get("homeScore"), match.get("awayScore"), match.get("status"))
        try:
            text = strip_html(fetch_text(LIVE_MATCH_SOURCES[key]))
        except (urllib.error.URLError, TimeoutError):
            if in_window:
                match["status"] = "Live"
                if match.get("homeScore") is None:
                    match["homeScore"] = 0
                if match.get("awayScore") is None:
                    match["awayScore"] = 0
                if before != (match.get("homeScore"), match.get("awayScore"), match.get("status")):
                    changed += 1
            continue
        parsed = parse_guardian_live_score(text, match["home"], match["away"])
        if parsed and parsed[2] == "FT":
            match["homeScore"], match["awayScore"], match["status"] = parsed
        elif parsed and in_window:
            match["homeScore"], match["awayScore"], match["status"] = parsed
        elif in_window:
            match["status"] = "Live"
            if match.get("homeScore") is None:
                match["homeScore"] = 0
            if match.get("awayScore") is None:
                match["awayScore"] = 0
        elif match.get("status") == "Live":
            match["status"] = "Scheduled"
        if before != (match.get("homeScore"), match.get("awayScore"), match.get("status")):
            changed += 1
    return changed


def load_data_with_live_check():
    data = load_data()
    live_changed = apply_live_score_updates(data)
    if live_changed:
        recalculate_from_matches(data)
        apply_verified_overrides(data)
        data["lastUpdated"] = utc_now()
        data["sourceNote"] = "Checked live match windows and live score sources on page load."
        save_data(data)
    return data


def normalize_team_name(team):
    aliases = {
        "Ivory Coast": "Côte d'Ivoire",
    }
    return aliases.get(team, team)


def parse_golden_boot_stats(text):
    start = text.find("Minutes")
    if start == -1:
        return []
    end = text.find("See More", start)
    chunk = text[start + len("Minutes") : end if end != -1 else len(text)]
    team_names = sorted({team for teams in GROUPS.values() for team in teams} | {"Ivory Coast"}, key=len, reverse=True)
    team_pattern = "|".join(re.escape(team) for team in team_names)
    row_pattern = re.compile(rf"(.+?)\s*({team_pattern})\s+(\d+)\s+(\d+)\s+(\d+)(?=\s+\S|\s*$)")
    rows = []
    for match in row_pattern.finditer(chunk):
        player, team, goals, assists, minutes = match.groups()
        player = player.strip()
        if not player:
            continue
        rows.append(
            {
                "player": player,
                "team": normalize_team_name(team),
                "goals": int(goals),
                "assists": int(assists),
                "yellowCards": 0,
                "redCards": 0,
                "minutes": int(minutes),
            }
        )
    return rows


def refresh_player_stats(data):
    try:
        text = strip_html(fetch_text(PLAYER_STATS_URL))
    except (urllib.error.URLError, TimeoutError):
        if not data.get("playerStats"):
            merge_player_stats(data)
        return len(data.get("playerStats", []))
    rows = parse_golden_boot_stats(text)
    if not rows:
        if not data.get("playerStats"):
            merge_player_stats(data)
        return len(data.get("playerStats", []))
    merge_player_stats(data, rows)
    return len(rows)


def write_dynamic_snapshot(data):
    apply_match_times(data)
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

    live_changed = apply_live_score_updates(data)
    if live_changed:
        recalculate_from_matches(data)
        apply_verified_overrides(data)

    if changed == 0:
        apply_verified_overrides(data)
        live_changed = apply_live_score_updates(data)
        if live_changed:
            recalculate_from_matches(data)
            apply_verified_overrides(data)
        data["lastUpdated"] = utc_now()
        data["sourceNote"] = "Refresh reached the standings source, checked live match pages, and kept verified local corrections where source tables could not be parsed."
        refresh_player_stats(data)
        update_project_data_files(data)
        generate_standings_image(data)
        save_data(data)
        return data

    apply_verified_overrides(data)
    live_changed = apply_live_score_updates(data)
    if live_changed:
        recalculate_from_matches(data)
        apply_verified_overrides(data)
    data["lastUpdated"] = utc_now()
    data["sourceNote"] = f"Refreshed {changed} group table(s), checked live match pages, and validated stored score corrections."
    refresh_player_stats(data)
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
            self.send_json(load_data_with_live_check())
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
            refresh_player_stats(data)
            data["lastUpdated"] = utc_now()
            data["sourceNote"] = f"Online refresh unavailable ({exc}). Cached data is still shown."
            update_project_data_files(data)
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
