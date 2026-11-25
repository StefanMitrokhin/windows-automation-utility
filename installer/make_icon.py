from __future__ import annotations

import sys
from pathlib import Path

FONT_CANDIDATES = (
    Path(r"C:\Windows\Fonts\arialbd.ttf"),
    Path(r"C:\Windows\Fonts\segoeuib.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    Path("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
)


def main() -> None:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("Pillow is required", file=sys.stderr)
        raise SystemExit(1) from None

    font_path = next((p for p in FONT_CANDIDATES if p.is_file()), None)
    if font_path is None:
        print("No font found:", file=sys.stderr)
        for path in FONT_CANDIDATES:
            print(f"  {path}", file=sys.stderr)
        raise SystemExit(1)

    size = 256
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    margin = size // 8
    radius = size // 6
    draw.rounded_rectangle(
        (margin, margin, size - margin, size - margin),
        radius=radius,
        fill="#1F6AA5",
    )
    font = ImageFont.truetype(str(font_path), int(size * 0.38))
    text = "DK"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text(((size - tw) / 2, (size - th) / 2 - 8), text, fill="white", font=font)
    assets = Path(__file__).resolve().parent.parent / "deskkit" / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    png_path = assets / "icon.png"
    ico_path = assets / "icon.ico"
    image.save(png_path)
    image.save(ico_path, sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (256, 256)])


if __name__ == "__main__":
    main()
