"""Fit a GDS PNG preview within the Tiny Tapeout datasheet image limit."""

import sys
from pathlib import Path

from PIL import Image


MAX_BYTES = 500_000


def main() -> None:
    source = Path(sys.argv[1])
    destination = Path(sys.argv[2])
    temporary = destination.with_suffix(".tmp.png")

    with Image.open(source) as original:
        for width in (1600, 1400, 1200, 1000, 800, 600):
            resized = original.convert("RGB")
            resized.thumbnail((width, width), Image.Resampling.LANCZOS)
            for colors in (128, 96, 64, 48, 32):
                preview = resized.quantize(
                    colors=colors,
                    method=Image.Quantize.MEDIANCUT,
                    dither=Image.Dither.NONE,
                )
                preview.save(temporary, optimize=True)
                if temporary.stat().st_size <= MAX_BYTES:
                    temporary.replace(destination)
                    print(f"Wrote {destination} ({preview.width}x{preview.height}, {destination.stat().st_size} bytes)")
                    return

    temporary.unlink(missing_ok=True)
    raise RuntimeError("Could not fit GDS preview within the datasheet image limit")


if __name__ == "__main__":
    main()
