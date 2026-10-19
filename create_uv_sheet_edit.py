from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "source-interior.png"
REFERENCE = ROOT / "reference-stone.png"
OUTPUT = ROOT / "edited-uv-sheet-warm-cream.png"
COMPARISON = ROOT / "before-after-comparison.png"


def polygon_mask(size, polygons):
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    for polygon in polygons:
        draw.polygon(polygon, fill=255)
    return mask


def rectangle_mask(size, rectangles):
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    for rectangle in rectangles:
        draw.rectangle(rectangle, fill=255)
    return mask


def fitted_texture(reference, width, height, crop_position=0.48):
    """Scale without distortion, then crop a slab-sized texture."""
    scale = max(width / reference.width, height / reference.height)
    resized = reference.resize(
        (round(reference.width * scale), round(reference.height * scale)),
        Image.Resampling.LANCZOS,
    )
    left = round((resized.width - width) * crop_position)
    top = round((resized.height - height) * 0.5)
    return resized.crop((left, top, left + width, top + height))


def apply_warm_lighting(image):
    """Turn neutral white light into a soft cream tone without yellowing wood."""
    rgb = np.asarray(image).astype(np.float32)
    maximum = rgb.max(axis=2)
    minimum = rgb.min(axis=2)
    saturation = maximum - minimum
    luminance = rgb.mean(axis=2)

    # Warm only bright, near-neutral surfaces so the room keeps natural colours.
    neutral = np.clip(1.0 - saturation / 58.0, 0.0, 1.0)
    bright = np.clip((luminance - 145.0) / 105.0, 0.0, 1.0)
    strength = (neutral * bright * 0.18)[..., None]
    cream = np.array([255.0, 237.0, 204.0], dtype=np.float32)
    warmed = rgb * (1.0 - strength) + cream * strength
    warmed_image = Image.fromarray(np.uint8(np.clip(warmed, 0, 255)), "RGB")

    # Recolour the visible ceiling strips and downlights to warm cream.
    light_core = Image.new("L", image.size, 0)
    core = ImageDraw.Draw(light_core)
    core.line([(303, 0), (390, 122), (688, 122), (809, 0)], fill=225, width=3)
    core.ellipse((360, 129, 379, 139), fill=190)
    core.ellipse((674, 130, 694, 140), fill=190)

    glow = light_core.filter(ImageFilter.GaussianBlur(7))
    glow_layer = Image.new("RGB", image.size, (255, 218, 158))
    warmed_image = Image.composite(glow_layer, warmed_image, glow.point(lambda p: round(p * 0.30)))
    core_layer = Image.new("RGB", image.size, (255, 239, 208))
    return Image.composite(core_layer, warmed_image, light_core)


def main():
    source = Image.open(SOURCE).convert("RGB")
    reference = Image.open(REFERENCE).convert("RGB")
    # Remove the thin black frame present in the supplied product swatch.
    reference = reference.crop((2, 2, reference.width - 2, reference.height - 2))
    width, height = source.size

    # Visible UV-sheet planes: the main feature wall and its matching upper-left return.
    uv_mask = polygon_mask(
        source.size,
        [
            [(223, 150), (707, 150), (707, 412), (223, 412)],
            [(0, 0), (164, 0), (224, 123), (177, 130), (0, 51)],
        ],
    )

    # Preserve doors, artwork, TV panel, display tower, furniture and trim.
    exclusions = rectangle_mask(
        source.size,
        [
            (224, 145, 278, 270),  # artwork and frame
            (273, 151, 350, 414),  # left door and frame
            (426, 153, 530, 354),  # dark TV backing panel
            (449, 240, 575, 325),  # TV and pale surround
            (579, 123, 636, 358),  # glass display tower
            (418, 341, 637, 405),  # media console
            (704, 132, 838, 414),  # right door and frame
            (235, 388, 428, 576),  # foreground dining chairs
            (668, 377, 1024, 576),  # sofa and foreground
        ],
    )
    uv_mask = Image.fromarray(
        np.minimum(
            np.asarray(uv_mask),
            255 - np.asarray(exclusions),
        ).astype(np.uint8),
        "L",
    )
    uv_mask = uv_mask.filter(ImageFilter.GaussianBlur(0.65))

    # Preserve the render's original marble detail while mapping it to the
    # reference swatch's beige, taupe and brown palette.
    gray = ImageEnhance.Contrast(source.convert("L")).enhance(1.06)
    recoloured = ImageOps.colorize(
        gray,
        black=(72, 56, 43),
        mid=(184, 162, 132),
        white=(238, 224, 199),
        blackpoint=18,
        whitepoint=245,
        midpoint=132,
    )

    # Add a restrained amount of the supplied stone pattern so it reads as the
    # requested product colour without obscuring architectural shadows.
    wall_texture = fitted_texture(reference, 662, 294, crop_position=0.48)
    texture_canvas = source.copy()
    texture_canvas.paste(wall_texture, (175, 118))
    stone_finish = Image.blend(recoloured, texture_canvas, 0.16)
    stone_finish = ImageEnhance.Color(stone_finish).enhance(1.02)
    stone_finish = ImageEnhance.Contrast(stone_finish).enhance(0.98)

    replaced = Image.composite(stone_finish, source, uv_mask)
    edited = apply_warm_lighting(replaced)
    edited.save(OUTPUT, quality=95)

    # A single review image keeps the result easy to inspect on GitHub.
    gap = 18
    label_height = 42
    comparison = Image.new("RGB", (width * 2 + gap, height + label_height), (244, 238, 225))
    comparison.paste(source, (0, label_height))
    comparison.paste(edited, (width + gap, label_height))
    labels = ImageDraw.Draw(comparison)
    labels.text((18, 13), "BEFORE", fill=(55, 48, 43))
    labels.text((width + gap + 18, 13), "AFTER - BEIGE STONE + WARM CREAM LIGHT", fill=(55, 48, 43))
    comparison.save(COMPARISON, quality=95)

    print(f"Created {OUTPUT.name} ({edited.width}x{edited.height})")
    print(f"Created {COMPARISON.name} ({comparison.width}x{comparison.height})")


if __name__ == "__main__":
    main()
