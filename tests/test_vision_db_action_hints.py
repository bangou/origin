from PIL import Image, ImageDraw

from vision_db.action_hints import compute_action_hints


def test_compute_action_hints_marks_glowing_buttons() -> None:
    image = Image.new("RGB", (300, 140), "#004f44")
    draw = ImageDraw.Draw(image)
    draw.ellipse((20, 20, 100, 100), fill="#f05d5d")
    draw.ellipse((110, 20, 190, 100), fill="#36a8ff")
    draw.ellipse((200, 20, 280, 100), fill="#1f7b2e")

    result = compute_action_hints(
        image,
        {
            "fold_button_roi": (20, 20, 80, 80),
            "bet_button_roi": (110, 20, 80, 80),
            "check_button_roi": (200, 20, 80, 80),
        },
    )

    assert result["fold_glowing"] is True
    assert result["bet_glowing"] is True
    assert result["check_glowing"] is False
    assert result["can_act_hint"] is True
