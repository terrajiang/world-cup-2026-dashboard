from __future__ import annotations

import json
import os
import re
import ssl
import urllib.error
import urllib.request
from datetime import date, datetime, time, timedelta, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlencode, urlparse
from zoneinfo import ZoneInfo

from world_cup_data import GROUPS, KNOCKOUT, PLAYER_STATS, SEED_STANDINGS, seed_payload


ROOT = Path(__file__).resolve().parent
CACHE = ROOT / "world_cup_cache.json"
STANDINGS_URL = "https://www.sbnation.com/soccer/1117905/world-cup-standings-updated-full-list-of-teams"
SCHEDULE_URL = "https://www.sbnation.com/soccer/1117513/world-cup-schedule-2026-how-to-watch-every-match-scores-and-more"
KNOCKOUT_SCHEDULE_URL = "https://www.sbnation.com/soccer/1120771/world-cup-schedule-scores-round-32"
PLAYER_STATS_URL = "https://www.sbnation.com/fifa-world-cup/1118693/world-cup-2026-golden-boot-standings"
ESPN_SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard"
FOOTBALL_DATA_API_BASE = "https://api.football-data.org/v4"
FOOTBALL_DATA_COMPETITION = os.environ.get("FOOTBALL_DATA_COMPETITION", "WC")
FOOTBALL_DATA_SEASON = os.environ.get("FOOTBALL_DATA_SEASON", "2026")
VERIFIED_GROUPS = {"D", "E", "F"}
PACIFIC_TZ = ZoneInfo("America/Los_Angeles")
EASTERN_TZ = ZoneInfo("America/New_York")
LIVE_WINDOW_MINUTES = 150
VERIFIED_MATCH_SCORES = {
    ("D", "Türkiye", "United States"): (3, 2, "FT"),
    ("D", "Paraguay", "Australia"): (0, 0, "FT"),
    ("E", "Curaçao", "Côte d'Ivoire"): (0, 2, "FT"),
    ("E", "Ecuador", "Germany"): (2, 1, "FT"),
    ("F", "Tunisia", "Netherlands"): (1, 3, "FT"),
    ("F", "Japan", "Sweden"): (1, 1, "FT"),
}
VERIFIED_KNOCKOUT_SCORES = {
    73: (0, 1, "FT", None, None),
    75: (1, 1, "FT", "Morocco", "Morocco wins 3-2 on penalties"),
}
KNOCKOUT_TIME_OVERRIDES = {
    # Delayed kickoff: Mexico vs Ecuador moved from 6 PM to 7 PM Pacific on June 30.
    "R32-11": "7:00 PM PST",
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
    "R32-1": "1:30 PM PST",
    "R32-2": "2:00 PM PST",
    "R32-3": "12:00 PM PST",
    "R32-4": "6:00 PM PST",
    "R32-5": "8:00 PM PST",
    "R32-6": "12:00 PM PST",
    "R32-7": "5:00 PM PST",
    "R32-8": "1:00 PM PST",
    "R32-9": "10:00 AM PST",
    "R32-10": "10:00 AM PST",
    "R32-11": "7:00 PM PST",
    "R32-12": "9:00 AM PST",
    "R32-13": "11:00 AM PST",
    "R32-14": "6:30 PM PST",
    "R32-15": "4:00 PM PST",
    "R32-16": "3:00 PM PST",
    "R16-1": "2:00 PM PST",
    "R16-2": "10:00 AM PST",
    "R16-3": "12:00 PM PST",
    "R16-4": "5:00 PM PST",
    "R16-5": "1:00 PM PST",
    "R16-6": "5:00 PM PST",
    "R16-7": "9:00 AM PST",
    "R16-8": "1:00 PM PST",
    "QF-1": "1:00 PM PST",
    "QF-2": "12:00 PM PST",
    "QF-3": "2:00 PM PST",
    "QF-4": "6:00 PM PST",
    "SF-1": "12:00 PM PST",
    "SF-2": "12:00 PM PST",
    "3P": "2:00 PM PST",
    "Final": "12:00 PM PST",
}
LIVE_MATCH_SOURCES = {
    ("G", "New Zealand", "Belgium"): "https://www.theguardian.com/football/live/2026/jun/26/new-zealand-v-belgium-world-cup-2026-live-updates",
    ("G", "Egypt", "Iran"): "https://www.theguardian.com/football/live/2026/jun/26/egypt-v-iran-world-cup-2026-live-updates",
    ("H", "Cabo Verde", "Saudi Arabia"): "https://www.theguardian.com/football/live/2026/jun/26/cape-verde-v-saudi-arabia-world-cup-2026-live",
    ("H", "Uruguay", "Spain"): "https://www.theguardian.com/football/live/2026/jun/26/uruguay-v-spain-world-cup-2026-live",
    ("I", "Norway", "France"): "https://www.theguardian.com/football/live/2026/jun/26/norway-v-france-world-cup-2026-live-updates",
    ("I", "Senegal", "Iraq"): "https://www.theguardian.com/football/live/2026/jun/26/senegal-v-iraq-world-cup-2026-live-updates",
    ("J", "Algeria", "Austria"): "https://www.theguardian.com/football/live/2026/jun/27/algeria-v-austria-world-cup-2026-live-updates",
    ("J", "Jordan", "Argentina"): "https://www.theguardian.com/football/live/2026/jun/27/jordan-v-argentina-world-cup-2026-live-updates",
    ("K", "Colombia", "Portugal"): "https://www.theguardian.com/football/live/2026/jun/27/colombia-v-portugal-world-cup-2026-live-updates",
    ("K", "DR Congo", "Uzbekistan"): "https://www.theguardian.com/football/live/2026/jun/27/dr-congo-v-uzbekistan-world-cup-2026-live-updates",
    ("L", "Panama", "England"): "https://www.theguardian.com/football/live/2026/jun/27/panama-v-england-world-cup-2026-live-updates",
    ("L", "Croatia", "Ghana"): "https://www.theguardian.com/football/live/2026/jun/27/croatia-v-ghana-world-cup-2026-live-updates",
}
LIVE_SOURCE_ALIASES = {
    "Cabo Verde": ["Cabo Verde", "Cape Verde"],
    "Côte d'Ivoire": ["Côte d'Ivoire", "Ivory Coast"],
}
THIRD_PLACE_ASSIGNMENT_OVERRIDES = {
    frozenset({"B", "D", "E", "F", "I", "J", "K", "L"}): {
        ("R32-1", "away"): "D",
        ("R32-2", "away"): "F",
        ("R32-7", "away"): "B",
        ("R32-8", "away"): "I",
        ("R32-11", "away"): "E",
        ("R32-12", "away"): "K",
        ("R32-15", "away"): "J",
        ("R32-16", "away"): "L",
    }
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
        sync_knockout(data)
        save_data(data)
        return data
    data = seed_payload()
    apply_match_times(data)
    sync_knockout(data)
    save_data(data)
    return data


def save_data(data):
    apply_match_times(data)
    sync_knockout(data)
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


def group_is_complete(rows):
    return len(rows or []) == 4 and all(row.get("played") == 3 for row in rows)


def group_place_team(data, group, place):
    rows = data.get("groups", {}).get(group, [])
    if not group_is_complete(rows) or len(rows) < place:
        return None
    return rows[place - 1].get("team")


def third_place_rankings(data):
    rows = []
    for group, group_rows in data.get("groups", {}).items():
        if group_is_complete(group_rows) and len(group_rows) >= 3:
            third = dict(group_rows[2])
            third["group"] = group
            rows.append(third)
    return sorted(rows, key=lambda row: (row.get("pts", 0), row.get("gd", 0), row.get("gf", 0), row.get("team", "")), reverse=True)


def assign_third_place_slots(data):
    rankings = third_place_rankings(data)
    if len(rankings) < 8:
        return {}
    rank_index = {row["group"]: index for index, row in enumerate(rankings)}
    advancing = {row["group"]: row["team"] for row in rankings[:8]}
    override = THIRD_PLACE_ASSIGNMENT_OVERRIDES.get(frozenset(advancing))
    if override:
        return {
            key: advancing[group]
            for key, group in override.items()
            if group in advancing
        }
    slots = []
    for match in KNOCKOUT:
        for side in ("home", "away"):
            label = match.get(side, "")
            slot_match = re.match(r"^3rd Group ([A-L/]+)$", label)
            if slot_match:
                candidates = [group for group in slot_match.group(1).split("/") if group in advancing]
                candidates.sort(key=lambda group: rank_index[group])
                slots.append((match["slot"], side, candidates))

    ordered_slots = sorted(enumerate(slots), key=lambda item: (len(item[1][2]), item[0]))

    def backtrack(index, used, assignments):
        if index == len(ordered_slots):
            return assignments
        _, (slot, side, candidates) = ordered_slots[index]
        for group in candidates:
            if group in used:
                continue
            result = backtrack(index + 1, used | {group}, {**assignments, (slot, side): advancing[group]})
            if result is not None:
                return result
        return None

    solved = backtrack(0, set(), {})
    if solved is not None:
        return solved

    assignments = {}
    used = set()
    for slot, side, candidates in slots:
        choice = next((group for group in candidates if group not in used), None)
        if not choice:
            continue
        assignments[(slot, side)] = advancing[choice]
        used.add(choice)
    return assignments


def knockout_result(match):
    if match.get("status") != "FT" or match.get("homeScore") is None or match.get("awayScore") is None:
        return None
    home = match.get("resolvedHome")
    away = match.get("resolvedAway")
    if not home or not away:
        return None
    if match.get("winner") in (home, away):
        winner = match["winner"]
        return {
            "winner": winner,
            "loser": away if winner == home else home,
        }
    home_score = int(match["homeScore"])
    away_score = int(match["awayScore"])
    if home_score == away_score:
        return None
    return {
        "winner": home if home_score > away_score else away,
        "loser": away if home_score > away_score else home,
    }


def resolve_knockout_label(label, data, knockout_by_slot, third_assignments, slot=None, side=None):
    match = re.match(r"^Winner Group ([A-L])$", label)
    if match:
        return group_place_team(data, match.group(1), 1)
    match = re.match(r"^Runner-up Group ([A-L])$", label)
    if match:
        return group_place_team(data, match.group(1), 2)
    match = re.match(r"^3rd Group ([A-L/]+)$", label)
    if match:
        return third_assignments.get((slot, side))
    match = re.match(r"^(Winner|Loser) ([A-Z0-9-]+)$", label)
    if match:
        prior = knockout_by_slot.get(match.group(2))
        result = knockout_result(prior) if prior else None
        if result:
            return result["winner" if match.group(1) == "Winner" else "loser"]
    return None


def sync_knockout(data):
    existing = {match.get("slot"): match for match in data.get("knockout", [])}
    knockout = []
    for template in KNOCKOUT:
        prior = existing.get(template["slot"], {})
        knockout.append(
            {
                **template,
                "date": prior.get("date", template["date"]),
                "timePst": prior.get("timePst"),
                "timeSource": prior.get("timeSource"),
                "homeScore": prior.get("homeScore"),
                "awayScore": prior.get("awayScore"),
                "status": prior.get("status", "Scheduled"),
                "winner": prior.get("winner"),
                "resultDetail": prior.get("resultDetail"),
                "resolvedHome": prior.get("resolvedHome"),
                "resolvedAway": prior.get("resolvedAway"),
            }
        )
    data["knockout"] = knockout
    apply_match_times(data)

    third_assignments = assign_third_place_slots(data)
    by_slot = {match["slot"]: match for match in data["knockout"]}
    for _ in range(4):
        changed = False
        for match in data["knockout"]:
            resolved_home = resolve_knockout_label(match["home"], data, by_slot, third_assignments, match["slot"], "home")
            resolved_away = resolve_knockout_label(match["away"], data, by_slot, third_assignments, match["slot"], "away")
            if match.get("resolvedHome") != resolved_home or match.get("resolvedAway") != resolved_away:
                match["resolvedHome"] = resolved_home
                match["resolvedAway"] = resolved_away
                changed = True
        if not changed:
            break


def apply_match_times(data):
    for match in data.get("matches", []):
        key = (match.get("group"), match.get("home"), match.get("away"))
        if key in MATCH_TIMES_PACIFIC:
            match["timePst"] = MATCH_TIMES_PACIFIC[key]
    for match in data.get("knockout", []):
        slot = match.get("slot")
        if slot in KNOCKOUT_TIME_OVERRIDES:
            match["timePst"] = KNOCKOUT_TIME_OVERRIDES[slot]
        elif slot in KNOCKOUT_TIMES_PACIFIC and match.get("timeSource") != "refreshed":
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
    for match in data.get("knockout", []):
        match_no = match.get("matchNo")
        if match_no in VERIFIED_KNOCKOUT_SCORES:
            home_score, away_score, status, winner, detail = VERIFIED_KNOCKOUT_SCORES[match_no]
            match["homeScore"] = home_score
            match["awayScore"] = away_score
            match["status"] = status
            match["winner"] = winner
            match["resultDetail"] = detail
    apply_match_times(data)
    sync_knockout(data)


def parse_guardian_live_score(text, home, away):
    def team_pattern(team):
        names = LIVE_SOURCE_ALIASES.get(team, [team])
        return r"(?:%s)" % "|".join(re.escape(name) for name in names)

    home_pattern = team_pattern(home)
    away_pattern = team_pattern(away)
    full_time_patterns = [
        rf"(?:FULL TIME|Full-time!?|Full time):?\s*{home_pattern}\s+(\d+)\s*[-–]\s*(\d+)\s+{away_pattern}",
        rf"(?:FULL TIME|Full-time!?|Full time):?\s*{away_pattern}\s+(\d+)\s*[-–]\s*(\d+)\s+{home_pattern}",
    ]
    for pattern in full_time_patterns:
        match = re.search(pattern, text, flags=re.I)
        if not match:
            continue
        first, second = map(int, match.groups())
        if re.search(rf"{home_pattern}\s+\d+\s*[-–]\s*\d+\s+{away_pattern}", match.group(0), flags=re.I):
            return first, second, "FT"
        return second, first, "FT"

    score_patterns = [
        (True, rf"{home_pattern}\s+(\d+)\s*[-–]\s*(\d+)\s+{away_pattern}"),
        (False, rf"{away_pattern}\s+(\d+)\s*[-–]\s*(\d+)\s+{home_pattern}"),
    ]
    for home_first, pattern in score_patterns:
        match = re.search(pattern, text, flags=re.I)
        if not match:
            continue
        first, second = map(int, match.groups())
        if home_first:
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
    sync_knockout(data)
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
                match["homeScore"] = None
                match["awayScore"] = None
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
            match["homeScore"] = None
            match["awayScore"] = None
        elif match.get("status") == "Live":
            match["status"] = "Scheduled"
            match["homeScore"] = None
            match["awayScore"] = None
        if before != (match.get("homeScore"), match.get("awayScore"), match.get("status")):
            changed += 1
    for match in data.get("knockout", []):
        if match.get("status") == "FT":
            continue
        in_window = is_match_in_live_window(match, now)
        before = (match.get("homeScore"), match.get("awayScore"), match.get("status"))
        if in_window:
            match["status"] = "Live"
        elif match.get("status") == "Live":
            match["status"] = "Scheduled"
            match["homeScore"] = None
            match["awayScore"] = None
        if before != (match.get("homeScore"), match.get("awayScore"), match.get("status")):
            changed += 1
    return changed


def find_schedule_score(text, group, home, away):
    patterns = [
        (home, away, rf"Group {re.escape(group)}:\s*{re.escape(home)}\s+(\d+),\s*{re.escape(away)}\s+(\d+)"),
        (away, home, rf"Group {re.escape(group)}:\s*{re.escape(away)}\s+(\d+),\s*{re.escape(home)}\s+(\d+)"),
    ]
    for first_team, _, pattern in patterns:
        match = re.search(pattern, text, flags=re.I)
        if not match:
            continue
        first_score, second_score = map(int, match.groups())
        if first_team == home:
            return first_score, second_score
        return second_score, first_score
    return None


def find_knockout_schedule_score(text, home, away):
    if not home or not away:
        return None
    def source_team_pattern(team):
        names = LIVE_SOURCE_ALIASES.get(team, [team])
        return r"(?:%s)" % "|".join(re.escape(name) for name in names)

    home_pattern = source_team_pattern(home)
    away_pattern = source_team_pattern(away)
    status_pattern = r"(?:Live|LIVE|HT|Half-time|Extra time|ET|AET|FT|Full-time|Final|[0-9]{1,3}(?:\+[0-9]+)?')"
    patterns = [
        (home, away, rf"{home_pattern}\s+(\d+),\s*{away_pattern}\s+(\d+)(?:\s+\(([^)]*)\))?"),
        (away, home, rf"{away_pattern}\s+(\d+),\s*{home_pattern}\s+(\d+)(?:\s+\(([^)]*)\))?"),
        (home, away, rf"{home_pattern}\s+(\d+)\s*[-–]\s*(\d+)\s+{away_pattern}(?:\s+\(([^)]*)\))?"),
        (away, home, rf"{away_pattern}\s+(\d+)\s*[-–]\s*(\d+)\s+{home_pattern}(?:\s+\(([^)]*)\))?"),
        (home, away, rf"{status_pattern}\s+{home_pattern}\s+(\d+)\s*[-–]\s*(\d+)\s+{away_pattern}(?:\s+\(([^)]*)\))?"),
        (away, home, rf"{status_pattern}\s+{away_pattern}\s+(\d+)\s*[-–]\s*(\d+)\s+{home_pattern}(?:\s+\(([^)]*)\))?"),
    ]
    for first_team, _, pattern in patterns:
        match = re.search(pattern, text, flags=re.I)
        if not match:
            continue
        first_score, second_score = map(int, match.groups()[:2])
        detail = match.group(3) if len(match.groups()) >= 3 else None
        winner = None
        status = "Live" if re.search(r"\b(Live|HT|Half-time|Extra time|ET|\d{1,3}(?:\+\d+)?')\b", match.group(0), flags=re.I) else "Score"
        if detail:
            winner_match = re.search(r"(.+?)\s+wins?\s+\d+\s*[-–]\s*\d+\s+on penalties", detail, flags=re.I)
            if winner_match:
                winner = normalize_team_name(winner_match.group(1).strip())
                status = "FT"
        if first_team == home:
            return first_score, second_score, status, winner, detail
        return second_score, first_score, status, winner, detail
    return None


def month_number(month_name):
    months = {
        "January": 1,
        "February": 2,
        "March": 3,
        "April": 4,
        "May": 5,
        "June": 6,
        "July": 7,
        "August": 8,
        "September": 9,
        "October": 10,
        "November": 11,
        "December": 12,
    }
    return months.get(month_name)


def format_pacific_time(dt):
    hour = dt.hour % 12 or 12
    suffix = "AM" if dt.hour < 12 else "PM"
    return f"{hour}:{dt.minute:02d} {suffix} PST"


def update_knockout_schedule_times(data, text):
    changed = 0
    date_pattern = re.compile(r"\b(?:Sunday|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday),\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})\b")
    date_matches = list(date_pattern.finditer(text))

    def source_team_pattern(team):
        names = LIVE_SOURCE_ALIASES.get(team, [team])
        return r"(?:%s)" % "|".join(re.escape(name) for name in names)

    for match in data.get("knockout", []):
        home = match.get("resolvedHome")
        away = match.get("resolvedAway")
        if not home or not away:
            continue
        fixture = re.search(
            rf"{source_team_pattern(home)}\s+vs\.?\s+{source_team_pattern(away)}\s+\([^)]*\):\s+(\d{{1,2}}):(\d{{2}})\s*([ap])\.m\.",
            text,
            flags=re.I,
        )
        if not fixture:
            continue
        prior_dates = [date_match for date_match in date_matches if date_match.start() < fixture.start()]
        if not prior_dates:
            continue
        date_match = prior_dates[-1]
        month = month_number(date_match.group(1))
        if not month:
            continue
        day = int(date_match.group(2))
        hour = int(fixture.group(1)) % 12
        minute = int(fixture.group(2))
        if fixture.group(3).lower() == "p":
            hour += 12
        eastern_dt = datetime(2026, month, day, hour, minute, tzinfo=EASTERN_TZ)
        pacific_dt = eastern_dt.astimezone(PACIFIC_TZ)
        before = (match.get("date"), match.get("timePst"))
        match["date"] = pacific_dt.date().isoformat()
        match["timePst"] = format_pacific_time(pacific_dt)
        match["timeSource"] = "refreshed"
        if before != (match.get("date"), match.get("timePst")):
            changed += 1
    return changed


def apply_schedule_score_updates(data, text):
    changed = 0
    sync_knockout(data)
    changed += update_knockout_schedule_times(data, text)
    for match in data.get("matches", []):
        parsed = find_schedule_score(text, match["group"], match["home"], match["away"])
        if not parsed:
            continue
        before = (match.get("homeScore"), match.get("awayScore"), match.get("status"))
        match["homeScore"], match["awayScore"], match["status"] = parsed[0], parsed[1], "FT"
        if before != (match.get("homeScore"), match.get("awayScore"), match.get("status")):
            changed += 1
    for match in data.get("knockout", []):
        parsed = find_knockout_schedule_score(text, match.get("resolvedHome"), match.get("resolvedAway"))
        if not parsed:
            continue
        before = (match.get("homeScore"), match.get("awayScore"), match.get("status"), match.get("winner"), match.get("resultDetail"))
        home_score, away_score, status, winner, detail = parsed
        if status == "Score":
            status = "Live" if is_match_in_live_window(match) else "FT"
        match["homeScore"], match["awayScore"], match["status"], match["winner"], match["resultDetail"] = home_score, away_score, status, winner, detail
        if before != (match.get("homeScore"), match.get("awayScore"), match.get("status"), match.get("winner"), match.get("resultDetail")):
            changed += 1
    if changed:
        sync_knockout(data)
    return changed


def load_data_with_live_check():
    data = load_data()
    schedule_changed = 0
    has_live_window = any(is_match_in_live_window(match) for match in data.get("matches", []) + data.get("knockout", []))
    if has_live_window or any(match.get("status") == "Live" for match in data.get("matches", []) + data.get("knockout", [])):
        try:
            schedule_changed = apply_schedule_score_updates(data, strip_html(fetch_text(SCHEDULE_URL)))
        except (urllib.error.URLError, TimeoutError):
            schedule_changed = 0
        try:
            schedule_changed += apply_schedule_score_updates(data, strip_html(fetch_text(KNOCKOUT_SCHEDULE_URL)))
        except (urllib.error.URLError, TimeoutError):
            pass
    live_changed = apply_live_score_updates(data)
    if schedule_changed or live_changed:
        recalculate_from_matches(data)
        apply_verified_overrides(data)
        sync_knockout(data)
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
    sync_knockout(data)
    snapshot = {
        "lastUpdated": data.get("lastUpdated"),
        "sourceNote": data.get("sourceNote"),
        "groups": data.get("groups", {}),
        "matches": data.get("matches", []),
        "knockout": data.get("knockout", []),
        "playerStats": data.get("playerStats", []),
        "playerStatsNote": data.get("playerStatsNote", ""),
    }
    (ROOT / "world_cup_dynamic_snapshot.json").write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")


def update_project_data_files(data):
    # Keep a source-controlled snapshot beside the Python seed module so refreshes are visible in the repo.
    write_dynamic_snapshot(data)


def football_data_headers():
    token = os.environ.get("FOOTBALL_DATA_API_KEY")
    if not token:
        return None
    return {
        "User-Agent": "Mozilla/5.0 WorldCupLocal/1.0",
        "X-Auth-Token": token,
    }


def football_data_get(path, params=None):
    headers = football_data_headers()
    if not headers:
        return None
    query = f"?{urlencode(params)}" if params else ""
    return fetch_json(f"{FOOTBALL_DATA_API_BASE}{path}{query}", headers=headers)


def espn_scoreboard_get(match_date):
    query = urlencode({"dates": match_date.replace("-", "")})
    return fetch_json(f"{ESPN_SCOREBOARD_URL}?{query}")


def normalize_api_team_name(name):
    aliases = {
        "Cape Verde": "Cabo Verde",
        "Congo DR": "DR Congo",
        "DR Congo": "DR Congo",
        "Czech Republic": "Czechia",
        "Iran": "Iran",
        "IR Iran": "Iran",
        "Ivory Coast": "Côte d'Ivoire",
        "Korea Republic": "South Korea",
        "South Korea": "South Korea",
        "Türkiye": "Türkiye",
        "Turkey": "Türkiye",
        "United States": "United States",
        "United States of America": "United States",
        "USA": "United States",
    }
    return aliases.get((name or "").strip(), (name or "").strip())


def scoreboard_dates(data):
    dates = {match.get("date") for match in data.get("matches", []) + data.get("knockout", []) if match.get("date")}
    dates.add(pacific_now().date().isoformat())
    return sorted(dates)


def espn_event_team(event, home_away):
    competition = (event.get("competitions") or [{}])[0]
    return next((item for item in competition.get("competitors", []) if item.get("homeAway") == home_away), None)


def espn_event_to_api_match(event):
    competition = (event.get("competitions") or [{}])[0]
    home = espn_event_team(event, "home")
    away = espn_event_team(event, "away")
    if not home or not away:
        return None
    status_type = ((competition.get("status") or {}).get("type") or {})
    state = (status_type.get("state") or "").lower()
    completed = bool(status_type.get("completed"))
    if completed or state == "post":
        status = "FINISHED"
    elif state == "in":
        status = "IN_PLAY"
    else:
        status = "SCHEDULED"
    has_real_score = status in {"FINISHED", "IN_PLAY"}
    home_score = int(home.get("score", 0)) if has_real_score and home.get("score") not in (None, "") else None
    away_score = int(away.get("score", 0)) if has_real_score and away.get("score") not in (None, "") else None
    winner = None
    if home.get("winner"):
        winner = "HOME_TEAM"
    elif away.get("winner"):
        winner = "AWAY_TEAM"
    return {
        "utcDate": competition.get("date") or event.get("date"),
        "status": status,
        "homeTeam": {"name": (home.get("team") or {}).get("displayName") or (home.get("team") or {}).get("name")},
        "awayTeam": {"name": (away.get("team") or {}).get("displayName") or (away.get("team") or {}).get("name")},
        "score": {
            "winner": winner,
            "fullTime": {
                "home": home_score,
                "away": away_score,
            },
        },
    }


def fetch_espn_scoreboard_matches(data):
    matches = []
    seen = set()
    for match_date in scoreboard_dates(data):
        try:
            payload = espn_scoreboard_get(match_date)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            continue
        for event in (payload or {}).get("events", []):
            event_id = event.get("id")
            if event_id in seen:
                continue
            seen.add(event_id)
            api_match = espn_event_to_api_match(event)
            if api_match:
                matches.append(api_match)
    return matches


def team_names_match(left, right):
    return normalize_api_team_name(left) == normalize_api_team_name(right)


def api_match_status(api_match):
    status = (api_match.get("status") or "").upper()
    if status in {"FINISHED", "AWARDED"}:
        return "FT"
    if status in {"IN_PLAY", "PAUSED", "LIVE", "EXTRA_TIME", "PENALTY_SHOOTOUT"}:
        return "Live"
    return "Scheduled"


def api_match_score(api_match):
    score = api_match.get("score") or {}
    for key in ("fullTime", "regularTime", "halfTime"):
        value = score.get(key) or {}
        home = value.get("home")
        away = value.get("away")
        if home is not None and away is not None:
            return int(home), int(away)
    return None, None


def api_match_winner(api_match, local_match, home_score, away_score):
    winner = ((api_match.get("score") or {}).get("winner") or "").upper()
    if winner == "HOME_TEAM":
        return local_match.get("resolvedHome") or local_match.get("home")
    if winner == "AWAY_TEAM":
        return local_match.get("resolvedAway") or local_match.get("away")
    if home_score is not None and away_score is not None and home_score != away_score:
        return (local_match.get("resolvedHome") or local_match.get("home")) if home_score > away_score else (local_match.get("resolvedAway") or local_match.get("away"))
    return None


def api_match_detail(api_match):
    score = api_match.get("score") or {}
    penalties = score.get("penalties") or {}
    home_penalties = penalties.get("home")
    away_penalties = penalties.get("away")
    if home_penalties is not None and away_penalties is not None:
        return f"Penalties {home_penalties}-{away_penalties}"
    return None


def apply_api_kickoff(local_match, api_match):
    utc_date = api_match.get("utcDate")
    if not utc_date:
        return 0
    try:
        api_dt = datetime.fromisoformat(utc_date.replace("Z", "+00:00")).astimezone(PACIFIC_TZ)
    except ValueError:
        return 0
    before = (local_match.get("date"), local_match.get("timePst"))
    local_match["date"] = api_dt.date().isoformat()
    local_match["timePst"] = format_pacific_time(api_dt)
    local_match["timeSource"] = "structured-api"
    return int(before != (local_match.get("date"), local_match.get("timePst")))


def local_match_teams(match):
    return match.get("resolvedHome") or match.get("home"), match.get("resolvedAway") or match.get("away")


def find_local_match_for_api(data, api_match):
    home = normalize_api_team_name((api_match.get("homeTeam") or {}).get("name"))
    away = normalize_api_team_name((api_match.get("awayTeam") or {}).get("name"))
    if not home or not away:
        return None
    for match in data.get("matches", []):
        local_home, local_away = local_match_teams(match)
        if team_names_match(local_home, home) and team_names_match(local_away, away):
            return match
        if team_names_match(local_home, away) and team_names_match(local_away, home):
            return match
    sync_knockout(data)
    for match in data.get("knockout", []):
        local_home, local_away = local_match_teams(match)
        if team_names_match(local_home, home) and team_names_match(local_away, away):
            return match
        if team_names_match(local_home, away) and team_names_match(local_away, home):
            return match
    return None


def apply_structured_match_updates(data, api_matches):
    changed = 0
    for api_match in api_matches:
        local = find_local_match_for_api(data, api_match)
        if not local:
            continue
        api_home = normalize_api_team_name((api_match.get("homeTeam") or {}).get("name"))
        local_home, local_away = local_match_teams(local)
        reverse = team_names_match(local_home, normalize_api_team_name((api_match.get("awayTeam") or {}).get("name"))) and team_names_match(local_away, api_home)
        home_score, away_score = api_match_score(api_match)
        if reverse:
            home_score, away_score = away_score, home_score
        status = api_match_status(api_match)
        before = (
            local.get("date"),
            local.get("timePst"),
            local.get("homeScore"),
            local.get("awayScore"),
            local.get("status"),
            local.get("winner"),
            local.get("resultDetail"),
        )
        changed += apply_api_kickoff(local, api_match)
        if home_score is not None and away_score is not None:
            local["homeScore"] = home_score
            local["awayScore"] = away_score
        preserve_finished = status == "Scheduled" and local.get("status") == "FT" and home_score is None and away_score is None
        if not preserve_finished:
            local["status"] = status
        if local in data.get("knockout", []) and not preserve_finished:
            local["winner"] = api_match_winner(api_match, local, home_score, away_score)
            local["resultDetail"] = api_match_detail(api_match)
        if before != (
            local.get("date"),
            local.get("timePst"),
            local.get("homeScore"),
            local.get("awayScore"),
            local.get("status"),
            local.get("winner"),
            local.get("resultDetail"),
        ):
            changed += 1
    if changed:
        sync_knockout(data)
    return changed


def try_refresh_from_structured_api(data):
    if not football_data_headers():
        return None
    payload = football_data_get(
        f"/competitions/{FOOTBALL_DATA_COMPETITION}/matches",
        {"season": FOOTBALL_DATA_SEASON},
    )
    matches = (payload or {}).get("matches", [])
    if not matches:
        return None
    changed = apply_structured_match_updates(data, matches)
    if changed:
        recalculate_from_matches(data)
        sync_knockout(data)
    data["lastUpdated"] = utc_now()
    data["sourceNote"] = f"Primary refresh used football-data.org structured match data ({len(matches)} match records); SB Nation remains the fallback for article-based standings/schedule parsing."
    refresh_player_stats(data)
    update_project_data_files(data)
    save_data(data)
    return data


def try_refresh_from_espn_scoreboard(data):
    matches = fetch_espn_scoreboard_matches(data)
    if not matches:
        return None
    changed = apply_structured_match_updates(data, matches)
    if changed:
        recalculate_from_matches(data)
        sync_knockout(data)
    data["lastUpdated"] = utc_now()
    data["sourceNote"] = f"Primary refresh used ESPN's free public FIFA World Cup scoreboard feed ({len(matches)} match records); football-data.org and SB Nation remain fallbacks."
    refresh_player_stats(data)
    update_project_data_files(data)
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


def fetch_json(url, headers=None):
    request = urllib.request.Request(url, headers=headers or {"User-Agent": "Mozilla/5.0 WorldCupLocal/1.0"})
    context = ssl._create_unverified_context()
    with urllib.request.urlopen(request, timeout=12, context=context) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def try_refresh_from_web(data):
    espn_error = None
    structured_error = None
    structured_configured = bool(football_data_headers())
    try:
        espn_data = try_refresh_from_espn_scoreboard(data)
        if espn_data is not None:
            return espn_data
    except (urllib.error.URLError, TimeoutError, RuntimeError, json.JSONDecodeError) as exc:
        espn_error = exc

    try:
        structured_data = try_refresh_from_structured_api(data)
        if structured_data is not None:
            return structured_data
    except (urllib.error.URLError, TimeoutError, RuntimeError, json.JSONDecodeError) as exc:
        structured_error = exc

    html = fetch_text(STANDINGS_URL)
    text = strip_html(html)
    schedule_text = ""
    try:
        schedule_text = strip_html(fetch_text(SCHEDULE_URL))
    except (urllib.error.URLError, TimeoutError):
        schedule_text = ""
    knockout_schedule_text = ""
    try:
        knockout_schedule_text = strip_html(fetch_text(KNOCKOUT_SCHEDULE_URL))
    except (urllib.error.URLError, TimeoutError):
        knockout_schedule_text = ""
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

    score_changed = apply_schedule_score_updates(data, schedule_text) if schedule_text else 0
    score_changed += apply_schedule_score_updates(data, knockout_schedule_text) if knockout_schedule_text else 0
    live_changed = apply_live_score_updates(data)
    if score_changed or live_changed:
        recalculate_from_matches(data)
        apply_verified_overrides(data)
        sync_knockout(data)

    if changed == 0:
        apply_verified_overrides(data)
        sync_knockout(data)
        score_changed = apply_schedule_score_updates(data, schedule_text) if schedule_text else 0
        score_changed += apply_schedule_score_updates(data, knockout_schedule_text) if knockout_schedule_text else 0
        live_changed = apply_live_score_updates(data)
        if score_changed or live_changed:
            recalculate_from_matches(data)
            apply_verified_overrides(data)
            sync_knockout(data)
        data["lastUpdated"] = utc_now()
        if espn_error:
            api_note = f" ESPN scoreboard unavailable ({espn_error}); used SB Nation fallback."
        elif structured_error:
            api_note = f" Structured API unavailable ({structured_error}); used SB Nation fallback."
        elif structured_configured:
            api_note = " ESPN returned no usable match records and structured API returned no usable match records; used SB Nation fallback."
        else:
            api_note = " ESPN returned no usable match records and structured API not configured; used SB Nation fallback."
        data["sourceNote"] = "Refresh reached the standings source, checked live match pages, and kept verified local corrections where source tables could not be parsed." + api_note
        refresh_player_stats(data)
        update_project_data_files(data)
        save_data(data)
        return data

    apply_verified_overrides(data)
    score_changed = apply_schedule_score_updates(data, schedule_text) if schedule_text else 0
    score_changed += apply_schedule_score_updates(data, knockout_schedule_text) if knockout_schedule_text else 0
    live_changed = apply_live_score_updates(data)
    if score_changed or live_changed:
        recalculate_from_matches(data)
        apply_verified_overrides(data)
        sync_knockout(data)
    data["lastUpdated"] = utc_now()
    if espn_error:
        api_note = f" ESPN scoreboard unavailable ({espn_error}); used SB Nation fallback."
    elif structured_error:
        api_note = f" Structured API unavailable ({structured_error}); used SB Nation fallback."
    elif structured_configured:
        api_note = " ESPN returned no usable match records and structured API returned no usable match records; used SB Nation fallback."
    else:
        api_note = " ESPN returned no usable match records and structured API not configured; used SB Nation fallback."
    data["sourceNote"] = f"Refreshed {changed} group table(s), checked live match pages, and validated stored score corrections." + api_note
    refresh_player_stats(data)
    update_project_data_files(data)
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
