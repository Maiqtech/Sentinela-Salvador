import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [
    react(),
    {
      name: 'geojson',
      transform(code, id) {
        if (id.endsWith('.geojson')) return `export default ${code}`
      }
    }
  ],
  server: {
    port: 3000,
    proxy: {
      '/api': 'http://localhost:8001'
    }
  }
})
