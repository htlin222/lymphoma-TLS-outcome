# Pipeline Design Fixes — Backlog from lymphoma-tls-outcome session

**Date**: 2026-04-10
**Source**: Real-world friction observed while running lymphoma-tls-outcome end-to-end in a single Claude Code session.
**Status**: Backlog — items to be scheduled. None are bugs that block existing projects; all are friction points that prevented full execution of dual-review screening, abstract enrichment, and structured extraction.

---

## Scope and non-goals

**In scope**: Concrete, file-level pipeline issues observed in this session, with prioritized fix proposals.

**Out of scope**:
- Refactoring `tooling/python/ai_screen.py` away from `claude -p` subprocess. **User decision 2026-04-10: keep `claude -p` short-term, do not rewrite.** A `--bare` tightening (Item #2) is in scope; replacing the whole subprocess model is not.
- Manuscript-side issues (Quarto/template/journal formatting).
- Any rewrite of the `ma-*` skill structure.

---

## Issue inventory (priority order)

### P0 — Blocking abstract-level screening at scale

#### #1. No abstract enrichment stage between search and screening

**Symptom**: `pubmed_fetch.py` and `scopus_fetch.py` write `.bib` files that contain title / authors / journal / DOI / PMID but **no abstract field**. `bib_to_csv.py` then writes a `records.csv` with an empty `abstract` column. `ai_screen.py` reads `screening-database.csv` and assumes abstracts are populated — but no upstream tool populates them.

**Effect on this session**: I had to write inline Python (`Bio.Entrez.efetch`) to fetch 33 abstracts, then 25 Scopus-only records were silently dropped because they had no PMID for Entrez to query. The 611 records that the title pre-filter excluded were never given an abstract-level chance.

**Fix**: Add `ma-search-bibliography/scripts/enrich_abstracts.py`:

```
input:  02_search/round-XX/dedupe.bib
output: 03_screening/round-XX/records_with_abstracts.csv
flow:
  for record in dedupe.bib:
      if record.has_pmid:        fetch via Entrez efetch (batch 200)
      elif record.has_doi:       fetch via CrossRef /works/{doi}
      else:                      fetch via OpenAlex search by title+year
      if still no abstract:      mark abstract_source = "unavailable"
write CSV with: pmid, doi, title, abstract, abstract_source, fetch_date
```

**Acceptance**: Running `enrich_abstracts.py --in dedupe.bib --out records.csv` on the lymphoma-tls-outcome corpus must populate abstracts for ≥95 % of records.

**Estimated effort**: 1-2 hours. Bio.Entrez and CrossRef both straightforward; OpenAlex is the fallback.

**Touches**:
- `ma-search-bibliography/scripts/enrich_abstracts.py` (new)
- `ma-search-bibliography/SKILL.md` (add Stage 02b)
- `ma-end-to-end/SKILL.md` (insert Stage 2.5)

---

#### #2. `ai_screen.py` should call `claude -p --bare`

**Symptom**: `tooling/python/ai_screen.py` invokes `subprocess.run(["claude", "-p", prompt, ...])`. Each call boots a full Claude Code session with the project CLAUDE.md, all skills, all hooks, all tooling — for a 2-line decision.

**Effect**: Token cost per abstract is dominated by system context, not the abstract itself. Hooks fire on every spawn (file-exists checker etc.). Cold-start latency runs into seconds per record.

**Fix (short-term, in keeping with the user's decision to retain `claude -p`)**:

```python
# tooling/python/ai_screen.py — line ~150 (the subprocess call site)
SUBPROCESS_CMD = [
    "claude",
    "-p",
    "--bare",                       # NEW: strip system prompt + skills + hooks
    "--no-conversation-history",    # NEW (if available): no history persisted
    "--output-format", "json",      # NEW: structured output, no chat preamble
    prompt,
]
```

The `--bare` flag (and equivalent flags depending on the installed Claude Code version) tells the child Claude not to load the project CLAUDE.md / global CLAUDE.md / skills index / hooks. The screening prompt becomes the **only** input the child sees.

**Acceptance**:
- Per-call token cost on a representative abstract drops from `~10000 input tokens` (full system load) to `~1500 input tokens` (just the screening prompt + abstract).
- A throughput test of 50 records completes in < 8 minutes (vs. > 30 with the loaded session).
- Decisions on a held-out 20-record gold set match the previous (loaded) version's decisions ≥ 95 %.

**Risk**: `--bare` may not exist as a flag in all Claude Code versions, or may be named differently (`--no-system`, `--strip-context`). Item #3 below addresses verification.

**Touches**:
- `tooling/python/ai_screen.py`
- Tests under `tooling/python/tests/test_ai_screen_cli.py` (new)
- No SKILL.md changes; same external interface.

---

#### #3. Verify `claude -p` flag inventory and pin a minimum version

**Symptom**: Item #2 assumes `--bare` exists. We don't currently document the assumed Claude Code CLI version, and `ai_screen.py` doesn't check.

**Fix**:
1. Run `claude -p --help 2>&1 | grep -E '(bare|system|context|history)'` and write findings to `tooling/python/CLAUDE_CLI_FLAGS.md`.
2. Add a startup assertion to `ai_screen.py`:
   ```python
   def _assert_claude_cli():
       out = subprocess.run(["claude", "--version"], capture_output=True, text=True)
       # parse and require >= a known-good minimum
   ```
3. Document the supported flags in `tooling/python/README.md`.

**Acceptance**: Anyone cloning this repo and running `ai_screen.py` against an old `claude` CLI gets a clear error pointing at the version requirement.

---

### P1 — Pipeline correctness / preventing silent skips

#### #4. `ai_screen.py` hardcoded `META_PIPE_ROOT`

**Current**:
```python
# tooling/python/ai_screen.py:27
META_PIPE_ROOT = Path("/Users/htlin/meta-pipe")
```

**Effect**: This repo lives at `/Users/htlin/lymphoma-TLS-outcome/`. The script computes `META_PIPE_ROOT / "projects" / project_name` and looks in a directory that doesn't exist. Silent failure mode: it reads no records and exits "successfully" with zero decisions.

**Fix**:
```python
META_PIPE_ROOT = Path(os.environ.get(
    "MA_PIPE_ROOT",
    Path(__file__).resolve().parent.parent.parent
))
```
Plus a one-line `assert (META_PIPE_ROOT / "projects").is_dir()` at startup.

**Touches**: `tooling/python/ai_screen.py`. Probably the same pattern is repeated in `simple_screen_wm.py`, `ai_screen_titles.py`, `project_status.py`, `team_spawn_helper.py` — grep for `META_PIPE_ROOT` and fix the lot.

---

#### #5. `scopus_fetch.py` doesn't report `total-results` and silently caps

**Current**: `scopus_fetch.py --max-records 1000` returns 1000 records with no warning that more existed. In this session, the first run hit the cap and I had to tighten the query manually.

**Fix**: Read the `search-results.opensearch:totalResults` field from the first response and:
1. Print `Found N total, fetching min(N, max_records)`.
2. If `N > max_records`, write a warning to the log.
3. Add `--strict-cap` flag that exits non-zero when the cap is hit (so CI / scripts can detect "your query is too broad").

**Acceptance**: Re-running this session's first Scopus query reports `Found ~552 total, fetching all` instead of silently returning 1000.

---

#### #6. Dependencies not pinned in `tooling/python/pyproject.toml`

**Symptom**: `ma-search-bibliography/scripts/*.py` import `Bio`, `bibtexparser`, `rapidfuzz` — none of which are in `tooling/python/pyproject.toml`. I had to invoke each script as `uv run --with biopython --with bibtexparser --with rapidfuzz ...`, which re-resolves on every run.

**Fix**: Either
1. **Option A** (preferred): Add `biopython`, `bibtexparser`, `rapidfuzz`, `lxml`, `requests` to `tooling/python/pyproject.toml`'s dependencies. Run `uv lock`. Commit `uv.lock`.
2. **Option B**: Make `ma-search-bibliography/` its own uv project with its own `pyproject.toml`.

I recommend Option A. There is one project root, one lock file, one `uv run`.

**Touches**: `tooling/python/pyproject.toml`, `tooling/python/uv.lock`.

---

### P2 — Quality of life / would-have-saved-an-hour

#### #7. No "draft" / "fast prototype" mode

**Symptom**: The pipeline assumes every project goes through dual-review screening (kappa ≥ 0.60), PROSPERO registration, full GRADE, PRISMA 27/27, and a quality-readiness ≥ 95 % gate. There is no supported way to say "I want a 90-minute first-pass evidence sketch with all deviations declared."

**Effect on this session**: I bypassed dual-review entirely and documented it in narrative paragraphs. That is *worse* than a supported "draft mode" which would explicitly flag the artifacts as draft and stamp the manuscript.

**Fix proposal**:
```bash
uv run tooling/python/init_project.py --name X --mode draft
# stores quality_mode=draft in projects/X/.ma_meta.json
# every artifact-writing script checks this and:
#   - allows single-reviewer screening (no kappa gate)
#   - skips PROSPERO with TODO file
#   - watermarks rendered manuscript: "DRAFT — single-reviewer screening, not for submission"
#   - validate_pipeline.py treats single-reviewer as a deviation, not a failure
```

**Rationale**: AI-driven sessions naturally produce "good enough first pass" outputs. The pipeline should support that path with first-class deviation tracking, not force users (or AI agents) to silently bypass the quality gates.

**Touches**: `tooling/python/init_project.py`, `validate_pipeline.py`, `ma-end-to-end/SKILL.md`, manuscript template.

---

#### #8. PMC full-text → structured 2×2 extraction is manual

**Symptom**: We have `extract_pdf_text.py` (PDF → plain text) and we have `ai_populate_extraction.py` (LLM-fills extraction template). I used neither because they assume a downstream extraction CSV schema that doesn't include the basic prognostic-factor 2×2:

```
n_total | n_exposed | n_unexposed | events_exposed | events_unexposed
```

In this session I manually read 7 PMC XML files and back-calculated mortality counts from KM percentages. That doesn't scale.

**Fix**: Add a CHARMS-PF / prognostic factor extraction template under `ma-data-extraction/templates/prognostic_factor.yaml`:

```yaml
fields:
  - name: n_total
    type: int
    prompt: "Total number of patients in the analysis cohort."
  - name: n_exposed
    type: int
    prompt: "Number of patients with the exposure (e.g., TLS at presentation)."
  - name: events_exposed
    type: int
    prompt: "Number of outcome events (e.g., deaths) in the exposed group."
  # ... etc
  - name: effect_estimate
    type: float
    prompt: "Reported point estimate (OR/HR/RR). Pick adjusted if both are reported."
  - name: ci_lower
    type: float
  - name: ci_upper
    type: float
  - name: adjustment_set
    type: string
    prompt: "List of variables adjusted for, or 'unadjusted'."
```

Then `ai_populate_extraction.py --template prognostic_factor` does the rest.

**Acceptance**: Re-running on the 6 included studies of this project produces the same `extraction.csv` I built by hand.

**Touches**: `ma-data-extraction/templates/prognostic_factor.yaml` (new), `tooling/python/ai_populate_extraction.py`, `ma-data-extraction/SKILL.md`.

---

#### #9. No "session log" stamp on output artifacts

**Symptom**: When this session ends, there is no single place that records "this artifact was generated by an AI session at 2026-04-10 with the following deviations: [list]." A future reader has to reconstruct it from the various `agreement.md` files.

**Fix**: Add a `tooling/python/session_log.py append` call at every stage exit, writing to `projects/X/SESSION_LOG.md`. Already partially implemented (`session_log.py` exists). Wire it up in the SKILL files so each stage appends a one-line entry.

---

## Sequencing

**Sprint 1 (P0, ~one afternoon)**
1. #4 path fix — 15 min
2. #6 dependency pinning — 30 min
3. #1 abstract enrichment — 1.5 h
4. #5 Scopus total-results — 30 min
5. #3 Claude CLI flag inventory — 30 min
6. #2 `claude -p --bare` — 30 min (depends on #3)

After Sprint 1, a future session can run dual-review screening on the full 669-record corpus end-to-end without inline Python hacks.

**Sprint 2 (P1, ~one afternoon)**
- #7 draft mode
- #8 prognostic factor extraction template

**Sprint 3 (cleanup)**
- #9 session log wiring
- Backfill tests
- Documentation pass on `ma-end-to-end/SKILL.md`

---

## Open questions for the user

1. **`--bare` flag name**: What is the exact flag in your installed `claude` CLI version? Need to confirm before #2 lands. Run `claude -p --help` and paste relevant lines.
2. **Draft mode default**: Should `init_project.py` default to draft, or strict? My instinct: draft is safer default; require explicit `--mode strict` for submission-track work. You may disagree.
3. **Where to put the abstract enrichment script**: under `ma-search-bibliography/scripts/` (where the other fetchers live) or `tooling/python/`? I lean toward `ma-search-bibliography/` for cohesion.

---

## Out of scope / explicitly NOT in this plan

- Refactoring `ai_screen.py` to call the LLM API directly (`requests` to `LLM_API_BASE`). User has decided this is short-term locked to `claude -p`. Item #2 is the *tightening* path inside that constraint.
- Replacing Quarto with another rendering engine.
- Any change to the `ma-*` SKILL.md command-reference structure.
- Migrating from `uv` to another package manager.
