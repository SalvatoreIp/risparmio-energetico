#!/usr/bin/env python3
"""Hook di Claude Code (configurato in .claude/settings.json).

  proteggi   (PreToolUse Edit|Write): impedisce di modificare .env
  articolo   (PostToolUse Edit|Write): dopo aver scritto un articolo, segnala a Claude
             errori e avvisi di scripts/controlla_articolo.py perché li corregga
  pubblica   (PreToolUse Bash): blocca git push / wrangler deploy se un articolo
             nuovo o modificato ha ERRORI (link rotti, slug, copertina, tag, data)

Exit 2 = il messaggio su stderr torna a Claude (e in PreToolUse blocca l'azione).
"""
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTROLLO = os.path.join(ROOT, "scripts", "controlla_articolo.py")


def registra(modo, testo):
    """Lascia traccia in logs/hook_controlli.log (utile per capire cosa è successo nei cron)."""
    import datetime
    try:
        with open(os.path.join(ROOT, "logs", "hook_controlli.log"), "a", encoding="utf-8") as f:
            f.write(f"[{datetime.datetime.now():%Y-%m-%d %H:%M}] {modo}\n{testo}\n\n")
    except OSError:
        pass


def esegui(*args):
    r = subprocess.run([sys.executable, CONTROLLO, *args], capture_output=True, text=True, cwd=ROOT)
    return r.returncode, r.stdout.strip()


def main():
    modo = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        dati = json.load(sys.stdin)
    except Exception:
        return 0
    inp = dati.get("tool_input") or {}

    if modo == "proteggi":
        if os.path.basename(inp.get("file_path", "")).startswith(".env"):
            print("Il file .env contiene le credenziali: non va modificato da Claude. "
                  "Se serve cambiarlo, chiedi a Salvatore.", file=sys.stderr)
            return 2
        return 0

    if modo == "articolo":
        path = os.path.abspath(inp.get("file_path", ""))
        rel = os.path.relpath(path, ROOT)
        if not re.match(r"content/[^/]+/[^/]+\.md$", rel) or rel.endswith("_index.md") or not os.path.exists(path):
            return 0
        _, out = esegui(path)
        if out:
            registra("articolo: segnalazioni", out)
            print("Controllo automatico dell'articolo (regole di CLAUDE.md). Correggi gli ERRORI; "
                  "gli avvisi correggili se possibile:\n" + out, file=sys.stderr)
            return 2
        return 0

    if modo == "pubblica":
        cmd = inp.get("command", "")
        if not re.search(r"git\s+push|wrangler\s+pages\s+deploy", cmd):
            return 0
        codice, out = esegui("--modificati")
        if codice != 0:
            registra("pubblicazione BLOCCATA", out)
            print("Pubblicazione BLOCCATA dal controllo automatico: correggi gli ERRORI qui sotto e "
                  "riprova (gli avvisi non bloccano).\n" + out, file=sys.stderr)
            return 2
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
