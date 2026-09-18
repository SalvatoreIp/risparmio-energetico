#!/bin/bash
# Pubblicazione automatica giornaliera - eseguito da cron su questa VPS.
# Sostituisce la routine cloud (bloccata: Claude GitHub App in sola lettura sul repo).
set -uo pipefail

cd /home/salvatore/risparmio-energetico || exit 1

git pull --ff-only origin main

PROMPT="$(cat scripts/daily_publish_prompt.txt)"

/home/salvatore/.local/bin/claude -p "$PROMPT" \
  --model claude-sonnet-5 \
  --allowedTools "Bash Read Write Edit Glob Grep WebSearch" \
  --permission-mode bypassPermissions
