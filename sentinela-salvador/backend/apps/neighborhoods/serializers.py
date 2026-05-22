from rest_framework import serializers
from .models import Neighborhood

class NeighborhoodSerializer(serializers.ModelSerializer):
    risk_label = serializers.SerializerMethodField()
    risk_color = serializers.SerializerMethodField()

    class Meta:
        model = Neighborhood
        fields = [
            'id', 'name', 'lat', 'lon', 'resilience_score',
            'current_risk_level', 'current_risk_probability',
            'current_precip_6h', 'risk_label', 'risk_color',
            'elevation_mean', 'pop_density', 'pct_sem_esgoto',
            'slope_percentage', 'drainage_quality', 'income_level',
            'historical_events',
        ]

    def get_risk_label(self, obj):
        return obj.risk_label()

    def get_risk_color(self, obj):
        return obj.risk_color()
