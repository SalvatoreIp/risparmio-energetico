
- Dopo aver creato il file eseguire SEMPRE: cd /home/salvatore/risparmio-energetico && rm -rf public/ && hugo --minify && npx wrangler pages deploy public --project-name risparmio-energetico --commit-dirty=true && git add . && git commit -m "TITOLO" && git push

## COME COSTRUIRE IL LINK ARTICOLO
Il link di un articolo NON usa la data come percorso.
La struttura URL è SEMPRE: https://guida-energia.com/SEZIONE/SLUG/

Esempio:
- File creato: content/smart-home/2026-04-24-10-pompe-di-calore.md
- URL corretto: https://guida-energia.com/smart-home/pompe-di-calore/
- URL SBAGLIATO: https://guida-energia.com/2026/04/24/pompe-di-calore/

Regola: prendi il nome della cartella dentro content/ (es. smart-home) 
e lo slug del file SENZA la parte data-ora iniziale (YYYY-MM-DD-HH-).

SLUG = nome file senza "YYYY-MM-DD-HH-" iniziale e senza ".md" finale
URL  = https://guida-energia.com/SEZIONE/SLUG/
