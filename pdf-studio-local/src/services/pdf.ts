import 'regenerator-runtime/runtime.js';
import fontkit from '@pdf-lib/fontkit';
import * as pdfLib from 'pdf-lib';
import { PDFDocument, type PDFPage, type PDFFont, degrees, rgb } from 'pdf-lib';
import { configure, lock } from 'pdf-lib-encrypt';
import * as pdfjsLib from 'pdfjs-dist';
import workerUrl from 'pdfjs-dist/build/pdf.worker.min.mjs?url';
import devanagariFontUrl from '@fontsource/noto-sans-devanagari/files/noto-sans-devanagari-devanagari-400-normal.woff?url';
import latinFontUrl from '@fontsource/noto-sans-devanagari/files/noto-sans-devanagari-latin-ext-400-normal.woff?url';
import type { Annotation, DocumentMetadata, EditorPage, Point } from '../types/editor';

pdfjsLib.GlobalWorkerOptions.workerSrc = workerUrl;
configure(pdfLib);

export async function protectPdf(bytes: Uint8Array, password: string) {
  return password ? lock(bytes, password) : bytes;
}

export type PdfJsDocument = Awaited<ReturnType<typeof pdfjsLib.getDocument>['promise']>;
type PageBox = { x: number; y: number; width: number; height: number };

export async function loadPdfForViewing(bytes: Uint8Array) {
  return pdfjsLib.getDocument({ data: bytes.slice() }).promise;
}

export async function getPdfInfo(bytes: Uint8Array) {
  const doc = await PDFDocument.load(bytes, { updateMetadata: false });
  return {
    pageCount: doc.getPageCount(),
    metadata: {
      title: doc.getTitle() ?? '', author: doc.getAuthor() ?? '', subject: doc.getSubject() ?? '', keywords: doc.getKeywords() ?? '',
    },
  };
}

export async function mergePdfs(base: Uint8Array, additions: Uint8Array[]) {
  const destination = await PDFDocument.load(base);
  let added = 0;
  for (const bytes of additions) {
    const source = await PDFDocument.load(bytes);
    const copied = await destination.copyPages(source, source.getPageIndices());
    copied.forEach((page) => destination.addPage(page));
    added += copied.length;
  }
  return { bytes: await destination.save(), added };
}

export async function appendBlankPage(base: Uint8Array) {
  const doc = await PDFDocument.load(base);
  doc.addPage([595.28, 841.89]);
  return doc.save();
}

function hexToRgb(hex: string) {
  const clean = hex.replace('#', '');
  const value = Number.parseInt(clean.length === 3 ? clean.split('').map((c) => c + c).join('') : clean, 16);
  return rgb(((value >> 16) & 255) / 255, ((value >> 8) & 255) / 255, (value & 255) / 255);
}

function displayPointToPdf(point: Point, box: PageBox, rotation: number) {
  const r = ((rotation % 360) + 360) % 360;
  if (r === 90) return { x: box.x + point.y * box.width, y: box.y + point.x * box.height };
  if (r === 180) return { x: box.x + (1 - point.x) * box.width, y: box.y + point.y * box.height };
  if (r === 270) return { x: box.x + (1 - point.y) * box.width, y: box.y + (1 - point.x) * box.height };
  return { x: box.x + point.x * box.width, y: box.y + (1 - point.y) * box.height };
}

function normalizedRect(annotation: Annotation, box: PageBox, rotation: number) {
  const corners = [
    { x: annotation.x, y: annotation.y }, { x: annotation.x + annotation.width, y: annotation.y },
    { x: annotation.x, y: annotation.y + annotation.height }, { x: annotation.x + annotation.width, y: annotation.y + annotation.height },
  ].map((point) => displayPointToPdf(point, box, rotation));
  const xs = corners.map((point) => point.x); const ys = corners.map((point) => point.y);
  const x = Math.min(...xs); const y = Math.min(...ys);
  return { x, y, width: Math.max(...xs) - x, height: Math.max(...ys) - y };
}

