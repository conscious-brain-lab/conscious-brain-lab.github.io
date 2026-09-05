/**
 * Publications Interactive Module
 * Real-time Search, Year/Topic Filtering, Sort Order Toggle (Newest First / Oldest First),
 * BibTeX Modal & Citation Copy
 */

let allPublications = [];
let activeYear = 'all';
let activeTopic = 'all';
let searchQuery = '';
let sortOrder = 'newest'; // 'newest' (default) or 'oldest'

document.addEventListener('DOMContentLoaded', async () => {
  const container = document.getElementById('publications-container');
  const searchInput = document.getElementById('pub-search-input');
  const sortBtn = document.getElementById('pub-sort-btn');
  const yearPills = document.querySelectorAll('.year-pill');
  const topicPills = document.querySelectorAll('.topic-pill');

  // Load publication data
  try {
    const res = await fetch('/data/publications.json');
    if (!res.ok) throw new Error('Failed to load publications');
    allPublications = await res.json();
    renderPublications();
  } catch (err) {
    console.error(err);
    if (container) {
      container.innerHTML = `<p class="error-msg">Could not load publications data. Please refresh or try again.</p>`;
    }
  }

  // Search input handler
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      searchQuery = e.target.value.toLowerCase().trim();
      renderPublications();
    });
  }

  // Sort toggle handler
  if (sortBtn) {
    sortBtn.addEventListener('click', () => {
      sortOrder = sortOrder === 'newest' ? 'oldest' : 'newest';
      updateSortButtonText();
      renderPublications();
    });
  }

  function updateSortButtonText() {
    if (!sortBtn) return;
    if (sortOrder === 'newest') {
      sortBtn.innerHTML = `
        <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M3 18h6v-2H3v2zM3 6v2h18V6H3zm0 7h12v-2H3v2z"/></svg>
        <span>Sort: Newest First &darr;</span>
      `;
    } else {
      sortBtn.innerHTML = `
        <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M3 18h18v-2H3v2zm0-5h12v-2H3v2zm0-7v2h6V6H3z"/></svg>
        <span>Sort: Oldest First &uarr;</span>
      `;
    }
  }

  // Year filter handlers
  yearPills.forEach(pill => {
    pill.addEventListener('click', () => {
      yearPills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      activeYear = pill.dataset.year;
      renderPublications();
    });
  });

  // Topic filter handlers
  topicPills.forEach(pill => {
    pill.addEventListener('click', () => {
      topicPills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      activeTopic = pill.dataset.topic;
      renderPublications();
    });
  });
});

function getPubYear(pub) {
  if (pub.year && /^\d{4}$/.test(String(pub.year).trim())) {
    return parseInt(pub.year, 10);
  }
  const ygMatch = (pub.year_group || '').match(/\b(19\d\d|20\d\d)\b/);
  if (ygMatch) return parseInt(ygMatch[0], 10);
  const citMatch = (pub.citation || '').match(/\b(19\d\d|20\d\d)\b/);
  if (citMatch) return parseInt(citMatch[0], 10);
  return 0;
}

function filterPublications() {
  return allPublications.filter(pub => {
    // Year matching
    let matchesYear = true;
    if (activeYear !== 'all') {
      const yg = (pub.year_group || pub.year || '').toLowerCase();
      if (activeYear === 'preprint') {
        matchesYear = yg.includes('rxiv') || yg.includes('submitted') || yg.includes('preprint');
      } else if (activeYear === 'older') {
        const y = getPubYear(pub);
        matchesYear = y > 0 && y <= 2018;
      } else {
        const y = getPubYear(pub);
        matchesYear = yg.includes(activeYear) || String(y) === activeYear;
      }
    }

    // Topic matching
    let matchesTopic = true;
    if (activeTopic !== 'all') {
      matchesTopic = pub.topics && pub.topics.some(t => t.toLowerCase() === activeTopic.toLowerCase());
    }

    // Search query matching
    let matchesSearch = true;
    if (searchQuery) {
      const fullContent = (pub.citation + ' ' + (pub.bibtex || '') + ' ' + (pub.topics ? pub.topics.join(' ') : '') + ' ' + (pub.year_group || '') + ' ' + (pub.year || '')).toLowerCase();
      matchesSearch = fullContent.includes(searchQuery);
    }

    return matchesYear && matchesTopic && matchesSearch;
  });
}

