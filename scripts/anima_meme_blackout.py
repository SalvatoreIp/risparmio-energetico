"""Anima il meme "Blackout nel quartiere" aggiungendo luci e oggetti animati sopra il disegno.

Animazioni: le finestre dei vicini sono accese, tremolano e si spengono (il blackout);
candele e torce dei telefoni che tremolano, fiamma del fornello, vapore da padella e
tazza, lanterne e lampade di casa mia, LED della batteria, lucciole nell'orto, stelle.
Audio: grilli, frittura in padella e il "clack" della corrente che salta.

Uso: python anima_meme_blackout.py OUTPUT.mp4
Richiede: pillow, numpy, imageio-ffmpeg.
"""
import math
import os
import subprocess
import sys
import wave

import imageio_ffmpeg
import numpy as np
from PIL import Image

SRC = "/home/salvatore/risparmio-energetico/static/immagini/meme-blackout-nel-quartiere.jpg"
OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/meme-blackout.mp4"
W, H = 1280, 720
FPS = 25
DUR = 10.0
N = int(FPS * DUR)
HEADER = 95
BLACKOUT = 1.6  # secondo in cui salta la corrente ai vicini
TAU = 2 * math.pi
rng = np.random.default_rng(11)

base = np.asarray(Image.open(SRC).convert("RGB")).astype(np.float32)
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


def flicker(t, seed, speed=1.0):
    """Tremolio tipo fiamma: somma di sinusoidi a frequenze non armoniche, 0..1."""
    v = (math.sin(t * 13.1 * speed + seed) + 0.6 * math.sin(t * 23.7 * speed + seed * 2)
         + 0.4 * math.sin(t * 41.3 * speed + seed * 3))
    return 0.5 + v / 4.0


# --- finestre dei vicini (x0, y0, x1, y1) ----------------------------------------
WINDOWS = [(40, 242, 82, 302), (128, 250, 167, 310), (332, 320, 352, 360), (357, 322, 375, 362),
           (420, 340, 435, 375), (440, 340, 452, 375), (480, 357, 490, 385), (492, 357, 502, 385),
           (372, 402, 395, 447), (520, 370, 530, 390)]
win_mask = np.zeros((H, W), np.float32)
for x0, y0, x1, y1 in WINDOWS:
    win_mask[y0:y1, x0:x1] = 1.0
# bordi morbidi: piccola sfocatura a scatola
for _ in range(2):
    win_mask = (win_mask + np.roll(win_mask, 1, 0) + np.roll(win_mask, -1, 0)
                + np.roll(win_mask, 1, 1) + np.roll(win_mask, -1, 1)) / 5
WIN_COLOR = np.array([255, 190, 90], np.float32)


def neighbours_on(t):
    if t < BLACKOUT:
        return 1.0
    # tremolio sempre piu' debole per mezzo secondo, poi buio
    pattern = [1, 0, 1, 0.3, 0, 0.7, 0, 0, 0.2, 0]
    k = int((t - BLACKOUT) * 20)
    return pattern[k] if k < len(pattern) else 0.0


# --- stelle: punti di cielo scuro con intorno tutto scuro --------------------------
lum = base.mean(axis=2)
stars = []
while len(stars) < 45:
    x, y = int(rng.uniform(5, W - 5)), int(rng.uniform(HEADER + 10, 300))
    if 560 < x < 590 or (x < 230 and y > 165):  # divisorio e tetti a sinistra
        continue
    patch = lum[y - 12:y + 13, x - 12:x + 13]
    if patch.max() < 70 and base[y, x, 2] > base[y, x, 0]:
        stars.append((x, y, rng.uniform(0, TAU), rng.uniform(1.5, 4)))

# --- lucciole nell'orto ------------------------------------------------------------
fireflies = [dict(x=rng.uniform(600, 1260), y=rng.uniform(470, 700), ph=rng.uniform(0, TAU),
                  fx=rng.uniform(0.1, 0.3), fy=rng.uniform(0.15, 0.35), ax=rng.uniform(20, 50),
                  ay=rng.uniform(10, 30)) for _ in range(14)]

# --- vapore -------------------------------------------------------------------------
steam = [dict(src=(790, 532), t0=rng.uniform(0, 2.0), drift=rng.uniform(-12, 12), per=2.0)
         for _ in range(10)]
steam += [dict(src=(930, 552), t0=rng.uniform(0, 2.6), drift=rng.uniform(-6, 6), per=2.6)
          for _ in range(4)]

S_SMALL, S_MED, S_BIG, S_HUGE = sprite(3), sprite(8), sprite(18), sprite(45)
S_FLAME = sprite(4, 0.6, 1.4)
S_STEAM = sprite(6)


