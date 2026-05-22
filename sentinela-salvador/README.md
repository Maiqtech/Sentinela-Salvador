# Sentinela Salvador
**Plataforma de Inteligência Climática para Defesa Civil**
Desenvolvido para a BaIA Week 2026 — UFBA

---

## O Problema

Em novembro de 2024, 219mm de chuva caíram sobre Salvador em 72 horas — o dobro da média histórica para o mês. Um jovem de 23 anos morreu soterrado em Saramandaia enquanto descansava em casa. Quatro pessoas foram soterradas no mesmo evento.

A CODESAL (Defesa Civil de Salvador) gerencia 163 bairros com vulnerabilidades distintas: encostas, drenagem precária, alta densidade populacional, baixa renda. Quando a chuva intensifica, operadores de plantão precisam decidir onde enviar equipes limitadas — sem ferramenta de priorização, em tempo real.

**O Sentinela resolve isso.**

---

## O que o Sistema Faz

- Monitora condições climáticas em tempo real via API OpenWeatherMap
- Calcula risco de alagamento/deslizamento por bairro usando modelo de IA
- Ajusta o risco pelo score de resiliência individual de cada bairro
- Prioriza automaticamente onde as equipes devem atuar primeiro, com justificativa
- Permite simular cenários hipotéticos ("o que acontece com 120mm em 3h?")
- Exibe previsão em 5 horizontes temporais: Agora, +6h, +12h, +24h, +48h

---

## Arquitetura

```
┌─────────────────────────────────────────────────────┐
│                    FRONTEND                          │
│  React 18 + Vite 5 + Leaflet.js + leaflet.heat      │
│  Mapa interativo · Tabs · Simulação · Dossiê         │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP (proxy /api → :8001)
┌──────────────────────▼──────────────────────────────┐
│                    BACKEND                           │
│  Django 4.2 + Django REST Framework                  │
│  SQLite · 163 bairros cadastrados                    │
├─────────────────────────────────────────────────────┤
│  Serviços                                            │
│  ├── weather_service.py  → OpenWeatherMap API        │
│  ├── predictor.py        → Random Forest (sklearn)   │
│  ├── data_loader.py      → snapshots climáticos      │
│  └── alert_generator.py → alertas + priorização IA  │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│                MODELO DE IA                          │
│  Random Forest Classifier (scikit-learn)             │
│  Treinado em dados INMET A401 · 2015–2021            │
│  ~2.4 milhões de registros horários                  │
│  10 features climáticas · 4 classes de risco         │
└─────────────────────────────────────────────────────┘
```

---

## Stack Técnico

| Camada | Tecnologia |
|--------|-----------|
| Frontend | React 18, Vite 5, Leaflet.js, leaflet.heat |
| Backend | Django 4.2, Django REST Framework |
| Banco de dados | SQLite (163 bairros de Salvador) |
| IA / ML | scikit-learn RandomForestClassifier |
| Dados climáticos | OpenWeatherMap API (fallback: mock sazonal) |
| Dados de treino | INMET Estação A401 — Salvador 2015–2021 |
| GeoJSON | 163 polígonos de bairros de Salvador (WGS84) |

---

## Modelo de Inteligência Artificial

### Dados de Treino
- **Fonte:** INMET (Instituto Nacional de Meteorologia) — Estação A401, Salvador
- **Período:** Janeiro 2015 a Dezembro 2021
- **Volume:** ~2.4 milhões de registros horários
- **Split:** 80% treino / 20% teste (estratificado por classe)

### Features de Entrada (10)

| Feature | Descrição |
|---------|-----------|
| `precip_1h` | Precipitação acumulada na última hora (mm) |
| `precip_3h` | Precipitação acumulada nas últimas 3h (mm) |
| `precip_6h` | Precipitação acumulada nas últimas 6h (mm) |
| `precip_12h` | Precipitação acumulada nas últimas 12h (mm) |
| `precip_24h` | Precipitação acumulada nas últimas 24h (mm) |
| `pressure_trend` | Variação de pressão nas últimas 3h (mB/h) |
| `humidity` | Umidade relativa do ar (%) |
| `wind_speed` | Velocidade do vento (m/s) |
| `month` | Mês do ano (sazonalidade) |
| `hour_of_day` | Hora do dia (padrão diurno/noturno) |

