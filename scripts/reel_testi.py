"""Aggiunge le scritte in italiano (titolo fisso + etichette a tempo) a un reel verticale.

I modelli video sbagliano il testo dentro l'immagine, quindi i reel ElevenLabs vengono
generati SENZA scritte e i testi si sovrappongono qui, nello stile dei meme della pagina:
titolo bianco su banda nera in alto, etichette bianche/verdi con bordo nero.

Uso:
  python reel_testi.py INPUT.mp4 OUTPUT.mp4 "TITOLO" "inizio|fine|testo|colore" ...
  colore: bianco, verde (per "IO"/il lato buono), fumetto (testo nero in un fumetto bianco)
Esempio:
  python reel_testi.py raw.mp4 out.mp4 "ARRIVA IL PRIMO FREDDO" \
      "0|3.4|CALDAIA A GAS|bianco" "3.6|8|IO|verde" "5|8|Freddo? Quale freddo?|fumetto"
Richiede: pillow, imageio-ffmpeg.
"""
import os
import subprocess
import sys
import tempfile

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
COLORS = {"bianco": (255, 255, 255), "verde": (90, 220, 60)}


def probe_size(path):
    out = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-hide_banner", "-i", path],
                         capture_output=True, text=True).stderr
    for tok in out.split():
        tok = tok.rstrip(",")
        if "x" in tok and tok.replace("x", "").isdigit():
            w, h = tok.split("x")
            return int(w), int(h)
    raise SystemExit("dimensioni del video non trovate")


def fit_font(draw, text, max_w, size):
    while size > 12:
        f = ImageFont.truetype(FONT, size)
        if draw.textlength(text, font=f) <= max_w:
            return f
        size -= 2
    return ImageFont.truetype(FONT, size)


def title_png(w, text, path):
    band = int(w * 0.2)
    im = Image.new("RGBA", (w, band), (0, 0, 0, 255))
    d = ImageDraw.Draw(im)
    f = fit_font(d, text, w * 0.92, int(band * 0.6))
    d.text((w / 2, band / 2), text, font=f, fill=(255, 255, 255), anchor="mm")
    im.save(path)
    return band


def label_png(w, text, color, path):
    im = Image.new("RGBA", (w, int(w * 0.2)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if color == "fumetto":
        f = fit_font(d, text, w * 0.8, int(w * 0.075))
        tw = d.textlength(text, font=f)
        pad = w * 0.04
        box = [w / 2 - tw / 2 - pad, 10, w / 2 + tw / 2 + pad, 10 + f.size + 2 * pad * 0.8]
        d.rounded_rectangle(box, radius=int(pad), fill=(255, 255, 255, 245), outline=(0, 0, 0), width=5)
        d.text((w / 2, (box[1] + box[3]) / 2), text, font=f, fill=(0, 0, 0), anchor="mm")
    else:
        f = fit_font(d, text, w * 0.9, int(w * 0.085))
        d.text((w / 2, im.height / 2), text, font=f, fill=COLORS[color], anchor="mm",
               stroke_width=max(4, f.size // 9), stroke_fill=(0, 0, 0))
    im.save(path)


def main():
    src, out, title, *labels = sys.argv[1:]
    w, h = probe_size(src)
    tmp = tempfile.mkdtemp()
    inputs, filters = ["-i", src], []
    band = title_png(w, title, f"{tmp}/title.png")
    inputs += ["-i", f"{tmp}/title.png"]
    filters.append("[0:v][1:v]overlay=0:0[v1]")
    last = "v1"
    for k, spec in enumerate(labels):
        t0, t1, text, color = spec.split("|")
        png = f"{tmp}/l{k}.png"
        label_png(w, text, color, png)
        inputs += ["-i", png]
        y = int(h * 0.70) if color == "fumetto" else band + 10
        filters.append(f"[{last}][{k + 2}:v]overlay=0:{y}:enable='between(t,{t0},{t1})'[v{k + 2}]")
        last = f"v{k + 2}"
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", *inputs,
                    "-filter_complex", ";".join(filters), "-map", f"[{last}]", "-map", "0:a?",
                    "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac",
                    "-b:a", "160k", "-movflags", "+faststart", out], check=True)
    print("OK", out)


if __name__ == "__main__":
    main()
