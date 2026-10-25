# UV Sheet Design Renders

## Bedroom ceiling panel colour samples

Attached bedroom image ki **sirf ceiling panels** recolour ki gayi hain. Fan, lights, walls, wardrobe, bed, floor aur baaki interior original rakhe gaye hain. Har option ek separate 1024×576 image hai; koi merged comparison image nahi banayi gayi.

**Best overall choices:** warm ivory room ko bright aur premium banata hai; ash grey balanced modern option hai; walnut existing wall panels ke saath sabse naturally match karta hai.

### Plain off-white VOX panel — new sample

Smooth off-white VOX finish with broad, subtle panel joints. Original dark wood grooves remove kiye gaye hain; fan aur warm ceiling lights retain kiye gaye hain.

![Bedroom ceiling with plain off-white VOX panels](bedroom-ceiling-plain-off-white-vox.png)

### 1. Warm ivory — light

![Bedroom ceiling in warm ivory](bedroom-ceiling-warm-ivory.png)

### 2. Natural oak — light

![Bedroom ceiling in natural oak](bedroom-ceiling-natural-oak.png)

### 3. Ash grey — light neutral

![Bedroom ceiling in ash grey](bedroom-ceiling-ash-grey.png)

### 4. Sage grey — medium

![Bedroom ceiling in sage grey](bedroom-ceiling-sage-grey.png)

### 5. Walnut — dark warm

![Bedroom ceiling in walnut](bedroom-ceiling-walnut.png)

### 6. Graphite — dark neutral

![Bedroom ceiling in graphite](bedroom-ceiling-graphite.png)

### 7. Midnight blue — dark cool

![Bedroom ceiling in midnight blue](bedroom-ceiling-midnight-blue.png)

### Bedroom source

![Original supplied bedroom](bedroom-ceiling-source.jpg)

### Recreate the bedroom ceiling samples

```bash
python -m pip install -r requirements.txt
python create_bedroom_ceiling_colours.py
```

## Previous UV sheet renders

Living-room render ke UV-sheet areas par supplied product references apply kiye gaye hain. Ceiling strip lights aur spotlights ko warm cream tone diya gaya hai.

## Latest result — UV Sheet CODE 2712

![Room render with UV Sheet CODE 2712](edited-uv-sheet-code-2712.png)

### Before / after

![CODE 2712 before and after comparison](code-2712-before-after.png)

### CODE 2712 reference

| Supplied screenshot | Extracted pattern |
|---|---|
| ![CODE 2712 screenshot](code-2712-reference.png) | ![Extracted CODE 2712 pattern](code-2712-pattern-crop.png) |

## Previous beige/brown version

![Previous beige UV sheet render](edited-uv-sheet-warm-cream.png)

![Previous before and after comparison](before-after-comparison.png)

## Source files

| Original room | Beige stone reference |
|---|---|
| ![Original room render](source-interior.png) | ![Beige stone reference](reference-stone.png) |

## Recreate the edits

```bash
python -m pip install -r requirements.txt
python create_code_2712_edit.py
python create_uv_sheet_edit.py
```

Generated CODE 2712 files:
- `edited-uv-sheet-code-2712.png`
- `code-2712-before-after.png`
- `code-2712-pattern-crop.png`
