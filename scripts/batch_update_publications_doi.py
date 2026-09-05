#!/usr/bin/env python3
"""
Batch Publication DOI & Metadata Resolver for Conscious Brain Lab
Finds DOIs for publications, fetches canonical APA citations and BibTeX via Content Negotiation,
and updates content/publications/*.json while strictly preserving year_group,
preprint_url, code_url, topics, and publication IDs.
"""

import os
import sys
import glob
import json
import re
import time
import ssl
import html
import urllib.request
import urllib.parse
import difflib

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PUBS_DIR = os.path.join(BASE_DIR, "content", "publications")
USER_AGENT = "ConsciousBrainLabBot/1.0 (mailto:consciousbrainlab@gmail.com; https://github.com/conscious-brain-lab/website)"

# Create unverified SSL context for macOS certificate compatibility
SSL_CTX = ssl._create_unverified_context()

def clean_doi(raw):
    if not raw:
        return None
    raw = str(raw).strip()
    
    # Nature articles URL mapping to DOI (e.g. nature.com/articles/s41562-019-0531-8 -> 10.1038/s41562-019-0531-8)
    m_nat = re.search(r"nature\.com/articles/([a-zA-Z0-9.-]+)", raw)
    if m_nat:
        return f"10.1038/{m_nat.group(1)}"

    # Standard DOI pattern matching
    m = re.search(r"10\.\d{4,9}/[^\s\"'<>]+", raw)
    if m:
        doi = m.group(0).strip()
        # Strip trailing suffixes like /full, /abstract, /pdf, /long, etc.
        doi = re.sub(r"/(?:full|abstract|pdf|long|short)$", "", doi, flags=re.I)
        # Strip trailing punctuation, parens, brackets, quotes, slashes
        doi = re.sub(r"[)\].;,/\"'>]+$", "", doi)
        doi = doi.replace("%2F", "/").replace("%2f", "/")
        return doi.strip()
    return None

def normalize_text(text):
    if not text:
        return ""
    # Strip HTML tags
    t = re.sub(r"<[^>]+>", " ", text)
    # Strip non-alphanumeric
    t = re.sub(r"[^a-zA-Z0-9\s]", " ", t)
    # Collapse whitespace and lowercase
    return " ".join(t.lower().split())

def string_similarity(a, b):
    na = normalize_text(a)
    nb = normalize_text(b)
    if not na or not nb:
        return 0.0
    return difflib.SequenceMatcher(None, na, nb).ratio()

def find_existing_doi(pub):
    doi = clean_doi(pub.get("paper_url"))
    if doi: return doi
    doi = clean_doi(pub.get("doi"))
    if doi: return doi
    doi = clean_doi(pub.get("citation"))
    if doi: return doi
    doi = clean_doi(pub.get("bibtex"))
    if doi: return doi
    return None

def search_crossref_doi(citation, pub_id=""):
    clean_cit = re.sub(r"https?://[^\s]+|doi:\s*10\.[^\s]+", "", citation).strip()
    clean_cit = re.sub(r"[\r\n\t]+", " ", clean_cit)
    
    params = {"query.bibliographic": clean_cit[:250], "rows": 5}
    url = "https://api.crossref.org/works?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    try:
        with urllib.request.urlopen(req, context=SSL_CTX, timeout=12) as resp:
            data = json.load(resp)
    except Exception as e:
        return None, 0.0, f"Query error: {e}"

    items = data.get("message", {}).get("items", [])
    if not items:
        return None, 0.0, "No results from Crossref"

    norm_cit = normalize_text(citation)
    
    best_doi = None
    best_score = 0.0
    best_cand_title = ""

    for item in items:
        cand_titles = item.get("title", [])
        cand_title = cand_titles[0] if cand_titles else ""
        cand_doi = clean_doi(item.get("DOI"))
        if not cand_doi or not cand_title:
            continue

        norm_title = normalize_text(cand_title)
        if len(norm_title) < 8:
            continue

        if norm_title in norm_cit:
            score = 0.95
        else:
            score = difflib.SequenceMatcher(None, norm_title, norm_cit).ratio()
            title_words = set(norm_title.split())
            cit_words = set(norm_cit.split())
            overlap = len(title_words.intersection(cit_words)) / max(len(title_words), 1)
            score = max(score, overlap)

        cand_authors = item.get("author", [])
        cand_families = [a.get("family", "").lower() for a in cand_authors if a.get("family")]
        
        author_match = False
        for fam in cand_families:
            if fam and len(fam) > 2 and fam in norm_cit:
                author_match = True
                break

        if author_match and score >= 0.70:
            if score > best_score:
                best_score = score
                best_doi = cand_doi
                best_cand_title = cand_title

    if best_doi and best_score >= 0.70:
        return best_doi, best_score, best_cand_title

    return None, best_score, best_cand_title

