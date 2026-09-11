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
import unicodedata
import html


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
        pattern = r'(?:[ \t]*<!-- (?:Preload|Prioritize) [^\n]*-->\n)?(?:[ \t]*<link rel="preload" as="image"[^\n]*>\n?)+'

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


def update_html_grid(html_rel_path, start_pattern, end_pattern, cards_html):
    """Synchronizes static HTML cards container with newly compiled items to eliminate layout shift."""
    html_path = os.path.join(BASE_DIR, html_rel_path)
    if not os.path.exists(html_path):
        return
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            content = f.read()

        pattern = re.compile(f'({start_pattern})(.*?)({end_pattern})', re.DOTALL)
        m = pattern.search(content)
        if m:
            replacement = m.group(1) + "\n" + cards_html + "\n" + m.group(3)
            new_content = content[:m.start()] + replacement + content[m.end():]
            if new_content != content:
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"Synchronized static grid in {html_rel_path}")
    except Exception as e:
        print(f"Warning: Failed to update grid in {html_rel_path}: {e}")


def get_youtube_embed_url(url):
    if not url or not isinstance(url, str):
        return ""
    m = re.search(r'(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})', url)
    return f"https://www.youtube-nocookie.com/embed/{m.group(1)}" if m else ""


def is_direct_video_file(url):
    if not url or not isinstance(url, str):
        return False
    clean = url.split("?")[0].lower()
    return clean.endswith((".mp4", ".webm", ".mov", ".ogg"))


def render_news_cards(items):
    cards = []
    for index, item in enumerate(items):
        title = item.get("title") or "News Update"
        date = item.get("date") or ""
        text = item.get("text") or ""
        link = item.get("link") or ""
        img_pos = item.get("position") or "center 20%"

        video_source = item.get("video") or ""
        img_src = item.get("image") or ""
        if not video_source and (is_direct_video_file(img_src) or get_youtube_embed_url(img_src)):
            video_source = img_src

        yt_embed = get_youtube_embed_url(video_source)
        if yt_embed:
            iframe_loading = "eager" if index < 3 else "lazy"
            media_html = f'''        <div class="news-card-video-wrap">
          <iframe src="{yt_embed}" title="{title}" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen loading="{iframe_loading}"></iframe>
        </div>'''
        elif is_direct_video_file(video_source):
            video_preload = "auto" if index < 3 else "metadata"
            media_html = f'''        <div class="news-card-video-wrap">
          <video src="{video_source}" controls playsinline preload="{video_preload}" class="news-card-video"></video>
        </div>'''
        elif img_src:
            is_logo = item.get("type") == "logo" or item.get("fit") == "contain" or item.get("position") == "contain"
            logo_class = " news-card-logo" if is_logo else ""
            fit_style = "object-fit: contain; background: var(--bg-tertiary);" if is_logo else f"object-fit: cover; object-position: {img_pos};"
            loading_attrs = 'loading="eager" fetchpriority="high" decoding="async"' if index < 3 else 'loading="lazy" decoding="async"'
            item_type = item.get("type", "photo")
            media_html = f'''        <div class="news-card-img-wrap">
          <img src="{img_src}" alt="{title}" class="news-card-img{logo_class}" data-type="{item_type}" {loading_attrs} style="{fit_style}" onerror="this.parentElement.style.display='none';" />
        </div>'''
        else:
            media_html = ""

        date_html = f'\n          <span class="news-card-date">{date}</span>' if date else ""
        link_html = f'''\n          <div style="margin-top: 0.75rem;">
            <a href="{link}" target="_blank" rel="noopener noreferrer" class="btn btn-secondary" style="font-size: 0.8rem; padding: 0.35rem 0.75rem;">
              Read More &rarr;
            </a>
          </div>''' if link else ""

        media_block = f'\n{media_html}' if media_html else ""

        card_str = f'''      <article class="news-card">{media_block}
        <div class="news-card-body">{date_html}
          <h3 class="news-card-title">{title}</h3>
          <p class="news-card-desc">{text}</p>{link_html}
        </div>
      </article>'''
        cards.append(card_str)
    return "\n\n".join(cards)


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

    # Auto-synchronize static fallback news grid
    update_html_grid("news/index.html", r'<div class="news-grid">', r'      </div>\s*</div>\s*</main>', render_news_cards(items))


