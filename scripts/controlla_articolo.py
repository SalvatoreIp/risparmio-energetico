#!/usr/bin/env python3
"""Controlla che un articolo rispetti le regole di CLAUDE.md.

Uso:
  python3 scripts/controlla_articolo.py content/sezione/file.md [...]
  python3 scripts/controlla_articolo.py --modificati   (articoli nuovi/cambiati rispetto a origin/main)

ERRORI = l'articolo uscirebbe rotto (link interni inesistenti, slug mancante, copertina
assente, tag Amazon sbagliato, data futura). Exit code 1.
AVVISI = regole editoriali (lunghezza, CTA, fonti, tono, prezzi vecchi). Non bloccano.
"""
import datetime
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG_OK = "audiobookit-21"
PAROLE_VIETATE = ["sogno", "sognare", "magia", "magico", "rivoluzione", "rivoluzionario",
                  "incredibile", "libertà energetica", "niente panico", "ti salva la vita"]
PREZZI_VECCHI = [r"0[,.]28\s*€\s*/\s*kWh", r"1[,.]10\s*€\s*/\s*(m³|m3|Smc)"]


def leggi_frontmatter(testo):
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", testo, re.S)
    if not m:
        return None, testo
    fm = {}
    for riga in m.group(1).splitlines():
        r = re.match(r"^(\s*)([A-Za-z_]+):\s*(.*)$", riga)
        if r:
            chiave = ("cover." if r.group(1) else "") + r.group(2)
            fm[chiave] = r.group(3).strip()
    return fm, m.group(2)


def togli_virgolette(v):
    return v.strip().strip('"')


def pagina_esiste(percorso):
    """percorso tipo /sezione/pagina/ -> controlla public/ e static/."""
    p = percorso.split("#")[0].split("?")[0]
    if not p or p == "/":
        return True
    if os.path.exists(os.path.join(ROOT, "static", p.lstrip("/"))):
        return True
    if p.startswith("/vai/"):  # redirect Cloudflare in static/_redirects
        return True
    pub = os.path.join(ROOT, "public", p.strip("/"))
    return os.path.exists(os.path.join(pub, "index.html")) or os.path.isfile(pub)


def e_nuovo(file):
    """True se il file non è ancora nel repository (articolo nuovo)."""
    rel = os.path.relpath(file, ROOT)
    r = subprocess.run(["git", "-C", ROOT, "cat-file", "-e", f"HEAD:{rel}"], capture_output=True)
    return r.returncode != 0


