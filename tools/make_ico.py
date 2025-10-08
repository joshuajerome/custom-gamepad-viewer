"""Generate a high‑quality multi‑size Windows ICO from a PNG.

Usage:
  uv run python tools/make_ico.py <input.png> [output.ico]

Defaults output to packaging/windows/CustomGamepadViewer.ico

Notes for crisp taskbar icons on HiDPI:
  - Include sizes for common DPI steps: 256, 128, 96, 64, 48, 40, 32, 24, 20, 16
  - Use LANCZOS resampling and a slight unsharp mask at small sizes
"""

import sys
from pathlib import Path
from PIL import Image, ImageFilter

def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[1] in {"-h", "--help"}:
        print(__doc__)
        return 0

    src = Path(argv[1])
    if not src.exists():
        print(f"Input not found: {src}")
        return 2

    if len(argv) >= 3:
        dst = Path(argv[2])
    else:
        dst = Path("packaging/windows/CustomGamepadViewer.ico")

    dst.parent.mkdir(parents=True, exist_ok=True)

    sizes = [
        (256, 256), (128, 128), (96, 96), (64, 64),
        (48, 48), (40, 40), (32, 32), (24, 24), (20, 20), (16, 16),
    ]

    img = Image.open(src).convert("RGBA")

    # Ensure square canvas; pad with transparent pixels if needed
    w, h = img.size
    if w != h:
        side = max(w, h)
        bg = Image.new("RGBA", (side, side), (0, 0, 0, 0))
        bg.paste(img, ((side - w) // 2, (side - h) // 2))
        img = bg

    # Create a base at max size to downscale from
    base = img
    if max(img.size) < 1024:
        # Upscale slightly to improve downsampling quality when source is small
        scale = 1024 / max(img.size)
        base = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)

    # Precompute resized variants with LANCZOS; apply gentle sharpening to small sizes
    variants: list[Image.Image] = []
    for (w, h) in sizes:
        im = base.resize((w, h), Image.LANCZOS)
        if w <= 32:
            im = im.filter(ImageFilter.UnsharpMask(radius=0.6, percent=120, threshold=2))
        elif w <= 64:
            im = im.filter(ImageFilter.UnsharpMask(radius=0.5, percent=80, threshold=2))
        variants.append(im)

    # Pillow selects ICO format by extension
    # Provide explicit sizes to embed all frames
    variants[0].save(dst, sizes=[im.size for im in variants])
    print("Wrote", dst)
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
