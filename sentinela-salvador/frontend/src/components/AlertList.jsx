function getSystemStatus(alerts) {
  const critical = alerts.filter(a => a.risk_level >= 3).length
  const high = alerts.filter(a => a.risk_level === 2).length
  const medium = alerts.filter(a => a.risk_level === 1).length
  if (critical >= 3) return { level: 3, label: 'EMERGÊNCIA', color: '#ef4444', bg: '#450a0a' }
  if (critical >= 1) return { level: 3, label: 'CRÍTICO', color: '#ef4444', bg: '#450a0a' }
  if (high >= 3)     return { level: 2, label: 'ALTO', color: '#f97316', bg: '#431407' }
  if (high >= 1)     return { level: 2, label: 'ELEVADO', color: '#f97316', bg: '#431407' }
  if (medium >= 1)   return { level: 1, label: 'ATENÇÃO', color: '#eab308', bg: '#422006' }
  return { level: 0, label: 'NORMAL', color: '#22c55e', bg: '#052e16' }
}

function buildInsight(alerts, climate, isSimulation) {
  if (!climate) return null
  const critical = alerts.filter(a => a.risk_level >= 3).length
  const high = alerts.filter(a => a.risk_level === 2).length
  const precip = climate.precip_6h ?? 0
  const pressure = climate.pressure_trend ?? 0
  const humidity = climate.humidity ?? 0
  const lines = []

  if (isSimulation) lines.push(`Cenário hipotético com ${precip.toFixed(0)}mm/6h acumulados.`)

  if (critical > 0)
    lines.push(`${critical} bairro${critical > 1 ? 's' : ''} em nível crítico — risco de deslizamento e alagamento iminente.`)
  else if (high > 0)
    lines.push(`${high} bairro${high > 1 ? 's' : ''} em risco elevado. Equipes devem ser pré-posicionadas.`)
  else if (alerts.length === 0 && !isSimulation)
    lines.push('Situação dentro da normalidade. Nenhum bairro em alerta no momento.')

  if (pressure < -2.5)
    lines.push('Pressão em queda acentuada — padrão associado a intensificação de chuvas nas próximas horas.')
  else if (pressure < -1)
    lines.push('Pressão levemente em queda — monitorar evolução.')

  if (humidity >= 90 && precip >= 20)
    lines.push('Umidade saturada combinada com chuva acumulada eleva risco de alagamentos rápidos.')

  if (precip >= 50)
    lines.push('Limiar crítico de 50mm/6h atingido. Protocolo de emergência recomendado.')
  else if (precip >= 35)
    lines.push(`Precipitação próxima ao limiar crítico (${precip.toFixed(0)}mm de 50mm). Monitoramento intensivo.`)
  else if (precip < 5 && critical === 0 && high === 0 && !isSimulation)
    lines.push('Dia de rotina. Recomenda-se verificar pontos históricos preventivamente.')

  return lines.length > 0 ? lines : null
}

export default function AlertList({ alerts, climate, onAlertClick, isSimulation }) {
  const hasAlerts = alerts && alerts.length > 0
  const status = getSystemStatus(alerts || [])
  const insight = buildInsight(alerts || [], climate, isSimulation)

  const critical = (alerts || []).filter(a => a.risk_level >= 3).length
  const high     = (alerts || []).filter(a => a.risk_level === 2).length
  const medium   = (alerts || []).filter(a => a.risk_level === 1).length

  const precip = climate?.precip_6h ?? 0
  const precipPct = Math.min((precip / 50) * 100, 100)
  const precipColor = precip >= 50 ? '#ef4444' : precip >= 35 ? '#f97316' : precip >= 15 ? '#eab308' : '#22c55e'

  return (
    <div className="alert-list-panel">

      {/* Status geral */}
      <div className="alert-status-card" style={{ borderColor: status.color, background: status.bg }}>
        <div className="alert-status-left">
          <div className="alert-status-dot" style={{ background: status.color }} />
          <div>
            <div className="alert-status-label" style={{ color: status.color }}>STATUS {status.label}</div>
            <div className="alert-status-counts">
              {critical > 0 && <span style={{ color: '#ef4444' }}>{critical} crítico{critical > 1 ? 's' : ''}</span>}
              {high > 0    && <span style={{ color: '#f97316' }}>{high} alto{high > 1 ? 's' : ''}</span>}
              {medium > 0  && <span style={{ color: '#eab308' }}>{medium} médio{medium > 1 ? 's' : ''}</span>}
              {!hasAlerts  && <span style={{ color: '#22c55e' }}>0 bairros em risco</span>}
            </div>
          </div>
        </div>
        <div className="alert-status-time">
          {new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
        </div>
      </div>

      {/* Barra de limiar */}
      {climate && (
        <div className="alert-threshold-section">
          <div className="alert-threshold-header">
            <span className="alert-threshold-label">Precipitação acumulada (6h)</span>
            <span className="alert-threshold-value" style={{ color: precipColor }}>
              {precip.toFixed(1)}mm <span style={{ color: '#475569' }}>/ 50mm limiar</span>
            </span>
          </div>
          <div className="alert-threshold-bar">
            <div className="alert-threshold-fill" style={{ width: `${precipPct}%`, background: precipColor }} />
            <div className="alert-threshold-mark" />
          </div>
          <div className="alert-climate-row">
            <span>🌡 {climate.temperature?.toFixed(0)}°C</span>
            <span>💧 {climate.humidity?.toFixed(0)}%</span>
            <span>📊 {climate.pressure_trend > 0 ? '+' : ''}{climate.pressure_trend?.toFixed(1)} mB/h</span>
            <span>💨 {climate.wind_speed?.toFixed(1)} m/s</span>
          </div>
        </div>
      )}

      {/* Análise situacional */}
      {insight && (
        <div className="alert-insight-box" style={{ borderLeftColor: status.color }}>
          <div className="alert-insight-title" style={{ color: status.color }}>Análise situacional</div>
          {insight.map((line, i) => (
            <p key={i} className="alert-insight-line">{line}</p>
          ))}
        </div>
      )}

      {/* Bairros em alerta */}
      <div className="alert-list-header">
        <span className="section-label">Bairros em alerta</span>
        {hasAlerts && (
          <span className="alert-count-badge">{alerts.length} bairro{alerts.length > 1 ? 's' : ''}</span>
        )}
      </div>

      {!hasAlerts ? (
        <div className="no-alerts">
          <span style={{ fontSize: '1.1rem' }}>✅</span>
          <span>Nenhum bairro em alerta ativo</span>
        </div>
      ) : (
        <div className="alert-items">
          {alerts.map((a) => (
            <button key={a.id} className="alert-item" onClick={() => onAlertClick(a.id)}>
              <div className="alert-item-left">
                <span className="alert-risk-dot" style={{ background: a.risk_color }} />
                <div className="alert-item-info">
                  <span className="alert-item-name">{a.name}</span>
                  {a.message
                    ? <span className="alert-item-msg">{a.message}</span>
                    : <span className="alert-item-sub">Resiliência {a.resilience_score}/100</span>
                  }
                </div>
              </div>
              <div className="alert-item-right">
                <span className="alert-risk-badge"
                  style={{ color: a.risk_color, borderColor: a.risk_color + '60', background: a.risk_color + '15' }}>
                  {a.risk_label}
                </span>
                <span className="alert-prob">{a.probability}%</span>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
