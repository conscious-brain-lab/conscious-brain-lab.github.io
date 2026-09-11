/**
 * Conscious Brain Lab - Dynamic News Renderer
 * Renders news and talks in chronological order from data/news.json
 * Supports images, YouTube video embeds, and direct HTML5 MP4 videos.
 */

function getYouTubeEmbedUrl(url) {
  if (!url || typeof url !== 'string') return null;
  const match = url.match(/(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=|shorts\/))([\w-]{11})/i);
  return match ? `https://www.youtube-nocookie.com/embed/${match[1]}` : null;
}

function isDirectVideoFile(url) {
  if (!url || typeof url !== 'string') return false;
  const clean = url.split('?')[0].toLowerCase();
  return clean.endsWith('.mp4') || clean.endsWith('.webm') || clean.endsWith('.mov') || clean.endsWith('.ogg');
}

function renderNewsMedia(item, title, imgPos, index = 0) {
  const videoSource = item.video || (isDirectVideoFile(item.image) || getYouTubeEmbedUrl(item.image) ? item.image : '');
  const ytEmbed = getYouTubeEmbedUrl(videoSource);

  if (ytEmbed) {
    const iframeLoading = index < 3 ? 'eager' : 'lazy';
    return `
      <div class="news-card-video-wrap">
        <iframe src="${ytEmbed}" title="${title}" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen loading="${iframeLoading}"></iframe>
      </div>
    `;
  }

  if (isDirectVideoFile(videoSource)) {
    const videoPreload = index < 3 ? 'auto' : 'metadata';
    return `
      <div class="news-card-video-wrap">
        <video src="${videoSource}" controls playsinline preload="${videoPreload}" class="news-card-video"></video>
      </div>
    `;
  }

  const imgSrc = item.image || '';
  if (imgSrc) {
    // Only mark as logo if explicitly configured as logo or contain; default to photo (object-fit: cover) matching Impressions
    const isLogo = item.type === 'logo' || item.fit === 'contain' || item.position === 'contain';

    const fitStyle = isLogo
      ? 'object-fit: contain; background: var(--bg-tertiary);'
      : `object-fit: cover; object-position: ${imgPos};`;

    // Automatically prioritize top 3 cards (entire top row) on any screen
    const isTopCard = index < 3;
    const loadingAttrs = isTopCard
      ? 'loading="eager" fetchpriority="high" decoding="async"'
      : 'loading="lazy" decoding="async"';

    return `
      <div class="news-card-img-wrap">
        <img src="${imgSrc}" alt="${title}" class="news-card-img ${isLogo ? 'news-card-logo' : ''}" data-type="${item.type || 'photo'}" ${loadingAttrs} style="${fitStyle}" onerror="this.parentElement.style.display='none';" />
      </div>
    `;
  }

  return '';
}

async function initNews() {
  const newsGrid = document.querySelector('.news-grid');
  if (!newsGrid) return;

  try {
    const res = await fetch('/data/news.json?t=' + Date.now(), {
      cache: 'no-cache',
      headers: { 'Cache-Control': 'no-cache' }
    });
    if (!res.ok) return;
    const newsItems = await res.json();
    if (!Array.isArray(newsItems) || newsItems.length === 0) return;

    // Sort by date_sort descending (newest first)
    newsItems.sort((a, b) => {
      const dateA = a.date_sort || '2000-01';
      const dateB = b.date_sort || '2000-01';
      return dateB.localeCompare(dateA);
    });

    newsGrid.innerHTML = newsItems.map((item, index) => {
      const imgPos = item.position || 'center 20%';
      const title = item.title || 'News Update';
      const date = item.date || '';
      const text = item.text || '';
      const link = item.link || '';

      const mediaHtml = renderNewsMedia(item, title, imgPos, index);

      const linkHtml = link 
        ? `<div style="margin-top: 0.75rem;">
             <a href="${link}" target="_blank" rel="noopener noreferrer" class="btn btn-secondary" style="font-size: 0.8rem; padding: 0.35rem 0.75rem;">
               Read More &rarr;
             </a>
           </div>`
        : '';

      return `
        <article class="news-card">
          ${mediaHtml}
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
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initNews);
} else {
  initNews();
}
