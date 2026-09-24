---
title: "Fotovoltaico con accumulo e pompa di calore: come abbinarli per il massimo risparmio (2026)"
slug: "fotovoltaico-accumulo-pompa-di-calore"
date: 2026-09-24T09:00:00+02:00
draft: false
description: "Come far lavorare insieme fotovoltaico, batteria di accumulo e pompa di calore nel 2026: strategie di coordinamento, dispositivi di gestione carichi e quanto si risparmia davvero rispetto a due impianti scollegati."
categories: ["fotovoltaico"]
tags: ["fotovoltaico", "accumulo fotovoltaico", "pompa di calore", "autoconsumo", "risparmio energetico"]
cover:
  image: "/immagini/fotovoltaico-accumulo-pompa-di-calore.jpg"
  alt: "Pannelli fotovoltaici sul tetto di una casa con pompa di calore installata a parete."
---

### Introduzione

Avere sia un impianto fotovoltaico con accumulo sia una pompa di calore non basta: se i due sistemi lavorano ognuno per conto proprio, senza essere coordinati, si rischia di produrre energia pulita di giorno e di farla scaldare l'acqua o gli ambienti di notte comprandola dalla rete al prezzo pieno. Per una famiglia che ha già entrambi gli impianti, far "dialogare" fotovoltaico e pompa di calore con una centralina di gestione carichi o un semplice automatismo può valere circa 250-300 euro l'anno in più di risparmio, con un investimento aggiuntivo che si ripaga in meno di un anno.

<div class="cta-box">
  <a href="https://www.amazon.it/s?k=centralina+gestione+carichi+fotovoltaico&tag=audiobookit-21" target="_blank" rel="nofollow sponsored" class="cta-button">🔍 Confronta le centraline di gestione carichi su Amazon</a>
</div>

### Cos'è e come funziona

Il fotovoltaico produce energia quando c'è sole, tipicamente tra le 9 e le 17. La pompa di calore, invece, spesso si accende quando serve davvero: al mattino presto per portare in temperatura la casa, o la sera per l'acqua calda sanitaria, cioè proprio nelle ore in cui i pannelli non producono o producono poco. Senza un coordinamento, il risultato è che l'impianto fotovoltaico vende alla rete (a 7-8 centesimi al kWh) l'energia che la pompa di calore poi ricompra dalla rete (a 25-30 centesimi al kWh): un doppio svantaggio economico.

Le due leve per evitarlo sono:

