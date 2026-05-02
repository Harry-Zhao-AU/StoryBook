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

from state import get_output_dir, load_state, save_state, load_story, save_brief
from prompts import character_ref_prompt, storyboard_prompt, panel_prompt

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
