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