def render_project_cards(items):
    cards = []
    for index, item in enumerate(items):
        title = item.get("title") or ""
        tag = item.get("tag") or ""
        desc = item.get("description") or ""
        img = item.get("image") or ""
        slug = item.get("slug") or ""
        fit = "contain" if item.get("fit") == "contain" else "cover"
        fit_style = "object-fit: contain; padding: 1.5rem;" if fit == "contain" else "object-fit: cover;"
        wrap_style = ' style="background: #ffffff;"' if fit == "contain" else ""

        loading_attrs = 'loading="eager" fetchpriority="high" decoding="async"' if index < 3 else 'loading="lazy" decoding="async"'

        img_html = f'''        <div class="project-card-img-wrap"{wrap_style}>
          <img src="{img}" alt="{title}" class="project-card-img" {loading_attrs} style="{fit_style}" onerror="this.parentElement.style.display='none';" />
        </div>\n''' if img else ""

        tag_html = f'<span class="tag tag-accent project-card-tag">{tag}</span>\n            ' if tag else ""
        desc_p = desc.replace("\n\n", '</p><p class="project-card-desc">')

        card_str = f'''      <article class="project-card" id="project-{slug}">
{img_html}        <div class="project-card-body">
            {tag_html}<h2 class="project-card-title">{title}</h2>
            <p class="project-card-desc">{desc_p}</p>
          </div>
        </article>'''
        cards.append(card_str)
    return "\n\n".join(cards)


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

    # Auto-synchronize static fallback projects grid
    update_html_grid("projects/index.html", r'<div class="projects-grid">', r'      </div>\s*</div>\s*</main>', render_project_cards(items))


def clean_bib_val(val):
    if not val:
        return ""
    val = re.sub(r"\s+", " ", str(val)).strip()
    val = val.replace("{", "").replace("}", "")
    return val


def parse_bibtex(raw):
    if not raw or not isinstance(raw, str) or not raw.strip().startswith("@"):
        return None
    first_brace = raw.find("{")
    if first_brace == -1:
        return None
    first_comma = raw.find(",", first_brace)
    if first_comma == -1:
        return None
    body = raw[first_comma + 1:]
    fields = {}
    pattern = re.compile(r'([a-zA-Z_\-]+)\s*=\s*(?:\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}|\"([^\"]*)\"|([a-zA-Z0-9_\-]+))', re.DOTALL)
    for m in pattern.finditer(body):
        k = m.group(1).lower()
        v = m.group(2) if m.group(2) is not None else (m.group(3) if m.group(3) is not None else m.group(4))
        if v:
            fields[k] = clean_bib_val(v)
    return fields


def format_author_apa(a):
    a = a.strip()
    if "," in a:
        parts = [p.strip() for p in a.split(",", 1)]
        last = parts[0]
        given = parts[1].split()
        inits = " ".join(g[0].upper() + "." for g in given if g)
        return f"{last}, {inits}" if inits else last
    parts = a.split()
    if len(parts) == 1:
        return parts[0]
    dutch = {"van", "de", "den", "der", "ten", "ter", "von"}
    if len(parts) >= 3 and parts[-2].lower() in dutch:
        last = " ".join(parts[-2:])
        inits = " ".join(p[0].upper() + "." for p in parts[:-2] if p)
        return f"{last}, {inits}" if inits else last
    last = parts[-1]
    inits = " ".join(p[0].upper() + "." for p in parts[:-1] if p)
    return f"{last}, {inits}" if inits else last


def format_authors_apa(raw_authors):
    if not raw_authors:
        return ""
    authors = [a.strip() for a in re.split(r"\s+and\s+", raw_authors, flags=re.I) if a.strip()]
    if not authors:
        return ""
    formatted = [format_author_apa(a) for a in authors]
    if len(formatted) == 1:
        return formatted[0]
    elif len(formatted) == 2:
        return f"{formatted[0]}, & {formatted[1]}"
    elif len(formatted) <= 20:
        main_part = ", ".join(formatted[:-1])
        return f"{main_part}, & {formatted[-1]}"
    else:
        main_part = ", ".join(formatted[:19])
        return f"{main_part}, … {formatted[-1]}"


