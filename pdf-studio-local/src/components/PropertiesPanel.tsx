import { Info, LockKeyhole, Trash2 } from 'lucide-react';
import type { Annotation, DocumentMetadata } from '../types/editor';

interface Props {
  annotation?: Annotation;
  metadata: DocumentMetadata;
  password: string;
  onPassword: (password: string) => void;
  onAnnotation: (patch: Partial<Annotation>) => void;
  onDelete: () => void;
  onMetadata: (metadata: DocumentMetadata) => void;
}

export default function PropertiesPanel({ annotation, metadata, password, onPassword, onAnnotation, onDelete, onMetadata }: Props) {
  return (
    <aside className="properties-panel">
      <div className="panel-heading"><div><strong>{annotation ? 'Properties' : 'Document'}</strong></div></div>
      {annotation ? (
        <div className="properties-content">
          <div className="selection-type">{annotation.type}</div>
          {annotation.type === 'text' && (
            <label>Text<textarea value={annotation.text ?? ''} onChange={(event) => onAnnotation({ text: event.target.value })} rows={5} /></label>
          )}
          <div className="field-row">
            <label>Color<input type="color" value={annotation.color} onChange={(event) => onAnnotation({ color: event.target.value })} /></label>
            {annotation.type === 'text' && <label>Size<input type="number" min="7" max="96" value={annotation.fontSize ?? 16} onChange={(event) => onAnnotation({ fontSize: Number(event.target.value) })} /></label>}
          </div>
          <label>Opacity <span>{Math.round(annotation.opacity * 100)}%</span><input type="range" min="0.05" max="1" step="0.05" value={annotation.opacity} onChange={(event) => onAnnotation({ opacity: Number(event.target.value) })} /></label>
          {['draw', 'signature', 'rectangle', 'ellipse'].includes(annotation.type) && (
            <label>Line width <span>{annotation.strokeWidth}px</span><input type="range" min="1" max="12" value={annotation.strokeWidth} onChange={(event) => onAnnotation({ strokeWidth: Number(event.target.value) })} /></label>
          )}
          {!['draw', 'signature'].includes(annotation.type) && <>
            <label>Width <span>{Math.round(annotation.width * 100)}%</span><input type="range" min="0.02" max="0.9" step="0.01" value={annotation.width} onChange={(event) => onAnnotation({ width: Number(event.target.value) })} /></label>
            <label>Height <span>{Math.round(annotation.height * 100)}%</span><input type="range" min="0.02" max="0.9" step="0.01" value={annotation.height} onChange={(event) => onAnnotation({ height: Number(event.target.value) })} /></label>
          </>}
          <button className="delete-selection" onClick={onDelete}><Trash2 size={16} /> Delete selection</button>
        </div>
      ) : (
        <div className="properties-content">
          <div className="privacy-note"><Info size={17} /><span>Your files never leave this computer.</span></div>
          <label>Title<input value={metadata.title} onChange={(event) => onMetadata({ ...metadata, title: event.target.value })} /></label>
          <label>Author<input value={metadata.author} onChange={(event) => onMetadata({ ...metadata, author: event.target.value })} /></label>
          <label>Subject<textarea rows={3} value={metadata.subject} onChange={(event) => onMetadata({ ...metadata, subject: event.target.value })} /></label>
          <label>Keywords<input placeholder="invoice, approved" value={metadata.keywords} onChange={(event) => onMetadata({ ...metadata, keywords: event.target.value })} /></label>
          <label><span className="label-icon"><LockKeyhole size={13} /> Open password (optional)</span><input type="password" autoComplete="new-password" placeholder="AES-256 protection" value={password} onChange={(event) => onPassword(event.target.value)} /></label>
          <hr />
          <div className="format-note"><strong>Secure redaction</strong><p>Cover sensitive content with Redact, then add replacement text if needed. Export flattens every redacted page so covered text cannot be searched or recovered. Text search is unavailable on those flattened pages.</p></div>
        </div>
      )}
    </aside>
  );
}
