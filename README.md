# Conscious Brain Lab Website (Subscription-Free CMS)

This repository contains the complete, modern, subscription-free website for the **Conscious Brain Lab** ([consciousbrainlab.com](https://www.consciousbrainlab.com)), built as a lightweight static architecture powered by **Decap CMS** and hosted on **GitHub Pages** ($0/month forever).

---

## Key Features & Improvements

- **Zero Subscription Fees**: Completely subscription-free hosting on GitHub Pages with free SSL certificates.
- **Visual Decap CMS Admin (`/admin`)**: Non-technical researchers and PIs can log into the web admin panel to add papers, edit team profiles, write news posts, and update projects without writing code.
- **Enhanced Publications Engine**:
  - Real-time instant search across titles, authors, journals, DOIs, and keywords.
  - Filter pills by **Year** (`Preprints`, `2026`, `2025`, `2024`...) and **Topic** (`EEG`, `fMRI`, `MEG`, `Consciousness`, `Decision Making`, `Neural Decoding`).
  - **1-Click Citation Copy** button with toast notifications.
  - **BibTeX Export Modal** with copyable BibTeX entries.
- **Interactive People & Alumni Directory**:
  - Filter tabs for Principal Investigators, Postdocs, PhD Candidates, and Alumni.
  - Full bio modals, university affiliations, and links to external profiles.
- **Dark / Light Mode**:
  - Built-in theme toggle with auto-detection of OS preferences and persistent `localStorage` memory.
- **Direct Email Contact**: Clean `mailto:` integration without third-party form dependencies.
- **Dutch Section Support**: Dedicated pages for participant recruitment (`/proefkonijnen`), open positions (`/vacatures`), and campus impressions (`/lab-and-campus-impressions`).
- **100/100 Performance & SEO**: Pure HTML5 and Vanilla CSS with fast load times, semantic HTML, and zero third-party framework runtime overhead.

---

## Project Structure

```
duplicate_CBL_website/
├── index.html                      # Homepage (Hero, Pillars, PIs, Latest Highlights)
├── members/
│   └── index.html                  # People & Alumni Directory (Filters & Bio Modals)
├── projects/
│   └── index.html                  # Research Projects & Themes
├── publications/
│   └── index.html                  # Searchable & Filterable Publications + BibTeX
├── news/
│   └── index.html                  # News, Talks & Media Feed
├── lab-and-campus-impressions/
│   └── index.html                  # Lab & Campus Impressions (Dutch)
├── proefkonijnen/
│   └── index.html                  # Participant Recruitment (Dutch)
├── vacatures/
│   └── index.html                  # Open Positions / Vacatures
├── contact/
│   └── index.html                  # Contact Info, Maps, Transit & Direct Email
├── admin/
│   ├── index.html                  # Decap CMS Visual Admin Web Portal
│   └── config.yml                  # CMS Data Collections Schema
├── assets/
│   ├── css/
│   │   ├── style.css               # Design System, Tokens, Dark/Light Themes, Mobile Nav
│   │   └── publications.css        # Search, Filter Pills, Badges & BibTeX Modal
│   ├── js/
│   │   ├── main.js                 # Theme Switcher, Mobile Drawer, Active Links, Toasts
│   │   ├── publications.js         # Real-time Search, Filters, BibTeX Generator
│   │   └── members.js              # Member Role Filtering & Bio Modals
│   └── images/
│       └── favicon.svg             # High-resolution Brain Logo & Favicon
├── data/
│   ├── publications.json           # All 106 structured publications
│   ├── members.json                # All 27 lab members and alumni
│   ├── projects.json               # Projects and research themes
│   └── news.json                   # News and talk announcements
├── .github/
│   └── workflows/
│       └── deploy.yml              # 1-Click Automated GitHub Pages Deployment
└── README.md                       # Documentation & Setup Guide
```

---

## Local Development & Preview

To preview the website locally on your computer:

1. Open your terminal in this repository directory:
   ```bash
   cd /Users/agenticai/Documents/ai_software/duplicate_CBL_website
   ```
2. Start Python's built-in local web server:
   ```bash
   python3 -m http.server 8080
   ```
3. Open your browser and navigate to:
   ```
   http://localhost:8080
   ```

---

## Deploying to GitHub Pages ($0/month)

1. **Create a GitHub Repository**:
   - Create a new public or private repository on GitHub (e.g. `github.com/conscious-brain-lab/website`).
2. **Push your code**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Conscious Brain Lab subscription-free CMS website"
   git branch -M main
   git remote add origin https://github.com/<your-username>/<your-repo-name>.git
   # Push locally when ready (note: per policy, remember git push requires explicit user direction)
   ```
3. **Enable GitHub Pages**:
   - Go to your repository **Settings** &rarr; **Pages**.
   - Under **Build and deployment** &rarr; **Source**, select **GitHub Actions**.
   - The included `.github/workflows/deploy.yml` workflow will automatically build and publish your website instantly on every commit!

---

## Connecting Custom Domain (`www.consciousbrainlab.com`)

When you are ready to connect your live custom domain:
1. In your GitHub repository, go to **Settings** &rarr; **Pages** &rarr; **Custom domain**.
2. Enter `www.consciousbrainlab.com` and save.
3. Update your DNS settings at your domain registrar (e.g. TransIP, Namecheap, Cloudflare, etc.):
   - Set a **CNAME** record for `www` pointing to `<your-github-username>.github.io`.
   - Set **A** records for the apex domain pointing to GitHub Pages IPs:
     - `185.199.108.153`
     - `185.199.109.153`
     - `185.199.110.153`
     - `185.199.111.153`
4. Check **Enforce HTTPS** in GitHub Pages settings.

---

## Managing Content via Decap CMS (`/admin`)

Lab members can update content directly through the web browser:
1. Visit `https://www.consciousbrainlab.com/admin/` (or `http://localhost:8080/admin/`).
2. Log in with your GitHub account.
3. Select any collection from the left sidebar:
   - **Publications**: Click "New Publication", fill in title, authors, year, and DOI, and click "Save".
   - **Lab Members & Alumni**: Add new team members, edit bios, or update alumni roles.
   - **News & Talks**: Post announcements, keynote talks, or media appearances.
4. Click **Publish** — GitHub Pages will automatically deploy the updates within seconds!
