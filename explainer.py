"""
Ship It or Skip It - kinetic explainer renderer (light 'tech explainer' style).
Headline + highlighted italic phrase, animated UI cards, word-by-word captions,
lip-synced Patch in a rounded frame at the bottom.

  python explainer.py VOICE.wav WORDS.json --out reel.mp4

WORDS.json = [[start, end, "word"], ...]   (faster-whisper word timestamps)
Edit SCENES / POSE_CUES below for each new video.
"""
import json, math, subprocess, sys, os, argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from lipsync import load_audio, mouth_track, blink_track, FPS

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "fonts")
W, H = 1080, 1920
INK, BG, BLUE, RED, GREEN, ORANGE, NAVY = (17, 17, 17), (243, 242, 238), (30, 91, 255), (235, 59, 59), (25, 195, 125), (255, 122, 26), (11, 16, 32)

def inter(size, weight=800):
    f = ImageFont.truetype(os.path.join(FONTS, "Inter.ttf"), size)
    f.set_variation_by_axes([min(32, max(14, size // 3)), weight]); return f
SERIF = lambda s: ImageFont.truetype(os.path.join(FONTS, "InstrumentSerif-Italic.ttf"), s)
MONO = lambda s: ImageFont.truetype(os.path.join(FONTS, "JetBrainsMono.ttf"), s)

# ------------------------------------------------------------------ easing
def clamp(v, a=0., b=1.): return max(a, min(b, v))
def ease_out_back(t, s=1.7): t -= 1; return t * t * ((s + 1) * t + s) + 1
def ease_out(t): return 1 - (1 - t) ** 3
def prog(t, start, dur): return clamp((t - start) / dur)

# ------------------------------------------------------------------ drawing helpers
def shadowed(img, radius=28, offset=10, alpha=55):
    """Return a larger RGBA with soft drop shadow under img."""
    pad = radius * 2
    out = Image.new("RGBA", (img.width + pad * 2, img.height + pad * 2), (0, 0, 0, 0))
    a = img.split()[3].point(lambda v: alpha if v > 0 else 0)
    sh = Image.new("RGBA", img.size, (20, 30, 60, 0)); sh.putalpha(a)
    out.alpha_composite(sh, (pad, pad + offset)); out = out.filter(ImageFilter.GaussianBlur(radius))
    out.alpha_composite(img, (pad, pad)); return out

def card(w, h, fill=(250, 250, 248), border=BLUE, r=34):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((2, 2, w - 3, h - 3), r, fill=fill, outline=border, width=4)
    return im, d

def text_c(d, cx, y, s, f, fill=INK):
    l, t, r, b = d.textbbox((0, 0), s, font=f); d.text((cx - (r - l) / 2 - l, y), s, font=f, fill=fill)

def pill(d, x, y, s, f, bg, fg=(255, 255, 255), padx=22, pady=12):
    l, t, r, b = d.textbbox((0, 0), s, font=f)
    d.rounded_rectangle((x, y, x + (r - l) + padx * 2, y + (b - t) + pady * 2), 40, fill=bg)
    d.text((x + padx - l, y + pady - t), s, font=f, fill=fg)
    return x + (r - l) + padx * 2

# ------------------------------------------------------------------ cards (fictional data)
def card_repo():
    im, d = card(920, 380)
    d.rounded_rectangle((50, 52, 120, 122), 18, fill=(230, 236, 252), outline=BLUE, width=3)
    d.text((70, 62), "{}", font=MONO(40), fill=BLUE)
    d.text((145, 52), "dev-unknown /", font=inter(34, 500), fill=(110, 110, 120))
    d.text((145, 92), "super-notes-ai-pro", font=inter(48, 800), fill=INK)
    d.text((50, 175), "AI that organizes all your notes", font=inter(36, 500), fill=(70, 70, 80))
    x = pill(d, 50, 260, "★  20.4k stars", inter(34, 700), (255, 214, 64), INK)
    pill(d, x + 18, 260, "Public", inter(34, 700), (232, 232, 236), INK)
    return im

def card_checklist(marks=0, crossed=False):
    im, d = card(920, 420)
    rows = ["Last commit", "Permissions", "Star history"]
    for i, r in enumerate(rows):
        y = 60 + i * 115
        on = i < marks
        c = RED if crossed else (BLUE if on else (200, 200, 208))
        d.ellipse((60, y, 140, y + 80), fill=c if on or crossed else None, outline=c, width=6)
        if crossed:
            d.line((82, y + 22, 118, y + 58), fill="white", width=9); d.line((118, y + 22, 82, y + 58), fill="white", width=9)
        else:
            d.text((86 if i else 89, y + 10), str(i + 1), font=inter(48, 800), fill="white" if on else c)
        d.text((175, y + 12), r, font=inter(52, 800), fill=INK if on or crossed else (150, 150, 158))
    return im

def card_commit(badge=False):
    im, d = card(920, 400)
    d.text((50, 45), "Latest commit", font=inter(34, 600), fill=(110, 110, 120))
    d.rounded_rectangle((50, 100, 870, 205), 22, fill=(240, 241, 245))
    d.text((80, 128), "fix typo in README", font=MONO(36), fill=INK)
    d.ellipse((50, 245, 120, 315), outline=RED, width=7)
    d.line((85, 262, 85, 282), fill=RED, width=6); d.line((85, 282, 100, 292), fill=RED, width=6)
    d.text((140, 245), "14 months ago", font=inter(56, 900), fill=RED)
    if badge:
        pill(d, 50, 330 - 4, "⚠  No one is patching it", inter(30, 700), RED)
    return im

def card_config(pulse=0.0):
    im, d = card(920, 470, fill=NAVY, border=BLUE)
    f = MONO(38)
    lines = [("# plugin.config.yaml", (120, 140, 180)), ("name: super-notes", (230, 235, 245)),
             ("permissions:", (230, 235, 245)), ("  - read: ./notes", (61, 255, 143)),
             ('  - filesystem: "*"', (255, 255, 255)), ("  - network: any", (255, 200, 90))]
    for i, (s, c) in enumerate(lines):
        y = 45 + i * 66
        if i == 4:
            a = int(110 + 120 * pulse)
            hl = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(hl).rounded_rectangle((30, y - 8, 890, y + 56), 12, fill=RED + (a,))
            im.alpha_composite(hl); d = ImageDraw.Draw(im)
        d.text((55, y), s, font=f, fill=c)
    return im

def card_chart(p=1.0):
    im, d = card(920, 460)
    x0, y0, x1, y1 = 70, 70, 860, 330
    for k in range(5): d.line((x0, y0 + k * (y1 - y0) / 4, x1, y0 + k * (y1 - y0) / 4), fill=(225, 226, 232), width=2)
    pts = []
    for i in range(101):
        u = i / 100
        v = 0.04 + 0.02 * u if u < 0.78 else 0.06 + 0.9 * (1 - math.exp(-(u - 0.78) * 40))
        pts.append((x0 + u * (x1 - x0), y1 - v * (y1 - y0)))
    n = max(2, int(len(pts) * p))
    d.line(pts[:n], fill=BLUE, width=9, joint="curve")
    d.ellipse((pts[n - 1][0] - 12, pts[n - 1][1] - 12, pts[n - 1][0] + 12, pts[n - 1][1] + 12), fill=BLUE)
    d.text((x0, 350), "Stars over time", font=inter(30, 600), fill=(120, 120, 130))
    if p > 0.95:
        pill(d, 70, 385, "+18k overnight", inter(32, 800), RED)
        pill(d, 420, 385, "1 contributor", inter(32, 800), INK)
    return im

def card_follow():
    im, d = card(920, 330)
    text_c(d, 460, 60, "Honest verdicts on AI tools", inter(44, 800))
    text_c(d, 460, 125, "No sponsors. Just ship it or skip it.", inter(32, 500), (100, 100, 110))
    d.rounded_rectangle((300, 205, 620, 285), 40, fill=BLUE)
    text_c(d, 460, 222, "Follow", inter(40, 800), (255, 255, 255))
    return im

def card_cta(keyword, what, lt=1.0):
    """End card: 'Comment KEYWORD and I'll DM you ...'. Keyword pill pulses."""
    im, d = card(920, 430, border=BLUE)
    text_c(d, 460, 40, "Comment", inter(64, 900))
    f = inter(96, 900)
    l, t, r, b = d.textbbox((0, 0), keyword, font=f)
    pw, ph = r - l + 110, b - t + 56
    sc = 1 + 0.04 * math.sin(lt * 6)
    pw2, ph2 = int(pw * sc), int(ph * sc)
    x0, y0 = 460 - pw2 // 2, 130 + (ph - ph2) // 2
    d.rounded_rectangle((x0, y0, x0 + pw2, y0 + ph2), 34, fill=BLUE)
    d.polygon([(x0 + 70, y0 + ph2 - 2), (x0 + 110, y0 + ph2 - 2), (x0 + 60, y0 + ph2 + 34)], fill=BLUE)
    text_c(d, 460, y0 + (ph2 - (b - t)) / 2 - t + 2, keyword, f, (255, 255, 255))
    text_c(d, 460, 300, "and I'll DM you", inter(38, 600), (90, 90, 100))
    text_c(d, 460, 350, what, inter(42, 900))
    return im

def stamp(text, color=RED):
    f = inter(150, 900)
    tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    l, t, r, b = tmp.textbbox((0, 0), text, font=f)
    im = Image.new("RGBA", (r - l + 80, b - t + 80), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((6, 6, im.width - 6, im.height - 6), 26, outline=color, width=12, fill=(255, 255, 255, 235))
    d.text((40 - l, 40 - t), text, font=f, fill=color)
    return im.rotate(-8, expand=True, resample=Image.BICUBIC)

# ------------------------------------------------------------------ scene script (edit per video)
SCENES = [  # start, headline, highlighted phrase, card factory(t, local_t)
    (0.00,  "This GitHub Repo", "Might Be a Trap", lambda t, lt: card_repo()),
    (4.92,  "Before You Install", "Check 3 Things", lambda t, lt: card_checklist(marks=min(3, 1 + int(lt / 0.5)))),
    (8.70,  "Check #1", "Last Commit", lambda t, lt: card_commit(badge=t > 11.2)),
    (16.34, "Check #2", "Permissions", lambda t, lt: card_config(pulse=(0.5 + 0.5 * math.sin(t * 7)) if t > 19.88 else 0)),
    (25.66, "Check #3", "Star History", lambda t, lt: card_chart(p=ease_out(prog(lt, 0.8, 2.6)))),
    (35.42, "So… Is It", "Worth the Risk?", lambda t, lt: card_checklist(crossed=True)),
    (40.30, "The Verdict", "Skip It", None),
    (41.58, "Ship It", "or Skip It?", lambda t, lt: card_follow()),
]
STAMPS = [(23.82, 25.4, "NO."), (32.78, 35.2, "BOUGHT?"), (40.30, 41.5, "SKIP IT")]
POSE_CUES = [(0, "shocked"), (4.9, "explain"), (8.7, "point"), (11.2, "warn"), (16.3, "point"), (19.9, "warn"),
             (23.8, "explain"), (25.6, "point"), (28.0, "warn"), (35.4, "think"), (40.3, "skip"), (41.6, "ship")]

# ------------------------------------------------------------------ static layers
def make_background():
    rng = np.random.default_rng(1)
    base = np.ones((H, W, 3)) * np.array(BG)
    yy, xx = np.mgrid[0:H, 0:W]
    glow = np.exp(-(((xx - 820) / 520) ** 2 + ((yy - 420) / 520) ** 2)) * 10
    base += glow[..., None] * np.array([-3, 0, 6]) / 6
    base += rng.normal(0, 7, (H, W, 1))
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).convert("RGBA")

def headline_img(l1, l2, style="v4"):
    im = Image.new("RGBA", (W, 330), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if style == "classic":
        text_c(d, W / 2, 20, l1, inter(96, 900))
        f = SERIF(118)
        l, t, r, b = d.textbbox((0, 0), l2, font=f)
        bw = r - l + 70
        x = (W - bw) / 2
        d.rectangle((x, 150, x + bw, 150 + 150), fill=BLUE)
        d.text((x + 35 - l, 150 + 14 - t + 8), l2, font=f, fill=(255, 255, 255))
        return im
    # v4: bold sans line + italic serif accent in colour, no box (shrinks to fit)
    f1 = inter(92, 900)
    while d.textlength(l1, font=f1) > W - 120: f1 = inter(f1.size - 4, 900)
    text_c(d, W / 2, 24, l1, f1)
    f2 = SERIF(140)
    while d.textlength(l2, font=f2) > W - 100: f2 = SERIF(f2.size - 4)
    text_c(d, W / 2, 128, l2, f2, BLUE)
    return im

def stack_card(c):
    """Put two offset 'paper' sheets behind a card so it reads as a pile of documents."""
    pad = 46
    out = Image.new("RGBA", (c.width + pad * 2, c.height + pad * 2), (0, 0, 0, 0))
    for k, (dx, dy, ang) in enumerate([(-22, 34, 3.2), (26, 18, -2.0)]):
        sh = Image.new("RGBA", c.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle((2, 2, c.width - 3, c.height - 3), 34,
                                             fill=(236, 234, 228) if k == 0 else (246, 245, 241), outline=(205, 203, 196), width=3)
        sh = sh.rotate(ang, expand=True, resample=Image.BICUBIC)
        out.alpha_composite(sh, (pad + dx - (sh.width - c.width) // 2, pad + dy - (sh.height - c.height) // 2))
    out.alpha_composite(c, (pad, pad))
    return out

def topbar_img(chapter, idx, counter_label=None, counter_val=None, color=RED, pop=1.0):
    im = Image.new("RGBA", (W, 120), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.text((60, 42), f"// {idx:02d} — {chapter}", font=MONO(32), fill=(95, 95, 108))
    if counter_label:
        fv = inter(int(46 * (1.25 - 0.25 * pop)), 900)
        vw = d.textlength(counter_val, font=fv)
        d.text((W - 60 - vw, 30 + (1 - pop) * -6), counter_val, font=fv, fill=color)
        fl = MONO(26); lw = d.textlength(counter_label, font=fl)
        d.text((W - 60 - vw - 22 - lw, 46), counter_label, font=fl, fill=(95, 95, 108))
    return im

def outlined_word(fr, cx, cy, wd, f, stroke=10):
    d = ImageDraw.Draw(fr)
    l, tt, r, b = d.textbbox((0, 0), wd, font=f)
    x, y = cx - (r - l) / 2 - l, cy - (b - tt) / 2 - tt
    d.text((x + 4, y + 7), wd, font=f, fill=(17, 17, 17), stroke_width=stroke, stroke_fill=(17, 17, 17))
    d.text((x, y), wd, font=f, fill=INK, stroke_width=stroke, stroke_fill=(255, 255, 255))
    d.text((x, y), wd, font=f, fill=INK)

def patch_window():
    im = Image.new("RGBA", (W - 100, 900), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, im.width - 1, im.height + 80), 70, fill=(222, 231, 255))
    return shadowed(im, radius=24, offset=8, alpha=50)

# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("audio"); ap.add_argument("words"); ap.add_argument("--out", default="explainer.mp4")
    ap.add_argument("--spec", help="python file defining SCENES, STAMPS, POSE_CUES (optional: CHAPTERS, COUNTER)")
    ap.add_argument("--style", default="v4", choices=["v4", "classic"],
                    help="v4: unboxed host, chapter bar, stacked cards (default). classic: the original boxed layout")
    ap.add_argument("--frames", help="debug: comma-separated seconds; save PNG stills instead of a video")
    a = ap.parse_args()
    global SCENES, STAMPS, POSE_CUES
    chapters, counter = None, None
    if a.spec:
        import importlib.util
        sp = importlib.util.spec_from_file_location("spec", a.spec); m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
        SCENES, STAMPS, POSE_CUES = m.SCENES, m.STAMPS, m.POSE_CUES
        chapters = getattr(m, "CHAPTERS", None)
        counter = getattr(m, "COUNTER", None)   # ("LABEL", [(start, "value", colour), ...])
    v4 = a.style == "v4"
    if chapters is None: chapters = [s[2].lower().rstrip(".?!") for s in SCENES]

    x, sr = load_audio(a.audio)
    mouths = mouth_track(x, sr); n = len(mouths); blinks = blink_track(n)
    words = [(float(s), float(e), w) for s, e, w in json.load(open(a.words))]
    merged = []
    for s, e, w in words:                     # join "20" + ",000"
        if merged and (w.startswith(",") or w.startswith("-")): merged[-1] = (merged[-1][0], e, merged[-1][2] + w)
        else: merged.append((s, e, w))
    words = merged

    bg = make_background()
    win = patch_window()
    heads = {i: headline_img(s[1], s[2], a.style) for i, s in enumerate(SCENES)}
    stamps = {i: shadowed(stamp(s[2], s[3] if len(s) > 3 else RED)) for i, s in enumerate(STAMPS)}
    pose_cache = {}

    def patch_img(pose, mouth, blink):
        k = (pose, mouth, blink)
        if k not in pose_cache:
            p = os.path.join(HERE, "poses", pose, f"{mouth}{'_blink' if blink else ''}.png")
            im = Image.open(p).convert("RGBA")
            if v4: im = shadowed(im, radius=18, offset=6, alpha=40)
            else: im = im.resize((900, 900), Image.LANCZOS)
            pose_cache[k] = im
        return pose_cache[k]

    def frame(i):
        t = i / FPS
        fr = bg.copy()
        si = max(k for k, s in enumerate(SCENES) if s[0] <= t)
        st = SCENES[si][0]; lt = t - st
        top = 150 if v4 else 150
        # chapter bar + counter (v4)
        if v4:
            cl = cv = None; cc = RED; pop = 1.0
            if counter:
                vals = [v for v in counter[1] if v[0] <= t]
                if vals:
                    v0 = vals[-1]; cl, cv = counter[0], v0[1]; cc = v0[2] if len(v0) > 2 else RED
                    pop = ease_out_back(prog(t, v0[0], 0.3)) if t - v0[0] < 0.3 else 1.0
            fr.alpha_composite(topbar_img(chapters[si], si + 1, cl, cv, cc, clamp(pop, 0, 1.2)), (0, 40))
        # headline: slide up + fade (frame 0 shows everything = cover frame)
        hp = ease_out(prog(lt, 0, 0.35)) if si > 0 else 1
        h = heads[si].copy()
        if hp < 1: h.putalpha(h.split()[3].point(lambda v, hp=hp: int(v * hp)))
        fr.alpha_composite(h, (0, int(top + 40 * (1 - hp))))
        # card
        fac = SCENES[si][3]
        if fac:
            c = fac(t, lt)
            c = shadowed(stack_card(c) if v4 else c)
            raw = prog(lt, 0.08, 0.38) if si > 0 else 1
            cp = ease_out_back(raw) if raw < 1 else 1
            sc = 0.86 + 0.14 * cp
            cw, ch = int(c.width * sc), int(c.height * sc)
            c = c.resize((cw, ch), Image.BILINEAR)
            if cp < 1: c.putalpha(c.split()[3].point(lambda v, cp=cp: int(v * clamp(cp))))
            cy = 520 if v4 else 505
            fr.alpha_composite(c, ((W - cw) // 2, cy + (470 - ch) // 2 - 10))
        # patch
        pose = [p for c0, p in POSE_CUES if c0 <= t][-1]
        bob = int(6 * math.sin(t * 2.2))
        if v4:
            fr.alpha_composite(patch_img(pose, mouths[i], blinks[i]), (-200 - 36, 880 + bob - 36))
        else:
            fr.alpha_composite(win, (50 - 48, 1120 - 48))
            fr.alpha_composite(patch_img(pose, mouths[i], blinks[i]), (90, 1100 + bob))
        # stamps (on top of everything but captions)
        for k, (s0, s1, *_) in enumerate(STAMPS):
            if s0 <= t < s1:
                p = prog(t, s0, 0.22)
                sc = 1.6 - 0.6 * ease_out(p)
                s = stamps[k]; sw, sh = int(s.width * sc), int(s.height * sc)
                s = s.resize((sw, sh), Image.BILINEAR)
                fr.alpha_composite(s, ((W - sw) // 2, 620 + (300 - sh) // 2))
        # kinetic caption (current word)
        cur = [w for w in words if w[0] <= t < max(w[1], w[0] + 0.18)]
        if not cur:
            prev = [w for w in words if w[1] <= t]
            if prev and t - prev[-1][1] < 0.35: cur = [prev[-1]]
        if cur:
            s0, _, wd = cur[-1]
            wd = wd.strip().strip(",.").lower() if not wd.endswith(("?", "!")) else wd.lower()
            p = prog(t, s0, 0.12); sc = 1.18 - 0.18 * ease_out(p)
            if v4:
                outlined_word(fr, W / 2, 1075, wd, inter(int(108 * sc), 900))
            else:
                f = inter(int(118 * sc), 900)
                d = ImageDraw.Draw(fr)
                l, tt, r, b = d.textbbox((0, 0), wd, font=f)
                cx, cy = W / 2, 1035
                d.text((cx - (r - l) / 2 - l + 5, cy - (b - tt) / 2 - tt + 6), wd, font=f, fill=(255, 255, 255))
                d.text((cx - (r - l) / 2 - l, cy - (b - tt) / 2 - tt), wd, font=f, fill=INK)
        return fr

    if a.frames:
        base = os.path.splitext(a.out)[0]
        for s in a.frames.split(","):
            i = min(n - 1, int(float(s) * FPS)); frame(i).convert("RGB").save(f"{base}_{float(s):05.1f}.png")
        print("stills saved"); return

    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-i", a.audio, "-map", "0:v", "-map", "1:a",
                           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", "-preset", "medium",
                           "-c:a", "aac", "-b:a", "192k", "-shortest", a.out], stdin=subprocess.PIPE)
    for i in range(n):
        ff.stdin.write(frame(i).convert("RGB").tobytes())
        if i % 150 == 0: print(f"{i / FPS:5.1f}s", flush=True)
    ff.stdin.close(); ff.wait()
    print("done:", a.out)

if __name__ == "__main__":
    main()
