"""Anima il meme "Quando piove" aggiungendo oggetti animati sopra il disegno originale.

Animazioni: pioggia su entrambi i pannelli, acqua che scorre dalla grondaia dei vicini
con schizzi a terra, cerchi nelle pozzanghere, lampo con tuono, e l'indicatore della
cisterna che sale da 0% a 100% con il badge "PIENA!". Audio: pioggia + tuono sintetizzati.

Uso: python anima_meme_pioggia.py OUTPUT.mp4 [--muovi]
  --muovi  fa muovere anche i personaggi del disegno (deformazione locale, vedi WARPS)
Richiede: pillow, numpy, imageio-ffmpeg.
"""
import math
import subprocess
import sys
import wave

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFont

SRC = "/home/salvatore/risparmio-energetico/static/immagini/meme-quando-piove-cisterna.jpg"
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
OUT = ARGS[0] if ARGS else "/tmp/meme-quando-piove.mp4"
MUOVI = "--muovi" in sys.argv
W, H = 1280, 720
FPS = 25
DUR = 10.0
N = int(FPS * DUR)
HEADER = 88  # sotto la fascia nera del titolo
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
rng = np.random.default_rng(7)

base = Image.open(SRC).convert("RGB")

# --- Indicatore cisterna -------------------------------------------------------
# Interno del tubo (misurato sull'originale): x 697-716, 0% a y=523, 100% a y=355
TX0, TX1 = 695, 721
TY_TOP, TY_BOT = 342, 538
Y0, Y100 = 523, 355
TICKS = [355, 369, 393, 414, 433, 455, 478, 500, 523]  # tacche 0-100% ogni 12.5%
orig = np.asarray(base).astype(np.float32)
# profilo orizzontale (ombreggiatura cilindrica) del tubo vuoto e pieno, senza giunture
empty_row = np.median(orig[346:398, TX0:TX1], axis=0)
blue_row = np.median(orig[415:532, TX0:TX1], axis=0)
shape = (TY_BOT - TY_TOP, TX1 - TX0, 3)
empty = np.broadcast_to(empty_row, shape).copy()
full = np.broadcast_to(blue_row, shape).copy()
full += rng.normal(0, 4, shape[:2])[..., None]  # leggera grana come nel disegno


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def level_at(t):
    return ease((t - 0.6) / 7.0)  # 0 -> 1 fra 0.6 s e 7.6 s


# --- Pioggia ---------------------------------------------------------------------
def make_drops(n, speed, length, alpha, width):
    return dict(x=rng.uniform(-100, W, n), y=rng.uniform(0, H, n),
                v=rng.uniform(0.8, 1.2, n) * speed, l=length, a=alpha, w=width)


layers = [make_drops(260, 900, 14, 70, 1), make_drops(110, 1500, 26, 120, 2)]
SLANT = 0.18  # spostamento orizzontale per pixel di caduta


# --- Grondaia dei vicini --------------------------------------------------------
stream = [(405, 150), (400, 200), (404, 330), (398, 450), (391, 595)]


def point_on(path, s):
    seg = [math.dist(a, b) for a, b in zip(path, path[1:])]
    s *= sum(seg)
    for (a, b), d in zip(zip(path, path[1:]), seg):
        if s <= d:
            k = s / d
            return a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k
        s -= d
    return path[-1]


splash = [dict(t0=rng.uniform(0, 1), vx=rng.uniform(-110, 110), vy=rng.uniform(-260, -120))
          for _ in range(40)]

# --- Pozzanghere -----------------------------------------------------------------
puddle_zones = [(20, 500, 330, 560), (60, 600, 520, 700), (620, 640, 900, 700)]
ripples = []
for _ in range(45):
    x0, y0, x1, y1 = puddle_zones[rng.integers(len(puddle_zones))]
    ripples.append((rng.uniform(x0, x1), rng.uniform(y0, y1), rng.uniform(0, DUR), rng.uniform(0.7, 1.1)))

# --- Lampi -----------------------------------------------------------------------
FLASHES = [(3.2, 0.45), (3.35, 0.25), (3.5, 0.55), (8.4, 0.4)]


def flash_at(t):
    return max([a * max(0.0, 1 - abs(t - ft) / 0.06) for ft, a in FLASHES] + [0.0])


font_badge = ImageFont.truetype(FONT, 30)

