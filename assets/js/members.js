/**
 * Members & Alumni Interactive Module
 * Filtering by Role/Status, Search, and Bio Details
 */

let allMembers = [];
let activeRole = 'all';
let memberSearchQuery = '';

document.addEventListener('DOMContentLoaded', async () => {
  const container = document.getElementById('members-grid');
  const searchInput = document.getElementById('member-search-input');
  const filterBtns = document.querySelectorAll('.member-filter-btn');

  try {
    const res = await fetch('/data/members.json?t=' + Date.now(), {
      cache: 'no-cache',
      headers: { 'Cache-Control': 'no-cache' }
    });
    if (!res.ok) throw new Error('Failed to load members data');
    allMembers = await res.json();
    renderMembers();
  } catch (err) {
    console.error(err);
    if (container) {
      container.innerHTML = `<p class="error-msg">Could not load lab members. Please refresh.</p>`;
    }
  }

  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      memberSearchQuery = e.target.value.toLowerCase().trim();
      renderMembers();
    });
  }

  function setRoleFilter(role, updateHash = true) {
    activeRole = role;
    filterBtns.forEach(b => {
      if (b.dataset.role === role) {
        b.classList.add('active');
      } else {
        b.classList.remove('active');
      }
    });
    if (updateHash && window.location.hash !== '#' + role) {
      if (role === 'all') {
        history.replaceState(null, '', window.location.pathname);
      } else {
        history.replaceState(null, '', '#' + role);
      }
    }
    renderMembers();
  }

  filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      setRoleFilter(btn.dataset.role);
    });
  });

  function checkHash() {
    const rawHash = window.location.hash.replace('#', '').toLowerCase();
    if (['all', 'pi', 'current', 'postdoc', 'phd', 'alumni'].includes(rawHash)) {
      setRoleFilter(rawHash, false);
    }
  }

  // Listen to hash changes (e.g. from top nav dropdown clicks)
  window.addEventListener('hashchange', checkHash);
  checkHash();
});

function filterMembersList() {
  return allMembers.filter(m => {
    let matchesRole = true;
    if (activeRole !== 'all') {
      if (activeRole === 'pi') {
        matchesRole = m.category === 'pi';
      } else if (activeRole === 'current') {
        matchesRole = m.status === 'current';
      } else if (activeRole === 'postdoc') {
        matchesRole = m.category === 'postdoc' && m.status !== 'alumni';
      } else if (activeRole === 'phd') {
        matchesRole = m.category === 'phd' && m.status !== 'alumni';
      } else if (activeRole === 'alumni') {
        matchesRole = m.status === 'alumni' || m.category === 'alumni';
      }
    }

    let matchesSearch = true;
    if (memberSearchQuery) {
      const full = (m.name + ' ' + m.role + ' ' + m.bio).toLowerCase();
      matchesSearch = full.includes(memberSearchQuery);
    }

    return matchesRole && matchesSearch;
  });
}

function renderMembers() {
  const container = document.getElementById('members-grid');
  if (!container) return;

  const filtered = filterMembersList();

  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="card" style="grid-column: 1 / -1; text-align: center; padding: 3rem 1.5rem;">
        <h3>No members found</h3>
        <p style="color: var(--text-muted);">Try adjusting your search query or role filter.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = filtered.map(m => {
    const isAlumni = m.status === 'alumni';
    const statusBadge = isAlumni ? '<span class="tag">Alumni</span>' : '<span class="tag tag-accent">Current Team</span>';
    const initial = m.name.charAt(0);
    
    // Render actual image if available
    let avatarHtml;
    if (m.image) {
      const srcWithVersion = m.image + (m.image.includes('?') ? '&' : '?') + 'v=3';
      avatarHtml = `<img src="${srcWithVersion}" alt="${m.name}" loading="lazy" style="width:100%; height:100%; object-fit:cover; border-radius:50%;" onerror="this.style.display='none'; this.parentElement.innerText='${initial}';" />`;
    } else {
      avatarHtml = `<div style="width:100%; height:100%; display:flex; align-items:center; justify-content:center; background:var(--brand-gradient); color:#fff; font-weight:700; font-size:2rem; border-radius:50%;">${initial}</div>`;
    }

    return `
      <article class="card member-card" id="member-${m.slug}">
        <div class="member-avatar">${avatarHtml}</div>
        <div style="margin-bottom: 0.5rem;">${statusBadge}</div>
        <h3 class="member-name">${m.name}</h3>
        <p class="member-role">${m.role}</p>
        <p class="member-bio">${m.bio}</p>
        <div class="member-links">
          ${m.link ? `<a href="${m.link}" target="_blank" rel="noopener" class="icon-btn" title="External Profile / UvA"><svg viewBox="0 0 24 24"><path d="M19 19H5V5h7V3H5c-1.11 0-2 .9-2 2v14c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2v-7h-2v7zM14 3v2h3.59l-9.83 9.83 1.41 1.41L19 6.41V10h2V3h-7z"/></svg></a>` : ''}
          <button class="icon-btn" onclick="openBioModal('${m.slug}')" title="Read full bio"><svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/></svg></button>
        </div>
      </article>
    `;
  }).join('');
}

function openBioModal(slug) {
  const member = allMembers.find(m => m.slug === slug);
  if (!member) return;

  let modal = document.getElementById('bio-modal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'bio-modal';
    modal.className = 'modal-overlay';
    document.body.appendChild(modal);
  }

  const initial = member.name.charAt(0);
  const avatarHtml = member.image ? `<img src="${member.image}" alt="${member.name}" style="width:100px; height:100px; border-radius:50%; object-fit:cover; border:3px solid var(--accent-light);" />` : `<div style="width:100px; height:100px; border-radius:50%; background:var(--brand-gradient); color:#fff; display:flex; align-items:center; justify-content:center; font-size:2rem; font-weight:700;">${initial}</div>`;

  modal.innerHTML = `
    <div class="modal-box">
      <div class="modal-header">
        <div style="display:flex; align-items:center; gap:1rem;">
          ${avatarHtml}
          <div>
            <h3 class="modal-title">${member.name}</h3>
            <p style="color:var(--accent-primary); font-weight:600; font-size:0.9rem; margin:0;">${member.role}</p>
          </div>
        </div>
        <button class="modal-close-btn" onclick="closeBioModal()">&times;</button>
      </div>
      <div style="margin: 1.5rem 0; line-height: 1.8; color: var(--text-secondary);">
        ${member.bio.replace(/\n\n/g, '<br><br>')}
      </div>
      <div style="display: flex; justify-content: space-between; align-items:center; border-top: 1px solid var(--border-color); padding-top: 1rem;">
        ${member.link ? `<a href="${member.link}" target="_blank" rel="noopener" class="btn btn-secondary" style="font-size:0.85rem;">University Profile &rarr;</a>` : '<span></span>'}
        <button class="btn btn-primary" onclick="closeBioModal()">Close</button>
      </div>
    </div>
  `;

  modal.classList.add('open');
  modal.addEventListener('click', (e) => {
    if (e.target === modal) closeBioModal();
  });
}

function closeBioModal() {
  const modal = document.getElementById('bio-modal');
  if (modal) modal.classList.remove('open');
}