def format_pub_apa_html(pub):
    b = parse_bibtex(pub.get("bibtex", ""))
    journal = (b.get("journal") or b.get("journaltitle") or b.get("booktitle") or "").strip() if b else ""
    publisher = (b.get("publisher") or "").strip() if b else ""

    # Only use BibTeX formatter if we have real journal/publisher metadata and not dummy journal
    if b and (publisher or (journal and journal.lower() != "conscious brain lab publications")):
        authors = format_authors_apa(b.get("author", ""))
        yr = b.get("year", "")
        year_str = f"({yr})." if yr else ""
        title = (b.get("title") or "").strip()
        if title and not title.endswith((".", "!", "?")):
            title += "."
        volume = (b.get("volume") or "").strip()
        issue = (b.get("number") or b.get("issue") or "").strip()
        pages = (b.get("pages") or "").strip().replace("--", "–")

        pub_details = ""
        if journal and journal.lower() != "conscious brain lab publications":
            pub_details = f"<em>{html.escape(journal)}</em>"
            if volume:
                pub_details += f", <em>{html.escape(volume)}</em>"
                if issue:
                    pub_details += f"({html.escape(issue)})"
            elif issue:
                pub_details += f"({html.escape(issue)})"
            if pages:
                pub_details += f", {html.escape(pages)}"
            if not pub_details.endswith("."):
                pub_details += "."
        elif publisher:
            pub_details = f"<em>{html.escape(publisher)}</em>."

        if authors or title:
            parts = [p for p in [authors, year_str, title, pub_details] if p]
            res = " ".join(parts)
            res = res.replace("&amp;amp;", "&amp;").replace("&Amp;", "&amp;")
            return res

    # Fallback to citation string with journal italicization
    cit = pub.get("citation", "").strip()
    cit = re.sub(r"\s*\b(?:CLOCKSS|LOCKSS)\b\.?\s*$", "", cit)
    cit = cit.replace("<i>", "<em>").replace("</i>", "</em>")
    if cit and not cit.endswith("."):
        cit += "."

    common = [
        "Nature Human Behavior", "Nature Human Behaviour", "Nature Neuroscience", "Nature Communications", "Nature",
        "The Journal of Neuroscience", "Journal of Neuroscience Methods", "Journal of Cognitive Neuroscience", "Journal of Neuroscience", "Journal of Vision", "Journal of Neurology",
        "Trends in Cognitive Sciences", "Trends in Neurosciences",
        "Philosophical Transactions of the Royal Society: B", "Philosophical Transactions of the Royal Society B",
        "Consciousness and Cognition", "Communications Biology", "Communications Psychology",
        "PLOS Biology", "PLOS Computational Biology", "PLOS ONE", "PLoS ONE",
        "NeuroImage: Clinical", "Neuroimage: Reports", "NeuroImage", "Neuroimage",
        "Frontiers in Human Neuroscience", "Frontiers in Neuroscience", "Frontiers in Psychology",
        "Front. Hum. Neurosci.", "eNeuro", "eLife", "Cerebral Cortex", "Current Biology", "Behavioral and Brain Sciences",
        "Neuroscience and Biobehavioral Reviews", "Neuroscience & Biobehavioral Reviews", "Neuroscience &amp; Biobehavioral Reviews", "Neuroscience of Consciousness",
        "Cognitive Neuroscience", "Attention, Perception, & Psychophysics", "Psychological Science", "Cognition", "Brain",
        "Neuropsychologia", "Scientific Reports", "Radboud University"
    ]
    for j in common:
        pattern = r"(?<!\w)" + re.escape(j) + r"(?!\w)"
        if re.search(pattern, cit):
            cit = re.sub(pattern, f"<em>{j}</em>", cit, count=1)
            break

    cit = cit.replace("&amp;amp;", "&amp;").replace("&Amp;", "&amp;")
    return cit


def normalize_text_ascii(text):
    if not text or not isinstance(text, str):
        return ""
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn").lower()


