# Image Generation Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local Python script that takes a real photo + Claude-generated story.json and produces 12 watercolour-style illustrated panels via GPT-Image-2, with human-in-the-loop approval at each phase.

**Architecture:** Stateful phase-based script. Claude Code (conversation) writes `output/<id>/story.json` first. The script reads it, runs three image generation phases (character reference → storyboard → full panels), saves a `state.json` checkpoint after each approved phase, and resumes from the last checkpoint on re-run.

**Tech Stack:** Python 3.11+, openai SDK, pillow, python-dotenv, pytest

---

## File Map

| File | Purpose |
|---|---|
| `tools/requirements.txt` | Python dependencies |
| `tools/.env.example` | Example env file (actual `.env` is gitignored) |
| `tools/conftest.py` | pytest sys.path setup so tests can import from `tools/` |
| `tools/state.py` | Output dir helpers, checkpoint read/write, brief read/write |
| `tools/prompts.py` | GPT-Image-2 prompt template functions |
| `tools/generate.py` | CLI entry point, API calls, approval loop, phase orchestration |
| `tools/tests/test_state.py` | Unit tests for state.py |
| `tools/tests/test_prompts.py` | Unit tests for prompts.py |
| `tools/tests/test_generate.py` | Unit tests for generate.py helpers |
| `.gitignore` | Add `output/` and `tools/.env` |

---

## Task 1: Project Scaffolding

**Files:**
- Create: `tools/requirements.txt`
- Create: `tools/.env.example`
- Create: `tools/conftest.py`
- Create: `tools/tests/__init__.py`
- Modify: `.gitignore`

- [ ] **Step 1: Update `.gitignore`**

  Open `.gitignore` (create it if absent) and add:

  ```
  # Image generation tool
  output/
  tools/.env
  ```

- [ ] **Step 2: Create `tools/requirements.txt`**

  ```
  openai>=1.0.0
  pillow>=10.0.0
  python-dotenv>=1.0.0
  pytest>=8.0.0
  ```

- [ ] **Step 3: Create `tools/.env.example`**

  ```
  OPENAI_API_KEY=sk-...
  ```

- [ ] **Step 4: Create `tools/conftest.py`**

  ```python
  import sys
  from pathlib import Path

  sys.path.insert(0, str(Path(__file__).parent))
  ```

- [ ] **Step 5: Create `tools/tests/__init__.py`**

  Empty file — makes `tests/` a package so pytest discovers it correctly.

  ```python
  ```

- [ ] **Step 6: Install dependencies**

  ```bash
  cd tools
  pip install -r requirements.txt
  ```

  Expected: all packages install without errors.

- [ ] **Step 7: Commit**

  ```bash
  git add tools/requirements.txt tools/.env.example tools/conftest.py tools/tests/__init__.py .gitignore
  git commit -m "chore: scaffold image generation tool"
  ```

---

## Task 2: `state.py` — Checkpoint Helpers

**Files:**
- Create: `tools/state.py`
- Create: `tools/tests/test_state.py`

- [ ] **Step 1: Write failing tests**

  Create `tools/tests/test_state.py`:

  ```python
  import json
  import pytest
  from pathlib import Path
  from state import get_output_dir, load_state, save_state, load_story, save_brief, load_brief


  def test_get_output_dir_returns_path_under_output():
      path = get_output_dir("pirate")
      assert path == Path("output") / "pirate"


  def test_save_and_load_state(tmp_path, monkeypatch):
      monkeypatch.chdir(tmp_path)
      state = {"id": "pirate", "photo_path": "/tmp/photo.jpg", "phase": "story_approved", "panels_completed": 0}
      save_state(state)
      loaded = load_state("pirate")
      assert loaded == state


  def test_load_state_returns_none_when_missing(tmp_path, monkeypatch):
      monkeypatch.chdir(tmp_path)
      assert load_state("pirate") is None


  def test_save_state_creates_output_dir(tmp_path, monkeypatch):
      monkeypatch.chdir(tmp_path)
      state = {"id": "pirate", "photo_path": "/tmp/photo.jpg", "phase": "story_approved", "panels_completed": 0}
      save_state(state)
      assert (tmp_path / "output" / "pirate" / "state.json").exists()


  def test_load_story_returns_parsed_json(tmp_path, monkeypatch):
      monkeypatch.chdir(tmp_path)
      story = {"title": "Test", "character_description": "A child", "pages": []}
      story_path = tmp_path / "output" / "pirate"
      story_path.mkdir(parents=True)
      (story_path / "story.json").write_text(json.dumps(story))
      assert load_story("pirate") == story


  def test_load_story_raises_when_missing(tmp_path, monkeypatch):
      monkeypatch.chdir(tmp_path)
      with pytest.raises(FileNotFoundError, match="story.json not found"):
          load_story("pirate")


  def test_save_and_load_brief(tmp_path, monkeypatch):
      monkeypatch.chdir(tmp_path)
      save_brief("pirate", "/tmp/photo.jpg")
      brief = load_brief("pirate")
      assert brief == {"id": "pirate", "photo_path": "/tmp/photo.jpg"}


  def test_load_brief_raises_when_missing(tmp_path, monkeypatch):
      monkeypatch.chdir(tmp_path)
      with pytest.raises(FileNotFoundError, match="brief.json not found"):
          load_brief("pirate")
  ```