def fetch_doi_metadata(doi):
    clean_d = clean_doi(doi)
    if not clean_d:
        return None, None

    doi_url = f"https://doi.org/{clean_d}"
    
    # 1. Fetch APA Citation via Content Negotiation
    req_apa = urllib.request.Request(
        doi_url, 
        headers={
            "Accept": "text/x-bibliography; style=apa",
            "User-Agent": USER_AGENT
        }
    )
    apa_cit = None
    try:
        with urllib.request.urlopen(req_apa, context=SSL_CTX, timeout=12) as resp:
            raw_cit = resp.read().decode("utf-8").strip()
            # Strip trailing URL / DOI from citation text
            cleaned_cit = re.sub(r"\s*(?:https?://(?:dx\.)?doi\.org/[^\s]+|https?://[^\s]+|doi:\s*10\.[^\s]+)\s*$", "", raw_cit, flags=re.I).strip()
            cleaned_cit = re.sub(r"[,;:]\s*$", "", cleaned_cit).strip()
            cleaned_cit = html.unescape(cleaned_cit)
            if cleaned_cit and not cleaned_cit.endswith("."):
                cleaned_cit += "."
            apa_cit = cleaned_cit
    except Exception as e:
        try:
            alt_url = f"https://api.crossref.org/works/{urllib.parse.quote(clean_d)}/transform/text/x-bibliography?style=apa"
            req_alt = urllib.request.Request(alt_url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req_alt, context=SSL_CTX, timeout=12) as resp:
                raw_cit = resp.read().decode("utf-8").strip()
                cleaned_cit = re.sub(r"\s*(?:https?://(?:dx\.)?doi\.org/[^\s]+|https?://[^\s]+|doi:\s*10\.[^\s]+)\s*$", "", raw_cit, flags=re.I).strip()
                cleaned_cit = re.sub(r"[,;:]\s*$", "", cleaned_cit).strip()
                cleaned_cit = html.unescape(cleaned_cit)
                if cleaned_cit and not cleaned_cit.endswith("."):
                    cleaned_cit += "."
                apa_cit = cleaned_cit
        except Exception as e2:
            print(f"    [!] Error fetching APA citation for {clean_d}: {e}")

    # 2. Fetch BibTeX via Content Negotiation
    req_bib = urllib.request.Request(
        doi_url, 
        headers={
            "Accept": "application/x-bibtex",
            "User-Agent": USER_AGENT
        }
    )
    bibtex = None
    try:
        with urllib.request.urlopen(req_bib, context=SSL_CTX, timeout=12) as resp:
            raw_bib = resp.read().decode("utf-8").strip()
            formatted_bib = re.sub(r",\s*([a-zA-Z0-9_-]+)\s*=", r",\n  \1 =", raw_bib)
            formatted_bib = re.sub(r"}\s*$", r"\n}", formatted_bib)
            formatted_bib = html.unescape(formatted_bib)
            bibtex = formatted_bib
    except Exception as e:
        try:
            alt_url = f"https://api.crossref.org/works/{urllib.parse.quote(clean_d)}/transform/application/x-bibtex"
            req_alt = urllib.request.Request(alt_url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req_alt, context=SSL_CTX, timeout=12) as resp:
                raw_bib = resp.read().decode("utf-8").strip()
                formatted_bib = re.sub(r",\s*([a-zA-Z0-9_-]+)\s*=", r",\n  \1 =", raw_bib)
                formatted_bib = re.sub(r"}\s*$", r"\n}", formatted_bib)
                formatted_bib = html.unescape(formatted_bib)
                bibtex = formatted_bib
        except Exception as e2:
            print(f"    [!] Error fetching BibTeX for {clean_d}: {e}")

    return apa_cit, bibtex

