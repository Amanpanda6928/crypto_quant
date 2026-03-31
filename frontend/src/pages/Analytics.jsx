import { useState, useEffect } from 'react'
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import MetricCard from '../components/MetricCard'
import { generateEquityCurve } from '../services/api'

const RETURNS_DATA = [
  {range:'<-5%',count:2},{range:'-5%',count:4},{range:'-3%',count:8},{range:'-1%',count:14},
  {range:'0%',count:20},{range:'+1%',count:26},{range:'+3%',count:19},{range:'+5%',count:11},{range:'>+5%',count:6},
]
const MONTHLY = [
  {month:'Oct',return:8.2},{month:'Nov',return:-3.1},{month:'Dec',return:12.7},
  {month:'Jan',return:6.4},{month:'Feb',return:-1.8},{month:'Mar',return:9.3},
]
const ttStyle = { contentStyle:{background:'#1e293b',border:'1px solid rgba(139,92,246,0.3)',borderRadius:12,color:'#f1f5f9',fontSize:12,boxShadow:'0 8px 30px rgba(0,0,0,0.4)'}, itemStyle:{color:'#94a3b8'}, labelStyle:{color:'#f1f5f9',fontWeight:700,fontFamily:"'Space Mono',monospace"} }

// AI Predictions mock data
const AI_PREDICTIONS = [
  { coin: 'BTC', name: 'Bitcoin', signal: 'BUY', confidence: 87, target_price: 67250, predicted_change: 2.4 },
  { coin: 'ETH', name: 'Ethereum', signal: 'BUY', confidence: 82, target_price: 3450, predicted_change: 1.8 },
  { coin: 'SOL', name: 'Solana', signal: 'SELL', confidence: 78, target_price: 142.50, predicted_change: -1.2 },
  { coin: 'AVAX', name: 'Avalanche', signal: 'BUY', confidence: 75, target_price: 38.20, predicted_change: 3.1 },
  { coin: 'LINK', name: 'Chainlink', signal: 'HOLD', confidence: 71, target_price: 18.45, predicted_change: 0.3 },
]

function AIPredictionsList() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8, maxHeight: 200, overflowY: 'auto' }}>
      {AI_PREDICTIONS.map((pred, i) => (
        <div key={pred.coin} style={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between',
          padding: '10px 12px',
          borderRadius: 10,
          background: i % 2 === 0 ? 'rgba(15,23,42,0.4)' : 'transparent',
          border: '1px solid rgba(71,85,105,0.15)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{ 
              width: 32, 
              height: 32, 
              borderRadius: 8, 
              background: 'rgba(139,92,246,0.15)', 
              border: '1px solid rgba(139,92,246,0.3)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 10,
              fontWeight: 800,
              color: '#a78bfa'
            }}>
              {pred.coin}
            </div>
            <div>
              <div style={{ color: '#f1f5f9', fontSize: 12, fontWeight: 700 }}>{pred.name}</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 2 }}>
                <span style={{ 
                  color: pred.signal === 'BUY' ? '#34d399' : pred.signal === 'SELL' ? '#f87171' : '#fbbf24',
                  fontSize: 10,
                  fontWeight: 700,
                  background: pred.signal === 'BUY' ? 'rgba(52,211,153,0.15)' : pred.signal === 'SELL' ? 'rgba(248,113,113,0.15)' : 'rgba(245,158,11,0.15)',
                  padding: '2px 6px',
                  borderRadius: 4
                }}>
                  {pred.signal}
                </span>
                <span style={{ color: '#64748b', fontSize: 9 }}>{pred.confidence}% confidence</span>
              </div>
            </div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div style={{ color: '#f1f5f9', fontSize: 13, fontWeight: 700, fontFamily: "'Space Mono',monospace" }}>
              ${pred.target_price.toLocaleString()}
            </div>
            <div style={{ 
              color: pred.predicted_change >= 0 ? '#34d399' : '#f87171',
              fontSize: 10,
              fontWeight: 700
            }}>
              {pred.predicted_change >= 0 ? '+' : ''}{pred.predicted_change}%
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

function Card({ title, children }) {
  return (
    <div style={{ background:'linear-gradient(145deg,rgba(30,41,59,0.8),rgba(15,23,42,0.9))', border:'1px solid rgba(71,85,105,0.35)', borderRadius:18, padding:26 }}>
      <h3 style={{ color:'#f1f5f9', fontWeight:700, fontSize:14, margin:'0 0 22px', fontFamily:"'Space Mono',monospace", letterSpacing:'0.04em' }}>{title}</h3>
      {children}
    </div>
  )
}

