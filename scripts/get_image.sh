#!/bin/bash
KEYWORD="${1:-news}"
SLUG="${2:-articolo}"

cd /home/salvatore/risparmio-energetico || exit 1

PIXABAY_KEY=$(grep PIXABAY_API_KEY .env | cut -d= -f2)
RESPONSE=$(wget -qO- "https://pixabay.com/api/?key=$PIXABAY_KEY&q=$KEYWORD&image_type=photo&orientation=horizontal&per_page=10&page=$((RANDOM % 3 + 1))" 2>/dev/null)
URL=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['hits'][0]['largeImageURL'] if d.get('hits') else '')" 2>/dev/null)

if [ -z "$URL" ]; then
  URL="https://picsum.photos/seed/$SLUG/1280/720"
fi

mkdir -p static/immagini
wget -q -O "static/immagini/$SLUG.jpg" "$URL" && echo "✅ static/immagini/$SLUG.jpg" || echo "❌ download fallito"
