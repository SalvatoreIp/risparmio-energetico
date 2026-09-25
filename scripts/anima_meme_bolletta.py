"""Anima il meme "Arriva la bolletta" aggiungendo luci e oggetti animati sopra il disegno.

Animazioni: PRIMA - la bolletta da 420 EUR trema nelle mani e pulsa di rosso, gocce di
sudore che cadono, vapore dal caffe'; DOPO - sole e riflesso che scorre sui pannelli,
LED della batteria che pulsa, il 38 EUR che brilla, vapore dalle tazze, uccellini in cielo.
Audio: battito del cuore teso a sinistra, uccellini e un "ding" allegro.

Uso: python anima_meme_bolletta.py OUTPUT.mp4
Richiede: pillow, numpy, imageio-ffmpeg.
"""
import math
import os
import subprocess
import sys
import wave

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw

SRC = "/home/salvatore/risparmio-energetico/static/immagini/meme-arriva-la-bolletta.jpg"
OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/meme-bolletta.mp4"
W, H = 1280, 720
FPS = 25
DUR = 10.0
N = int(FPS * DUR)
HEADER = 98
TAU = 2 * math.pi
rng = np.random.default_rng(7)

base_img = Image.open(SRC).convert("RGB")
base = np.asarray(base_img).astype(np.float32)
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)


def sprite(r, sx=1.0, sy=1.0):
    """Macchia di luce gaussiana (float 0-1), raggio r, eventualmente schiacciata."""
    n = int(r * 3)
    y, x = np.mgrid[-n:n + 1, -n:n + 1].astype(np.float32)
    return np.exp(-((x / sx) ** 2 + (y / sy) ** 2) / (2 * r * r))


def add(light, spr, cx, cy, color, k):
    """Somma una macchia di luce colorata con intensita' k nel buffer additivo."""
    h, w = spr.shape
    x0, y0 = int(cx) - w // 2, int(cy) - h // 2
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
    if xa >= xb or ya >= yb:
        return
    s = spr[ya - y0:yb - y0, xa - x0:xb - x0, None]
    light[ya:yb, xa:xb] += s * (np.array(color, np.float32) * k)


def feather_rect(x0, y0, x1, y1, soft=6):
    """Maschera rettangolare con bordi sfumati."""
    m = np.zeros((H, W), np.float32)
    m[y0:y1, x0:x1] = 1.0
    for _ in range(soft):
        m = (m + np.roll(m, 1, 0) + np.roll(m, -1, 0) + np.roll(m, 1, 1) + np.roll(m, -1, 1)) / 5
    return m


# --- bolletta che trema: foglio + mani + busta ---------------------------------------
LETTER = (95, 410, 360, 630)
letter_mask = feather_rect(*LETTER, soft=8)[..., None]

# --- pannelli solari: pixel blu scuri nella zona del tetto ----------------------------
roof = np.zeros((H, W), bool)
roof[100:225, 950:1280] = True
panel_mask = (roof & (base[..., 2] > base[..., 0] + 15) & (base.mean(axis=2) < 120)).astype(np.float32)

# --- gocce di sudore -----------------------------------------------------------------
DROPS = [dict(x=283, y=292, t0=0.3, per=2.2), dict(x=352, y=290, t0=1.4, per=2.6),
         dict(x=372, y=335, t0=0.8, per=2.0), dict(x=468, y=262, t0=1.9, per=2.4)]

# --- vapore dalle tazze --------------------------------------------------------------
steam = []
for src, n, per in [((560, 610), 8, 2.4), ((742, 500), 6, 2.2), ((1170, 570), 6, 2.6)]:
    steam += [dict(src=src, t0=rng.uniform(0, per), drift=rng.uniform(-8, 8), per=per)
              for _ in range(n)]