- [ ] **Step 2: Run tests to verify they fail**

  ```bash
  cd tools
  pytest tests/test_state.py -v
  ```

  Expected: `ModuleNotFoundError: No module named 'state'`

- [ ] **Step 3: Implement `tools/state.py`**

  ```python
  import json
  from pathlib import Path


  def get_output_dir(story_id: str) -> Path:
      return Path("output") / story_id


  def load_state(story_id: str) -> dict | None:
      state_path = get_output_dir(story_id) / "state.json"
      if not state_path.exists():
          return None
      return json.loads(state_path.read_text())


  def save_state(state: dict) -> None:
      output_dir = get_output_dir(state["id"])
      output_dir.mkdir(parents=True, exist_ok=True)
      (output_dir / "state.json").write_text(json.dumps(state, indent=2))


  def load_story(story_id: str) -> dict:
      story_path = get_output_dir(story_id) / "story.json"
      if not story_path.exists():
          raise FileNotFoundError(
              f"story.json not found at {story_path}. Ask Claude Code to generate the story first."
          )
      return json.loads(story_path.read_text())


  def save_brief(story_id: str, photo_path: str) -> None:
      output_dir = get_output_dir(story_id)
      output_dir.mkdir(parents=True, exist_ok=True)
      brief = {"id": story_id, "photo_path": photo_path}
      (output_dir / "brief.json").write_text(json.dumps(brief, indent=2))


  def load_brief(story_id: str) -> dict:
      brief_path = get_output_dir(story_id) / "brief.json"
      if not brief_path.exists():
          raise FileNotFoundError(f"brief.json not found. Run with --photo to start.")
      return json.loads(brief_path.read_text())
  ```

- [ ] **Step 4: Run tests to verify they pass**

  ```bash
  cd tools
  pytest tests/test_state.py -v
  ```

  Expected: 8 tests PASS

- [ ] **Step 5: Commit**

  ```bash
  git add tools/state.py tools/tests/test_state.py
  git commit -m "feat: add state checkpoint helpers"
  ```

---

## Task 3: `prompts.py` — Prompt Templates

**Files:**
- Create: `tools/prompts.py`
- Create: `tools/tests/test_prompts.py`

