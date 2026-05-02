#!/usr/bin/env python3
import base64
import io
import os
import sys
import urllib.request
from pathlib import Path

from dotenv import load_dotenv
from openai import AzureOpenAI
from PIL import Image

from state import get_output_dir, load_state, save_state, load_story, save_brief
from prompts import character_ref_prompt, storyboard_prompt, panel_prompt


def crop_all_panels(storyboard_path: Path, output_dir: Path, total: int) -> None:
    """Crop all panels from the storyboard and save as panel_1.png … panel_N.png."""
    img = Image.open(storyboard_path)
    w, h = img.size
    cols, rows = 4, 3
    pw, ph = w // cols, h // rows
    for n in range(1, total + 1):
        col = (n - 1) % cols
        row = (n - 1) // cols
        crop = img.crop((col * pw, row * ph, (col + 1) * pw, (row + 1) * ph))
        crop.save(output_dir / f"panel_{n}.png")
    print(f"Cropped {total} panels from storyboard.")


def generate_image(
    client: AzureOpenAI,
    prompt: str,
    reference_images: list,
    size: str,
    output_path: Path,
    deployment: str,
) -> None:
    handles = []
    try:
        open_refs = []
        for ref in reference_images:
            if isinstance(ref, Path):
                f = open(ref, "rb")
                handles.append(f)
                open_refs.append(f)
            else:
                open_refs.append(ref)
        image_arg = open_refs[0] if len(open_refs) == 1 else open_refs
        response = client.images.edit(
            model=deployment,
            image=image_arg,
            prompt=prompt,
            size=size,
            n=1,
        )
    finally:
        for f in handles:
            f.close()

    item = response.data[0]
    if item.b64_json:
        image_bytes = base64.b64decode(item.b64_json)
    else:
        with urllib.request.urlopen(item.url) as r:
            image_bytes = r.read()
    Image.open(io.BytesIO(image_bytes)).save(output_path)


def do_generate(
    client: AzureOpenAI, state: dict, story: dict, output_dir: Path, deployment: str
) -> None:
    phase = state["phase"]

    if phase in ("character_pending", "storyboard_pending", "panel_pending"):
        print("Already generated — run with --approve or --feedback.")
        return

    if phase == "done":
        print(f"All panels complete. Upload output/{state['id']}/ to Blob Storage.")
        return

    if phase == "story_approved":
        output_path = output_dir / "character_ref.png"
        prompt = character_ref_prompt(story["character_description"])
        print("[Phase 1] Generating character reference sheet...")
        generate_image(client, prompt, [Path(state["photo_path"])], "1536x1024", output_path, deployment)
        state["phase"] = "character_pending"
        save_state(state)
        print(f"GENERATED: {output_path}")

    elif phase == "character_approved":
        output_path = output_dir / "storyboard.png"
        scene_descriptions = [p["scene_description"] for p in story["pages"]]
        prompt = storyboard_prompt(scene_descriptions)
        print("[Phase 2] Generating storyboard overview...")
        generate_image(client, prompt, [output_dir / "character_ref.png"], "1536x1024", output_path, deployment)
        state["phase"] = "storyboard_pending"
        save_state(state)
        print(f"GENERATED: {output_path}")

    elif phase == "storyboard_approved":
        pages = story["pages"]
        panel_num = state.get("panels_completed", 0) + 1
        if panel_num > len(pages):
            state["phase"] = "done"
            save_state(state)
            print(f"All panels complete. Upload output/{state['id']}/ to Blob Storage.")
            return
        output_path = output_dir / f"page{panel_num}.png"
        panel_crop = output_dir / f"panel_{panel_num}.png"
        if not panel_crop.exists():
            crop_all_panels(output_dir / "storyboard.png", output_dir, len(pages))
        refs = [panel_crop, output_dir / "character_ref.png"]
        prev_page = output_dir / f"page{panel_num - 1}.png"
        if prev_page.exists():
            refs.append(prev_page)
        prompt = panel_prompt(pages[panel_num - 1]["scene_description"], panel_num)
        print(f"[Phase 3] Generating panel {panel_num}/{len(pages)}...")
        generate_image(client, prompt, refs, "1024x1024", output_path, deployment)
        state["phase"] = "panel_pending"
        state["current_panel"] = panel_num
        save_state(state)
        print(f"GENERATED: {output_path}")


