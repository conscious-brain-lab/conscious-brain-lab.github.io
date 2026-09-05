/**
 * Dynamic Research Projects Renderer
 * Loads items dynamically from data/projects.json (compiled from content/projects/*.json via Decap CMS)
 */

async function initProjects() {
  const container = document.querySelector('.projects-grid');
  if (!container) return;

  try {
    const res = await fetch('/data/projects.json?t=' + Date.now(), {
      cache: 'no-cache',
      headers: { 'Cache-Control': 'no-cache' }
    });
    if (!res.ok) return;
    const items = await res.json();
    if (!Array.isArray(items) || items.length === 0) return;

    // Sort by order ascending (default 99), then title
    items.sort((a, b) => {
      const orderA = typeof a.order === 'number' ? a.order : parseInt(a.order, 10) || 99;
      const orderB = typeof b.order === 'number' ? b.order : parseInt(b.order, 10) || 99;
      if (orderA !== orderB) return orderA - orderB;
      return (a.title || '').localeCompare(b.title || '');
    });

    container.innerHTML = items.map(item => {
      const title = item.title || '';
      const tag = item.tag ? `<span class="tag tag-accent project-card-tag">${item.tag}</span>` : '';
      const desc = item.description || '';
      const img = item.image || '';
      const slug = item.slug || '';
      const fit = item.fit === 'contain' ? 'contain' : 'cover';
      const fitStyle = fit === 'contain'
        ? 'object-fit: contain; padding: 1.5rem;'
        : 'object-fit: cover;';
      const wrapStyle = fit === 'contain' ? 'style="background: #ffffff;"' : '';

      const imgHtml = img ? `
        <div class="project-card-img-wrap" ${wrapStyle}>
          <img src="${img}" alt="${title}" class="project-card-img" style="${fitStyle}" onerror="this.parentElement.style.display='none';" />
        </div>
      ` : '';

      return `
        <article class="project-card" id="project-${slug}">
          ${imgHtml}
          <div class="project-card-body">
            ${tag}
            <h2 class="project-card-title">${title}</h2>
            <p class="project-card-desc">${desc.replace(/\n\n/g, '</p><p class="project-card-desc">')}</p>
          </div>
        </article>
      `;
    }).join('');

  } catch (err) {
    console.warn('Could not load dynamic projects:', err);
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initProjects);
} else {
  initProjects();
}
