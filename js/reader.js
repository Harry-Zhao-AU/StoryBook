let pages = [];
let currentPage = 0;
let storyId = '';

async function loadStory(id) {
  const res = await fetch(`${BLOB_BASE}/${encodeURIComponent(id)}/story.json`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

function renderPage() {
  const page = pages[currentPage];
  document.getElementById('page-image').src =
    `${BLOB_BASE}/${encodeURIComponent(storyId)}/${encodeURIComponent(page.image)}`;
  document.getElementById('page-text').textContent = page.text;
  document.getElementById('page-counter').textContent =
    `${currentPage + 1} / ${pages.length}`;
  document.getElementById('btn-prev').disabled = currentPage === 0;
  document.getElementById('btn-next').disabled = currentPage === pages.length - 1;
}

function prevPage() {
  if (currentPage > 0) { currentPage--; renderPage(); }
}

function nextPage() {
  if (currentPage < pages.length - 1) { currentPage++; renderPage(); }
}

async function init() {
  const params = new URLSearchParams(window.location.search);
  storyId = params.get('story');
  if (!storyId) { window.location.href = 'index.html'; return; }

  try {
    const story = await loadStory(storyId);
    pages = story.pages;
    if (!Array.isArray(pages) || pages.length === 0) {
      document.getElementById('page-text').textContent =
        'This story has no pages yet.';
      return;
    }
    document.title = story.title + ' — My Storybook';
    document.getElementById('story-title').textContent = story.title;
    renderPage();
  } catch (e) {
    document.getElementById('page-text').textContent =
      'Could not load this story. Please go back and try again.';
  }
}

document.getElementById('btn-prev').addEventListener('click', prevPage);
document.getElementById('btn-next').addEventListener('click', nextPage);

// Swipe support
let touchStartX = 0;
document.addEventListener('touchstart', e => { touchStartX = e.touches[0].clientX; }, { passive: true });
document.addEventListener('touchend', e => {
  const dx = e.changedTouches[0].clientX - touchStartX;
  if (dx < -50) nextPage();
  else if (dx > 50) prevPage();
}, { passive: true });

init();
