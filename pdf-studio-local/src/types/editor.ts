export type Tool = 'select' | 'text' | 'highlight' | 'rectangle' | 'ellipse' | 'draw' | 'redact' | 'image' | 'signature';

export interface EditorPage {
  id: string;
  sourceIndex: number;
  rotation: number;
}

export interface Point {
  x: number;
  y: number;
}

export interface Annotation {
  id: string;
  pageId: string;
  type: Exclude<Tool, 'select'>;
  x: number;
  y: number;
  width: number;
  height: number;
  color: string;
  opacity: number;
  strokeWidth: number;
  text?: string;
  fontSize?: number;
  points?: Point[];
  dataUrl?: string;
}

export interface DocumentMetadata {
  title: string;
  author: string;
  subject: string;
  keywords: string;
}

export interface EditorDocumentState {
  pages: EditorPage[];
  annotations: Annotation[];
  metadata: DocumentMetadata;
}

export interface OpenedPdf {
  data: Uint8Array;
  filePath: string;
  name: string;
}

export interface PdfApi {
  openPdf(): Promise<OpenedPdf | null>;
  openAdditionalPdfs(): Promise<Array<{ data: Uint8Array; name: string }>>;
  openImage(): Promise<{ dataUrl: string; name: string } | null>;
  saveToDesktop(bytes: Uint8Array, sourceName: string): Promise<string>;
  saveAs(bytes: Uint8Array, sourceName: string): Promise<string | null>;
  showInFolder(filePath: string): Promise<void>;
}

declare global {
  interface Window {
    pdfAPI: PdfApi;
  }
}