- [ ] **Step 1: Write failing tests**

  Create `tools/tests/test_prompts.py`:

  ```python
  from prompts import character_ref_prompt, storyboard_prompt, panel_prompt


  def test_character_ref_prompt_includes_character_description():
      result = character_ref_prompt("Emma, 5-year-old girl with curly red hair")
      assert "Emma, 5-year-old girl with curly red hair" in result


  def test_character_ref_prompt_includes_three_views():
      result = character_ref_prompt("Emma")
      assert "front" in result.lower()
      assert "3/4" in result.lower()
      assert "side" in result.lower()


  def test_character_ref_prompt_includes_style():
      result = character_ref_prompt("Emma")
      assert "watercolour" in result.lower()


  def test_storyboard_prompt_includes_all_scene_descriptions():
      scenes = ["Scene A", "Scene B", "Scene C"]
      result = storyboard_prompt(scenes)
      assert "Scene A" in result
      assert "Scene B" in result
      assert "Scene C" in result


  def test_storyboard_prompt_includes_panel_numbers():
      scenes = ["Scene A", "Scene B"]
      result = storyboard_prompt(scenes)
      assert "Panel 1" in result
      assert "Panel 2" in result


  def test_storyboard_prompt_includes_style():
      result = storyboard_prompt(["Scene A"])
      assert "watercolour" in result.lower()


  def test_panel_prompt_includes_scene_description():
      result = panel_prompt("Emma runs through the forest", 3)
      assert "Emma runs through the forest" in result


  def test_panel_prompt_includes_panel_number():
      result = panel_prompt("Emma runs", 7)
      assert "7" in result


  def test_panel_prompt_includes_style():
      result = panel_prompt("Emma runs", 1)
      assert "watercolour" in result.lower()
  ```

- [ ] **Step 2: Run tests to verify they fail**

  ```bash
  cd tools
  pytest tests/test_prompts.py -v
  ```

  Expected: `ModuleNotFoundError: No module named 'prompts'`

- [ ] **Step 3: Implement `tools/prompts.py`**

  ```python
  STYLE = (
      "watercolour children's book illustration, soft watercolour style, "
      "gentle colours, hand-painted texture"
  )


  def character_ref_prompt(character_description: str) -> str:
      return (
          f"Character reference sheet of {character_description}. "
          f"Show front view, 3/4 view, and side profile arranged side by side. "
          f"Maintain exact likeness to the reference photo. "
          f"{STYLE}."
      )


  def storyboard_prompt(scene_descriptions: list[str]) -> str:
      scenes = "\n".join(
          f"Panel {i + 1}: {desc}" for i, desc in enumerate(scene_descriptions)
      )
      return (
          f"12-panel storyboard grid for a children's story. "
          f"Arrange all panels in a 4x3 grid, each labelled with its number. "
          f"Maintain consistent character appearance throughout. "
          f"{STYLE}.\n\n{scenes}"
      )


  def panel_prompt(scene_description: str, panel_number: int) -> str:
      return (
          f"Page {panel_number} of a children's storybook. "
          f"{scene_description}. "
          f"Maintain consistent character appearance with the reference sheet. "
          f"Full illustration, no text or page numbers. "
          f"{STYLE}."
      )
  ```

- [ ] **Step 4: Run tests to verify they pass**

  ```bash
  cd tools
  pytest tests/test_prompts.py -v
  ```

  Expected: 9 tests PASS

- [ ] **Step 5: Commit**

  ```bash
  git add tools/prompts.py tools/tests/test_prompts.py
  git commit -m "feat: add GPT-Image-2 prompt templates"
  ```

---

## Task 4: `generate.py` — Image Generation + Approval Helpers

**Files:**
- Create: `tools/generate.py` (partial — helpers only, no `main()` yet)
- Create: `tools/tests/test_generate.py`

