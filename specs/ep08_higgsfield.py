"""Ep08 - Higgsfield: ship it or skip it?  Every number here is from the creator's own account (Oct 2026)."""
from explainer import card, pill, text_c, inter, MONO, INK, BLUE, RED, GREEN, NAVY, ease_out, prog

GREY = (110, 110, 120)
AMBER = (240, 160, 30)

def c_title():
    im, d = card(920, 330)
    text_c(d, 460, 50, "Higgsfield", inter(72, 900))
    text_c(d, 460, 150, "AI image · video · voice studio", inter(34, 500), GREY)
    pill(d, 300, 230, "Verdict coming", inter(34, 800), INK)
    return im

def c_good():
    im, d = card(920, 330, border=GREEN)
    for i, s in enumerate(["Image", "Video", "Voice"]):
        x = 60 + i * 280
        d.rounded_rectangle((x, 60, x + 240, 180), 26, fill=(225, 246, 236), outline=GREEN, width=4)
        text_c(d, x + 120, 98, s, inter(44, 800))
    pill(d, 60, 230, "All in one place = saves time", inter(34, 800), GREEN)
    return im

def c_math(lt):
    im, d = card(920, 430, border=RED)
    d.text((50, 40), "Basic plan", font=inter(34, 700), fill=GREY)
    d.text((50, 90), "120 credits / month", font=inter(56, 900), fill=INK)
    if lt > 1.6:
        d.text((50, 190), "1 video clip (default model)", font=inter(34, 600), fill=GREY)
        d.text((50, 236), "= 35 credits", font=inter(56, 900), fill=RED)
    if lt > 3.2:
        pill(d, 50, 340, "≈ 3 clips a month", inter(38, 900), RED)
    return im

def c_burn(t, lt):
    im, d = card(920, 450)
    d.text((50, 36), "My account, Oct 2026", font=inter(32, 700), fill=GREY)
    p = ease_out(prog(lt, 0.3, 2.2))
    left = 120 * (1 - p)
    d.text((50, 90), f"{left:5.0f}", font=MONO(96), fill=RED if left < 20 else INK)
    d.text((370, 130), "credits left", font=inter(40, 700), fill=GREY)
    d.rounded_rectangle((50, 240, 870, 290), 25, fill=(232, 232, 238))
    d.rounded_rectangle((50, 240, 50 + max(50, int(820 * (1 - p))), 290), 25, fill=RED if left < 20 else BLUE)
    if p > 0.98:
        pill(d, 50, 340, "Gone in 4 days", inter(38, 900), RED)
    if t > 17.0:
        pill(d, 450, 340, "Out of credits", inter(38, 900), INK)
    return im

def c_terms(t, lt):
    im, d = card(920, 440, fill=(252, 251, 247))
    d.text((50, 36), "Terms of use", font=inter(32, 700), fill=GREY)
    for i in range(6):
        y = 100 + i * 46
        w = [760, 700, 780, 640, 740, 520][i]
        d.rounded_rectangle((50, y, 50 + w, y + 18), 9, fill=(225, 226, 232))
    if t > 22.3:
        d.rounded_rectangle((40, 186, 880, 290), 14, fill=(255, 236, 236), outline=RED, width=4)
        d.text((65, 205), "Trains on your uploads", font=inter(40, 800), fill=RED)
        d.text((65, 252), "On by default", font=inter(30, 700), fill=INK)
    pill(d, 50, 350, "Read before you upload", inter(32, 800), INK)
    return im

def c_plans():
    im, d = card(920, 360)
    rows = [("Basic", "Try it, then skip", RED), ("Bigger plans", "Only if you post daily", GREEN)]
    for i, (a, b, c) in enumerate(rows):
        y = 60 + i * 130
        d.ellipse((60, y + 10, 110, y + 60), fill=c)
        d.text((140, y), a, font=inter(50, 900), fill=INK)
        d.text((140, y + 62), b, font=inter(32, 600), fill=GREY)
    return im

def c_follow():
    im, d = card(920, 330)
    text_c(d, 460, 60, "Honest verdicts on AI tools", inter(44, 800))
    text_c(d, 460, 125, "Numbers from my own account.", inter(32, 500), GREY)
    d.rounded_rectangle((300, 205, 620, 285), 40, fill=BLUE)
    text_c(d, 460, 222, "Follow", inter(40, 800), (255, 255, 255))
    return im

SCENES = [
    (0.00,  "Higgsfield:", "Ship It or Skip It?", lambda t, lt: c_title()),
    (3.58,  "The Good", "All in One", lambda t, lt: c_good()),
    (8.56,  "The Catch?", "Credits", lambda t, lt: c_math(lt)),
    (14.40, "I Tried It", "I Ran Out", lambda t, lt: c_burn(t, lt)),
    (19.82, "One More Thing", "Read the Terms", lambda t, lt: c_terms(t, lt)),
    (25.82, "So… Ship It", "or Skip It?", None),
    (31.18, "Who Should", "Pay for It?", lambda t, lt: c_plans()),
    (35.70, "Ship It", "or Skip It?", lambda t, lt: c_follow()),
]
STAMPS = [(30.20, 31.18, "SKIP IT")]
POSE_CUES = [(0, "explain"), (3.58, "ship"), (8.56, "think"), (10.36, "point"), (14.40, "shocked"),
             (19.82, "warn"), (25.82, "think"), (30.20, "skip"), (31.18, "explain"), (35.70, "idle")]
