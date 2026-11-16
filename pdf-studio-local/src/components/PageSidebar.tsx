import { useEffect, useRef } from 'react';
import { Copy, FilePlus, GripVertical, RotateCw, Trash2 } from 'lucide-react';
import type { PdfJsDocument } from '../services/pdf';
import type { EditorPage } from '../types/editor';

function Thumbnail({ pdf, page, active, number, onClick }: { pdf: PdfJsDocument; page: EditorPage; active: boolean; number: number; onClick: () => void }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    let cancelled = false;
    let task: { cancel: () => void; promise: Promise<void> } | undefined;
    void pdf.getPage(page.sourceIndex + 1).then((pdfPage) => {
      if (cancelled || !canvasRef.current) return;
      const rotation = (pdfPage.rotate + page.rotation) % 360;
      const viewport = pdfPage.getViewport({ scale: 0.19, rotation });
      const canvas = canvasRef.current;
      canvas.width = viewport.width;
      canvas.height = viewport.height;
      task = pdfPage.render({ canvas, canvasContext: canvas.getContext('2d')!, viewport });
      return task.promise;
    }).catch(() => undefined);
    return () => { cancelled = true; task?.cancel(); };
  }, [pdf, page.sourceIndex, page.rotation]);

  return (
    <button className={`thumbnail ${active ? 'active' : ''}`} onClick={onClick}>
      <GripVertical className="drag-grip" size={14} />
      <canvas ref={canvasRef} />
      <span>{number}</span>
    </button>
  );
}

interface SidebarProps {
  pdf: PdfJsDocument;
  pages: EditorPage[];
  activePageId: string;
  onActive: (id: string) => void;
  onReorder: (from: number, to: number) => void;
  onRotate: () => void;
  onDelete: () => void;
  onDuplicate: () => void;
  onAddBlank: () => void;
}

export default function PageSidebar(props: SidebarProps) {
  const dragged = useRef<number | null>(null);
  return (
    <aside className="page-sidebar">
      <div className="panel-heading"><div><strong>Pages</strong><span>{props.pages.length}</span></div><button title="Add blank page" onClick={props.onAddBlank}><FilePlus size={17} /></button></div>
      <div className="page-list">
        {props.pages.map((page, index) => (
          <div key={page.id} draggable onDragStart={() => { dragged.current = index; }} onDragOver={(event) => event.preventDefault()} onDrop={() => {
            if (dragged.current !== null && dragged.current !== index) props.onReorder(dragged.current, index);
            dragged.current = null;
          }}>
            <Thumbnail pdf={props.pdf} page={page} number={index + 1} active={page.id === props.activePageId} onClick={() => props.onActive(page.id)} />
          </div>
        ))}
      </div>
      <div className="page-actions">
        <button onClick={props.onRotate} title="Rotate page"><RotateCw size={17} /></button>
        <button onClick={props.onDuplicate} title="Duplicate page"><Copy size={17} /></button>
        <button onClick={props.onDelete} title="Delete page" className="danger"><Trash2 size={17} /></button>
      </div>
    </aside>
  );
}
