"""
Seed all 163 neighborhoods from the GeoJSON.
Hand-crafted data for the 27 most important ones;
deterministic mock for the rest (based on name hash).
"""
import json, hashlib
from pathlib import Path
from django.core.management.base import BaseCommand
from apps.neighborhoods.models import Neighborhood

GEOJSON_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent.parent.parent
    / 'frontend' / 'src' / 'data' / 'neighborhoods.geojson'
)

# Hand-crafted data keyed by GeoJSON "nome" property
CURATED = {
    "Paripe":                {"resilience_score": 16, "slope_risk": True,  "drainage_quality": "poor",   "income_level": "low",    "historical_events": 7, "slope_percentage": 38, "elevation_mean": 46, "pop_density": 18500, "pct_sem_esgoto": 52},
    "Periperi":              {"resilience_score": 18, "slope_risk": True,  "drainage_quality": "poor",   "income_level": "low",    "historical_events": 8, "slope_percentage": 42, "elevation_mean": 53, "pop_density": 21000, "pct_sem_esgoto": 55},
    "Plataforma":            {"resilience_score": 20, "slope_risk": True,  "drainage_quality": "poor",   "income_level": "low",    "historical_events": 6, "slope_percentage": 35, "elevation_mean": 38, "pop_density": 17500, "pct_sem_esgoto": 48},
    "Praia Grande":          {"resilience_score": 22, "slope_risk": True,  "drainage_quality": "poor",   "income_level": "low",    "historical_events": 5, "slope_percentage": 30, "elevation_mean": 55, "pop_density": 16000, "pct_sem_esgoto": 45},
    "Palestina":             {"resilience_score": 20, "slope_risk": False, "drainage_quality": "poor",   "income_level": "low",    "historical_events": 5, "slope_percentage": 15, "elevation_mean": 25, "pop_density": 15000, "pct_sem_esgoto": 47},
    "Rio Sena":              {"resilience_score": 19, "slope_risk": True,  "drainage_quality": "poor",   "income_level": "low",    "historical_events": 6, "slope_percentage": 32, "elevation_mean": 48, "pop_density": 19000, "pct_sem_esgoto": 50},
    "Pau Miúdo":             {"resilience_score": 25, "slope_risk": True,  "drainage_quality": "poor",   "income_level": "low",    "historical_events": 5, "slope_percentage": 28, "elevation_mean": 62, "pop_density": 22000, "pct_sem_esgoto": 42},
    "Pero Vaz":              {"resilience_score": 26, "slope_risk": True,  "drainage_quality": "poor",   "income_level": "low",    "historical_events": 5, "slope_percentage": 30, "elevation_mean": 58, "pop_density": 20500, "pct_sem_esgoto": 40},
    "Retiro":                {"resilience_score": 28, "slope_risk": False, "drainage_quality": "poor",   "income_level": "low",    "historical_events": 4, "slope_percentage": 12, "elevation_mean": 35, "pop_density": 14000, "pct_sem_esgoto": 38},
    "Resgate":               {"resilience_score": 27, "slope_risk": False, "drainage_quality": "poor",   "income_level": "low",    "historical_events": 4, "slope_percentage": 10, "elevation_mean": 28, "pop_density": 13500, "pct_sem_esgoto": 36},
    "Pernambués":            {"resilience_score": 30, "slope_risk": False, "drainage_quality": "medium", "income_level": "low",    "historical_events": 4, "slope_percentage":  8, "elevation_mean": 32, "pop_density": 12000, "pct_sem_esgoto": 32},
    "Saramandaia":           {"resilience_score": 32, "slope_risk": True,  "drainage_quality": "poor",   "income_level": "low",    "historical_events": 5, "slope_percentage": 25, "elevation_mean": 68, "pop_density": 16500, "pct_sem_esgoto": 39},
    "Sete de Abril":         {"resilience_score": 30, "slope_risk": True,  "drainage_quality": "poor",   "income_level": "low",    "historical_events": 4, "slope_percentage": 22, "elevation_mean": 44, "pop_density": 14500, "pct_sem_esgoto": 37},
    "Pirajá":                {"resilience_score": 35, "slope_risk": False, "drainage_quality": "medium", "income_level": "low",    "historical_events": 3, "slope_percentage": 10, "elevation_mean": 38, "pop_density": 10500, "pct_sem_esgoto": 28},
    "Porto Seco Pirajá":     {"resilience_score": 36, "slope_risk": False, "drainage_quality": "medium", "income_level": "low",    "historical_events": 3, "slope_percentage":  8, "elevation_mean": 35, "pop_density":  9800, "pct_sem_esgoto": 26},
    "Pau da Lima":           {"resilience_score": 38, "slope_risk": False, "drainage_quality": "medium", "income_level": "low",    "historical_events": 3, "slope_percentage": 10, "elevation_mean": 42, "pop_density": 11000, "pct_sem_esgoto": 24},
    "Beiru/Tancredo Neves":  {"resilience_score": 40, "slope_risk": False, "drainage_quality": "medium", "income_level": "medium", "historical_events": 3, "slope_percentage":  8, "elevation_mean": 30, "pop_density":  9000, "pct_sem_esgoto": 20},
    "Sussuarana":            {"resilience_score": 42, "slope_risk": False, "drainage_quality": "medium", "income_level": "medium", "historical_events": 2, "slope_percentage":  6, "elevation_mean": 35, "pop_density":  8500, "pct_sem_esgoto": 18},
    "Tororó":                {"resilience_score": 50, "slope_risk": False, "drainage_quality": "medium", "income_level": "medium", "historical_events": 2, "slope_percentage":  5, "elevation_mean": 48, "pop_density":  7500, "pct_sem_esgoto": 14},
    "Uruguai":               {"resilience_score": 48, "slope_risk": False, "drainage_quality": "medium", "income_level": "medium", "historical_events": 2, "slope_percentage":  6, "elevation_mean": 42, "pop_density":  7000, "pct_sem_esgoto": 15},
    "Ribeira":               {"resilience_score": 55, "slope_risk": False, "drainage_quality": "medium", "income_level": "medium", "historical_events": 2, "slope_percentage":  5, "elevation_mean": 12, "pop_density":  6500, "pct_sem_esgoto": 12},
    "Pituaçu":               {"resilience_score": 65, "slope_risk": False, "drainage_quality": "good",   "income_level": "medium", "historical_events": 1, "slope_percentage":  3, "elevation_mean": 22, "pop_density":  5500, "pct_sem_esgoto":  7},
    "Patamares":             {"resilience_score": 68, "slope_risk": False, "drainage_quality": "good",   "income_level": "medium", "historical_events": 1, "slope_percentage":  2, "elevation_mean": 18, "pop_density":  5000, "pct_sem_esgoto":  6},
    "Piatã":                 {"resilience_score": 74, "slope_risk": False, "drainage_quality": "good",   "income_level": "high",   "historical_events": 1, "slope_percentage":  2, "elevation_mean": 10, "pop_density":  4500, "pct_sem_esgoto":  4},
    "Pituba":                {"resilience_score": 78, "slope_risk": False, "drainage_quality": "good",   "income_level": "high",   "historical_events": 1, "slope_percentage":  2, "elevation_mean":  8, "pop_density":  4200, "pct_sem_esgoto":  3},
    # Nobres / orla
    "Barra":                 {"resilience_score": 76, "slope_risk": False, "drainage_quality": "good",   "income_level": "high",   "historical_events": 1, "slope_percentage":  2, "elevation_mean": 14, "pop_density":  5000, "pct_sem_esgoto":  3},
    "Graça":                 {"resilience_score": 72, "slope_risk": False, "drainage_quality": "good",   "income_level": "high",   "historical_events": 1, "slope_percentage":  3, "elevation_mean": 18, "pop_density":  4800, "pct_sem_esgoto":  4},
    "Ondina":                {"resilience_score": 70, "slope_risk": False, "drainage_quality": "good",   "income_level": "high",   "historical_events": 1, "slope_percentage":  4, "elevation_mean": 16, "pop_density":  5200, "pct_sem_esgoto":  5},
    "Rio Vermelho":          {"resilience_score": 68, "slope_risk": False, "drainage_quality": "good",   "income_level": "high",   "historical_events": 1, "slope_percentage":  3, "elevation_mean": 12, "pop_density":  5800, "pct_sem_esgoto":  5},
    "Itaigara":              {"resilience_score": 75, "slope_risk": False, "drainage_quality": "good",   "income_level": "high",   "historical_events": 1, "slope_percentage":  2, "elevation_mean": 10, "pop_density":  4000, "pct_sem_esgoto":  3},
    "Stella Maris":          {"resilience_score": 72, "slope_risk": False, "drainage_quality": "good",   "income_level": "high",   "historical_events": 1, "slope_percentage":  2, "elevation_mean":  9, "pop_density":  3800, "pct_sem_esgoto":  4},
    "Costa Azul":            {"resilience_score": 70, "slope_risk": False, "drainage_quality": "good",   "income_level": "high",   "historical_events": 1, "slope_percentage":  2, "elevation_mean": 11, "pop_density":  4200, "pct_sem_esgoto":  4},
    "Itapuã":                {"resilience_score": 65, "slope_risk": False, "drainage_quality": "good",   "income_level": "medium", "historical_events": 1, "slope_percentage":  3, "elevation_mean":  8, "pop_density":  5000, "pct_sem_esgoto":  6},
    "Boca do Rio":           {"resilience_score": 60, "slope_risk": False, "drainage_quality": "good",   "income_level": "medium", "historical_events": 1, "slope_percentage":  3, "elevation_mean": 10, "pop_density":  5500, "pct_sem_esgoto":  7},
    # Populares / vulneráveis
    "Liberdade":             {"resilience_score": 24, "slope_risk": True,  "drainage_quality": "poor",   "income_level": "low",    "historical_events": 6, "slope_percentage": 35, "elevation_mean": 60, "pop_density": 25000, "pct_sem_esgoto": 38},
    "Nordeste de Amaralina": {"resilience_score": 22, "slope_risk": True,  "drainage_quality": "poor",   "income_level": "low",    "historical_events": 5, "slope_percentage": 30, "elevation_mean": 45, "pop_density": 22000, "pct_sem_esgoto": 42},
    "Federação":             {"resilience_score": 28, "slope_risk": True,  "drainage_quality": "poor",   "income_level": "low",    "historical_events": 4, "slope_percentage": 25, "elevation_mean": 55, "pop_density": 18000, "pct_sem_esgoto": 35},
    "Brotas":                {"resilience_score": 45, "slope_risk": False, "drainage_quality": "medium", "income_level": "medium", "historical_events": 2, "slope_percentage":  8, "elevation_mean": 40, "pop_density":  9000, "pct_sem_esgoto": 16},
    "Cabula":                {"resilience_score": 38, "slope_risk": False, "drainage_quality": "medium", "income_level": "low",    "historical_events": 3, "slope_percentage": 10, "elevation_mean": 45, "pop_density": 11000, "pct_sem_esgoto": 25},
    "Cajazeiras IV":         {"resilience_score": 32, "slope_risk": False, "drainage_quality": "medium", "income_level": "low",    "historical_events": 3, "slope_percentage":  8, "elevation_mean": 36, "pop_density": 13000, "pct_sem_esgoto": 30},
    "Cajazeiras VIII":       {"resilience_score": 30, "slope_risk": True,  "drainage_quality": "poor",   "income_level": "low",    "historical_events": 4, "slope_percentage": 18, "elevation_mean": 42, "pop_density": 14000, "pct_sem_esgoto": 35},
    "Cajazeiras XI":         {"resilience_score": 28, "slope_risk": True,  "drainage_quality": "poor",   "income_level": "low",    "historical_events": 4, "slope_percentage": 20, "elevation_mean": 44, "pop_density": 15000, "pct_sem_esgoto": 38},
    "Fazenda Grande I":      {"resilience_score": 26, "slope_risk": True,  "drainage_quality": "poor",   "income_level": "low",    "historical_events": 5, "slope_percentage": 22, "elevation_mean": 40, "pop_density": 16000, "pct_sem_esgoto": 42},
    "Fazenda Grande II":     {"resilience_score": 27, "slope_risk": True,  "drainage_quality": "poor",   "income_level": "low",    "historical_events": 4, "slope_percentage": 20, "elevation_mean": 38, "pop_density": 15500, "pct_sem_esgoto": 40},
    "Mata Escura":           {"resilience_score": 24, "slope_risk": True,  "drainage_quality": "poor",   "income_level": "low",    "historical_events": 6, "slope_percentage": 32, "elevation_mean": 52, "pop_density": 17000, "pct_sem_esgoto": 45},
    "Bairro da Paz":         {"resilience_score": 21, "slope_risk": True,  "drainage_quality": "poor",   "income_level": "low",    "historical_events": 5, "slope_percentage": 28, "elevation_mean": 48, "pop_density": 20000, "pct_sem_esgoto": 48},
    "IAPI":                  {"resilience_score": 33, "slope_risk": False, "drainage_quality": "medium", "income_level": "low",    "historical_events": 3, "slope_percentage": 10, "elevation_mean": 30, "pop_density": 12000, "pct_sem_esgoto": 29},
    "Lobato":                {"resilience_score": 23, "slope_risk": True,  "drainage_quality": "poor",   "income_level": "low",    "historical_events": 5, "slope_percentage": 26, "elevation_mean": 44, "pop_density": 18000, "pct_sem_esgoto": 46},
    "Coutos":                {"resilience_score": 21, "slope_risk": False, "drainage_quality": "poor",   "income_level": "low",    "historical_events": 5, "slope_percentage": 12, "elevation_mean": 22, "pop_density": 16000, "pct_sem_esgoto": 50},
    "Alto do Cabrito":       {"resilience_score": 18, "slope_risk": True,  "drainage_quality": "poor",   "income_level": "low",    "historical_events": 7, "slope_percentage": 40, "elevation_mean": 65, "pop_density": 19000, "pct_sem_esgoto": 54},
}


