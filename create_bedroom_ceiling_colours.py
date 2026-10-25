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


def full_ceiling_mask(size):
    """Return the complete horizontal ceiling surface mask."""
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).polygon(CEILING_POLYGON, fill=255)
    return mask


def fan_fixture_mask(size):
    """Return a soft mask for the complete fan, rod, and canopy."""
    fan = Image.new("L", size, 0)
    fan_draw = ImageDraw.Draw(fan)
    fan_draw.ellipse((508, 56, 529, 76), fill=255)  # canopy
    fan_draw.polygon([(514, 67), (523, 67), (522, 132), (511, 139)], fill=255)  # rod
    fan_draw.polygon([(513, 139), (454, 75), (455, 67), (465, 65), (524, 132)], fill=255)
    fan_draw.polygon([(510, 137), (466, 166), (459, 175), (466, 179), (526, 148)], fill=255)
    fan_draw.polygon([(516, 135), (612, 139), (626, 146), (616, 151), (514, 151)], fill=255)
    fan_draw.ellipse((495, 124, 535, 163), fill=255)  # motor housing
    return fan.filter(ImageFilter.GaussianBlur(2.0))


def ceiling_mask(size):
    """Mask only the horizontal ceiling, excluding the fan."""
    mask = full_ceiling_mask(size)

    ceiling = np.asarray(mask, dtype=np.float32) / 255.0
    fixture = np.asarray(fan_fixture_mask(size), dtype=np.float32) / 255.0
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


def create_plain_off_white_vox_ceiling(source):
    """Replace the wood slats with broad, plain off-white VOX panels."""
    pixels = np.asarray(source).astype(np.float32)
    height, width = pixels.shape[:2]
    mask = np.asarray(full_ceiling_mask((width, height)), dtype=np.float32) / 255.0

    luminance = (
        pixels[..., 0] * 0.2126
        + pixels[..., 1] * 0.7152
        + pixels[..., 2] * 0.0722
    )

    # A broad blur retains room-scale lighting but removes the original wood grooves.
    soft_light = Image.fromarray(np.uint8(np.clip(luminance, 0, 255)), "L")
    soft_light = np.asarray(soft_light.filter(ImageFilter.GaussianBlur(24.0)), dtype=np.float32)
    reference = float(np.median(soft_light[mask > 0.9]))
    shade = np.clip(0.965 + (soft_light - reference) / 360.0, 0.88, 1.08)

    off_white = np.array((236, 233, 224), dtype=np.float32)
    panel_pixels = np.clip(off_white[None, None, :] * shade[..., None], 0, 250)
    panels = Image.fromarray(np.uint8(panel_pixels + 0.5), "RGB").convert("RGBA")

    # Wide, low-contrast joints make the finish read as plain installed VOX panels.
    seams = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    seam_draw = ImageDraw.Draw(seams)
    vanishing_point = (580, 193)
    for top_x in (124, 275, 430, 585, 740, 910):
        seam_draw.line(
            [vanishing_point, (top_x, 0)],
            fill=(137, 135, 130, 78),
            width=1,
        )
    panels = Image.alpha_composite(panels, seams).convert("RGB")
    panel_array = np.asarray(panels).astype(np.float32)

    # Rebuild the original warm LED/downlight glow over the new smooth surface.
    ceiling_area = mask > 0.05
    light_core = np.uint8(((luminance > 168.0) & ceiling_area) * 255)
    halo = Image.fromarray(light_core, "L").filter(ImageFilter.MaxFilter(7))
    halo = np.asarray(halo.filter(ImageFilter.GaussianBlur(7.0)), dtype=np.float32) / 255.0
    warm_light = np.array((255, 214, 159), dtype=np.float32)
    panel_array = panel_array * (1.0 - halo[..., None] * 0.28) + warm_light * halo[..., None] * 0.28

    # Preserve the luminous cores and trim of the existing installed fixtures.
    fixture_alpha = smoothstep(182.0, 242.0, luminance) * mask
    panel_array = (
        panel_array * (1.0 - fixture_alpha[..., None])
        + pixels * fixture_alpha[..., None]
    )

    edge_mask = Image.fromarray(np.uint8(np.clip(mask * 255.0, 0, 255)), "L")
    edge_mask = edge_mask.filter(ImageFilter.GaussianBlur(0.65))
    alpha = np.asarray(edge_mask, dtype=np.float32) / 255.0
    result = pixels * (1.0 - alpha[..., None]) + panel_array * alpha[..., None]

    # Restore only actual neutral-coloured fan pixels, not the brown ceiling behind it.
    gross_fan = np.asarray(fan_fixture_mask((width, height)), dtype=np.float32) / 255.0
    chroma = pixels.max(axis=2) - pixels.min(axis=2)
    fan_pixels = np.uint8(
        ((gross_fan > 0.08) & (luminance > 82.0) & (chroma < 78.0)) * 255
    )
    precise_fan = Image.fromarray(fan_pixels, "L").filter(ImageFilter.GaussianBlur(0.45))
    fan_alpha = np.asarray(precise_fan, dtype=np.float32) / 255.0
    result = result * (1.0 - fan_alpha[..., None]) + pixels * fan_alpha[..., None]
    return Image.fromarray(np.uint8(np.clip(result + 0.5, 0, 255)), "RGB")


def main():
    source = Image.open(SOURCE).convert("RGB")
    for name, colour in COLOURS.items():
        output = ROOT / f"bedroom-ceiling-{name}.png"
        recolour_ceiling(source, colour).save(output, optimize=True)
        print(f"Created {output.name}: {source.width}x{source.height}")

    vox_output = ROOT / "bedroom-ceiling-plain-off-white-vox.png"
    create_plain_off_white_vox_ceiling(source).save(vox_output, optimize=True)
    print(f"Created {vox_output.name}: {source.width}x{source.height}")


if __name__ == "__main__":
    main()
