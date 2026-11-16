import { useEffect, useRef, useState } from 'react';
import type { PdfJsDocument } from '../services/pdf';
import type { Annotation, EditorPage, Point, Tool } from '../types/editor';

interface Props {
  pdf: PdfJsDocument;
  page: EditorPage;
  annotations: Annotation[];
  selectedId: string | null;
  tool: Tool;
  zoom: number;
  pendingImage: string | null;
  onSelect: (id: string | null) => void;
  onCreate: (annotation: Annotation) => void;
  onUpdate: (id: string, patch: Partial<Annotation>) => void;
  onImagePlaced: () => void;
}

const defaultColor: Record<string, string> = {
  highlight: '#ffd633', redact: '#000000', signature: '#173c8c', draw: '#d11f36', text: '#18202b', rectangle: '#2563eb', ellipse: '#2563eb', image: '#ffffff',
};

function id() { return crypto.randomUUID(); }
function clamp(value: number, min = 0, max = 1) { return Math.max(min, Math.min(max, value)); }

export default function PageCanvas(props: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const overlayRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 700, height: 990 });
  const [draft, setDraft] = useState<Annotation | null>(null);
  const [preview, setPreview] = useState<Annotation | null>(null);
  const startRef = useRef<Point | null>(null);
  const editRef = useRef<{ annotation: Annotation; start: Point; resize: boolean } | null>(null);

  useEffect(() => {
    let cancelled = false;
    let renderTask: { cancel: () => void; promise: Promise<void> } | undefined;
    void props.pdf.getPage(props.page.sourceIndex + 1).then((pdfPage) => {
      if (cancelled || !canvasRef.current) return;
      const viewport = pdfPage.getViewport({ scale: 1.25 * props.zoom, rotation: (pdfPage.rotate + props.page.rotation) % 360 });
      const canvas = canvasRef.current;
      canvas.width = Math.floor(viewport.width);
      canvas.height = Math.floor(viewport.height);
      canvas.style.width = `${viewport.width}px`;
      canvas.style.height = `${viewport.height}px`;
      setDimensions({ width: viewport.width, height: viewport.height });
      renderTask = pdfPage.render({ canvas, canvasContext: canvas.getContext('2d')!, viewport });
      return renderTask.promise;
    }).catch(() => undefined);
    return () => { cancelled = true; renderTask?.cancel(); };
  }, [props.pdf, props.page.sourceIndex, props.page.rotation, props.zoom]);

  const pointFromEvent = (event: React.PointerEvent): Point => {
    const rect = overlayRef.current!.getBoundingClientRect();
    return { x: clamp((event.clientX - rect.left) / rect.width), y: clamp((event.clientY - rect.top) / rect.height) };
  };

  const beginEdit = (event: React.PointerEvent, annotation: Annotation, resize = false) => {
    event.stopPropagation();
    props.onSelect(annotation.id);
    if (props.tool !== 'select') return;
    const start = pointFromEvent(event);
    editRef.current = { annotation, start, resize };
    setPreview(annotation);
    overlayRef.current?.setPointerCapture(event.pointerId);
  };

  const pointerDown = (event: React.PointerEvent) => {
    if (event.button !== 0) return;
    if (props.tool === 'select') { props.onSelect(null); return; }
    const start = pointFromEvent(event);
    startRef.current = start;
    overlayRef.current?.setPointerCapture(event.pointerId);
    if (props.tool === 'text') {
      const annotation: Annotation = { id: id(), pageId: props.page.id, type: 'text', x: start.x, y: start.y, width: 0.3, height: 0.075, color: defaultColor.text, opacity: 1, strokeWidth: 1, fontSize: 16, text: 'Type here' };
      props.onCreate(annotation); props.onSelect(annotation.id); startRef.current = null;
    } else if (props.tool === 'image' && props.pendingImage) {
      const annotation: Annotation = { id: id(), pageId: props.page.id, type: 'image', x: start.x, y: start.y, width: 0.28, height: 0.2, color: '#ffffff', opacity: 1, strokeWidth: 0, dataUrl: props.pendingImage };
      props.onCreate(annotation); props.onSelect(annotation.id); props.onImagePlaced(); startRef.current = null;
    } else {
      const annotation: Annotation = {
        id: id(), pageId: props.page.id, type: props.tool as Annotation['type'], x: start.x, y: start.y, width: 0, height: 0,
        color: defaultColor[props.tool] ?? '#2563eb', opacity: props.tool === 'highlight' ? 0.42 : 1,
        strokeWidth: props.tool === 'signature' ? 3 : 2, points: ['draw', 'signature'].includes(props.tool) ? [start] : undefined,
      };
      setDraft(annotation);
    }
  };

  const pointerMove = (event: React.PointerEvent) => {
    if (editRef.current) {
      const current = pointFromEvent(event);
      const { annotation, start, resize } = editRef.current;
      const dx = current.x - start.x; const dy = current.y - start.y;
      if (resize && !['draw', 'signature'].includes(annotation.type)) {
        setPreview({ ...annotation, width: clamp(annotation.width + dx, 0.01, 1 - annotation.x), height: clamp(annotation.height + dy, 0.01, 1 - annotation.y) });
      } else if (annotation.type === 'draw' || annotation.type === 'signature') {
        setPreview({ ...annotation, points: annotation.points?.map((point) => ({ x: clamp(point.x + dx), y: clamp(point.y + dy) })) });
      } else {
        setPreview({ ...annotation, x: clamp(annotation.x + dx, 0, 1 - annotation.width), y: clamp(annotation.y + dy, 0, 1 - annotation.height) });
      }
      return;
    }
    if (!draft || !startRef.current) return;
    const current = pointFromEvent(event);
    if (draft.type === 'draw' || draft.type === 'signature') {
      setDraft({ ...draft, points: [...(draft.points ?? []), current] });
    } else {
      setDraft({ ...draft, x: Math.min(startRef.current.x, current.x), y: Math.min(startRef.current.y, current.y), width: Math.abs(current.x - startRef.current.x), height: Math.abs(current.y - startRef.current.y) });
    }
  };

  const pointerUp = () => {
    if (editRef.current && preview) {
      const original = editRef.current.annotation;
      const patch = original.type === 'draw' || original.type === 'signature'
        ? { points: preview.points }
        : { x: preview.x, y: preview.y, width: preview.width, height: preview.height };
      props.onUpdate(original.id, patch);
      editRef.current = null; setPreview(null);
      return;
    }
    if (!draft) return;
    const valid = draft.type === 'draw' || draft.type === 'signature' ? (draft.points?.length ?? 0) > 1 : draft.width > 0.005 && draft.height > 0.005;
    if (valid) { props.onCreate(draft); props.onSelect(draft.id); }
    setDraft(null); startRef.current = null;
  };

  const rendered = [
    ...props.annotations.map((annotation) => preview?.id === annotation.id ? preview : annotation),
    ...(draft ? [draft] : []),
  ];
  return (
    <div className="page-stage" style={{ width: dimensions.width, height: dimensions.height }}>
      <canvas ref={canvasRef} className="pdf-canvas" />
      <div ref={overlayRef} className={`annotation-layer tool-${props.tool}`} onPointerDown={pointerDown} onPointerMove={pointerMove} onPointerUp={pointerUp} onPointerCancel={pointerUp}>
        {rendered.map((annotation) => {
          const selected = annotation.id === props.selectedId;
          if (annotation.type === 'draw' || annotation.type === 'signature') {
            const points = annotation.points ?? [];
            const d = points.map((point, index) => `${index ? 'L' : 'M'} ${point.x * dimensions.width} ${point.y * dimensions.height}`).join(' ');
            return <svg key={annotation.id} className={`ink-annotation ${selected ? 'selected' : ''}`} onPointerDown={(event) => beginEdit(event, annotation)}><path d={d} fill="none" stroke={annotation.color} strokeWidth={annotation.strokeWidth * 1.25 * props.zoom} opacity={annotation.opacity} strokeLinecap="round" strokeLinejoin="round" /></svg>;
          }
          const style: React.CSSProperties = { left: `${annotation.x * 100}%`, top: `${annotation.y * 100}%`, width: `${annotation.width * 100}%`, height: `${annotation.height * 100}%`, opacity: annotation.opacity };
          return (
            <div key={annotation.id} className={`annotation annotation-${annotation.type} ${selected ? 'selected' : ''}`} style={style} onPointerDown={(event) => beginEdit(event, annotation)}>
              {annotation.type === 'text' && <span style={{ color: annotation.color, fontSize: `${(annotation.fontSize ?? 16) * 1.25 * props.zoom}px` }}>{annotation.text}</span>}
              {annotation.type === 'highlight' && <span style={{ background: annotation.color }} />}
              {annotation.type === 'redact' && <span />}
              {annotation.type === 'rectangle' && <span style={{ borderColor: annotation.color, borderWidth: annotation.strokeWidth * 1.25 * props.zoom }} />}
              {annotation.type === 'ellipse' && <span style={{ borderColor: annotation.color, borderWidth: annotation.strokeWidth * 1.25 * props.zoom }} />}
              {annotation.type === 'image' && <img src={annotation.dataUrl} alt="Inserted" />}
              {selected && !['draw', 'signature'].includes(annotation.type) && <i className="resize-handle" onPointerDown={(event) => beginEdit(event, annotation, true)} />}
            </div>
          );
        })}
      </div>
    </div>
  );
}
