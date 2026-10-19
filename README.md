# UV Sheet Colour Edit

Living-room render mein marble UV sheet ko supplied beige/brown stone reference ke colour palette mein update kiya gaya hai. Ceiling strip lights aur spotlights ko warm cream tone diya gaya hai.

## Final result

![Edited UV sheet with warm cream lighting](edited-uv-sheet-warm-cream.png)

## Before / after

![Before and after comparison](before-after-comparison.png)

## Supplied files

| Original render | Stone colour reference |
|---|---|
| ![Original render](source-interior.png) | ![Stone reference](reference-stone.png) |

## Recreate the edit

```bash
python -m pip install -r requirements.txt
python create_uv_sheet_edit.py
```

The script generates:
- `edited-uv-sheet-warm-cream.png`
- `before-after-comparison.png`
