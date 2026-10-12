# text_utils.py — Robust text wrapping and auto-fitting for Pygame
import pygame


def wrap_text_to_lines(text: str, font: pygame.font.Font, max_width: int) -> list[str]:
    """
    Splits text into multiple lines such that no line exceeds max_width pixels.
    Handles explicit newlines as well as word wrapping.
    """
    paragraphs = text.split('\n')
    lines = []

    for para in paragraphs:
        if not para.strip():
            lines.append("")
            continue

        words = para.split(' ')
        current_line = ""

        for word in words:
            test_line = f"{current_line} {word}".strip() if current_line else word
            width, _ = font.size(test_line)

            if width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

    return lines


def draw_wrapped_text(
    surface: pygame.Surface,
    text: str,
    font: pygame.font.Font,
    color: tuple[int, int, int],
    max_width: int,
    center_x: int | None = None,
    center_y: int | None = None,
    top_y: int | None = None,
    left_x: int | None = None,
    line_spacing: int = 4,
    shadow_color: tuple[int, int, int] | None = None,
    align: str = "center"
) -> int:
    """
    Draws wrapped text onto the surface.
    align: 'center' or 'left'
    Returns the total pixel height rendered.
    """
    lines = wrap_text_to_lines(text, font, max_width)
    if not lines:
        return 0

    line_height = font.get_linesize() + line_spacing
    total_height = len(lines) * line_height - line_spacing

    if top_y is None and center_y is not None:
        start_y = center_y - total_height // 2
    elif top_y is not None:
        start_y = top_y
    else:
        start_y = 0

    for i, line in enumerate(lines):
        if not line:
            continue

        curr_y = start_y + i * line_height
        rendered = font.render(line, True, color)

        if align == "center" and center_x is not None:
            dest_x = center_x - rendered.get_width() // 2
        elif left_x is not None:
            dest_x = left_x
        elif center_x is not None:
            dest_x = center_x - max_width // 2
        else:
            dest_x = 0

        if shadow_color:
            sh = font.render(line, True, shadow_color)
            surface.blit(sh, (dest_x + 1, curr_y + 1))

        surface.blit(rendered, (dest_x, curr_y))

    return total_height
