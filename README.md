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

## Notes

The dashboard uses local seed data plus a public standings refresh attempt. Player stats show every player currently available in the local stats feed; a full official player feed can be connected later.
