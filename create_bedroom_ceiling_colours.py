from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "bedroom-ceiling-source.jpg"

# A balanced set of light, medium, and dark panel finishes.
COLOURS = {
    "warm-ivory": (231, 218, 194),
    "natural-oak": (196, 151, 96),
    "ash-grey": (181, 181, 174),
    "sage-grey": (132, 145, 124),
    "walnut": (108, 72, 51),
    "graphite": (67, 71, 74),
    "midnight-blue": (46, 60, 75),
}

CEILING_POLYGON = [
    (124, 0),
    (910, 0),
    (858, 107),
    (580, 193),
    (162, 75),
]


def smoothstep(edge0, edge1, values):
    values = np.clip((values - edge0) / (edge1 - edge0), 0.0, 1.0)
    return values * values * (3.0 - 2.0 * values)


def ceiling_mask(size):
    """Mask only the horizontal slatted ceiling, excluding the fan."""
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.polygon(CEILING_POLYGON, fill=255)

    # Keep the complete fan, down-rod, canopy, and soft anti-aliased edges unchanged.
    fan = Image.new("L", size, 0)
    fan_draw = ImageDraw.Draw(fan)
    fan_draw.ellipse((508, 56, 529, 76), fill=255)  # canopy
    fan_draw.polygon([(514, 67), (523, 67), (522, 132), (511, 139)], fill=255)  # rod
    fan_draw.polygon([(513, 139), (454, 75), (455, 67), (465, 65), (524, 132)], fill=255)
    fan_draw.polygon([(510, 137), (466, 166), (459, 175), (466, 179), (526, 148)], fill=255)
    fan_draw.polygon([(516, 135), (612, 139), (626, 146), (616, 151), (514, 151)], fill=255)
    fan_draw.ellipse((495, 124, 535, 163), fill=255)  # motor housing
    fan = fan.filter(ImageFilter.GaussianBlur(2.0))

    ceiling = np.asarray(mask, dtype=np.float32) / 255.0
    fixture = np.asarray(fan, dtype=np.float32) / 255.0
    ceiling *= 1.0 - fixture
    return ceiling


def recolour_ceiling(source, target_rgb):
    """Tint the panels while preserving slat grooves, lighting, and texture."""
    pixels = np.asarray(source).astype(np.float32)
    height, width = pixels.shape[:2]
    mask = ceiling_mask((width, height))

    # Relative luminance keeps the original wood grain, perspective shading, and grooves.
    luminance = (
        pixels[..., 0] * 0.2126
        + pixels[..., 1] * 0.7152
        + pixels[..., 2] * 0.0722
    )
    panel_samples = luminance[(mask > 0.95) & (luminance > 48) & (luminance < 185)]
    reference_luminance = float(np.median(panel_samples))

    target = np.array(target_rgb, dtype=np.float32)
    target_luminance = float(target @ np.array([0.2126, 0.7152, 0.0722]))

    # Scale the selected colour with the source brightness. A power curve retains
    # dark grooves even when the selected panel finish is very light.
    texture_scale = np.power(np.maximum(luminance, 1.0) / reference_luminance, 0.72)
    desired_luminance = np.clip(target_luminance * texture_scale, 4.0, 250.0)
    tinted = target[None, None, :] * (desired_luminance[..., None] / target_luminance)
    tinted = np.clip(tinted, 0.0, 255.0)

    # Preserve nearly black grooves and all original lighting. Expanding the hottest
    # pixels also retains each LED strip's warm halo instead of tinting it panel colour.
    deep_shadow = 1.0 - smoothstep(18.0, 58.0, luminance)
    bright_fixture = smoothstep(188.0, 246.0, luminance)
    light_cores = np.uint8(((luminance > 160.0) & (mask > 0.2)) * 255)
    light_halo = Image.fromarray(light_cores, "L").filter(ImageFilter.MaxFilter(9))
    light_halo = light_halo.filter(ImageFilter.GaussianBlur(5.0))
    light_preservation = np.asarray(light_halo, dtype=np.float32) / 255.0
    source_preservation = np.maximum.reduce(
        [deep_shadow * 0.82, bright_fixture * 0.98, light_preservation * 0.94]
    )
    tinted = tinted * (1.0 - source_preservation[..., None]) + pixels * source_preservation[..., None]

    # Feather only the architectural boundary; everything outside remains pixel-identical.
    edge_mask = Image.fromarray(np.uint8(np.clip(mask * 255.0, 0, 255)), "L")
    edge_mask = edge_mask.filter(ImageFilter.GaussianBlur(0.65))
    alpha = np.asarray(edge_mask, dtype=np.float32) / 255.0
    result = pixels * (1.0 - alpha[..., None]) + tinted * alpha[..., None]
    return Image.fromarray(np.uint8(np.clip(result + 0.5, 0, 255)), "RGB")


def main():
    source = Image.open(SOURCE).convert("RGB")
    for name, colour in COLOURS.items():
        output = ROOT / f"bedroom-ceiling-{name}.png"
        recolour_ceiling(source, colour).save(output, optimize=True)
        print(f"Created {output.name}: {source.width}x{source.height}")


if __name__ == "__main__":
    main()
