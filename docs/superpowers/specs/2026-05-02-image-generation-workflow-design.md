# Image Generation Workflow — Design Spec
_Date: 2026-05-02_

## Overview

A local Python script that takes a real photo and a Claude Code-generated story, then produces 12 watercolour-style illustrated panels via GPT-Image-2. Story text is generated conversationally through Claude Code (no API call in the script). The script handles image generation only, with human-in-the-loop approval at every phase. Output lands in a gitignored `output/<story-id>/` folder ready for manual upload to Azure Blob Storage.

---

## Architecture

**Approach: Stateful phase-based script**

- Claude Code (conversation) generates story text and writes `output/<id>/story.json`
- Python script reads `story.json`, runs 3 image phases using GPT-Image-2 API
- `state.json` checkpoint saved after each approved phase — re-running the same command resumes from where it left off
- Human approves or provides typed feedback at each phase boundary; script regenerates on feedback

### Phase State Machine

```
story_approved → character_approved → storyboard_approved → panels_in_progress → done
```

`story_approved` is the initial state — the script always starts here because Claude Code has already written `story.json` before the script runs.

---

## File Structure

```
StoryBook/
  tools/
    generate.py        ← single entry point
    prompts.py         ← all GPT-Image-2 prompt templates
    state.py           ← checkpoint read/write helpers
    requirements.txt   ← openai, pillow, python-dotenv
    .env               ← gitignored; OPENAI_API_KEY
  output/              ← gitignored
    <story-id>/
      brief.json       ← copy of CLI args (kept for re-runs)
      state.json       ← checkpoint: current phase + panels_completed count
      story.json       ← written by Claude Code; read by script
      character_ref.png
      storyboard.png
      page1.png … page12.png
```

---

## Usage

**Step 1 — Generate story (Claude Code conversation)**

Ask Claude Code to write a story with character name, theme, and moral. Claude writes `output/<id>/story.json` directly including `scene_description` per page.

**Step 2 — First run (starts at character reference)**

```bash
python tools/generate.py --id pirate --photo ~/photos/emma.jpg
```

**Step 3 — Resume after interruption**

```bash
python tools/generate.py --id pirate
```

Re-running with just `--id` resumes from the last saved checkpoint automatically.

---

## Data Schemas

### `story.json` — written by Claude Code

```json
{
  "title": "Emma's Forest Adventure",
  "character_description": "Emma, 5-year-old girl with curly red hair and blue dress",
  "pages": [
    {
      "image": "page1.png",
      "text": "One morning, Emma wandered into the enchanted forest...",
      "scene_description": "Emma in blue dress at edge of glowing magical forest, curious expression, soft morning light, watercolour children's book illustration"
    }
  ]
}
```

`scene_description` is used as the image prompt. The website reader ignores this field.

### `state.json` — written by the script

```json
{
  "id": "pirate",
  "photo_path": "/Users/harry/photos/emma.jpg",
  "phase": "storyboard_approved",
  "panels_completed": 0
}
```

### `brief.json` — written on first run

```json
{
  "id": "pirate",
  "photo_path": "/Users/harry/photos/emma.jpg"
}
```

---

## Phases

### Phase 1 — Character Reference Sheet

- **Input:** real photo + `character_description` from `story.json`
- **Resolution:** `1536x1024` (landscape — 3 views side by side)
- **Prompt:** watercolour children's book character reference sheet, front / 3/4 / side profile views, maintain exact likeness, soft watercolour style
- **Output:** `character_ref.png`
- **Approval:** auto-opens image; Enter to approve, type feedback to regenerate

### Phase 2 — Storyboard Overview

- **Input:** `character_ref.png` + all 12 `scene_description` values
- **Resolution:** `1536x1024` (landscape — 12-panel grid)
- **Prompt:** watercolour children's book 12-panel storyboard grid, thumbnail scenes, consistent character
- **Output:** `storyboard.png`
- **Approval:** auto-opens image; Enter to approve, type feedback to regenerate

### Phase 3 — Full Panels

- **Input:** `character_ref.png` + one `scene_description` per panel
- **Resolution:** `1024x1024` (square — fast, compatible with reader `object-fit: contain`)
- **Output:** `page1.png` … `page12.png`
- **Approval:** each panel auto-opens individually; Enter to approve and generate next, type feedback to regenerate current panel
- **Checkpoint:** `panels_completed` incremented after each approval — re-run skips completed panels

---

## Human-in-the-Loop Interaction

At each phase boundary the script prints:

```
[Phase 1 complete] character_ref.png saved. Opening for review...
Approve? Press Enter to continue, or type feedback to regenerate: 
```

- **Enter (empty):** saves checkpoint, advances to next phase
- **Typed feedback:** re-runs the generation with feedback appended to the prompt
- **Ctrl+C:** exits; re-running resumes from last saved checkpoint

---

## Environment Setup

```
OPENAI_API_KEY=sk-...
```

Stored in `tools/.env` (gitignored). Loaded via `python-dotenv`.

No Anthropic API key required — story generation is handled through Claude Code conversation.

---

## Final Output

After all phases complete, `output/<id>/` contains everything needed for Blob Storage upload:

```
story.json       ← upload as-is (scene_description field is harmless)
page1.png … page12.png
character_ref.png    ← not needed by website, keep locally for reference
storyboard.png       ← not needed by website, keep locally for reference
```

Manually add the story entry to `stories.json` in Blob Storage after upload.

---

## Out of Scope

- Automatic Blob Storage upload
- Generating supporting characters (described inline in scene prompts)
- WebP conversion (optional future optimisation)
- More or fewer than 12 panels (fixed for now)
