"""Avvisa Bing (e gli altri motori IndexNow: Yandex, Seznam, Naver...) delle pagine nuove o cambiate.

Legge public/sitemap.xml (quindi va lanciato DOPO hugo + deploy) e invia solo gli URL il cui
<lastmod> e' diverso da quello gia' inviato: reinviare pagine invariate e' sconsigliato da IndexNow.
Lo stato sta fuori dal repo, come per i post Facebook, per non sporcare il working tree.
La chiave e' il file static/<KEY>.txt, pubblicato su https://guida-energia.com/<KEY>.txt.

Uso: python3 scripts/indexnow.py [--prova] [--tutti]
  --prova  mostra cosa invierebbe, senza inviare e senza toccare lo stato
  --tutti  invia tutti gli URL della sitemap (primo invio)
"""
import json
import os
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

HOST = "guida-energia.com"
KEY = "0bb2e6e80ed609fcf5e8a05a730d2948"
REPO = "/home/salvatore/risparmio-energetico"
SITEMAP = os.path.join(REPO, "public", "sitemap.xml")
STATE = "/home/salvatore/output/indexnow_state.json"
NS = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}

prova = "--prova" in sys.argv
tutti = "--tutti" in sys.argv

urls = {}
for u in ET.parse(SITEMAP).getroot().findall("s:url", NS):
    loc = u.findtext("s:loc", namespaces=NS)
    urls[loc] = u.findtext("s:lastmod", default="", namespaces=NS)

stato = json.load(open(STATE)) if os.path.exists(STATE) else {}
da_inviare = [loc for loc, mod in urls.items() if tutti or stato.get(loc) != mod]

if not da_inviare:
    print("IndexNow: nessuna pagina nuova o cambiata")
    sys.exit(0)

print(f"IndexNow: {len(da_inviare)} URL da inviare")
for loc in da_inviare[:20]:
    print("  ", loc)
if prova:
    sys.exit(0)

body = json.dumps({"host": HOST, "key": KEY, "keyLocation": f"https://{HOST}/{KEY}.txt",
                   "urlList": da_inviare}).encode()
req = urllib.request.Request("https://api.indexnow.org/indexnow", data=body,
                             headers={"Content-Type": "application/json; charset=utf-8"})
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        codice = r.status
except urllib.error.HTTPError as e:
    codice = e.code
print(f"IndexNow: risposta {codice}")

# 200 = ricevuto, 202 = ricevuto, chiave in verifica. Altro (400/403/422/429) = non salvare lo stato,
# cosi' al prossimo giro gli stessi URL vengono ritentati.
if codice in (200, 202):
    for loc in da_inviare:
        stato[loc] = urls[loc]
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    json.dump(stato, open(STATE, "w"), indent=1)
else:
    sys.exit(1)
