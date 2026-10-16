"""
One-shot voiceover prep: optional cuts -> tighten pauses -> loudness master -> word timings.
  python prep_voice.py voice.mp3 OUTNAME [--cut "2.8-5.2,10.1-10.9"] [--keep "it might:0.5"] [--denoise]
--cut removes stutters/flubbed lines (seconds), --keep holds a dramatic pause before the given words.
Produces OUTNAME.wav (mastered, -14 LUFS) and OUTNAME.words.json for explainer.py
"""
import argparse, json, os, subprocess, sys, tempfile, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument("audio"); ap.add_argument("out")
ap.add_argument("--cut", default=""); ap.add_argument("--keep", default="")
ap.add_argument("--max", default="0.32")
ap.add_argument("--denoise", action="store_true", help="for raw mic recordings: high-pass, 50/100 Hz hum notch, light denoise")
a = ap.parse_args()

src = tempfile.mktemp(suffix=".wav")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.audio, "-ac", "1", "-ar", "44100", src], check=True)
if a.cut:
    w = wave.open(src); sr = w.getframerate()
    x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    spans = sorted(tuple(map(float, s.split("-"))) for s in a.cut.split(","))
    xf = int(0.015 * sr); ramp = np.linspace(0, 1, xf, dtype=np.float32)
    out, pos = np.zeros(0, np.float32), 0
    for s, e in spans + [(len(x) / sr, len(x) / sr)]:
        piece = x[pos:int(s * sr)]
        out = np.concatenate([out[:-xf], out[-xf:] * (1 - ramp) + piece[:xf] * ramp, piece[xf:]]) if len(out) > xf and len(piece) > xf else np.concatenate([out, piece])
        pos = int(e * sr)
    with wave.open(src, "w") as o:
        o.setnchannels(1); o.setsampwidth(2); o.setframerate(sr)
        o.writeframes((np.clip(out, -1, 1) * 32767).astype(np.int16).tobytes())

tight = tempfile.mktemp(suffix=".wav")
cmd = [sys.executable, os.path.join(HERE, "tighten.py"), src, "--out", tight, "--max", a.max]
if a.keep: cmd += ["--keep", a.keep]
subprocess.run(cmd, check=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tight, "-af", ("highpass=f=75,bandreject=f=50:width_type=q:w=8,bandreject=f=100:width_type=q:w=8,afftdn=nr=10:nf=-50," if a.denoise else "") + "loudnorm=I=-14:TP=-1.5:LRA=9", "-ar", "44100", a.out + ".wav"], check=True)

from faster_whisper import WhisperModel
t16 = tempfile.mktemp(suffix=".wav")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.out + ".wav", "-ac", "1", "-ar", "16000", t16], check=True)
w = wave.open(t16); y = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
segs, _ = WhisperModel("small.en", device="cpu", compute_type="int8").transcribe(y, word_timestamps=True)
words, lines = [], []
for s in segs:
    ws = [(round(x.start, 2), round(x.end, 2), x.word.strip()) for x in s.words if x.end > x.start]
    words += ws
    if ws: lines.append(f"{ws[0][0]:6.2f}  {' '.join(t for _, _, t in ws)}")
json.dump(words, open(a.out + ".words.json", "w"))
print(f"{a.out}.wav  {len(y)/16000:.1f}s"); print("\n".join(lines))
