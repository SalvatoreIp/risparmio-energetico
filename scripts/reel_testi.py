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


def probe(path):
    """Restituisce (larghezza, altezza, durata in secondi) del video."""
    out = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-hide_banner", "-i", path],
                         capture_output=True, text=True).stderr
    hh, mm, ss = out.split("Duration: ")[1].split(",")[0].split(":")
    dur = int(hh) * 3600 + int(mm) * 60 + float(ss)
    for tok in out.split():
        tok = tok.rstrip(",")
        if "x" in tok and tok.replace("x", "").isdigit():
            w, h = tok.split("x")
            return int(w), int(h), dur
    raise SystemExit("dimensioni del video non trovate")


def fit_font(draw, text, max_w, size):
    while size > 12:
        f = ImageFont.truetype(FONT, size)
        if draw.textlength(text, font=f) <= max_w:
            return f
        size -= 2
    return ImageFont.truetype(FONT, size)


def fit_lines(draw, text, max_w, size):
    """Testo su una riga se ci sta ad almeno il 75% della dimensione, altrimenti su due righe."""
    f = fit_font(draw, text, max_w, size)
    words = text.split()
    if f.size >= size * 0.75 or len(words) < 2:
        return [text], f
    # spezza nel punto che rende le due righe il piu' possibile uguali
    cut = min(range(1, len(words)), key=lambda k: abs(len(" ".join(words[:k])) - len(" ".join(words[k:]))))
    lines = [" ".join(words[:cut]), " ".join(words[cut:])]
    return lines, fit_font(draw, max(lines, key=len), max_w, size)


def title_png(w, text, path):
    d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    lines, f = fit_lines(d, text, w * 0.92, int(w * 0.12))
    band = int(len(lines) * f.size * 1.15 + w * 0.06)
    im = Image.new("RGBA", (w, band), (0, 0, 0, 255))
    d = ImageDraw.Draw(im)
    d.multiline_text((w / 2, band / 2), "\n".join(lines), font=f, fill=(255, 255, 255),
                     anchor="mm", align="center", spacing=int(f.size * 0.15))
    im.save(path)
    return band


def label_png(w, text, color, path):
    im = Image.new("RGBA", (w, int(w * 0.3)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if color == "fumetto":
        lines, f = fit_lines(d, text, w * 0.8, int(w * 0.075))
        tw = max(d.textlength(t, font=f) for t in lines)
        pad = w * 0.04
        th = len(lines) * f.size * 1.2
        box = [w / 2 - tw / 2 - pad, 10, w / 2 + tw / 2 + pad, 10 + th + 2 * pad * 0.8]
        d.rounded_rectangle(box, radius=int(pad), fill=(255, 255, 255, 245), outline=(0, 0, 0), width=5)
        d.multiline_text((w / 2, (box[1] + box[3]) / 2), "\n".join(lines), font=f, fill=(0, 0, 0),
                         anchor="mm", align="center", spacing=int(f.size * 0.2))
    else:
        lines, f = fit_lines(d, text, w * 0.9, int(w * 0.085))
        d.multiline_text((w / 2, im.height * 0.4), "\n".join(lines), font=f, fill=COLORS[color],
                         anchor="mm", align="center", spacing=int(f.size * 0.15),
                         stroke_width=max(4, f.size // 9), stroke_fill=(0, 0, 0))
    im.save(path)


def main():
    src, out, title, *labels = sys.argv[1:]
    w, h, dur = probe(src)
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
                    # audio sfumato ai due capi: il reel riparte in loop senza "scatto" sonoro
                    "-filter_complex", ";".join(filters + [
                        f"[0:a]afade=t=in:d=0.15,afade=t=out:st={dur - 0.35:.2f}:d=0.35[a]"]),
                    "-map", f"[{last}]", "-map", "[a]",
                    "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac",
                    "-b:a", "160k", "-movflags", "+faststart", out], check=True)
    print("OK", out)


if __name__ == "__main__":
    main()
