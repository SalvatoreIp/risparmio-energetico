---
title: "Calcolatore fotovoltaico: conviene per casa tua? Inserisci i tuoi consumi"
slug: "calcolatore-convenienza-fotovoltaico"
date: 2026-11-06T11:00:00+01:00
draft: false
description: "Calcolatore gratuito: inserisci consumi, prezzo della luce e zona e scopri quanti kW servono, quanto risparmi all'anno e in quanti anni rientri, con le detrazioni 2026."
categories: ["fotovoltaico"]
tags: ["fotovoltaico", "calcolo risparmio fotovoltaico", "tempo di rientro fotovoltaico", "simulatore fotovoltaico", "autoconsumo"]
cover:
  image: "/immagini/calcolatore-convenienza-fotovoltaico.jpg"
  alt: "Tavolo di legno con bolletta della luce, calcolatrice e quaderno, e dalla finestra un tetto in coppi con pannelli fotovoltaici"
---

### Introduzione

Per capire se il fotovoltaico conviene servono quattro numeri: quanti kWh consumi in un anno, quanto paghi ogni kWh, dove abiti e quanta energia riesci a usare mentre il sole produce. Questo calcolatore li mette insieme e ti dà tre risposte: quanti kW servono, quanto risparmi all'anno e in quanti anni l'impianto si ripaga, contando la detrazione 2026 che torna in 10 rate. Il consumo annuo lo trovi in bolletta, nella sezione "consumi degli ultimi 12 mesi". Tutti i conti avvengono sul tuo telefono: nessun dato viene inviato o salvato.

<div class="cta-box">
  <a href="https://www.amazon.it/s?k=misuratore+consumo+energia+elettrica+wifi&tag=audiobookit-21" target="_blank" rel="nofollow sponsored" class="cta-button">🔍 Confronta i misuratori di consumo elettrico su Amazon</a>
</div>

<div class="calc-fv" id="calc-fv">
<h3>Calcola la convenienza</h3>
<div class="riga"><label for="fv-consumo">Consumo annuo di luce (kWh)</label><input id="fv-consumo" type="number" inputmode="numeric" min="500" max="20000" step="100" value="2700"><small>In bolletta: "consumo annuo" o somma degli ultimi 12 mesi. Una famiglia di 3 persone consuma in media 2.500-3.000 kWh.</small></div>
<div class="riga"><label for="fv-prezzo">Quanto paghi ogni kWh, tutto compreso (€)</label><input id="fv-prezzo" type="number" inputmode="decimal" min="0.10" max="0.80" step="0.01" value="0.32"><small>Spesa totale dell'anno divisa per i kWh consumati. Valore indicativo novembre 2026: 0,30-0,35 €.</small></div>
<div class="riga"><label for="fv-zona">Dove abiti</label><select id="fv-zona"><option value="1150">Nord Italia</option><option value="1300" selected>Centro Italia</option><option value="1450">Sud e isole</option></select></div>
<div class="riga"><label for="fv-orient">Verso dove guarda il tetto</label><select id="fv-orient"><option value="1" selected>Sud, sud-est o sud-ovest</option><option value="0.85">Est o ovest</option></select></div>
<div class="riga"><label for="fv-presenza">Quanto consumate di giorno (8-18)</label><select id="fv-presenza"><option value="0.25">Poco: di giorno casa vuota</option><option value="0.35" selected>Un po': qualcuno a casa o lavatrice di giorno</option><option value="0.45">Tanto: smart working, pompa di calore, piano a induzione</option></select></div>
<div class="riga"><label for="fv-batteria">Batteria di accumulo</label><select id="fv-batteria"><option value="0" selected>No</option><option value="1">Sì</option></select></div>
<div class="riga"><label for="fv-aliquota">L'impianto va sulla tua prima casa?</label><select id="fv-aliquota"><option value="0.5" selected>Sì (detrazione 50% nel 2026)</option><option value="0.36">No, seconda casa (36%)</option><option value="0">Nessuna detrazione</option></select></div>
<div class="riga"><label for="fv-kw">Potenza dell'impianto (kW)</label><input id="fv-kw" type="number" inputmode="decimal" min="0" max="20" step="0.5" placeholder="lascia vuoto: la calcolo io"><small>Se hai già un preventivo, scrivi la potenza indicata.</small></div>
<div class="riga"><label for="fv-preventivo">Prezzo del tuo preventivo (€, facoltativo)</label><input id="fv-preventivo" type="number" inputmode="numeric" min="0" step="100" placeholder="lascia vuoto: uso un prezzo medio"></div>
<div class="esito" id="fv-esito" aria-live="polite">Attiva JavaScript per vedere il risultato.</div>
</div>