async function dataUrlBytes(dataUrl: string) {
  const encoded = dataUrl.split(',')[1];
  return Uint8Array.from(atob(encoded), (character) => character.charCodeAt(0));
}

async function embedDataImage(doc: PDFDocument, dataUrl: string) {
  const bytes = await dataUrlBytes(dataUrl);
  return dataUrl.startsWith('data:image/png') ? doc.embedPng(bytes) : doc.embedJpg(bytes);
}

async function fetchFont(url: string) {
  const response = await fetch(url);
  if (!response.ok) throw new Error('Bundled Unicode font could not be loaded.');
  return response.arrayBuffer();
}

function textRuns(text: string) {
  const runs: Array<{ text: string; devanagari: boolean }> = [];
  for (const character of text) {
    const devanagari = /[\u0900-\u097f]/u.test(character);
    const previous = runs[runs.length - 1];
    if (previous && previous.devanagari === devanagari) previous.text += character;
    else runs.push({ text: character, devanagari });
  }
  return runs;
}

function drawMixedText(page: PDFPage, value: string, x: number, y: number, size: number, maxWidth: number, color: ReturnType<typeof rgb>, opacity: number, latinFont: PDFFont, devanagariFont: PDFFont) {
  let cursorX = x;
  let cursorY = y;
  const lineHeight = size * 1.25;
  for (const line of value.split('\n')) {
    for (const run of textRuns(line)) {
      const font = run.devanagari ? devanagariFont : latinFont;
      const runWidth = font.widthOfTextAtSize(run.text, size);
      if (cursorX > x && cursorX + runWidth > x + maxWidth) { cursorX = x; cursorY -= lineHeight; }
      page.drawText(run.text, { x: cursorX, y: cursorY, size, font, color, opacity });
      cursorX += runWidth;
    }
    cursorX = x;
    cursorY -= lineHeight;
  }
}

async function rasterizeVisiblePage(viewer: PdfJsDocument, model: EditorPage, redactions: Annotation[]) {
  const sourcePage = await viewer.getPage(model.sourceIndex + 1);
  const rotation = (sourcePage.rotate + model.rotation + 360) % 360;
  const viewport = sourcePage.getViewport({ scale: 2, rotation });
  const canvas = document.createElement('canvas');
  canvas.width = Math.ceil(viewport.width); canvas.height = Math.ceil(viewport.height);
  const context = canvas.getContext('2d', { alpha: false });
  if (!context) throw new Error('Canvas rendering is unavailable.');
  await sourcePage.render({ canvas, canvasContext: context, viewport }).promise;
  context.fillStyle = '#000000';
  for (const redaction of redactions) {
    context.fillRect(redaction.x * canvas.width, redaction.y * canvas.height, redaction.width * canvas.width, redaction.height * canvas.height);
  }
  return { dataUrl: canvas.toDataURL('image/png'), width: viewport.width / 2, height: viewport.height / 2 };
}

