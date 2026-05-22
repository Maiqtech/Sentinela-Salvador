from django.db import models

class Neighborhood(models.Model):
    name = models.CharField(max_length=100)
    lat = models.FloatField()
    lon = models.FloatField()
    resilience_score = models.IntegerField()  # 0-100
    slope_risk = models.BooleanField(default=False)
    drainage_quality = models.CharField(max_length=20)  # poor/medium/good
    income_level = models.CharField(max_length=20)  # low/medium/high
    historical_events = models.IntegerField(default=0)
    slope_percentage = models.IntegerField(default=0)
    # Census / topography enrichment
    elevation_mean = models.FloatField(default=30.0)   # mean elevation (m)
    pop_density = models.FloatField(default=6000.0)    # people per km²
    pct_sem_esgoto = models.FloatField(default=30.0)   # % households without sewage

    RISK_LOW = 0
    RISK_MEDIUM = 1
    RISK_HIGH = 2
    RISK_CRITICAL = 3

    current_risk_level = models.IntegerField(default=0)
    current_risk_probability = models.FloatField(default=0.0)
    current_precip_6h = models.FloatField(default=0.0)
    current_pressure_trend = models.FloatField(default=0.0)
    current_humidity = models.FloatField(default=0.0)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def risk_label(self):
        labels = {0: 'Baixo', 1: 'Médio', 2: 'Alto', 3: 'Crítico'}
        return labels[self.current_risk_level]

    def risk_color(self):
        colors = {0: '#22c55e', 1: '#eab308', 2: '#f97316', 3: '#ef4444'}
        return colors[self.current_risk_level]
