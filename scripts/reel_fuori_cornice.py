"""Effetto "esce dalla cornice" (finto 3D) per i reel Facebook.

Il video (verticale, camera fissa) viene mostrato dentro un finto post di Facebook; il
soggetto che si muove viene scontornato fotogramma per fotogramma e disegnato SOPRA la
cornice, cosi' quando avanza sembra uscire dal post verso chi guarda.

Uso:
  /home/salvatore/venv-reel/bin/python scripts/reel_fuori_cornice.py IN.mp4 OUT.mp4 "Testo del post" [--top 520] [--bottom 1300]

--top/--bottom/--margine: bordi della finestra-foto sulla tela 1080x1920 (il video viene
scalato a tutta tela; fuori da quella finestra si vede solo il soggetto).
Richiede il venv /home/salvatore/venv-reel (rembg, opencv, imageio-ffmpeg).
"""
import argparse
import subprocess
import textwrap

import cv2
import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from rembg import new_session, remove

W, H = 1080, 1920
BG = (240, 242, 245)
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
PAGE = "Guida Energia Italia"


def cornice(testo, top, bottom):
    """Disegna il finto post (tutto tranne la foto) e restituisce l'immagine RGB."""
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    card_top = top - 330
    d.rectangle([0, card_top, W, bottom + 170], fill=(255, 255, 255))
    # intestazione: logo tondo, nome pagina, "Adesso"
    d.ellipse([40, card_top + 40, 150, card_top + 150], fill=(46, 160, 67))
    d.text((95, card_top + 95), "GE", font=ImageFont.truetype(FONT_B, 44), fill="white", anchor="mm")
    d.text((175, card_top + 50), PAGE, font=ImageFont.truetype(FONT_B, 40), fill=(5, 5, 5))
    d.text((175, card_top + 105), "Adesso", font=ImageFont.truetype(FONT, 32), fill=(101, 103, 107))
    d.text((W - 60, card_top + 80), "•••", font=ImageFont.truetype(FONT_B, 40), fill=(101, 103, 107), anchor="mm")
    # testo del post (max 3 righe)
    f = ImageFont.truetype(FONT, 42)
    righe = textwrap.wrap(testo, 40)[:3]
    d.multiline_text((40, card_top + 180), "\n".join(righe), font=f, fill=(5, 5, 5), spacing=12)
    # barra azioni sotto la foto
    fa = ImageFont.truetype(FONT_B, 36)
    for i, t in enumerate(["Mi piace", "Commenta", "Condividi"]):
        d.text((W * (i + 0.5) / 3, bottom + 95), t, font=fa, fill=(101, 103, 107), anchor="mm")
    d.line([40, bottom + 30, W - 40, bottom + 30], fill=(206, 208, 212), width=2)
    return np.asarray(im).astype(np.float32)


def maschera(session, frame_rgb):
    """Alpha 0-1 del soggetto principale (solo la componente connessa piu' grande)."""
    a = np.asarray(remove(Image.fromarray(frame_rgb), session=session, only_mask=True)).astype(np.uint8)
    n, lab, stats, _ = cv2.connectedComponentsWithStats((a > 128).astype(np.uint8))
    if n <= 1:
        return np.zeros(a.shape, np.float32)
    big = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    keep = cv2.dilate((lab == big).astype(np.uint8), np.ones((15, 15), np.uint8))
    return (a.astype(np.float32) / 255.0) * keep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inp")
    ap.add_argument("out")
    ap.add_argument("testo")
    ap.add_argument("--top", type=int, default=520)
    ap.add_argument("--bottom", type=int, default=1300)
    ap.add_argument("--margine", type=int, default=50, help="margine laterale della foto")
    args = ap.parse_args()

    base = cornice(args.testo, args.top, args.bottom)
    fuori = np.ones((H, W, 1), np.float32)
    t, b, m = args.top, args.bottom, args.margine
    fuori[t:b, m:W - m] = 0.0  # 1 = fuori dalla finestra-foto

    reader = imageio_ffmpeg.read_frames(args.inp)
    meta = next(reader)
    fps = meta["fps"]
    tmp = args.out + ".noaudio.mp4"
    writer = imageio_ffmpeg.write_frames(tmp, (W, H), fps=fps, quality=8, macro_block_size=8)
    writer.send(None)
    session = new_session("isnet-general-use")
    sw, sh = meta["size"]
    for i, raw in enumerate(reader):
        fr = np.frombuffer(raw, np.uint8).reshape(sh, sw, 3)
        big = cv2.resize(fr, (W, H), interpolation=cv2.INTER_CUBIC).astype(np.float32)
        a = cv2.resize(maschera(session, fr), (W, H))[..., None]
        out = base.copy()
        out[t:b, m:W - m] = big[t:b, m:W - m]
        # ombra morbida del soggetto sulla cornice, poi il soggetto sopra
        sposta = np.zeros_like(a[..., 0])
        sposta[28:, 18:] = a[:-28, :-18, 0]  # ombra spostata in basso a destra, senza "riavvolgere" i bordi
        ombra = cv2.GaussianBlur(sposta, (0, 0), 18)[..., None] * 0.35 * fuori
        out = out * (1 - ombra)
        k = a * fuori
        out = out * (1 - k) + big * k
        writer.send(np.clip(out, 0, 255).astype(np.uint8).tobytes())
        if i % 25 == 0:
            print("fotogramma", i, flush=True)
    writer.close()
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-y", "-loglevel", "error", "-i", tmp, "-i", args.inp, "-map", "0:v", "-map", "1:a?",
                    "-c:v", "copy", "-c:a", "aac", "-shortest", args.out], check=True)
    subprocess.run(["rm", "-f", tmp])
    print("OK", args.out)


if __name__ == "__main__":
    main()
