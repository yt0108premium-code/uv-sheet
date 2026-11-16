# PDF Studio Local

A private, offline PDF editor for Windows 11. Documents stay on the computer and are never uploaded.

## Windows app

Build the portable x64 executable on Windows with `npm run dist:portable`. The generated file is written to:

```text
release/PDF-Studio-Local-Windows-1.0.0.exe
```

Build artifacts are intentionally excluded from Git history. The portable app runs without installation.

## Features

- Open and render local PDFs
- Add English and Hindi/Devanagari text
- Highlight, rectangles, ellipses, freehand ink, and signatures
- Insert PNG and JPEG images
- Move, resize, recolor, and change annotation opacity
- Secure redaction by flattening affected pages during export
- Rotate, reorder, duplicate, and delete pages
- Add blank A4 pages and merge multiple PDFs
- Edit title, author, subject, and keywords
- Optional AES-256 open-password protection
- Undo/redo and keyboard shortcuts
- Save a collision-safe `*-edited.pdf` copy directly to Desktop
- Save As to a custom path

## Important behavior

- The original file is never overwritten by **Save to Desktop**.
- Redacted pages are flattened to remove covered content. Original searchable text is therefore unavailable on those pages.
- Existing PDF text is replaced safely by redacting the old area and placing new text. Arbitrary paragraph reflow like Microsoft Word is not supported by the PDF format.
- Existing digital signatures are not preserved after editing because changing a signed PDF invalidates its signature.
- The provided executable is unsigned. Windows SmartScreen may show an “Unknown publisher” warning until the app is signed with a trusted code-signing certificate.

## Keyboard shortcuts

- `Ctrl+O`: Open PDF
- `Ctrl+S`: Save a new edited copy to Desktop
- `Ctrl+Shift+S`: Save As
- `Ctrl+Z`: Undo
- `Ctrl+Y` or `Ctrl+Shift+Z`: Redo
- `Delete`: Delete selected annotation

## Development

```bash
npm install
npm run dev
npm run typecheck
npm run build
```

On Windows, build an installer with:

```bash
npm run dist:win
```

Build a portable executable with:

```bash
npm run dist:portable
```

Build output is written to `release/`.
