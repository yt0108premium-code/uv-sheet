# UV Sheet Design Renders

Supplied room renders par UV-sheet options aur ceiling concepts apply kiye gaye hain. All generated images, references and reproducible Pillow scripts are included.

## Latest — Bedroom redesign

Bedroom ki visible walls par **UV Sheet CODE 2712** apply ki gayi hai. Wooden slat ceiling ko warm-white panel ceiling se replace karke perspective seams, six recessed warm downlights aur perimeter cove lighting add ki gayi hai.

![Bedroom with white panel ceiling and CODE 2712 walls](bedroom-white-ceiling-code-2712.png)

### Bedroom before / after

![Bedroom redesign comparison](bedroom-before-after.png)

## Living room — UV Sheet CODE 2712

![Living room with UV Sheet CODE 2712](edited-uv-sheet-code-2712.png)

![Living-room CODE 2712 comparison](code-2712-before-after.png)

### CODE 2712 reference

| Supplied screenshot | Extracted pattern |
|---|---|
| ![CODE 2712 screenshot](code-2712-reference.png) | ![Extracted CODE 2712 pattern](code-2712-pattern-crop.png) |

## Previous beige/brown version

![Previous beige UV sheet render](edited-uv-sheet-warm-cream.png)

![Previous before and after comparison](before-after-comparison.png)

## Source renders

- `bedroom-source.png`
- `source-interior.png`
- `reference-stone.png`

## Recreate the edits

```bash
python -m pip install -r requirements.txt
python create_bedroom_code_2712_edit.py
python create_code_2712_edit.py
python create_uv_sheet_edit.py
```

Latest bedroom outputs:
- `bedroom-white-ceiling-code-2712.png`
- `bedroom-before-after.png`
