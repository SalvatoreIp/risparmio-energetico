"""Scarica un'immagine generata con ElevenLabs e la salva come JPG in static/immagini/.

L'URL restituito da ElevenLabs (media[].url di creative_get_flow_run_status) e' firmato e
scade dopo circa 2 ore: va scaricato subito. L'immagine viene ridimensionata a 1280 px di
larghezza (come le altre copertine del sito) e salvata come static/immagini/<slug>.jpg.

Uso: python3 scripts/salva_immagine.py "<URL>" <slug>
Richiede: pillow (gia' installato nel python3 di sistema).
"""
import io
import os
import sys
import urllib.request

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WIDTH = 1280


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    url, slug = sys.argv[1], sys.argv[2]
    if not slug.replace("-", "").isalnum() or slug != slug.lower():
        sys.exit(f"slug non valido: {slug} (solo minuscole, numeri e trattini)")
    with urllib.request.urlopen(url, timeout=60) as r:
        data = r.read()
    im = Image.open(io.BytesIO(data)).convert("RGB")
    if im.width > WIDTH:
        im = im.resize((WIDTH, round(im.height * WIDTH / im.width)), Image.LANCZOS)
    out = os.path.join(ROOT, "static", "immagini", f"{slug}.jpg")
    im.save(out, "JPEG", quality=85, optimize=True, progressive=True)
    print(f"OK {out} {im.width}x{im.height} {os.path.getsize(out) // 1024} KB")


if __name__ == "__main__":
    main()
