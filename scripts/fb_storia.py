#!/usr/bin/env python3
"""Ripubblica un video (reel/meme animato) come STORIA della pagina Facebook Guida Energia Italia.

Uso: fb_storia.py URL_VIDEO_MP4 [--prova]

Composio non ha un tool per le storie: si passa dal suo sandbox (COMPOSIO_REMOTE_WORKBENCH),
dove si ricava il token della pagina e si chiamano direttamente le API /video_stories.
Il token resta nel sandbox e non viene mai stampato qui.
Il video va inviato come byte: col parametro file_url il robot di Facebook prende 403 da Cloudflare.
Esce con codice 0 solo se la storia risulta "published" nell'elenco storie della pagina.
"""
import json
import subprocess
import sys

PAGE_ID = "101206045148755"
COMPOSIO = "/home/salvatore/assistente-pagine/composio.mjs"

CODICE = r'''
import requests, time, json
PAGE = "%(page)s"
URL = "%(url)s"
G = "https://graph.facebook.com/v21.0"
r, _ = proxy_execute("GET", "/me/accounts", "facebook", query_params={"fields": "id,access_token"})
tok = [p["access_token"] for p in r["data"] if p["id"] == PAGE][0]
esito = {}
b = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=60).content
esito["byte"] = len(b)
if %(prova)s:
    esito["prova"] = True
else:
    s = requests.post(f"{G}/{PAGE}/video_stories", data={"upload_phase": "start", "access_token": tok}).json()
    vid = s.get("video_id")
    esito["video_id"] = vid
    if vid:
        u = requests.post(s["upload_url"], headers={"Authorization": f"OAuth {tok}", "offset": "0",
                                                    "file_size": str(len(b))}, data=b).json()
        esito["upload"] = u.get("success", u)
        f = requests.post(f"{G}/{PAGE}/video_stories",
                          data={"upload_phase": "finish", "video_id": vid, "access_token": tok}).json()
        esito["finish"] = f.get("success", f)
        for _ in range(8):
            time.sleep(15)
            st = requests.get(f"{G}/{PAGE}/stories", params={"access_token": tok}).json().get("data", [])
            m = [x for x in st if x.get("media_id") == vid]
            if m and m[0].get("status") == "published":
                esito["pubblicata"] = m[0].get("url", "")
                break
    else:
        esito["errore_start"] = s
print("ESITO_STORIA " + json.dumps(esito))
'''


def main():
    args = [a for a in sys.argv[1:] if a != "--prova"]
    prova = "--prova" in sys.argv
    if len(args) != 1:
        sys.exit("uso: fb_storia.py URL_VIDEO_MP4 [--prova]")
    codice = CODICE % {"page": PAGE_ID, "url": args[0], "prova": prova}
    out = subprocess.run(["node", COMPOSIO, "call", "COMPOSIO_REMOTE_WORKBENCH",
                          json.dumps({"code_to_execute": codice, "thought": "storia facebook da video"})],
                         capture_output=True, text=True, timeout=420).stdout
    try:
        stdout = json.loads(out[out.index("{"):])["data"]["stdout"]
        esito = json.loads(stdout.split("ESITO_STORIA ", 1)[1].splitlines()[0])
    except Exception:
        print("ERRORE: risposta del sandbox non leggibile: " + out[-600:].replace("EAA", "[tok]"))
        sys.exit(1)
    print(json.dumps(esito, ensure_ascii=False))
    sys.exit(0 if (prova and esito.get("byte")) or esito.get("pubblicata") else 1)


if __name__ == "__main__":
    main()
