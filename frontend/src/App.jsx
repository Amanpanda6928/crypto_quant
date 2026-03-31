import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import Navbar from './components/Navbar'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import TradingDashboard from './pages/TradingDashboard'
import Signals from './pages/Signals'
import Portfolio from './pages/Portfolio'
import Analytics from './pages/Analytics'
import Admin from './pages/Admin'

function ProtectedRoute({ children, adminOnly = false }) {
  const { user, loading } = useAuth()
  if (loading) {
    return (
      <div style={{ minHeight: '100vh', background: '#0a0f1e', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ width: 48, height: 48, borderRadius: '50%', border: '3px solid rgba(139,92,246,0.2)', borderTopColor: '#8b5cf6', animation: 'spin 0.8s linear infinite', margin: '0 auto 16px' }} />
          <div style={{ color: '#475569', fontSize: 13, fontFamily: "'Space Mono', monospace", letterSpacing: '0.1em' }}>LOADING…</div>
        </div>
      </div>
    )
  }
  if (!user) return <Navigate to="/login" replace />
  if (adminOnly && user.role !== 'admin') return <Navigate to="/dashboard" replace />
  return children
}

function AppLayout({ children }) {
  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#0a0f1e' }}>
      <Navbar />
      <main style={{
        marginLeft: 240, flex: 1, padding: '32px 40px', minHeight: '100vh', overflowY: 'auto',
        backgroundImage: `
          radial-gradient(ellipse 100% 60% at 70% 0%, rgba(139,92,246,0.06) 0%, transparent 60%),
          radial-gradient(ellipse 60% 40% at 10% 100%, rgba(99,102,241,0.04) 0%, transparent 50%)
        `,
      }}>
        {children}
      </main>
    </div>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/dashboard" element={<ProtectedRoute><AppLayout><Dashboard /></AppLayout></ProtectedRoute>} />
      <Route path="/trading"   element={<ProtectedRoute><AppLayout><TradingDashboard /></AppLayout></ProtectedRoute>} />
      <Route path="/signals"   element={<ProtectedRoute><AppLayout><Signals /></AppLayout></ProtectedRoute>} />
      <Route path="/portfolio" element={<ProtectedRoute><AppLayout><Portfolio /></AppLayout></ProtectedRoute>} />
      <Route path="/analytics" element={<ProtectedRoute><AppLayout><Analytics /></AppLayout></ProtectedRoute>} />
      <Route path="/admin"     element={<ProtectedRoute adminOnly><AppLayout><Admin /></AppLayout></ProtectedRoute>} />
      <Route path="*"          element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}