def frame(i):
    t = i / FPS
    light = np.zeros((H, W, 3), np.float32)

    # finestre dei vicini accese prima del blackout
    on = neighbours_on(t)
    img = base.copy()
    if on > 0:
        img += (win_mask[..., None] * on) * (WIN_COLOR * 0.75 - img * 0.4)
        for x0, y0, x1, y1 in WINDOWS:
            add(light, S_BIG, (x0 + x1) / 2, (y0 + y1) / 2, (255, 180, 80), 0.25 * on)

    # candele: fiammella che danza + alone caldo sui visi
    for (cx, cy), seed in [((93, 478), 1.0), ((420, 585), 4.0)]:
        f = flicker(t, seed)
        add(light, S_FLAME, cx + 1.5 * math.sin(t * 9 + seed), cy - 3, (255, 200, 90), 0.5 + 0.4 * f)
        add(light, S_HUGE, cx, cy - 20, (255, 150, 60), 0.10 + 0.10 * f)

    # torce dei telefoni: tremolano appena (mani che si muovono)
    for (cx, cy), seed in [((262, 478), 2.0), ((366, 512), 5.0)]:
        f = flicker(t, seed, 0.3)
        add(light, S_MED, cx + 2 * math.sin(t * 1.7 + seed), cy + 1.5 * math.sin(t * 2.3 + seed),
            (230, 240, 255), 0.35 + 0.2 * f)

    # stelle che brillano
    for x, y, ph, sp in stars:
        k = max(0.0, math.sin(t * sp + ph)) ** 3
        add(light, S_SMALL, x, y, (220, 230, 255), 1.4 * k)

    # fornello: lingue di fiamma blu attorno al bruciatore
    for j in range(9):
        a = TAU * j / 9
        fx, fy = 785 + 16 * math.cos(a), 561 + 3.5 * math.sin(a)
        h = 0.6 + 0.4 * flicker(t, j * 1.7, 1.6)
        add(light, S_FLAME, fx, fy - 3 * h, (70, 140, 255), 0.55 * h)
    add(light, S_BIG, 785, 556, (80, 120, 255), 0.18 + 0.05 * flicker(t, 9))

    # vapore da padella e tazza
    for s in steam:
        age = (t + s["t0"]) % s["per"]
        k = age / s["per"]
        x = s["src"][0] + s["drift"] * k + 4 * math.sin(age * 3 + s["t0"])
        y = s["src"][1] - 70 * k
        spr = S_STEAM if k < 0.5 else S_MED
        add(light, spr, x, y, (255, 235, 210), 0.22 * math.sin(math.pi * k))

    # luci di casa mia: lampade, lanterna, finestre calde (respirano appena)
    for (cx, cy), seed in [((805, 385), 3.0), ((1058, 365), 6.0), ((668, 645), 7.0)]:
        add(light, S_BIG, cx, cy, (255, 190, 90), 0.20 + 0.08 * flicker(t, seed, 0.5))
    add(light, S_HUGE, 750, 410, (255, 180, 80), 0.08 + 0.02 * math.sin(t * 2))

    # LED verde della batteria che pulsa
    add(light, S_SMALL, 1073, 368, (80, 255, 110), 0.5 + 0.5 * math.sin(t * 4) ** 2)

    # lucciole
    for f in fireflies:
        x = f["x"] + f["ax"] * math.sin(TAU * f["fx"] * t + f["ph"])
        y = f["y"] + f["ay"] * math.sin(TAU * f["fy"] * t + f["ph"] * 2)
        k = max(0.0, math.sin(t * 2.2 + f["ph"])) ** 2
        add(light, S_SMALL, x, y, (220, 255, 120), 1.8 * k)
        add(light, S_MED, x, y, (200, 255, 100), 0.35 * k)

    light[:HEADER] = 0
    out = img + light * (1 - img / 255 * 0.5)  # somma "morbida" che non brucia i chiari
    return out.clip(0, 255).astype(np.uint8)


def make_audio(path, sr=44100):
    n = int(DUR * sr)
    tt = np.arange(n) / sr
    audio = np.zeros(n)
    # grilli: trilli acuti a gruppi, due grilli sfasati
    for f0, rate, ph, amp in [(4300, 3.1, 0.0, 0.10), (4700, 2.6, 1.3, 0.07)]:
        gate = (np.sin(TAU * rate * tt + ph) > 0.55).astype(float)
        trill = 0.5 + 0.5 * np.sin(TAU * 30 * tt)
        audio += amp * np.sin(TAU * f0 * tt) * gate * trill
    # frittura: fruscio con scoppiettii
    white = rng.normal(0, 1, n)
    hiss = white - np.convolve(white, np.ones(8) / 8, mode="same")
    pops = (rng.random(n) < 0.0015) * rng.normal(0, 1.2, n)
    pops = np.convolve(pops, np.exp(-np.arange(200) / 30), mode="same")
    audio += 0.06 * hiss + 0.25 * pops
    # "clack" del blackout con un ronzio che si spegne
    x = tt - BLACKOUT
    audio += np.where(x > 0, 0.9 * np.exp(-x * 60) * np.sin(TAU * 90 * x), 0)
    audio += np.where(tt < BLACKOUT, 0.05 * np.sin(TAU * 50 * tt), 0)
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