# --- uccellini ----------------------------------------------------------------------
# volano nella striscia di cielo tra il divisorio e la scritta DOPO, sopra il fumetto
BIRDS = [dict(y=138, speed=40, x0=0, ph=0.0, s=1.0), dict(y=152, speed=33, x0=90, ph=1.7, s=0.8),
         dict(y=128, speed=47, x0=150, ph=0.9, s=0.7)]
BIRD_X0, BIRD_X1 = 650, 840

S_SMALL, S_MED, S_BIG, S_HUGE = sprite(3), sprite(8), sprite(18), sprite(60)
S_STEAM = sprite(6)


def draw_overlay(t):
    """Disegni vettoriali (gocce, uccellini, scintille) su un livello RGBA."""
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    # gocce di sudore: si formano, scivolano giu' accelerando e svaniscono
    for g in DROPS:
        age = (t + g["t0"]) % g["per"]
        k = age / g["per"]
        if k < 0.25:
            r = 2 + 10 * k
            y = g["y"]
        else:
            r = 4.5
            y = g["y"] + 180 * (k - 0.25) ** 2
        a = int(230 * (1 - max(0, k - 0.7) / 0.3))
        d.ellipse([g["x"] - r, y - r, g["x"] + r, y + r * 1.3], fill=(170, 215, 255, a),
                  outline=(60, 110, 170, a))
        d.polygon([(g["x"] - r * 0.7, y - r * 0.5), (g["x"] + r * 0.7, y - r * 0.5),
                   (g["x"], y - r * 2.2)], fill=(170, 215, 255, a))
        d.ellipse([g["x"] - r * 0.4, y - r * 0.2, g["x"] - r * 0.05, y + r * 0.3],
                  fill=(255, 255, 255, a))
    # uccellini: due archi che sbattono le ali
    for b in BIRDS:
        x = (b["x0"] + b["speed"] * t) % (BIRD_X1 - BIRD_X0) + BIRD_X0
        y = b["y"] + 6 * math.sin(t * 1.3 + b["ph"])
        flap = math.sin(t * 9 + b["ph"])
        s = 11 * b["s"]
        wy = y - s * 0.7 * flap
        a = int(230 * min(1.0, (x - BIRD_X0) / 25, (BIRD_X1 - x) / 25))  # entrano/escono sfumando
        d.line([(x - s, wy), (x - s * 0.35, y - s * 0.15), (x, y)], fill=(45, 45, 55, a), width=3)
        d.line([(x, y), (x + s * 0.35, y - s * 0.15), (x + s, wy)], fill=(45, 45, 55, a), width=3)
    # scintille attorno al 38 EUR
    for j, (sx, sy) in enumerate([(872, 512), (975, 520), (930, 488), (962, 562)]):
        k = max(0.0, math.sin(t * 2.4 + j * 1.6)) ** 4
        if k > 0.05:
            r = 12 * k
            c = (255, 255, 200, int(255 * k))
            d.line([(sx - r, sy), (sx + r, sy)], fill=c, width=3)
            d.line([(sx, sy - r), (sx, sy + r)], fill=c, width=3)
            d.line([(sx - r * 0.4, sy - r * 0.4), (sx + r * 0.4, sy + r * 0.4)], fill=c, width=2)
            d.line([(sx - r * 0.4, sy + r * 0.4), (sx + r * 0.4, sy - r * 0.4)], fill=c, width=2)
    return np.asarray(ov).astype(np.float32)