def controlla(file):
    errori, avvisi = [], []
    nuovo = e_nuovo(file)
    with open(file, encoding="utf-8") as f:
        testo = f.read()
    fm, corpo = leggi_frontmatter(testo)
    if fm is None:
        return ["frontmatter mancante o malformato (deve iniziare e finire con ---)"], []

    # slug e copertina: obbligatori solo per gli articoli nuovi. I vecchi senza slug
    # vivono all'URL preso dal titolo e non vanno toccati (cambierebbe un URL indicizzato).
    obbligatori = ["title", "date", "description", "categories"]
    if nuovo:
        obbligatori += ["slug", "cover.image"]
    for campo in obbligatori:
        if not fm.get(campo):
            errori.append(f"manca il campo '{campo}' nel frontmatter")
    for campo in ["title", "description", "slug"]:
        v = fm.get(campo, "")
        if v and not (v.startswith('"') and v.endswith('"')):
            avvisi.append(f"il campo '{campo}' va tra virgolette doppie")

    slug = togli_virgolette(fm.get("slug", ""))
    if slug and not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", slug):
        errori.append(f"slug '{slug}' non valido: solo minuscole, numeri e trattini")

    cover = togli_virgolette(fm.get("cover.image", ""))
    if cover and not cover.startswith("http") and not os.path.exists(os.path.join(ROOT, "static", cover.lstrip("/"))):
        errori.append(f"immagine di copertina {cover} non trovata in static/")

    data = togli_virgolette(fm.get("date", ""))
    try:
        d = datetime.datetime.fromisoformat(data.replace("Z", "+00:00"))
        if d.tzinfo is None:
            d = d.replace(tzinfo=datetime.timezone.utc)
        if d > datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=5):
            errori.append(f"data {data} nel futuro: Hugo non pubblica la pagina")
    except ValueError:
        if data:
            errori.append(f"data '{data}' non leggibile")

    if togli_virgolette(fm.get("draft", "false")) == "true":
        avvisi.append("draft: true, l'articolo non verrà pubblicato")

    # Tag affiliato Amazon
    for tag in re.findall(r"amazon\.it[^\s\"')]*[?&]tag=([A-Za-z0-9-]+)", corpo):
        if tag != TAG_OK:
            errori.append(f"link Amazon con tag '{tag}' invece di '{TAG_OK}'")
    for link in re.findall(r"https?://(?:www\.)?amazon\.it/[^\s\"')]+", corpo):
        if "tag=" not in link:
            avvisi.append(f"link Amazon senza tag affiliato: {link[:80]}")

    # Link interni: solo se public/ esiste (cioè dopo almeno un build)
    if os.path.isdir(os.path.join(ROOT, "public")):
        interni = re.findall(r"\]\((/[^)\s]*)\)", corpo) + re.findall(r'href="(/[^"]*)"', corpo)
        for link in sorted(set(interni)):
            if not pagina_esiste(link):
                errori.append(f"link interno a una pagina che non esiste: {link}")

    # Regole editoriali (avvisi)
    senza_html = re.sub(r"<[^>]+>", " ", corpo)
    parole = len(re.findall(r"\w+", senza_html))
    if parole < 800 or parole > 1300:
        avvisi.append(f"{parole} parole (regola: 800-1200)")
    if 'class="cta-box"' not in corpo:
        avvisi.append("manca il pulsante arancione cta-box dopo l'introduzione")
    if not re.search(r"\*Fonti", corpo):
        avvisi.append("manca la riga *Fonti: ...* in fondo")
    if "€" not in corpo:
        avvisi.append("nessun calcolo in euro")
    basso = senza_html.lower()
    for p in PAROLE_VIETATE:
        # "non è magia" / "nessuna magia" sono frasi concrete, non enfasi
        if re.search(r"(?<!non è )(?<!nessuna )\b" + re.escape(p) + r"\b", basso):
            avvisi.append(f"parola da evitare (tono): '{p}'")
    esclamativi = len(re.findall(r"\w!", senza_html))
    if esclamativi:
        avvisi.append(f"{esclamativi} punti esclamativi")
    for pat in PREZZI_VECCHI:
        if re.search(pat, corpo):
            avvisi.append(f"prezzo superato trovato ({pat}): usare i prezzi aggiornati")
    return errori, avvisi


def articoli_modificati():
    def git(*a):
        r = subprocess.run(["git", "-C", ROOT, *a], capture_output=True, text=True)
        return r.stdout.split()
    files = set(git("diff", "--name-only", "origin/main", "--", "content"))
    files |= set(git("diff", "--name-only", "HEAD", "--", "content"))
    files |= set(git("ls-files", "--others", "--exclude-standard", "--", "content"))
    return sorted(f for f in files if re.match(r"content/[^/]+/[^/]+\.md$", f)
                  and not f.endswith("_index.md") and os.path.exists(os.path.join(ROOT, f)))


def main(argv):
    if argv and argv[0] == "--modificati":
        files = articoli_modificati()
    else:
        files = argv
    totale_errori = 0
    for f in files:
        percorso = f if os.path.isabs(f) else os.path.join(ROOT, f)
        errori, avvisi = controlla(percorso)
        if not errori and not avvisi:
            continue
        print(f"\n{os.path.relpath(percorso, ROOT)}")
        for e in errori:
            print(f"  ERRORE: {e}")
        for a in avvisi:
            print(f"  avviso: {a}")
        totale_errori += len(errori)
    return 1 if totale_errori else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