- [ ] **Step 1: Write failing tests for helpers**

  Create `tools/tests/test_generate.py`:

  ```python
  import base64
  import io
  import json
  from pathlib import Path
  from unittest.mock import MagicMock, patch, mock_open

  import pytest
  from PIL import Image

  from generate import open_image, ask_approval, generate_image


  def test_ask_approval_returns_empty_string_on_enter(tmp_path):
      fake_image = tmp_path / "test.png"
      Image.new("RGB", (10, 10)).save(fake_image)
      with patch("generate.open_image"), patch("builtins.input", return_value=""):
          result = ask_approval("Phase 1", fake_image)
      assert result == ""


  def test_ask_approval_returns_feedback_text(tmp_path):
      fake_image = tmp_path / "test.png"
      Image.new("RGB", (10, 10)).save(fake_image)
      with patch("generate.open_image"), patch("builtins.input", return_value="make it brighter"):
          result = ask_approval("Phase 1", fake_image)
      assert result == "make it brighter"


  def test_generate_image_saves_file(tmp_path):
      # Build a minimal PNG as base64
      buf = io.BytesIO()
      Image.new("RGB", (4, 4), color=(255, 0, 0)).save(buf, format="PNG")
      b64 = base64.b64encode(buf.getvalue()).decode()

      mock_response = MagicMock()
      mock_response.data = [MagicMock(b64_json=b64)]

      mock_client = MagicMock()
      mock_client.images.edit.return_value = mock_response

      ref_image = tmp_path / "ref.png"
      Image.new("RGB", (4, 4)).save(ref_image)
      output_path = tmp_path / "out.png"

      generate_image(mock_client, "a prompt", ref_image, "1024x1024", output_path)

      assert output_path.exists()
      img = Image.open(output_path)
      assert img.size == (4, 4)


  def test_generate_image_passes_correct_args_to_api(tmp_path):
      buf = io.BytesIO()
      Image.new("RGB", (4, 4)).save(buf, format="PNG")
      b64 = base64.b64encode(buf.getvalue()).decode()

      mock_response = MagicMock()
      mock_response.data = [MagicMock(b64_json=b64)]
      mock_client = MagicMock()
      mock_client.images.edit.return_value = mock_response

      ref_image = tmp_path / "ref.png"
      Image.new("RGB", (4, 4)).save(ref_image)
      output_path = tmp_path / "out.png"

      generate_image(mock_client, "a detailed prompt", ref_image, "1536x1024", output_path)

      call_kwargs = mock_client.images.edit.call_args.kwargs
      assert call_kwargs["model"] == "gpt-image-2"
      assert call_kwargs["prompt"] == "a detailed prompt"
      assert call_kwargs["size"] == "1536x1024"
      assert call_kwargs["n"] == 1
      assert call_kwargs["response_format"] == "b64_json"
  ```

- [ ] **Step 2: Run tests to verify they fail**

  ```bash
  cd tools
  pytest tests/test_generate.py -v
  ```

  Expected: `ModuleNotFoundError: No module named 'generate'`

- [ ] **Step 3: Implement helpers in `tools/generate.py`**

  ```python
  #!/usr/bin/env python3
  import base64
  import io
  import os
  import platform
  import subprocess
  import sys
  from pathlib import Path

  from dotenv import load_dotenv
  from openai import OpenAI
  from PIL import Image

  load_dotenv(Path(__file__).parent / ".env")


  def open_image(path: Path) -> None:
      if platform.system() == "Windows":
          os.startfile(str(path))
      elif platform.system() == "Darwin":
          subprocess.run(["open", str(path)])
      else:
          subprocess.run(["xdg-open", str(path)])


  def ask_approval(phase_name: str, image_path: Path) -> str:
      print(f"\n[{phase_name} complete] {image_path.name} saved. Opening for review...")
      open_image(image_path)
      return input("Approve? Press Enter to continue, or type feedback to regenerate: ").strip()


  def generate_image(
      client: OpenAI,
      prompt: str,
      reference_image_path: Path,
      size: str,
      output_path: Path,
  ) -> None:
      with open(reference_image_path, "rb") as img_file:
          response = client.images.edit(
              model="gpt-image-2",
              image=img_file,
              prompt=prompt,
              size=size,
              n=1,
              response_format="b64_json",
          )
      image_bytes = base64.b64decode(response.data[0].b64_json)
      Image.open(io.BytesIO(image_bytes)).save(output_path)
  ```

- [ ] **Step 4: Run tests to verify they pass**

  ```bash
  cd tools
  pytest tests/test_generate.py -v
  ```

  Expected: 4 tests PASS

- [ ] **Step 5: Commit**

  ```bash
  git add tools/generate.py tools/tests/test_generate.py
  git commit -m "feat: add image generation and approval helpers"
  ```

---

## Task 5: `generate.py` — Phase Runners + CLI

**Files:**
- Modify: `tools/generate.py` (add phase runners + `main()`)
- Create: `tools/tests/test_phases.py` (phase + CLI tests in their own file)

