# Phase 4: Full-Text Review Quick Start

**Project**: {{PROJECT_NAME}}
**Date**: {{DATE}}
**Phase**: Phase 4 - Full-Text Retrieval and Review
**Studies for review**: {{FULLTEXT_COUNT}} ({{INCLUDE_COUNT}} include + {{MAYBE_COUNT}} maybe)

---

## 📊 Current Status

### Completed

- ✅ Title/abstract screening: {{TOTAL_RECORDS}} → {{FULLTEXT_COUNT}} studies
- ✅ BibTeX subset created: `04_fulltext/round-01/fulltext_subset.bib`
- ✅ PDF download directory prepared

### To Do

- ⏳ Obtain PDF files (~{{FULLTEXT_COUNT}} studies)
- ⏳ Full-text review to verify inclusion criteria
- ⏳ Final inclusion decision (expected {{EXPECTED_FINAL_INCLUDE}} studies)

---

## 🎯 Phase 4 Objectives

### Main Tasks

1. **PDF Retrieval** (3-5 days)
   - Automatically search for Open Access PDFs (Unpaywall)
   - Manually download subscription-required articles
   - Expected 40-60% can be obtained automatically

2. **Full-Text Review** (1-2 weeks)
   - Read full text to verify inclusion criteria
   - Document exclusion reasons
   - Identify duplicate reports

3. **Final Inclusion List** (2-3 days)
   - Compile final list of included studies
   - Document PRISMA flow diagram data
   - Prepare for data extraction

---

## 📁 File Structure

```
04_fulltext/round-01/
├── fulltext_subset.bib          # {{FULLTEXT_COUNT}} studies needing full text ✅
├── unpaywall_results.csv        # Unpaywall OA status (to be created)
├── unpaywall_summary.md         # OA statistics summary (to be created)
├── pdf_download.log             # PDF download log (to be created)
├── pdfs/                        # PDF storage location
│   ├── {{EXAMPLE_PDF_1}}.pdf
│   ├── {{EXAMPLE_PDF_2}}.pdf
│   └── ... (to be downloaded)
└── fulltext_decisions.csv       # Full-text review decisions (to be created)
```

---

## 🚀 Step 1: Automatic PDF Retrieval (Recommended)

### Using Unpaywall API (Free)

Unpaywall can find 40-60% of Open Access PDFs automatically.

**Automated method**:

```bash
cd /Users/htlin/meta-pipe/tooling/python

# Query Unpaywall API for OA status
uv run ../../ma-fulltext-management/scripts/unpaywall_fetch_robust.py \
  --in-bib ../../projects/{{PROJECT_NAME}}/04_fulltext/round-01/fulltext_subset.bib \
  --out-csv ../../projects/{{PROJECT_NAME}}/04_fulltext/round-01/unpaywall_results.csv \
  --out-log ../../projects/{{PROJECT_NAME}}/04_fulltext/round-01/unpaywall_fetch.log \
  --out-json ../../projects/{{PROJECT_NAME}}/04_fulltext/round-01/unpaywall_results.json \
  --email "{{YOUR_EMAIL}}" \
  --continue-on-error \
  --max-retries 3

# Analyze Unpaywall results
uv run ../../ma-fulltext-management/scripts/analyze_unpaywall.py \
  --in-csv ../../projects/{{PROJECT_NAME}}/04_fulltext/round-01/unpaywall_results.csv \
  --out-md ../../projects/{{PROJECT_NAME}}/04_fulltext/round-01/unpaywall_summary.md

# Download Open Access PDFs automatically
uv run ../../ma-fulltext-management/scripts/download_oa_pdfs.py \
  --in-csv ../../projects/{{PROJECT_NAME}}/04_fulltext/round-01/unpaywall_results.csv \
  --pdf-dir ../../projects/{{PROJECT_NAME}}/04_fulltext/round-01/pdfs \
  --out-log ../../projects/{{PROJECT_NAME}}/04_fulltext/round-01/pdf_download.log \
  --sleep 1 \
  --max-retries 3
```

**Expected results**:

- 40-60% PDFs downloaded automatically (Gold/Green OA)
- Remaining PDFs need manual retrieval via institutional access
- See `unpaywall_summary.md` for retrieval statistics

**Manual method** (if API issues):

1. **Install Unpaywall browser extension**
   - Visit: https://unpaywall.org/products/extension
   - Install for Chrome/Firefox
   - When visiting article pages, automatically shows OA versions

2. **Prioritize key studies**:
   - {{KEY_STUDY_1}}
   - {{KEY_STUDY_2}}
   - {{KEY_STUDY_3}}
   - Other included studies ({{INCLUDE_COUNT}} total)

---

## 🔍 Step 2: Manual PDF Retrieval

For non-OA articles:

### Method 1: Institutional Subscription Access

1. **Via library proxy**
   - Connect to VPN (if off-campus)
   - Access journal website
   - Download PDF directly

2. **Major publishers**:
   - NEJM, JAMA Network
   - Lancet series
   - Nature Medicine
   - BMJ
   - Major society journals (ASCO, ESMO, etc.)

