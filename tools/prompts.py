STYLE = (
    "Studio Ghibli anime style, rich oil-painting-like texture with visible brushstrokes, "
    "dramatic cinematic golden-hour lighting with deep warm shadows, "
    "detailed fabric and fur textures, expressive Ghibli characters, "
    "deep atmospheric perspective, vivid saturated colour palette"
)


def character_ref_prompt(character_description: str) -> str:
    return (
        f"Character reference sheet for a children's storybook. "
        f"Show all characters from this description: {character_description}. "
        f"For each character, show front view, 3/4 view, and side profile arranged side by side. "
        f"Print each character's name as a label underneath their views. "
        f"Maintain exact likeness to the reference photo for the human character. "
        f"Clean white background, thin border separating each character section. "
        f"{STYLE}."
    )


def storyboard_prompt(scene_descriptions: list[str]) -> str:
    scenes = "\n".join(
        f"Panel {i + 1}: {desc}" for i, desc in enumerate(scene_descriptions)
    )
    n = len(scene_descriptions)
    return (
        f"{n}-panel storyboard grid for a children's story. "
        f"Arrange all {n} panels in a grid, each labelled with its number. "
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