function renderPublications() {
  const container = document.getElementById('publications-container');
  const countBadge = document.getElementById('pub-count-badge');
  if (!container) return;

  const filtered = filterPublications();
  if (countBadge) {
    countBadge.innerText = `Showing ${filtered.length} of ${allPublications.length} publications`;
  }

  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="card" style="text-align: center; padding: 3rem 1.5rem; margin: 2rem 0;">
        <h3 style="margin-bottom: 0.5rem;">No publications found</h3>
        <p style="color: var(--text-muted);">Try adjusting your search keywords or clearing filter pills.</p>
      </div>
    `;
    return;
  }

  // Helper to get numeric weight for sorting
  function getYearWeight(yearGroupStr, firstPub) {
    const s = (yearGroupStr || '').toLowerCase();
    if (s.includes('rxiv') || s.includes('submitted') || s.includes('preprint') || s.includes('review')) {
      return 9999;
    }
    const yrMatch = s.match(/\b(19\d\d|20\d\d)\b/);
    if (yrMatch) return parseInt(yrMatch[0], 10);
    if (firstPub) return getPubYear(firstPub);
    return 0;
  }

  // Group by year / year_group using an ordered Map (prevents JS numeric key auto-sort bug)
  const groupMap = new Map();
  filtered.forEach(pub => {
    const groupName = pub.year_group || (pub.year ? String(pub.year) : 'Other');
    if (!groupMap.has(groupName)) {
      groupMap.set(groupName, []);
    }
    groupMap.get(groupName).push(pub);
  });

  // Convert to array of [groupName, pubs]
  let sortedGroups = Array.from(groupMap.entries());

  // Sort groups by year weight (Default: Newest First)
  sortedGroups.sort((a, b) => {
    const weightA = getYearWeight(a[0], a[1][0]);
    const weightB = getYearWeight(b[0], b[1][0]);
    if (sortOrder === 'newest') {
      return weightB - weightA;
    } else {
      return weightA - weightB;
    }
  });

  let html = '';
  for (const [groupName, pubs] of sortedGroups) {
    html += `
      <div class="pub-year-group">
        <h3 class="pub-year-heading">
          <span>${groupName}</span>
          <span class="pub-year-count">${pubs.length} paper${pubs.length > 1 ? 's' : ''}</span>
        </h3>
        <div class="pub-items-list">
    `;

    pubs.forEach(pub => {
      const topicBadges = (pub.topics || []).map(t => `<span class="tag tag-accent">${t}</span>`).join(' ');
      
      let linkButtons = '';
      if (pub.preprint_url) {
        linkButtons += `<a href="${pub.preprint_url}" target="_blank" rel="noopener" class="pub-btn pub-btn-primary">Preprint</a>`;
      }
      if (pub.paper_url) {
        linkButtons += `<a href="${pub.paper_url}" target="_blank" rel="noopener" class="pub-btn">Paper / DOI</a>`;
      }
      if (pub.code_url) {
        linkButtons += `<a href="${pub.code_url}" target="_blank" rel="noopener" class="pub-btn">Data & Code</a>`;
      }

      html += `
        <article class="pub-card" id="${pub.id}">
          <div class="pub-citation-text">${getPublicationCitationHtml(pub)}</div>
          <div class="pub-meta-row">
            <div class="pub-topic-tags">${topicBadges}</div>
            <div class="pub-badge-links">
              ${linkButtons}
              <button class="pub-btn" onclick="copyCitation('${pub.id}')" title="Copy formatted citation to clipboard">
                <svg viewBox="0 0 24 24"><path d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/></svg>
                Copy
              </button>
              <button class="pub-btn" onclick="openBibtexModal('${pub.id}')" title="View and copy BibTeX entry">
                BibTeX
              </button>
            </div>
          </div>
        </article>
      `;
    });

    html += `
        </div>
      </div>
    `;
  }

  container.innerHTML = html;
}

/**
 * Robust BibTeX Parser
 * Extracts fields from standard and Crossref BibTeX entries.
 */
function parseBibtexFields(raw) {
  if (!raw || typeof raw !== 'string') return null;
  const str = raw.trim();
  if (!str.startsWith('@')) return null;

  const firstBrace = str.indexOf('{');
  if (firstBrace === -1) return null;

  const fields = {};
  let pos = firstBrace + 1;
  const firstComma = str.indexOf(',', pos);
  if (firstComma === -1) return null;
  pos = firstComma + 1;

  while (pos < str.length) {
    while (pos < str.length && /[\s,]/.test(str[pos])) pos++;
    if (pos >= str.length || str[pos] === '}') break;

    const nameMatch = str.slice(pos).match(/^([a-zA-Z_][a-zA-Z0-9_\-]*)\s*=/);
    if (!nameMatch) {
      pos++;
      continue;
    }
    const fieldName = nameMatch[1].toLowerCase();
    pos += nameMatch[0].length;

    while (pos < str.length && /\s/.test(str[pos])) pos++;

    let val = '';
    if (str[pos] === '{') {
      let depth = 1;
      pos++;
      const startVal = pos;
      while (pos < str.length && depth > 0) {
        if (str[pos] === '{') depth++;
        else if (str[pos] === '}') depth--;
        pos++;
      }
      val = str.slice(startVal, pos - 1);
    } else if (str[pos] === '"') {
      pos++;
      const startVal = pos;
      while (pos < str.length && str[pos] !== '"') {
        if (str[pos] === '\\') pos++;
        pos++;
      }
      val = str.slice(startVal, pos);
      if (str[pos] === '"') pos++;
    } else {
      const startVal = pos;
      while (pos < str.length && !/[\s,}]/.test(str[pos])) pos++;
      val = str.slice(startVal, pos);
    }

    fields[fieldName] = val.replace(/\{|\}/g, '').replace(/\s+/g, ' ').trim();
  }

  // Validate if valid article metadata exists
  const journal = (fields.journal || fields.journaltitle || fields.booktitle || '').trim();
  if (!journal || journal.toLowerCase() === 'conscious brain lab publications') {
    return null; // Fallback to full citation text
  }
  if (!fields.author && !fields.title) {
    return null;
  }

  return fields;
}

/**
 * Format a single author in APA 7 style: Lastname, Initials.
 */
function formatAuthorAPA(authorStr) {
  if (!authorStr) return '';
  const trimmed = authorStr.trim();
  const parts = trimmed.split(/\s*,\s*/);
  if (parts.length >= 2) {
    const lastName = parts[0].trim();
    const givenNames = parts[1].trim().split(/\s+/);
    const initials = givenNames.map(g => g.charAt(0).toUpperCase() + '.').join(' ');
    return initials ? `${lastName}, ${initials}` : lastName;
  }
  const tokens = trimmed.split(/\s+/);
  if (tokens.length === 1) return tokens[0];
  const lastName = tokens.pop();
  const initials = tokens.map(t => t.charAt(0).toUpperCase() + '.').join(' ');
  return initials ? `${lastName}, ${initials}` : lastName;
}

/**
 * Format author list in APA 7 style (with '&' before last author, et al. for >20 authors)
 */
function formatAuthorsListAPA(authorsRaw) {
  if (!authorsRaw) return '';
  const authors = authorsRaw.split(/\s+and\s+/i).map(a => a.trim()).filter(Boolean);
  if (authors.length === 0) return '';

  const formatted = authors.map(formatAuthorAPA);
  if (formatted.length === 1) {
    return formatted[0];
  } else if (formatted.length === 2) {
    return `${formatted[0]}, & ${formatted[1]}`;
  } else if (formatted.length <= 20) {
    const allExceptLast = formatted.slice(0, -1).join(', ');
    return `${allExceptLast}, & ${formatted[formatted.length - 1]}`;
  } else {
    const first19 = formatted.slice(0, 19).join(', ');
    return `${first19}, … ${formatted[formatted.length - 1]}`;
  }
}

/**
 * Permissively highlights Conscious Brain Lab PIs / lab heads in bold.
 * Matches:
 *  - Johannes Fahrenfort: J.J.Fahrenfort, J. J. Fahrenfort, Fahrenfort, J.J., Fahrenfort, J. J., Fahrenfort, J., Johannes Fahrenfort, etc.
 *  - Simon van Gaal: van Gaal, S., Van Gaal, S., Gaal, S. van, Gaal, Simon van, Simon van Gaal, S. van Gaal, Van Gaal, van Gaal, etc.
 *  - Timo Stein: Stein, T., Stein, Timo, Timo Stein, T. Stein, T.Stein, etc.
 */
function highlightPINames(text) {
  if (!text) return '';

  // Clean any preexisting <strong> around PI names to prevent duplicate tags
  let cleaned = text.replace(/<strong>(.*?)<\/strong>/gi, '$1');

  // Permissive patterns for each PI
  const fahrenfort = '(?:(?:Johannes(?:\\s+Jacobus|\\s+J(?:\\.|\\b))?|J\\s*\\.\\s*J(?:\\.|\\b)|J\\s*\\.|JJ\\b)\\s*Fahrenfort|Fahrenfort,\\s*(?:Johannes(?:\\s+Jacobus|\\s+J(?:\\.|\\b))?|J\\s*\\.\\s*J(?:\\.|\\b)|J\\s*\\.|JJ\\b|J\\b)|Fahrenfort\\s+(?:JJ\\b|J\\b)|Fahrenfort\\b)';
  const vangaal = '(?:Gaal,\\s*(?:Simon\\b|S\\s*\\.|S\\b)?\\s*,?\\s*[Vv](?:an\\b|\\.)|[Vv]an\\s+Gaal(?:,\\s*(?:Simon\\b|S\\s*\\.|S\\b))?|(?:Simon\\b|S\\s*\\.|S\\b)\\s*[Vv]an\\s+Gaal|[Vv]an\\s+Gaal\\b)';
  const stein = '(?:Stein,\\s*(?:Timo\\b|T\\s*\\.|T\\b)|(?:Timo\\b|T\\s*\\.|T\\b)\\s*Stein|Stein\\s+T\\b)';

  const piRegex = new RegExp(`\\b(${fahrenfort}|${vangaal}|${stein})`, 'gi');
  return cleaned.replace(piRegex, '<strong>$1</strong>');
}

/**
 * Format a BibTeX fields object into complete APA 7 HTML
 */
function formatBibtexAPA(fields) {
  const authors = formatAuthorsListAPA(fields.author);
  const year = fields.year ? `(${fields.year}).` : '';

  let title = (fields.title || '').trim();
  if (title && !/[.!?]$/.test(title)) {
    title += '.';
  }

  const journal = (fields.journal || fields.journaltitle || fields.booktitle || '').trim();
  const volume = (fields.volume || '').trim();
  const issue = (fields.number || fields.issue || '').trim();
  const pages = (fields.pages || '').trim();

  let pubDetails = '';
  if (journal) {
    pubDetails += `<em>${journal}</em>`;
    if (volume) {
      pubDetails += `, <em>${volume}</em>`;
      if (issue) pubDetails += `(${issue})`;
    } else if (issue) {
      pubDetails += `(${issue})`;
    }
    if (pages) {
      const cleanPages = pages.replace(/--/g, '–');
      pubDetails += `, ${cleanPages}`;
    }
    if (!pubDetails.endsWith('.')) {
      pubDetails += '.';
    }
  }

  const parts = [authors, year, title, pubDetails].filter(Boolean);
  let html = parts.join(' ');

  // Highlight lab heads / PIs in bold
  html = highlightPINames(html);
  return html;
}

/**
 * Main Publication Formatter:
 * Uses BibTeX APA style when present; otherwise falls back to full citation text.
 */
function getPublicationCitationHtml(pub) {
  if (pub.bibtex && pub.bibtex.trim()) {
    const fields = parseBibtexFields(pub.bibtex);
    if (fields) {
      const apaHtml = formatBibtexAPA(fields);
      if (apaHtml) return apaHtml;
    }
  }
  // Fallback to full citation text
  return formatFallbackCitation(pub.citation || '');
}

/**
 * Formats fallback citation text: highlights PIs and italicizes known journal names
 */
function formatFallbackCitation(text) {
  if (!text) return '';
  let cleaned = text.replace(/\s*\b(?:CLOCKSS|LOCKSS)\b\.?\s*$/i, '').trim();
  if (cleaned && !cleaned.endsWith('.')) cleaned += '.';
  let formatted = highlightPINames(cleaned);

  const commonJournals = [
    'Nature Human Behavior', 'Nature Human Behaviour', 'Nature Neuroscience', 'Nature Communications', 'Nature',
    'The Journal of Neuroscience', 'Journal of Neuroscience Methods', 'Journal of Cognitive Neuroscience', 'Journal of Neuroscience', 'Journal of Vision', 'Journal of Neurology',
    'Trends in Cognitive Sciences', 'Trends in Neurosciences',
    'Philosophical Transactions of the Royal Society: B', 'Philosophical Transactions of the Royal Society B',
    'Consciousness and Cognition', 'Communications Biology', 'Communications Psychology',
    'PLOS Biology', 'PLOS Computational Biology', 'PLOS ONE', 'PLoS ONE',
    'NeuroImage: Clinical', 'Neuroimage: Reports', 'NeuroImage', 'Neuroimage',
    'Frontiers in Human Neuroscience', 'Frontiers in Neuroscience', 'Frontiers in Psychology',
    'eNeuro', 'eLife', 'Cerebral Cortex', 'Current Biology', 'Behavioral and Brain Sciences',
    'Neuroscience and Biobehavioral Reviews', 'Neuroscience & Biobehavioral Reviews', 'Neuroscience of Consciousness',
    'Cognitive Neuroscience', 'Attention, Perception, & Psychophysics', 'Psychological Science', 'Cognition', 'Brain',
    'Neuropsychologia', 'Scientific Reports'
  ];

  for (const j of commonJournals) {
    const reg = new RegExp('\\b(' + j.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')\\b', 'g');
    if (reg.test(formatted)) {
      formatted = formatted.replace(reg, '<em>$1</em>');
      break;
    }
  }

  return formatted;
}

function copyCitation(pubId) {
  const pub = allPublications.find(p => p.id === pubId);
  if (!pub) return;
  let textToCopy = '';
  if (pub.bibtex && pub.bibtex.trim()) {
    const fields = parseBibtexFields(pub.bibtex);
    if (fields) {
      textToCopy = formatBibtexAPA(fields).replace(/<[^>]+>/g, '');
    }
  }
  if (!textToCopy) {
    let raw = (pub.citation || '').replace(/\s*\b(?:CLOCKSS|LOCKSS)\b\.?\s*$/i, '').trim();
    if (raw && !raw.endsWith('.')) raw += '.';
    textToCopy = raw;
  }
  navigator.clipboard.writeText(textToCopy).then(() => {
    showToast('Citation copied to clipboard!');
  }).catch(() => {
    showToast('Failed to copy citation.');
  });
}

function openBibtexModal(pubId) {
  const pub = allPublications.find(p => p.id === pubId);
  if (!pub) return;

  let modal = document.getElementById('bibtex-modal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'bibtex-modal';
    modal.className = 'modal-overlay';
    document.body.appendChild(modal);
  }

  modal.innerHTML = `
    <div class="modal-box">
      <div class="modal-header">
        <h3 class="modal-title">BibTeX Citation</h3>
        <button class="modal-close-btn" onclick="closeBibtexModal()">&times;</button>
      </div>
      <pre class="modal-code-block"><code>${escapeHtml(pub.bibtex)}</code></pre>
      <div style="display: flex; justify-content: flex-end; gap: 0.75rem;">
        <button class="btn btn-secondary" onclick="closeBibtexModal()">Close</button>
        <button class="btn btn-primary" onclick="copyBibtex('${pub.id}')">Copy BibTeX</button>
      </div>
    </div>
  `;

  modal.classList.add('open');
  modal.addEventListener('click', (e) => {
    if (e.target === modal) closeBibtexModal();
  });
}

function closeBibtexModal() {
  const modal = document.getElementById('bibtex-modal');
  if (modal) modal.classList.remove('open');
}

function copyBibtex(pubId) {
  const pub = allPublications.find(p => p.id === pubId);
  if (!pub) return;
  navigator.clipboard.writeText(pub.bibtex).then(() => {
    showToast('BibTeX copied to clipboard!');
    closeBibtexModal();
  });
}

function escapeHtml(string) {
  return String(string).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