### Method 2: Contact Authors

For inaccessible articles:

1. Find corresponding author's email
2. Send polite request:

```
Subject: Request for full text: [Paper Title]

Dear Dr. [Author],

I am conducting a systematic review on {{RESEARCH_TOPIC}}.
I would greatly appreciate if you could share a PDF of your publication:

[Full Citation]

This will be used solely for academic purposes in our meta-analysis.

Thank you for your consideration.

Best regards,
[Your Name]
```

### Method 3: ResearchGate / Academia.edu

Many authors share their papers on these platforms.

### Method 4: Inter-library Loan (ILL)

If your institution offers ILL services:

1. Submit request through library portal
2. Usually takes 3-7 days
3. Often free for academic purposes

---

## 📋 Step 3: Organize PDF Files

### Naming Convention

Recommended format: `FirstAuthor_Year_ShortTitle.pdf` or `FirstAuthor_Year_TrialName.pdf`

Examples:

- `Schmid_2022_KEYNOTE522.pdf`
- `Mittendorf_2020_IMpassion031.pdf`
- `Loibl_2019_GeparNuevo.pdf`

### Folder structure

```
04_fulltext/round-01/pdfs/
├── included/           # PDFs that will be included (after full-text review)
├── excluded/           # PDFs excluded after full-text review
└── uncertain/          # PDFs needing discussion
```

---

## 📖 Step 4: Full-Text Review

### Create review spreadsheet

```bash
cd /Users/htlin/meta-pipe/tooling/python

# Create full-text review template
uv run create_fulltext_review_template.py \
  --in-bib ../../projects/{{PROJECT_NAME}}/04_fulltext/round-01/fulltext_subset.bib \
  --out-csv ../../projects/{{PROJECT_NAME}}/04_fulltext/round-01/fulltext_decisions.csv
```

### Review columns

```csv
record_id              # Unique identifier
title                  # Study title
first_author           # First author
year                   # Publication year
pdf_obtained           # yes/no
pdf_file_name          # Actual PDF filename
reviewer_1_decision    # include/exclude/uncertain
reviewer_2_decision    # include/exclude/uncertain
final_decision         # Consensus decision
exclusion_reason       # If excluded
notes                  # Additional notes
```

### Review checklist for each study

For each PDF, verify:

1. ✅ **Study design**: Matches {{STUDY_DESIGN}}?
2. ✅ **Population**: Matches {{POPULATION}}?
3. ✅ **Intervention**: Matches {{INTERVENTION}}?
4. ✅ **Comparator**: Matches {{COMPARATOR}}?
5. ✅ **Outcomes**: Reports {{OUTCOMES}}?
6. ✅ **Sample size**: Meets minimum N={{MIN_SAMPLE_SIZE}}?
7. ✅ **Data availability**: Sufficient data for meta-analysis?

### Common reasons for full-text exclusion

1. **Wrong outcomes**: No relevant outcomes reported
2. **Wrong intervention**: Different intervention than specified
3. **Wrong population**: Different population
4. **Duplicate**: Same data published elsewhere
5. **Insufficient data**: Cannot extract needed data
6. **Study design issues**: Protocol violation, stopped early, etc.

---

## 📊 Expected Results

### PDF Retrieval Success Rate

- **Automatic retrieval (Unpaywall)**: 40-60%
- **Institutional access**: 30-40%
- **Author contact**: 5-10%
- **Unable to obtain**: <5%

### Full-text Exclusion Rate

Typically 30-50% of full-text articles are excluded:

- Wrong outcomes: ~15%
- Wrong intervention/comparator: ~10%
- Duplicate publication: ~10%
- Insufficient data: ~5%
- Other reasons: ~5%

**Expected final inclusion**: {{EXPECTED_FINAL_INCLUDE}} studies

---

## ⏱️ Time Planning

| Task                          | Time        | Cumulative   |
| ----------------------------- | ----------- | ------------ |
| Unpaywall query + analysis    | 1 hour      | 1 hour       |
| Automatic PDF download        | 2-3 hours   | 3-4 hours    |
| Manual PDF retrieval          | 5-10 hours  | 8-14 hours   |
| PDF organization              | 1 hour      | 9-15 hours   |
| Full-text review (Reviewer 1) | 10-15 hours | 19-30 hours  |
| Full-text review (Reviewer 2) | 10-15 hours | (concurrent) |
| Conflict resolution           | 2-3 hours   | 21-33 hours  |
| Final documentation           | 1-2 hours   | 22-35 hours  |

**Total**: 22-35 hours per reviewer (distributed over 2-3 weeks)

---

## 📝 Handling Special Cases

### Case 1: Multiple reports from same trial

Example: KEYNOTE-522 has primary analysis (2020), 3-year follow-up (2022), 5-year follow-up (2024)

**Decision**:

- Include all reports
- Mark as "same trial, different time points"
- Extract data from each for relevant outcomes

### Case 2: Conference abstract + full publication

**Decision**:

- Include full publication
- Exclude conference abstract as "duplicate"
- Unless abstract has unique data not in full publication

### Case 3: Subgroup analysis / post-hoc analysis

