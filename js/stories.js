async function loadStories() {
  const res = await fetch(`${BLOB_BASE}/stories.json`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data = await res.json();
  return data.stories;
}

function renderList(stories) {
  const list = document.getElementById('story-list');
  list.innerHTML = stories.map(story => `
    <li>
      <a class="story-row" href="reader.html?story=${encodeURIComponent(story.id)}">
        <img
          class="story-cover"
          src="${BLOB_BASE}/${encodeURIComponent(story.id)}/${encodeURIComponent(story.cover)}"
          alt="${story.title} cover"
          onerror="this.style.visibility='hidden'"
        >
        <div class="story-info">
          <div class="story-title">${story.title}</div>
          <div class="story-pages">${story.pages} page${story.pages === 1 ? '' : 's'}</div>
        </div>
        <div class="story-chevron">›</div>
      </a>
    </li>
  `).join('');
}

async function init() {
  const list = document.getElementById('story-list');
  try {
    const stories = await loadStories();
    if (stories.length === 0) {
      list.innerHTML = '<li><p class="status-message">No stories yet.</p></li>';
      return;
    }
    renderList(stories);
  } catch (e) {
    list.innerHTML = '<li><p class="status-message">Could not load stories. Please try again later.</p></li>';
  }
}

init();
