import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import App from './App.jsx'
import { AuthProvider } from './context/AuthContext.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <App />
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 3500,
            style: {
              background: '#1e293b',
              color: '#f1f5f9',
              border: '1px solid rgba(139,92,246,0.3)',
              borderRadius: '12px',
              fontFamily: '"DM Sans", sans-serif',
              fontSize: '14px',
              boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
            },
            success: { iconTheme: { primary: '#10b981', secondary: '#f1f5f9' }, style: { borderColor: 'rgba(16,185,129,0.3)' } },
            error:   { iconTheme: { primary: '#ef4444', secondary: '#f1f5f9' }, style: { borderColor: 'rgba(239,68,68,0.3)'  } },
          }}
        />
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>
)
