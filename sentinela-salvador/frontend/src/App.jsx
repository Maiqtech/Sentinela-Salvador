import { useState, useEffect } from 'react'
import SalvadorMap from './components/SalvadorMap'
import AlertList from './components/AlertList'
import PriorityPanel from './components/PriorityPanel'
import Dossier from './components/Dossier'
import { fetchForecast, fetchDossier, simulateRain } from './services/api'

const HORIZON_KEYS = ['now', '+6h', '+12h', '+24h', '+48h']
const SIDEBAR_TABS = ['Alertas', 'Prioridade', 'Dossiê', 'Simulação']

export default function App() {
  const [forecast, setForecast] = useState([])
  const [selectedIdx, setSelectedIdx] = useState(0)
  const [sideTab, setSideTab] = useState(0)
  const [dossier, setDossier] = useState(null)
  const [loading, setLoading] = useState(true)
  const [forecastError, setForecastError] = useState(null)
  const [simPrecip, setSimPrecip] = useState(80)
  const [simHours, setSimHours] = useState(6)
  const [simData, setSimData] = useState(null)
  const [simPriority, setSimPriority] = useState([])
  const [simClimate, setSimClimate] = useState(null)
  const [simLoading, setSimLoading] = useState(false)
  const [simError, setSimError] = useState(null)

  const loadForecast = async () => {
    setLoading(true)
    setForecastError(null)
    try {
      const data = await fetchForecast()
      setForecast(data.forecast)
    } catch (e) {
      setForecastError('Erro ao carregar previsão')
      console.error(e)
    }
    setLoading(false)
  }

  // Auto-simulate 80mm/6h on load for a compelling first impression
  const runDefaultSim = async () => {
    try {
      const data = await simulateRain(80, 6)
      if (data.simulation) {
        setSimData(data.simulation)
        setSimPriority(data.priority || [])
        setSimClimate(data.climate_input || null)
        setSimPrecip(80)
        setSimHours(6)
        setSideTab(1)
      }
    } catch (e) { /* silent — forecast still shows */ }
  }

  useEffect(() => {
    loadForecast()
    runDefaultSim()
  }, [])

  const selected = forecast[selectedIdx] || null
  const neighborhoods = simData || selected?.neighborhoods || []
  const climate = simData ? simClimate : (selected?.climate || null)
  const priority = simData ? simPriority : (selected?.priority || [])
  const alerts = simData
    ? simData.filter(n => n.risk_level >= 1).slice(0, 8).map(n => ({
        id: n.id, name: n.name, risk_level: n.risk_level,
        risk_label: n.risk_label, risk_color: n.risk_color,
        probability: n.probability, resilience_score: n.resilience_score,
        message: n.message || null,
      }))
    : selected?.alerts || []

  const handleNeighborhoodClick = async (id) => {
    try {
      const params = simData
        ? { precip_mm: simPrecip, hours: simHours }
        : { horizon: HORIZON_KEYS[selectedIdx] }
      const data = await fetchDossier(id, params)
      setDossier(data)
      setSideTab(2)
    } catch (e) { console.error(e) }
  }

  const handleSimulate = async () => {
    setSimLoading(true)
    setSimError(null)
    try {
      const data = await simulateRain(simPrecip, simHours)
      if (!data.simulation) throw new Error('Resposta inválida do servidor')
      setSimData(data.simulation)
      setSimPriority(data.priority || [])
      setSimClimate(data.climate_input || null)
      setSideTab(1)
    } catch (e) {
      setSimError(e.message || 'Erro na simulação')
      console.error(e)
    }
    setSimLoading(false)
  }

  const clearSim = () => {
    setSimData(null)
    setSimPriority([])
    setSimClimate(null)
    setSimError(null)
    setDossier(null)
    setSideTab(0)
  }

  const criticalCount = (simData || selected?.neighborhoods || []).filter(
    n => (n.risk_level ?? n.current_risk_level) >= 2
  ).length

  return (
    <div className="app">
      {/* Header */}
      <div className="header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <img src="/logo-header.png" alt="Sentinela" style={{ height: 38, width: 'auto' }} />
          <div>
            <h1>Sentinela Salvador</h1>
            <div className="subtitle">Plataforma de Inteligência Climática — CODESAL</div>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {simData && (
            <span className="sim-pill">⚡ Simulação {simPrecip}mm/{simHours}h</span>
          )}
          {criticalCount > 0 && (
            <span className="badge">{criticalCount} bairro{criticalCount > 1 ? 's' : ''} em risco alto/crítico</span>
          )}
          {loading && <span style={{ fontSize: '0.78rem', color: '#64748b' }}>Carregando...</span>}
        </div>
      </div>

      {/* Forecast bar */}
      <div className="forecast-bar">
        <div className="forecast-bar-tabs">
          {forecast.map((h, i) => (
            <button
              key={h.horizon}
              className={`fbar-tab${i === selectedIdx ? ' active' : ''}`}
              onClick={() => { setSelectedIdx(i); setSimData(null); setSimPriority([]); setDossier(null); setSideTab(0) }}
            >
              {h.label}
              {h.critical_count > 0 && <span className="fbar-badge">{h.critical_count}</span>}
            </button>
          ))}
          {forecast.length === 0 && !loading && (
            <button className="fbar-tab" onClick={loadForecast}>↻ Recarregar</button>
          )}
        </div>
        {climate && (
          <div className="forecast-bar-climate">
            <span>🌧 <b>{climate.precip_6h?.toFixed(1)}</b>mm/6h</span>
            <span>🌡 <b>{climate.temperature?.toFixed(0)}</b>°C</span>
            <span>💧 <b>{climate.humidity?.toFixed(0)}</b>%</span>
            <span>📊 <b>{climate.pressure_trend > 0 ? '+' : ''}{climate.pressure_trend?.toFixed(1)}</b>mB/h</span>
            <span>💨 <b>{climate.wind_speed?.toFixed(1)}</b>m/s</span>
          </div>
        )}
        <div className="forecast-bar-legend">
          {[['#22c55e','Baixo'],['#eab308','Médio'],['#f97316','Alto'],['#ef4444','Crítico']].map(([c,l]) => (
            <span key={l} className="fbar-legend-item">
              <span style={{ width: 8, height: 8, borderRadius: '50%', background: c, display:'inline-block' }} />
              {l}
            </span>
          ))}
        </div>
        {forecastError && <span style={{ color: '#ef4444', fontSize: '0.75rem' }}>{forecastError}</span>}
      </div>

      {/* Main */}
      <div className="main">
        <div className="map-container">
          <SalvadorMap
            neighborhoods={selected?.neighborhoods || []}
            onNeighborhoodClick={handleNeighborhoodClick}
            simulationData={simData}
          />
        </div>

        <div className="sidebar">
          <div className="side-tabs">
            {SIDEBAR_TABS.map((t, i) => (
              <button
                key={t}
                className={`side-tab${sideTab === i ? ' active' : ''}`}
                onClick={() => setSideTab(i)}
              >
                {t}
                {i === 0 && alerts.filter(a => a.risk_level >= 2).length > 0 && (
                  <span className="side-tab-dot" />
                )}
              </button>
            ))}
          </div>

          <div className="side-content">
            {sideTab === 0 && (
              <AlertList alerts={alerts} climate={climate} onAlertClick={handleNeighborhoodClick} isSimulation={!!simData} />
            )}
            {sideTab === 1 && (
              <PriorityPanel priority={priority} onItemClick={handleNeighborhoodClick} />
            )}
            {sideTab === 2 && (
              <Dossier data={dossier} onClose={() => setDossier(null)} />
            )}
            {sideTab === 3 && (
              <div className="sim-panel">
                <h3>Simulação de Cenário</h3>
                <p className="sim-hint">Defina uma chuva hipotética e veja quais bairros entram em risco.</p>
                <div className="sim-controls">
                  <div className="sim-input">
                    <label>Precipitação (mm)</label>
                    <input type="number" value={simPrecip} onChange={e => setSimPrecip(Number(e.target.value))} min="0" max="300" />
                  </div>
                  <div className="sim-input">
                    <label>Em (horas)</label>
                    <input type="number" value={simHours} onChange={e => setSimHours(Number(e.target.value))} min="1" max="24" />
                  </div>
                  <button className="btn" onClick={handleSimulate} disabled={simLoading}>
                    {simLoading ? '...' : 'Simular'}
                  </button>
                </div>
                <div className="sim-presets">
                  <span className="sim-preset-label">Cenários:</span>
                  {[['Moderada','30mm/6h',30,6],['Intensa','80mm/6h',80,6],['Extrema','120mm/3h',120,3]].map(([name,desc,p,h]) => (
                    <button key={name} className="sim-preset-btn"
                      onClick={() => { setSimPrecip(p); setSimHours(h) }}>
                      {name}<span>{desc}</span>
                    </button>
                  ))}
                </div>
                {simError && <div style={{ color: '#ef4444', fontSize: '0.75rem', marginTop: 6 }}>{simError}</div>}
                {simData && (
                  <div className="sim-active-banner">
                    <span>⚡ {simData.filter(n => n.risk_level >= 2).length} bairros em risco alto/crítico</span>
                    <button onClick={clearSim} className="sim-clear">Limpar</button>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
