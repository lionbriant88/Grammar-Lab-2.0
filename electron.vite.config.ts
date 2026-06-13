import { defineConfig } from 'electron-vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  main: {
    plugins: [react()],
    define: {
      // electron-vite 通过此环境变量把 dev server URL 传给主进程
      'process.env.VITE_DEV_SERVER_URL': JSON.stringify(process.env.VITE_DEV_SERVER_URL)
    },
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
        '@main': path.resolve(__dirname, './src/main'),
        '@shared': path.resolve(__dirname, './src/shared')
      }
    }
  },
  preload: {
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
        '@shared': path.resolve(__dirname, './src/shared')
      }
    }
  },
  renderer: {
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
        '@renderer': path.resolve(__dirname, './src/renderer'),
        '@shared': path.resolve(__dirname, './src/shared')
      }
    }
  }
});