def run_batch(apply_changes=False):
    files = sorted(glob.glob(os.path.join(PUBS_DIR, "*.json")))
    print(f"==================================================")
    print(f"Starting Publication DOI & Metadata Batch Processor")
    print(f"Total Publications: {len(files)}")
    print(f"Mode: {'APPLY CHANGES' if apply_changes else 'DRY RUN (Preview)'}")
    print(f"==================================================\n")

    stats = {
        "already_had_doi": 0,
        "newly_discovered_doi": 0,
        "could_not_find_doi": 0,
        "citation_updated": 0,
        "bibtex_updated": 0,
        "skipped_safety_mismatch": 0
    }

    updated_pubs = []

    for idx, f in enumerate(files, 1):
        with open(f, "r", encoding="utf-8") as fp:
            pub = json.load(fp)

        pid = pub.get("id")
        orig_cit = pub.get("citation", "")
        
        print(f"[{idx}/{len(files)}] Processing {pid}...")

        doi = find_existing_doi(pub)
        discovered = False

        if doi:
            stats["already_had_doi"] += 1
            print(f"  -> Existing DOI: {doi}")
        else:
            print(f"  -> No DOI in fields. Searching Crossref for: '{orig_cit[:70]}'...")
            cand_doi, score, cand_title = search_crossref_doi(orig_cit, pid)
            if cand_doi and score >= 0.70:
                doi = clean_doi(cand_doi)
                discovered = True
                stats["newly_discovered_doi"] += 1
                print(f"  -> ✓ Found DOI via search: {doi} (score: {score:.2f})")
                print(f"     Matched: {cand_title[:70]}")
            else:
                stats["could_not_find_doi"] += 1
                print(f"  -> ✗ No confident DOI match found (best score: {score:.2f}: '{cand_title[:50]}')")

        if not doi:
            continue

        time.sleep(0.15)
        new_cit, new_bib = fetch_doi_metadata(doi)

        should_update_cit = False
        if new_cit:
            words_orig = set(normalize_text(orig_cit).split())
            words_new = set(normalize_text(new_cit).split())
            overlap = len(words_orig.intersection(words_new)) / max(len(words_orig), 1)
            
            if overlap >= 0.35 or string_similarity(orig_cit, new_cit) >= 0.35:
                should_update_cit = True
            else:
                print(f"  -> ⚠️ Citation mismatch check warning (overlap: {overlap:.2f}):\n     Orig: '{orig_cit[:70]}'\n     New:  '{new_cit[:70]}'\n     Keeping original citation.")
                stats["skipped_safety_mismatch"] += 1

        canonical_doi_url = f"https://doi.org/{doi}"
        has_changes = False

        # Strictly preserve: id, year_group, preprint_url, code_url, topics
        if pub.get("paper_url") != canonical_doi_url:
            pub["paper_url"] = canonical_doi_url
            has_changes = True

        if pub.get("doi") != canonical_doi_url:
            pub["doi"] = canonical_doi_url
            has_changes = True

        if should_update_cit and new_cit and pub.get("citation") != new_cit:
            pub["citation"] = new_cit
            stats["citation_updated"] += 1
            has_changes = True

        if new_bib and pub.get("bibtex") != new_bib:
            pub["bibtex"] = new_bib
            stats["bibtex_updated"] += 1
            has_changes = True

        if has_changes:
            updated_pubs.append((f, pub))
            if apply_changes:
                with open(f, "w", encoding="utf-8") as fp:
                    json.dump(pub, fp, indent=2, ensure_ascii=False)
                    fp.write("\n")
                print(f"  -> ✓ Saved updates to {os.path.basename(f)}")
            else:
                print(f"  -> [Preview] Would update {os.path.basename(f)}")

    print(f"\n==================================================")
    print(f"Batch Processing Summary:")
    print(f"Total Publications: {len(files)}")
    print(f"Already had DOIs: {stats['already_had_doi']}")
    print(f"Newly discovered DOIs: {stats['newly_discovered_doi']}")
    print(f"Could not find DOIs: {stats['could_not_find_doi']}")
    print(f"Citations updated: {stats['citation_updated']}")
    print(f"BibTeX updated: {stats['bibtex_updated']}")
    print(f"Total files updated: {len(updated_pubs)}")
    print(f"==================================================")

    if apply_changes:
        print("\nRe-syncing data/publications.json...")
        sys.path.insert(0, os.path.dirname(__file__))
        import local_cms_server
        local_cms_server.sync_collections_to_data()
        print("✓ All updates applied and synced successfully!")

if __name__ == "__main__":
    apply = "--apply" in sys.argv
    run_batch(apply_changes=apply)
