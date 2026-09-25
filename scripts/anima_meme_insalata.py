"""Anima il meme "L'insalata aumenta ancora" aggiungendo luci e oggetti animati sopra il disegno.

Animazioni: AL SUPERMERCATO - neon che tremolano (uno fa i capricci), la busta
d'insalata trema nella mano, il cartellino 3,49 EUR pulsa di rosso e ne escono
frecce "prezzo in salita", gocce di sudore; IO - sole caldo, riflesso sul pannellino,
farfalle tra le piante, scintille su fragole e insalata, cartello IDROPONICA che dondola.
Audio: ronzio dei neon, "bip" della cassa a ogni rincaro, uccellini.

Uso: python anima_meme_insalata.py OUTPUT.mp4
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

SRC = "/home/salvatore/risparmio-energetico/static/immagini/meme-insalata-idroponica.jpg"
OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/meme-insalata.mp4"
W, H = 1280, 720
FPS = 25
DUR = 10.0
N = int(FPS * DUR)
HEADER = 80
TAU = 2 * math.pi
RISE_PERIOD = 2.5  # ogni quanto il prezzo "sale" (freccia + bip)
rng = np.random.default_rng(5)

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


# --- neon del supermercato: segmenti (x0, y0, x1, y1) ---------------------------------
NEONS = [(0, 107, 118, 118), (0, 172, 75, 178), (570, 150, 630, 118), (0, 212, 45, 218)]
BAD_NEON = 1  # quello che fa i capricci


def neon_on(t):
    """Il neon difettoso si spegne a scatti ogni tanto."""
    k = int(t * 12) % 40
    return 0.0 if k in (5, 7, 8, 23, 25) else 1.0


# --- busta d'insalata + mano che tremano --------------------------------------------
BAG = (245, 320, 490, 700)
bag_mask = feather_rect(*BAG, soft=8)[..., None]

# --- cartello IDROPONICA che dondola attorno al gancio -------------------------------
SIGN = (1128, 528, 1280, 652)
SIGN_PIVOT = (1210, 540)
sign_mask = feather_rect(*SIGN, soft=4)[..., None]

# --- pannellino solare: pixel blu scuri nel suo riquadro ----------------------------
box = np.zeros((H, W), bool)
box[525:655, 638:760] = True
panel_mask = (box & (base[..., 2] > base[..., 0] + 10) & (base.mean(axis=2) < 150)).astype(np.float32)

DROPS = [dict(x=148, y=232, t0=0.4, per=2.4), dict(x=262, y=222, t0=1.5, per=2.1)]

BUTTERFLIES = [dict(cx=1000, cy=560, ax=110, ay=60, fx=0.11, fy=0.23, ph=0.0, col=(255, 200, 40)),
               dict(cx=1150, cy=330, ax=80, ay=90, fx=0.15, fy=0.19, ph=2.0, col=(255, 255, 255)),
               dict(cx=705, cy=440, ax=28, ay=60, fx=0.13, fy=0.17, ph=4.0, col=(255, 140, 60))]

SPARKLES = [(1250, 283), (1238, 462), (1268, 452), (1010, 360), (1060, 420), (960, 430)]

S_SMALL, S_MED, S_BIG, S_HUGE = sprite(3), sprite(8), sprite(18), sprite(60)
S_NEON = sprite(5)


def sparkle(d, sx, sy, k):
    r = 11 * k
    c = (255, 255, 220, int(255 * k))
    d.line([(sx - r, sy), (sx + r, sy)], fill=c, width=3)
    d.line([(sx, sy - r), (sx, sy + r)], fill=c, width=3)
    d.line([(sx - r * 0.4, sy - r * 0.4), (sx + r * 0.4, sy + r * 0.4)], fill=c, width=2)
    d.line([(sx - r * 0.4, sy + r * 0.4), (sx + r * 0.4, sy - r * 0.4)], fill=c, width=2)


def draw_overlay(t):
    """Disegni vettoriali (frecce, gocce, farfalle, scintille) su un livello RGBA."""
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)

    # frecce rosse che salgono dal cartellino del prezzo
    for j in range(2):
        age = (t - j * 0.25) % RISE_PERIOD
        if age < 1.4:
            k = age / 1.4
            x, y = 565 + 30 * j, 390 - 120 * k
            a = int(255 * (1 - k) ** 0.7)
            s = 24 * (0.6 + 0.4 * min(1, age * 5))
            d.polygon([(x, y - s), (x - s, y + s * 0.3), (x - s * 0.4, y + s * 0.3),
                       (x - s * 0.4, y + s * 1.2), (x + s * 0.4, y + s * 1.2),
                       (x + s * 0.4, y + s * 0.3), (x + s, y + s * 0.3)],
                      fill=(230, 30, 30, a), outline=(255, 255, 255, a))

    # gocce di sudore
    for g in DROPS:
        age = (t + g["t0"]) % g["per"]
        k = age / g["per"]
        r = 2 + 10 * k if k < 0.25 else 4.5
        y = g["y"] if k < 0.25 else g["y"] + 160 * (k - 0.25) ** 2
        a = int(230 * (1 - max(0, k - 0.7) / 0.3))
        d.ellipse([g["x"] - r, y - r, g["x"] + r, y + r * 1.3], fill=(170, 215, 255, a),
                  outline=(60, 110, 170, a))
        d.polygon([(g["x"] - r * 0.7, y - r * 0.5), (g["x"] + r * 0.7, y - r * 0.5),
                   (g["x"], y - r * 2.2)], fill=(170, 215, 255, a))

    # farfalle: quattro ali che si chiudono e aprono
    for b in BUTTERFLIES:
        x = b["cx"] + b["ax"] * math.sin(TAU * b["fx"] * t + b["ph"])
        y = b["cy"] + b["ay"] * math.sin(TAU * b["fy"] * t + b["ph"] * 1.3)
        open_ = 0.25 + 0.75 * abs(math.sin(t * 11 + b["ph"]))
        c = b["col"] + (240,)
        edge = (60, 40, 20, 240)
        for side in (-1, 1):
            wx = side * 20 * open_
            d.ellipse([x + min(0, wx), y - 20, x + max(0, wx), y + 2], fill=c, outline=edge)
            wx2 = side * 14 * open_
            d.ellipse([x + min(0, wx2), y - 2, x + max(0, wx2), y + 14], fill=c, outline=edge)
        d.line([(x, y - 16), (x, y + 12)], fill=(50, 35, 20, 255), width=3)

    # scintille su fragole e insalata
    for j, (sx, sy) in enumerate(SPARKLES):
        k = max(0.0, math.sin(t * 2.1 + j * 1.9)) ** 5
        if k > 0.05:
            sparkle(d, sx, sy, k)
    return np.asarray(ov).astype(np.float32)


def frame(i):
    t = i / FPS
    light = np.zeros((H, W, 3), np.float32)
    img = base.copy()

    # busta d'insalata che trema nella mano
    dx = int(round(2.0 * math.sin(t * 29) + 1.0 * math.sin(t * 47)))
    dy = int(round(1.5 * math.sin(t * 33 + 2)))
    img = img * (1 - bag_mask) + np.roll(np.roll(base, dy, 0), dx, 1) * bag_mask

    # cartello IDROPONICA che dondola (+-2 gradi)
    ang = 2.0 * math.sin(t * 1.6)
    rot = np.asarray(base_img.rotate(ang, resample=Image.BICUBIC, center=SIGN_PIVOT)).astype(np.float32)
    img = img * (1 - sign_mask) + rot * sign_mask

    # neon: alone freddo lungo ogni tubo, quello difettoso a scatti
    for j, (x0, y0, x1, y1) in enumerate(NEONS):
        on = neon_on(t) if j == BAD_NEON else 1.0
        for u in np.linspace(0, 1, 8):
            add(light, S_NEON, x0 + (x1 - x0) * u, y0 + (y1 - y0) * u, (220, 240, 255),
                (0.45 + 0.05 * math.sin(t * 50)) * on)
        if on == 0:  # tubo spento: lo scuriamo davvero
            add(light, S_MED, (x0 + x1) / 2, (y0 + y1) / 2, (-160, -160, -160), 1.0)

    # cartellino del prezzo che pulsa di rosso a ogni rincaro
    age = t % RISE_PERIOD
    pulse = math.exp(-age * 3)
    add(light, S_BIG, 545, 440, (255, 40, 30), 0.15 + 0.5 * pulse)

    # sole caldo sul balcone
    add(light, S_HUGE, 690, 95, (255, 230, 170), 0.35 + 0.05 * math.sin(t * 1.4))
    add(light, S_BIG, 690, 95, (255, 250, 220), 0.4)

    # riflesso che scorre sul pannellino ogni 3 s
    pos = ((t % 3.0) / 3.0) * 300 + 1100
    band = np.exp(-((XX + YY * 0.8 - pos) / 16) ** 2)
    light += (panel_mask * band)[..., None] * np.array([200, 220, 255], np.float32)

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
    # ronzio dei neon a 100 Hz con armoniche
    audio += 0.05 * (np.sin(TAU * 100 * tt) + 0.5 * np.sin(TAU * 200 * tt) + 0.25 * np.sin(TAU * 300 * tt))
    # bip della cassa a ogni rincaro
    x = tt % RISE_PERIOD
    audio += np.where(x < 0.12, 0.45 * np.sin(TAU * 1800 * x), 0)
    # uccellini
    for _ in range(16):
        t0 = rng.uniform(0.5, DUR - 0.5)
        f0 = rng.uniform(2800, 4200)
        for rep in range(int(rng.integers(2, 4))):
            xx = tt - (t0 + rep * 0.11)
            env = np.where((xx > 0) & (xx < 0.07), np.sin(math.pi * np.clip(xx / 0.07, 0, 1)), 0)
            audio += 0.12 * env * np.sin(TAU * (f0 * xx + 9000 * xx * xx))
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
