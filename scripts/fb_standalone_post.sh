#!/bin/bash
# Pubblica UN post Facebook standalone (senza link al sito) preso dalla coda
# scripts/fb_posts_queue.json. Eseguito da cron due volte al giorno (13:30 e 19:30),
# in aggiunta al post con link dell'articolo del mattino (daily_publish_vps.sh).
#
# La coda sta in git; lo stato di cosa e' gia' uscito NO, altrimenti ogni
# pubblicazione sporcherebbe il working tree e il git pull del cron delle 09:05.
set -uo pipefail

# Il cron ha un PATH minimale: node serve a openclaw
export PATH="/home/salvatore/.npm-global/bin:/home/salvatore/.local/bin:/usr/local/bin:/usr/bin:/bin"

# --prova: fa tutto (coda, immagine, messaggio) tranne pubblicare davvero
PROVA=0
[ "${1:-}" = "--prova" ] && PROVA=1

REPO="/home/salvatore/risparmio-energetico"
QUEUE="$REPO/scripts/fb_posts_queue.json"
STATE="/home/salvatore/output/fb_standalone_state.json"
PAGE_ID="101206045148755"
BASE_IMG="https://guida-energia.com/immagini"
OPENCLAW="/home/salvatore/.npm-global/bin/openclaw"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

[ -f "$QUEUE" ] || { log "ERRORE: coda non trovata in $QUEUE"; exit 1; }
mkdir -p "$(dirname "$STATE")"
[ -f "$STATE" ] || echo '{"pubblicati": []}' > "$STATE"

# --- sceglie il prossimo post non ancora pubblicato ---
NEXT="$(python3 - "$QUEUE" "$STATE" <<'PY'
import json, sys
queue = json.load(open(sys.argv[1]))["posts"]
fatti = {p["id"] for p in json.load(open(sys.argv[2]))["pubblicati"]}
restanti = [p for p in queue if p["id"] not in fatti]
if not restanti:
    print("__CODA_VUOTA__")
    sys.exit(0)
p = restanti[0]
print(json.dumps({"id": p["id"], "tema": p["tema"], "immagine": p["immagine"],
                  "testo": p["testo"], "restanti": len(restanti)}, ensure_ascii=False))
PY
)"

if [ "$NEXT" = "__CODA_VUOTA__" ]; then
  log "CODA ESAURITA: nessun post da pubblicare. Va rifornito $QUEUE."
  exit 0
fi

POST_ID="$(echo "$NEXT"  | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')"
TEMA="$(echo "$NEXT"     | python3 -c 'import json,sys; print(json.load(sys.stdin)["tema"])')"
IMG="$(echo "$NEXT"      | python3 -c 'import json,sys; print(json.load(sys.stdin)["immagine"])')"
RESTANTI="$(echo "$NEXT" | python3 -c 'import json,sys; print(json.load(sys.stdin)["restanti"])')"
echo "$NEXT" | python3 -c 'import json,sys; sys.stdout.write(json.load(sys.stdin)["testo"])' > /tmp/fb_caption_$$.txt

IMG_URL="$BASE_IMG/$IMG.jpg"
log "post #$POST_ID ($TEMA) - immagine $IMG - restanti in coda dopo questo: $((RESTANTI-1))"

# --- l'immagine deve essere raggiungibile, altrimenti Facebook rifiuta il post ---
HTTP="$(curl -s -o /dev/null -w '%{http_code}' -m 20 "$IMG_URL")"
if [ "$HTTP" != "200" ]; then
  log "ERRORE: immagine non raggiungibile ($HTTP) $IMG_URL - post NON pubblicato, riprovo al prossimo slot"
  rm -f /tmp/fb_caption_$$.txt
  exit 1
fi

log "immagine raggiungibile (HTTP 200)"

if [ "$PROVA" = "1" ]; then
  log "MODALITA' PROVA: non pubblico. Testo che sarebbe uscito:"
  echo "----------------------------------------"
  cat /tmp/fb_caption_$$.txt
  echo "----------------------------------------"
  log "immagine: $IMG_URL"
  log "lo stato NON e' stato modificato: il post #$POST_ID resta il prossimo in coda"
  rm -f /tmp/fb_caption_$$.txt
  exit 0
fi

# --- pubblicazione ---
CAP="$(cat /tmp/fb_caption_$$.txt)"
OUT="$($OPENCLAW agent --agent main --json --timeout 240 --message "Pubblica ORA un post con foto sulla pagina Facebook Guida Energia Italia.

Usa il tool FACEBOOK_CREATE_PHOTO_POST con questi parametri esatti:
- page_id: $PAGE_ID
- image url: $IMG_URL
- caption: il testo qui sotto, copiato IDENTICO senza aggiungere o togliere nulla, emoji e a capo compresi.

Non aggiungere link, non accorciare, non riscrivere, non chiedere conferma. Pubblicalo subito (published=true) e rispondi con l'ID del post.

--- INIZIO TESTO ---
$CAP
--- FINE TESTO ---" 2>&1)"
rm -f /tmp/fb_caption_$$.txt

FB_ID="$(echo "$OUT" | grep -oE "${PAGE_ID}_[0-9]+" | head -1)"

if [ -z "$FB_ID" ]; then
  log "ERRORE: nessun ID post restituito, il post #$POST_ID resta in coda e verra' ritentato"
  echo "$OUT" | tail -c 800
  exit 1
fi

log "pubblicato: $FB_ID  https://www.facebook.com/$PAGE_ID/posts/${FB_ID#*_}"

# --- segna come fatto PRIMA della verifica: un doppione e' peggio di un post perso ---
python3 - "$STATE" "$POST_ID" "$TEMA" "$FB_ID" <<'PY'
import json, sys, datetime
path, pid, tema, fbid = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
d = json.load(open(path))
d["pubblicati"].append({"id": pid, "tema": tema, "fb_post_id": fbid,
                        "quando": datetime.datetime.now().isoformat(timespec="seconds")})
json.dump(d, open(path, "w"), ensure_ascii=False, indent=2)
PY

# --- verifica indipendente: il sub-agente dichiara successo anche quando fallisce ---
VER="$($OPENCLAW agent --agent main --json --timeout 180 --message "Usa il tool FACEBOOK_GET_PAGE_POSTS sulla pagina page_id $PAGE_ID e rispondi SOLO con l'id del post piu' recente, nient'altro. Non inventare: riporta quello che restituisce il tool." 2>&1)"
ULTIMO="$(echo "$VER" | grep -oE "${PAGE_ID}_[0-9]+" | head -1)"
if [ "$ULTIMO" = "$FB_ID" ]; then
  log "verifica OK: il post piu' recente sulla pagina e' $FB_ID"
else
  log "ATTENZIONE: verifica non confermata (atteso $FB_ID, pagina riporta '${ULTIMO:-nulla}'). Controllare a mano."
fi

if [ "$((RESTANTI-1))" -le 6 ]; then
  log "AVVISO: restano solo $((RESTANTI-1)) post in coda (meno di 3 giorni). Rifornire $QUEUE."
fi
