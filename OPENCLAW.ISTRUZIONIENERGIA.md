# Istruzioni Operative — Sito Risparmio Energetico

## SEZIONI DISPONIBILI
- `fotovoltaico`  → pannelli solari, plug&play, accumulo batterie
- `smart-home`    → termostati smart, valvole termostatiche, prese intelligenti
- `riscaldamento` → pompe di calore, caldaie, confronti
- `illuminazione` → LED, soluzioni illuminazione efficiente
- `incentivi`     → ecobonus, bonus casa, detrazioni 2026
- `guide`         → come risparmiare in bolletta, guide pratiche

Cartelle reali:
- /home/salvatore/risparmio-energetico/content/fotovoltaico/
- /home/salvatore/risparmio-energetico/content/smart-home/
- /home/salvatore/risparmio-energetico/content/riscaldamento/
- /home/salvatore/risparmio-energetico/content/illuminazione/
- /home/salvatore/risparmio-energetico/content/incentivi/
- /home/salvatore/risparmio-energetico/content/guide/

## KEYWORD PRIORITA (attacca da qui in ordine)
1. "Pannello solare balcone senza installazione" → fotovoltaico
2. "Fotovoltaico plug and play come funziona"   → fotovoltaico
3. "Valvole termostatiche smart confronto"      → smart-home
4. "Presa smart misuratore consumo"             → smart-home
5. "Termostato smart wifi caldaia"              → smart-home
6. "Bonus efficienza energetica 2026"           → incentivi
7. "Miglior termostato smart 2026"              → smart-home
8. "Pannello solare balcone guida completa"     → fotovoltaico
9. "Pompa di calore prezzi 2026"                → riscaldamento
10. "Come risparmiare sulla bolletta"           → guide

## OBIETTIVO
Ogni esecuzione:
1. Scegli la prossima keyword dalla lista PRIORITA non ancora pubblicata
2. Ricerca dati aggiornati (prezzi reali, modelli 2026, normative)
3. Scarica immagine con Pixabay (keyword in INGLESE)
4. Scrivi articolo originale italiano 800-1200 parole
5. Includi SEMPRE tabella prodotti con link Amazon placeholder
6. Esegui scripts/publish_post.sh poi git push

## STRUTTURA ARTICOLO OBBLIGATORIA

### Introduzione
[Hook con risparmio concreto in euro/anno - 2-3 frasi]

### Cos'e e come funziona
[Spiegazione tecnica semplice - 150-200 parole]

### I migliori modelli del 2026
[Tabella markdown: Nome | Prezzo | Pro | Contro | Link]
[Link formato: [Nome Prodotto](https://www.amazon.it/dp/ASIN/?tag=audiobookit-21)]
[OpenClaw: cerca il prodotto su Amazon.it, trova l'ASIN nell'URL e costruisci il link]

### Quanto si risparmia davvero
[Calcolo concreto in euro - dati reali]

### Incentivi disponibili
[Bonus applicabili, percentuale, scadenza - max 100 parole]

### Conclusione
[Raccomandazione chiara - 2-3 frasi]

*Fonti: [nome testata](URL)*

## IMMAGINI - USA SEMPRE PIXABAY
PIXABAY_KEY=$(grep PIXABAY_API_KEY /home/salvatore/risparmio-energetico/.env | cut -d= -f2)
URL=$(wget -qO- "https://pixabay.com/api/?key=$PIXABAY_KEY&q=KEYWORD_INGLESE&image_type=photo&orientation=horizontal&per_page=3" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['hits'][0]['largeImageURL'])")
wget -O /home/salvatore/risparmio-energetico/static/immagini/SLUG.jpg "$URL"

Keyword per sezione:
- fotovoltaico   → "solar panel" oppure "solar energy"
- smart-home     → "smart thermostat" oppure "home automation"
- riscaldamento  → "heat pump" oppure "heating system"
- illuminazione  → "led light" oppure "energy saving lamp"
- incentivi      → "green energy" oppure "tax saving"
- guide          → "energy saving house" oppure "electricity bill"

## NAVIGAZIONE STEALTH
Se un sito blocca: ~/.openclaw/skills/stealth-browser/generate.sh URL
MAI Browser Relay (siamo su VPS)

## REGOLE ASSOLUTE
- MAI copiare testo originale da altre fonti
- Tono: esperto ma accessibile, focus sul risparmio concreto in euro
- Slug: solo minuscolo + trattini, niente apostrofi o accenti
- UNA sola categoria per articolo
- Virgolette doppie nel frontmatter, MAI apostrofi singoli
- MAI creare cartelle non elencate sopra
- SEMPRE almeno un calcolo concreto di risparmio in euro
- SEMPRE link Amazon con formato (https://amzn.to/PLACEHOLDER)
- Dati prezzi: indicare sempre "Prezzo indicativo aprile 2026"
- Dopo creazione file eseguire SEMPRE:
  cd /home/salvatore/risparmio-energetico && rm -rf public/ && hugo --minify && npx wrangler pages deploy public --project-name risparmio-energetico --commit-dirty=true && git add . && git commit -m "TITOLO" && git push
- MAI creare post di test, prova o placeholder

## FRONTMATTER OBBLIGATORIO
---
title: "Titolo SEO max 60 caratteri"
date: YYYY-MM-DDTHH:MM:SSZ
draft: false
description: "Riassunto 120-155 caratteri con keyword principale"
categories: ["<sezione>"]
tags: ["tag1", "tag2", "tag3"]
cover:
  image: "/immagini/slug.jpg"
  alt: "Descrizione immagine"
---
- IMPORTANTE: Inserire link Amazon SOLO per prodotti sotto €500 effettivamente venduti su Amazon.it. Per impianti costosi (pompe di calore, caldaie) linkare pagine informative o comparatori, NON inventare ASIN.
