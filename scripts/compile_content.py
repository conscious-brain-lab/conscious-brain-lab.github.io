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


def update_html_preloads(html_rel_path, image_urls, comment_label="Top Row Images"):
    """Automatically synchronizes <link rel="preload"> in the given HTML file with the top images."""
    html_path = os.path.join(BASE_DIR, html_rel_path)
    if not os.path.exists(html_path) or not image_urls:
        return
    if isinstance(image_urls, str):
        image_urls = [image_urls]

    # Deduplicate and preserve order
    valid_urls = []
    for u in image_urls:
        if u and isinstance(u, str) and u not in valid_urls:
            valid_urls.append(u)

    if not valid_urls:
        return

    try:
        with open(html_path, "r", encoding="utf-8") as f:
            content = f.read()

        preload_tags = "\n".join([f'  <link rel="preload" as="image" href="{u}" fetchpriority="high">' for u in valid_urls])
        replacement_block = f'  <!-- Preload {comment_label} -->\n{preload_tags}'

        # Match existing preload comment (if any) and all consecutive image preload link tags
        pattern = r'(?:[ \t]*<!-- Preload [^\n]*-->\n)?(?:[ \t]*<link rel="preload" as="image"[^\n]*>\n?)+'

        if re.search(pattern, content):
            new_content = re.sub(pattern, replacement_block + "\n", content, count=1)
        else:
            new_content = content.replace("</head>", f"{replacement_block}\n</head>")

        if new_content != content:
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"Updated {html_rel_path} preload tags -> {valid_urls}")
    except Exception as e:
        print(f"Warning: Failed to update preloads in {html_rel_path}: {e}")


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

    # Auto-synchronize the preload tags in news/index.html with the top 3 news items' images (entire top row)
    top_news_imgs = []
    for it in items:
        img = it.get("image")
        if img and isinstance(img, str) and not (img.endswith(".mp4") or "youtube" in img or "youtu.be" in img):
            if img not in top_news_imgs:
                top_news_imgs.append(img)
                if len(top_news_imgs) == 3:
                    break
    if top_news_imgs:
        update_html_preloads("news/index.html", top_news_imgs, "Top News Row Images (Top 3 Cards)")


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

    # Auto-synchronize the preload tags in projects/index.html with the top 3 projects' images (entire top row)
    top_proj_imgs = []
    for p in items:
        img = p.get("image")
        if img and isinstance(img, str):
            if img not in top_proj_imgs:
                top_proj_imgs.append(img)
                if len(top_proj_imgs) == 3:
                    break
    if top_proj_imgs:
        update_html_preloads("projects/index.html", top_proj_imgs, "Above-the-Fold Project Images (Top 3 Cards)")


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
    cat_order = {"header": 0, "pi": 1, "postdoc": 2, "phd": 3, "ra": 4, "visiting": 5}
    def member_sort_key(m):
        is_alumni = 1 if m.get("status") == "alumni" else 0
        raw_cat = m.get("category", "phd")
        ranks = []
        if isinstance(raw_cat, (list, tuple)):
            for c in raw_cat:
                if isinstance(c, (list, tuple)):
                    ranks.extend([cat_order.get(str(sub_c), 99) for sub_c in c])
                elif isinstance(c, str):
                    ranks.append(cat_order.get(c, 99))
                elif isinstance(c, dict):
                    val = c.get("value") or c.get("label") or ""
                    ranks.append(cat_order.get(str(val), 99))
                else:
                    ranks.append(cat_order.get(str(c), 99))
            category_rank = min(ranks) if ranks else 99
        elif isinstance(raw_cat, str):
            category_rank = cat_order.get(raw_cat, 99)
        else:
            category_rank = 99
        try:
            display_order = int(m.get("order", 99))
        except Exception:
            display_order = 99
        name = str(m.get("name", ""))
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

    # Sort topics alphabetically and sort publications by preprint/year descending
    for p in items:
        if isinstance(p.get("topics"), list):
            p["topics"] = sorted(p["topics"], key=lambda x: str(x).lower())

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


def compile_impressions():
    file_path = os.path.join(DATA_DIR, "impressions.json")
    if not os.path.exists(file_path):
        return
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        items = data if isinstance(data, list) else data.get("items", [])
        if not items:
            return

        top_imp_imgs = []
        for it in items:
            img = it.get("image")
            if img and isinstance(img, str):
                if img not in top_imp_imgs:
                    top_imp_imgs.append(img)
                    if len(top_imp_imgs) == 3:
                        break
        if top_imp_imgs:
            update_html_preloads("lab-and-campus-impressions/index.html", top_imp_imgs, "Above-the-Fold Impression Images (Top 3 Cards)")
    except Exception as e:
        print(f"Warning: Failed to compile impressions preloads: {e}")


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    print("Compiling CMS content collections...")
    compile_news()
    compile_projects()
    compile_members()
    compile_publications()
    compile_impressions()
    print("Content compilation complete.")


if __name__ == "__main__":
    main()
