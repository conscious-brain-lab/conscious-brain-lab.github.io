/**
 * Dynamic Open Positions Renderer
 * Loads items dynamically from data/positions.json (edited via Decap CMS)
 */

async function initPositions() {
  const container = document.getElementById('positions-grid') || document.querySelector('.grid-2');
  if (!container) return;

  try {
    const res = await fetch('/data/positions.json?t=' + Date.now(), {
      cache: 'no-cache',
      headers: { 'Cache-Control': 'no-cache' }
    });
    if (!res.ok) return;
    const rawData = await res.json();
    const items = Array.isArray(rawData) ? rawData : (rawData && rawData.items ? rawData.items : []);
    if (!Array.isArray(items) || items.length === 0) return;

    container.innerHTML = items.map(item => {
      const title = item.title || '';
      const icon = item.icon || '🎓';
      const description = item.description || '';
      const buttonText = item.button_text || 'Inquire with the Lab';
      const buttonLink = item.button_link || 'mailto:consciousbrainlab@gmail.com';
      const tag = item.tag ? `<span class="tag tag-accent" style="margin-bottom: 0.5rem; display: inline-block;">${item.tag}</span>` : '';

      return `
        <div class="card" id="position-${item.slug || ''}">
          <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div class="card-icon-box">${icon}</div>
            ${tag}
          </div>
          <h2 class="card-title">${title}</h2>
          <p class="card-description">${description.replace(/\n\n/g, '</p><p class="card-description">')}</p>
          ${buttonLink ? `<a href="${buttonLink}" class="btn btn-secondary" style="margin-top: 1rem;">${buttonText}</a>` : ''}
        </div>
      `;
    }).join('');

  } catch (err) {
    console.warn('Could not load dynamic positions:', err);
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initPositions);
} else {
  initPositions();
}
