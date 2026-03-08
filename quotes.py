"""
Generate quote card images - PFP as full background, text with shadow + gradient.
"""
import io
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter


def _text_bbox(draw, text: str, font) -> tuple:
    """Get text bounding box (Pillow 9+ has textbbox)."""
    if hasattr(draw, "textbbox"):
        return draw.textbbox((0, 0), text, font=font)
    return draw.textsize(text, font=font)  # old Pillow returns (w, h)

def _wrap_text(draw, text: str, font, max_width: int) -> list:
    """Wrap text to fit max_width."""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip() if current else word
        bbox = _text_bbox(draw, test, font=font)
        w = bbox[2] - bbox[0] if len(bbox) == 4 else bbox[0]
        if w <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _find_font(size: int):
    """Try Papyrus first, then fallbacks."""
    candidates = [
        "/System/Library/Fonts/Supplemental/Papyrus.ttc",
        "/System/Library/Fonts/Supplemental/Papyrus.ttf",
        "/Library/Fonts/Papyrus.ttc",
        "C:\\Windows\\Fonts\\papyrus.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:\\Windows\\Fonts\\arial.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def _draw_centered_text_with_shadow(draw, x: int, y: int, text: str, font, fill, shadow_color=(0, 0, 0), shadow_offset=4) -> int:
    """Draw centered text with heavy shadow. Returns height."""
    bbox = _text_bbox(draw, text, font=font)
    tw = bbox[2] - bbox[0] if len(bbox) == 4 else bbox[0]
    th = bbox[3] - bbox[1] if len(bbox) == 4 else bbox[1]
    cx = x - tw // 2
    # Heavy shadow - multiple layers for thickness
    for dx, dy in [(shadow_offset, shadow_offset), (shadow_offset+1, shadow_offset+1), (shadow_offset+2, shadow_offset+2)]:
        draw.text((cx + dx, y + dy), text, fill=shadow_color, font=font)
    draw.text((cx, y), text, fill=fill, font=font)
    return th


def create_quote_image(
    avatar_bytes: bytes,
    username: str,
    content: str,
    timestamp: datetime,
    *,
    width: int = 1200,
    min_height: int = 900,
    padding: int = 80,
    text_color: tuple[int, int, int] = (255, 255, 255),
    muted_color: tuple[int, int, int] = (200, 200, 200),
) -> bytes:
    """
    Create a poster-style quote card. Image height grows with text length.
    - User's PFP as full background
    - Black gradient at bottom over the text area
    - Heavy shadow on text
    - Quotes around the message
    - Papyrus font
    Returns PNG bytes.
    """
    font_name = _find_font(64)
    font_content = _find_font(52)
    font_time = _find_font(32)
    max_text_width = width - padding * 2

    # Temp image to measure text layout
    temp_img = Image.new("RGB", (width, min_height))
    temp_draw = ImageDraw.Draw(temp_img)

    raw_content = content or "(no content)"
    quoted = f'"{raw_content}"'
    lines = _wrap_text(temp_draw, quoted, font_content, max_text_width)

    # Calculate total height needed
    line_height = 72  # approx per line
    username_bbox = _text_bbox(temp_draw, username, font=font_name)
    username_h = username_bbox[3] - username_bbox[1] if len(username_bbox) == 4 else 40
    try:
        ts_str = timestamp.strftime("%b %d, %Y at ") + timestamp.strftime("%I:%M %p").lstrip("0")
    except (ValueError, TypeError, AttributeError):
        ts_str = str(timestamp)
    ts_bbox = _text_bbox(temp_draw, ts_str, font=font_time)
    ts_h = ts_bbox[3] - ts_bbox[1] if len(ts_bbox) == 4 else 32

    text_block_height = username_h + 36 + (len(lines) * line_height) + 36 + ts_h + 80
    gradient_height = int(text_block_height * 1.2)  # gradient covers text area
    height = max(min_height, 400 + gradient_height)  # no cap - grows with text

    # 1. Full background = avatar scaled to cover (tall enough for all text)
    avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGB")
    try:
        avatar = ImageOps.fit(avatar, (width, height), method=Image.Resampling.LANCZOS)
    except AttributeError:
        avatar = ImageOps.fit(avatar, (width, height), method=Image.LANCZOS)
    avatar = avatar.filter(ImageFilter.GaussianBlur(radius=1))
    img = avatar.copy()

    # 2. Black gradient overlay at bottom
    gradient_top = height - gradient_height
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    for i in range(gradient_height):
        alpha = int(255 * (i / gradient_height) ** 0.7)
        y = gradient_top + i
        overlay_draw.line([(0, y), (width, y)], fill=(0, 0, 0, alpha))
    img = img.convert("RGBA")
    img = Image.alpha_composite(img, overlay)
    img = img.convert("RGB")
    draw = ImageDraw.Draw(img)
    center_x = width // 2

    # 3. Text - all lines, no limit
    y = height - gradient_height + int(gradient_height * 0.2)

    _draw_centered_text_with_shadow(draw, center_x, y, username, font_name, text_color, shadow_offset=5)
    bbox = _text_bbox(draw, username, font=font_name)
    y += (bbox[3] - bbox[1] if len(bbox) == 4 else bbox[1]) + 36

    for line in lines:
        _draw_centered_text_with_shadow(draw, center_x, y, line, font_content, text_color, shadow_offset=5)
        bbox = _text_bbox(draw, line, font=font_content)
        y += (bbox[3] - bbox[1] if len(bbox) == 4 else bbox[1]) + 20
    y += 36

    _draw_centered_text_with_shadow(draw, center_x, y, ts_str, font_time, muted_color, shadow_offset=4)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
