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
