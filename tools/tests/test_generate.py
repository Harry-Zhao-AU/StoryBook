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
