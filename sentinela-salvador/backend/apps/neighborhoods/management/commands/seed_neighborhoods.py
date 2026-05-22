from django.core.management.base import BaseCommand
from apps.neighborhoods.models import Neighborhood

# Names match exactly the GeoJSON "nome" property from Bairros_Salvador.json
NEIGHBORHOODS = [
    # Subúrbio Ferroviário — alta vulnerabilidade
    {"name": "Paripe",           "lat": -12.8277, "lon": -38.4680, "resilience_score": 16, "slope_risk": True,  "drainage_quality": "poor",   "income_level": "low",    "historical_events": 7, "slope_percentage": 38, "elevation_mean": 46.0, "pop_density": 18500, "pct_sem_esgoto": 52.0},
    {"name": "Periperi",         "lat": -12.8620, "lon": -38.4645, "resilience_score": 18, "slope_risk": True,  "drainage_quality": "poor",   "income_level": "low",    "historical_events": 8, "slope_percentage": 42, "elevation_mean": 53.0, "pop_density": 21000, "pct_sem_esgoto": 55.0},
    {"name": "Plataforma",       "lat": -12.9007, "lon": -38.4727, "resilience_score": 20, "slope_risk": True,  "drainage_quality": "poor",   "income_level": "low",    "historical_events": 6, "slope_percentage": 35, "elevation_mean": 38.0, "pop_density": 17500, "pct_sem_esgoto": 48.0},
    {"name": "Praia Grande",     "lat": -12.8721, "lon": -38.4747, "resilience_score": 22, "slope_risk": True,  "drainage_quality": "poor",   "income_level": "low",    "historical_events": 5, "slope_percentage": 30, "elevation_mean": 55.0, "pop_density": 16000, "pct_sem_esgoto": 45.0},
    {"name": "Palestina",        "lat": -12.8687, "lon": -38.4145, "resilience_score": 20, "slope_risk": False, "drainage_quality": "poor",   "income_level": "low",    "historical_events": 5, "slope_percentage": 15, "elevation_mean": 25.0, "pop_density": 15000, "pct_sem_esgoto": 47.0},
    {"name": "Rio Sena",         "lat": -12.8786, "lon": -38.4647, "resilience_score": 19, "slope_risk": True,  "drainage_quality": "poor",   "income_level": "low",    "historical_events": 6, "slope_percentage": 32, "elevation_mean": 48.0, "pop_density": 19000, "pct_sem_esgoto": 50.0},
    # Miolo e bairros populares — vulnerabilidade média-alta
    {"name": "Pau Miúdo",        "lat": -12.9595, "lon": -38.4773, "resilience_score": 25, "slope_risk": True,  "drainage_quality": "poor",   "income_level": "low",    "historical_events": 5, "slope_percentage": 28, "elevation_mean": 62.0, "pop_density": 22000, "pct_sem_esgoto": 42.0},
    {"name": "Pero Vaz",         "lat": -12.9525, "lon": -38.4878, "resilience_score": 26, "slope_risk": True,  "drainage_quality": "poor",   "income_level": "low",    "historical_events": 5, "slope_percentage": 30, "elevation_mean": 58.0, "pop_density": 20500, "pct_sem_esgoto": 40.0},
    {"name": "Retiro",           "lat": -12.9575, "lon": -38.4713, "resilience_score": 28, "slope_risk": False, "drainage_quality": "poor",   "income_level": "low",    "historical_events": 4, "slope_percentage": 12, "elevation_mean": 35.0, "pop_density": 14000, "pct_sem_esgoto": 38.0},
    {"name": "Resgate",          "lat": -12.9645, "lon": -38.4583, "resilience_score": 27, "slope_risk": False, "drainage_quality": "poor",   "income_level": "low",    "historical_events": 4, "slope_percentage": 10, "elevation_mean": 28.0, "pop_density": 13500, "pct_sem_esgoto": 36.0},
    {"name": "Pernambués",       "lat": -12.9723, "lon": -38.4700, "resilience_score": 30, "slope_risk": False, "drainage_quality": "medium", "income_level": "low",    "historical_events": 4, "slope_percentage":  8, "elevation_mean": 32.0, "pop_density": 12000, "pct_sem_esgoto": 32.0},
    {"name": "Saramandaia",      "lat": -13.0149, "lon": -38.4544, "resilience_score": 32, "slope_risk": True,  "drainage_quality": "poor",   "income_level": "low",    "historical_events": 5, "slope_percentage": 25, "elevation_mean": 68.0, "pop_density": 16500, "pct_sem_esgoto": 39.0},
    {"name": "Sete de Abril",    "lat": -12.8993, "lon": -38.3879, "resilience_score": 30, "slope_risk": True,  "drainage_quality": "poor",   "income_level": "low",    "historical_events": 4, "slope_percentage": 22, "elevation_mean": 44.0, "pop_density": 14500, "pct_sem_esgoto": 37.0},
    # Bairros de transição — vulnerabilidade média
    {"name": "Pirajá",           "lat": -12.9027, "lon": -38.4535, "resilience_score": 35, "slope_risk": False, "drainage_quality": "medium", "income_level": "low",    "historical_events": 3, "slope_percentage": 10, "elevation_mean": 38.0, "pop_density": 10500, "pct_sem_esgoto": 28.0},
    {"name": "Porto Seco Pirajá","lat": -12.9073, "lon": -38.4493, "resilience_score": 36, "slope_risk": False, "drainage_quality": "medium", "income_level": "low",    "historical_events": 3, "slope_percentage":  8, "elevation_mean": 35.0, "pop_density": 9800,  "pct_sem_esgoto": 26.0},
    {"name": "Pau da Lima",      "lat": -12.9219, "lon": -38.4350, "resilience_score": 38, "slope_risk": False, "drainage_quality": "medium", "income_level": "low",    "historical_events": 3, "slope_percentage": 10, "elevation_mean": 42.0, "pop_density": 11000, "pct_sem_esgoto": 24.0},
    {"name": "Tancredo Neves",   "lat": -12.9563, "lon": -38.4108, "resilience_score": 40, "slope_risk": False, "drainage_quality": "medium", "income_level": "medium", "historical_events": 3, "slope_percentage":  8, "elevation_mean": 30.0, "pop_density": 9000,  "pct_sem_esgoto": 20.0},
    {"name": "Sussuarana",       "lat": -12.9398, "lon": -38.4068, "resilience_score": 42, "slope_risk": False, "drainage_quality": "medium", "income_level": "medium", "historical_events": 2, "slope_percentage":  6, "elevation_mean": 35.0, "pop_density": 8500,  "pct_sem_esgoto": 18.0},
    {"name": "Vila Matos",       "lat": -12.9155, "lon": -38.4352, "resilience_score": 44, "slope_risk": False, "drainage_quality": "medium", "income_level": "medium", "historical_events": 2, "slope_percentage":  5, "elevation_mean": 38.0, "pop_density": 8000,  "pct_sem_esgoto": 17.0},
    {"name": "Tororó",           "lat": -12.9234, "lon": -38.3828, "resilience_score": 50, "slope_risk": False, "drainage_quality": "medium", "income_level": "medium", "historical_events": 2, "slope_percentage":  5, "elevation_mean": 48.0, "pop_density": 7500,  "pct_sem_esgoto": 14.0},
    {"name": "Uruguaia",         "lat": -12.9402, "lon": -38.3926, "resilience_score": 48, "slope_risk": False, "drainage_quality": "medium", "income_level": "medium", "historical_events": 2, "slope_percentage":  6, "elevation_mean": 42.0, "pop_density": 7000,  "pct_sem_esgoto": 15.0},
    {"name": "Ribeira",          "lat": -12.9208, "lon": -38.4965, "resilience_score": 55, "slope_risk": False, "drainage_quality": "medium", "income_level": "medium", "historical_events": 2, "slope_percentage":  5, "elevation_mean": 12.0, "pop_density": 6500,  "pct_sem_esgoto": 12.0},
    {"name": "Sacramenta",       "lat": -13.0055, "lon": -38.4864, "resilience_score": 58, "slope_risk": False, "drainage_quality": "medium", "income_level": "medium", "historical_events": 1, "slope_percentage":  3, "elevation_mean": 25.0, "pop_density": 6000,  "pct_sem_esgoto": 10.0},
    # Orla e bairros nobres — baixa vulnerabilidade
    {"name": "Pituaçu",          "lat": -12.9645, "lon": -38.4013, "resilience_score": 65, "slope_risk": False, "drainage_quality": "good",   "income_level": "medium", "historical_events": 1, "slope_percentage":  3, "elevation_mean": 22.0, "pop_density": 5500,  "pct_sem_esgoto":  7.0},
    {"name": "Patamares",        "lat": -12.9645, "lon": -38.4013, "resilience_score": 68, "slope_risk": False, "drainage_quality": "good",   "income_level": "medium", "historical_events": 1, "slope_percentage":  2, "elevation_mean": 18.0, "pop_density": 5000,  "pct_sem_esgoto":  6.0},
    {"name": "Piatã",            "lat": -12.9368, "lon": -38.3741, "resilience_score": 74, "slope_risk": False, "drainage_quality": "good",   "income_level": "high",   "historical_events": 1, "slope_percentage":  2, "elevation_mean": 10.0, "pop_density": 4500,  "pct_sem_esgoto":  4.0},
    {"name": "Pituba",           "lat": -12.9838, "lon": -38.4514, "resilience_score": 78, "slope_risk": False, "drainage_quality": "good",   "income_level": "high",   "historical_events": 1, "slope_percentage":  2, "elevation_mean":  8.0, "pop_density": 4200,  "pct_sem_esgoto":  3.0},
]

class Command(BaseCommand):
    help = 'Seed neighborhoods with resilience and census data'

    def handle(self, *args, **options):
        Neighborhood.objects.all().delete()
        for data in NEIGHBORHOODS:
            Neighborhood.objects.create(**data)
        self.stdout.write(self.style.SUCCESS(f'Seeded {len(NEIGHBORHOODS)} neighborhoods'))