export default function Analytics() {
  const [equityData, setEquityData] = useState([])
  const [loading, setLoading]       = useState(true)

  useEffect(() => { setTimeout(() => { setEquityData(generateEquityCurve(60)); setLoading(false) }, 700) }, [])

  const lastEq  = equityData[equityData.length - 1]?.equity || 0
  const totalRet = lastEq ? (((lastEq - 10000) / 10000) * 100).toFixed(1) : '0.0'

  return (
    <div style={{ animation: 'fadeUp 0.4s ease both' }}>
      <div style={{ marginBottom:32, paddingBottom:22, borderBottom:'1px solid rgba(71,85,105,0.18)' }}>
        <h1 style={{ color:'#f1f5f9', fontWeight:800, fontSize:26, margin:'0 0 4px', fontFamily:"'Space Mono',monospace", letterSpacing:'-0.03em' }}>Analytics</h1>
        <p style={{ color:'#475569', fontSize:13, margin:0 }}>Strategy performance & portfolio analytics</p>
      </div>

      <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:16, marginBottom:28 }}>
        <MetricCard loading={loading} icon="📈" label="Total Return"  value={`+${totalRet}%`} sub="Since inception"    color="#10b981" trend="+8.3%" positive />
        <MetricCard loading={loading} icon="⚖️" label="Sharpe Ratio"  value="2.14"            sub="Risk-adjusted"     color="#8b5cf6" trend="vs 1.2 BM" positive />
        <MetricCard loading={loading} icon="📉" label="Max Drawdown"  value="-8.3%"           sub="Peak to trough"    color="#ef4444" trend="-2.1% mth" positive={false} />
        <MetricCard loading={loading} icon="🎯" label="Win Rate"      value="67.3%"           sub="Profitable signals" color="#6366f1" trend="+4.2% mth" positive />
      </div>

      <div style={{ display:'grid', gridTemplateColumns:'2fr 1fr', gap:20, marginBottom:20 }}>
        <Card title="Equity Curve — Strategy vs Benchmark">
          {loading ? <div className="skeleton" style={{height:230,borderRadius:10}}/> : (
            <ResponsiveContainer width="100%" height={230}>
              <AreaChart data={equityData} margin={{top:4,right:4,bottom:0,left:0}}>
                <defs>
                  <linearGradient id="gradEq" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.35}/><stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/></linearGradient>
                  <linearGradient id="gradBm" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#64748b" stopOpacity={0.18}/><stop offset="95%" stopColor="#64748b" stopOpacity={0}/></linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(71,85,105,0.2)"/>
                <XAxis dataKey="day" stroke="#475569" tick={{fill:'#475569',fontSize:10}} interval={9}/>
                <YAxis stroke="#475569" tick={{fill:'#475569',fontSize:10}} tickFormatter={v=>`$${(v/1000).toFixed(1)}k`}/>
                <Tooltip {...ttStyle} formatter={(v,n)=>[`$${v.toFixed(0)}`,n==='equity'?'Strategy':'Benchmark']}/>
                <Legend wrapperStyle={{color:'#64748b',fontSize:12}}/>
                <Area type="monotone" dataKey="benchmark" stroke="#64748b" strokeWidth={1.5} fill="url(#gradBm)" strokeDasharray="5 4" name="Benchmark"/>
                <Area type="monotone" dataKey="equity"    stroke="#8b5cf6" strokeWidth={2.5} fill="url(#gradEq)" name="Strategy"/>
              </AreaChart>
            </ResponsiveContainer>
          )}
        </Card>
        <Card title="Monthly Returns">
          <ResponsiveContainer width="100%" height={230}>
            <BarChart data={MONTHLY} margin={{top:4,right:4,bottom:0,left:0}}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(71,85,105,0.2)"/>
              <XAxis dataKey="month" stroke="#475569" tick={{fill:'#475569',fontSize:10}}/>
              <YAxis stroke="#475569" tick={{fill:'#475569',fontSize:10}} tickFormatter={v=>`${v}%`}/>
              <Tooltip {...ttStyle} formatter={v=>[`${v}%`,'Return']}/>
              <Bar dataKey="return" radius={[5,5,0,0]} fill="#8b5cf6" name="Return"/>
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:20, marginBottom:20 }}>
        <Card title="Returns Distribution">
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={RETURNS_DATA} margin={{top:4,right:4,bottom:0,left:0}}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(71,85,105,0.2)"/>
              <XAxis dataKey="range" stroke="#475569" tick={{fill:'#475569',fontSize:10}}/>
              <YAxis stroke="#475569" tick={{fill:'#475569',fontSize:10}}/>
              <Tooltip {...ttStyle}/>
              <Bar dataKey="count" radius={[5,5,0,0]} fill="#6366f1" name="Frequency"/>
            </BarChart>
          </ResponsiveContainer>
        </Card>
        <Card title="AI Future Predictions (1h)">
          <AIPredictionsList />
        </Card>
      </div>
    </div>
  )
}
