import {
  Circle, Download, Eraser, FilePlus2, FolderOpen, Highlighter, ImagePlus, Menu,
  MousePointer2, PenLine, Redo2, Save, Square, Type, Undo2, UserRoundPen, ZoomIn, ZoomOut,
} from 'lucide-react';
import type { Tool } from '../types/editor';

interface ToolbarProps {
  tool: Tool;
  zoom: number;
  canUndo: boolean;
  canRedo: boolean;
  busy: boolean;
  onTool: (tool: Tool) => void;
  onOpen: () => void;
  onMerge: () => void;
  onSave: () => void;
  onSaveAs: () => void;
  onUndo: () => void;
  onRedo: () => void;
  onZoom: (zoom: number) => void;
}

const tools: Array<{ id: Tool; label: string; icon: typeof MousePointer2 }> = [
  { id: 'select', label: 'Select', icon: MousePointer2 },
  { id: 'text', label: 'Add text', icon: Type },
  { id: 'highlight', label: 'Highlight', icon: Highlighter },
  { id: 'redact', label: 'Redact', icon: Eraser },
  { id: 'rectangle', label: 'Rectangle', icon: Square },
  { id: 'ellipse', label: 'Ellipse', icon: Circle },
  { id: 'draw', label: 'Draw', icon: PenLine },
  { id: 'signature', label: 'Sign', icon: UserRoundPen },
];

export default function Toolbar(props: ToolbarProps) {
  return (
    <header className="toolbar">
      <div className="brand"><span className="brand-mark">P</span><span>PDF Studio <b>Local</b></span></div>
      <div className="toolbar-divider" />
      <button className="action-button primary" disabled={props.busy} onClick={props.onOpen} title="Open PDF (Ctrl+O)"><FolderOpen size={17} /> Open</button>
      <button className="icon-button" disabled={props.busy} onClick={props.onMerge} title="Merge PDFs"><FilePlus2 size={18} /></button>
      <div className="toolbar-divider" />
      <button className="icon-button" disabled={props.busy || !props.canUndo} onClick={props.onUndo} title="Undo (Ctrl+Z)"><Undo2 size={18} /></button>
      <button className="icon-button" disabled={props.busy || !props.canRedo} onClick={props.onRedo} title="Redo (Ctrl+Y)"><Redo2 size={18} /></button>
      <div className="tool-group">
        {tools.map(({ id, label, icon: Icon }) => (
          <button key={id} disabled={props.busy} className={`tool-button ${props.tool === id ? 'active' : ''}`} onClick={() => props.onTool(id)} title={label}>
            <Icon size={18} /><span>{label}</span>
          </button>
        ))}
        <button disabled={props.busy} className={`tool-button ${props.tool === 'image' ? 'active' : ''}`} onClick={() => props.onTool('image')} title="Insert image">
          <ImagePlus size={18} /><span>Image</span>
        </button>
      </div>
      <div className="toolbar-spacer" />
      <div className="zoom-control">
        <button onClick={() => props.onZoom(Math.max(0.5, props.zoom - 0.1))}><ZoomOut size={16} /></button>
        <span>{Math.round(props.zoom * 100)}%</span>
        <button onClick={() => props.onZoom(Math.min(2.5, props.zoom + 0.1))}><ZoomIn size={16} /></button>
      </div>
      <button className="action-button" disabled={props.busy} onClick={props.onSaveAs} title="Save As"><Save size={17} /> Save As</button>
      <button className="action-button primary" disabled={props.busy} onClick={props.onSave} title="Save new PDF to Desktop (Ctrl+S)">
        <Download size={17} /> {props.busy ? 'Saving…' : 'Desktop'}
      </button>
      <button className="icon-button" title="More information"><Menu size={18} /></button>
    </header>
  );
}
