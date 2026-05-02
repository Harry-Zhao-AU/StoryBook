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
