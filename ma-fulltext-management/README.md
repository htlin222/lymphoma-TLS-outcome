# ma-fulltext-management

Tools for managing full-text PDF retrieval in systematic reviews.

---

## Overview

This module provides scripts for:

1. Querying Open Access databases (Unpaywall API)
2. Downloading PDFs automatically
3. Tracking retrieval status
4. Analyzing coverage statistics

---

## Installation

```bash
cd tooling/python
uv add requests bibtexparser
```

---

## Workflow: Stage 03 → Stage 04

### Step 1: Extract BibTeX Subset

After title/abstract screening, extract records for full-text review:

```bash
# Option A: Only "Include" decisions
uv run ../../ma-search-bibliography/scripts/bib_subset_by_ids.py \
  --in-csv ../../03_screening/round-01/decisions.csv \
  --in-bib ../../02_search/round-01/dedupe.bib \
  --out-bib ../../04_fulltext/round-01/fulltext_subset.bib \
  --filter-column final_decision \
  --filter-value Include

# Option B: Include + Uncertain (recommended)
uv run ../../ma-search-bibliography/scripts/bib_subset_by_ids.py \
  --in-csv ../../03_screening/round-01/decisions.csv \
  --in-bib ../../02_search/round-01/dedupe.bib \
  --out-bib ../../04_fulltext/round-01/fulltext_subset.bib
```

**Inputs**:

- CSV with `record_id` column
- Original BibTeX file from Stage 02

**Outputs**:

- Filtered BibTeX file with selected records

---

### Step 2: Query Unpaywall API

Check Open Access availability for all records:

```bash
uv run ../../ma-fulltext-management/scripts/unpaywall_fetch.py \
  --in-bib ../../04_fulltext/round-01/fulltext_subset.bib \
  --out-csv ../../04_fulltext/round-01/unpaywall_results.csv \
  --out-log ../../04_fulltext/round-01/unpaywall_fetch.log \
  --email "your@email.com"
```

**Required**:

- Valid email address (Unpaywall requirement)
- Or set `UNPAYWALL_EMAIL` in `.env`

**Outputs**:

- `unpaywall_results.csv` - Full API results
- `unpaywall_fetch.log` - Query log

**CSV columns**:

- `record_id`, `doi`, `pmid`, `title`
- `is_oa` - True/False
- `oa_status` - gold/green/hybrid/bronze/closed
- `best_oa_url` - Landing page URL
- `best_oa_pdf_url` - Direct PDF URL
- `host_type` - publisher/repository
- `license` - License type
- `updated` - Unpaywall last update

---

### Step 3: Analyze Coverage

Generate summary statistics:

```bash
uv run ../../ma-fulltext-management/scripts/analyze_unpaywall.py \
  --in-csv ../../04_fulltext/round-01/unpaywall_results.csv \
  --out-md ../../04_fulltext/round-01/unpaywall_summary.md
```

**Outputs**:

- Console: Quick summary
- Markdown: Detailed report with tables

**Example output**:

```
📊 Unpaywall Analysis Results
==================================================
Total records queried: 52
Open Access (OA): 38 (73.1%)
  - With PDF URL: 38 (73.1%)
Closed Access: 13 (25.0%)

OA Types:
  - gold      : 16 (42.1% of OA)
  - hybrid    : 14 (36.8% of OA)
  - bronze    :  5 (13.2% of OA)
  - green     :  3 ( 7.9% of OA)
```

---

### Step 4: Download OA PDFs

Automatically download available PDFs:

```bash
uv run ../../ma-fulltext-management/scripts/download_oa_pdfs.py \
  --in-csv ../../04_fulltext/round-01/unpaywall_results.csv \
  --pdf-dir ../../04_fulltext/round-01/pdfs \
  --out-log ../../04_fulltext/round-01/pdf_download.log \
  --sleep 1 \
  --max-retries 3 \
  --timeout 30
```

**Parameters**:

- `--sleep` - Seconds between downloads (rate limiting)
- `--max-retries` - Retry failed downloads
- `--timeout` - HTTP timeout per request
- `--skip-existing` - Skip if PDF already exists (default: True)

**Outputs**:

- PDFs saved to `--pdf-dir` with naming: `{record_id}.pdf`
- Detailed log with success/failure reasons

**Expected success rate**:

- Gold OA: ~80-90% (open publishers like MDPI, BMC)
- Green OA: ~60-70% (repositories)
- Hybrid OA: ~20-30% (most block direct downloads)
- Bronze OA: ~10-20% (paywall with free access)

**Common failure reasons**:

1. **403 Forbidden** - Publisher blocks bot downloads
   → Solution: Manual download via institutional access
2. **404 Not Found** - URL expired or moved
   → Solution: Check publisher website
3. **Timeout** - Server slow response
   → Solution: Increase `--timeout` or retry

---

## Script Reference

### bib_subset_by_ids.py

**Location**: `ma-search-bibliography/scripts/`

**Purpose**: Extract BibTeX entries matching CSV record IDs

**Usage**:

```bash
uv run bib_subset_by_ids.py \
  --in-csv <csv_file> \
  --in-bib <bib_file> \
  --out-bib <output_file> \
  [--id-column record_id] \
  [--filter-column <column>] \
  [--filter-value <value>]
```

**Options**:

- `--id-column` - CSV column with record IDs (default: `record_id`)
- `--filter-column` - Optional column to filter by
- `--filter-value` - Value to match in filter column