<script>
(function () {
  function n(id) { var v = parseFloat(String(document.getElementById(id).value).replace(",", ".")); return isNaN(v) ? 0 : v; }
  function f(x) { return String(Math.round(x)).replace(/\B(?=(\d{3})+(?!\d))/g, "."); }
  function d(x) { return String(x).replace(".", ","); }
  function e(x) { return f(x) + " €"; }
  function k(x) { return f(x) + " kWh"; }
  function calcola() {
    var consumo = n("fv-consumo"), prezzo = n("fv-prezzo"), batteria = n("fv-batteria") === 1;
    var out = document.getElementById("fv-esito");
    if (consumo < 300 || prezzo <= 0) { out.innerHTML = "Inserisci il consumo annuo e il prezzo del kWh."; return; }
    var prodKw = n("fv-zona") * n("fv-orient");
    var kw = n("fv-kw") > 0 ? n("fv-kw") : Math.max(2, Math.ceil(consumo / prodKw * 2) / 2);
    var prod = kw * prodKw;
    var battKwh = batteria ? Math.round(kw * 1.25 * 2) / 2 : 0;
    var quota = Math.min(n("fv-presenza") + (batteria ? 0.35 : 0), 0.8);
    var auto = Math.min(prod * quota, consumo * (batteria ? 0.85 : 0.6));
    var surplus = prod - auto;
    var rid = 0.10;
    var risp = auto * prezzo + surplus * rid;
    var costo = n("fv-preventivo") > 0 ? n("fv-preventivo") : 1500 + 1300 * kw + 800 * battKwh;
    var detr = costo * n("fv-aliquota");
    var cum = -costo, rientro = null;
    for (var a = 1; a <= 25; a++) {
      var r = risp * Math.pow(0.995, a - 1);
      if (a <= 10) r += detr / 10;
      if (a === 12) r -= 1200;
      cum += r;
      if (rientro === null && cum >= 0) rientro = a;
    }
    var cls, testo;
    if (rientro !== null && rientro <= 7) { cls = "si"; testo = "Conviene: rientri in circa " + rientro + " anni"; }
    else if (rientro !== null && rientro <= 11) { cls = "forse"; testo = "Conviene, ma con margine stretto: rientro in circa " + rientro + " anni"; }
    else { cls = "no"; testo = "Con questi numeri non conviene: " + (rientro === null ? "non rientri in 25 anni" : "rientro in " + rientro + " anni"); }
    var avviso = prod > consumo * 1.5 ? "<p><small>Attenzione: l'impianto produce molto più di quanto consumi. L'energia in più si vende a circa 0,10 €/kWh: un impianto più piccolo di solito rientra prima.</small></p>" : "";
    out.innerHTML =
      '<div class="verdetto ' + cls + '">' + testo + "</div>" +
      "<table><tbody>" +
      "<tr><td>Potenza consigliata</td><td>" + d(kw) + " kW" + (battKwh ? " + batteria " + d(battKwh) + " kWh" : "") + "</td></tr>" +
      "<tr><td>Produzione in un anno</td><td>" + k(prod) + "</td></tr>" +
      "<tr><td>Usata subito in casa (" + Math.round(auto / prod * 100) + "%)</td><td>" + k(auto) + "</td></tr>" +
      "<tr><td>Risparmio in bolletta all'anno</td><td>" + e(auto * prezzo) + "</td></tr>" +
      "<tr><td>Energia venduta al GSE all'anno</td><td>" + e(surplus * rid) + "</td></tr>" +
      "<tr><td>Costo dell'impianto" + (n("fv-preventivo") > 0 ? "" : " (stima)") + "</td><td>" + e(costo) + "</td></tr>" +
      "<tr><td>Detrazione (in 10 rate)</td><td>" + e(detr) + "</td></tr>" +
      "<tr><td>Guadagno netto in 25 anni</td><td>" + e(cum) + "</td></tr>" +
      "</tbody></table>" + avviso +
      "<p><small>Stima con prezzi indicativi novembre 2026. Il calcolo tiene conto del calo dei pannelli (0,5% l'anno) e di 1.200 € per cambiare l'inverter dopo circa 12 anni. Non sostituisce un preventivo.</small></p>";
  }
  var box = document.getElementById("calc-fv");
  box.addEventListener("input", calcola);
  box.addEventListener("change", calcola);
  calcola();
})();
</script>