def match_member_publications(member, pubs):
    name = member.get("name", "").replace("★", "").strip()
    if not name:
        return []
    parts = name.split()
    if len(parts) == 1:
        surname = parts[0]
    else:
        dutch_prefixes = {"van", "de", "den", "der", "ten", "ter", "von"}
        surname_parts = []
        for p in parts[1:]:
            if p.lower() in dutch_prefixes or surname_parts:
                surname_parts.append(p)
        surname = " ".join(surname_parts) if surname_parts else parts[-1]

    norm_surname = normalize_text_ascii(surname)
    matched = []
    for p in pubs:
        cit = p.get("citation", "")
        bib = p.get("bibtex", "")
        norm_cit = normalize_text_ascii(cit)
        norm_bib = normalize_text_ascii(bib)

        # Match hyphenated surname (e.g. Canales-Johnson, Sánchez-Fuenzalida)
        if "-" in norm_surname:
            if re.search(r'\b' + re.escape(norm_surname) + r'\b', norm_cit) or re.search(r'\b' + re.escape(norm_surname) + r'\b', norm_bib):
                matched.append(p)
        # Match multi-word Dutch surname (e.g. van Gaal, de Jong)
        elif " " in norm_surname:
            if re.search(r'\b' + re.escape(norm_surname) + r'\b', norm_cit) or re.search(r'\b' + re.escape(norm_surname) + r'\b', norm_bib):
                matched.append(p)
        # Match single surname (e.g. Fahrenfort, Stein, Nuiten)
        else:
            pattern = r'(?<!-)\b' + re.escape(norm_surname) + r'\b'
            if re.search(pattern, norm_cit) or re.search(pattern, norm_bib):
                if norm_surname == "johnson":
                    if re.search(r'\bjohnson,\s*p\b', norm_cit) or "philippa" in norm_bib:
                        matched.append(p)
                else:
                    matched.append(p)

    # Format lightweight summaries for the member profile
    summaries = []
    for p in matched:
        summaries.append({
            "id": p.get("id"),
            "citation": p.get("citation", ""),
            "citation_html": p.get("citation_html") or format_pub_apa_html(p),
            "url": p.get("paper_url") or p.get("doi") or p.get("preprint_url") or "",
            "year": p.get("year_group", "")
        })
    return summaries



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

    # Load publications to link them to members
    pubs_path = os.path.join(DATA_DIR, "publications.json")
    all_pubs = []
    if os.path.exists(pubs_path):
        try:
            with open(pubs_path, "r", encoding="utf-8") as f:
                all_pubs = json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load publications for members: {e}")

    for m in items:
        if m.get("slug") == "lab-group-photo":
            continue
        matched_pubs = match_member_publications(m, all_pubs)
        m["publications"] = matched_pubs
        m["publication_count"] = len(matched_pubs)

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
    print(f"Successfully compiled {len(items)} members into {out_path} (linked publications)")

    # Auto-synchronize the group banner photo in members/index.html
    banner = next((m for m in items if m.get("slug") == "lab-group-photo" or "header" in m.get("category", []) or "Group Photo" in str(m.get("name", ""))), None)
    if banner and banner.get("image"):
        banner_img = banner.get("image")
        update_html_preloads("members/index.html", [banner_img], "Lab Overview Photo")

        # Also update the static <img id="team-group-photo" src="..."> in members/index.html
        html_path = os.path.join(BASE_DIR, "members/index.html")
        if os.path.exists(html_path):
            try:
                with open(html_path, "r", encoding="utf-8") as f:
                    html_content = f.read()

                new_html = re.sub(r'(<img\s+id="team-group-photo"[^>]*\ssrc=")[^"]*(")', r'\g<1>' + banner_img + r'\2', html_content)
                if new_html != html_content:
                    with open(html_path, "w", encoding="utf-8") as f:
                        f.write(new_html)
                    print(f"Updated members/index.html #team-group-photo src -> {banner_img}")
            except Exception as e:
                print(f"Warning: Failed to update team-group-photo in members/index.html: {e}")


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

    # Sort topics alphabetically, generate formatted APA HTML, and sort publications
    for p in items:
        if isinstance(p.get("topics"), list):
            p["topics"] = sorted(p["topics"], key=lambda x: str(x).lower())
        p["citation_html"] = format_pub_apa_html(p)


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


def render_impression_cards(items):
    cards = []
    for index, item in enumerate(items):
        title = item.get("title") or ""
        tag = item.get("tag") or ""
        date = item.get("date") or ""
        image = item.get("image") or ""
        description = item.get("description") or ""
        slug = item.get("slug") or ""

        loading_attrs = 'loading="eager" fetchpriority="high" decoding="async"' if index < 3 else 'loading="lazy" decoding="async"'

        img_html = f'''          <div style="width: 100%; height: 280px; overflow: hidden; background: var(--bg-tertiary);">
            <img src="{image}" alt="{title}" style="width: 100%; height: 100%; object-fit: cover; transition: transform 0.3s ease;" onmouseover="this.style.transform='scale(1.03)'" onmouseout="this.style.transform='scale(1)'" {loading_attrs} onerror="this.parentElement.style.display='none';" />
          </div>''' if image else ""

        tag_html = f'<span class="tag tag-accent">{tag}</span>' if tag else '<span></span>'
        date_html = f'\n              <span style="font-size: 0.85rem; color: var(--text-muted); font-weight: 600;">{date}</span>' if date else ""

        img_block = f'\n{img_html}' if img_html else ""

        card_str = f'''      <article class="card" style="padding: 0; overflow: hidden; border-radius: var(--radius-lg); box-shadow: var(--shadow-md);" id="impression-{slug}">{img_block}
        <div style="padding: 1.5rem;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; flex-wrap: wrap; gap: 0.5rem;">
            {tag_html}{date_html}
          </div>
          <h3 style="margin-bottom: 0.5rem; font-size: 1.3rem;">{title}</h3>
          <p style="color: var(--text-secondary); line-height: 1.6; margin: 0;">{description}</p>
        </div>
      </article>'''
        cards.append(card_str)
    return "\n\n".join(cards)


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

        # Auto-synchronize static fallback impressions grid
        update_html_grid("lab-and-campus-impressions/index.html", r'<div class="grid-2"[^>]*id="impressions-grid">', r'      </div>\s*</div>\s*</main>', render_impression_cards(items))
    except Exception as e:
        print(f"Warning: Failed to compile impressions: {e}")


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    print("Compiling CMS content collections...")
    compile_news()
    compile_projects()
    compile_publications()
    compile_members()
    compile_impressions()
    print("Content compilation complete.")


if __name__ == "__main__":
    main()
