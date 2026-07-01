# World Cup 2026 Dashboard

Local interactive dashboard for World Cup 2026 group standings, player stats, and knockout tree projections.

## Run locally

For people who are comfortable with Terminal:

```bash
python3 server.py
```

Open:

```text
http://127.0.0.1:8080/
```

## Beginner Instructions

GitHub may look like a page full of files. That is normal. The steps below download the folder and open the dashboard on your own computer.

### Mac Users

1. Open the GitHub link.
2. Click the green **Code** button.
3. Click **Download ZIP**.
4. Find the downloaded ZIP file, usually in **Downloads**.
5. Double-click the ZIP file to unzip it.
6. Right-click the unzipped folder and choose **New Terminal at Folder**.
7. Paste this into Terminal and press **Enter**:

```bash
python3 server.py
```

8. Keep the Terminal window open.
9. Open this link in your browser:

```text
http://127.0.0.1:8080/
```

### Windows Users

1. Open the GitHub link.
2. Click the green **Code** button.
3. Click **Download ZIP**.
4. Find the downloaded ZIP file, usually in **Downloads**.
5. Double-click the ZIP file to unzip it.
6. Open the unzipped folder.
7. Click the address bar at the top of the folder window.
8. Type `cmd` and press **Enter**.
9. In the black window that opens, paste this and press **Enter**:

```bash
python server.py
```

10. Keep the black command window open.
11. Open this link in your browser:

```text
http://127.0.0.1:8080/
```

If Windows says Python is not installed, install Python from <https://www.python.org/downloads/> and make sure to check **Add python.exe to PATH** during installation.

## Troubleshooting

### The dashboard does not open

- Make sure the Terminal or black command window is still open.
- Make sure the browser link is exactly `http://127.0.0.1:8080/`.
- If the command window shows an error, close it and try the steps again from the unzipped folder.

### Mac: "Address already in use" or port 8080 is busy

This usually means the dashboard is already running in another Terminal window.

1. First try opening `http://127.0.0.1:8080/` in your browser.
2. If it still does not work, paste this into Terminal and press **Enter**:

```bash
lsof -nP -iTCP:8080 -sTCP:LISTEN
```

3. Look for the number under `PID`.
4. Replace `PID_NUMBER` below with that number, then press **Enter**:

```bash
kill PID_NUMBER
```

5. Start the dashboard again:

```bash
python3 server.py
```

### Windows: port 8080 is busy

This usually means the dashboard is already running in another command window.

1. First try opening `http://127.0.0.1:8080/` in your browser.
2. If it still does not work, close any old black command windows that mention `server.py`.
3. Start the dashboard again with:

```bash
python server.py
```

If that still does not work, restart the computer and try again.

## Features

- Refreshable group standings
- Standings table with GD, GF, and bold Pts
- Hidden-but-retained match score editing backend
- Player stats table with goals, assists, yellow cards, and red cards
- Team flags in standings, player stats, and knockout tree
- Split knockout tree centered around the Final

## Data Sources

The dashboard is fan-made and uses multiple sources. Refresh prefers a free public scoreboard feed, then falls back to optional structured API data, public article/live pages, and local verified corrections.

### Primary structured source

- **ESPN public FIFA World Cup scoreboard feed**: primary free/no-key source for match status, kickoff time, live/finished state, and scores.
  - <https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard>
  - The dashboard calls the scoreboard by match date so it can refresh group-stage and knockout matches across the tournament.

### Optional structured source

- **football-data.org API**: optional fallback source for match status, kickoff time, live/finished state, and scores when `FOOTBALL_DATA_API_KEY` is set.
  - Documentation: <https://www.football-data.org/documentation/quickstart>
  - The dashboard calls `/v4/competitions/{competition}/matches`.
  - Free tier access exists, but live scores require a paid plan, so ESPN remains the default no-key live source.
  - Defaults:
    - `FOOTBALL_DATA_COMPETITION=WC`
    - `FOOTBALL_DATA_SEASON=2026`
  - To enable it as an additional fallback:

```bash
export FOOTBALL_DATA_API_KEY="your_api_key_here"
python3 server.py
```

### Fallback public article sources

- **SB Nation World Cup standings**: fallback source for group standings.
  - <https://www.sbnation.com/soccer/1117905/world-cup-standings-updated-full-list-of-teams>
- **SB Nation World Cup schedule**: fallback source for group-stage schedule and scores.
  - <https://www.sbnation.com/soccer/1117513/world-cup-schedule-2026-how-to-watch-every-match-scores-and-more>
- **SB Nation Round of 32 schedule/scores**: fallback source for knockout schedule, times, and scores.
  - <https://www.sbnation.com/soccer/1120771/world-cup-schedule-scores-round-32>
- **SB Nation Golden Boot table**: source for player goals, assists, and minutes.
  - <https://www.sbnation.com/fifa-world-cup/1118693/world-cup-2026-golden-boot-standings>

### Live blog sources

- **The Guardian live blogs**: used for a hardcoded set of late group-stage live-score checks when those pages are configured in `server.py`.
  - Examples include Guardian live pages for New Zealand-Belgium, Egypt-Iran, Cabo Verde-Saudi Arabia, Uruguay-Spain, Norway-France, Senegal-Iraq, Algeria-Austria, Jordan-Argentina, Colombia-Portugal, DR Congo-Uzbekistan, Panama-England, and Croatia-Ghana.

### Local sources and corrections

- `world_cup_data.py`: seed data, local match schedule, initial standings, player stat seed rows, and verified local corrections.
- `world_cup_cache.json`: runtime cache written by the local server.
- `world_cup_dynamic_snapshot.json`: refreshed snapshot written after successful refreshes so the repo can preserve the latest local data state.
- Verified local overrides in `server.py`: trusted corrections for selected group-stage scores, knockout scores, third-place assignment, and known kickoff-time changes.

## Notes

Disclaimer: this is a fan-made local dashboard, not an official FIFA product. The standings, projections, player stats, schedules, and historical summaries are provided for personal analysis and may contain assumptions or stale data. Verify against official FIFA sources before relying on the information publicly.

The dashboard uses local seed data plus public refresh attempts for standings, live scores, and player goals/assists. Refresh writes `world_cup_dynamic_snapshot.json`, so `world_cup_data.py` can load the latest refreshed snapshot instead of falling back to the original seed.

`make_world_cup_standings_image.py` is kept as a deprecated manual utility. Run it directly if you want to regenerate `world_cup_2026_group_standings.png` from the latest local cache.

Player stats refresh from the current Golden Boot table when the online source is reachable. Yellow and red cards stay at 0 until a reliable card feed is connected.
