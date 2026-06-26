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
- Image tab that overwrites and previews `world_cup_2026_group_standings.png`

## Notes

Disclaimer: this is a fan-made local dashboard, not an official FIFA product. The standings, projections, player stats, schedules, historical summaries, and generated images are provided for personal analysis and may contain assumptions or stale data. Verify against official FIFA sources before relying on the information publicly.

The dashboard uses local seed data plus public refresh attempts for standings, live scores, and player goals/assists. Refresh writes `world_cup_dynamic_snapshot.json`, so `world_cup_data.py` can load the latest refreshed snapshot instead of falling back to the original seed. Refresh also regenerates the standings PNG.

Player stats refresh from the current Golden Boot table when the online source is reachable. Yellow and red cards stay at 0 until a reliable card feed is connected.