### Classes de Saída

| Classe | Label | Limiar (precip_6h) |
|--------|-------|--------------------|
| 0 | Baixo | < 10mm |
| 1 | Médio | 10mm – 29mm |
| 2 | Alto | 30mm – 49mm |
| 3 | Crítico | ≥ 50mm |

### Hiperparâmetros

```python
RandomForestClassifier(
    n_estimators=100,
    max_depth=10,
    min_samples_leaf=5,
    random_state=42,
    n_jobs=-1
)
```

### Ajuste por Resiliência de Bairro

O risco base do modelo é ajustado pelo **score de resiliência** de cada bairro (0–100):

```
score < 35  → escala +1 nível de risco (bairro vulnerável)
score ≥ 70  → reduz -1 nível de risco (bairro resiliente)
35–69       → risco base mantido
```

A probabilidade também é ajustada proporcionalmente ao delta do score.

---

## Score de Resiliência

Cada bairro possui um score de 0 a 100 composto por:

| Fator | Impacto |
|-------|---------|
| Qualidade da drenagem (poor/medium/good) | Alto |
| Percentual de domicílios em encosta | Alto |
| Renda predominante (low/medium/high) | Médio |
| Histórico de eventos graves (2000–2021) | Médio |
| Percentual sem saneamento básico | Médio |
| Densidade populacional (hab/km²) | Baixo |
| Altitude média (m) | Baixo |

**Bairros com dados curados (amostra):**

| Bairro | Score | Encosta | Drenagem | Eventos Hist. |
|--------|-------|---------|---------|---------------|
| Periperi | 28 | 48% | Deficiente | 9 |
| Nordeste de Amaralina | 31 | 42% | Deficiente | 7 |
| Cajazeiras | 34 | 28% | Regular | 6 |
| Pau da Lima | 38 | 35% | Deficiente | 8 |
| Liberdade | 41 | 22% | Regular | 5 |
| Pituba | 71 | 0% | Boa | 1 |
| Barra | 74 | 0% | Boa | 0 |
| Itaigara | 78 | 0% | Boa | 0 |

---

## API Endpoints

Base URL: `http://localhost:8001/api`

### `GET /neighborhoods/forecast/`
Retorna previsão de risco para os 5 horizontes temporais (Agora, +6h, +12h, +24h, +48h).

**Resposta resumida:**
```json
{
  "forecast": [
    {
      "horizon": "now",
      "label": "Agora",
      "climate": {
        "precip_6h": 12.4,
        "temperature": 27.1,
        "humidity": 84.0,
        "pressure_trend": -1.2,
        "wind_speed": 3.1
      },
      "neighborhoods": [
        {
          "id": 1,
          "name": "Periperi",
          "risk_level": 3,
          "risk_label": "Crítico",
          "risk_color": "#ef4444",
          "probability": 87.3,
          "resilience_score": 28,
          "lat": -12.8912,
          "lon": -38.5234
        }
      ],
      "critical_count": 8,
      "alerts": [...],
      "priority": [...]
    }
  ]
}
```

### `POST /neighborhoods/simulate/`
Simula cenário hipotético de chuva para todos os 163 bairros.

**Body:**
```json
{ "precip_mm": 80, "hours": 6 }
```

**Resposta resumida:**
```json
{
  "simulation": [
    { "id": 1, "name": "Periperi", "risk_level": 3, "probability": 91.2,
      "message": "ALERTA CRÍTICO — Periperi apresenta risco máximo de alagamento..." }
  ],
  "climate_input": { "precip_6h": 80.0, "pressure_trend": -4.2, "humidity": 93.0 },
  "priority": [
    {
      "rank": 1,
      "name": "Periperi",
      "risk_level": 3,
      "probability": 91.2,
      "explanation": "48% dos domicílios em encosta — alto risco de deslizamento. Drenagem deficiente acelera alagamento. Capacidade de resposta crítica (score 28/100)."
    }
  ]
}
```

### `GET /neighborhoods/{id}/dossier/`
Dossiê completo de um bairro com análise de vulnerabilidade e recomendação da IA.

