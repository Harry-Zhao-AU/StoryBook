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
