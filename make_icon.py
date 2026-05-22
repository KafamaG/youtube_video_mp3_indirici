"""Generate a modern app icon for the YouTube downloader.

Run once to (re)create app_icon.ico:
    py make_icon.py
"""
from PIL import Image, ImageDraw, ImageFilter


def lerp(a, b, t):
    return int(a + (b - a) * t)


def diagonal_gradient(size, c1, c2):
    img = Image.new("RGB", (size, size), c1)
    px = img.load()
    for y in range(size):
        for x in range(size):
            t = (x + y) / (2 * (size - 1))
            px[x, y] = (lerp(c1[0], c2[0], t),
                        lerp(c1[1], c2[1], t),
                        lerp(c1[2], c2[2], t))
    return img


def make_icon(size):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    # Rounded square gradient body (vibrant indigo -> blue)
    body = diagonal_gradient(size, (96, 92, 246), (37, 99, 235))  # #605cf6 -> #2563eb
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [(0, 0), (size - 1, size - 1)],
        radius=int(size * 0.235),
        fill=255,
    )
    img.paste(body, (0, 0), mask)

    # Inner soft glow / highlight on top-left for depth
    highlight = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    hd = ImageDraw.Draw(highlight)
    hd.ellipse(
        [(-int(size * 0.4), -int(size * 0.55)),
         (int(size * 0.85), int(size * 0.25))],
        fill=(255, 255, 255, 38),
    )
    highlight = highlight.filter(ImageFilter.GaussianBlur(radius=size * 0.06))
    img.alpha_composite(highlight)

    # Subtle inner border for crispness
    border = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    bd = ImageDraw.Draw(border)
    bd.rounded_rectangle(
        [(0, 0), (size - 1, size - 1)],
        radius=int(size * 0.235),
        outline=(255, 255, 255, 28),
        width=max(1, int(size * 0.012)),
    )
    img.alpha_composite(border)

    draw = ImageDraw.Draw(img)
    white = (255, 255, 255, 255)
    cx = size / 2

    # Download arrow (stem + head)
    stem_w = size * 0.18
    stem_top = size * 0.22
    stem_bottom = size * 0.54
    draw.rounded_rectangle(
        [(cx - stem_w / 2, stem_top), (cx + stem_w / 2, stem_bottom)],
        radius=stem_w * 0.35,
        fill=white,
    )

    # Arrow head triangle
    head_w = size * 0.50
    head_top = stem_bottom - stem_w * 0.18  # slight overlap to avoid seam
    head_bottom = size * 0.74
    draw.polygon(
        [
            (cx - head_w / 2, head_top),
            (cx + head_w / 2, head_top),
            (cx, head_bottom),
        ],
        fill=white,
    )

    # Base "tray" (pill bar) under arrow
    tray_y = size * 0.81
    tray_h = size * 0.075
    tray_left = size * 0.21
    tray_right = size * 0.79
    draw.rounded_rectangle(
        [(tray_left, tray_y), (tray_right, tray_y + tray_h)],
        radius=tray_h / 2,
        fill=white,
    )

    return img


def main():
    sizes = [16, 24, 32, 48, 64, 128, 256]
    images = [make_icon(s) for s in sizes]
    images[-1].save(
        "app_icon.ico",
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=images[:-1],
    )
    print(f"Wrote app_icon.ico with sizes {sizes}")


if __name__ == "__main__":
    main()
