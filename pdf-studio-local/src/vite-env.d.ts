/// <reference types="vite/client" />

declare module '*?url' {
  const url: string;
  export default url;
}

declare module 'pdf-lib-encrypt' {
  import type * as PdfLib from 'pdf-lib';
  export function configure(pdfLib: typeof PdfLib): void;
  export function lock(bytes: Uint8Array, password: string, options?: { algo?: 'aes256' | 'rc4'; permissions?: number }): Promise<Uint8Array>;
}
