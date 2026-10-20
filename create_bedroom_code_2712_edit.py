from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "bedroom-source.png"
PATTERN = ROOT / "code-2712-pattern-crop.png"
OUTPUT = ROOT / "bedroom-white-ceiling-code-2712.png"
COMPARISON = ROOT / "bedroom-before-after.png"


def polygon_mask(size, polygons):
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    for polygon in polygons:
        draw.polygon(polygon, fill=255)
    return mask


def build_pattern_canvas(pattern, size, panel_width=110):
    """Create adjacent full-height panels from the supplied CODE 2712 print."""
    width, height = size
    scaled_height = height + 120
    scaled_width = max(panel_width, round(pattern.width * scaled_height / pattern.height))
    panel = pattern.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)
    panel = panel.crop(((scaled_width - panel_width) // 2, 0, (scaled_width - panel_width) // 2 + panel_width, height))
    panel = panel.filter(ImageFilter.UnsharpMask(radius=1.0, percent=65, threshold=3))

    canvas = Image.new("RGB", size, (211, 214, 213))
    x = -panel_width
    index = 0
    while x < width:
        tile = ImageOps.mirror(panel) if index % 2 else panel
        canvas.paste(tile, (x, 0))
        x += panel_width
        index += 1
    return canvas


def preserve_fixture_mask(size):
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)

    # Furniture and fitted objects stay untouched.
    draw.polygon([(47, 72), (439, 176), (439, 457), (15, 541)], fill=255)  # wardrobe
    draw.polygon([(476, 214), (550, 194), (551, 348), (476, 366)], fill=255)  # display cabinet
    draw.polygon([(566, 326), (716, 313), (770, 346), (813, 576), (366, 576), (368, 448), (523, 383)], fill=255)  # bed
    draw.polygon([(590, 150), (741, 135), (743, 204), (594, 220)], fill=255)  # AC
    draw.rectangle((527, 346, 576, 425), fill=255)  # plant and bedside objects

    # Preserve the feature artwork on the headboard wall.
    draw.ellipse((625, 223, 758, 299), fill=255)  # grey oval backing
    draw.ellipse((625, 222, 708, 302), fill=255)  # black circular feature
    draw.rectangle((584, 256, 756, 270), fill=255)  # gold horizontal detail

    # Preserve the framed artwork on the right wall.
    draw.polygon([(929, 0), (1024, 0), (1024, 393), (958, 391)], fill=255)
    return mask


def apply_code_2712_walls(source, pattern):
    size = source.size
    wall_polygons = [
        [(0, 0), (47, 0), (69, 72), (16, 541), (0, 576)],  # left return
        [(438, 163), (593, 121), (597, 419), (438, 458)],  # display wall
        [(592, 120), (770, 77), (771, 465), (596, 419)],  # headboard wall
        [(769, 77), (902, 48), (947, 526), (770, 465)],  # right wall
        [(901, 48), (929, 0), (1024, 0), (1024, 576), (946, 526)],  # far-right return
    ]
    wall_mask = polygon_mask(size, wall_polygons)
    fixtures = preserve_fixture_mask(size)
    wall_mask = Image.fromarray(
        np.minimum(np.asarray(wall_mask), 255 - np.asarray(fixtures)).astype(np.uint8),
        "L",
    ).filter(ImageFilter.GaussianBlur(0.7))

    texture = build_pattern_canvas(pattern, size)
    texture_pixels = np.asarray(texture).astype(np.float32)

    # Keep the new light-grey sheets readable while respecting each wall plane's depth.
    shade = np.ones((size[1], size[0]), dtype=np.float32)
    shade[:, :80] *= 0.91
    shade[:, 438:593] *= 0.94
    shade[:, 593:771] *= 0.98
    right_gradient = np.linspace(0.94, 0.85, 253, dtype=np.float32)
    shade[:, 771:1024] *= right_gradient[None, :]
    texture_pixels = np.clip(texture_pixels * shade[..., None], 0, 255).astype(np.uint8)
    texture = Image.fromarray(texture_pixels, "RGB")
    texture = ImageEnhance.Contrast(texture).enhance(0.98)

    return Image.composite(texture, source, wall_mask)


def create_white_panel_ceiling(image):
    size = image.size
    ceiling_polygon = [(47, 0), (875, 0), (891, 69), (439, 181), (68, 73)]
    ceiling_mask = polygon_mask(size, [ceiling_polygon]).filter(ImageFilter.GaussianBlur(0.65))

    # Matte warm-white surface with a subtle back-to-front tonal gradient.
    ceiling = Image.new("RGB", size, (244, 242, 236))
    ceiling_pixels = np.asarray(ceiling).astype(np.float32)
    y_gradient = np.linspace(0.98, 1.02, size[1], dtype=np.float32)[:, None, None]
    ceiling_pixels = np.clip(ceiling_pixels * y_gradient, 0, 255).astype(np.uint8)
    ceiling = Image.fromarray(ceiling_pixels, "RGB")

    # Fine perspective seams make the surface read as installed white panels.
    seams = Image.new("RGBA", size, (0, 0, 0, 0))
    seam_draw = ImageDraw.Draw(seams)
    vanishing = (439, 181)
    for top_x in (48, 245, 445, 645, 875):
        seam_draw.line([vanishing, (top_x, 0)], fill=(178, 178, 174, 105), width=1)
    for left, right in [((61, 48), (881, 46)), ((66, 70), (891, 68)), ((196, 110), (724, 110)), ((316, 145), (584, 145))]:
        seam_draw.line([left, right], fill=(185, 184, 180, 82), width=1)
    seams.putalpha(Image.composite(seams.getchannel("A"), Image.new("L", size, 0), ceiling_mask))
    ceiling = Image.alpha_composite(ceiling.convert("RGBA"), seams).convert("RGB")
    result = Image.composite(ceiling, image, ceiling_mask)

    # Warm perimeter cove and six recessed lights, arranged symmetrically in perspective.
    cove_core = Image.new("L", size, 0)
    cove_draw = ImageDraw.Draw(cove_core)
    cove_draw.line([(68, 73), (439, 181), (891, 69)], fill=175, width=3)
    cove_draw.line([(48, 1), (875, 1)], fill=105, width=2)
    cove_glow = cove_core.filter(ImageFilter.GaussianBlur(10))
    warm_glow = Image.new("RGB", size, (255, 218, 157))
    result = Image.composite(warm_glow, result, cove_glow.point(lambda p: round(p * 0.35)))
    cove_surface = Image.new("RGB", size, (255, 238, 204))
    result = Image.composite(cove_surface, result, cove_core)

    light_mask = Image.new("L", size, 0)
    light_draw = ImageDraw.Draw(light_mask)
    lights = [
        (247, 35, 7), (744, 34, 7),
        (301, 91, 6), (654, 91, 6),
        (379, 139, 5), (557, 139, 5),
    ]
    for x, y, radius in lights:
        light_draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=235)

    light_glow = light_mask.filter(ImageFilter.GaussianBlur(13))
    result = Image.composite(warm_glow, result, light_glow.point(lambda p: round(p * 0.42)))
    fixture = Image.new("RGB", size, (255, 244, 219))
    result = Image.composite(fixture, result, light_mask)

    # Small neutral trim rings keep the downlights architectural rather than painted dots.
    trim = Image.new("RGBA", size, (0, 0, 0, 0))
    trim_draw = ImageDraw.Draw(trim)
    for x, y, radius in lights:
        trim_draw.ellipse((x - radius - 1, y - radius - 1, x + radius + 1, y + radius + 1), outline=(112, 108, 101, 125), width=1)
    return Image.alpha_composite(result.convert("RGBA"), trim).convert("RGB")


def main():
    source = Image.open(SOURCE).convert("RGB")
    pattern = Image.open(PATTERN).convert("RGB")

    walls_updated = apply_code_2712_walls(source, pattern)
    edited = create_white_panel_ceiling(walls_updated)
    edited.save(OUTPUT, quality=95)

    gap = 18
    label_height = 42
    comparison = Image.new("RGB", (source.width * 2 + gap, source.height + label_height), (244, 243, 239))
    comparison.paste(source, (0, label_height))
    comparison.paste(edited, (source.width + gap, label_height))
    labels = ImageDraw.Draw(comparison)
    labels.text((18, 13), "BEFORE", fill=(48, 47, 44))
    labels.text((source.width + gap + 18, 13), "AFTER - WHITE PANEL CEILING + UV SHEET CODE 2712", fill=(48, 47, 44))
    comparison.save(COMPARISON, quality=95)

    print(f"Created {OUTPUT.name}: {edited.width}x{edited.height}")
    print(f"Created {COMPARISON.name}: {comparison.width}x{comparison.height}")


if __name__ == "__main__":
    main()