- [ ] **Step 1: Write failing tests for phases and CLI**

  Create `tools/tests/test_phases.py`:

  ```python
  import base64
  import io
  from pathlib import Path
  from unittest.mock import MagicMock, patch

  import pytest
  from PIL import Image

  from generate import run_phase1, run_phase2, run_phase3, main


  def _make_story(pages=2):
      return {
          "title": "Test Story",
          "character_description": "Emma, red hair",
          "pages": [
              {
                  "image": f"page{i+1}.png",
                  "text": f"Page {i+1} text",
                  "scene_description": f"Scene {i+1} description",
              }
              for i in range(pages)
          ],
      }


  def _make_state(phase="story_approved", panels_completed=0):
      return {
          "id": "test",
          "photo_path": "/tmp/photo.jpg",
          "phase": phase,
          "panels_completed": panels_completed,
      }


  def _make_ref_image(output_dir: Path) -> Path:
      ref = output_dir / "character_ref.png"
      Image.new("RGB", (4, 4)).save(ref)
      return ref


  def _make_photo(tmp_path: Path) -> Path:
      photo = tmp_path / "photo.jpg"
      Image.new("RGB", (4, 4)).save(photo)
      return photo


  def _b64_png() -> str:
      buf = io.BytesIO()
      Image.new("RGB", (4, 4)).save(buf, format="PNG")
      return base64.b64encode(buf.getvalue()).decode()


  def test_run_phase1_saves_character_ref_and_updates_state(tmp_path, monkeypatch):
      monkeypatch.chdir(tmp_path)
      output_dir = tmp_path / "output" / "test"
      output_dir.mkdir(parents=True)
      photo = _make_photo(tmp_path)

      state = _make_state()
      state["photo_path"] = str(photo)
      story = _make_story()

      mock_response = MagicMock()
      mock_response.data = [MagicMock(b64_json=_b64_png())]
      mock_client = MagicMock()
      mock_client.images.edit.return_value = mock_response

      with patch("generate.ask_approval", return_value=""):
          run_phase1(mock_client, state, story, output_dir)

      assert (output_dir / "character_ref.png").exists()
      assert state["phase"] == "character_approved"


  def test_run_phase1_regenerates_on_feedback(tmp_path, monkeypatch):
      monkeypatch.chdir(tmp_path)
      output_dir = tmp_path / "output" / "test"
      output_dir.mkdir(parents=True)
      photo = _make_photo(tmp_path)

      state = _make_state()
      state["photo_path"] = str(photo)
      story = _make_story()

      mock_response = MagicMock()
      mock_response.data = [MagicMock(b64_json=_b64_png())]
      mock_client = MagicMock()
      mock_client.images.edit.return_value = mock_response

      # First call returns feedback, second call approves
      with patch("generate.ask_approval", side_effect=["make it brighter", ""]):
          run_phase1(mock_client, state, story, output_dir)

      assert mock_client.images.edit.call_count == 2
      assert state["phase"] == "character_approved"


  def test_run_phase2_saves_storyboard_and_updates_state(tmp_path, monkeypatch):
      monkeypatch.chdir(tmp_path)
      output_dir = tmp_path / "output" / "test"
      output_dir.mkdir(parents=True)
      _make_ref_image(output_dir)

      state = _make_state(phase="character_approved")
      story = _make_story(pages=12)

      mock_response = MagicMock()
      mock_response.data = [MagicMock(b64_json=_b64_png())]
      mock_client = MagicMock()
      mock_client.images.edit.return_value = mock_response

      with patch("generate.ask_approval", return_value=""):
          run_phase2(mock_client, state, story, output_dir)

      assert (output_dir / "storyboard.png").exists()
      assert state["phase"] == "storyboard_approved"


  def test_run_phase3_generates_all_panels(tmp_path, monkeypatch):
      monkeypatch.chdir(tmp_path)
      output_dir = tmp_path / "output" / "test"
      output_dir.mkdir(parents=True)
      _make_ref_image(output_dir)

      state = _make_state(phase="storyboard_approved")
      story = _make_story(pages=3)

      mock_response = MagicMock()
      mock_response.data = [MagicMock(b64_json=_b64_png())]
      mock_client = MagicMock()
      mock_client.images.edit.return_value = mock_response

      with patch("generate.ask_approval", return_value=""):
          run_phase3(mock_client, state, story, output_dir)

      assert (output_dir / "page1.png").exists()
      assert (output_dir / "page2.png").exists()
      assert (output_dir / "page3.png").exists()
      assert state["phase"] == "done"


  def test_run_phase3_skips_completed_panels(tmp_path, monkeypatch):
      monkeypatch.chdir(tmp_path)
      output_dir = tmp_path / "output" / "test"
      output_dir.mkdir(parents=True)
      _make_ref_image(output_dir)
      # Simulate page1 and page2 already done
      Image.new("RGB", (4, 4)).save(output_dir / "page1.png")
      Image.new("RGB", (4, 4)).save(output_dir / "page2.png")

      state = _make_state(phase="panels_in_progress", panels_completed=2)
      story = _make_story(pages=3)

      mock_response = MagicMock()
      mock_response.data = [MagicMock(b64_json=_b64_png())]
      mock_client = MagicMock()
      mock_client.images.edit.return_value = mock_response

      with patch("generate.ask_approval", return_value=""):
          run_phase3(mock_client, state, story, output_dir)

      # Only panel 3 should have been generated via API
      assert mock_client.images.edit.call_count == 1
      assert state["phase"] == "done"


  def test_main_errors_without_photo_on_first_run(tmp_path, monkeypatch, capsys):
      monkeypatch.chdir(tmp_path)
      with pytest.raises(SystemExit):
          main(["--id", "pirate"])
      captured = capsys.readouterr()
      assert "--photo is required" in captured.err


  def test_main_errors_without_story_json(tmp_path, monkeypatch, capsys):
      monkeypatch.chdir(tmp_path)
      photo = _make_photo(tmp_path)
      with pytest.raises(SystemExit):
          main(["--id", "pirate", "--photo", str(photo)])
      captured = capsys.readouterr()
      assert "story.json not found" in captured.err
  ```

