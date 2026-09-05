#!/usr/bin/env python3
"""
compile_content.py

Aggregates individual CMS content files from `content/news/*.json` into consolidated
`data/news.json` used by the public website frontend.
"""

import os
import glob
import json

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


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    print("Compiling CMS content collections...")
    compile_news()
    print("Content compilation complete.")


if __name__ == "__main__":
    main()