**Examples**:

```bash
# Extract all records
uv run bib_subset_by_ids.py \
  --in-csv records.csv \
  --in-bib full.bib \
  --out-bib subset.bib

# Extract only included records
uv run bib_subset_by_ids.py \
  --in-csv screening.csv \
  --in-bib full.bib \
  --out-bib included.bib \
  --filter-column decision \
  --filter-value Include
```

---

### unpaywall_fetch.py

**Location**: `ma-fulltext-management/scripts/`

**Purpose**: Query Unpaywall API for Open Access information

**Usage**:

```bash
uv run unpaywall_fetch.py \
  --in-bib <bib_file> \
  --out-csv <output_csv> \
  --out-log <log_file> \
  [--email <email>] \
  [--sleep 1]
```

**Required**:

- Email address (via `--email` or `UNPAYWALL_EMAIL` env var)

**Rate limits**:

- 100,000 requests/day per email
- Recommended: 1-2 seconds between requests

---

### analyze_unpaywall.py

**Location**: `ma-fulltext-management/scripts/`

**Purpose**: Analyze Unpaywall results and generate statistics

**Usage**:

```bash
uv run analyze_unpaywall.py \
  --in-csv <unpaywall_results.csv> \
  [--out-md <summary.md>]
```

**Outputs**:

- Console summary
- Optional markdown report with tables

---

### download_oa_pdfs.py

**Location**: `ma-fulltext-management/scripts/`

**Purpose**: Download PDFs from Unpaywall URLs

**Usage**:

```bash
uv run download_oa_pdfs.py \
  --in-csv <unpaywall_results.csv> \
  --pdf-dir <output_directory> \
  --out-log <log_file> \
  [--sleep 1] \
  [--max-retries 3] \
  [--timeout 30] \
  [--skip-existing]
```

**Best practices**:

- Use `--sleep 1` to avoid rate limiting
- Set `--max-retries 3` for transient failures
- Check log file for failure reasons
- Manually retrieve failed PDFs via institutional access

---

## Troubleshooting

### Unpaywall 422 Error

**Problem**: `422 Unprocessable Entity`

**Cause**: Invalid email address

**Solution**:

```bash
# Use real email address
export UNPAYWALL_EMAIL="your.real.email@institution.edu"
```

---

### Low PDF Download Success Rate

**Problem**: Only 20-30% PDFs download successfully

**Cause**: Publishers block direct bot downloads (403 errors)

**Solution**:

1. **Use institutional access** for hybrid/bronze OA
2. **Try PubMed Central** for articles with PMID
3. **Contact authors** for closed-access articles

**Workflow**:

```bash
# 1. Check which PDFs failed
grep "FAIL:" pdf_download.log

# 2. Filter for 403 errors (institutional access can help)
grep "403" pdf_download.log

# 3. Try PMC for articles with PMID
# https://www.ncbi.nlm.nih.gov/pmc/articles/PMID{pmid}/pdf/
```

---

### DOI Not Found in Unpaywall

**Problem**: Some records return no results

**Cause**:

- DOI not indexed in Unpaywall
- Invalid DOI format
- Very recent publication (not yet indexed)

**Solution**:

- Check DOI at https://doi.org/
- Try CrossRef API as alternative
- Search directly on publisher website

---

## Expected Retrieval Rates

Based on systematic review benchmarks:

| Source    | Expected Success | Method                         |
| --------- | ---------------- | ------------------------------ |
| Gold OA   | 80-90%           | Automated download             |
| Green OA  | 60-70%           | Automated + repository         |
| Hybrid OA | 60-80%           | Institutional access required  |
| Bronze OA | 40-60%           | Institutional + manual         |
| Closed    | 50-70%           | Institutional + author contact |

**Overall target**: 70-85% of full-text candidates

---

## Integration with CLAUDE.md

These scripts are documented in the main `CLAUDE.md` file under:

- **Stage 04: Fulltext** section

For systematic review workflows, follow the command sequence in CLAUDE.md.

---

## Development Notes

### Moving Scripts from tooling/python

These scripts were originally developed in `tooling/python/` and generalized for reuse:

- `csv_to_bib_subset.py` → `bib_subset_by_ids.py`
- `download_oa_pdfs.py` (paths made configurable)
- `analyze_unpaywall.py` (added markdown output)

**Changes made for generalization**:

1. All file paths converted to argparse parameters
2. Added flexible column name handling
3. Improved error messages and validation
4. Added retry logic for download failures
5. Comprehensive docstrings and help text

---

## Future Enhancements

Potential additions:

1. **Browser automation** - Use Selenium for institutional downloads
2. **Batch retry** - Re-attempt failed downloads after manual fixes
3. **PubMed Central integration** - Automatic PMC fallback
4. **Zotero connector** - Use Zotero's retrieval capabilities
5. **CrossRef API** - Alternative to Unpaywall
6. **Unpaywall snapshot** - Work with local Unpaywall data dump

---

## Related Modules

- `ma-search-bibliography` - BibTeX manipulation and search
- `ma-screening-quality` - Title/abstract screening
- `ma-data-extraction` - PDF text extraction

---

## Support

For issues or questions:

1. Check `TROUBLESHOOTING.md` in project root
2. Review Unpaywall documentation: https://unpaywall.org/
3. Check script help: `uv run <script>.py --help`
