import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Proxy API requests to FastAPI backend (localhost:8000)
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/ask': 'http://localhost:8000',
      '/feedback': 'http://localhost:8000',
    }
  }
})
