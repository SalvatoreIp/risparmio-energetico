"""Trasforma un post-consiglio con foto in un breve video verticale (reel 9:16), gratis.

Perche': sulla pagina Facebook i video raggiungono ~200 persone, i post con foto 0-4
(dati letti il 29/09/2026). Il video non ha bisogno di crediti: parte dalla foto gia' usata
per il post (static/immagini/<immagine>.jpg), la anima con uno zoom lento e ci mette sopra,
nello stile dei meme della pagina, un titolo fisso su banda nera e 3-5 schede con i numeri
chiave che compaiono una dopo l'altra. Audio: tappeto morbido sintetizzato + un "tic" a scheda.

Uso:
  python3 scripts/video_consiglio.py ID            # un post della coda (usa "video_testi")
  python3 scripts/video_consiglio.py --tutti       # tutti i post con "video_testi" ma senza video
Nella coda (scripts/fb_posts_queue.json) il post deve avere:
  "video_testi": {"titolo": "...", "schede": [["testo", "bianco|verde|giallo"], ...]}
Il video esce in static/video/consiglio-<immagine>.mp4 e il campo "video" del post viene
compilato, cosi' fb_standalone_post.sh lo pubblica come video invece che come foto.
Richiede: pillow, numpy, imageio-ffmpeg.
"""
import json
import math
import os
import subprocess
import sys
import tempfile
import wave

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

REPO = "/home/salvatore/risparmio-energetico"
QUEUE = os.path.join(REPO, "scripts", "fb_posts_queue.json")
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
COLORS = {"bianco": (255, 255, 255), "verde": (90, 220, 60), "giallo": (255, 215, 64)}
W, H, FPS = 720, 1280, 25
T_INTRO = 1.2        # secondi di sola immagine + titolo prima della prima scheda
T_SCHEDA = 3.0       # durata di ogni scheda
T_FINE = 2.8         # chiusura "guida completa nel primo commento"
SR = 44100


def font_fit(draw, lines, max_w, size):
    while size > 16:
        f = ImageFont.truetype(FONT, size)
        if max(draw.textlength(t, font=f) for t in lines) <= max_w:
            return f
        size -= 2
    return ImageFont.truetype(FONT, size)


def wrap(draw, text, max_w, size, max_lines=3):
    """Va a capo sulle parole cercando la dimensione piu' grande che sta in max_lines righe."""
    words = text.split()
    for s in range(size, 16, -2):
        f = ImageFont.truetype(FONT, s)
        lines, cur = [], ""
        for w_ in words:
            prova = (cur + " " + w_).strip()
            if draw.textlength(prova, font=f) <= max_w:
                cur = prova
            else:
                lines.append(cur)
                cur = w_
        lines.append(cur)
        if len(lines) <= max_lines and all(draw.textlength(t, font=f) <= max_w for t in lines):
            return lines, f
    return lines, f


def title_img(text):
    d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    lines, f = wrap(d, text.upper(), W * 0.92, 72, max_lines=2)
    band = int(len(lines) * f.size * 1.18 + 56)
    im = Image.new("RGBA", (W, band), (0, 0, 0, 255))
    ImageDraw.Draw(im).multiline_text((W / 2, band / 2), "\n".join(lines), font=f, fill="white",
                                      anchor="mm", align="center", spacing=int(f.size * 0.18))
    return im


