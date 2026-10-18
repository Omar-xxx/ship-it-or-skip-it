"""Render the DM checklist images people receive after commenting a keyword (1080x1350, IG portrait)."""
import os, sys
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else "."
W, H = 1080, 1350
INK, BG, BLUE, RED, GREEN, GREY = (17, 17, 17), (243, 242, 238), (30, 91, 255), (235, 59, 59), (25, 195, 125), (100, 100, 112)

def inter(size, weight=800):
    f = ImageFont.truetype(os.path.join(HERE, "fonts", "Inter.ttf"), size)
    f.set_variation_by_axes([min(32, max(14, size // 3)), weight]); return f
SERIF = lambda s: ImageFont.truetype(os.path.join(HERE, "fonts", "InstrumentSerif-Italic.ttf"), s)
MONO = lambda s: ImageFont.truetype(os.path.join(HERE, "fonts", "JetBrainsMono.ttf"), s)

def wrap(d, text, font, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) <= width: cur = t
        else: lines.append(cur); cur = w
    lines.append(cur); return lines

def render(path, line1, line2, items, footer, accent=BLUE):
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    d.text((70, 70), line1, font=inter(64, 900), fill=INK)
    f2 = SERIF(84); tw = d.textlength(line2, font=f2)
    d.rectangle((60, 160, 60 + tw + 40, 270), fill=accent)
    d.text((80, 166), line2, font=f2, fill=(255, 255, 255))
    y = 320
    for i, (title, body) in enumerate(items, 1):
        d.ellipse((70, y, 130, y + 60), fill=accent)
        num = str(i); nw = d.textlength(num, font=inter(36, 900))
        d.text((100 - nw / 2, y + 8), num, font=inter(36, 900), fill=(255, 255, 255))
        d.text((155, y + 6), title, font=inter(38, 800), fill=INK)
        yy = y + 58
        for ln in wrap(d, body, inter(28, 500), 840):
            d.text((155, yy), ln, font=inter(28, 500), fill=GREY); yy += 38
        y = yy + 22
    d.line((70, H - 120, W - 70, H - 120), fill=(215, 215, 222), width=3)
    d.text((70, H - 95), "@shipit_or_skipit", font=inter(32, 800), fill=INK)
    fw = d.textlength(footer, font=inter(28, 600))
    d.text((W - 70 - fw, H - 92), footer, font=inter(28, 600), fill=accent)
    im.save(path)

render(os.path.join(OUT, "DM_SAFE_agent_setup_checklist.png"), "AI Agent", "Safe Setup Checklist", [
    ("Give it its own folder", "One project folder, never your whole drive or home folder."),
    ("No saved passwords", "Use a separate browser profile with no logins for anything the agent browses."),
    ("Ask before it acts", "Turn off auto-approve. Delete, run commands, push, send: you click yes every time."),
    ("Scoped keys only", "Separate API keys with limits. Never production database passwords. Read-only if possible."),
    ("Backups it can't touch", "Keep a backup somewhere the agent has no access to. Deleted backups is how 9 seconds became 30 hours."),
    ("Untrusted pages = logged out", "Hidden text on a webpage can give an AI browser orders. Don't browse random sites with it while signed in."),
], "Ship it, safely.")

render(os.path.join(OUT, "DM_CHECK_repo_3_checks.png"), "Before You Install", "The 3 Checks", [
    ("Last commit", "Repo page, top of the file list: the latest commit and \"x months ago\". Then open Issues: are recent ones being answered?"),
    ("What it asks for", "Extension: manifest.json \"permissions\". npm package: package.json \"scripts\". Watch for preinstall / postinstall. MCP server: the list of tools it exposes."),
    ("Star history", "Paste the repo into star-history.com. A vertical overnight spike = suspicious. Then Insights > Contributors: just one?"),
    ("Bonus: the name", "Typosquats copy popular names with one letter off. Check the publisher matches the official repo."),
], "Fails one? Skip it.", accent=RED)
print("ok")
