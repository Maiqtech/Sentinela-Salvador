export default function Legend() {
  const items = [
    { color: '#22c55e', label: 'Baixo' },
    { color: '#eab308', label: 'Médio' },
    { color: '#f97316', label: 'Alto' },
    { color: '#ef4444', label: 'Crítico' },
  ]
  return (
    <div className="legend">
      <h4>Nível de Risco</h4>
      <div className="legend-items">
        {items.map(i => (
          <div key={i.label} className="legend-item">
            <div className="legend-dot" style={{ background: i.color }} />
            <span>{i.label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