- [ ] **Step 2: Run tests to verify they fail**

  ```bash
  cd tools
  pytest tests/test_phases.py -v
  ```

  Expected: `ImportError: cannot import name 'run_phase1' from 'generate'`

- [ ] **Step 3: Add phase runners and `main()` to `tools/generate.py`**

  Append to the existing `tools/generate.py` (after `generate_image`):

  ```python
  from state import get_output_dir, load_state, save_state, load_story, save_brief
  from prompts import character_ref_prompt, storyboard_prompt, panel_prompt


  def run_phase1(client: OpenAI, state: dict, story: dict, output_dir: Path) -> None:
      photo_path = Path(state["photo_path"])
      character_description = story["character_description"]
      output_path = output_dir / "character_ref.png"
      extra_feedback = ""

      while True:
          desc = character_description if not extra_feedback else f"{character_description}. Feedback: {extra_feedback}"
          prompt = character_ref_prompt(desc)
          print(f"\n[Phase 1] Generating character reference sheet...")
          generate_image(client, prompt, photo_path, "1536x1024", output_path)
          feedback = ask_approval("Phase 1", output_path)
          if not feedback:
              state["phase"] = "character_approved"
              save_state(state)
              break
          extra_feedback = feedback


  def run_phase2(client: OpenAI, state: dict, story: dict, output_dir: Path) -> None:
      character_ref_path = output_dir / "character_ref.png"
      scene_descriptions = [p["scene_description"] for p in story["pages"]]
      output_path = output_dir / "storyboard.png"
      extra_feedback = ""

      while True:
          prompt = storyboard_prompt(scene_descriptions)
          if extra_feedback:
              prompt += f"\n\nFeedback: {extra_feedback}"
          print(f"\n[Phase 2] Generating storyboard overview...")
          generate_image(client, prompt, character_ref_path, "1536x1024", output_path)
          feedback = ask_approval("Phase 2", output_path)
          if not feedback:
              state["phase"] = "storyboard_approved"
              save_state(state)
              break
          extra_feedback = feedback


  def run_phase3(client: OpenAI, state: dict, story: dict, output_dir: Path) -> None:
      character_ref_path = output_dir / "character_ref.png"
      pages = story["pages"]

      state["phase"] = "panels_in_progress"
      save_state(state)

      for i, page in enumerate(pages):
          panel_num = i + 1
          if panel_num <= state.get("panels_completed", 0):
              print(f"[Phase 3] Skipping panel {panel_num}/{len(pages)} (already completed)")
              continue

          output_path = output_dir / f"page{panel_num}.png"
          extra_feedback = ""

          while True:
              prompt = panel_prompt(page["scene_description"], panel_num)
              if extra_feedback:
                  prompt += f"\n\nFeedback: {extra_feedback}"
              print(f"\n[Phase 3] Generating panel {panel_num}/{len(pages)}...")
              generate_image(client, prompt, character_ref_path, "1024x1024", output_path)
              feedback = ask_approval(f"Phase 3 — Panel {panel_num}", output_path)
              if not feedback:
                  state["panels_completed"] = panel_num
                  save_state(state)
                  break
              extra_feedback = feedback

      state["phase"] = "done"
      save_state(state)
      print(f"\n[Done] All panels complete. Upload output/{state['id']}/ to Blob Storage.")


  def main(argv: list[str] | None = None) -> None:
      import argparse

      parser = argparse.ArgumentParser(description="Generate storybook illustrations via GPT-Image-2")
      parser.add_argument("--id", required=True, help="Story ID (e.g. pirate)")
      parser.add_argument("--photo", help="Path to reference photo (required on first run)")
      args = parser.parse_args(argv)

      output_dir = get_output_dir(args.id)

      state = load_state(args.id)
      if state is None:
          if not args.photo:
              print("Error: --photo is required on first run.", file=sys.stderr)
              sys.exit(1)
          photo_path_resolved = str(Path(args.photo).resolve())
          if not Path(photo_path_resolved).exists():
              print(f"Error: photo not found at {args.photo}", file=sys.stderr)
              sys.exit(1)
          save_brief(args.id, photo_path_resolved)
          state = {
              "id": args.id,
              "photo_path": photo_path_resolved,
              "phase": "story_approved",
              "panels_completed": 0,
          }
          save_state(state)
      elif args.photo:
          state["photo_path"] = str(Path(args.photo).resolve())

      try:
          story = load_story(args.id)
      except FileNotFoundError as e:
          print(f"Error: {e}", file=sys.stderr)
          sys.exit(1)

      client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

      phase = state["phase"]

      if phase == "story_approved":
          run_phase1(client, state, story, output_dir)
          phase = state["phase"]

      if phase == "character_approved":
          run_phase2(client, state, story, output_dir)
          phase = state["phase"]

      if phase in ("storyboard_approved", "panels_in_progress"):
          run_phase3(client, state, story, output_dir)


  if __name__ == "__main__":
      main()
  ```

