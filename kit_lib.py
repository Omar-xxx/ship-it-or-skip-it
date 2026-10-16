import os, random, cairosvg
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.dirname(os.path.abspath(__file__))
INK, SKIN, ORANGE, ORANGE_D = "#111111", "#F4EFE6", "#FF7A1A", "#E2621A"
BLUE, GREEN, RED, YELLOW, NAVY = "#1E5BFF", "#19C37D", "#FF3B3B", "#FFD23F", "#0B1020"
S = 14

# ---------- face parts ----------
MOUTHS = {
    "rest": f'<path d="M500 615 Q540 640 580 615" fill="none" stroke="{INK}" stroke-width="{S}" stroke-linecap="round"/>',
    "A": f'<path d="M488 598 Q540 590 592 598 Q588 682 540 688 Q492 682 488 598 Z" fill="{INK}" stroke="{INK}" stroke-width="{S}" stroke-linejoin="round"/>'
         f'<path d="M510 668 Q540 650 570 668 Q556 682 540 683 Q524 682 510 668 Z" fill="#E8603C"/>',
    "O": f'<ellipse cx="540" cy="630" rx="28" ry="38" fill="{INK}"/>',
    "E": f'<path d="M478 602 Q540 614 602 602 Q592 656 540 660 Q488 656 478 602 Z" fill="{INK}" stroke="{INK}" stroke-width="{S}" stroke-linejoin="round"/>'
         f'<path d="M492 610 Q540 620 588 610 L584 626 Q540 634 496 626 Z" fill="#FFFFFF"/>',
}

def dots(dx=0, dy=0, r=17):
    return f'<circle cx="{435+dx}" cy="{462+dy}" r="{r}" fill="{INK}"/><circle cx="{645+dx}" cy="{462+dy}" r="{r}" fill="{INK}"/>'

EYES = {
    "normal": dots(),
    "side": dots(20, 0),
    "up": dots(14, -22),
    "wide": dots(0, 0, 27) + '<circle cx="444" cy="452" r="8" fill="#fff"/><circle cx="654" cy="452" r="8" fill="#fff"/>',
    "happy": f'<path d="M413 472 Q435 444 457 472 M623 472 Q645 444 667 472" fill="none" stroke="{INK}" stroke-width="{S}" stroke-linecap="round"/>',
}
BLINK = f'<path d="M418 462 L452 462 M628 462 L662 462" stroke="{INK}" stroke-width="{S}" stroke-linecap="round"/>'

def brow(d):
    return f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="16" stroke-linecap="round"/>'
BROWS = {
    "normal": brow("M405 362 Q437 346 470 360 M610 360 Q643 346 675 362"),
    "raised": brow("M405 362 Q437 346 470 360 M610 340 Q643 318 675 338"),
    "angry":  brow("M405 345 L470 372 M610 372 L675 345"),
    "worried": brow("M405 368 L470 344 M610 344 L675 368"),
    "high":   brow("M405 340 Q437 318 470 336 M610 336 Q643 318 675 340"),
}

# ---------- limbs ----------
def arm(d):
    return (f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="66" stroke-linecap="round"/>'
            f'<path d="{d}" fill="none" stroke="{ORANGE}" stroke-width="40" stroke-linecap="round"/>')
def hand(x, y, r=40):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{SKIN}" stroke="{INK}" stroke-width="11"/>'
def digit(x1, y1, x2, y2):
    return (f'<path d="M{x1} {y1} L{x2} {y2}" stroke="{INK}" stroke-width="40" stroke-linecap="round"/>'
            f'<path d="M{x1} {y1} L{x2} {y2}" stroke="{SKIN}" stroke-width="18" stroke-linecap="round"/>')

L_DOWN = ""
R_DOWN = ""

POSES = {
    # name: (back layer, front layer, eyes, brows, use)
    "idle":    (L_DOWN + R_DOWN, "", "normal", "normal", "neutral talking"),
    "explain": (L_DOWN + arm("M680 790 Q820 840 840 640"),
                hand(845, 608) + digit(845, 580, 845, 530),
                "normal", "raised", "making a point"),
    "point":   (L_DOWN + arm("M680 790 Q800 800 900 700"),
                hand(912, 688) + digit(925, 672, 990, 600), "side", "normal", "look at the screen"),
    "think":   (L_DOWN + arm("M680 790 Q790 880 650 745"),
                hand(618, 712, 44), "up", "raised", "is it worth it?"),
    "ship":    (L_DOWN + arm("M680 790 Q800 860 820 700"),
                hand(825, 680, 44) + digit(812, 650, 812, 585), "happy", "normal", "verdict: ship it"),
    "skip":    (L_DOWN + arm("M680 790 Q820 800 840 900"),
                hand(845, 925, 44) + digit(840, 955, 840, 1022), "normal", "angry", "verdict: skip it"),
    "shocked": (arm("M405 790 Q290 770 318 630") + arm("M675 790 Q790 770 762 630"),
                hand(322, 610, 44) + hand(758, 610, 44), "wide", "high", "hook: wait, what?"),
    "warn":    (L_DOWN + arm("M680 790 Q800 780 830 650"),
                hand(838, 650, 42) +
                f'<path d="M760 420 L850 392 L940 420 L940 500 Q940 580 850 620 Q760 580 760 500 Z" fill="{YELLOW}" stroke="{INK}" stroke-width="13" stroke-linejoin="round"/>'
                f'<path d="M850 445 L850 530" stroke="{INK}" stroke-width="20" stroke-linecap="round"/><circle cx="850" cy="570" r="12" fill="{INK}"/>',
                "normal", "angry", "security warning"),
}

