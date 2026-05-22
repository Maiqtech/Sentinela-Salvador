import hashlib
import datetime

RISK_LABELS = {0: 'Baixo', 1: 'Médio', 2: 'Alto', 3: 'Crítico'}
RISK_COLORS = {0: '#22c55e', 1: '#eab308', 2: '#f97316', 3: '#ef4444'}

DRAINAGE_PT = {'poor': 'deficiente', 'medium': 'regular', 'good': 'boa'}
INCOME_PT = {'low': 'baixa', 'medium': 'média', 'high': 'alta'}


def generate_historical_insights(neighborhoods):
    today = datetime.date.today()
    insights = []

    for n in neighborhoods:
        h = int(hashlib.md5(n.name.encode()).hexdigest(), 16)

        days_ago = 10 + (h % 200)
        event_date = today - datetime.timedelta(days=int(days_ago))

        if n.slope_risk and n.drainage_quality == 'poor':
            event_type = 'deslizamento com alagamento'
            icon = '⛰️'
        elif n.slope_risk and n.slope_percentage >= 20:
            event_type = 'deslizamento em encosta'
            icon = '⛰️'
        elif n.drainage_quality == 'poor':
            event_type = 'alagamento em via pública'
            icon = '🌊'
        else:
            event_type = 'alagamento localizado'
            icon = '💧'

        if n.historical_events >= 8:
            severity = 'grave'
            severity_color = '#ef4444'
        elif n.historical_events >= 4:
            severity = 'moderado'
            severity_color = '#f97316'
        else:
            severity = 'leve'
            severity_color = '#eab308'

        hours = 2 + (h % 10)
        families = 3 + (h % 14)

        if n.slope_risk and n.slope_percentage >= 20:
            action_pool = [
                f'{families} famílias realocadas preventivamente. Encosta monitorada por 72h.',
                f'Contenção emergencial instalada em {hours}h. Área interditada até vistoria.',
                f'Equipe de geotecnia acionada. Solo estabilizado em {hours + 4}h.',
            ]
        elif n.drainage_quality == 'poor':
            action_pool = [
                f'Ponto de drenagem desobstruído em {hours}h. Via liberada.',
                f'Bombeamento acionado. Situação normalizada em {hours + 2}h.',
                f'Limpeza de bueiros emergencial. Trânsito restabelecido em {hours}h.',
            ]
        else:
            action_pool = [
                f'Monitoramento intensificado por 48h. Sem novas ocorrências.',
                f'Vistoria realizada no dia seguinte. Ponto mapeado no sistema.',
                f'Situação normalizada em {hours}h após cessar a chuva.',
            ]

        action = action_pool[h % len(action_pool)]

        insights.append({
            'neighborhood': n.name,
            'date': event_date.strftime('%d/%m/%Y'),
            'date_iso': event_date.isoformat(),
            'event_type': event_type,
            'severity': severity,
            'severity_color': severity_color,
            'action': action,
            'icon': icon,
            'resilience_score': n.resilience_score,
            'historical_total': n.historical_events,
        })

    insights.sort(key=lambda x: x['date_iso'], reverse=True)
    return insights[:8]


def _priority_explanation(n, risk_level):
    reasons = []
    if n.slope_risk and n.slope_percentage >= 25:
        reasons.append(f"{n.slope_percentage}% dos domicílios em encosta — alto risco de deslizamento")
    elif n.slope_risk:
        reasons.append(f"área com risco de deslizamento ({n.slope_percentage}% em encosta)")
    if n.drainage_quality == 'poor':
        reasons.append("drenagem deficiente acelera alagamento")
    if n.historical_events >= 5:
        reasons.append(f"{n.historical_events} eventos graves registrados no histórico")
    if n.resilience_score < 30:
        reasons.append(f"capacidade de resposta crítica (score {n.resilience_score}/100)")
    elif n.resilience_score < 45:
        reasons.append(f"infraestrutura de resposta limitada (score {n.resilience_score}/100)")
    if n.pop_density > 15000:
        reasons.append(f"alta densidade — {int(n.pop_density):,} hab/km²".replace(',', '.'))
    if n.pct_sem_esgoto > 40:
        reasons.append(f"{n.pct_sem_esgoto:.0f}% sem saneamento básico")
    if not reasons:
        reasons.append(f"score de resiliência {n.resilience_score}/100")
    return '. '.join(reasons[:3]).capitalize() + '.'


def generate_priority_list(ranked):
    """
    ranked: list of dicts with keys id, name, risk_level, probability, neighborhood_obj
    Returns list with rank + explanation for each.
    """
    result = []
    for i, item in enumerate(ranked):
        n = item['obj']
        result.append({
            'rank': i + 1,
            'id': item['id'],
            'name': item['name'],
            'risk_level': item['risk_level'],
            'risk_label': RISK_LABELS[item['risk_level']],
            'risk_color': RISK_COLORS[item['risk_level']],
            'probability': item['probability'],
            'explanation': _priority_explanation(n, item['risk_level']),
        })
    return result

