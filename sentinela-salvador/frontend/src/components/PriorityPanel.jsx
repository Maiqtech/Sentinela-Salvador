export default function PriorityPanel({ priority, onItemClick }) {
  if (!priority || priority.length === 0) return (
    <div className="empty-state" style={{ padding: '32px 16px' }}>
      <div style={{ fontSize: '1.5rem', marginBottom: 8 }}>🤖</div>
      <div style={{ fontWeight: 600, marginBottom: 4, color: '#94a3b8' }}>Nenhum bairro em risco</div>
      <div style={{ fontSize: '0.75rem', color: '#475569' }}>Execute uma simulação ou selecione um horizonte com chuva para ver a priorização da IA.</div>
    </div>
  )

  return (
    <div className="priority-panel">
      <div className="priority-header">
        <span className="section-label">🤖 Priorização da IA</span>
        <span style={{ fontSize: '0.68rem', color: '#64748b' }}>clique para ver dossiê</span>
      </div>
      <div className="priority-items">
        {priority.map(item => (
          <button key={item.id} className="priority-item" onClick={() => onItemClick(item.id)}>
            <div className="priority-rank" style={{ color: item.risk_color }}>{item.rank}º</div>
            <div className="priority-body">
              <div className="priority-name-row">
                <span className="priority-name">{item.name}</span>
                <span className="priority-badge"
                  style={{ color: item.risk_color, background: item.risk_color + '18', border: `1px solid ${item.risk_color}60` }}>
                  {item.risk_label} · {item.probability}%
                </span>
              </div>
              <div className="priority-reason">{item.explanation}</div>
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}
