# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Hugo static site (`guida-energia.com`, theme: PaperMod as a git submodule) — an Italian-language content farm/blog about energy savings (fotovoltaico, smart home, riscaldamento, incentivi, ecc.). This is not an application codebase; the vast majority of work here is writing and publishing Markdown articles, not editing code. Deployed to Cloudflare Pages.

## Commands

Build and deploy (the full publish cycle used after any content or config change):

```bash
cd /home/salvatore/risparmio-energetico && rm -rf public/ && hugo --minify \
  && npx wrangler pages deploy public --project-name risparmio-energetico --commit-dirty=true \
  && git add . && git commit -m "TITOLO" && git push
```

- Local preview: `hugo server -D`
- `scripts/publish_post.sh "$TITLE" "$BODY" "$SECTION" "$IMAGE_PATH" "$DESCRIPTION" "$TAGS"` — scaffolds a new article file under `content/$SECTION/YYYY-MM-DD-slug.md` from args, then runs `git add/commit/push` itself. Only handles the six sections hardcoded in its `case` statement (falls back to `guide` otherwise) — new sections (idroponica, mobilita-sostenibile, raffrescamento, terrazzi) must be created by hand.
- `scripts/get_image.sh KEYWORD SLUG` — fetches a Pixabay photo (English keyword) into `static/immagini/SLUG.jpg`, falling back to picsum.photos if Pixabay returns nothing. Requires `PIXABAY_API_KEY` in `.env`.
- There is no test suite, linter, or build step beyond `hugo --minify`; correctness is "does `hugo` build without errors and does the page look right."

## Content architecture

- **Articles live in `content/<section>/`**, one Markdown file per article, named `YYYY-MM-DD-slug.md` (or `YYYY-MM-DD-HH-slug.md`). Each section has an `_index.md` for its listing page.
- **URLs strip the date.** Permalinks (`hugo.toml` `[permalinks]`) are `/<section>/:slug/` — the leading `YYYY-MM-DD(-HH)-` in the filename is NOT part of the URL. E.g. `content/smart-home/2026-04-24-10-pompe-di-calore.md` → `https://guida-energia.com/smart-home/pompe-di-calore/`.
- **Sections must be registered in three places** to fully work (nav menu, listing behavior, URL structure) — `hugo.toml`'s `[params].mainSections`, `[[menu.main]]` entries, and `[permalinks]`. `content/terrazzi/` currently exists on disk but is not registered in any of these — treat unregistered content directories as broken/orphaned until wired up.
- Required frontmatter per article:
  ```yaml
  ---
  title: "..."
  date: YYYY-MM-DDTHH:MM:SSZ
  draft: false
  description: "..."
  categories: ["<section>"]
  tags: ["tag1", "tag2", "tag3"]
  cover:
    image: "/immagini/slug.jpg"
    alt: "..."
  ---
  ```
- Cover/content images go in `static/immagini/`, referenced as `/immagini/<slug>.jpg`.
- `hugo.toml` is the live config; `hugo.toml.bak*` are untracked-by-purpose scratch backups from past edits — don't treat them as alternate configs to merge from unless explicitly asked.
- `layouts/partials/extend_head.html` / `extend_footer.html` override the PaperMod theme to inject Google Analytics (GA4) and a custom cookie-consent banner (sets `cookie_consent`/`cookie_analytics`/`cookie_marketing` cookies). This is the only custom layout code in the repo — everything else is the unmodified PaperMod submodule (`themes/PaperMod`).
- `static/_redirects` defines a Cloudflare Pages redirect: `/vai/*` → Amazon affiliate links (tag `botofferte04-21`) — a cloaked-link shortener for affiliate URLs used in article link tables.

## Editorial rules for new articles

These are the standing content rules this site has been built under (see `OPENCLAW.ISTRUZIONIENERGIA.md` for the exhaustive version, including the current keyword backlog per section):

- Italian, 800–1200 words, original text only (never copy from sources).
- Mandatory structure: Introduzione → Cos'è e come funziona → I migliori modelli (Markdown product table) → Quanto si risparmia davvero → Incentivi disponibili → Conclusione → `*Fonti: ...*`.
- Every article needs at least one concrete savings calculation in euros.
- Amazon links: only use a real link found by searching the actual product on Amazon.it — never fabricate an ASIN or URL. If the product isn't found, omit the link (or link an informational/comparison page for big-ticket items like heat pumps/boilers).
- Slug: lowercase + hyphens only, no apostrophes or accented characters.
- One category per article; double quotes in frontmatter, never single/apostrophes.
- Don't create content directories beyond the ones already registered (see Content architecture above).
- Price references should be dated (e.g. "Prezzo indicativo maggio 2026").
- No test/placeholder/draft-only posts committed.

## Environment

`.env` (gitignored) holds `PIXABAY_API_KEY`, `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID` — required for image fetching and `wrangler pages deploy`.
