#!/usr/bin/env python3
"""
Test database API connections.
Run with: uv run tests/test_db_connections.py

Requires .env file with API keys.
"""

import os
import sys
from pathlib import Path

# Load .env from project root
ROOT = Path(__file__).parent.parent
ENV_FILE = ROOT / ".env"


def load_env():
    """Load environment variables from .env file."""
    if not ENV_FILE.exists():
        print(f"⚠️  No .env file found at {ENV_FILE}")
        print("   Copy .env.example to .env and add your API keys")
        return False

    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())
    return True


def test_pubmed():
    """Test PubMed E-utilities connection."""
    print("\n" + "=" * 50)
    print("TEST: PubMed E-utilities")
    print("=" * 50)

    try:
        from Bio import Entrez
    except ImportError:
        print("❌ SKIP: biopython not installed (uv add biopython)")
        return None

    api_key = os.environ.get("PUBMED_API_KEY", "")
    email = os.environ.get("UNPAYWALL_EMAIL", "test@example.com")

    Entrez.email = email
    if api_key:
        Entrez.api_key = api_key
        print(f"   API Key: {api_key[:8]}...")
    else:
        print("   API Key: Not set (rate limited to 3 req/sec)")

    try:
        # Simple search
        handle = Entrez.esearch(
            db="pubmed",
            term="cognitive behavioral therapy depression",
            retmax=1,
        )
        results = Entrez.read(handle)
        handle.close()

        count = int(results.get("Count", 0))
        print(f"   Search results: {count:,} records found")

        if count > 0:
            print("✅ PASSED: PubMed connection OK")
            return True
        else:
            print("⚠️  WARNING: Search returned 0 results")
            return True

    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_scopus():
    """Test Scopus API connection."""
    print("\n" + "=" * 50)
    print("TEST: Scopus API (Elsevier)")
    print("=" * 50)

    try:
        import requests
    except ImportError:
        print("❌ SKIP: requests not installed")
        return None

    api_key = os.environ.get("SCOPUS_API_KEY", "")
    inst_token = os.environ.get("SCOPUS_INST_TOKEN", "")

    if not api_key:
        print("❌ SKIP: SCOPUS_API_KEY not set")
        return None

    print(f"   API Key: {api_key[:8]}...")
    if inst_token:
        print(f"   Inst Token: {inst_token[:8]}...")

    headers = {
        "X-ELS-APIKey": api_key,
        "Accept": "application/json",
    }
    if inst_token:
        headers["X-ELS-Insttoken"] = inst_token

    try:
        # Simple search
        url = "https://api.elsevier.com/content/search/scopus"
        params = {
            "query": "TITLE(cognitive behavioral therapy) AND TITLE(depression)",
            "count": 1,
        }

        response = requests.get(url, headers=headers, params=params, timeout=30)

        if response.status_code == 200:
            data = response.json()
            total = data.get("search-results", {}).get("opensearch:totalResults", "0")
            print(f"   Search results: {total} records found")
            print("✅ PASSED: Scopus connection OK")
            return True
        elif response.status_code == 401:
            print("❌ FAILED: Invalid API key or unauthorized")
            return False
        elif response.status_code == 403:
            print("❌ FAILED: Access forbidden (check subscription/inst token)")
            return False
        else:
            print(f"❌ FAILED: HTTP {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False

    except requests.Timeout:
        print("❌ FAILED: Request timeout")
        return False
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_zotero():
    """Test Zotero API connection."""
    print("\n" + "=" * 50)
    print("TEST: Zotero API")
    print("=" * 50)

    try:
        import requests
    except ImportError:
        print("❌ SKIP: requests not installed")
        return None

    api_key = os.environ.get("ZOTERO_API_KEY", "")
    library_type = os.environ.get("ZOTERO_LIBRARY_TYPE", "user")
    library_id = os.environ.get("ZOTERO_LIBRARY_ID", "")

    if not api_key:
        print("❌ SKIP: ZOTERO_API_KEY not set")
        return None

    if not library_id:
        print("❌ SKIP: ZOTERO_LIBRARY_ID not set")
        return None

    print(f"   API Key: {api_key[:8]}...")
    print(f"   Library: {library_type}/{library_id}")

    headers = {
        "Zotero-API-Key": api_key,
    }

    try:
        # Get library info
        if library_type == "user":
            url = f"https://api.zotero.org/users/{library_id}/items"
        else:
            url = f"https://api.zotero.org/groups/{library_id}/items"

        response = requests.get(
            url,
            headers=headers,
            params={"limit": 1},
            timeout=30,
        )

        if response.status_code == 200:
            total = response.headers.get("Total-Results", "unknown")
            print(f"   Library items: {total}")
            print("✅ PASSED: Zotero connection OK")
            return True
        elif response.status_code == 403:
            print("❌ FAILED: Access forbidden (check API key permissions)")
            return False
        elif response.status_code == 404:
            print("❌ FAILED: Library not found (check library ID)")
            return False
        else:
            print(f"❌ FAILED: HTTP {response.status_code}")
            return False

    except requests.Timeout:
        print("❌ FAILED: Request timeout")
        return False
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_unpaywall():
    """Test Unpaywall API connection."""
    print("\n" + "=" * 50)
    print("TEST: Unpaywall API")
    print("=" * 50)

    try:
        import requests
    except ImportError:
        print("❌ SKIP: requests not installed")
        return None

    email = os.environ.get("UNPAYWALL_EMAIL", "")

    if not email:
        print("❌ SKIP: UNPAYWALL_EMAIL not set")
        return None

    print(f"   Email: {email}")

    try:
        # Test with a known open access DOI
        test_doi = "10.1371/journal.pmed.0020124"  # Famous OA paper
        url = f"https://api.unpaywall.org/v2/{test_doi}"

        response = requests.get(
            url,
            params={"email": email},
            timeout=30,
        )

        if response.status_code == 200:
            data = response.json()
            is_oa = data.get("is_oa", False)
            print(f"   Test DOI: {test_doi}")
            print(f"   Is OA: {is_oa}")
            print("✅ PASSED: Unpaywall connection OK")
            return True
        elif response.status_code == 422:
            print("❌ FAILED: Invalid email format")
            return False
        else:
            print(f"❌ FAILED: HTTP {response.status_code}")
            return False

    except requests.Timeout:
        print("❌ FAILED: Request timeout")
        return False
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def main():
    """Run all connection tests."""
    print("\n" + "=" * 50)
    print("DATABASE CONNECTION TESTS")
    print("=" * 50)

    if not load_env():
        print("\n⚠️  Running without .env file")

    tests = [
        ("PubMed", test_pubmed),
        ("Scopus", test_scopus),
        ("Zotero", test_zotero),
        ("Unpaywall", test_unpaywall),
    ]

    results = []
    for name, test_fn in tests:
        try:
            result = test_fn()
            results.append((name, result))
        except Exception as e:
            print(f"❌ EXCEPTION: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)

    for name, result in results:
        if result is True:
            status = "✅ OK"
        elif result is False:
            status = "❌ FAILED"
        else:
            status = "⏭️  SKIPPED"
        print(f"  {status:12} {name}")

    passed = sum(1 for _, r in results if r is True)
    failed = sum(1 for _, r in results if r is False)
    skipped = sum(1 for _, r in results if r is None)

    print(f"\nTotal: {passed} passed, {failed} failed, {skipped} skipped")

    # Return failure if any test failed (not skipped)
    return 1 if failed > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
