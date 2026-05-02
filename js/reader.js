let pages = [];
let currentPage = 0;
let storyId = '';
let storyMusic = null;

// ── Reader ──────────────────────────────────────────

async function loadStory(id) {
  const res = await fetch(`${BLOB_BASE}/${encodeURIComponent(id)}/story.json${BLOB_SAS}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

function renderPage() {
  const page = pages[currentPage];
  document.getElementById('page-image').src =
    `${BLOB_BASE}/${encodeURIComponent(storyId)}/${encodeURIComponent(page.image)}${BLOB_SAS}`;
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
    storyMusic = story.music || null;
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
  if (!document.getElementById('player-overlay').classList.contains('hidden')) return;
  const dx = e.changedTouches[0].clientX - touchStartX;
  if (dx < -50) nextPage();
  else if (dx > 50) prevPage();
}, { passive: true });

// ── Player ──────────────────────────────────────────

const PLAYER_DEFAULT_DURATION = 6000;   // ms per page
const PLAYER_DIALOGUE_MS = 3200;        // ms per dialogue line
const KB_ANIMS = ['kb1', 'kb2', 'kb3', 'kb4'];
const MUSIC_VOLUME = 0.35;

let playerPaused = false;
let playerMuted = false;
let playerTimer = null;
let playerDialogueTimer = null;
let kbIndex = 0;

function audioFade(audio, targetVol, ms, onDone) {
  const startVol = audio.volume;
  const diff = targetVol - startVol;
  const startTime = performance.now();
  function step(now) {
    const t = Math.min((now - startTime) / ms, 1);
    audio.volume = Math.max(0, Math.min(1, startVol + diff * t));
    if (t < 1) requestAnimationFrame(step);
    else if (onDone) onDone();
  }
  requestAnimationFrame(step);
}

function enterPlayer() {
  playerPaused = false;
  document.getElementById('player-overlay').classList.remove('hidden');
  document.getElementById('player-story-title').textContent =
    document.getElementById('story-title').textContent;
  if (storyMusic) {
    const audio = document.getElementById('player-audio');
    audio.src = `${BLOB_BASE}/${encodeURIComponent(storyId)}/${encodeURIComponent(storyMusic)}${BLOB_SAS}`;
    audio.muted = playerMuted;
    audio.volume = 0;
    audio.play().catch(() => {});
    audioFade(audio, MUSIC_VOLUME, 1500);
  }
  playerGoToPage(currentPage);
}

function exitPlayer() {
  clearTimeout(playerTimer);
  clearTimeout(playerDialogueTimer);
  const audio = document.getElementById('player-audio');
  if (!audio.paused) {
    audioFade(audio, 0, 800, () => { audio.pause(); audio.currentTime = 0; });
  }
  document.getElementById('player-overlay').classList.add('hidden');
  renderPage();
}

function playerGoToPage(index) {
  clearTimeout(playerTimer);
  clearTimeout(playerDialogueTimer);
  currentPage = index;

  const page = pages[currentPage];
  const dialogue = Array.isArray(page.dialogue) ? page.dialogue : [];
  const baseDuration = page.duration || PLAYER_DEFAULT_DURATION;
  const duration = Math.max(baseDuration, dialogue.length * PLAYER_DIALOGUE_MS + 1000);

  document.getElementById('player-counter').textContent =
    `${currentPage + 1} / ${pages.length}`;
  document.getElementById('btn-player-prev').disabled = currentPage === 0;
  document.getElementById('btn-player-next').disabled = currentPage === pages.length - 1;

  // Fade out stage
  const stage = document.getElementById('player-stage');
  stage.classList.add('fading');

  const img = document.getElementById('player-image');
  img.src = `${BLOB_BASE}/${encodeURIComponent(storyId)}/${encodeURIComponent(page.image)}${BLOB_SAS}`;

  setTimeout(() => {
    // Restart Ken Burns
    img.style.animation = 'none';
    void img.offsetWidth; // force reflow
    img.style.animation =
      `${KB_ANIMS[kbIndex % KB_ANIMS.length]} ${duration / 1000}s ease-in-out forwards`;
    kbIndex++;

    // Subtitle (字幕)
    const subtitle = page.subtitle || page.text || '';
    const subtitleEl = document.getElementById('player-subtitle');
    subtitleEl.textContent = subtitle;
    subtitleEl.style.display = subtitle ? 'block' : 'none';

    // Fade in stage
    stage.classList.remove('fading');

    // Progress bar
    startProgressBar(duration);

    // Dialogue (对白)
    if (dialogue.length) {
      playerShowDialogue(dialogue, 0);
    } else {
      document.getElementById('player-dialogue').style.display = 'none';
    }

    // Auto-advance
    if (!playerPaused) {
      playerTimer = setTimeout(() => {
        if (currentPage < pages.length - 1) {
          playerGoToPage(currentPage + 1);
        } else {
          exitPlayer();
        }
      }, duration);
    }
  }, 380); // wait for fade-out transition
}

function playerShowDialogue(dialogues, index) {
  const box = document.getElementById('player-dialogue');
  if (index >= dialogues.length) {
    box.style.display = 'none';
    return;
  }
  const d = dialogues[index];
  document.querySelector('.player-dialogue-char').textContent = d.character;
  document.querySelector('.player-dialogue-text').textContent = d.text;
  box.style.display = 'flex';
  playerDialogueTimer = setTimeout(
    () => playerShowDialogue(dialogues, index + 1),
    PLAYER_DIALOGUE_MS
  );
}

function startProgressBar(duration) {
  const fill = document.getElementById('player-progress-fill');
  fill.style.transition = 'none';
  fill.style.width = '0%';
  void fill.offsetWidth;
  fill.style.transition = `width ${duration}ms linear`;
  fill.style.width = '100%';
}

function togglePlayerPause() {
  playerPaused = !playerPaused;
  const btn = document.getElementById('btn-player-play-pause');
  btn.textContent = playerPaused ? '▶' : '⏸';
  btn.setAttribute('aria-label', playerPaused ? 'Play' : 'Pause');

  const img = document.getElementById('player-image');
  const fill = document.getElementById('player-progress-fill');

  const audio = document.getElementById('player-audio');
  if (playerPaused) {
    clearTimeout(playerTimer);
    clearTimeout(playerDialogueTimer);
    img.style.animationPlayState = 'paused';
    fill.style.transitionDuration = '0s';
    audioFade(audio, 0, 400, () => audio.pause());
  } else {
    img.style.animationPlayState = 'running';
    audio.play().catch(() => {});
    audioFade(audio, MUSIC_VOLUME, 400);
    playerGoToPage(currentPage);
  }
}

function togglePlayerMute() {
  playerMuted = !playerMuted;
  const audio = document.getElementById('player-audio');
  audio.muted = playerMuted;
  document.getElementById('btn-player-mute').textContent = playerMuted ? '🔇' : '🔊';
}

document.getElementById('btn-play').addEventListener('click', enterPlayer);
document.getElementById('btn-player-mute').addEventListener('click', togglePlayerMute);
document.getElementById('btn-player-close').addEventListener('click', exitPlayer);
document.getElementById('btn-player-play-pause').addEventListener('click', togglePlayerPause);
document.getElementById('btn-player-prev').addEventListener('click', () => {
  if (currentPage > 0) playerGoToPage(currentPage - 1);
});
document.getElementById('btn-player-next').addEventListener('click', () => {
  if (currentPage < pages.length - 1) playerGoToPage(currentPage + 1);
});

document.addEventListener('keydown', e => {
  if (document.getElementById('player-overlay').classList.contains('hidden')) return;
  if (e.key === 'Escape') { exitPlayer(); return; }
  if (e.key === ' ') { e.preventDefault(); togglePlayerPause(); return; }
  if (e.key === 'ArrowRight' && currentPage < pages.length - 1) playerGoToPage(currentPage + 1);
  if (e.key === 'ArrowLeft'  && currentPage > 0)                playerGoToPage(currentPage - 1);
});

init();
