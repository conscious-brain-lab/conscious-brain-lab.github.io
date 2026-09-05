#!/usr/bin/env python3
import json
import os
import re
import time
import urllib.request
import urllib.parse
import ssl
import html

ctx = ssl._create_unverified_context()
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,application/json;q=0.8,*/*;q=0.7',
    'Accept-Language': 'en-US,en;q=0.9'
}

def clean_doi(doi_str):
    if not doi_str:
        return ''
    m = re.search(r'10\.\d{4,9}/[-._;()/:A-Za-z0-9]+', doi_str)
    if m:
        return m.group(0).rstrip('.')
    return doi_str.replace('https://doi.org/', '').replace('http://doi.org/', '').strip()

def clean_text(txt):
    if not txt:
        return ''
    # unescape HTML entities
    txt = html.unescape(txt)
    # strip HTML tags
    txt = re.sub(r'<[^>]+>', ' ', txt)
    txt = re.sub(r'\s+', ' ', txt).strip()
    return txt

def fetch_doi_page(doi_or_url):
    """Directly follows the DOI or paper URL to the landing page and extracts the abstract."""
    url = doi_or_url if doi_or_url.startswith('http') else f'https://doi.org/{doi_or_url}'
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=4) as resp:
            content_type = resp.headers.get('Content-Type', '')
            # read first 250KB max to be fast
            raw = resp.read(250000).decode('utf-8', errors='ignore')
            
            # 1. citation_abstract meta tag (HighWire / Google Scholar standard across almost all academic publishers)
            m = re.search(r'<meta\s+name=[\"\']citation_abstract[\"\']\s+content=[\"\'](.*?)[\"\']', raw, re.I | re.S)
            if not m:
                m = re.search(r'<meta\s+content=[\"\'](.*?)[\"\']\s+name=[\"\']citation_abstract[\"\']', raw, re.I | re.S)
            if m:
                val = clean_text(m.group(1))
                if len(val) > 40:
                    return val, 'doi_citation_abstract'

            # 2. dc.description or description meta tag
            m = re.search(r'<meta\s+name=[\"\'](?:dc\.description|description)[\"\']\s+content=[\"\'](.*?)[\"\']', raw, re.I | re.S)
            if not m:
                m = re.search(r'<meta\s+content=[\"\'](.*?)[\"\']\s+name=[\"\'](?:dc\.description|description)[\"\']', raw, re.I | re.S)
            if m:
                val = clean_text(m.group(1))
                if len(val) > 60 and not val.lower().startswith('read the latest article'):
                    return val, 'doi_description_meta'

            # 3. og:description meta tag
            m = re.search(r'<meta\s+property=[\"\']og:description[\"\']\s+content=[\"\'](.*?)[\"\']', raw, re.I | re.S)
            if not m:
                m = re.search(r'<meta\s+content=[\"\'](.*?)[\"\']\s+property=[\"\']og:description[\"\']', raw, re.I | re.S)
            if m:
                val = clean_text(m.group(1))
                if len(val) > 60 and not val.lower().startswith('read the latest article'):
                    return val, 'doi_og_description'

            # 4. Common HTML abstract block
            m = re.search(r'<(?:section|div)[^>]*(?:class|id)=[\"\'][^\"\']*(?:abstract|Abstract)[^\"\']*[\"\'][^>]*>(.*?)</(?:section|div)>', raw, re.I | re.S)
            if m:
                val = clean_text(m.group(1))
                # remove "Abstract" label if at start
                val = re.sub(r'^(?:abstract|summary)\s*', '', val, flags=re.I)
                if len(val) > 60:
                    return val, 'doi_html_abstract'
    except Exception as e:
        pass
    return None, None

def fetch_europe_pmc(doi):
    try:
        url = f'https://europepmc.org/api/rest/search?query=DOI:"{doi}"&format=json&resultType=core'
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, context=ctx, timeout=3) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            results = data.get('resultList', {}).get('result', [])
            if results:
                res = results[0]
                ab = clean_text(res.get('abstractText'))
                if ab:
                    return {
                        'title': res.get('title'),
                        'abstract': ab,
                        'journal': res.get('journalTitle'),
                        'keywords': res.get('keywordList', {}).get('keyword', [])
                    }
    except Exception:
        pass
    return None

def fetch_biorxiv(doi):
    try:
        url = f'https://api.biorxiv.org/details/biorxiv/{doi}'
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, context=ctx, timeout=3) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            collection = data.get('collection', [])
            if collection:
                res = collection[-1]
                ab = clean_text(res.get('abstract'))
                if ab:
                    return {
                        'title': res.get('title'),
                        'abstract': ab
                    }
    except Exception:
        pass
    return None

def fetch_semantic_scholar(doi):
    try:
        url = f'https://api.semanticscholar.org/graph/v1/paper/{doi}?fields=title,abstract'
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, context=ctx, timeout=3) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            ab = clean_text(data.get('abstract'))
            if ab:
                return {
                    'title': data.get('title'),
                    'abstract': ab
                }
    except Exception:
        pass
    return None

def fetch_crossref(doi):
    try:
        url = f'https://api.crossref.org/works/{doi}'
        req = urllib.request.Request(url, headers={'User-Agent': 'CBL-Auditor/1.0 (mailto:info@consciousbrainlab.com)'})
        with urllib.request.urlopen(req, context=ctx, timeout=3) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            msg = data.get('message', {})
            ab = clean_text(msg.get('abstract', ''))
            if ab:
                titles = msg.get('title', [])
                return {
                    'title': titles[0] if titles else '',
                    'abstract': ab
                }
    except Exception:
        pass
    return None

def main():
    with open('scripts/audit/publications_catalog.json') as f:
        catalog = json.load(f)

    out_file = 'scripts/audit/publications_with_abstracts.json'
    existing = {}
    if os.path.exists(out_file):
        try:
            with open(out_file) as f:
                for item in json.load(f):
                    if item.get('abstract'):
                        existing[item['id']] = item
        except Exception:
            pass

    results = []
    print(f"Loaded {len(existing)} existing abstracts. Starting audit for {len(catalog)} publications...", flush=True)

    for i, item in enumerate(catalog):
        pub_id = item['id']
        raw_doi = item['doi']
        doi = clean_doi(raw_doi)

        if pub_id in existing and len(existing[pub_id].get('abstract', '')) > 40:
            print(f"[{i+1}/{len(catalog)}] {pub_id}: CACHED ({existing[pub_id].get('source')})", flush=True)
            results.append(existing[pub_id])
            continue

        print(f"[{i+1}/{len(catalog)}] Fetching {pub_id}: DOI={doi}", flush=True)

        meta = {
            'id': pub_id,
            'doi': doi,
            'title': item['title'],
            'journal': item['journal'],
            'year': item['year'],
            'citation': item['citation'],
            'existing_topics': item['topics'],
            'abstract': '',
            'source': '',
            'keywords': []
        }

        # Strategy 1: Follow DOI page directly (as suggested by the user!)
        if raw_doi:
            ab, src = fetch_doi_page(raw_doi)
            if ab:
                meta['abstract'] = ab
                meta['source'] = src

        # Strategy 2: bioRxiv API
        if not meta['abstract'] and '1101' in doi:
            bio = fetch_biorxiv(doi)
            if bio and bio.get('abstract'):
                meta['abstract'] = bio['abstract']
                meta['source'] = 'biorxiv'

        # Strategy 3: Semantic Scholar
        if not meta['abstract'] and doi:
            ss = fetch_semantic_scholar(doi)
            if ss and ss.get('abstract'):
                meta['abstract'] = ss['abstract']
                meta['source'] = 'semanticscholar'

        # Strategy 4: Europe PMC
        if not meta['abstract'] and doi:
            epmc = fetch_europe_pmc(doi)
            if epmc and epmc.get('abstract'):
                meta['abstract'] = epmc['abstract']
                meta['source'] = 'europepmc'
                meta['keywords'] = epmc.get('keywords', [])

        # Strategy 5: Crossref
        if not meta['abstract'] and doi:
            cr = fetch_crossref(doi)
            if cr and cr.get('abstract'):
                meta['abstract'] = cr['abstract']
                meta['source'] = 'crossref'

        has_abs = bool(meta['abstract'])
        print(f"    -> Status: {'FOUND (' + meta['source'] + ', len=' + str(len(meta['abstract'])) + ')' if has_abs else 'NOT FOUND'}", flush=True)
        results.append(meta)

        # Incremental save so nothing is lost!
        with open(out_file, 'w') as out:
            json.dump(results, out, indent=2)

        time.sleep(0.1)

    found_count = sum(1 for r in results if r.get('abstract'))
    print(f"\nCompleted! Found abstracts for {found_count}/{len(results)} publications.", flush=True)
    print(f"Saved to {out_file}", flush=True)

if __name__ == '__main__':
    main()
