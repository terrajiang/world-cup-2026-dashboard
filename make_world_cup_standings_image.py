from PIL import Image, ImageDraw, ImageFont


OUT = "world_cup_2026_group_standings_june25.png"

groups = {
    "A": [("Mexico", 9), ("South Africa", 4), ("South Korea", 3), ("Czechia", 1)],
    "B": [("Switzerland", 7), ("Canada", 4), ("Bosnia and Herzegovina", 4), ("Qatar", 1)],
    "C": [("Brazil", 7), ("Morocco", 7), ("Scotland", 3), ("Haiti", 0)],
    "D": [("United States", 6), ("Australia", 3), ("Paraguay", 3), ("Türkiye", 0)],
    "E": [("Germany", 6), ("Côte d'Ivoire", 6), ("Ecuador", 4), ("Curaçao", 1)],
    "F": [("Netherlands", 4), ("Japan", 4), ("Sweden", 3), ("Tunisia", 0)],
    "G": [("Egypt", 4), ("Iran", 2), ("Belgium", 2), ("New Zealand", 1)],
    "H": [("Spain", 4), ("Uruguay", 2), ("Cabo Verde", 2), ("Saudi Arabia", 1)],
    "I": [("France", 6), ("Norway", 6), ("Senegal", 0), ("Iraq", 0)],
    "J": [("Argentina", 6), ("Austria", 3), ("Algeria", 3), ("Jordan", 0)],
    "K": [("Colombia", 6), ("Portugal", 4), ("DR Congo", 1), ("Uzbekistan", 0)],
    "L": [("England", 4), ("Ghana", 4), ("Croatia", 3), ("Panama", 0)],
}

advanced = {
    "Mexico",
    "South Africa",
    "Switzerland",
    "Canada",
    "Brazil",
    "Morocco",
    "United States",
    "Germany",
    "France",
    "Norway",
    "Argentina",
    "Colombia",
}

eliminated = {
    "Czechia",
    "Qatar",
    "Haiti",
    "Türkiye",
    "Tunisia",
    "Jordan",
    "Panama",
}

third_place = {teams[2][0] for teams in groups.values()}

W, H = 2400, 1800
MARGIN = 86
GAP_X = 40
GAP_Y = 42
COLS = 4
ROWS = 3
CARD_W = (W - 2 * MARGIN - (COLS - 1) * GAP_X) // COLS
CARD_H = 395

BG = "#f6f4ef"
INK = "#15171a"
MUTED = "#858585"
LINE = "#ded8cc"
CARD = "#fffdf8"
HEADER = "#0f3d3e"
ADV_FILL = "#d9f0df"
ADV_TEXT = "#0d6b35"
ELIM_FILL = "#efefef"
ELIM_TEXT = "#9a9a9a"
THIRD_FILL = "#fff3bf"

FONT_DIR = "/System/Library/Fonts/Supplemental"
regular = ImageFont.truetype(f"{FONT_DIR}/Arial.ttf", 34)
bold = ImageFont.truetype(f"{FONT_DIR}/Arial Bold.ttf", 34)
small = ImageFont.truetype(f"{FONT_DIR}/Arial.ttf", 26)
small_bold = ImageFont.truetype(f"{FONT_DIR}/Arial Bold.ttf", 26)
title_font = ImageFont.truetype(f"{FONT_DIR}/Arial Bold.ttf", 72)
subtitle_font = ImageFont.truetype(f"{FONT_DIR}/Arial.ttf", 32)
group_font = ImageFont.truetype(f"{FONT_DIR}/Arial Bold.ttf", 42)
pts_font = ImageFont.truetype(f"{FONT_DIR}/Arial Bold.ttf", 34)
label_font = ImageFont.truetype(f"{FONT_DIR}/Arial Bold.ttf", 24)


