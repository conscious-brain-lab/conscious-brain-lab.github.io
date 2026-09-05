#!/usr/bin/env python3
"""
compile_content.py

Aggregates individual CMS content files from `content/*/*.json` into consolidated
`data/*.json` files used by the public website frontend.
"""

import os
import glob
import json
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT_DIR = os.path.join(BASE_DIR, "content")
DATA_DIR = os.path.join(BASE_DIR, "data")


def compile_news():
    folder_path = os.path.join(CONTENT_DIR, "news")
    if not os.path.exists(folder_path):
        return
    items = []
    for filepath in sorted(glob.glob(os.path.join(folder_path, "*.json"))):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                items.append(json.load(f))
        except Exception as e:
            print(f"Warning: Failed to load {filepath}: {e}")

    if not items:
        return

    # Sort by date_sort descending (e.g. '2025-05', '2024-09', '2024-03-b', '2024-03')
    items.sort(key=lambda x: str(x.get("date_sort", x.get("date", "2000-01"))), reverse=True)
    out_path = os.path.join(DATA_DIR, "news.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)
    print(f"Successfully compiled {len(items)} news items into {out_path}")


def compile_projects():
    folder_path = os.path.join(CONTENT_DIR, "projects")
    if not os.path.exists(folder_path):
        return
    items = []
    for filepath in sorted(glob.glob(os.path.join(folder_path, "*.json"))):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                items.append(json.load(f))
        except Exception as e:
            print(f"Warning: Failed to load {filepath}: {e}")

    if not items:
        return

    # Sort by order ascending (default 99), then title
    def project_sort_key(p):
        try:
            order_val = int(p.get("order", 99))
        except Exception:
            order_val = 99
        return (order_val, str(p.get("title", "")))

    items.sort(key=project_sort_key)
    out_path = os.path.join(DATA_DIR, "projects.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)
    print(f"Successfully compiled {len(items)} project items into {out_path}")


def compile_members():
    folder_path = os.path.join(CONTENT_DIR, "members")
    if not os.path.exists(folder_path):
        return
    items = []
    for filepath in sorted(glob.glob(os.path.join(folder_path, "*.json"))):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                items.append(json.load(f))
        except Exception as e:
            print(f"Warning: Failed to load {filepath}: {e}")

    if not items:
        return

    # Sort members: PIs first, current team, then alumni; by explicit order, then name
    cat_order = {"header": 0, "pi": 1, "postdoc": 2, "phd": 3, "alumni": 4}
    def member_sort_key(m):
        is_alumni = 1 if m.get("status") == "alumni" else 0
        category_rank = cat_order.get(m.get("category", "phd"), 99)
        try:
            display_order = int(m.get("order", 99))
        except Exception:
            display_order = 99
        name = m.get("name", "")
        return (is_alumni, category_rank, display_order, name)

    items.sort(key=member_sort_key)
    out_path = os.path.join(DATA_DIR, "members.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)
    print(f"Successfully compiled {len(items)} members into {out_path}")


def compile_publications():
    folder_path = os.path.join(CONTENT_DIR, "publications")
    if not os.path.exists(folder_path):
        return
    items = []
    for filepath in sorted(glob.glob(os.path.join(folder_path, "*.json"))):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                items.append(json.load(f))
        except Exception as e:
            print(f"Warning: Failed to load {filepath}: {e}")

    if not items:
        return

    # Sort publications: Preprint/in review first, then year descending
    def pub_sort_key(p):
        yg = str(p.get("year_group", "")).strip()
        if any(k in yg.lower() for k in ["preprint", "review", "rxiv", "submitted"]):
            return (0, 9999)
        m = re.search(r"\b(19\d\d|20\d\d)\b", yg) or re.search(r"\b(19\d\d|20\d\d)\b", str(p.get("citation", "")))
        if m:
            return (1, -int(m.group(1)))
        return (2, 0)

    items.sort(key=pub_sort_key)
    out_path = os.path.join(DATA_DIR, "publications.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)
    print(f"Successfully compiled {len(items)} publications into {out_path}")


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    print("Compiling CMS content collections...")
    compile_news()
    compile_projects()
    compile_members()
    compile_publications()
    print("Content compilation complete.")


if __name__ == "__main__":
    main()