| Parâmetro | Comportamento |
|-----------|--------------|
| `?precip_mm=80&hours=6` | Usa snapshot da simulação |
| `?horizon=+12h` | Usa snapshot do horizonte de previsão |
| *(sem parâmetros)* | Usa dados climáticos atuais |

### `GET /neighborhoods/`
Lista todos os bairros com risco atual calculado e persistido.

### `GET /neighborhoods/insights/`
Retorna insights históricos gerados a partir das características de vulnerabilidade dos bairros.

---

## Cenários de Simulação Pré-definidos

| Cenário | Precipitação | Duração | Referência real |
|---------|-------------|---------|----------------|
| Moderada | 30mm | 6h | Chuva intensa típica da temporada |
| Intensa | 80mm | 6h | Limiar crítico ultrapassado |
| Extrema | 120mm | 3h | Próximo ao evento de novembro 2024 (219mm/72h) |

---

## Instalação e Execução

### Pré-requisitos
- Python 3.11+
- Node.js 18+

### Backend

```bash
cd backend
pip install -r requirements.txt

# Criar banco e popular os 163 bairros
python manage.py migrate
python manage.py seed_all_neighborhoods

# Treinar modelo de IA (necessário apenas na primeira vez)
python ml/train.py

# Iniciar servidor na porta 8001
python manage.py runserver 8001
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# Acesse: http://localhost:5173
```

### API OpenWeatherMap (opcional)
Se não configurada, o sistema usa mock sazonal automático baseado no mês do ano.

```bash
# No backend, definir como variável de ambiente ou em settings.py
OWM_API_KEY=sua_chave_aqui
```

---

## Estrutura do Projeto

```
sentinela-salvador/
├── backend/
│   ├── apps/
│   │   ├── neighborhoods/
│   │   │   ├── models.py              # Modelo Neighborhood (163 bairros)
│   │   │   ├── views.py               # ForecastView, SimulateView, DossierView
│   │   │   ├── serializers.py
│   │   │   └── management/commands/
│   │   │       └── seed_all_neighborhoods.py  # Seed dos 163 bairros via GeoJSON
│   │   └── climate/
│   │       └── services/
│   │           ├── weather_service.py   # OWM API + mock sazonal
│   │           ├── predictor.py         # Inferência Random Forest
│   │           ├── data_loader.py       # Snapshots climáticos
│   │           └── alert_generator.py   # Alertas + priorização + recomendações
│   ├── ml/
│   │   ├── features.py          # Feature engineering (rolling windows)
│   │   ├── train.py             # Script de treino
│   │   └── saved_models/
│   │       └── rf_model.pkl     # Modelo treinado (não versionado)
│   └── sentinela/
│       └── settings.py
└── frontend/
    ├── src/
    │   ├── App.jsx              # Orquestrador principal + estado global
    │   ├── components/
    │   │   ├── SalvadorMap.jsx  # Mapa Leaflet + heatmap de risco
    │   │   ├── AlertList.jsx    # Painel de alertas + análise situacional
    │   │   ├── PriorityPanel.jsx # Priorização da IA com justificativa
    │   │   └── Dossier.jsx      # Dossiê completo do bairro
    │   ├── services/
    │   │   └── api.js
    │   └── data/
    │       └── neighborhoods.geojson  # 163 polígonos de Salvador (WGS84)
    └── public/
        ├── favicon.ico
        ├── logo-512.png
        └── logo-header.png
```

---

## Limitações Conhecidas

| Limitação | Contexto |
|-----------|---------|
| Risco uniforme por horizonte | O modelo usa features climáticas globais da cidade — a diferenciação por bairro vem exclusivamente do score de resiliência, não de microclima local |
| Dados socioeconômicos estáticos | Baseados em IBGE e estimativas históricas; não refletem mudanças após 2022 |
| Histórico de ocorrências sintético | Gerado a partir das características dos bairros; em produção seria integrado ao SAC 156 ou ao sistema de registro da CODESAL |
| Modelo treinado até 2021 | Eventos extremos de 2024–2025 não estão no conjunto de treino |

---

## Contexto de Desenvolvimento

Desenvolvido em **72 horas** durante a **BaIA Week 2026** — Hackathon LEÃO, UFBA.

**Trilha:** Inteligência Artificial aplicada a Gestão Pública

---

*"Salvador não precisa de sorte na próxima tempestade. Precisa de inteligência."*
