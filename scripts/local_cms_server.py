#!/usr/bin/env python3
"""
Decap CMS Local Backend Proxy Server
Emulates decap-server on port 8081 for 100% offline, local CMS editing.
Automatically synchronizes content/ collections back into data/*.json for the frontend.
"""

import http.server
import socketserver
import json
import os
import glob
import hashlib
import base64
import urllib.request
import re

PORT = 8081
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()

def sha256_str(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def normalize_path(p):
    return p.replace("\\", "/").lstrip("/")

def full_path(rel_path):
    clean = normalize_path(rel_path)
    return os.path.join(BASE_DIR, clean)

def sync_collections_to_data():
    """Compiles content/ files into data/*.json so frontend immediately updates."""
    # Members sync
    members_dir = os.path.join(BASE_DIR, "content", "members")
    if os.path.exists(members_dir):
        all_members = []
        for f in sorted(glob.glob(os.path.join(members_dir, "*.json"))):
            try:
                with open(f, "r", encoding="utf-8") as mf:
                    all_members.append(json.load(mf))
            except Exception as e:
                print(f"Error reading {f}: {e}")
        
        # Sort members: PIs first, current team, then alumni; by explicit order, then name
        cat_order = {"pi": 1, "postdoc": 2, "phd": 3, "alumni": 4}
        def member_sort_key(m):
            is_alumni = 1 if m.get("status") == "alumni" else 0
            category_rank = cat_order.get(m.get("category", "phd"), 99)
            try:
                display_order = int(m.get("order", 99))
            except Exception:
                display_order = 99
            name = m.get("name", "")
            return (is_alumni, category_rank, display_order, name)

        all_members.sort(key=member_sort_key)
        
        data_members_path = os.path.join(BASE_DIR, "data", "members.json")
        with open(data_members_path, "w", encoding="utf-8") as df:
            json.dump(all_members, df, indent=2, ensure_ascii=False)
        print(f"✓ Synced {len(all_members)} members to data/members.json")

    # News sync
    news_dir = os.path.join(BASE_DIR, "content", "news")
    if os.path.exists(news_dir):
        all_news = []
        for f in sorted(glob.glob(os.path.join(news_dir, "*.json"))):
            try:
                with open(f, "r", encoding="utf-8") as nf:
                    all_news.append(json.load(nf))
            except Exception as e:
                print(f"Error reading {f}: {e}")
        
        data_news_path = os.path.join(BASE_DIR, "data", "news.json")
        with open(data_news_path, "w", encoding="utf-8") as df:
            json.dump(all_news, df, indent=2, ensure_ascii=False)
        print(f"✓ Synced {len(all_news)} news items to data/news.json")

    # Publications sync
    pubs_dir = os.path.join(BASE_DIR, "content", "publications")
    if os.path.exists(pubs_dir):
        all_pubs = []
        for f in sorted(glob.glob(os.path.join(pubs_dir, "*.json"))):
            try:
                with open(f, "r", encoding="utf-8") as pf:
                    all_pubs.append(json.load(pf))
            except Exception as e:
                print(f"Error reading {f}: {e}")
        
        # Sort publications: Preprint/in review first, then year descending
        def pub_sort_key(p):
            yg = str(p.get("year_group", "")).strip()
            if any(k in yg.lower() for k in ["preprint", "review", "rxiv", "submitted"]):
                return (0, 9999)
            m = re.search(r"\b(19\d\d|20\d\d)\b", yg) or re.search(r"\b(19\d\d|20\d\d)\b", str(p.get("citation", "")))
            if m:
                return (1, -int(m.group(1)))
            return (2, 0)

        all_pubs.sort(key=pub_sort_key)
        data_pubs_path = os.path.join(BASE_DIR, "data", "publications.json")
        with open(data_pubs_path, "w", encoding="utf-8") as df:
            json.dump(all_pubs, df, indent=2, ensure_ascii=False)
        print(f"✓ Synced {len(all_pubs)} publications to data/publications.json")

class DecapProxyHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Clean custom logging
        print(f"[Decap Proxy] {self.command} {self.path} - {format % args}")

    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self):
        if self.path.startswith("/api/v1"):
            self.send_response(200)
            self.send_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "repo": os.path.basename(BASE_DIR),
                "publish_modes": ["simple"],
                "type": "local_fs"
            }).encode("utf-8"))
            return

        self.send_response(404)
        self.send_cors_headers()
        self.end_headers()

    def do_POST(self):
        content_len = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_len).decode("utf-8")
        
        try:
            req_data = json.loads(raw_body)
        except Exception:
            req_data = {}

        action = req_data.get("action", "")
        params = req_data.get("params", {})

        print(f"--> Action: {action}")

        resp_data = None
        status_code = 200

        try:
            if action == "info":
                resp_data = {
                    "repo": os.path.basename(BASE_DIR),
                    "publish_modes": ["simple"],
                    "type": "local_fs"
                }

            elif action == "entriesByFolder":
                folder = params.get("folder", "")
                extension = params.get("extension", "")
                depth = params.get("depth", 1)
                
                target_dir = full_path(folder)
                entries = []

                if os.path.exists(target_dir):
                    pattern = os.path.join(target_dir, f"*.{extension}" if extension else "*")
                    for file_path in glob.glob(pattern):
                        if os.path.isfile(file_path):
                            rel = normalize_path(os.path.relpath(file_path, BASE_DIR))
                            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                                content = f.read()
                            entries.append({
                                "data": content,
                                "file": {
                                    "path": rel,
                                    "label": os.path.basename(file_path),
                                    "id": sha256_str(content)
                                }
                            })

                # Sort publications identical to the live site: Preprints/in review first, then year descending
                if "publications" in folder.lower():
                    def pub_entry_sort_key(item):
                        try:
                            d = json.loads(item.get("data") or "{}")
                        except Exception:
                            d = {}
                        yg = str(d.get("year_group", "")).strip()
                        if any(k in yg.lower() for k in ["preprint", "review", "rxiv", "submitted"]):
                            return (0, 9999, d.get("citation", ""))
                        m = re.search(r"\b(19\d\d|20\d\d)\b", yg) or re.search(r"\b(19\d\d|20\d\d)\b", str(d.get("citation", "")))
                        if m:
                            return (1, -int(m.group(1)), d.get("citation", ""))
                        return (2, 0, d.get("citation", ""))

                    entries.sort(key=pub_entry_sort_key)

                resp_data = entries

            elif action == "entriesByFiles":
                files = params.get("files", [])
                entries = []
                for file_item in files:
                    rel_path = normalize_path(file_item.get("path", ""))
                    abs_path = full_path(rel_path)
                    if os.path.exists(abs_path) and os.path.isfile(abs_path):
                        with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                        entries.append({
                            "data": content,
                            "file": {
                                "path": rel_path,
                                "label": file_item.get("label", os.path.basename(rel_path)),
                                "id": sha256_str(content)
                            }
                        })
                    else:
                        entries.append({
                            "data": None,
                            "file": {
                                "path": rel_path,
                                "label": file_item.get("label", os.path.basename(rel_path)),
                                "id": None
                            }
                        })
                resp_data = entries

            elif action == "getEntry":
                rel_path = normalize_path(params.get("path", ""))
                abs_path = full_path(rel_path)
                if os.path.exists(abs_path):
                    with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    resp_data = {
                        "data": content,
                        "file": {
                            "path": rel_path,
                            "id": sha256_str(content)
                        }
                    }
                else:
                    status_code = 404
                    resp_data = {"error": f"File not found: {rel_path}"}

            elif action == "persistEntry":
                data_files = params.get("dataFiles", [])
                assets = params.get("assets", [])
                
                # If entry was provided in old shape
                if not data_files and "entry" in params:
                    data_files = [params["entry"]]

                for df in data_files:
                    path = normalize_path(df.get("path", ""))
                    raw = df.get("raw", "")
                    abs_path = full_path(path)
                    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
                    with open(abs_path, "w", encoding="utf-8") as f:
                        f.write(raw)
                    print(f"Persisted data file: {path}")

                    # Handle rename/move if newPath is provided
                    new_path = df.get("newPath")
                    if new_path and normalize_path(new_path) != path:
                        new_abs = full_path(new_path)
                        os.makedirs(os.path.dirname(new_abs), exist_ok=True)
                        os.rename(abs_path, new_abs)
                        print(f"Moved file to: {new_path}")

                for a in assets:
                    path = normalize_path(a.get("path", ""))
                    content_b64 = a.get("content", "")
                    encoding = a.get("encoding", "base64")
                    abs_path = full_path(path)
                    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
                    if encoding == "base64":
                        bin_data = base64.b64decode(content_b64)
                    else:
                        bin_data = content_b64.encode("utf-8")
                    with open(abs_path, "wb") as f:
                        f.write(bin_data)
                    print(f"Persisted asset: {path}")

                # Sync back to data/*.json for instant frontend update
                sync_collections_to_data()
                resp_data = {"message": "entry persisted"}

            elif action == "deleteFile":
                rel_path = normalize_path(params.get("path", ""))
                abs_path = full_path(rel_path)
                if os.path.exists(abs_path):
                    os.remove(abs_path)
                    print(f"Deleted file: {rel_path}")
                    sync_collections_to_data()
                resp_data = {"message": f"deleted file {rel_path}"}

            elif action == "deleteFiles":
                paths = params.get("paths", [])
                for p in paths:
                    rel = normalize_path(p)
                    abs_p = full_path(rel)
                    if os.path.exists(abs_p):
                        os.remove(abs_p)
                sync_collections_to_data()
                resp_data = {"message": "deleted files"}

            elif action == "getMedia":
                media_folder = normalize_path(params.get("mediaFolder", "assets/images"))
                abs_media = full_path(media_folder)
                media_list = []
                if os.path.exists(abs_media):
                    for fname in sorted(os.listdir(abs_media)):
                        if fname.startswith(".") or fname.endswith(".DS_Store"):
                            continue
                        fpath = os.path.join(abs_media, fname)
                        if not os.path.isfile(fpath):
                            continue
                        rel = f"{media_folder}/{fname}"
                        try:
                            with open(fpath, "rb") as mf:
                                b_data = mf.read()
                            media_list.append({
                                "id": sha256_bytes(b_data),
                                "name": fname,
                                "path": rel,
                                "size": len(b_data),
                                "displayURL": f"/{rel}",
                                "encoding": "base64",
                                "content": base64.b64encode(b_data).decode("utf-8")
                            })
                        except Exception as err:
                            print(f"Error reading media {fpath}: {err}")
                resp_data = media_list

            elif action == "getMediaFile":
                rel_path = normalize_path(params.get("path", ""))
                abs_path = full_path(rel_path)
                if os.path.exists(abs_path):
                    with open(abs_path, "rb") as mf:
                        b_data = mf.read()
                    resp_data = {
                        "id": sha256_bytes(b_data),
                        "name": os.path.basename(rel_path),
                        "path": rel_path,
                        "content": base64.b64encode(b_data).decode("utf-8"),
                        "encoding": "base64"
                    }
                else:
                    status_code = 404
                    resp_data = {"error": "Media file not found"}

            elif action == "persistMedia":
                asset = params.get("asset", {})
                rel_path = normalize_path(asset.get("path", ""))
                content_b64 = asset.get("content", "")
                abs_path = full_path(rel_path)
                os.makedirs(os.path.dirname(abs_path), exist_ok=True)
                bin_data = base64.b64decode(content_b64)
                with open(abs_path, "wb") as mf:
                    mf.write(bin_data)
                resp_data = {
                    "id": sha256_bytes(bin_data),
                    "name": os.path.basename(rel_path),
                    "path": rel_path,
                    "content": content_b64,
                    "encoding": "base64"
                }

            elif action == "fetchBibtex":
                url_to_check = params.get("url", "")
                citation = params.get("citation", "")
                year = params.get("year", "2024")
                pub_id = params.get("id", "pub")

                doi_match = re.search(r"(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)", url_to_check)
                bibtex_result = None
                source = "none"

                if doi_match:
                    doi = doi_match.group(1).rstrip(".")
                    try:
                        doi_req = urllib.request.Request(
                            f"https://doi.org/{doi}",
                            headers={
                                "Accept": "application/x-bibtex",
                                "User-Agent": "ConsciousBrainLab/1.0 (mailto:info@consciousbrainlab.com)"
                            }
                        )
                        with urllib.request.urlopen(doi_req, timeout=8) as resp:
                            bibtex_result = resp.read().decode("utf-8").strip()
                            source = "crossref"
                    except Exception as e:
                        print(f"DOI fetch error for {doi}: {e}")

                if not bibtex_result and citation:
                    # Synthesize clean standard BibTeX
                    parts = citation.split(".")
                    author = parts[0].strip() if len(parts) > 0 else "Conscious Brain Lab"
                    title = parts[1].strip() if len(parts) > 1 else citation
                    clean_author = re.sub(r"[^\w]", "", author.split(",")[0].lower()) or "cbl"
                    key = f"{clean_author}_{year}"
                    bibtex_result = f"""@article{{{key},
  author = {{{author}}},
  title = {{{title}}},
  year = {{{year}}},
  journal = {{Conscious Brain Lab Publications}},
  url = {{{url_to_check}}}
}}"""
                    source = "synthesized"

                resp_data = {
                    "bibtex": bibtex_result,
                    "source": source
                }

            elif action == "getDeployPreview":
                resp_data = None

            else:
                print(f"Unknown action: {action}")
                status_code = 422
                resp_data = {"error": f"Unknown action {action}"}

        except Exception as e:
            import traceback
            traceback.print_exc()
            status_code = 500
            resp_data = {"error": str(e)}

        self.send_response(status_code)
        self.send_cors_headers()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(resp_data).encode("utf-8"))

def run():
    # Perform initial sync
    sync_collections_to_data()
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", PORT), DecapProxyHandler) as httpd:
        print(f"🚀 Decap CMS Local Backend Server listening at http://127.0.0.1:{PORT}")
        print("Ready for local Decap CMS connections on http://localhost:8080/admin/")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    run()
