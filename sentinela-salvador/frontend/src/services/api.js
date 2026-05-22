import axios from 'axios'

const BASE = '/api'

export const fetchNeighborhoods = (date = '2016-01-17') =>
  axios.get(`${BASE}/neighborhoods/?date=${date}`).then(r => r.data)

export const fetchForecast = () =>
  axios.get(`${BASE}/neighborhoods/forecast/`).then(r => r.data)

export const fetchDossier = (id, { horizon, precip_mm, hours } = {}) => {
  const params = precip_mm != null
    ? `precip_mm=${precip_mm}&hours=${hours ?? 6}`
    : `horizon=${horizon ?? 'now'}`
  return axios.get(`${BASE}/neighborhoods/${id}/dossier/?${params}`).then(r => r.data)
}

export const simulateRain = (precip_mm, hours) =>
  axios.post(`${BASE}/neighborhoods/simulate/`, { precip_mm, hours }).then(r => r.data)

export const fetchInsights = () =>
  axios.get(`${BASE}/neighborhoods/insights/`).then(r => r.data)

export const fetchCurrentClimate = (date = '2016-01-17') =>
  axios.get(`${BASE}/climate/current/?date=${date}`).then(r => r.data)
