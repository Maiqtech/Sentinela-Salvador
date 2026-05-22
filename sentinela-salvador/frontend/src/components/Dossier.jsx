const LABELS = {
  precip_6h: 'Chuva acumulada (6h)',
  pressure_trend: 'Tendência de pressão',
  humidity: 'Umidade relativa',
  score_resiliencia: 'Score de resiliência',
  drenagem: 'Qualidade da drenagem',
  renda: 'Renda predominante',
  percentual_encosta: 'Domicílios em encosta',
  eventos_historicos: 'Eventos históricos',
  risco: 'Nível de risco',
  probabilidade: 'Probabilidade',
  altitude_media: 'Altitude média',
  densidade_pop: 'Densidade populacional',
  sem_esgoto: 'Sem saneamento básico',
}

export default function Dossier({ data, onClose }) {
  if (!data) return (
    <div className="dossier">
      <div className="empty-state">
        Clique em um bairro no mapa para ver o dossiê completo
      </div>
    </div>
  )

  const { neighborhood, alert, dossier, prediction } = data
  const riskColors = { 0: '#22c55e', 1: '#eab308', 2: '#f97316', 3: '#ef4444' }
  const riskLabels = { 0: 'Baixo', 1: 'Médio', 2: 'Alto', 3: 'Crítico' }
  const color = riskColors[prediction?.risk_level ?? 0]
  const label = riskLabels[prediction?.risk_level ?? 0]
  const score = neighborhood.resilience_score
  const scoreColor = score < 35 ? '#ef4444' : score < 60 ? '#f97316' : '#22c55e'

  return (
    <div className="dossier">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '4px' }}>
        <h2>{neighborhood.name}</h2>
        <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', fontSize: '1.1rem' }}>✕</button>
      </div>
      <span className="risk-badge" style={{ background: color + '20', color, border: `1px solid ${color}` }}>
        Risco {label} — {prediction?.probability}%
      </span>

      <div className="section">
        <div className="section-title">Situação Atual</div>
        {dossier?.situacao_atual && Object.entries(dossier.situacao_atual).map(([k, v]) => (
          <div className="metric" key={k}>
            <span className="metric-label">{LABELS[k] || k.replace(/_/g,' ')}</span>
            <span className="metric-value" style={{ maxWidth: '55%', textAlign: 'right' }}>{v}</span>
          </div>
        ))}
      </div>

      <div className="section">
        <div className="section-title">Score de Resiliência</div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
          <span style={{ fontSize: '1.4rem', fontWeight: 700, color: scoreColor }}>{score}</span>
          <span style={{ fontSize: '0.75rem', color: '#64748b' }}>/ 100</span>
        </div>
        <div className="score-bar">
          <div className="score-fill" style={{ width: `${score}%`, background: scoreColor }} />
        </div>
      </div>

      <div className="section">
        <div className="section-title">Vulnerabilidade do Bairro</div>
        {dossier?.vulnerabilidade && Object.entries(dossier.vulnerabilidade).map(([k, v]) => (
          <div className="metric" key={k}>
            <span className="metric-label">{LABELS[k] || k.replace(/_/g,' ')}</span>
            <span className="metric-value" style={{ maxWidth: '55%', textAlign: 'right' }}>{v}</span>
          </div>
        ))}
      </div>

      <div className="section">
        <div className="section-title">Recomendação da IA</div>
        <div className="recommendation">{dossier?.recomendacao}</div>
      </div>
    </div>
  )
}
