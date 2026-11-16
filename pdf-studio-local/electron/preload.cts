const { contextBridge, ipcRenderer } = require('electron') as typeof import('electron');

contextBridge.exposeInMainWorld('pdfAPI', {
  openPdf: () => ipcRenderer.invoke('pdf:open'),
  openAdditionalPdfs: () => ipcRenderer.invoke('pdf:open-additional'),
  openImage: () => ipcRenderer.invoke('image:open'),
  saveToDesktop: (bytes: Uint8Array, sourceName: string) => ipcRenderer.invoke('pdf:save-desktop', bytes, sourceName),
  saveAs: (bytes: Uint8Array, sourceName: string) => ipcRenderer.invoke('pdf:save-as', bytes, sourceName),
  showInFolder: (filePath: string) => ipcRenderer.invoke('file:show', filePath),
});
