"""
Tighten pauses in a generated voiceover (short-form pacing).
  python tighten.py voice.mp3 --out tight.wav [--max 0.32] [--keep "it might:0.5,skip it:0.55"]
--keep: word that FOLLOWS a pause you want to keep longer (dramatic beat), with its length.
"""
import argparse, subprocess, tempfile, wave
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("audio"); ap.add_argument("--out", default="tight.wav")
ap.add_argument("--max", type=float, default=0.32)
ap.add_argument("--keep", default="")
a = ap.parse_args()

tmp = tempfile.mktemp(suffix=".wav")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.audio, "-ac", "1", "-ar", "44100", tmp], check=True)
w = wave.open(tmp); sr = w.getframerate()
x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768

keep = {}
if a.keep:
    from faster_whisper import WhisperModel
    y16 = x[::int(sr / 16000)] if sr % 16000 == 0 else None
    t16 = tempfile.mktemp(suffix=".wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-ar", "16000", t16], check=True)
    w16 = wave.open(t16); y = np.frombuffer(w16.readframes(w16.getnframes()), np.int16).astype(np.float32) / 32768
    targets = {k.lower(): float(v) for k, v in (p.split(":") for p in a.keep.split(","))}
    segs, _ = WhisperModel("small.en", device="cpu", compute_type="int8").transcribe(y, word_timestamps=True)
    ws = [(wd.start, wd.word.strip().strip(".,!?").lower()) for s in segs for wd in s.words]
    for phrase, L in targets.items():          # phrase = the words right AFTER the pause, e.g. "it might"
        parts = phrase.split()
        for k in range(len(ws) - len(parts) + 1):
            if [t for _, t in ws[k:k + len(parts)]] == parts:
                keep[ws[k][0]] = L

hop = int(0.01 * sr); n = len(x) // hop
db = 20 * np.log10(np.sqrt((x[:n * hop].reshape(n, hop) ** 2).mean(1)) + 1e-9)
thr = np.percentile(db, 10) + 22
silent_raw = db < thr
# bridge tiny blips (<50 ms) inside pauses
silent = silent_raw.copy()
for k in range(1, len(silent) - 5):
    if not silent_raw[k] and silent_raw[k - 1] and silent_raw[k:k + 5].any() and not silent_raw[k:k + 5].all():
        if silent_raw[k + 1:k + 6].any(): silent[k] = True
remove, i = [], 0
while i < n:
    if silent[i]:
        j = i
        while j < n and silent[j]: j += 1
        a0, b0 = i * 0.01, j * 0.01
        tgt = a.max
        for ws, L in keep.items():
            if a0 - 0.15 <= ws <= b0 + 0.15: tgt = L
        if b0 - a0 > tgt + 0.04 and a0 > 0.05:
            mid, cut = (a0 + b0) / 2, (b0 - a0) - tgt
            remove.append((mid - cut / 2, mid + cut / 2))
        i = j
    else:
        i += 1

xf = int(0.012 * sr); ramp = np.linspace(0, 1, xf, dtype=np.float32)
out, pos = np.zeros(0, np.float32), 0
for s, e in remove + [(len(x) / sr, len(x) / sr)]:
    piece = x[pos:int(s * sr)]
    if len(out) > xf and len(piece) > xf:
        out = np.concatenate([out[:-xf], out[-xf:] * (1 - ramp) + piece[:xf] * ramp, piece[xf:]])
    else:
        out = np.concatenate([out, piece])
    pos = int(e * sr)
with wave.open(a.out, "w") as o:
    o.setnchannels(1); o.setsampwidth(2); o.setframerate(sr)
    o.writeframes((np.clip(out, -1, 1) * 32767).astype(np.int16).tobytes())
print(f"{len(x)/sr:.1f}s -> {len(out)/sr:.1f}s  ({len(remove)} pauses tightened, {len(keep)} dramatic beats kept)")
