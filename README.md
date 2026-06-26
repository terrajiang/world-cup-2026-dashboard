# World Cup 2026 Dashboard

Local interactive dashboard for World Cup 2026 group standings, player stats, and knockout tree projections.

## Run locally

```bash
python3 server.py
```

Open:

```text
http://127.0.0.1:8080/
```

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

The dashboard uses local seed data plus a public standings refresh attempt. Refresh writes `world_cup_dynamic_snapshot.json`, so `world_cup_data.py` can load the latest refreshed snapshot instead of falling back to the original seed. Refresh also regenerates the standings PNG.

Player stats show every player currently available in the local stats feed; a full official player feed can be connected later.
