"""19/11/2026: toglie riquadri e link Amazon dagli articoli (affiliazione chiusa, e su Google
fanno sembrare il sito un sito di affiliazione). Uso: python3 scripts/togli_amazon.py [--scrivi]
Senza --scrivi mostra solo cosa cambierebbe."""
import glob, re, sys

AMZ = r"https?://(?:www\.)?(?:amazon\.[a-z.]+|amzn\.[a-z]+)[^\s)\"']*"
scrivi = "--scrivi" in sys.argv
tot = {"riquadri": 0, "colonne": 0, "link": 0, "file": 0}


def cella_amazon(c):
    c = c.strip()
    return bool(re.fullmatch(r"(\[[^\]]*\]\(" + AMZ + r"\)|<a [^>]*" + AMZ + r"[^>]*>[^<]*</a>|—|-|–|n\.d\.|)", c, re.I)) and c not in ("",)


def tabella(righe):
    """Toglie le colonne fatte solo di link Amazon (o vuote/trattini)."""
    celle = [r.strip().strip("|").split("|") for r in righe]
    n = len(celle[0])
    if any(len(c) != n for c in celle):
        return righe, 0
    via = []
    for j in range(n):
        corpo = [c[j] for c in celle[2:]]
        if corpo and any(re.search(AMZ, x) for x in corpo) and all(cella_amazon(x) or not x.strip() for x in corpo):
            via.append(j)
    if not via:
        return righe, 0
    out = []
    for c in celle:
        out.append("| " + " | ".join(x.strip() for j, x in enumerate(c) if j not in via) + " |")
    return out, len(via)


for f in sorted(glob.glob("content/**/*.md", recursive=True)):
    t = open(f, encoding="utf-8").read()
    o = t
    # 1. riquadro arancione
    t, n = re.subn(r"\n?<div class=\"cta-box\">.*?</div>\n?", "\n", t, flags=re.S)
    tot["riquadri"] += n
    # 2. colonne di tabella con soli link Amazon
    righe = t.split("\n")
    nuove, blocco = [], []
    for r in righe + [""]:
        if r.lstrip().startswith("|"):
            blocco.append(r); continue
        if blocco:
            b, k = tabella(blocco) if len(blocco) >= 3 else (blocco, 0)
            tot["colonne"] += k; nuove += b; blocco = []
        nuove.append(r)
    t = "\n".join(nuove[:-1])
    # 3. link rimasti: si tiene il testo, si toglie il link
    t, n1 = re.subn(r"\[([^\]]*)\]\(" + AMZ + r"\)", r"\1", t)
    t, n2 = re.subn(r"<a [^>]*href=\"" + AMZ + r"\"[^>]*>(.*?)</a>", r"\1", t, flags=re.S)
    tot["link"] += n1 + n2
    t = re.sub(r"\n{3,}", "\n\n", t)
    if t != o:
        tot["file"] += 1
        if scrivi:
            open(f, "w", encoding="utf-8").write(t)
print(tot)
