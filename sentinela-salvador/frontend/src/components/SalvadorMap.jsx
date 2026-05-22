import { useEffect, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import 'leaflet.heat'
import geojsonData from '../data/neighborhoods.geojson'

const RISK_COLORS = { 0: '#22c55e', 1: '#eab308', 2: '#f97316', 3: '#ef4444' }
const RISK_LABELS = { 0: 'Baixo', 1: 'Médio', 2: 'Alto', 3: 'Crítico' }

export default function SalvadorMap({ neighborhoods, onNeighborhoodClick, simulationData }) {
  const mapRef = useRef(null)
  const mapInstance = useRef(null)
  const polyLayerRef = useRef(null)
  const heatLayerRef = useRef(null)
  const selectedLayerRef = useRef(null)

  useEffect(() => {
    if (mapInstance.current) return
    mapInstance.current = L.map(mapRef.current, {
      center: [-12.97, -38.49],
      zoom: 12,
      zoomControl: true,
    })
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap',
      opacity: 0.35,
    }).addTo(mapInstance.current)

    const ro = new ResizeObserver(() => mapInstance.current?.invalidateSize())
    ro.observe(mapRef.current)
    return () => ro.disconnect()
  }, [])

  useEffect(() => {
    if (!mapInstance.current || !neighborhoods.length) return

    const dataSource = simulationData || neighborhoods
    const riskMap = {}
    dataSource.forEach(n => {
      const riskLevel = n.risk_level ?? n.current_risk_level ?? 0
      riskMap[n.name] = {
        id: n.id,
        risk_level: riskLevel,
        risk_color: n.risk_color ?? RISK_COLORS[riskLevel],
        risk_label: n.risk_label ?? RISK_LABELS[riskLevel],
        probability: n.probability ?? n.current_risk_probability ?? 0,
        resilience_score: n.resilience_score,
      }
    })

    const baseStyle = (info) => ({
      fillColor: info?.risk_color ?? '#334155',
      fillOpacity: 0.55,
      color: '#0f172a',
      weight: 1.5,
    })

    const highlightStyle = (info) => ({
      fillColor: info?.risk_color ?? '#334155',
      fillOpacity: 0.85,
      color: '#ffffff',
      weight: 3,
    })

    selectedLayerRef.current = null

    if (polyLayerRef.current) polyLayerRef.current.remove()
    polyLayerRef.current = L.geoJSON(geojsonData, {
      style: feature => baseStyle(riskMap[feature.properties.nome]),
      onEachFeature: (feature, layer) => {
        const nome = feature.properties.nome
        const info = riskMap[nome]

        if (info) {
          layer.bindTooltip(
            `<b>${nome}</b><br/>Risco: ${info.risk_label}<br/>Prob: ${info.probability}%<br/>Score: ${info.resilience_score}/100`,
            { sticky: true }
          )
          layer.on('click', () => {
            // Reset previous selection
            if (selectedLayerRef.current && selectedLayerRef.current !== layer) {
              const prevNome = selectedLayerRef.current.feature.properties.nome
              selectedLayerRef.current.setStyle(baseStyle(riskMap[prevNome]))
            }
            // Highlight clicked polygon
            layer.setStyle(highlightStyle(info))
            layer.bringToFront()
            selectedLayerRef.current = layer
            onNeighborhoodClick(info.id)
          })
        } else {
          layer.bindTooltip(`<b>${nome}</b><br/><i>Sem dados</i>`, { sticky: true })
        }
      },
    }).addTo(mapInstance.current)

    // --- Heatmap layer ---
    if (heatLayerRef.current) heatLayerRef.current.remove()
    const heatPoints = neighborhoods
      .map(n => {
        const info = riskMap[n.name]
        const intensity = (info?.risk_level ?? 0) / 3
        return [n.lat, n.lon, intensity]
      })
      .filter(p => p[2] > 0)

    if (heatPoints.length > 0) {
      heatLayerRef.current = L.heatLayer(heatPoints, {
        radius: 55,
        blur: 45,
        maxZoom: 13,
        max: 1.0,
        gradient: {
          0.0: '#22c55e',
          0.35: '#eab308',
          0.65: '#f97316',
          1.0: '#ef4444',
        },
      }).addTo(mapInstance.current)
    }

  }, [neighborhoods, simulationData])

  return <div ref={mapRef} style={{ width: '100%', height: '100%' }} />
}
