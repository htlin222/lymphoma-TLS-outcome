# PubMed E-utilities Python Tutorial (Compact)

## Goal
Fetch PubMed records with a reproducible query, then export them to BibTeX.

## Setup (uv)
1. Run `uv init` inside `tooling/python/`.
2. Run `uv add biopython requests`.
3. Store credentials in `.env` in the project root (recommended).
4. Execute scripts with `uv run` (avoid direct `python3` calls).

## Minimal Pipeline
1. Build a PubMed query string from `01_protocol/pico.yaml`.
2. Call `esearch` with `usehistory=y` to obtain `WebEnv` and `QueryKey`.
3. Use `efetch` with `retstart` and `retmax` to page results.
4. Convert the XML response to BibTeX and write `02_search/round-01/results.bib`.

## Notes
- Set `Entrez.email` and `Entrez.api_key` for compliant usage.
- `PUBMED_API_KEY` is read from `.env` if not passed via CLI.
- Respect PubMed limits: large queries may require paging and history use.
- Preserve query and retrieval metadata in `02_search/round-01/log.md`.
