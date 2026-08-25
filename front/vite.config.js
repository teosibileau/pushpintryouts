import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react()],
  server: {
    // file events from the mac host don't propagate over colima's
    // virtiofs mount, so watch by polling or HMR serves stale code
    watch: {
      usePolling: true,
      interval: 300,
    },
    proxy: {
      '/ws': {
        target: 'http://pushpin:7999',
        ws: true,
      },
      '/api': {
        target: 'http://pushpin:7999',
      },
    },
  },
})