def generate_alert(neighborhood, climate_snapshot: dict, risk_prediction: dict) -> str:
    name = neighborhood.name
    risk = risk_prediction['risk_level']
    prob = risk_prediction['probability']
    precip_6h = climate_snapshot['precip_6h']
    score = neighborhood.resilience_score

    if risk == 3:
        return (
            f"ALERTA CRÍTICO — {name} apresenta risco máximo de alagamento e deslizamento "
            f"nas próximas horas. Precipitação acumulada de {precip_6h:.1f}mm nas últimas 6h "
            f"combinada com score de resiliência de {score}/100. "
            f"Probabilidade de evento grave: {prob}%. Acionar equipes imediatamente."
        )
    elif risk == 2:
        return (
            f"ALERTA ALTO — {name} com risco elevado de alagamento. "
            f"{precip_6h:.1f}mm acumulados nas últimas 6h. "
            f"Score de resiliência: {score}/100. Monitorar e pré-posicionar equipes."
        )
    elif risk == 1:
        return (
            f"ATENÇÃO — {name} em nível de atenção. {precip_6h:.1f}mm nas últimas 6h. "
            f"Score de resiliência: {score}/100. Monitorar evolução."
        )
    return (
        f"{name} — Situação normal. {precip_6h:.1f}mm nas últimas 6h. "
        f"Score de resiliência: {score}/100. Sem ação necessária."
    )

def _build_recommendation(n, risk):
    if risk == 0:
        return "Nenhuma ação necessária. Manter monitoramento padrão."

    actions = []

    if risk >= 3:
        actions.append("Acionar equipes de resgate imediatamente")
    elif risk == 2:
        actions.append("Pré-posicionar equipes de defesa civil")
    else:
        actions.append("Monitorar evolução a cada 30 minutos")

    if n.slope_risk and n.slope_percentage >= 20:
        actions.append(
            f"emitir alerta de deslizamento para os {n.slope_percentage:.0f}% de domicílios em encosta"
        )

    if n.drainage_quality == 'poor':
        actions.append("acionar equipes de desobstrução de drenagem — risco iminente de alagamento")
    elif n.drainage_quality == 'medium' and risk >= 2:
        actions.append("verificar pontos de drenagem críticos")

    if n.historical_events >= 5:
        actions.append(
            f"priorizar pontos com histórico recorrente ({n.historical_events} eventos registrados)"
        )

    if n.resilience_score < 35:
        actions.append(
            f"acionar reforço externo — capacidade local crítica (score {n.resilience_score}/100)"
        )
    elif n.resilience_score < 50 and risk >= 2:
        actions.append(f"coordenar com CODESAL central — infraestrutura local limitada")

    if n.pop_density > 12000 and risk >= 2:
        actions.append(
            f"preparar rota de evacuação para área de alta densidade ({int(n.pop_density):,} hab/km²)".replace(',', '.')
        )

    if n.pct_sem_esgoto > 50 and risk >= 2:
        actions.append("alertar sobre risco sanitário por contaminação de água")

    if not actions:
        actions.append("manter equipe em standby")

    first = actions[0].capitalize()
    rest = '. '.join(a.capitalize() for a in actions[1:])
    return (first + ('. ' + rest if rest else '')) + '.'


def generate_dossier_text(neighborhood, climate_snapshot: dict, risk_prediction: dict) -> dict:
    risk = risk_prediction['risk_level']
    precip_6h = climate_snapshot['precip_6h']
    pressure_trend = climate_snapshot['pressure_trend']
    humidity = climate_snapshot['humidity']
    score = neighborhood.resilience_score

    threshold_status = "ACIMA" if precip_6h >= 50 else ("PRÓXIMO" if precip_6h >= 35 else "ABAIXO")
    pressure_desc = "em queda" if pressure_trend < -2 else ("estável" if pressure_trend > -1 else "levemente em queda")

    recommendation = _build_recommendation(neighborhood, risk)

    return {
        'situacao_atual': {
            'precip_6h': f"{precip_6h:.1f}mm (limiar crítico: 50mm) — {threshold_status} do limiar",
            'pressure_trend': f"{pressure_trend:+.1f}mB nas últimas 3h — pressão {pressure_desc}",
            'humidity': f"{humidity:.0f}%",
        },
        'projecao': {
            'risco': RISK_LABELS[risk],
            'probabilidade': f"{risk_prediction['probability']}%",
        },
        'vulnerabilidade': {
            'score_resiliencia': f"{score}/100",
            'drenagem': DRAINAGE_PT.get(neighborhood.drainage_quality, neighborhood.drainage_quality),
            'renda': INCOME_PT.get(neighborhood.income_level, neighborhood.income_level),
            'percentual_encosta': f"{neighborhood.slope_percentage}% dos domicílios em área de encosta",
            'eventos_historicos': f"{neighborhood.historical_events} eventos graves registrados (2000-2021)",
            'altitude_media': f"{neighborhood.elevation_mean:.0f}m acima do nível do mar",
            'densidade_pop': f"{neighborhood.pop_density:,.0f} hab/km²",
            'sem_esgoto': f"{neighborhood.pct_sem_esgoto:.1f}% dos domicílios sem saneamento",
        },
        'recomendacao': recommendation,
    }