**Decision**:

- If reports new relevant subgroup data: Include
- If only repeats main analysis: Exclude as "duplicate"
- Mark relationship to main publication

### Case 4: Pooled analysis of multiple trials

**Decision**:

- If individual trial data available: Include original trials only
- If only pooled data: Include pooled analysis but note limitation

### Case 5: Unable to obtain PDF

**Decision**:

- Document as "unable to obtain full text"
- Report in PRISMA flow diagram
- Consider as limitation in discussion

---

## 📈 Quality Checks

### After PDF retrieval

1. **Check retrieval completeness**

```bash
# Count PDFs obtained
ls -1 04_fulltext/round-01/pdfs/*.pdf | wc -l

# Expected: 85-95% of {{FULLTEXT_COUNT}} studies
```

2. **Verify key studies obtained**

```bash
# Ensure all key studies have PDFs
ls 04_fulltext/round-01/pdfs/ | grep -i "{{KEY_STUDY_1}}\|{{KEY_STUDY_2}}"
```

### After full-text review

1. **Calculate inter-rater agreement**

```bash
cd /Users/htlin/meta-pipe/tooling/python

uv run ../../ma-screening-quality/scripts/dual_review_agreement.py \
  --file ../../projects/{{PROJECT_NAME}}/04_fulltext/round-01/fulltext_decisions.csv \
  --col-a reviewer_1_decision \
  --col-b reviewer_2_decision \
  --out ../../projects/{{PROJECT_NAME}}/04_fulltext/round-01/fulltext_agreement.md
```

Target: Cohen's kappa ≥0.70 (higher than title/abstract screening)

2. **Verify expected inclusion count**

Expected: {{EXPECTED_FINAL_INCLUDE}} studies
If much higher/lower: Review decisions for consistency

---

## 🎯 Success Criteria

### Must Achieve

- [ ] PDFs obtained for ≥90% of {{FULLTEXT_COUNT}} studies
- [ ] All key studies have PDFs
- [ ] All studies have full-text review decisions
- [ ] Cohen's kappa ≥0.70 (dual review)
- [ ] Final inclusion count: {{EXPECTED_FINAL_INCLUDE}} ± 30%
- [ ] All exclusions have documented reasons
- [ ] PRISMA flow diagram data complete

### Optional

- [ ] PDF naming convention followed consistently
- [ ] PDFs organized in included/excluded folders
- [ ] Duplicate publications identified and linked

---

## 📞 Need Help?

### Technical Issues

- **Unpaywall API not working**: Use browser extension method
- **PDF download fails**: Check network connection, try manual download
- **Cannot access institutional subscriptions**: Contact library help desk

### Retrieval Issues

- **Cannot find PDF anywhere**: Document as "unable to obtain", proceed with available studies
- **Author doesn't respond**: Wait 1 week, try co-authors, or alternative email
- **Paywall for key study**: Use inter-library loan or document request

### Review Issues

- **Uncertain about inclusion**: Mark as "uncertain", discuss with co-reviewer
- **Missing data in full text**: Include study but note limitation for extraction
- **Conflicting information**: Prioritize main publication over abstracts/presentations

---

## 📝 Next Phase Preview

After full-text review completion (expected 2-3 weeks), you will proceed to:

**Phase 5: Data Extraction** (Weeks 8-10)

- Create data extraction form
- Extract study characteristics
- Extract outcome data
- Assess risk of bias
- Expected time: 20-30 hours

---

## ✅ Start Now

**Immediate actions** (today):

1. **Run Unpaywall query** (1 hour)

```bash
cd /Users/htlin/meta-pipe/tooling/python
uv run ../../ma-fulltext-management/scripts/unpaywall_fetch_robust.py \
  --in-bib ../../projects/{{PROJECT_NAME}}/04_fulltext/round-01/fulltext_subset.bib \
  --out-csv ../../projects/{{PROJECT_NAME}}/04_fulltext/round-01/unpaywall_results.csv \
  --email "{{YOUR_EMAIL}}"
```

2. **Review Unpaywall summary** (15 min)

```bash
# Check how many PDFs are available as OA
cat 04_fulltext/round-01/unpaywall_summary.md
```

3. **Start downloading OA PDFs** (2-3 hours)

```bash
uv run ../../ma-fulltext-management/scripts/download_oa_pdfs.py \
  --in-csv ../../projects/{{PROJECT_NAME}}/04_fulltext/round-01/unpaywall_results.csv \
  --pdf-dir ../../projects/{{PROJECT_NAME}}/04_fulltext/round-01/pdfs
```

4. **Plan manual retrieval** (this week)
   - Identify non-OA studies from unpaywall results
   - Check institutional access for each
   - Contact authors for remaining studies

---

**Status**: ✅ Ready to start full-text retrieval
**Confidence level**: High (systematic approach, multiple retrieval methods)
**Next milestone**: Complete PDF retrieval (expected within 1 week)
**Overall project timeline**: {{PROJECT_TIMELINE}}

---

**Document version**: 1.0
**Date**: {{DATE}}
**Generated by**: Meta-analysis pipeline