export async function exportPdf(sourceBytes: Uint8Array, pages: EditorPage[], annotations: Annotation[], metadata: DocumentMetadata) {
  const source = await PDFDocument.load(sourceBytes);
  const output = await PDFDocument.create();
  output.registerFontkit(fontkit);
  const [latinBytes, devanagariBytes] = await Promise.all([fetchFont(latinFontUrl), fetchFont(devanagariFontUrl)]);
  const [latinFont, devanagariFont] = await Promise.all([
    output.embedFont(latinBytes, { subset: true }), output.embedFont(devanagariBytes, { subset: true }),
  ]);
  const needsRaster = pages.some((model) => {
    const pageAnnotations = annotations.filter((item) => item.pageId === model.id);
    const rotation = (source.getPage(model.sourceIndex).getRotation().angle + model.rotation + 360) % 360;
    return pageAnnotations.some((item) => item.type === 'redact') || (pageAnnotations.length > 0 && rotation !== 0);
  });
  const viewer = needsRaster ? await loadPdfForViewing(sourceBytes) : null;
  const pageGeometry: Array<{ box: PageBox; rotation: number; rasterized: boolean }> = [];

  try {
    for (const model of pages) {
      const pageAnnotations = annotations.filter((item) => item.pageId === model.id);
      const sourcePage = source.getPage(model.sourceIndex);
      const rotation = (sourcePage.getRotation().angle + model.rotation + 360) % 360;
      const rasterized = pageAnnotations.some((item) => item.type === 'redact') || (pageAnnotations.length > 0 && rotation !== 0);
      if (rasterized) {
        const flattened = await rasterizeVisiblePage(viewer!, model, pageAnnotations.filter((item) => item.type === 'redact'));
        const page = output.addPage([flattened.width, flattened.height]);
        const image = await output.embedPng(await dataUrlBytes(flattened.dataUrl));
        page.drawImage(image, { x: 0, y: 0, width: flattened.width, height: flattened.height });
        pageGeometry.push({ box: { x: 0, y: 0, width: flattened.width, height: flattened.height }, rotation: 0, rasterized: true });
      } else {
        const [copied] = await output.copyPages(source, [model.sourceIndex]);
        copied.setRotation(degrees(rotation));
        output.addPage(copied);
        pageGeometry.push({ box: copied.getCropBox(), rotation, rasterized: false });
      }
    }
  } finally {
    await viewer?.cleanup();
  }

  if (metadata.title) output.setTitle(metadata.title);
  if (metadata.author) output.setAuthor(metadata.author);
  if (metadata.subject) output.setSubject(metadata.subject);
  if (metadata.keywords) output.setKeywords(metadata.keywords.split(',').map((item) => item.trim()).filter(Boolean));
  output.setProducer('PDF Studio Local'); output.setModificationDate(new Date());

  for (let outputIndex = 0; outputIndex < pages.length; outputIndex += 1) {
    const model = pages[outputIndex]; const page = output.getPage(outputIndex); const geometry = pageGeometry[outputIndex];
    for (const annotation of annotations.filter((item) => item.pageId === model.id && item.type !== 'redact')) {
      const color = hexToRgb(annotation.color); const rect = normalizedRect(annotation, geometry.box, geometry.rotation);
      const opacity = Math.max(0.05, Math.min(1, annotation.opacity));
      if (annotation.type === 'text') {
        const fontSize = annotation.fontSize ?? 16;
        drawMixedText(page, annotation.text || 'Text', rect.x, rect.y + Math.max(0, rect.height - fontSize), fontSize, Math.max(20, rect.width), color, opacity, latinFont, devanagariFont);
      } else if (annotation.type === 'highlight') {
        page.drawRectangle({ ...rect, color, opacity: Math.min(0.65, opacity), borderWidth: 0 });
      } else if (annotation.type === 'rectangle') {
        page.drawRectangle({ ...rect, borderColor: color, borderWidth: annotation.strokeWidth, borderOpacity: opacity });
      } else if (annotation.type === 'ellipse') {
        page.drawEllipse({ x: rect.x + rect.width / 2, y: rect.y + rect.height / 2, xScale: rect.width / 2, yScale: rect.height / 2, borderColor: color, borderWidth: annotation.strokeWidth, borderOpacity: opacity });
      } else if ((annotation.type === 'draw' || annotation.type === 'signature') && annotation.points?.length) {
        for (let index = 1; index < annotation.points.length; index += 1) {
          page.drawLine({ start: displayPointToPdf(annotation.points[index - 1], geometry.box, geometry.rotation), end: displayPointToPdf(annotation.points[index], geometry.box, geometry.rotation), color, thickness: annotation.strokeWidth, opacity });
        }
      } else if (annotation.type === 'image' && annotation.dataUrl) {
        const image = await embedDataImage(output, annotation.dataUrl);
        page.drawImage(image, { ...rect, opacity });
      }
    }
  }
  return output.save();
}