### Come funziona il calcolo

Il calcolatore segue gli stessi passaggi di un tecnico che prepara un preventivo, con valori medi prudenti.

**1. La produzione.** Ogni kW di pannelli rivolti a sud produce in un anno circa 1.150 kWh al Nord, 1.300 al Centro e 1.450 al Sud e nelle isole. Un tetto rivolto a est o a ovest rende circa il 15% in meno. Se non indichi la potenza, il calcolatore sceglie quella che in un anno produce quanto consumi, arrotondata al mezzo kW.

**2. L'autoconsumo.** È la parte decisiva. Un kWh usato in casa mentre i pannelli producono ti fa risparmiare il prezzo pieno, circa 0,32 €. Un kWh mandato in rete il GSE lo paga con il Ritiro Dedicato, che in media vale circa 0,10 €. Senza batteria una famiglia usa direttamente il 25-45% della produzione, a seconda di quanto consuma di giorno. Con la batteria si arriva al 60-80%.

**3. Il costo.** Senza preventivo il calcolatore usa una stima: 1.500 € di costi fissi (progetto, pratiche, ponteggio, allaccio) più 1.300 € per kW, più 800 € per ogni kWh di batteria. Per un impianto da 4 kW fa 6.700 €, nella fascia dei preventivi reali 2026 (6.000-10.000 € senza accumulo).

**4. Il rientro.** È il conto anno per anno: l'impianto lo paghi tutto all'inizio, la detrazione rientra in 10 rate e ogni anno si somma il risparmio. Il calcolo toglie anche il calo dei pannelli e il cambio dell'inverter.

### Le configurazioni più comuni

| Famiglia | Consumo annuo | Impianto tipico | Costo indicativo | Con batteria |
|---|---|---|---|---|
| 1-2 persone | 1.500-2.000 kWh | 2 kW | 4.000-5.000 € | +2.000-2.500 € (2,5 kWh) |
| 3 persone | 2.500-3.000 kWh | 2,5-3 kW | 4.700-6.000 € | +2.500-3.500 € (3-4 kWh) |
| 4 persone | 3.000-4.000 kWh | 3-4 kW | 5.500-7.500 € | +3.500-5.000 € (4-5 kWh) |
| Con pompa di calore | 5.000-7.000 kWh | 5-6 kW | 8.000-10.500 € | +5.000-6.000 € (6-8 kWh) |

*Prezzi indicativi novembre 2026, chiavi in mano con IVA al 10%, prima delle detrazioni. Per le batterie vedi la nostra guida alla [batteria di accumulo per fotovoltaico](/fotovoltaico/batteria-accumulo-fotovoltaico/).*

### Quanto si risparmia davvero: l'esempio con i valori di partenza

