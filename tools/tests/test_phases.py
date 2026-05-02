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
