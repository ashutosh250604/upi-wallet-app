import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // host: true, // listen on all addresses
    allowedHosts: ['localhost','192.168.1.16:5000','192.168.1.16:5173'], // add your ngrok URL here
  }
});
