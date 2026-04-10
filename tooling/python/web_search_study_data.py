#!/usr/bin/env python3
"""Search PubMed and ClinicalTrials.gov for study data (web-based extraction)."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from xml.etree import ElementTree


def _load_env() -> None:
    """Load .env for email configuration."""
    env_utils = (
        Path(__file__).resolve().parent.parent
        / "ma-search-bibliography"
        / "scripts"
        / "env_utils.py"
    )
    if env_utils.exists():
        import importlib.util

        spec = importlib.util.spec_from_file_location("env_utils", env_utils)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.load_dotenv()


def _get_email() -> str:
    """Get email from env or fail."""
    email = os.environ.get("ENTREZ_EMAIL") or os.environ.get("EMAIL") or ""
    if not email:
        raise SystemExit(
            "Email required for PubMed Entrez API. "
            "Set ENTREZ_EMAIL in .env or environment."
        )
    return email


# --- PubMed Entrez helpers ---

ENTREZ_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
ENTREZ_DELAY = 0.34  # seconds between calls (NCBI rate limit: 3/s)


def _entrez_fetch_by_pmid(pmid: str, email: str) -> dict:
    """Fetch article metadata from PubMed by PMID."""
    url = (
        f"{ENTREZ_BASE}/efetch.fcgi?"
        f"db=pubmed&id={pmid}&rettype=xml&retmode=xml&email={email}"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "meta-pipe/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            xml_bytes = resp.read()
        return _parse_pubmed_xml(xml_bytes)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        return {"error": str(exc)}


def _entrez_search_by_title(title: str, email: str) -> str | None:
    """Search PubMed for a PMID by title."""
    import urllib.parse

    query = urllib.parse.quote(title[:200])
    url = (
        f"{ENTREZ_BASE}/esearch.fcgi?"
        f"db=pubmed&term={query}&retmax=1&retmode=json&email={email}"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "meta-pipe/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        ids = data.get("esearchresult", {}).get("idlist", [])
        return ids[0] if ids else None
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
        return None


def _parse_pubmed_xml(xml_bytes: bytes) -> dict:
    """Parse PubMed XML into a flat dict of useful fields."""
    result: dict = {}
    try:
        root = ElementTree.fromstring(xml_bytes)
    except ElementTree.ParseError:
        return {"error": "XML parse error"}

    article = root.find(".//MedlineCitation/Article")
    if article is None:
        return {"error": "No article found in XML"}

    # Title
    title_el = article.find("ArticleTitle")
    if title_el is not None and title_el.text:
        result["title"] = title_el.text

    # Abstract
    abstract_parts = article.findall("Abstract/AbstractText")
    if abstract_parts:
        result["abstract"] = " ".join((p.text or "") for p in abstract_parts).strip()

    # Journal
    journal_el = article.find("Journal/Title")
    if journal_el is not None and journal_el.text:
        result["journal"] = journal_el.text

    # Year
    year_el = article.find("Journal/JournalIssue/PubDate/Year")
    if year_el is not None and year_el.text:
        result["publication_year"] = year_el.text

    # DOI
    for aid in root.findall(".//ArticleIdList/ArticleId"):
        if aid.get("IdType") == "doi" and aid.text:
            result["doi"] = aid.text
        if aid.get("IdType") == "pubmed" and aid.text:
            result["pmid"] = aid.text

    # Authors
    authors = article.findall("AuthorList/Author")
    if authors:
        names = []
        for a in authors:
            last = a.findtext("LastName") or ""
            init = a.findtext("Initials") or ""
            if last:
                names.append(f"{last} {init}".strip())
        result["authors"] = "; ".join(names)
        if names:
            result["first_author"] = names[0]

    # MeSH terms
    mesh_terms = root.findall(".//MeshHeadingList/MeshHeading/DescriptorName")
    if mesh_terms:
        result["mesh_terms"] = [m.text for m in mesh_terms if m.text]

    # Keywords
    kw_els = root.findall(".//KeywordList/Keyword")
    if kw_els:
        result["keywords"] = [k.text for k in kw_els if k.text]

    # Registry (DataBank)
    acc = root.find(".//DataBankList/DataBank/AccessionNumberList/AccessionNumber")
    if acc is not None and acc.text:
        result["nct_number"] = acc.text

    return result


# --- ClinicalTrials.gov v2 API ---

CTGOV_BASE = "https://clinicaltrials.gov/api/v2/studies"
CTGOV_DELAY = 1.0  # seconds between calls


def _ctgov_fetch(nct_id: str) -> dict:
    """Fetch study record from ClinicalTrials.gov v2 API."""
    url = f"{CTGOV_BASE}/{nct_id}?format=json"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "meta-pipe/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        return _parse_ctgov_v2(data)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        return {"error": str(exc)}


def _parse_ctgov_v2(data: dict) -> dict:
    """Extract useful fields from ClinicalTrials.gov v2 response."""
    result: dict = {}
    proto = data.get("protocolSection", {})

    ident = proto.get("identificationModule", {})
    result["nct_number"] = ident.get("nctId", "")
    result["official_title"] = ident.get("officialTitle", "")
    result["brief_title"] = ident.get("briefTitle", "")

    org = ident.get("organization", {})
    result["sponsor"] = org.get("fullName", "")

    design = proto.get("designModule", {})
    result["study_type"] = design.get("studyType", "")
    phases = design.get("phases", [])
    result["phase"] = ", ".join(phases) if phases else ""

    enrollment = design.get("enrollmentInfo", {})
    result["enrollment_count"] = enrollment.get("count")

    arms = proto.get("armsInterventionsModule", {})
    arm_groups = arms.get("armGroups", [])
    result["arms"] = [
        {"label": a.get("label", ""), "type": a.get("type", "")} for a in arm_groups
    ]

    interventions = arms.get("interventions", [])
    result["interventions"] = [
        {"name": i.get("name", ""), "type": i.get("type", "")} for i in interventions
    ]

    eligibility = proto.get("eligibilityModule", {})
    result["eligibility_criteria"] = eligibility.get("eligibilityCriteria", "")

    dates = proto.get("statusModule", {})
    result["start_date"] = dates.get("startDateStruct", {}).get("date", "")
    result["completion_date"] = dates.get("completionDateStruct", {}).get("date", "")

    return result


def process_study(record: dict, email: str, log_lines: list[str]) -> dict:
    """Gather data for a single study from web sources."""
    rid = record.get("record_id", "unknown")
    result: dict = {
        "record_id": rid,
        "sources": [],
        "pubmed": {},
        "ctgov": {},
    }

    pmid = record.get("pmid", "").strip()
    doi = record.get("doi", "").strip()
    title = record.get("title", "").strip()

    # --- PubMed ---
    if pmid:
        log_lines.append(f"  PubMed fetch PMID={pmid}")
        result["pubmed"] = _entrez_fetch_by_pmid(pmid, email)
        result["sources"].append("pubmed_pmid")
        time.sleep(ENTREZ_DELAY)
    elif title:
        log_lines.append(f"  PubMed search by title")
        found_pmid = _entrez_search_by_title(title, email)
        time.sleep(ENTREZ_DELAY)
        if found_pmid:
            result["pubmed"] = _entrez_fetch_by_pmid(found_pmid, email)
            result["sources"].append("pubmed_title_search")
            time.sleep(ENTREZ_DELAY)
        else:
            log_lines.append(f"  PubMed: no result for title search")

    # --- ClinicalTrials.gov ---
    nct = record.get("nct_number", "").strip()
    if not nct:
        nct = result.get("pubmed", {}).get("nct_number", "")
    if nct and nct.upper().startswith("NCT"):
        log_lines.append(f"  CTgov fetch NCT={nct}")
        result["ctgov"] = _ctgov_fetch(nct)
        result["sources"].append("ctgov")
        time.sleep(CTGOV_DELAY)

    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Search PubMed and ClinicalTrials.gov for study data"
    )
    parser.add_argument("--manifest", required=True, help="Input manifest CSV")
    parser.add_argument(
        "--data-dict", default=None, help="Data dictionary (for reference)"
    )
    parser.add_argument("--out-jsonl", required=True, help="Output JSONL with web data")
    parser.add_argument("--out-log", required=True, help="Output log file")
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    out_jsonl = Path(args.out_jsonl)
    out_log = Path(args.out_log)

    if not manifest_path.exists():
        raise SystemExit(f"Manifest not found: {manifest_path}")

    _load_env()
    email = _get_email()

    # Read manifest
    with manifest_path.open(newline="", encoding="utf-8") as fh:
        records = list(csv.DictReader(fh))

    if not records:
        raise SystemExit("Manifest is empty")

    print(f"Processing {len(records)} studies")
    print(f"Email: {email}")
    print()

    log_lines: list[str] = [f"Web search log — {len(records)} studies", ""]
    results: list[dict] = []

    for i, record in enumerate(records, 1):
        rid = record.get("record_id", "unknown")
        print(f"[{i:2d}/{len(records)}] {rid}")
        log_lines.append(f"[{i}/{len(records)}] {rid}")

        result = process_study(record, email, log_lines)
        sources = result.get("sources", [])
        print(f"         Sources: {', '.join(sources) if sources else 'none'}")
        log_lines.append(f"  Sources: {', '.join(sources) if sources else 'none'}")
        log_lines.append("")

        results.append(result)

    # Write outputs
    out_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with out_jsonl.open("w", encoding="utf-8") as fh:
        for r in results:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    out_log.parent.mkdir(parents=True, exist_ok=True)
    out_log.write_text("\n".join(log_lines) + "\n", encoding="utf-8")

    # Summary
    with_pubmed = sum(
        1 for r in results if r.get("pubmed") and "error" not in r["pubmed"]
    )
    with_ctgov = sum(1 for r in results if r.get("ctgov") and "error" not in r["ctgov"])
    print()
    print(f"PubMed data: {with_pubmed}/{len(results)}")
    print(f"CTgov data:  {with_ctgov}/{len(results)}")
    print(f"Output: {out_jsonl}")


if __name__ == "__main__":
    main()
