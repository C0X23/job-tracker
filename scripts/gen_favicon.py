"""Generate the Job Tracker favicon set from a vector definition.

Outputs in static/favicons/:
- favicon.ico (16, 32, 48 multi-resolution)
- favicon-16x16.png
- favicon-32x32.png
- favicon-512x512.png (master)

Run: python scripts/gen_favicon.py
"""

from pathlib import Path

from PIL import Image, ImageDraw

ACCENT = (31, 77, 58, 255)  # #1F4D3A
TRANSPARENT = (0, 0, 0, 0)

OUT = Path(__file__).resolve().parent.parent / "static" / "favicons"
OUT.mkdir(parents=True, exist_ok=True)


def draw_tree(size: int) -> Image.Image:
    """Draw a 3-tier fir tree silhouette on a transparent canvas of `size` px."""
    img = Image.new("RGBA", (size, size), TRANSPARENT)
    draw = ImageDraw.Draw(img)

    s = size
    cx = s / 2.0

    # Vertical layout. Trunk butts up against the bottom tier (no gap).
    top = 0.08 * s
    trunk_h = 0.10 * s
    base_y = s - 0.04 * s  # bottom of trunk
    trunk_top = base_y - trunk_h  # also the bottom of the lowest tier
    foliage_h = trunk_top - top

    # Three overlapping tiers. With overlap = 0.42 * tier_h:
    #   total = tier_h + 2*(tier_h - overlap) = (3 - 2*0.42) * tier_h
    overlap_ratio = 0.42
    tier_h = foliage_h / (3 - 2 * overlap_ratio)
    overlap = tier_h * overlap_ratio

    # Widths grow tier by tier (top → bottom).
    margin_x = 0.10 * s
    widths = [
        s - 2 * (margin_x + 0.18 * s),  # top tier (narrowest)
        s - 2 * (margin_x + 0.09 * s),  # middle
        s - 2 * margin_x,  # bottom (widest)
    ]

    apex_y = top
    for w in widths:
        bottom_y = apex_y + tier_h
        half = w / 2.0
        draw.polygon(
            [(cx, apex_y), (cx + half, bottom_y), (cx - half, bottom_y)],
            fill=ACCENT,
        )
        apex_y = bottom_y - overlap

    # Trunk: rectangle butted against the bottom tier.
    trunk_w = 0.16 * s
    draw.rectangle(
        [(cx - trunk_w / 2, trunk_top), (cx + trunk_w / 2, base_y)],
        fill=ACCENT,
    )

    return img


def main() -> None:
    # Master 512×512 — drawn at 4× then downsampled for super-crisp edges.
    high = draw_tree(2048)
    master = high.resize((512, 512), Image.LANCZOS)
    master.save(OUT / "favicon-512x512.png")

    # 32×32 — drawn natively (better than downsampling) for pixel-crisp edges.
    icon_32 = draw_tree(32)
    icon_32.save(OUT / "favicon-32x32.png")

    # 16×16 — same.
    icon_16 = draw_tree(16)
    icon_16.save(OUT / "favicon-16x16.png")

    # 48×48 for the .ico bundle.
    icon_48 = draw_tree(48)

    # Build favicon.ico with the three native sizes embedded.
    icon_32.save(
        OUT / "favicon.ico",
        format="ICO",
        sizes=[(16, 16), (32, 32), (48, 48)],
        append_images=[icon_16, icon_48],
    )

    print(f"Wrote {len(list(OUT.glob('*')))} files to {OUT}")
    for f in sorted(OUT.iterdir()):
        print(f"  {f.name}  ({f.stat().st_size:,} B)")


if __name__ == "__main__":
    main()