def card_img(text, color):
    """Scheda: testo grande con bordo nero su un pannello scuro semitrasparente."""
    d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    lines, f = wrap(d, text, W * 0.84, 70, max_lines=3)
    th = len(lines) * f.size * 1.22
    box_h = int(th + 60)
    im = Image.new("RGBA", (W, box_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([24, 0, W - 24, box_h], radius=28, fill=(0, 0, 0, 165))
    d.multiline_text((W / 2, box_h / 2), "\n".join(lines), font=f, fill=COLORS[color],
                     anchor="mm", align="center", spacing=int(f.size * 0.22),
                     stroke_width=max(3, f.size // 12), stroke_fill=(0, 0, 0))
    return im


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def audio(path, dur, tics):
    """Tappeto morbido (accordo maggiore lento) + 'tic' leggeri all'arrivo di ogni scheda."""
    t = np.arange(int(SR * dur)) / SR
    pad = np.zeros_like(t)
    for f0, a in ((220.0, 0.05), (277.18, 0.035), (329.63, 0.035), (440.0, 0.02)):
        pad += a * np.sin(2 * math.pi * f0 * t) * (0.75 + 0.25 * np.sin(2 * math.pi * 0.2 * t + f0))
    env = np.minimum(1, t / 1.0) * np.minimum(1, (dur - t) / 1.0)
    sig = pad * env
    for t0 in tics:
        i0 = int(t0 * SR)
        n = int(0.18 * SR)
        tt = np.arange(n) / SR
        tic = 0.22 * np.sin(2 * math.pi * 1318.5 * tt) * np.exp(-tt * 28)
        sig[i0:i0 + n] += tic[:len(sig) - i0]
    sig = np.clip(sig, -1, 1)
    st = np.repeat((sig * 32767).astype(np.int16)[:, None], 2, axis=1)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(st.tobytes())


def render(img_path, out, titolo, schede):
    schede = schede + [["Guida completa nel primo commento", "giallo"]]
    dur = T_INTRO + T_SCHEDA * (len(schede) - 1) + T_FINE
    n = int(dur * FPS)

    src = Image.open(img_path).convert("RGB")
    # sfondo: la stessa foto riempita, sfocata e scurita
    s = max(W / src.width, H / src.height)
    bg = src.resize((int(src.width * s) + 1, int(src.height * s) + 1)).crop((0, 0, W, H))
    bg = Image.eval(bg.filter(ImageFilter.GaussianBlur(28)), lambda v: int(v * 0.45))
    title = title_img(titolo)
    top = title.height
    # foto in primo piano: riempie tutto lo spazio sotto il titolo (ritaglio ai lati)
    fw, fh = W, H - top
    cards = [card_img(t, c) for t, c in schede]
    starts = [T_INTRO + k * T_SCHEDA for k in range(len(schede))]

    tmp = tempfile.mkdtemp()
    wav = os.path.join(tmp, "a.wav")
    audio(wav, dur, starts)
    ff = subprocess.Popen([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error",
                           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                           "-i", "-", "-i", wav, "-c:v", "libx264", "-crf", "21", "-preset", "medium",
                           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-shortest",
                           "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    for i in range(n):
        t = i / FPS
        frame = bg.copy()
        # zoom lento 1.00 -> 1.10 sulla foto (effetto Ken Burns)
        z = 1.0 + 0.10 * (t / dur)
        ch = min(src.height, src.width * fh / fw) / z
        cw = ch * fw / fh
        cx, cy = src.width / 2, src.height / 2 + (src.height * 0.03) * math.sin(t / dur * math.pi)
        crop = src.crop((int(cx - cw / 2), int(max(0, cy - ch / 2)),
                         int(cx + cw / 2), int(min(src.height, cy + ch / 2))))
        frame.paste(crop.resize((fw, fh), Image.BILINEAR), (0, top))
        frame.paste(title, (0, 0), title)
        # scheda corrente: entra dal basso con una piccola dissolvenza
        k = max([j for j, s0 in enumerate(starts) if t >= s0], default=-1)
        if k >= 0:
            c = cards[k]
            a = ease((t - starts[k]) / 0.35)
            y = int(H - c.height - 110 + (1 - a) * 60)
            if a < 1:
                c = c.copy()
                c.putalpha(c.getchannel("A").point(lambda v: int(v * a)))
            frame.paste(c, (0, y), c)
        ff.stdin.write(frame.tobytes())
    ff.stdin.close()
    ff.wait()
    if ff.returncode != 0:
        raise SystemExit(f"ffmpeg ha fallito per {out}")
    print(f"OK {out} ({dur:.1f} s, {os.path.getsize(out) // 1024} KB)")


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    q = json.load(open(QUEUE))
    posts = q["posts"]
    if sys.argv[1] == "--tutti":
        scelti = [p for p in posts if p.get("video_testi") and not p.get("video")]
    else:
        scelti = [p for p in posts if str(p["id"]) == sys.argv[1]]
        if not scelti or not scelti[0].get("video_testi"):
            raise SystemExit(f"post {sys.argv[1]} non trovato o senza video_testi")
    for p in scelti:
        slug = f"consiglio-{p['immagine']}"
        out = os.path.join(REPO, "static", "video", f"{slug}.mp4")
        vt = p["video_testi"]
        render(os.path.join(REPO, "static", "immagini", f"{p['immagine']}.jpg"), out,
               vt["titolo"], vt["schede"])
        p["video"] = slug
    json.dump(q, open(QUEUE, "w"), ensure_ascii=False, indent=2)
    open(QUEUE, "a").write("\n")


if __name__ == "__main__":
    main()