# --- Movimento del disegno (deformazione locale, senza ritagli né buchi) ---------
# Ogni zona: centro, raggio x/y della sfumatura gaussiana, spostamento (dx, dy) nel tempo.
TAU = 2 * math.pi
WARPS = [
    # vicino: l'ombrello ondeggia nel vento
    (150, 290, 95, 55, lambda t: (4 * math.sin(TAU * 0.8 * t), 1.5 * math.sin(TAU * 1.6 * t))),
    # vicino: sbuffo/scuotimento di testa
    (178, 318, 28, 30, lambda t: (1.5 * math.sin(TAU * 2.5 * t), 0)),
    # io: saltello di gioia (corpo)
    (880, 420, 75, 140, lambda t: (0, -7 * abs(math.sin(TAU * 1.0 * t)))),
    # io: testa che ride
    (885, 255, 38, 40, lambda t: (2 * math.sin(TAU * 2 * t), -2 * abs(math.sin(TAU * 1.0 * t)))),
    # io: braccio che indica il cielo
    (768, 200, 30, 40, lambda t: (3 * math.sin(TAU * 2 * t), -3 * abs(math.sin(TAU * 2 * t)))),
    # io: pugno che esulta
    (1005, 355, 30, 30, lambda t: (2 * math.sin(TAU * 2 * t + 1), -4 * abs(math.sin(TAU * 2 * t)))),
    # galline che beccano (fase diversa ciascuna)
    (1152, 492, 20, 18, lambda t: (0, 4 * max(0, math.sin(TAU * 1.3 * t)))),
    (1203, 492, 20, 18, lambda t: (0, 4 * max(0, math.sin(TAU * 1.3 * t + 2)))),
    (1245, 488, 20, 18, lambda t: (0, 4 * max(0, math.sin(TAU * 1.3 * t + 4)))),
    # foglie di zucchine e piante di pomodoro nel vento
    (1000, 600, 70, 40, lambda t: (3 * math.sin(TAU * 0.7 * t), 0)),
    (1180, 610, 70, 40, lambda t: (3 * math.sin(TAU * 0.7 * t + 1), 0)),
    (970, 460, 60, 60, lambda t: (2.5 * math.sin(TAU * 0.6 * t + 2), 0)),
    # alberi sullo sfondo
    (1180, 300, 90, 60, lambda t: (3 * math.sin(TAU * 0.5 * t), 0)),
    (20, 300, 40, 70, lambda t: (3 * math.sin(TAU * 0.5 * t + 1), 0)),
]
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)


def warp(arr, t):
    dx = np.zeros((H, W), np.float32)
    dy = np.zeros((H, W), np.float32)
    for cx, cy, sx, sy, f in WARPS:
        ox, oy = f(t)
        y0, y1 = max(0, cy - 3 * sy), min(H, cy + 3 * sy)
        x0, x1 = max(0, cx - 3 * sx), min(W, cx + 3 * sx)
        g = np.exp(-((XX[y0:y1, x0:x1] - cx) ** 2 / (2 * sx * sx) + (YY[y0:y1, x0:x1] - cy) ** 2 / (2 * sy * sy)))
        dx[y0:y1, x0:x1] += ox * g
        dy[y0:y1, x0:x1] += oy * g
    sx_ = np.clip(XX - dx, 0, W - 1.001)
    sy_ = np.clip(YY - dy, 0, H - 1.001)
    x0 = sx_.astype(np.int32)
    y0 = sy_.astype(np.int32)
    fx = (sx_ - x0)[..., None]
    fy = (sy_ - y0)[..., None]
    a = arr.astype(np.float32)
    top = a[y0, x0] * (1 - fx) + a[y0, x0 + 1] * fx
    bot = a[y0 + 1, x0] * (1 - fx) + a[y0 + 1, x0 + 1] * fx
    return (top * (1 - fy) + bot * fy).astype(np.uint8)


