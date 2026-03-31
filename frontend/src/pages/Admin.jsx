import { useState, useEffect } from 'react'
import toast from 'react-hot-toast'
import MetricCard from '../components/MetricCard'
import { fetchAdminUsers, updateUserPlan } from '../services/api'

const PLAN_COLORS = {
  ELITE: { bg:'rgba(251,191,36,0.12)', border:'rgba(251,191,36,0.3)', text:'#fbbf24' },
  PRO:   { bg:'rgba(139,92,246,0.12)', border:'rgba(139,92,246,0.3)', text:'#a78bfa' },
  FREE:  { bg:'rgba(100,116,139,0.12)',border:'rgba(100,116,139,0.3)',text:'#94a3b8' },
}

export default function Admin() {
  const [users, setUsers]     = useState([])
  const [loading, setLoading] = useState(true)
  const [updating, setUpdating] = useState(null)
  const [search, setSearch]   = useState('')

  useEffect(() => { fetchAdminUsers().then(d => { setUsers(d); setLoading(false) }) }, [])

  const handlePlanChange = async (id, plan) => {
    setUpdating(id)
    try { await updateUserPlan(id, plan); setUsers(p => p.map(u => u.id===id?{...u,plan}:u)); toast.success(`Plan updated to ${plan}`) }
    catch { toast.error('Failed to update plan') }
    finally { setUpdating(null) }
  }

  const filtered = search.trim() ? users.filter(u => u.name.toLowerCase().includes(search.toLowerCase()) || u.email.toLowerCase().includes(search.toLowerCase())) : users
  const totals = { ELITE: users.filter(u=>u.plan==='ELITE').length, PRO: users.filter(u=>u.plan==='PRO').length, FREE: users.filter(u=>u.plan==='FREE').length }

  return (
    <div style={{ animation: 'fadeUp 0.4s ease both' }}>
      <div style={{ display:'flex', alignItems:'flex-start', justifyContent:'space-between', marginBottom:32, paddingBottom:22, borderBottom:'1px solid rgba(71,85,105,0.18)' }}>
        <div>
          <div style={{ display:'flex', alignItems:'center', gap:10, marginBottom:4 }}>
            <h1 style={{ color:'#f1f5f9', fontWeight:800, fontSize:26, margin:0, fontFamily:"'Space Mono',monospace", letterSpacing:'-0.03em' }}>Admin Panel</h1>
            <span style={{ background:'rgba(239,68,68,0.12)', border:'1px solid rgba(239,68,68,0.25)', color:'#f87171', fontSize:10, fontWeight:800, borderRadius:6, padding:'2px 9px', letterSpacing:'0.1em', fontFamily:"'Space Mono',monospace" }}>RESTRICTED</span>
          </div>
          <p style={{ color:'#475569', fontSize:13, margin:0 }}>User management and plan administration</p>
        </div>
      </div>

      <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:16, marginBottom:30 }}>
        <MetricCard loading={loading} icon="👤" label="Total Users" value={users.length}   sub="All registered"   color="#8b5cf6" />
        <MetricCard loading={loading} icon="🏆" label="Elite"       value={totals.ELITE}   sub="Top tier"         color="#fbbf24" />
        <MetricCard loading={loading} icon="⭐" label="Pro"         value={totals.PRO}     sub="Paid"             color="#a78bfa" />
        <MetricCard loading={loading} icon="🆓" label="Free"        value={totals.FREE}    sub="Convert"          color="#64748b" />
      </div>

      <div style={{ background:'linear-gradient(145deg,rgba(30,41,59,0.8),rgba(15,23,42,0.9))', border:'1px solid rgba(71,85,105,0.35)', borderRadius:18, overflow:'hidden' }}>
        <div style={{ padding:'18px 26px', borderBottom:'1px solid rgba(71,85,105,0.25)', display:'flex', alignItems:'center', justifyContent:'space-between', gap:16 }}>
          <div style={{ display:'flex', alignItems:'center', gap:10 }}>
            <h3 style={{ color:'#f1f5f9', fontWeight:700, fontSize:15, margin:0, fontFamily:"'Space Mono',monospace" }}>User Management</h3>
            <span style={{ color:'#a78bfa', fontSize:12, fontFamily:"'Space Mono',monospace", background:'rgba(139,92,246,0.1)', border:'1px solid rgba(139,92,246,0.2)', borderRadius:6, padding:'2px 9px' }}>{users.length} users</span>
          </div>
          <input type="text" value={search} onChange={e => setSearch(e.target.value)} placeholder="Search by name or email…" style={{ padding:'8px 14px', borderRadius:10, width:240, background:'rgba(10,15,30,0.7)', border:'1px solid rgba(71,85,105,0.4)', color:'#f1f5f9', fontSize:13, outline:'none', fontFamily:'inherit' }} />
        </div>

        {loading ? (
          <div style={{ padding:'16px 26px', display:'flex', flexDirection:'column', gap:10 }}>
            {Array(4).fill(0).map((_,i) => <div key={i} className="skeleton" style={{height:62,borderRadius:10}}/>)}
          </div>
        ) : (
          <div style={{ overflowX:'auto' }}>
            <table style={{ width:'100%', borderCollapse:'collapse' }}>
              <thead>
                <tr style={{ borderBottom:'1px solid rgba(71,85,105,0.25)' }}>
                  {['User','Email','Role','Plan','Signals','Joined','Change Plan'].map(h => (
                    <th key={h} style={{ padding:'12px 20px', textAlign:'left', color:'#475569', fontSize:10, fontWeight:700, letterSpacing:'0.12em', textTransform:'uppercase', whiteSpace:'nowrap' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.map((u, i) => {
                  const ps = PLAN_COLORS[u.plan] || PLAN_COLORS.FREE
                  const initials = u.name.split(' ').map(w=>w[0]).join('').slice(0,2).toUpperCase()
                  return (
                    <tr key={u.id} style={{ borderBottom:i<filtered.length-1?'1px solid rgba(71,85,105,0.18)':'none' }}
                      onMouseEnter={e=>e.currentTarget.style.background='rgba(139,92,246,0.04)'}
                      onMouseLeave={e=>e.currentTarget.style.background='transparent'}>
                      <td style={{ padding:'15px 20px' }}>
                        <div style={{ display:'flex', alignItems:'center', gap:11 }}>
                          <div style={{ width:34, height:34, borderRadius:'50%', flexShrink:0, background:'linear-gradient(135deg,#8b5cf6,#6366f1)', display:'flex', alignItems:'center', justifyContent:'center', fontSize:12, fontWeight:800, color:'#fff', fontFamily:"'Space Mono',monospace" }}>{initials}</div>
                          <span style={{ color:'#f1f5f9', fontSize:13, fontWeight:600, whiteSpace:'nowrap' }}>{u.name}</span>
                        </div>
                      </td>
                      <td style={{ padding:'15px 20px', color:'#94a3b8', fontSize:12, whiteSpace:'nowrap' }}>{u.email}</td>
                      <td style={{ padding:'15px 20px' }}>
                        <span style={{ background:u.role==='admin'?'rgba(239,68,68,0.1)':'rgba(71,85,105,0.15)', border:`1px solid ${u.role==='admin'?'rgba(239,68,68,0.25)':'rgba(71,85,105,0.3)'}`, color:u.role==='admin'?'#f87171':'#94a3b8', borderRadius:7, padding:'3px 10px', fontSize:10, fontWeight:700, letterSpacing:'0.08em', textTransform:'uppercase', fontFamily:"'Space Mono',monospace" }}>{u.role}</span>
                      </td>
                      <td style={{ padding:'15px 20px' }}>
                        <span style={{ background:ps.bg, border:`1px solid ${ps.border}`, color:ps.text, borderRadius:7, padding:'3px 10px', fontSize:10, fontWeight:700, letterSpacing:'0.08em', textTransform:'uppercase', fontFamily:"'Space Mono',monospace" }}>{u.plan}</span>
                      </td>
                      <td style={{ padding:'15px 20px', color:'#64748b', fontSize:13, fontFamily:"'Space Mono',monospace" }}>{u.signals}</td>
                      <td style={{ padding:'15px 20px', color:'#64748b', fontSize:12, fontFamily:"'Space Mono',monospace", whiteSpace:'nowrap' }}>{u.joined}</td>
                      <td style={{ padding:'15px 20px' }}>
                        <div style={{ display:'flex', gap:6 }}>
                          {['FREE','PRO','ELITE'].map(plan => {
                            const pc = PLAN_COLORS[plan]
                            return (
                              <button key={plan} onClick={() => handlePlanChange(u.id, plan)} disabled={u.plan===plan||updating===u.id} style={{ padding:'5px 11px', borderRadius:8, fontSize:10, fontWeight:700, fontFamily:"'Space Mono',monospace", cursor:u.plan===plan?'default':'pointer', letterSpacing:'0.06em', background:u.plan===plan?pc.bg:'rgba(15,23,42,0.6)', border:`1px solid ${u.plan===plan?pc.border:'rgba(71,85,105,0.35)'}`, color:u.plan===plan?pc.text:'#64748b', opacity:updating===u.id&&u.plan!==plan?0.5:1, transition:'all 0.15s ease' }}>
                                {updating===u.id&&u.plan!==plan?'…':plan}
                              </button>
                            )
                          })}
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
