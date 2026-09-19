#!/bin/bash
# Pubblicazione automatica giornaliera - eseguito da cron su questa VPS.
# Sostituisce la routine cloud (bloccata: Claude GitHub App in sola lettura sul repo).
set -uo pipefail

# Il cron ha un PATH minimale: node serve a openclaw
export PATH="/home/salvatore/.npm-global/bin:/home/salvatore/.local/bin:/usr/local/bin:/usr/bin:/bin"

cd /home/salvatore/risparmio-energetico || exit 1

git pull --ff-only origin main

BEFORE="$(git rev-parse HEAD)"

PROMPT="$(cat scripts/daily_publish_prompt.txt)"

/home/salvatore/.local/bin/claude -p "$PROMPT" \
  --model claude-sonnet-5 \
  --allowedTools "Bash Read Write Edit Glob Grep WebSearch" \
  --permission-mode bypassPermissions

# Post Facebook (solo se e' stato pubblicato un nuovo articolo)
AFTER="$(git rev-parse HEAD)"
if [ "$BEFORE" != "$AFTER" ]; then
  ARTICLE="$(git diff --name-only --diff-filter=A "$BEFORE" "$AFTER" -- 'content/*/*.md' | grep -v '_index.md' | head -1)"
  if [ -n "$ARTICLE" ]; then
    TITLE="$(grep -m1 '^title:' "$ARTICLE" | sed 's/^title: *"\(.*\)"$/\1/')"
    DESC="$(grep -m1 '^description:' "$ARTICLE" | sed 's/^description: *"\(.*\)"$/\1/')"
    SECTION="$(echo "$ARTICLE" | cut -d/ -f2)"
    SLUG="$(grep -m1 '^slug:' "$ARTICLE" | sed 's/^slug: *"\?\([^"]*\)"\?$/\1/')"
    [ -z "$SLUG" ] && SLUG="$(basename "$ARTICLE" .md | sed -E 's/^[0-9]{4}-[0-9]{2}-[0-9]{2}(-[0-9]{2})?-//')"
    URL="https://guida-energia.com/$SECTION/$SLUG/"
    echo "Post Facebook per: $TITLE ($URL)"
    /home/salvatore/.npm-global/bin/openclaw agent --agent main --json --timeout 240 \
      --message "Pubblica ORA sulla Pagina Facebook Guida Energia Italia (page_id 101206045148755) usando FACEBOOK_CREATE_POST un post in italiano, breve e accattivante, basato su questo articolo. Titolo: $TITLE. Descrizione: $DESC. Includi il link $URL come parametro link. Non chiedere conferma: pubblica direttamente e rispondi con l'ID del post." \
      | grep -o '"text": *"[^"]\{0,300\}' | tail -3
  fi
fi
