#!/bin/bash
TITLE="$1"
BODY="$2"
SECTION="${3:-attualita}"
IMAGE_PATH="${4:-}"
DESCRIPTION="${5:-}"
TAGS="${6:-}"

cd /home/salvatore/risparmio-energetico || exit 1

case "$SECTION" in
  "fotovoltaico"|"riscaldamento"|"illuminazione"|"smart-home"|"incentivi"|"guide") ;;
  *) SECTION="guide" ;;
esac

SLUG=$(echo "$TITLE" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | sed 's/[^a-z0-9-]//g;s/--*/-/g')
DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
DATEONLY=$(date -u +"%Y-%m-%d")
HOUR=$(date -u +"%H")
FILE="content/$SECTION/$DATEONLY-$SLUG.md"

mkdir -p static/immagini
mkdir -p "content/$SECTION"

if [ -n "$IMAGE_PATH" ] && [ -f "$IMAGE_PATH" ]; then
  cp "$IMAGE_PATH" "static/immagini/$SLUG.jpg"
fi

BODY_REAL=$(printf '%b' "$BODY")

cat > "$FILE" << MD
---
title: "$TITLE"
date: $DATE
draft: false
description: "$DESCRIPTION"
categories: ["$SECTION"]
tags: [$TAGS]
cover:
  image: /immagini/$SLUG.jpg
  alt: "Immagine per $TITLE"
---

$BODY_REAL
MD

chmod 644 "$FILE"
chown salvatore:salvatore "$FILE"

CHARS=$(wc -m < "$FILE")
echo "✅ $FILE creato! ($CHARS caratteri)"
echo "📋 description: $DESCRIPTION"
echo "🏷️  tags: $TAGS"
echo "🔥 Prossimo: git add . && git commit -m '$TITLE' && git push"

# Git push automatico
git add "$FILE"
git commit -m "📝 $TITLE"
git push origin main
echo "🚀 Pubblicato su Cloudflare!"
