import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { FileLock2, FilePenLine, FolderOpen, Plus, ShieldCheck } from 'lucide-react';
import Toolbar from './components/Toolbar';
import PageSidebar from './components/PageSidebar';
import PageCanvas from './components/PageCanvas';
import PropertiesPanel from './components/PropertiesPanel';
import Toast from './components/Toast';
import { appendBlankPage, exportPdf, getPdfInfo, loadPdfForViewing, mergePdfs, protectPdf, type PdfJsDocument } from './services/pdf';
import type { Annotation, EditorDocumentState, OpenedPdf, Tool } from './types/editor';

const emptyMetadata = { title: '', author: '', subject: '', keywords: '' };
const initialDocument: EditorDocumentState = { pages: [], annotations: [], metadata: emptyMetadata };

function pageId() { return crypto.randomUUID(); }

function rotateAnnotationClockwise(annotation: Annotation): Annotation {
  if (annotation.type === 'draw' || annotation.type === 'signature') {
    return { ...annotation, points: annotation.points?.map((point) => ({ x: 1 - point.y, y: point.x })) };
  }
  return { ...annotation, x: 1 - annotation.y - annotation.height, y: annotation.x, width: annotation.height, height: annotation.width };
}

export default function App() {
  const [source, setSource] = useState<OpenedPdf | null>(null);
  const [sourceBytes, setSourceBytes] = useState<Uint8Array | null>(null);
  const [pdf, setPdf] = useState<PdfJsDocument | null>(null);
  const [documentState, setDocumentState] = useState<EditorDocumentState>(initialDocument);
  const [past, setPast] = useState<EditorDocumentState[]>([]);
  const [future, setFuture] = useState<EditorDocumentState[]>([]);
  const [activePageId, setActivePageId] = useState('');
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [tool, setTool] = useState<Tool>('select');
  const [zoom, setZoom] = useState(1);
  const [pendingImage, setPendingImage] = useState<string | null>(null);
  const [exportPassword, setExportPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [toast, setToast] = useState<{ message: string; error?: boolean; path?: string } | null>(null);
  const toastTimer = useRef<number | undefined>(undefined);
  const revision = useRef(0);

  const showToast = useCallback((message: string, error = false, path?: string) => {
    window.clearTimeout(toastTimer.current);
    setToast({ message, error, path });
    toastTimer.current = window.setTimeout(() => setToast(null), 5000);
  }, []);

  const commit = useCallback((updater: EditorDocumentState | ((state: EditorDocumentState) => EditorDocumentState)) => {
    revision.current += 1;
    setDocumentState((current) => {
      const next = typeof updater === 'function' ? updater(current) : updater;
      setPast((history) => [...history.slice(-49), current]);
      setFuture([]);
      return next;
    });
    setDirty(true);
  }, []);

  const undo = useCallback(() => {
    setPast((history) => {
      if (!history.length) return history;
      revision.current += 1;
      const previous = history[history.length - 1];
      setDocumentState((current) => { setFuture((items) => [current, ...items].slice(0, 50)); return previous; });
      setSelectedId(null); setDirty(true);
      return history.slice(0, -1);
    });
  }, []);

  const redo = useCallback(() => {
    setFuture((items) => {
      if (!items.length) return items;
      revision.current += 1;
      const next = items[0];
      setDocumentState((current) => { setPast((history) => [...history.slice(-49), current]); return next; });
      setSelectedId(null); setDirty(true);
      return items.slice(1);
    });
  }, []);

  const loadDocument = useCallback(async (opened: OpenedPdf) => {
    setBusy(true);
    try {
      const bytes = new Uint8Array(opened.data);
      const [viewer, info] = await Promise.all([loadPdfForViewing(bytes), getPdfInfo(bytes)]);
      const pages = Array.from({ length: info.pageCount }, (_, sourceIndex) => ({ id: pageId(), sourceIndex, rotation: 0 }));
      setSource(opened); setSourceBytes(bytes); setPdf((current) => { void current?.cleanup(); return viewer; });
      revision.current = 0;
      setDocumentState({ pages, annotations: [], metadata: info.metadata });
      setPast([]); setFuture([]); setActivePageId(pages[0]?.id ?? ''); setSelectedId(null); setTool('select'); setExportPassword(''); setDirty(false);
    } catch (error) {
      showToast(error instanceof Error ? error.message : 'Could not open this PDF.', true);
    } finally { setBusy(false); }
  }, [showToast]);

  const openPdf = useCallback(async () => {
    if (busy || (dirty && !window.confirm('Open another PDF? Unsaved edits will be lost.'))) return;
    setBusy(true);
    try {
      const opened = await window.pdfAPI.openPdf();
      if (opened) await loadDocument(opened);
    } finally { setBusy(false); }
  }, [busy, dirty, loadDocument]);

  const merge = useCallback(async () => {
    if (busy || !sourceBytes || !pdf) return;
    setBusy(true);
    try {
      const files = await window.pdfAPI.openAdditionalPdfs();
      if (!files.length) return;
      const oldCount = pdf.numPages;
      const result = await mergePdfs(sourceBytes, files.map((file) => new Uint8Array(file.data)));
      const bytes = new Uint8Array(result.bytes);
      const viewer = await loadPdfForViewing(bytes);
      setSourceBytes(bytes); setPdf((current) => { void current?.cleanup(); return viewer; });
      commit((state) => ({ ...state, pages: [...state.pages, ...Array.from({ length: result.added }, (_, index) => ({ id: pageId(), sourceIndex: oldCount + index, rotation: 0 }))] }));
      showToast(`${result.added} page${result.added === 1 ? '' : 's'} added.`);
    } catch (error) { showToast(error instanceof Error ? error.message : 'Could not merge PDFs.', true); }
    finally { setBusy(false); }
  }, [busy, sourceBytes, pdf, commit, showToast]);

  const addBlank = useCallback(async () => {
    if (busy || !sourceBytes || !pdf) return;
    setBusy(true);
    try {
      const newPage = { id: pageId(), sourceIndex: pdf.numPages, rotation: 0 };
      const bytes = new Uint8Array(await appendBlankPage(sourceBytes));
      const viewer = await loadPdfForViewing(bytes);
      setSourceBytes(bytes); setPdf((current) => { void current?.cleanup(); return viewer; }); commit((state) => ({ ...state, pages: [...state.pages, newPage] })); setActivePageId(newPage.id);
    } catch (error) { showToast(error instanceof Error ? error.message : 'Could not add a blank page.', true); }
    finally { setBusy(false); }
  }, [busy, sourceBytes, pdf, commit, showToast]);

  const save = useCallback(async (saveAs = false) => {
    if (busy || !sourceBytes || !source) return;
    const savedRevision = revision.current;
    setBusy(true);
    try {
      const plainBytes = new Uint8Array(await exportPdf(sourceBytes, documentState.pages, documentState.annotations, documentState.metadata));
      const bytes = new Uint8Array(await protectPdf(plainBytes, exportPassword));
      const target = saveAs ? await window.pdfAPI.saveAs(bytes, source.name) : await window.pdfAPI.saveToDesktop(bytes, source.name);
      if (target) { if (revision.current === savedRevision) setDirty(false); showToast(`Saved: ${target}`, false, target); }
    } catch (error) { showToast(error instanceof Error ? error.message : 'Could not save the PDF.', true); }
    finally { setBusy(false); }
  }, [busy, sourceBytes, source, documentState, exportPassword, showToast]);

  const handleTool = useCallback(async (nextTool: Tool) => {
    if (busy) return;
    if (nextTool === 'image') {
      setBusy(true);
      try {
        const image = await window.pdfAPI.openImage();
        if (!image) return;
        setPendingImage(image.dataUrl);
      } finally { setBusy(false); }
    }
    setTool(nextTool);
  }, [busy]);

  const activePage = documentState.pages.find((page) => page.id === activePageId) ?? documentState.pages[0];
  const selected = documentState.annotations.find((annotation) => annotation.id === selectedId);
  const pageAnnotations = useMemo(() => documentState.annotations.filter((annotation) => annotation.pageId === activePage?.id), [documentState.annotations, activePage?.id]);

  const deleteSelected = useCallback(() => {
    if (!selectedId) return;
    commit((state) => ({ ...state, annotations: state.annotations.filter((annotation) => annotation.id !== selectedId) }));
    setSelectedId(null);
  }, [selectedId, commit]);

  useEffect(() => {
    const listener = (event: KeyboardEvent) => {
      if (busy) return;
      const modifier = event.ctrlKey || event.metaKey;
      if (modifier && event.key.toLowerCase() === 'o') { event.preventDefault(); void openPdf(); }
      if (modifier && event.key.toLowerCase() === 's') { event.preventDefault(); void save(event.shiftKey); }
      if (modifier && event.key.toLowerCase() === 'z') { event.preventDefault(); event.shiftKey ? redo() : undo(); }
      if (modifier && event.key.toLowerCase() === 'y') { event.preventDefault(); redo(); }
      if ((event.key === 'Delete' || event.key === 'Backspace') && selectedId && !(event.target instanceof HTMLInputElement) && !(event.target instanceof HTMLTextAreaElement)) deleteSelected();
    };
    window.addEventListener('keydown', listener);
    return () => window.removeEventListener('keydown', listener);
  }, [busy, openPdf, save, undo, redo, selectedId, deleteSelected]);

  if (!source || !pdf || !sourceBytes) {
    return (
      <div className="welcome-shell">
        <div className="welcome-top"><div className="brand"><span className="brand-mark">P</span><span>PDF Studio <b>Local</b></span></div><div className="offline-pill"><ShieldCheck size={15} /> 100% offline</div></div>
        <main className="welcome-card">
          <div className="welcome-icon"><FilePenLine size={42} /></div>
          <h1>Edit PDFs privately.</h1>
          <p>Professional PDF tools that run entirely on your Windows computer. Your documents are never uploaded.</p>
          <button className="open-large" onClick={() => void openPdf()} disabled={busy}><FolderOpen size={20} /> {busy ? 'Opening…' : 'Open a PDF'}</button>
          <div className="feature-grid">
            <div><FilePenLine size={20} /><span><strong>Edit & annotate</strong>Text, highlights, drawing, images</span></div>
            <div><Plus size={20} /><span><strong>Organize pages</strong>Merge, rotate, reorder, delete</span></div>
            <div><FileLock2 size={20} /><span><strong>Private by design</strong>No cloud, accounts, or uploads</span></div>
          </div>
        </main>
        <footer>PDF Studio Local · Windows 11 · Files stay on this device</footer>
      </div>
    );
  }

  return (
    <div className="app-shell">
      <Toolbar tool={tool} zoom={zoom} canUndo={past.length > 0} canRedo={future.length > 0} busy={busy} onTool={(value) => void handleTool(value)} onOpen={() => void openPdf()} onMerge={() => void merge()} onSave={() => void save(false)} onSaveAs={() => void save(true)} onUndo={undo} onRedo={redo} onZoom={setZoom} />
      <div className="document-bar"><span className={`dirty-dot ${dirty ? 'visible' : ''}`} /> <strong>{source.name}</strong><span>{documentState.pages.length} pages</span><span className="local-badge"><ShieldCheck size={13} /> Local file</span></div>
      <div className="workspace">
        <PageSidebar pdf={pdf} pages={documentState.pages} activePageId={activePage?.id ?? ''} onActive={(id) => { setActivePageId(id); setSelectedId(null); }} onReorder={(from, to) => commit((state) => { const pages = [...state.pages]; const [moved] = pages.splice(from, 1); pages.splice(to, 0, moved); return { ...state, pages }; })} onRotate={() => activePage && commit((state) => ({ ...state, pages: state.pages.map((page) => page.id === activePage.id ? { ...page, rotation: (page.rotation + 90) % 360 } : page), annotations: state.annotations.map((annotation) => annotation.pageId === activePage.id ? rotateAnnotationClockwise(annotation) : annotation) }))} onDuplicate={() => activePage && commit((state) => { const index = state.pages.findIndex((page) => page.id === activePage.id); const duplicate = { ...activePage, id: pageId() }; const duplicatedAnnotations = state.annotations.filter((annotation) => annotation.pageId === activePage.id).map((annotation) => ({ ...annotation, id: crypto.randomUUID(), pageId: duplicate.id })); const pages = [...state.pages]; pages.splice(index + 1, 0, duplicate); return { ...state, pages, annotations: [...state.annotations, ...duplicatedAnnotations] }; })} onDelete={() => { if (!activePage || documentState.pages.length === 1) { showToast('A PDF must contain at least one page.', true); return; } commit((state) => ({ ...state, pages: state.pages.filter((page) => page.id !== activePage.id), annotations: state.annotations.filter((annotation) => annotation.pageId !== activePage.id) })); const index = documentState.pages.findIndex((page) => page.id === activePage.id); setActivePageId(documentState.pages[Math.max(0, index - 1)].id); }} onAddBlank={() => void addBlank()} />
        <main className="canvas-area">
          {activePage && <PageCanvas pdf={pdf} page={activePage} annotations={pageAnnotations} selectedId={selectedId} tool={tool} zoom={zoom} pendingImage={pendingImage} onSelect={setSelectedId} onCreate={(annotation) => commit((state) => ({ ...state, annotations: [...state.annotations, annotation] }))} onUpdate={(id, patch) => commit((state) => ({ ...state, annotations: state.annotations.map((annotation) => annotation.id === id ? { ...annotation, ...patch } : annotation) }))} onImagePlaced={() => { setPendingImage(null); setTool('select'); }} />}
        </main>
        <PropertiesPanel annotation={selected} metadata={documentState.metadata} password={exportPassword} onPassword={(password) => { setExportPassword(password); setDirty(true); revision.current += 1; }} onAnnotation={(patch) => selected && commit((state) => ({ ...state, annotations: state.annotations.map((annotation) => annotation.id === selected.id ? { ...annotation, ...patch } : annotation) }))} onDelete={deleteSelected} onMetadata={(metadata) => commit((state) => ({ ...state, metadata }))} />
      </div>
      {busy && <div className="busy-shield"><span>Working…</span></div>}
      <div className="statusbar"><span>Page {Math.max(1, documentState.pages.findIndex((page) => page.id === activePage?.id) + 1)} of {documentState.pages.length}</span><span>{tool === 'select' ? 'Select an object to edit its properties' : tool === 'image' ? 'Click on the page to place the image' : `Tool: ${tool}`}</span><span>Offline</span></div>
      {toast && <Toast message={toast.message} error={toast.error} action={toast.path ? () => void window.pdfAPI.showInFolder(toast.path!) : undefined} />}
    </div>
  );
}
