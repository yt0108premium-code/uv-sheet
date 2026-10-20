from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "source-interior.png"
REFERENCE_SCREENSHOT = ROOT / "code-2712-reference.png"
PATTERN_CROP = ROOT / "code-2712-pattern-crop.png"
OUTPUT = ROOT / "edited-uv-sheet-code-2712.png"
COMPARISON = ROOT / "code-2712-before-after.png"


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


def crop_code_2712_pattern(screenshot):
    """Extract and flatten the clean inner area of the left CODE 2712 panel."""
    # Coordinates omit the gold border, white handle and page UI.
    pattern = screenshot.crop((58, 360, 201, 670)).convert("RGB")

    # Remove the showroom photograph's broad spotlight/shadow while retaining
    # the printed grey marble lines. The room render supplies its own lighting.
    pixels = np.asarray(pattern).astype(np.float32)
    smooth = np.asarray(pattern.filter(ImageFilter.GaussianBlur(22))).astype(np.float32)
    detail = pixels - smooth
    base = np.array([211.0, 214.0, 213.0], dtype=np.float32)
    flattened = np.clip(base + detail * 1.12, 168, 240).astype(np.uint8)
    pattern = Image.fromarray(flattened, "RGB")
    pattern = ImageEnhance.Contrast(pattern).enhance(1.04)
    pattern = ImageEnhance.Color(pattern).enhance(0.72)
    pattern.save(PATTERN_CROP, quality=95)
    return pattern


def tile_vertical_panels(pattern, size, wall_box):
    """Lay the tall product swatch as realistic adjacent UV-sheet panels."""
    canvas = Image.new("RGB", size, (225, 226, 223))
    left, top, right, bottom = wall_box
    wall_height = bottom - top
    scale = wall_height / pattern.height
    panel_width = max(1, round(pattern.width * scale))
    panel = pattern.resize((panel_width, wall_height), Image.Resampling.LANCZOS)
    panel = panel.filter(ImageFilter.UnsharpMask(radius=1.0, percent=80, threshold=3))

    x = left
    index = 0
    while x < right:
        current = ImageOps.mirror(panel) if index % 2 else panel
        canvas.paste(current, (x, top))
        x += panel_width
        index += 1

    # Use the same material on the upper-left UV-sheet return.
    return_pattern = pattern.resize((250, 534), Image.Resampling.LANCZOS)
    canvas.paste(return_pattern, (0, 0))
    return canvas


def relight_texture(texture, source, mask):
    """Transfer broad room illumination to the pattern without old orange veins."""
    source_luma = np.asarray(source.convert("L").filter(ImageFilter.GaussianBlur(18))).astype(np.float32)
    texture_rgb = np.asarray(texture).astype(np.float32)
    texture_luma = np.asarray(texture.convert("L").filter(ImageFilter.GaussianBlur(8))).astype(np.float32)
    valid = np.asarray(mask) > 32

    source_mean = float(source_luma[valid].mean())
    texture_mean = float(texture_luma[valid].mean())
    ratio = np.clip(
        (source_luma / source_mean) / (texture_luma / texture_mean + 1e-6),
        0.74,
        1.09,
    )
    relit = np.clip(texture_rgb * ratio[..., None], 0, 255).astype(np.uint8)
    result = Image.fromarray(relit, "RGB")
    result = ImageEnhance.Contrast(result).enhance(0.96)
    return ImageEnhance.Color(result).enhance(0.88)


def apply_warm_cream_lighting(image):
    rgb = np.asarray(image).astype(np.float32)
    maximum = rgb.max(axis=2)
    minimum = rgb.min(axis=2)
    saturation = maximum - minimum
    luminance = rgb.mean(axis=2)

    neutral = np.clip(1.0 - saturation / 58.0, 0.0, 1.0)
    bright = np.clip((luminance - 145.0) / 105.0, 0.0, 1.0)
    strength = (neutral * bright * 0.10)[..., None]
    cream = np.array([255.0, 238.0, 207.0], dtype=np.float32)
    warmed = rgb * (1.0 - strength) + cream * strength
    warmed_image = Image.fromarray(np.uint8(np.clip(warmed, 0, 255)), "RGB")

    light_core = Image.new("L", image.size, 0)
    core = ImageDraw.Draw(light_core)
    core.line([(303, 0), (390, 122), (688, 122), (809, 0)], fill=215, width=3)
    core.ellipse((360, 129, 379, 139), fill=185)
    core.ellipse((674, 130, 694, 140), fill=185)

    glow = light_core.filter(ImageFilter.GaussianBlur(7))
    glow_layer = Image.new("RGB", image.size, (255, 220, 164))
    warmed_image = Image.composite(glow_layer, warmed_image, glow.point(lambda p: round(p * 0.28)))
    core_layer = Image.new("RGB", image.size, (255, 240, 211))
    return Image.composite(core_layer, warmed_image, light_core)


def main():
    source = Image.open(SOURCE).convert("RGB")
    screenshot = Image.open(REFERENCE_SCREENSHOT).convert("RGB")
    pattern = crop_code_2712_pattern(screenshot)
    width, height = source.size

    uv_mask = polygon_mask(
        source.size,
        [
            [(223, 150), (707, 150), (707, 412), (223, 412)],
            [(0, 0), (164, 0), (224, 123), (177, 130), (0, 51)],
        ],
    )
    exclusions = rectangle_mask(
        source.size,
        [
            (224, 145, 278, 270),  # artwork
            (273, 151, 350, 414),  # left door
            (426, 153, 530, 354),  # dark TV panel
            (449, 240, 575, 325),  # TV and surround
            (579, 123, 636, 358),  # display tower
            (418, 341, 637, 405),  # media console
            (704, 132, 838, 414),  # right door
            (235, 388, 428, 576),  # dining chairs
            (668, 377, 1024, 576),  # sofa
        ],
    )
    uv_mask = Image.fromarray(
        np.minimum(np.asarray(uv_mask), 255 - np.asarray(exclusions)).astype(np.uint8),
        "L",
    ).filter(ImageFilter.GaussianBlur(0.65))

    texture = tile_vertical_panels(pattern, source.size, (223, 150, 707, 412))
    texture = relight_texture(texture, source, uv_mask)
    replaced = Image.composite(texture, source, uv_mask)
    edited = apply_warm_cream_lighting(replaced)
    edited.save(OUTPUT, quality=95)

    gap = 18
    label_height = 42
    comparison = Image.new("RGB", (width * 2 + gap, height + label_height), (242, 242, 239))
    comparison.paste(source, (0, label_height))
    comparison.paste(edited, (width + gap, label_height))
    labels = ImageDraw.Draw(comparison)
    labels.text((18, 13), "BEFORE", fill=(48, 48, 46))
    labels.text((width + gap + 18, 13), "AFTER - UV SHEET CODE 2712", fill=(48, 48, 46))
    comparison.save(COMPARISON, quality=95)

    print(f"Extracted {PATTERN_CROP.name}: {pattern.size[0]}x{pattern.size[1]}")
    print(f"Created {OUTPUT.name}: {edited.size[0]}x{edited.size[1]}")
    print(f"Created {COMPARISON.name}: {comparison.size[0]}x{comparison.size[1]}")


if __name__ == "__main__":
    main()