Sono i valori con cui il calcolatore si apre: famiglia del Centro Italia, consumo di 2.700 kWh l'anno, luce a 0,32 €/kWh, tetto a sud, qualcuno in casa di giorno, niente batteria, prima casa.

- Impianto consigliato: 2.700 ÷ 1.300 = 2,1 kW, arrotondato a **2,5 kW**
- Produzione: 2,5 × 1.300 = **3.250 kWh l'anno**
- Usata subito in casa (35%): 1.138 kWh × 0,32 € = **364 € di bolletta in meno**
- Venduta al GSE: 2.113 kWh × 0,10 € = **211 € incassati**
- Totale: **circa 575 € l'anno**
- Costo stimato 4.750 €, detrazione del 50% = 2.375 €, cioè 237,50 € l'anno per 10 anni
- **Rientro nel sesto anno**, guadagno netto in 25 anni di **circa 10.000 €**

Con la batteria (3 kWh, +2.400 €) l'energia usata in casa sale al 70% e il risparmio a circa 825 € l'anno. L'impianto costa però 7.150 € e il rientro passa al settimo anno. Il guadagno in 25 anni sale a circa 14.700 €, ma solo se la batteria dura: le garanzie tipiche sono di 10 anni. Chi di giorno non è mai in casa e non ha detrazioni (36% invece del 50%, Nord Italia) scende a circa 445 € l'anno e rientra nell'ottavo anno.

Per il dettaglio della formula, con un esempio da 4 kW, vedi [come calcolare se conviene il fotovoltaico](/fotovoltaico/come-calcolare-se-conviene-il-fotovoltaico/).

### Incentivi disponibili nel 2026

**Bonus ristrutturazioni.** Per tutto il 2026 la detrazione IRPEF è del 50% sull'abitazione principale e del 36% sulle altre case, su una spesa massima di 96.000 € per unità, recuperata in 10 rate annuali. Copre anche la batteria installata con l'impianto. Dal 2027 le aliquote sono previste in calo al 36% per la prima casa e al 30% per le altre: chi è vicino alla decisione ha interesse a pagare entro il 31 dicembre 2026. Per detrarre serve capienza IRPEF, cioè abbastanza imposte da cui scalare la rata. Il Superbonus per il fotovoltaico non è più disponibile.

**IVA al 10%** sugli impianti residenziali, già compresa nei prezzi della tabella.

**Ritiro Dedicato del GSE.** Il GSE paga l'energia immessa in rete al prezzo di mercato dell'ora, con un minimo garantito. Nel calcolatore usiamo 0,10 €/kWh come media prudente. Tutte le regole sono nella guida ai [bonus fotovoltaico 2026](/fotovoltaico/bonus-fotovoltaico-2026-ecobonus-50-e-incentivi-attivi/).

### Conclusione

Il fotovoltaico conviene quasi sempre a chi ha un tetto a sud, consuma almeno 2.000 kWh l'anno e può detrarre il 50%: con i valori medi del 2026 rientra in 5-7 anni. Conviene meno a chi di giorno non consuma quasi nulla e a chi non ha capienza IRPEF. Prima di firmare, inserisci nel calcolatore la potenza e il prezzo del preventivo: se il rientro supera gli 11 anni, chiedi altri due preventivi o valuta un impianto più piccolo. Se il tetto non c'è, l'alternativa è un [kit fotovoltaico da balcone](/fotovoltaico/kit-fotovoltaico-balcone-con-accumulo/).

*Fonti: [GSE - Ritiro Dedicato](https://www.gse.it), [Agenzia delle Entrate - Bonus ristrutturazioni](https://www.agenziaentrate.gov.it), [PVGIS - Commissione Europea, produzione fotovoltaica per zona](https://re.jrc.ec.europa.eu/pvg_tools/it/), [ARERA](https://www.arera.it), [Money.it - costi impianti fotovoltaici 2026](https://www.money.it/quanto-costa-impianto-fotovoltaico-prezzi-detrazioni)*
