/**
 * Publications Interactive Module
 * Real-time Search, Year/Topic Filtering, BibTeX Modal & Citation Copy
 */

let allPublications = [];
let activeYear = 'all';
let activeTopic = 'all';
let searchQuery = '';

document.addEventListener('DOMContentLoaded', async () => {
  const container = document.getElementById('publications-container');
  const searchInput = document.getElementById('pub-search-input');
  const countBadge = document.getElementById('pub-count-badge');
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

function filterPublications() {
  return allPublications.filter(pub => {
    // Year matching
    let matchesYear = true;
    if (activeYear !== 'all') {
      if (activeYear === 'preprint') {
        matchesYear = pub.year_group.toLowerCase().includes('rxiv') || pub.year_group.toLowerCase().includes('submitted');
      } else if (activeYear === 'older') {
        const y = parseInt(pub.year, 10);
        matchesYear = !isNaN(y) && y <= 2018;
      } else {
        matchesYear = pub.year === activeYear || pub.year_group.includes(activeYear);
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
      const fullContent = (pub.citation + ' ' + (pub.topics ? pub.topics.join(' ') : '') + ' ' + pub.year).toLowerCase();
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

  // Group by year / year_group
  const groups = {};
  filtered.forEach(pub => {
    const groupName = pub.year_group || pub.year || 'Other';
    if (!groups[groupName]) groups[groupName] = [];
    groups[groupName].push(pub);
  });

  let html = '';
  for (const [groupName, pubs] of Object.entries(groups)) {
    html += `
      <div class="pub-year-group">
        <h3 class="pub-year-heading">
          <span>${groupName}</span>
          <span class="pub-year-count">${pubs.length} paper${pubs.length > 1 ? 's' : ''}</span>
        </h3>
        <div class="pub-items-list">
    `;

    pubs.forEach(pub => {
      // Build badges
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
          <div class="pub-citation-text">${formatCitation(pub.citation)}</div>
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

function formatCitation(text) {
  // Highlight authors if known
  return text
    .replace(/(van Gaal, S\.|Fahrenfort, J\.J\.|Stein, T\.)/g, '<strong>$1</strong>');
}

function copyCitation(pubId) {
  const pub = allPublications.find(p => p.id === pubId);
  if (!pub) return;
  navigator.clipboard.writeText(pub.citation).then(() => {
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
