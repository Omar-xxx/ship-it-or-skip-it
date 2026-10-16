import os
from kit_lib import *

# ---------- build ----------
for d in ("poses", "backgrounds", "overlays", "previews"):
    os.makedirs(os.path.join(OUT, d), exist_ok=True)

for pose in POSES:
    pd = os.path.join(OUT, "poses", pose)
    os.makedirs(pd, exist_ok=True)
    for m in MOUTHS:
        for blink in (False, True):
            render(wrap(character(pose, m, blink)), os.path.join(pd, f"{m}{'_blink' if blink else ''}.png"))

for name, s in BGS.items():
    render(wrap(s, 1080, 1920), os.path.join(OUT, "backgrounds", f"{name}.png"))
render(wrap(BGS["grid"] + screen_frame(False), 1080, 1920), os.path.join(OUT, "backgrounds", "grid_screen_layout.png"))
render(wrap(BGS["terminal"] + screen_frame(False), 1080, 1920), os.path.join(OUT, "backgrounds", "terminal_screen_layout.png"))

render(wrap(sticker("SHIP IT", GREEN), 1080, 420), os.path.join(OUT, "overlays", "sticker_ship_it.png"))
render(wrap(sticker("SKIP IT", RED), 1080, 420), os.path.join(OUT, "overlays", "sticker_skip_it.png"))
render(wrap(logo(540, 230), 1080, 520), os.path.join(OUT, "overlays", "logo.png"))

endcard = (BGS["grid"] + logo(540, 330) +
           '<text x="540" y="760" text-anchor="middle" font-family="DejaVu Sans" font-weight="bold" font-size="54" fill="#FFFFFF" '
           f'stroke="{INK}" stroke-width="10" paint-order="stroke">Honest verdicts. No sponsors.</text>' +
           f'<g transform="translate(54 900) scale(0.9)">{character("ship", "E")}</g>')

SCENES = [
    ("1 hook",    "0-3s: shocked, big",       BGS["grid"] + char_hero("shocked", "O")),
    ("2 demo",    "3-30s: point at recording", BGS["grid"] + screen_frame() + char_small("point", "E")),
    ("3 think",   "30-35s: worth it?",         BGS["grid"] + char_hero("think", "rest")),
    ("4 ship",    "verdict + sticker",         BGS["ship"] + sticker("SHIP IT", GREEN).replace('rotate(-5 540 200)', 'translate(0 230) rotate(-5 540 200)') + char_hero("ship", "E")),
    ("5 skip",    "verdict + sticker",         BGS["skip"] + sticker("SKIP IT", RED).replace('rotate(-5 540 200)', 'translate(0 230) rotate(-5 540 200)') + char_hero("skip", "rest")),
    ("6 warn",    "security demo",             BGS["terminal"] + screen_frame() + char_small("warn", "A")),
    ("7 end card", "last 2s",                  endcard),
]
thumbs = []
for name, use, sc in SCENES:
    p = os.path.join(OUT, "previews", name.replace(" ", "_") + ".png")
    render(wrap(sc, 1080, 1920), p)
    thumbs.append((name, use, p))

tw, th, cols = 300, 533, 4
rows = (len(thumbs) + cols - 1) // cols
sheet = Image.new("RGB", (tw * cols, (th + 70) * rows), NAVY)
d = ImageDraw.Draw(sheet)
fb = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
fr = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
for i, (n, use, p) in enumerate(thumbs):
    x, y = (i % cols) * tw, (i // cols) * (th + 70)
    sheet.paste(Image.open(p).convert("RGB").resize((tw, th)), (x, y))
    d.text((x + 12, y + th + 8), n, fill="white", font=fb)
    d.text((x + 12, y + th + 40), use, fill="#9FB3FF", font=fr)
sheet.save(os.path.join(OUT, "scene_sheet.png"))
print("ok")