def _compute_centroid(geometry):
    """Average lat/lon from the largest ring."""
    def flatten(coords):
        while coords and isinstance(coords[0][0], list):
            coords = coords[0]
        return coords

    gtype = geometry.get('type', '')
    try:
        if gtype == 'Polygon':
            ring = flatten(geometry['coordinates'])
        elif gtype == 'MultiPolygon':
            rings = [flatten(p) for p in geometry['coordinates']]
            ring = max(rings, key=len)
        else:
            return None, None
        lats = [c[1] for c in ring]
        lons = [c[0] for c in ring]
        return sum(lats) / len(lats), sum(lons) / len(lons)
    except Exception:
        return None, None


def _mock_data(name):
    """Deterministic but varied mock data based on name hash."""
    h = int(hashlib.md5(name.encode('utf-8')).hexdigest(), 16)
    score = 28 + (h % 45)           # 28–73
    slope = (h % 5) == 0
    drainage = ['poor', 'poor', 'medium', 'medium', 'good'][h % 5]
    income   = ['low', 'low', 'low', 'medium', 'medium'][h % 5]
    hist     = 1 + (h % 5)
    slope_p  = 5 + (h % 28)
    elev     = 10 + (h % 60)
    dens     = 4500 + (h % 16000)
    esgoto   = 8 + (h % 45)
    return {
        'resilience_score': score,
        'slope_risk': slope,
        'drainage_quality': drainage,
        'income_level': income,
        'historical_events': hist,
        'slope_percentage': slope_p,
        'elevation_mean': float(elev),
        'pop_density': float(dens),
        'pct_sem_esgoto': float(esgoto),
    }


class Command(BaseCommand):
    help = 'Seed all GeoJSON neighborhoods with curated + mock data'

    def handle(self, *args, **options):
        if not GEOJSON_PATH.exists():
            self.stdout.write(self.style.ERROR(f'GeoJSON not found: {GEOJSON_PATH}'))
            return

        with open(GEOJSON_PATH, encoding='utf-8') as f:
            geojson = json.load(f)

        Neighborhood.objects.all().delete()
        count = 0
        skipped = 0

        for feature in geojson['features']:
            nome = feature['properties'].get('nome', '').strip()
            if not nome:
                skipped += 1
                continue

            lat, lon = _compute_centroid(feature['geometry'])
            if lat is None:
                skipped += 1
                continue

            extra = CURATED.get(nome) or _mock_data(nome)
            Neighborhood.objects.create(
                name=nome,
                lat=round(lat, 6),
                lon=round(lon, 6),
                **extra,
            )
            count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Seeded {count} neighborhoods ({skipped} skipped). '
                f'{len(CURATED)} curated, {count - len([n for n in CURATED if any(f["properties"].get("nome") == n for f in geojson["features"])])} auto-mocked.'
            )
        )
