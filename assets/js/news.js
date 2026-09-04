/**
 * Conscious Brain Lab - Dynamic News Renderer
 * Renders news and talks in chronological order from data/news.json
 */

document.addEventListener('DOMContentLoaded', async () => {
  const newsGrid = document.querySelector('.news-grid');
  if (!newsGrid) return;

  try {
    const res = await fetch('../data/news.json');
    if (!res.ok) return; // Keep server-rendered/static cards on error
    const newsItems = await res.json();
    if (!Array.isArray(newsItems) || newsItems.length === 0) return;

    // Sort by date_sort descending (newest first)
    newsItems.sort((a, b) => {
      const dateA = a.date_sort || '2000-01';
      const dateB = b.date_sort || '2000-01';
      return dateB.localeCompare(dateA);
    });

    newsGrid.innerHTML = newsItems.map(item => {
      const imgSrc = item.image || item.wix_url || '';
      const imgPos = item.position || 'center 20%';
      const title = item.title || 'News Update';
      const date = item.date || '';
      const text = item.text || '';
      const link = item.link || '';

      const imgHtml = imgSrc 
        ? `<div class="news-card-img-wrap">
             <img src="${imgSrc}" alt="${title}" class="news-card-img" style="object-fit: cover; object-position: ${imgPos};" onerror="this.parentElement.style.display='none';" />
           </div>`
        : '';

      const linkHtml = link 
        ? `<div style="margin-top: 0.75rem;">
             <a href="${link}" target="_blank" rel="noopener noreferrer" class="btn btn-secondary" style="font-size: 0.8rem; padding: 0.35rem 0.75rem;">
               Read More &rarr;
             </a>
           </div>`
        : '';

      return `
        <article class="news-card">
          ${imgHtml}
          <div class="news-card-body">
            ${date ? `<span class="news-card-date">${date}</span>` : ''}
            <h3 class="news-card-title">${title}</h3>
            <p class="news-card-desc">${text}</p>
            ${linkHtml}
          </div>
        </article>
      `;
    }).join('');

  } catch (err) {
    console.warn('Could not load dynamic news:', err);
  }
});
