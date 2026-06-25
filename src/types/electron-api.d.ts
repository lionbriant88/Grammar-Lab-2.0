// M3: Ambient declaration for the preload-injected electronAPI.
// The runtime value is set by contextBridge.exposeInMainWorld() in src/preload/index.ts.
// This file exists so the renderer's TypeScript checker sees window.electronAPI
// as strongly-typed without requiring every file to import from src/preload.
//
// preload/index.ts owns the *single* source of truth for the surface
// (`exposeInMainWorld` + the matching `export interface ElectronAPI`).
// If you add/remove/change a method on electronAPI, update both places together.

import type { ElectronAPI } from '../preload';

declare global {
  interface Window {
    electronAPI: ElectronAPI;
  }
}

export {};