def frame(i):
    t = i / FPS
    light = np.zeros((H, W, 3), np.float32)
    img = base.copy()

    # bolletta che trema: copia spostata di 1-3 px, fusa con bordi morbidi
    dx = int(round(2.5 * math.sin(t * 31) + 1.0 * math.sin(t * 53)))
    dy = int(round(1.5 * math.sin(t * 37 + 1)))
    shifted = np.roll(np.roll(base, dy, 0), dx, 1)
    img = img * (1 - letter_mask) + shifted * letter_mask

    # 420 EUR che pulsa di rosso, col ritmo del battito
    beat = math.exp(-((t * 1.3) % 1.0) * 6)
    add(light, S_BIG, 205 + dx, 485 + dy, (255, 40, 30), 0.25 + 0.35 * beat)
    add(light, S_HUGE, 205, 485, (255, 30, 20), 0.05 + 0.08 * beat)

    # sole in alto e alone caldo sul lato DOPO
    add(light, S_HUGE, 700, 120, (255, 240, 180), 0.30 + 0.05 * math.sin(t * 1.5))
    add(light, S_BIG, 700, 120, (255, 255, 230), 0.5)

    # riflesso che scorre sui pannelli ogni 3,3 s
    pos = ((t % 3.3) / 3.3) * 600 + 850
    band = np.exp(-((XX + YY * 1.2 - pos - 120) / 22) ** 2)
    light += (panel_mask * band)[..., None] * np.array([200, 220, 255], np.float32)

    # LED verde della batteria
    add(light, S_SMALL, 1072, 372, (80, 255, 110), 0.6 + 0.6 * math.sin(t * 3.5) ** 2)
    add(light, S_MED, 1072, 372, (80, 255, 110), 0.15 + 0.15 * math.sin(t * 3.5) ** 2)

    # 38 EUR che "respira" di verde
    add(light, S_BIG, 925, 535, (90, 255, 120), 0.15 + 0.10 * math.sin(t * 2.4))

    # vapore dalle tazze
    for s in steam:
        age = (t + s["t0"]) % s["per"]
        k = age / s["per"]
        x = s["src"][0] + s["drift"] * k + 4 * math.sin(age * 3 + s["t0"])
        y = s["src"][1] - 70 * k
        add(light, S_STEAM if k < 0.5 else S_MED, x, y, (255, 245, 230), 0.22 * math.sin(math.pi * k))

    light[:HEADER] = 0
    out = img + light * (1 - img / 255 * 0.5)
    ov = draw_overlay(t)
    a = ov[..., 3:4] / 255
    out = out * (1 - a) + ov[..., :3] * a
    out[:HEADER] = base[:HEADER]
    return out.clip(0, 255).astype(np.uint8)


def make_audio(path, sr=44100):
    n = int(DUR * sr)
    tt = np.arange(n) / sr
    audio = np.zeros(n)
    # battito del cuore: doppio colpo grave "tu-tum" a 78 bpm
    period = 1 / 1.3
    for off, amp in [(0.0, 0.9), (0.16, 0.6)]:
        x = (tt - off) % period
        audio += amp * np.exp(-x * 25) * np.sin(TAU * 55 * x)
    # uccellini: cinguettii brevi a frequenza che sale
    for _ in range(18):
        t0 = rng.uniform(0.5, DUR - 0.5)
        f0 = rng.uniform(2800, 4200)
        for rep in range(int(rng.integers(2, 4))):
            s = t0 + rep * 0.11
            x = tt - s
            env = np.where((x > 0) & (x < 0.07), np.sin(math.pi * np.clip(x / 0.07, 0, 1)), 0)
            audio += 0.12 * env * np.sin(TAU * (f0 * x + 9000 * x * x))
    # "ding" allegro quando il 38 EUR brilla la prima volta
    x = tt - 0.65
    audio += np.where(x > 0, 0.35 * np.exp(-x * 4) * (np.sin(TAU * 1568 * x) + 0.5 * np.sin(TAU * 2093 * x)), 0)
    fade = np.minimum(1, np.minimum(tt / 0.3, (DUR - tt) / 0.5))
    audio = (audio * fade / np.abs(audio).max() * 0.8 * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(audio.tobytes())


if __name__ == "__main__":
    wav = OUT + ".wav"
    make_audio(wav)
    proc = subprocess.Popen(
        [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "rawvideo",
         "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav,
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "medium",
         "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", OUT],
        stdin=subprocess.PIPE)
    for i in range(N):
        proc.stdin.write(frame(i).tobytes())
    proc.stdin.close()
    proc.wait()
    os.remove(wav)
    print("OK", OUT)
