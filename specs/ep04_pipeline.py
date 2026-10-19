"""Ep04 - How I animate this character (mood: upbeat)"""
import os, math
from PIL import Image, ImageDraw
from explainer import card_cta, card, pill, text_c, inter, MONO, INK, BLUE, RED, GREEN, ORANGE, NAVY, ease_out, HERE

GREY = (110, 110, 120)
_faces = {}
def face(m):
    if m not in _faces:
        im = Image.open(os.path.join(HERE, "poses", "idle", f"{m}.png")).convert("RGBA")
        _faces[m] = im.crop((300, 240, 780, 720)).resize((170, 170), Image.LANCZOS)
    return _faces[m]

def c_overview(lt):
    im, d = card(920, 300)
    steps = ["Voice", "Script", "Lip-sync", "Cards"]
    for i, s in enumerate(steps):
        if lt < 0.3 + i * 0.45: break
        x = 40 + i * 215
        d.rounded_rectangle((x, 90, x + 185, 190), 24, fill=(230, 236, 252), outline=BLUE, width=3)
        text_c(d, x + 92, 120, s, inter(36, 800))
        if i < 3: d.polygon([(x + 192, 128), (x + 210, 140), (x + 192, 152)], fill=BLUE)
    text_c(d, 460, 225, "4 steps. All automated.", inter(32, 600), GREY)
    return im

def c_voice(t):
    im, d = card(920, 420)
    d.text((50, 40), "Step 1 · The voice", font=inter(32, 700), fill=GREY)
    for i in range(46):
        h = 18 + 70 * abs(math.sin(i * 0.7 + t * 6)) * (0.5 + 0.5 * math.sin(i * 0.23))
        x = 55 + i * 18
        d.rounded_rectangle((x, 175 - h, x + 10, 175 + h), 5, fill=BLUE)
    for i, s in enumerate(["2 min of my voice", "cleaned up", "cloned"]):
        x = [50, 400, 640][i]
        pill(d, x, 290, s, inter(30, 800), [INK, BLUE, GREEN][i])
    d.text((50, 368), "Voice clone: Fish Audio (paid plan)", font=inter(26, 500), fill=GREY)
    return im

def c_tags():
    im, d = card(920, 400, fill=NAVY)
    d.text((50, 40), "Step 2 · Emotion tags", font=inter(32, 700), fill=(150, 165, 200))
    lines = [("[surprised]", " That repo?"), ("[thinking]", " Is it worth it?"), ("[confident]", " Skip it.")]
    for i, (tag, rest) in enumerate(lines):
        y = 120 + i * 85
        f = MONO(40)
        l, _, r, _ = d.textbbox((0, 0), tag, font=f)
        d.rounded_rectangle((44, y - 8, 56 + r - l, y + 54), 10, fill=(255, 122, 26))
        d.text((50, y), tag, font=f, fill=(255, 255, 255))
        d.text((60 + r - l, y), rest, font=f, fill=(230, 235, 245))
    return im

def c_mouths(t, blink_badge=False):
    im, d = card(920, 430)
    d.text((50, 36), "Step 3 · Auto lip-sync", font=inter(32, 700), fill=GREY)
    ms = ["rest", "A", "O", "E"]
    act = int(t * 7) % 4
    for i, m in enumerate(ms):
        x = 55 + i * 210
        on = i == act
        d.rounded_rectangle((x - 8, 92, x + 186, 286), 26, fill=(230, 236, 252) if on else (246, 246, 248), outline=BLUE if on else (220, 220, 228), width=5 if on else 2)
        im.alpha_composite(face(m), (x + 4, 104))
        d = ImageDraw.Draw(im)
    pill(d, 50, 320, "30× per second", inter(34, 900), BLUE)
    if blink_badge: pill(d, 420, 320, "+ blinks on its own", inter(34, 900), INK)
    return im

def c_code():
    im, d = card(920, 400, fill=NAVY)
    d.text((50, 40), "Step 4 · Cards + captions", font=inter(32, 700), fill=(150, 165, 200))
    code = [("def", (255, 122, 26)), (" card_commit", (61, 255, 143)), ("(badge=True):", (230, 235, 245))]
    x = 50
    for s, c in code:
        d.text((x, 130), s, font=MONO(40), fill=c); l, _, r, _ = d.textbbox((0, 0), s, font=MONO(40)); x += r - l
    d.text((50, 200), '  pill("14 months ago")', font=MONO(40), fill=(230, 235, 245))
    d.text((50, 270), "  # every frame = Python", font=MONO(40), fill=(120, 140, 180))
    return im

def c_cost():
    im, d = card(920, 330)
    rows = [("Animation code", "Free", GREEN), ("Voice clone", "Paid plan", INK)]
    for i, (a, b, c) in enumerate(rows):
        y = 70 + i * 110
        d.text((60, y), a, font=inter(46, 800), fill=INK)
        pill(d, 600, y - 4, b, inter(36, 900), c)
    return im

def c_render(lt):
    im, d = card(920, 340)
    p = ease_out(min(1, lt / 2.2))
    d.text((50, 50), "Rendering reel.mp4", font=inter(38, 800), fill=INK)
    d.rounded_rectangle((50, 130, 870, 180), 25, fill=(232, 232, 238))
    d.rounded_rectangle((50, 130, 50 + int(820 * p), 180), 25, fill=GREEN)
    pill(d, 50, 230, "≈ 2 minutes", inter(34, 900), INK)
    pill(d, 370, 230, "0 credits", inter(34, 900), GREEN)
    return im

def c_github():
    im, d = card(920, 340)
    text_c(d, 460, 55, "The code is going public", inter(46, 900))
    text_c(d, 460, 125, "Open-source on GitHub · link in bio soon", inter(30, 500), GREY)
    d.rounded_rectangle((300, 210, 620, 290), 40, fill=BLUE)
    text_c(d, 460, 227, "Follow", inter(40, 800), (255, 255, 255))
    return im

SCENES = [
    (0.00,  "This Character Is", "Made by Code", lambda t, lt: c_overview(lt)),
    (5.22,  "Step 1", "The Voice", lambda t, lt: c_voice(t)),
    (10.86, "Step 2", "Emotion Tags", lambda t, lt: c_tags()),
    (18.76, "Step 3", "Auto Lip-Sync", lambda t, lt: c_mouths(t, blink_badge=t > 30.52)),
    (32.84, "Step 4", "Cards by Code", lambda t, lt: c_code()),
    (37.36, "Is This Pipeline", "Worth It?", lambda t, lt: c_cost()),
    (41.10, "Render Time", "2 Minutes", lambda t, lt: c_render(lt)),
    (44.76, "Want the", "Code?", lambda t, lt: card_cta("CODE", "the GitHub link + setup", lt)),
]
STAMPS = [(43.80, 44.76, "SHIP IT", GREEN)]
POSE_CUES = [(0, "explain"), (5.22, "point"), (18.76, "point"), (30.52, "idle"), (32.84, "point"),
             (37.36, "think"), (41.10, "explain"), (43.80, "ship"), (44.76, "explain")]

# v4 chapter bar + counter
CHAPTERS = ["the pipeline", "voice", "emotion tags", "lip-sync", "cards", "the cost", "render", "the code"]
COUNTER = ("STEP", [(0, "0/4", BLUE), (5.22, "1/4", BLUE), (10.86, "2/4", BLUE), (18.76, "3/4", BLUE), (32.84, "4/4", BLUE),
                    (37.36, "0 CREDITS", GREEN)])
