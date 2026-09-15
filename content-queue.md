# Coda argomenti per pubblicazione automatica

Uso interno per la routine di pubblicazione giornaliera (non è un articolo, non va pubblicato come pagina). Ogni riga è un gap di keyword verificato con dati reali (volume di ricerca mensile Italia, difficoltà SEO) tramite DataForSEO/OpenSEO il 2026-09-15. Quando un argomento viene pubblicato, la routine deve rimuoverlo da questa lista e committarla insieme all'articolo.

Formato: `- [ ] Titolo proposto | sezione | keyword target (volume/mese, difficoltà) | note`

## Da pubblicare

- [ ] Tesla Powerwall 3: prezzo, scheda tecnica e vale la pena nel 2026? | fotovoltaico | tesla powerwall 3 prezzo (1.000/mese, bassa) + tesla powerwall 3 scheda tecnica (210/mese) + tesla powerwall 2 prezzo (210/mese) | Spoke dedicato al brand, diverso da batteria-accumulo-fotovoltaico (comparativo generico). Collega a /fotovoltaico/batteria-accumulo-fotovoltaico/ e /fotovoltaico/impianto-fotovoltaico-con-accumulo/. Verificare prezzo Powerwall 3 aggiornato via web search (non fidarsi di questa nota, i prezzi salgono/scendono).
- [ ] Fotovoltaico con accumulo: pro e contro, conviene davvero nel 2026? | fotovoltaico | fotovoltaico con accumulo pro e contro (960/mese combinando varianti, bassa) | Articolo di decisione (top of funnel), diverso dagli articoli di prezzo già pubblicati. Collega a /fotovoltaico/impianto-fotovoltaico-con-accumulo/ e /fotovoltaico/batteria-accumulo-fotovoltaico/ per chi decide di procedere.
- [ ] Come calcolare se conviene il fotovoltaico: la formula e un esempio reale | fotovoltaico | come calcolare se conviene il fotovoltaico (260/mese, bassa) | Guida pratica con formula di calcolo autoconsumo/payback, esempio numerico reale. Collega agli articoli prezzi/accumulo esistenti.
- [ ] Fotovoltaico con accumulo e pompa di calore: come abbinarli per il massimo risparmio | fotovoltaico o riscaldamento | fotovoltaico con accumulo e pompa di calore (260/mese, bassa) | Articolo "crossover" che collega il cluster fotovoltaico e il cluster pompe di calore già esistenti - ottimo per internal linking, valuta bene in quale sezione metterlo per non creare confusione di categoria.
- [ ] Fotovoltaico senza immissione in rete: cos'è e quando conviene | fotovoltaico | schema impianto fotovoltaico senza immissione in rete (260/mese, bassa) | Argomento più tecnico/di nicchia (impianti a zero immissione). Verificare che ci sia domanda reale sufficiente prima di scrivere, è il più debole della lista.

## Quando la coda è vuota

Non c'è accesso a OpenSEO/DataForSEO dall'agente cloud (nessun connettore MCP disponibile in quell'ambiente), quindi non è possibile rifare una ricerca keyword con dati di volume reali in automatico. Quando questa lista è vuota:

1. Leggi `hugo.toml` (`[params].mainSections`) e i titoli in `content/*/` per capire quali sezioni sono più scarne o quali argomenti mancano.
2. Usa WebSearch per validare 2-3 idee plausibili (query tipo "domande frequenti [argomento] risparmio energetico 2026", "cosa cercano gli italiani su [argomento]") — non avrai dati di volume/difficoltà precisi, quindi preferisci argomenti con intento commerciale chiaro (prezzo, incentivi, confronto modelli) rispetto a quelli puramente informativi.
3. Scegli l'argomento più solido, scrivilo, e NON aggiungerlo a questa coda (pubblica direttamente).
4. Segnala nel messaggio di commit che la coda era vuota e la scelta è stata fatta senza dati di volume verificati, cosicché in una prossima sessione locale (con accesso OpenSEO) si possa rifare il rifornimento della coda con dati reali.
