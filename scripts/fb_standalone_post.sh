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
BASE_VIDEO="https://guida-energia.com/video"
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
print(json.dumps({"id": p["id"], "tema": p["tema"], "immagine": p.get("immagine", ""),
                  "video": p.get("video", ""), "testo": p["testo"],
                  "link_commento": p.get("link_commento", ""),
                  "restanti": len(restanti)}, ensure_ascii=False))
PY
)"

if [ "$NEXT" = "__CODA_VUOTA__" ]; then
  log "CODA ESAURITA: nessun post da pubblicare. Va rifornito $QUEUE."
  exit 0
fi

POST_ID="$(echo "$NEXT"  | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')"
TEMA="$(echo "$NEXT"     | python3 -c 'import json,sys; print(json.load(sys.stdin)["tema"])')"
IMG="$(echo "$NEXT"      | python3 -c 'import json,sys; print(json.load(sys.stdin)["immagine"])')"
VIDEO="$(echo "$NEXT"    | python3 -c 'import json,sys; print(json.load(sys.stdin)["video"])')"
RESTANTI="$(echo "$NEXT" | python3 -c 'import json,sys; print(json.load(sys.stdin)["restanti"])')"
LINK_COMMENTO="$(echo "$NEXT" | python3 -c 'import json,sys; print(json.load(sys.stdin)["link_commento"])')"
echo "$NEXT" | python3 -c 'import json,sys; sys.stdout.write(json.load(sys.stdin)["testo"])' > /tmp/fb_caption_$$.txt

# Un post con "video" (slug di static/video/<slug>.mp4) esce come video, altrimenti come foto
if [ -n "$VIDEO" ]; then
  TIPO="video"
  MEDIA_URL="$BASE_VIDEO/$VIDEO.mp4"
else
  TIPO="immagine"
  MEDIA_URL="$BASE_IMG/$IMG.jpg"
fi
log "post #$POST_ID ($TEMA) - $TIPO $MEDIA_URL - restanti in coda dopo questo: $((RESTANTI-1))"

# --- il file deve essere raggiungibile, altrimenti Facebook rifiuta il post ---
HTTP="$(curl -s -o /dev/null -w '%{http_code}' -m 20 "$MEDIA_URL")"
if [ "$HTTP" != "200" ]; then
  log "ERRORE: $TIPO non raggiungibile ($HTTP) $MEDIA_URL - post NON pubblicato, riprovo al prossimo slot"
  rm -f /tmp/fb_caption_$$.txt
  exit 1
fi

log "$TIPO raggiungibile (HTTP 200)"

if [ "$PROVA" = "1" ]; then
  log "MODALITA' PROVA: non pubblico. Testo che sarebbe uscito:"
  echo "----------------------------------------"
  cat /tmp/fb_caption_$$.txt
  echo "----------------------------------------"
  log "$TIPO: $MEDIA_URL"
  log "lo stato NON e' stato modificato: il post #$POST_ID resta il prossimo in coda"
  rm -f /tmp/fb_caption_$$.txt
  exit 0
fi

# --- pubblicazione ---
CAP="$(cat /tmp/fb_caption_$$.txt)"
if [ "$TIPO" = "video" ]; then
  ISTRUZIONI="Pubblica ORA un post con video sulla pagina Facebook Guida Energia Italia.

Usa il tool FACEBOOK_CREATE_VIDEO_POST con questi parametri esatti:
- page_id: $PAGE_ID
- file_url: $MEDIA_URL
- description: il testo qui sotto, copiato IDENTICO senza aggiungere o togliere nulla, emoji e a capo compresi.

Non usare il parametro video, non aggiungere title, link o targeting. Se la risposta contiene unsuccessful=true consideralo un errore e NON riprovare (si creerebbero doppioni)."
else
  ISTRUZIONI="Pubblica ORA un post con foto sulla pagina Facebook Guida Energia Italia.

Usa il tool FACEBOOK_CREATE_PHOTO_POST con questi parametri esatti:
- page_id: $PAGE_ID
- image url: $MEDIA_URL
- caption: il testo qui sotto, copiato IDENTICO senza aggiungere o togliere nulla, emoji e a capo compresi."
fi
OUT="$($OPENCLAW agent --agent main --json --timeout 240 --message "$ISTRUZIONI

Non aggiungere link, non accorciare, non riscrivere, non chiedere conferma. Pubblicalo subito (published=true) e rispondi con l'ID del post.

--- INIZIO TESTO ---
$CAP
--- FINE TESTO ---" 2>&1)"
rm -f /tmp/fb_caption_$$.txt

FB_ID="$(echo "$OUT" | grep -oE "${PAGE_ID}_[0-9]+" | head -1)"
# FACEBOOK_CREATE_VIDEO_POST restituisce solo l'id del video (15-20 cifre, senza "PAGEID_"):
# senza questo il 25/09 il reel era uscito ma lo script l'ha creduto fallito e l'ha ritentato
if [ -z "$FB_ID" ] && [ -n "$VIDEO" ]; then
  FB_ID="$(echo "$OUT" | grep -oE "\b[0-9]{15,20}\b" | grep -v "^${PAGE_ID}$" | head -1)"
fi

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

# Qui stava una "verifica indipendente" via FACEBOOK_GET_PAGE_POSTS, rimossa il 2026-09-22:
# quella lettura richiede lo scope OAuth 'pages_read_engagement' che la connessione Composio
# non ha, quindi non poteva funzionare. Falliva in silenzio e l'agente rispondeva con l'ID che
# aveva appena visto nel proprio contesto, producendo un "verifica OK" che confermava il nulla.
log "NOTA: l'ID sopra e' quello dichiarato dall'agente; non e' verificabile via API finche' manca lo scope pages_read_engagement"

# --- primo commento con il link all'articolo (solo se il post ne ha uno) ---
# Il link sta nel commento e non nel post perche' Facebook fa girare meno i post con link.
# Un errore qui non tocca il post, che e' gia' uscito.
if [ -n "$LINK_COMMENTO" ]; then
  if [ "$(curl -s -o /dev/null -w '%{http_code}' -m 20 "$LINK_COMMENTO")" = "200" ]; then
    COUT="$($OPENCLAW agent --agent main --json --timeout 240 --message "Esegui UNA sola volta il tool FACEBOOK_CREATE_COMMENT con object_id \"$FB_ID\" e message esattamente questo testo, a capo compreso:
📖 Se vuoi approfondire, qui trovi la guida completa con tutti i conti:
$LINK_COMMENTO
Non usare altri tool e non riprovare se fallisce. Rispondi con l'id del commento restituito dal tool oppure con l'errore esatto." 2>&1)"
    C_ID="$(echo "$COUT" | grep -oE '"id\\?"?: *\\?"[0-9]+_[0-9]+' | grep -oE '[0-9]+_[0-9]+' | head -1)"
    [ -z "$C_ID" ] && C_ID="$(echo "$COUT" | grep -oE '\b[0-9]{9,20}_[0-9]{9,20}\b' | grep -v "^$FB_ID$" | head -1)"
    if [ -n "$C_ID" ]; then log "primo commento con link pubblicato: $C_ID ($LINK_COMMENTO)"
    else log "ATTENZIONE: primo commento NON confermato ($LINK_COMMENTO)"; echo "$COUT" | tail -c 400; fi
  else
    log "ATTENZIONE: link del commento non raggiungibile, commento saltato: $LINK_COMMENTO"
  fi
fi

if [ "$((RESTANTI-1))" -le 6 ]; then
  log "AVVISO: restano solo $((RESTANTI-1)) post in coda (meno di 3 giorni). Rifornire $QUEUE."
fi