def do_approve(state: dict, story: dict, output_dir: Path) -> None:
    phase = state["phase"]

    if phase == "character_pending":
        state["phase"] = "character_approved"
        save_state(state)
        print("Approved character reference. Run again to generate storyboard.")

    elif phase == "storyboard_pending":
        crop_all_panels(output_dir / "storyboard.png", output_dir, len(story["pages"]))
        state["phase"] = "storyboard_approved"
        save_state(state)
        print("Approved storyboard. Run again to start generating panels.")

    elif phase == "panel_pending":
        panel_num = state["current_panel"]
        total = len(story["pages"])
        state["panels_completed"] = panel_num
        if panel_num >= total:
            state["phase"] = "done"
            save_state(state)
            print(f"Approved panel {panel_num}/{total}. All done!")
        else:
            state["phase"] = "storyboard_approved"
            save_state(state)
            print(f"Approved panel {panel_num}/{total}. Run again to generate panel {panel_num + 1}.")

    else:
        print(f"Nothing to approve in phase '{phase}'.")


def do_feedback(
    client: AzureOpenAI, state: dict, story: dict, output_dir: Path, deployment: str, feedback: str
) -> None:
    phase = state["phase"]

    if phase == "character_pending":
        output_path = output_dir / "character_ref.png"
        desc = f"{story['character_description']}. Feedback: {feedback}"
        prompt = character_ref_prompt(desc)
        print("[Phase 1] Regenerating character reference sheet...")
        generate_image(client, prompt, [Path(state["photo_path"])], "1536x1024", output_path, deployment)
        save_state(state)
        print(f"REGENERATED: {output_path}")

    elif phase == "storyboard_pending":
        output_path = output_dir / "storyboard.png"
        scene_descriptions = [p["scene_description"] for p in story["pages"]]
        prompt = storyboard_prompt(scene_descriptions) + f"\n\nFeedback: {feedback}"
        print("[Phase 2] Regenerating storyboard...")
        generate_image(client, prompt, [output_dir / "character_ref.png"], "1536x1024", output_path, deployment)
        save_state(state)
        print(f"REGENERATED: {output_path}")

    elif phase == "panel_pending":
        panel_num = state["current_panel"]
        pages = story["pages"]
        output_path = output_dir / f"page{panel_num}.png"
        panel_crop = output_dir / f"panel_{panel_num}.png"
        if not panel_crop.exists():
            crop_all_panels(output_dir / "storyboard.png", output_dir, len(pages))
        refs = [panel_crop, output_dir / "character_ref.png"]
        prev_page = output_dir / f"page{panel_num - 1}.png"
        if prev_page.exists():
            refs.append(prev_page)
        prompt = panel_prompt(pages[panel_num - 1]["scene_description"], panel_num) + f"\n\nFeedback: {feedback}"
        print(f"[Phase 3] Regenerating panel {panel_num}/{len(pages)}...")
        generate_image(client, prompt, refs, "1024x1024", output_path, deployment)
        save_state(state)
        print(f"REGENERATED: {output_path}")

    else:
        print(f"Nothing to regenerate in phase '{phase}'.")


def main(argv: list[str] | None = None) -> None:
    import argparse
    load_dotenv(Path(__file__).parent / ".env")

    parser = argparse.ArgumentParser(description="Generate storybook illustrations via GPT-Image-2")
    parser.add_argument("--id", required=True, help="Story ID (e.g. pirate)")
    parser.add_argument("--photo", help="Path to reference photo (required on first run)")
    parser.add_argument("--approve", action="store_true", help="Approve the last generated image")
    parser.add_argument("--feedback", help="Regenerate last image with this feedback")
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

    if args.approve:
        do_approve(state, story, output_dir)
        return

    api_key = os.environ.get("AZURE_OPENAI_API_KEY")
    if not api_key:
        print("Error: AZURE_OPENAI_API_KEY is not set. Add it to tools/.env", file=sys.stderr)
        sys.exit(1)

    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    if not endpoint:
        print("Error: AZURE_OPENAI_ENDPOINT is not set. Add it to tools/.env", file=sys.stderr)
        sys.exit(1)

    api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2025-04-01-preview")
    deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-image-2")

    client = AzureOpenAI(
        api_key=api_key,
        azure_endpoint=endpoint,
        api_version=api_version,
    )

    if args.feedback:
        do_feedback(client, state, story, output_dir, deployment, args.feedback)
    else:
        do_generate(client, state, story, output_dir, deployment)


if __name__ == "__main__":
    main()