def frame(i):
    t = i / FPS
    img = base.copy()

    # cisterna
    lv = level_at(t)
    yl = Y0 + (Y100 - Y0) * lv
    arr = np.asarray(img).copy()
    tube = empty.copy()
    cut = int(round(yl)) - TY_TOP
    tube[max(cut, 0):] = full[max(cut, 0):]
    arr[TY_TOP:TY_BOT, TX0:TX1] = tube.clip(0, 255).astype(np.uint8)
    img = Image.fromarray(warp(arr, t) if MUOVI else arr)

    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)

    for k, ty in enumerate(TICKS):  # ridisegna le tacche coperte dal nuovo riempimento
        d.line([(TX1 - (9 if k % 2 == 0 else 5), ty), (TX1 - 1, ty)], fill=(225, 230, 230, 220), width=2)

    # superficie dell'acqua nel tubo, con piccola onda
    wob = math.sin(t * 9) * 1.2
    d.line([(TX0, yl + wob), (TX1 - 1, yl - wob)], fill=(210, 235, 255, 230), width=2)
    for k in range(4):  # bollicine che salgono
        by = TY_BOT - ((t * 40 + k * 37) % max(1, TY_BOT - yl))
        if by > yl + 4:
            d.ellipse([TX0 + 4 + k * 3, by, TX0 + 7 + k * 3, by + 3], fill=(230, 245, 255, 150))

    # badge "PIENA!" quando arriva al 100%
    if lv >= 0.999:
        tp = t - 7.6
        s = min(1.0, tp / 0.25) * (1 + 0.15 * math.exp(-tp * 6) * math.sin(tp * 30))
        if s > 0.05:
            bw, bh = int(170 * s), int(56 * s)
            cx, cy = 740, 300
            d.rounded_rectangle([cx - bw // 2, cy - bh // 2, cx + bw // 2, cy + bh // 2],
                                radius=int(14 * s), fill=(40, 170, 60, 240), outline=(255, 255, 255, 255), width=3)
            if s > 0.6:
                d.text((cx, cy), "PIENA!", font=ImageFont.truetype(FONT, int(30 * s)),
                       fill="white", anchor="mm")

    # acqua che scorre dalla grondaia
    for k in range(14):
        s = ((t * 1.6) + k / 14) % 1.0
        x, y = point_on(stream, s)
        d.line([(x, y), (x + rng.uniform(-2, 2), y + 16)], fill=(235, 245, 255, 170), width=3)
    for p in splash:
        tt = (t * 1.3 + p["t0"]) % 1.0 * 0.7
        x = 391 + p["vx"] * tt
        y = 598 + p["vy"] * tt + 700 * tt * tt
        if y < 605:
            d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=(230, 240, 255, int(200 * (1 - tt / 0.7))))

    # cerchi nelle pozzanghere
    for x, y, t0, sc in ripples:
        age = (t - t0) % 1.4
        if age < 0.9:
            r = 4 + age * 22 * sc
            a = int(140 * (1 - age / 0.9))
            d.ellipse([x - r, y - r * 0.35, x + r, y + r * 0.35], outline=(220, 230, 240, a), width=1)

    # pioggia
    for L in layers:
        ys = (L["y"] + L["v"] * t) % H
        xs = (L["x"] + ys * SLANT) % (W + 100) - 50
        for x, y in zip(xs, ys):
            if y > HEADER:
                d.line([(x, y), (x + L["l"] * SLANT, y + L["l"])], fill=(215, 225, 235, L["a"]), width=L["w"])

    img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")

    # lampo (solo sotto il titolo)
    f = flash_at(t)
    if f > 0:
        a = np.asarray(img).astype(np.float32)
        a[HEADER:] = a[HEADER:] + (255 - a[HEADER:]) * f * 0.6
        img = Image.fromarray(a.astype(np.uint8))
    return img


def make_audio(path, sr=44100):
    n = int(DUR * sr)
    white = rng.normal(0, 1, n)
    # pioggia: rumore filtrato (passa-basso semplice) + crepitio
    rain = np.convolve(white, np.ones(6) / 6, mode="same") * 0.25
    rain += (rng.random(n) < 0.004) * rng.normal(0, 0.5, n)
    # tuono dopo il lampo: rumore molto grave con inviluppo
    brown = np.cumsum(rng.normal(0, 1, n))
    brown -= np.convolve(brown, np.ones(2000) / 2000, mode="same")
    brown /= np.abs(brown).max()
    tt = np.arange(n) / sr
    env = np.zeros(n)
    for start, amp in [(3.9, 1.0), (8.9, 0.7)]:
        x = tt - start
        env += np.where(x > 0, amp * (1 - np.exp(-x * 8)) * np.exp(-x * 0.9), 0)
    audio = rain + brown * env * 0.9
    fade = np.minimum(1, np.minimum(tt / 0.3, (DUR - tt) / 0.5))
    audio = audio * fade
    audio = (audio / np.abs(audio).max() * 0.8 * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(audio.tobytes())


if __name__ == "__main__":
    wav = OUT + ".wav"
    make_audio(wav)
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    proc = subprocess.Popen(
        [ff, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
         "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-pix_fmt", "yuv420p",
         "-crf", "20", "-preset", "medium", "-c:a", "aac", "-b:a", "128k", "-shortest",
         "-movflags", "+faststart", OUT],
        stdin=subprocess.PIPE)
    for i in range(N):
        proc.stdin.write(frame(i).tobytes())
    proc.stdin.close()
    proc.wait()
    import os
    os.remove(wav)
    print("OK", OUT)
