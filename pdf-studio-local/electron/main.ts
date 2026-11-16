import { app, BrowserWindow, dialog, ipcMain, shell } from 'electron';
import { existsSync } from 'node:fs';
import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
let mainWindow: BrowserWindow | null = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1480,
    height: 920,
    minWidth: 1100,
    minHeight: 700,
    title: 'PDF Studio Local',
    backgroundColor: '#eef1f5',
    autoHideMenuBar: true,
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith('https://')) void shell.openExternal(url);
    return { action: 'deny' };
  });

  if (!app.isPackaged && process.env.VITE_DEV_SERVER_URL) {
    void mainWindow.loadURL(process.env.VITE_DEV_SERVER_URL);
  } else if (!app.isPackaged) {
    void mainWindow.loadURL('http://localhost:5173');
  } else {
    void mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
  }
}

function safeEditedName(sourceName: string) {
  const base = path.basename(sourceName, path.extname(sourceName)).replace(/[<>:"/\\|?*]/g, '_');
  return `${base || 'document'}-edited.pdf`;
}

function nextAvailablePath(folder: string, fileName: string) {
  const extension = path.extname(fileName);
  const base = path.basename(fileName, extension);
  let candidate = path.join(folder, fileName);
  let suffix = 2;
  while (existsSync(candidate)) {
    candidate = path.join(folder, `${base}-${suffix}${extension}`);
    suffix += 1;
  }
  return candidate;
}

ipcMain.handle('pdf:open', async () => {
  const result = await dialog.showOpenDialog(mainWindow!, {
    title: 'Open PDF',
    properties: ['openFile'],
    filters: [{ name: 'PDF documents', extensions: ['pdf'] }],
  });
  if (result.canceled || !result.filePaths[0]) return null;
  const filePath = result.filePaths[0];
  const data = await readFile(filePath);
  return { data: new Uint8Array(data), filePath, name: path.basename(filePath) };
});

ipcMain.handle('pdf:open-additional', async () => {
  const result = await dialog.showOpenDialog(mainWindow!, {
    title: 'Select PDFs to merge',
    properties: ['openFile', 'multiSelections'],
    filters: [{ name: 'PDF documents', extensions: ['pdf'] }],
  });
  if (result.canceled) return [];
  return Promise.all(result.filePaths.map(async (filePath) => ({
    data: new Uint8Array(await readFile(filePath)),
    name: path.basename(filePath),
  })));
});

ipcMain.handle('image:open', async () => {
  const result = await dialog.showOpenDialog(mainWindow!, {
    title: 'Insert image',
    properties: ['openFile'],
    filters: [{ name: 'Images', extensions: ['png', 'jpg', 'jpeg'] }],
  });
  if (result.canceled || !result.filePaths[0]) return null;
  const filePath = result.filePaths[0];
  const bytes = await readFile(filePath);
  const extension = path.extname(filePath).toLowerCase();
  const mime = extension === '.png' ? 'image/png' : 'image/jpeg';
  return { dataUrl: `data:${mime};base64,${bytes.toString('base64')}`, name: path.basename(filePath) };
});

ipcMain.handle('pdf:save-desktop', async (_event, bytes: Uint8Array, sourceName: string) => {
  const target = nextAvailablePath(app.getPath('desktop'), safeEditedName(sourceName));
  await writeFile(target, Buffer.from(bytes));
  return target;
});

ipcMain.handle('pdf:save-as', async (_event, bytes: Uint8Array, sourceName: string) => {
  const result = await dialog.showSaveDialog(mainWindow!, {
    title: 'Save edited PDF',
    defaultPath: path.join(app.getPath('desktop'), safeEditedName(sourceName)),
    filters: [{ name: 'PDF documents', extensions: ['pdf'] }],
  });
  if (result.canceled || !result.filePath) return null;
  const target = result.filePath.toLowerCase().endsWith('.pdf') ? result.filePath : `${result.filePath}.pdf`;
  await writeFile(target, Buffer.from(bytes));
  return target;
});

ipcMain.handle('file:show', async (_event, filePath: string) => {
  shell.showItemInFolder(filePath);
});

app.whenReady().then(() => {
  createWindow();
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