def character(pose, mouth="rest", blink=False):
    back, front, eyes, brows, _ = POSES[pose]
    e = EYES["happy"] if eyes == "happy" else (BLINK if blink else EYES[eyes])
    return f'''
<path d="M220 1090 Q230 810 400 745 L680 745 Q850 810 860 1090 Z" fill="{ORANGE}" stroke="{INK}" stroke-width="{S}" stroke-linejoin="round"/>
<path d="M495 770 L485 880 M585 770 L595 880" stroke="{INK}" stroke-width="10" stroke-linecap="round"/>
<circle cx="485" cy="888" r="11" fill="{SKIN}" stroke="{INK}" stroke-width="8"/><circle cx="595" cy="888" r="11" fill="{SKIN}" stroke="{INK}" stroke-width="8"/>
<path d="M500 945 L540 932 L580 945 L580 980 Q580 1015 540 1032 Q500 1015 500 980 Z" fill="{BLUE}" stroke="{INK}" stroke-width="9" stroke-linejoin="round"/>
<path d="M522 980 L536 995 L560 965" fill="none" stroke="{SKIN}" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>
{back}
<ellipse cx="540" cy="560" rx="275" ry="255" fill="{ORANGE_D}" stroke="{INK}" stroke-width="{S}"/>
<circle cx="540" cy="480" r="230" fill="{SKIN}" stroke="{INK}" stroke-width="{S}"/>
<rect x="350" y="398" width="172" height="128" rx="22" fill="#FFFFFF" fill-opacity="0.3" stroke="{INK}" stroke-width="{S+2}"/>
<rect x="558" y="398" width="172" height="128" rx="22" fill="#FFFFFF" fill-opacity="0.3" stroke="{INK}" stroke-width="{S+2}"/>
<path d="M522 450 Q540 438 558 450 M350 440 L318 430 M730 440 L762 430" fill="none" stroke="{INK}" stroke-width="{S}" stroke-linecap="round"/>
{BROWS[brows]}
{e}
{MOUTHS[mouth]}
{front}'''

def wrap(inner, w=1080, h=1080):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">{inner}</svg>'

# ---------- backgrounds (9:16) ----------
def rays(c1, c2, cx=540, cy=1350, n=28):
    import math
    out = f'<rect width="1080" height="1920" fill="{c1}"/>'
    for i in range(0, n, 2):
        a1, a2 = 2*math.pi*i/n, 2*math.pi*(i+1)/n
        x1, y1 = cx + 3000*math.cos(a1), cy + 3000*math.sin(a1)
        x2, y2 = cx + 3000*math.cos(a2), cy + 3000*math.sin(a2)
        out += f'<path d="M{cx} {cy} L{x1:.0f} {y1:.0f} L{x2:.0f} {y2:.0f} Z" fill="{c2}"/>'
    return out

def big_word(txt, fill):
    return (f'<g transform="rotate(-5 540 330)"><text x="540" y="380" text-anchor="middle" font-family="DejaVu Sans" font-weight="bold" '
            f'font-size="190" fill="{fill}" stroke="{INK}" stroke-width="16" paint-order="stroke" letter-spacing="-4">{txt}</text></g>')

def bg_grid():
    s = f'<rect width="1080" height="1920" fill="{BLUE}"/>'
    for x in range(0, 1081, 90):
        s += f'<path d="M{x} 0 L{x} 1920" stroke="#4A7BFF" stroke-width="2"/>'
    for y in range(0, 1921, 90):
        s += f'<path d="M0 {y} L1080 {y}" stroke="#4A7BFF" stroke-width="2"/>'
    glyphs = [("&lt;/&gt;", 120, 260, -12, 80), ("{ }", 880, 210, 10, 90), ("✦", 960, 620, 0, 70), ("$_", 90, 760, 8, 70),
              ("✦", 170, 470, 0, 46), ("01", 840, 860, -8, 64), ("⌘", 540, 140, 0, 60)]
    for t, x, y, r, fs in glyphs:
        s += (f'<text x="{x}" y="{y}" transform="rotate({r} {x} {y})" text-anchor="middle" font-family="DejaVu Sans Mono" '
              f'font-weight="bold" font-size="{fs}" fill="#FFFFFF" fill-opacity="0.35">{t}</text>')
    return s