- [ ] **Step 4: Run all tests**

  ```bash
  cd tools
  pytest tests/ -v
  ```

  Expected: all tests PASS (21 total across test_state.py, test_prompts.py, test_generate.py, test_phases.py)

- [ ] **Step 5: Commit**

  ```bash
  git add tools/generate.py tools/tests/test_phases.py
  git commit -m "feat: add phase runners and CLI entry point"
  ```

---

## Task 6: End-to-End Smoke Test

**Files:**
- No new files — manual test against real API

- [ ] **Step 1: Create `tools/.env` from example**

  ```bash
  cp tools/.env.example tools/.env
  # Edit tools/.env and add your real OPENAI_API_KEY
  ```

- [ ] **Step 2: Ask Claude Code to write a sample story**

  In a new Claude Code conversation, ask:

  > "Write a 12-page watercolour children's storybook story with id `smoke-test`. Character: a small orange cat named Mochi. Theme: finding a lost ball of yarn. Moral: asking for help is brave. Write it to output/smoke-test/story.json."

- [ ] **Step 3: Run the script with a test photo**

  ```bash
  cd tools
  python generate.py --id smoke-test --photo /path/to/any/photo.jpg
  ```

  Expected:
  - `[Phase 1] Generating character reference sheet...` prints
  - Image opens in default viewer
  - Approval prompt appears
  - Enter advances to Phase 2
  - Ctrl+C exits cleanly; re-running resumes from last checkpoint

- [ ] **Step 4: Verify output structure**

  After completing all phases:

  ```
  output/smoke-test/
    brief.json
    state.json          ← phase: "done"
    story.json
    character_ref.png
    storyboard.png
    page1.png … page12.png
  ```

- [ ] **Step 5: Commit final state**

  ```bash
  git add tools/
  git commit -m "feat: complete image generation workflow"
  ```