def rounded_rectangle(draw, xy, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def fit_font(draw, text, bold_face, max_w, min_size=25):
    font_name = "Arial Bold.ttf" if bold_face else "Arial.ttf"
    for size in range(34, min_size - 1, -1):
        font = ImageFont.truetype(f"{FONT_DIR}/{font_name}", size)
        if draw.textlength(text, font=font) <= max_w:
            return font
    return ImageFont.truetype(f"{FONT_DIR}/Arial Narrow Bold.ttf" if bold_face else f"{FONT_DIR}/Arial Narrow.ttf", 28)


img = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(img)

draw.text((MARGIN, 58), "World Cup 2026 Group Standings", font=title_font, fill=INK)
draw.text(
    (MARGIN, 142),
    "Current points only - all 12 groups / 48 teams - retrieved June 25, 2026 at 3:03 PM PDT",
    font=subtitle_font,
    fill="#4d5157",
)

legend_y = 200
legend = [
    (ADV_FILL, ADV_TEXT, "Guaranteed advance"),
    (ELIM_FILL, ELIM_TEXT, "Guaranteed eliminated"),
    (THIRD_FILL, INK, "Bold = current 3rd-place comparison"),
]
x = MARGIN
for fill, color, text in legend:
    rounded_rectangle(draw, (x, legend_y, x + 34, legend_y + 34), 8, fill, outline=LINE)
    draw.text((x + 48, legend_y + 3), text, font=small, fill=color)
    x += int(draw.textlength(text, font=small)) + 95

start_y = 270
for idx, (group, teams) in enumerate(groups.items()):
    row = idx // COLS
    col = idx % COLS
    x0 = MARGIN + col * (CARD_W + GAP_X)
    y0 = start_y + row * (CARD_H + GAP_Y)
    x1 = x0 + CARD_W
    y1 = y0 + CARD_H

    rounded_rectangle(draw, (x0, y0, x1, y1), 18, CARD, outline=LINE, width=2)
    draw.rectangle((x0, y0, x1, y0 + 76), fill=HEADER)
    draw.rounded_rectangle((x0, y0, x1, y0 + 92), radius=18, outline=HEADER, width=2)
    draw.rectangle((x0, y0 + 56, x1, y0 + 92), fill=HEADER)
    draw.text((x0 + 26, y0 + 17), f"Group {group}", font=group_font, fill="white")
    draw.text((x1 - 78, y0 + 25), "PTS", font=label_font, fill="#dbe8e7")

    for i, (team, pts) in enumerate(teams):
        ry = y0 + 98 + i * 69
        is_adv = team in advanced
        is_elim = team in eliminated
        is_third = team in third_place
        if is_adv:
            fill = ADV_FILL
            color = ADV_TEXT
        elif is_elim:
            fill = ELIM_FILL
            color = ELIM_TEXT
        elif is_third:
            fill = THIRD_FILL
            color = INK
        else:
            fill = "#ffffff"
            color = INK

        rounded_rectangle(draw, (x0 + 18, ry, x1 - 18, ry + 54), 10, fill, outline="#ebe7de")
        rank_color = "#777b80" if not is_elim else "#b6b6b6"
        draw.text((x0 + 34, ry + 10), str(i + 1), font=small_bold, fill=rank_color)
        font = fit_font(draw, team, is_third, CARD_W - 160)
        draw.text((x0 + 78, ry + 8), team, font=font, fill=color)
        draw.text((x1 - 70, ry + 8), str(pts), font=pts_font, fill=color)

note_y = H - 112
draw.line((MARGIN, note_y - 22, W - MARGIN, note_y - 22), fill=LINE, width=2)
draw.text(
    (MARGIN, note_y),
    "Sources checked: SB Nation standings/knockout updates; Guardian live blogs for in-progress Group E movement on Jun 25.",
    font=small,
    fill="#4d5157",
)
draw.text(
    (MARGIN, note_y + 38),
    "Style encodes status; no goal difference, wins, draws, or losses are shown.",
    font=small,
    fill="#4d5157",
)

img.save(OUT, quality=95)
print(OUT)