def bg_terminal():
    rnd = random.Random(7)
    toks = ["sudo", "chmod", "curl", "--token", "fetch()", "eval(", "0x7f", "ssh", "git clone", "rm -rf", "npm i", "PERMISSIONS", "allow:*", "api_key=", "import os", "exec"]
    s = f'<rect width="1080" height="1920" fill="{NAVY}"/>'
    for i, y in enumerate(range(70, 1900, 54)):
        line = "  ".join(rnd.choice(toks) for _ in range(rnd.randint(3, 6)))
        op = 0.10 + 0.25 * rnd.random()
        s += (f'<text x="40" y="{y}" font-family="DejaVu Sans Mono" font-size="30" fill="#3DFF8F" fill-opacity="{op:.2f}">'
              f'<tspan fill="#3DFF8F" fill-opacity="0.6">$ </tspan>{line}</text>')
    s += '<rect y="0" width="1080" height="1920" fill="url(#vig)"/>'
    return ('<defs><radialGradient id="vig" cx="50%" cy="60%" r="70%"><stop offset="55%" stop-color="#000" stop-opacity="0"/>'
            '<stop offset="100%" stop-color="#000" stop-opacity="0.6"/></radialGradient></defs>' + s)

BGS = {
    "grid": bg_grid(),
    "terminal": bg_terminal(),
    "ship": rays(GREEN, "#14AE6E"),
    "skip": rays(RED, "#E52F2F"),
}
POSE_BG = {"idle": "grid", "explain": "grid", "point": "grid", "think": "grid",
           "shocked": "grid", "warn": "terminal", "ship": "ship", "skip": "skip"}

def render(svgtxt, path):
    cairosvg.svg2png(bytestring=svgtxt.encode(), write_to=path)



import re as _re
def outlined(svg_text):
    """cairosvg ignores paint-order: draw each stroked <text> twice (stroke first, fill on top)."""
    def fix(m):
        el = m.group(0)
        fill_only = _re.sub(r' stroke="[^"]*"| stroke-width="[^"]*"| paint-order="[^"]*"', '', el)
        return el + fill_only
    return _re.sub(r'<text[^>]*paint-order="stroke"[^>]*>.*?</text>', fix, svg_text)

# ---------- branding & layouts ----------
def logo(cx=540, cy=300, k=1.0):
    t = lambda y, txt, fill, fs: (f'<text x="{cx}" y="{cy+y*k}" text-anchor="middle" font-family="DejaVu Sans" font-weight="bold" '
                                  f'font-size="{fs*k}" fill="{fill}" stroke="{INK}" stroke-width="{14*k}" paint-order="stroke" letter-spacing="-3">{txt}</text>')
    return (f'<g transform="rotate(-4 {cx} {cy})">' + t(-40, "SHIP IT", GREEN, 150) +
            t(28, "or", "#FFFFFF", 64).replace(f'stroke-width="{14*k}"', f'stroke-width="{8*k}"') + t(170, "SKIP IT", RED, 150) + '</g>')

def sticker(txt, fill):
    return (f'<g transform="rotate(-5 540 200)"><rect x="150" y="90" width="780" height="220" rx="40" fill="{fill}" stroke="{INK}" stroke-width="16"/>'
            f'<text x="540" y="262" text-anchor="middle" font-family="DejaVu Sans" font-weight="bold" font-size="150" fill="#FFFFFF" '
            f'stroke="{INK}" stroke-width="12" paint-order="stroke" letter-spacing="-4">{txt}</text></g>')

FRAME_Y0, FRAME_Y1 = 150, 1130
def screen_frame(label=True):
    s = (f'<rect x="50" y="{FRAME_Y0}" width="980" height="{FRAME_Y1-FRAME_Y0}" rx="36" fill="{NAVY}" stroke="{INK}" stroke-width="16"/>'
         f'<rect x="50" y="{FRAME_Y0}" width="980" height="70" rx="36" fill="#E9EEF8" stroke="{INK}" stroke-width="16"/>'
         f'<rect x="58" y="{FRAME_Y0+40}" width="964" height="30" fill="#E9EEF8"/>'
         f'<path d="M50 {FRAME_Y0+70} L1030 {FRAME_Y0+70}" stroke="{INK}" stroke-width="12"/>'
         f'<circle cx="105" cy="{FRAME_Y0+36}" r="13" fill="{RED}" stroke="{INK}" stroke-width="5"/>'
         f'<circle cx="148" cy="{FRAME_Y0+36}" r="13" fill="{YELLOW}" stroke="{INK}" stroke-width="5"/>'
         f'<circle cx="191" cy="{FRAME_Y0+36}" r="13" fill="{GREEN}" stroke="{INK}" stroke-width="5"/>')
    if label:
        s += (f'<text x="540" y="{(FRAME_Y0+FRAME_Y1)//2+40}" text-anchor="middle" font-family="DejaVu Sans" font-weight="bold" '
              f'font-size="44" fill="#FFFFFF" fill-opacity="0.35">SCREEN RECORDING</text>')
    return s

def char_small(pose, mouth):   # bottom, under the screen
    return f'<g transform="translate(150 1180) scale(0.72)">{character(pose, mouth)}</g>'
def char_hero(pose, mouth):    # big, for hook / think / verdict
    return f'<g transform="translate(-270 285) scale(1.5)">{character(pose, mouth)}</g>'

def render(svgtxt, path):
    cairosvg.svg2png(bytestring=outlined(svgtxt).encode(), write_to=path)

