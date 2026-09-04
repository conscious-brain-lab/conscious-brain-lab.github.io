/**
 * Dynamic Lab & Campus Impressions Renderer
 * Loads items dynamically from data/impressions.json (edited via Decap CMS)
 */

async function initImpressions() {
  const container = document.getElementById('impressions-grid') || document.querySelector('.grid-2');
  if (!container) return;

  try {
    const res = await fetch('/data/impressions.json?t=' + Date.now(), {
      cache: 'no-cache',
      headers: { 'Cache-Control': 'no-cache' }
    });
    if (!res.ok) return;
    const items = await res.json();
    if (!Array.isArray(items) || items.length === 0) return;

    // Sort by order ascending, fallback to title
    items.sort((a, b) => {
      const orderA = parseInt(a.order ?? 99, 10);
      const orderB = parseInt(b.order ?? 99, 10);
      if (orderA !== orderB) return orderA - orderB;
      return (a.title || '').localeCompare(b.title || '');
    });

    container.innerHTML = items.map(item => {
      const title = item.title || '';
      const tag = item.tag || '';
      const date = item.date || '';
      const image = item.image || '';
      const description = item.description || '';

      const imgHtml = image
        ? `<img src="${image}" alt="${title}" style="width: 100%; height: 100%; object-fit: cover; transition: transform 0.3s ease;" onmouseover="this.style.transform='scale(1.03)'" onmouseout="this.style.transform='scale(1)'" loading="lazy" onerror="this.parentElement.style.display='none';" />`
        : '';

      return `
        <article class="card" style="padding: 0; overflow: hidden; border-radius: var(--radius-lg); box-shadow: var(--shadow-md);" id="impression-${item.slug || ''}">
          <div style="width: 100%; height: 280px; overflow: hidden; background: var(--bg-tertiary);">
            ${imgHtml}
          </div>
          <div style="padding: 1.5rem;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; flex-wrap: wrap; gap: 0.5rem;">
              ${tag ? `<span class="tag tag-accent">${tag}</span>` : '<span></span>'}
              ${date ? `<span style="font-size: 0.85rem; color: var(--text-muted); font-weight: 600;">${date}</span>` : ''}
            </div>
            <h3 style="margin-bottom: 0.5rem; font-size: 1.3rem;">${title}</h3>
            <p style="color: var(--text-secondary); line-height: 1.6; margin: 0;">${description}</p>
          </div>
        </article>
      `;
    }).join('');

  } catch (err) {
    console.warn('Could not load dynamic impressions:', err);
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initImpressions);
} else {
  initImpressions();
}
