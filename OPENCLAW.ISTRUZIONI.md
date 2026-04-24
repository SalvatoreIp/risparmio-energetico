
- Dopo aver creato il file eseguire SEMPRE: cd /home/salvatore/risparmio-energetico && rm -rf public/ && hugo --minify && npx wrangler pages deploy public --project-name risparmio-energetico --commit-dirty=true && git add . && git commit -m "TITOLO" && git push
