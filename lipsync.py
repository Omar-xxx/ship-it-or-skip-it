"""
Patch auto lip-sync — Ship It or Skip It
Turns a voice file into a talking-Patch video. No AI credits needed.

Usage:
  python lipsync.py VOICE.wav --out patch.mp4
  python lipsync.py VOICE.wav --cues "0:shocked,3:point,30:think,35:ship" --layout scene --out reel.mp4

  --layout green  1080x1080 Patch on chroma green (key it out in CapCut over anything)   [default]
  --layout scene  1080x1920 full reel: backgrounds, screen frame, stickers per pose
  --cues          "seconds:pose,..."  poses: idle explain point think ship skip shocked warn
"""
import argparse, os, subprocess, tempfile, wave
import numpy as np
import cairosvg
from kit_lib import (character, wrap, outlined, BGS, POSE_BG, screen_frame, sticker,
                     char_small, char_hero, GREEN, RED, POSES)

FPS = 30
HERO = {"idle", "explain", "think", "ship", "skip", "shocked"}

def load_audio(path):
    tmp = tempfile.mktemp(suffix=".wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-ac", "1", "-ar", "16000", tmp], check=True)
    w = wave.open(tmp)
    x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    return x, 16000

def mouth_track(x, sr):
    hop = sr // FPS
    n = len(x) // hop
    fr = x[:n * hop].reshape(n, hop)
    db = 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9)
    spec = np.abs(np.fft.rfft(fr * np.hanning(hop), axis=1))
    freqs = np.fft.rfftfreq(hop, 1 / sr)
    cent = (spec * freqs).sum(1) / (spec.sum(1) + 1e-9)
    floor = np.percentile(db, 12)
    talking = db > floor + 10
    sp_db, sp_c = db[talking], cent[talking]
    loud_t = np.percentile(sp_db, 60) if talking.any() else 0
    hi_c, lo_c = (np.percentile(sp_c, 70), np.percentile(sp_c, 30)) if talking.any() else (0, 0)
    out = []
    for i in range(n):
        if not talking[i]:
            m = "rest"
        elif cent[i] < lo_c:
            m = "O"
        elif db[i] > loud_t:
            m = "A"
        elif cent[i] > hi_c:
            m = "E"
        else:
            m = "A" if i % 4 < 2 else "E"
        out.append(m)
    # hold each shape >= 2 frames (kills flicker), and close mouth on very short gaps
    for i in range(1, n - 1):
        if out[i] != out[i - 1] and out[i] != out[i + 1]:
            out[i] = out[i - 1]
    return out

def blink_track(n, seed=3):
    rnd, b, i = np.random.default_rng(seed), [False] * n, int(FPS * 1.5)
    while i < n:
        for k in range(4):
            if i + k < n: b[i + k] = True
        i += int(FPS * rnd.uniform(2.5, 5.0))
    return b

def pose_track(n, cues):
    track, cur, j = [], cues[0][1], 0
    for i in range(n):
        t = i / FPS
        while j < len(cues) and cues[j][0] <= t:
            cur = cues[j][1]; j += 1
        track.append(cur)
    return track

def scene_svg(pose, mouth, blink):
    bg = BGS[POSE_BG[pose]]
    if pose in HERO:
        body = f'<g transform="translate(-270 285) scale(1.5)">{character(pose, mouth, blink)}</g>'
        extra = ""
        if pose in ("ship", "skip"):
            extra = sticker("SHIP IT" if pose == "ship" else "SKIP IT", GREEN if pose == "ship" else RED) \
                .replace('rotate(-5 540 200)', 'translate(0 230) rotate(-5 540 200)')
        return wrap(bg + extra + body, 1080, 1920)
    return wrap(bg + screen_frame() + f'<g transform="translate(150 1180) scale(0.72)">{character(pose, mouth, blink)}</g>', 1080, 1920)

def green_svg(pose, mouth, blink):
    return wrap('<rect width="1080" height="1080" fill="#00FF00"/>' + character(pose, mouth, blink))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("audio")
    ap.add_argument("--out", default="patch_talking.mp4")
    ap.add_argument("--cues", default="0:idle")
    ap.add_argument("--layout", choices=["green", "scene"], default="green")
    a = ap.parse_args()

    cues = sorted((float(c.split(":")[0]), c.split(":")[1].strip()) for c in a.cues.split(","))
    for _, p in cues:
        assert p in POSES, f"unknown pose {p}"
    x, sr = load_audio(a.audio)
    mouths = mouth_track(x, sr)
    n = len(mouths)
    blinks, poses = blink_track(n), pose_track(n, cues)

    work = tempfile.mkdtemp()
    cache, entries = {}, []
    make = scene_svg if a.layout == "scene" else green_svg
    for i in range(n):
        key = (poses[i], mouths[i], blinks[i])
        if key not in cache:
            p = os.path.join(work, f"{len(cache)}.png")
            cairosvg.svg2png(bytestring=outlined(make(*key)).encode(), write_to=p)
            cache[key] = p
        if entries and entries[-1][0] == cache[key]:
            entries[-1][1] += 1
        else:
            entries.append([cache[key], 1])
    lst = os.path.join(work, "list.txt")
    with open(lst, "w") as f:
        for p, k in entries:
            f.write(f"file '{p}'\nduration {k / FPS:.5f}\n")
        f.write(f"file '{entries[-1][0]}'\n")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-i", a.audio,
                    "-map", "0:v", "-map", "1:a", "-r", str(FPS), "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-crf", "20", "-c:a", "aac", "-b:a", "160k", "-shortest", a.out], check=True)
    used = {m: mouths.count(m) for m in set(mouths)}
    print(f"done: {a.out}  frames={n}  unique images={len(cache)}  mouth mix={used}")

if __name__ == "__main__":
    main()