1. **La batteria di accumulo**, che sposta l'energia prodotta di giorno verso la sera, coprendo la parte di fabbisogno della pompa di calore che cade fuori dalle ore di sole.
2. **Lo spostamento intelligente dei carichi**: far lavorare la pompa di calore proprio nelle ore centrali della giornata, sfruttando l'inerzia termica dell'edificio (o dell'accumulo termico, se presente) per "immagazzinare" calore quando il sole c'è, invece di produrlo quando manca. Questo si fa con termostati programmabili, centraline dedicate al fotovoltaico o, nei sistemi più moderni, con la comunicazione diretta tra inverter fotovoltaico e pompa di calore (alcuni produttori, come Daikin e Vaillant, offrono già kit di integrazione con determinati inverter).

Il vantaggio pratico riguarda soprattutto la stagione di riscaldamento: una pompa di calore accesa 3-4 ore al mattino e 3-4 ore nel primo pomeriggio, invece che concentrata la sera, aumenta di molto la quota di energia solare autoconsumata direttamente, riducendo il peso sulla batteria e sulla rete. Per approfondire il dimensionamento dell'impianto fotovoltaico e della batteria in sé, vedi la guida all'[impianto fotovoltaico con accumulo](/fotovoltaico/impianto-fotovoltaico-con-accumulo/) e il confronto tra i moduli batteria in [batteria di accumulo fotovoltaico](/fotovoltaico/batteria-accumulo-fotovoltaico/).

### I migliori dispositivi per coordinare fotovoltaico e pompa di calore

Non serve sempre sostituire l'impianto: spesso basta aggiungere un dispositivo di monitoraggio o controllo carichi tra il contatore, l'inverter e la pompa di calore.

| Dispositivo | Funzione | Prezzo indicativo | Pro | Contro | Link |
|---|---|---|---|---|---|
| [Shelly EM + 1 pinza amperometrica](https://www.shelly.com/it/pages/smart-energy-meter) | Monitora produzione fotovoltaico e consumo in tempo reale via app | €40-50 | Economico, facile da installare, dati precisi | Solo monitoraggio, non aziona da solo la pompa di calore | [Amazon](https://www.amazon.it/Shelly-Amperometrica-misurazione-consumo-elettrico/dp/B0BL7VC2H7?tag=audiobookit-21) |
| [Shelly Pro EM-50](https://www.shelly.com/it/pages/smart-energy-meter) | Misura 2 canali (rete + fotovoltaico) e pilota un contattore per attivare carichi in surplus | €90-100 | Può accendere automaticamente un carico quando c'è surplus solare, integrabile con Home Assistant | Richiede installazione su guida DIN, va abbinato a un contattore per la pompa di calore | [Amazon](https://www.amazon.it/Shelly-Contatore-Contattori-Misurazione-Compatibile/dp/B0CH1JW2CW?tag=audiobookit-21) |
| [Vemer Solar-3 VE474300](https://www.vemer.it/) | Centralina dedicata: misura il surplus immesso in rete e attiva fino a 3 carichi non prioritari in base a soglie programmate | €180-210 | Pensata specificamente per massimizzare l'autoconsumo fotovoltaico, fino a 60A, made in Italy | Prezzo più alto, va installata da un elettricista nel quadro | [Amazon](https://www.amazon.it/Vemer-VE474300-Centralina-Controllo-Fotovoltaici/dp/B00SKTNRSK?tag=audiobookit-21) |

*Prezzi indicativi settembre 2026, solo dispositivo, IVA inclusa; l'installazione (mezza giornata di elettricista) va aggiunta a parte, in genere 100-200 euro.*

### Quanto si risparmia davvero

Ipotesi: famiglia che ha già un impianto fotovoltaico da 6 kW con batteria da 10 kWh (produzione stimata 7.800 kWh/anno) e una pompa di calore per il riscaldamento, con un fabbisogno elettrico complessivo di 5.500 kWh/anno (2.500 kWh di utenze domestiche + 3.000 kWh per il riscaldamento con pompa di calore, COP medio stagionale 3). Prezzo energia da rete €0,28/kWh, prezzo di vendita del surplus in Ritiro Dedicato €0,08/kWh.

**Caso A — impianti non coordinati** (la pompa di calore si accende quando serve, senza tenere conto della produzione solare, la batteria copre solo la sera)
- Autoconsumo stimato: 60% del fabbisogno, circa 3.300 kWh
- Energia acquistata dalla rete: 2.200 kWh × €0,28 = **€616/anno**
- Surplus venduto: 4.500 kWh × €0,08 = **€360/anno**
- Costo netto energia: 616 - 360 = **€256/anno**

**Caso B — impianti coordinati** (pompa di calore programmata nelle ore centrali della giornata quando c'è produzione, batteria dimensionata sul resto del fabbisogno serale)
- Autoconsumo stimato: 85% del fabbisogno, circa 4.675 kWh
- Energia acquistata dalla rete: 825 kWh × €0,28 = **€231/anno**
- Surplus venduto: 3.125 kWh × €0,08 = **€250/anno**
- Costo netto energia: 231 - 250 = **-€19/anno** (bolletta azzerata con un piccolo guadagno)

**Risparmio aggiuntivo dal solo coordinamento: circa 275 euro l'anno**, a fronte di un investimento in centralina di gestione carichi + installazione di circa 200-300 euro: il tempo di rientro è di **meno di un anno**, senza contare che una centralina come la Vemer Solar-3 o uno Shelly Pro EM restano utili anche per coordinare altri carichi (colonnina auto elettrica, lavatrice, scaldabagno).

### Incentivi disponibili 2026

**Bonus Ristrutturazioni:** copre fotovoltaico e batteria di accumulo con detrazione del 50% per l'abitazione principale (36% per le altre unità), tetto di spesa 96.000 euro per unità immobiliare, recuperata in 10 rate annuali; dal 2027 l'aliquota scende al 30%.

**Conto Termico 3.0:** copre la pompa di calore con un contributo diretto dal GSE fino al 65% della spesa ammissibile (calcolata su un massimale di 700 euro/kW), erogato in tempi più rapidi rispetto alla detrazione fiscale. Per il confronto dettagliato tra Ecobonus e Conto Termico vedi la [guida agli incentivi pompe di calore 2026](/incentivi/incentivi-pompe-di-calore-2026/).

I dispositivi di gestione carichi (Shelly, Vemer e simili) non sono di norma una voce a sé negli incentivi: se acquistati e fatturati insieme all'impianto fotovoltaico o alla pompa di calore possono rientrare nella spesa complessiva agevolata, ma va verificato caso per caso con l'installatore in fase di preventivo, perché la prassi varia.

### Conclusione

Chi ha già investito in fotovoltaico con accumulo e in una pompa di calore sta lasciando sul tavolo qualche centinaio di euro l'anno se i due impianti non "si parlano": il modo più economico per recuperarli non è comprare più pannelli o una batteria più grande, ma aggiungere un dispositivo di gestione carichi da 100-200 euro e riprogrammare gli orari di accensione della pompa di calore sulle ore di sole. Chi sta ancora scegliendo taglia e configurazione dell'impianto fotovoltaico può partire dalla guida [impianto fotovoltaico con accumulo](/fotovoltaico/impianto-fotovoltaico-con-accumulo/); chi valuta ancora quale pompa di calore installare può confrontare prezzi e modelli in [pompa di calore prezzi 2026](/riscaldamento/pompa-di-calore-prezzi/) o, se ha già i termosifoni, nella guida [pompa di calore per termosifoni](/riscaldamento/pompa-di-calore-per-termosifoni/).

*Fonti: [GSE - Gestore Servizi Energetici, Conto Termico](https://www.gse.it/servizi-per-te/efficienza-energetica/conto-termico), [Agenzia delle Entrate - Bonus Ristrutturazioni](https://www.agenziaentrate.gov.it), [ARERA - prezzi tutela energia elettrica](https://www.arera.it)*
