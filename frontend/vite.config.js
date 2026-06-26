import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,          // bind 0.0.0.0 so forwarded ports work (e.g. Codespaces)
    allowedHosts: true,  // accept the Codespaces *.app.github.dev forwarded host
    proxy: {
      '/api': 'http://localhost:8000'
    }
  }
})
