# Conscious Brain Lab Website (Subscription-Free CMS)

This repository contains the complete, modern, subscription-free website for the **Conscious Brain Lab** at the University of Amsterdam ([consciousbrainlab.com](https://www.consciousbrainlab.com)), built as a lightweight static architecture powered by **Decap CMS** and hosted on **GitHub Pages** ($0/month forever).

---

## Architecture Overview & Operation

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                             PUBLIC STATIC WEBSITE                                │
│                                                                                  │
│   HTML5 + Vanilla CSS + Vanilla JS (No build step, zero framework runtime)      │
│   Hosted on GitHub Pages: https://conscious-brain-lab.github.io                  │
└──────────────────────────────────────┬───────────────────────────────────────────┘
                                       │ Reads content & media
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                            REPOSITORY DATA & ASSETS                              │
│                                                                                  │
│   ├── content/          -> Individual JSON files per entry (pubs, members, news) │
│   ├── data/             -> Consolidated data fallback files                      │
│   └── assets/images/    -> Team photos, banners, publication figures             │
└──────────────────────────────────────▲───────────────────────────────────────────┘
                                       │ Commits content & uploads
                                       │ (via GitHub REST API)
┌──────────────────────────────────────┴───────────────────────────────────────────┐
│                          DECAP CMS PORTAL (/admin)                               │
│                                                                                  │
│   • Local Dev: Uses Decap local backend proxy (local_backend: true)              │
│   • Production: Direct GitHub API with Personal Access Token (PAT)               │
│   • Integrated tools: DOI auto-fetch, Cropper.js image editor, auto-sort         │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## How the Site Operates

### 1. Operation on GitHub (Production)

- **Hosting**: Hosted on **GitHub Pages** directly from the repository (`conscious-brain-lab/conscious-brain-lab.github.io`) on branch `main`.
- **Zero-Build Architecture**: There is no Node.js/Vite/Webpack build step needed. Pages are pure semantic HTML5 with Vanilla CSS and Vanilla JavaScript that run natively in every browser with instantaneous load times.
- **Automated Deployment**: Any commit to the `main` branch (either made by a developer via git or by Decap CMS when saving an entry) automatically triggers GitHub Pages deployment, going live worldwide in ~30–60 seconds.
- **Content Storage**: Every publication, team member, news item, project, vacancy, and impression is stored as an individual, structured JSON file under `content/<collection>/` (e.g. `content/publications/pub-01.json`).

### 2. CMS Authentication on GitHub Pages

Because GitHub Pages is a purely static hosting environment without a backend server to run OAuth proxy secrets, authentication is handled via **GitHub Personal Access Tokens (PAT)**:

- **Login Screen (`/admin/index.html`)**: When visiting `/admin/`, users who are not logged in see an integrated Conscious Brain Lab CMS authentication card.
- **1-Click Token Creation**: Users click **`🔑 Generate Token on GitHub (1 Click)`**, which opens GitHub's token generator with the required `repo` scope pre-checked and description pre-filled (`Conscious Brain Lab CMS`).
- **Browser Persistence**: Once entered, the token is validated against GitHub API (`api.github.com/user`) and saved in the user's browser `localStorage` (`decap-cms-user`). Users only paste the token **once per browser/device**.
- **Direct Git Commits**: Decap CMS communicates directly with GitHub's REST API. When a user clicks "Publish" or edits an entry, Decap CMS creates a git commit directly on branch `main` as that authenticated GitHub user.

### 3. Operation Locally (Development & Testing)

You can run and test both the public website and the CMS locally on your machine without needing GitHub tokens or committing to the live site:

1. **Start the Local Web Server**:
   ```bash
   python3 -m http.server 8080
   ```
2. **Access the Site Locally**:
   - Public Website: [http://localhost:8080](http://localhost:8080)
   - Decap CMS: [http://localhost:8080/admin/](http://localhost:8080/admin/)
3. **Local CMS Editing**:
   - `admin/config.yml` has `local_backend: true` enabled.
   - When running a local Decap proxy (e.g., `npx decap-server` or `python3 scripts/local_cms_server.py`), Decap CMS detects `localhost` and allows direct local filesystem editing without requiring any GitHub token.

---

## Repository Structure

```
duplicate_CBL_website/
├── index.html                      # Homepage (Hero, Research Pillars, PIs, Latest Highlights)
├── members/
│   └── index.html                  # People & Alumni Directory (Filters & Bio Modals)
├── projects/
│   └── index.html                  # Research Projects & Themes
├── publications/
│   └── index.html                  # Searchable & Filterable Publications + BibTeX Modal
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
│   ├── index.html                  # Decap CMS Portal + Auth Card + DOI Fetcher + Cropper.js
│   └── config.yml                  # CMS Collection Schemas & GitHub Backend Config
├── assets/
│   ├── css/
│   │   ├── style.css               # Design System, Tokens, Dark/Light Themes, Mobile Nav
│   │   └── publications.css        # Publication Search, Filter Pills, Badges & Modals
│   ├── js/
│   │   ├── main.js                 # Theme Switcher, Mobile Drawer, Active Links, Toasts
│   │   ├── publications.js         # Real-time Search, Filters, Citation & BibTeX
│   │   ├── members.js              # Member Role Filtering & Bio Modals
│   │   ├── news.js                 # News Feed Renderer
│   │   ├── projects.js             # Research Projects Renderer
│   │   ├── impressions.js          # Campus Impressions Gallery
│   │   └── positions.js            # Vacatures & Open Positions
│   └── images/                     # Team photos, lab logos, and publication figures
├── content/                        # Individual JSON content files edited by Decap CMS
│   ├── members/                    # Lab member profile files
│   ├── publications/               # Publication entry files
│   ├── news/                       # News and talk announcement files
│   ├── projects/                   # Research project files
│   ├── vacancies/                  # Job opening files
│   └── impressions/                # Campus life photo files
├── data/                           # Consolidated JSON data files (fallback / bulk data)
│   ├── publications.json
│   ├── members.json
│   ├── projects.json
│   └── news.json
├── scripts/                        # Local dev & helper scripts (local_cms_server.py, etc.)
├── .github/
│   └── workflows/
│       └── deploy.yml              # GitHub Pages Deployment Workflow
└── README.md                       # This Documentation & Maintenance Guide
```

---

## Key Custom Features Built Into the CMS (`/admin/index.html`)

1. **DOI Auto-Fetch Engine**:
   - In the publication editor, entering a DOI (e.g. `10.1038/s41593-024-01600-z`) and clicking **⚡ Auto-Fill from DOI** queries Crossref API (`api.crossref.org`) and automatically populates:
     - Paper Title
     - Author list (formatted with initials)
     - Journal name
     - Publication year
     - BibTeX entry
2. **Interactive Cropper.js Image Editor**:
   - When uploading photos for lab members, banners, or news, users can click **✂️ Crop / Resize** to open an interactive modal with pre-configured aspect ratios:
     - `1:1 (Square / Avatar)` for lab member photos
     - `4:3` for lab photos
     - `16:9` for wide banner images
     - Freeform cropping & 90° rotation
   - Saves cropped, optimized images directly into `assets/images/`.
3. **Automated Chronological Publication Sorting**:
   - Automatically sorts publication cards in the CMS overview by Year (descending) so the newest papers are always at the top of the list.
4. **Floating Utility Dock**:
   - A non-intrusive floating pill positioned in the bottom-right corner of the CMS (`#cbl-cms-topbar`) provides:
     - `← Back to Public Website` (cleanly exits the CMS single-page hash router)
     - Active GitHub user handle badge
     - `Sign Out / Switch Token` button

---

## Guidelines for Future Agents & Maintainers

> [!IMPORTANT]
> **Git Push Policy**: Only commit locally unless the user's message explicitly contains the word `"push"`. Always obtain user authorization before pushing to remote repositories.

### Modifying Content Collections
- To add or modify fields in the CMS, edit [admin/config.yml](file:///Users/agenticai/Documents/ai_software/duplicate_CBL_website/admin/config.yml).
- Ensure any new fields are also accounted for in the corresponding frontend renderer (`assets/js/publications.js`, `assets/js/members.js`, etc.).

### Preserving CMS Header Layout
- Decap CMS uses Emotion CSS to position its top editor toolbar (`EditorControlBarContainer`) at `position: fixed; top: 0`.
- **Do not** place full-width fixed banners at `top: 0` in [admin/index.html](file:///Users/agenticai/Documents/ai_software/duplicate_CBL_website/admin/index.html). All utility navigation should remain in floating corner docks (bottom-right) to prevent covering editor controls (`←` back button, "CHANGES SAVED", "Publish", "Delete entry").

### Styling & Design System
- The global design system is defined in [assets/css/style.css](file:///Users/agenticai/Documents/ai_software/duplicate_CBL_website/assets/css/style.css) with CSS custom properties (`--bg-primary`, `--text-primary`, `--accent-primary`, etc.).
- Dark mode is toggled via `document.documentElement.setAttribute('data-theme', 'dark')` and automatically respects user OS preferences.

---

## Connecting a Custom Domain (`www.consciousbrainlab.com`)

When ready to route the production custom domain:
1. In the GitHub repository, go to **Settings** &rarr; **Pages** &rarr; **Custom domain**.
2. Enter `www.consciousbrainlab.com` and save.
3. At your DNS registrar:
   - Add a `CNAME` record for `www` pointing to `conscious-brain-lab.github.io`.
   - Add `A` records for the apex domain pointing to GitHub Pages IPs:
     - `185.199.108.153`
     - `185.199.109.153`
     - `185.199.110.153`
     - `185.199.111.153`
4. Check **Enforce HTTPS** in GitHub Pages settings.
