export default function AlertPanel({ alert, climate }) {
  if (!alert && !climate) return null
  const getClass = (text) => {
    if (!text) return 'alert-normal'
    if (text.includes('CRÍTICO')) return 'alert-critical'
    if (text.includes('ALTO')) return 'alert-high'
    if (text.includes('ATENÇÃO')) return 'alert-medium'
    return 'alert-normal'
  }
  return (
    <div className="alert-panel">
      <div style={{ fontSize: '0.7rem', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '8px' }}>
        Alerta Automático
      </div>
      {alert ? (
        <div className={`alert-box ${getClass(alert)}`}>{alert}</div>
      ) : (
        <div className="alert-box alert-normal">Sistema monitorando. Sem alertas ativos.</div>
      )}
      {climate && (
        <div style={{ marginTop: '8px', fontSize: '0.75rem', color: '#64748b', display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          <span>🌧 {climate.precip_6h?.toFixed(1)}mm/6h</span>
          <span>💧 {climate.humidity?.toFixed(0)}%</span>
          <span>📊 {climate.pressure?.toFixed(1)}mB</span>
          <span>💨 {climate.wind_speed?.toFixed(1)}m/s</span>
        </div>
      )}
    </div>
  )
}
