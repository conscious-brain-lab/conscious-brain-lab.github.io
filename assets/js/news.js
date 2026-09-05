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

function renderNewsMedia(item, title, imgPos) {
  const videoSource = item.video || (isDirectVideoFile(item.image) || getYouTubeEmbedUrl(item.image) ? item.image : '');
  const ytEmbed = getYouTubeEmbedUrl(videoSource);

  if (ytEmbed) {
    return `
      <div class="news-card-video-wrap">
        <iframe src="${ytEmbed}" title="${title}" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen loading="lazy"></iframe>
      </div>
    `;
  }

  if (isDirectVideoFile(videoSource)) {
    return `
      <div class="news-card-video-wrap">
        <video src="${videoSource}" controls playsinline preload="metadata" class="news-card-video"></video>
      </div>
    `;
  }

  const imgSrc = item.image || '';
  if (imgSrc) {
    const isLogo = item.type === 'logo' || 
                   imgSrc.includes('logo') || 
                   imgSrc.includes('pnas') || 
                   imgSrc.includes('assc') || 
                   imgSrc.includes('erc') || 
                   imgSrc.includes('templeton') || 
                   imgSrc.includes('nrc') || 
                   imgSrc.includes('proefkonijnen');

    let fitStyle = `object-fit: cover; object-position: ${imgPos};`;
    if (isLogo) {
      const padding = (imgSrc.includes('pnas') || imgSrc.includes('nrc') || imgSrc.includes('assc')) 
        ? 'padding: 2rem 1.5rem;' 
        : 'padding: 1.5rem;';
      fitStyle = `object-fit: contain; ${padding} background: var(--bg-tertiary);`;
    } else if (item.fit === 'contain' || item.position === 'contain') {
      fitStyle = `object-fit: contain; background: var(--bg-tertiary);`;
    }

    return `
      <div class="news-card-img-wrap">
        <img src="${imgSrc}" alt="${title}" class="news-card-img ${isLogo ? 'news-card-logo' : ''}" data-type="${item.type || ''}" style="${fitStyle}" onerror="this.parentElement.style.display='none';" />
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

    newsGrid.innerHTML = newsItems.map(item => {
      const imgPos = item.position || 'center 20%';
      const title = item.title || 'News Update';
      const date = item.date || '';
      const text = item.text || '';
      const link = item.link || '';

      const mediaHtml = renderNewsMedia(item, title, imgPos);

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
