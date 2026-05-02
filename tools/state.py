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
