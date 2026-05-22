from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Neighborhood
from .serializers import NeighborhoodSerializer
from apps.climate.services.data_loader import get_current_climate_snapshot, simulate_climate_snapshot
from apps.climate.services.predictor import predict_risk
from apps.climate.services.alert_generator import generate_alert, generate_dossier_text, generate_priority_list, generate_historical_insights
from apps.climate.services.weather_service import get_forecast_snapshots, HORIZONS


def _adjusted_risk(prediction, resilience_score):
    """
    ML risk level adjusted by neighborhood resilience score.
    Low resilience escalates risk one level; high resilience absorbs one level.
    """
    base_risk = prediction['risk_level']
    base_prob = prediction['probability']

    if resilience_score < 35 and base_risk >= 1:
        # Vulnerable neighborhood: escalate one level
        adjusted_risk = min(base_risk + 1, 3)
        adj_prob = min(base_prob + (35 - resilience_score) * 0.4, 99.0)
    elif resilience_score >= 70 and base_risk >= 1:
        # Resilient neighborhood: absorb one risk level
        adjusted_risk = max(base_risk - 1, 0)
        adj_prob = max(base_prob - (resilience_score - 70) * 0.4, 5.0)
    else:
        adjusted_risk = base_risk
        adj_prob = base_prob

    return adjusted_risk, round(adj_prob, 1)


class NeighborhoodListView(APIView):
    def get(self, request):
        reference_date = request.query_params.get('date', '2016-01-17')
        try:
            climate = get_current_climate_snapshot(reference_date)
            prediction = predict_risk(climate)
            neighborhoods = Neighborhood.objects.all()
            for n in neighborhoods:
                risk, adj_prob = _adjusted_risk(prediction, n.resilience_score)
                n.current_risk_level = risk
                n.current_risk_probability = adj_prob
                n.current_precip_6h = climate['precip_6h']
                n.current_pressure_trend = climate['pressure_trend']
                n.current_humidity = climate['humidity']
            Neighborhood.objects.bulk_update(
                neighborhoods,
                ['current_risk_level', 'current_risk_probability', 'current_precip_6h',
                 'current_pressure_trend', 'current_humidity']
            )
            serializer = NeighborhoodSerializer(neighborhoods, many=True)
            at_risk = sorted(
                [n for n in neighborhoods if n.current_risk_level >= 1],
                key=lambda x: (-x.current_risk_level, x.resilience_score)
            )[:8]
            alerts = [
                {
                    'id': n.id,
                    'name': n.name,
                    'risk_level': n.current_risk_level,
                    'risk_label': n.risk_label(),
                    'risk_color': n.risk_color(),
                    'probability': round(n.current_risk_probability, 1),
                    'resilience_score': n.resilience_score,
                    'message': generate_alert(n, climate, {'risk_level': n.current_risk_level, 'probability': n.current_risk_probability}),
                }
                for n in at_risk
            ]
            return Response({
                'neighborhoods': serializer.data,
                'climate_snapshot': climate,
                'alerts': alerts,
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class NeighborhoodDossierView(APIView):
    def get(self, request, pk):
        try:
            neighborhood = Neighborhood.objects.get(pk=pk)
            precip_mm = request.query_params.get('precip_mm')
            hours = request.query_params.get('hours')
            horizon_key = request.query_params.get('horizon')
            if precip_mm is not None:
                climate = simulate_climate_snapshot(float(precip_mm), int(hours or 6))
            elif horizon_key:
                snapshots = get_forecast_snapshots()
                horizon_map = {h['key']: i for i, h in enumerate(HORIZONS)}
                idx = horizon_map.get(horizon_key, 0)
                climate = snapshots[idx]
            else:
                reference_date = request.query_params.get('date', '2016-01-17')
                climate = get_current_climate_snapshot(reference_date)
            prediction = predict_risk(climate)
            risk_level, adj_prob = _adjusted_risk(prediction, neighborhood.resilience_score)
            prediction['risk_level'] = risk_level
            prediction['probability'] = adj_prob
            alert = generate_alert(neighborhood, climate, prediction)
            dossier = generate_dossier_text(neighborhood, climate, prediction)
            serializer = NeighborhoodSerializer(neighborhood)
            return Response({
                'neighborhood': serializer.data,
                'alert': alert,
                'dossier': dossier,
                'climate': climate,
                'prediction': prediction,
            })
        except Neighborhood.DoesNotExist:
            return Response({'error': 'Neighborhood not found'}, status=404)


class SimulateView(APIView):
    def post(self, request):
        precip_mm = float(request.data.get('precip_mm', 80))
        hours = int(request.data.get('hours', 6))
        climate = simulate_climate_snapshot(precip_mm, hours)
        prediction = predict_risk(climate)
        neighborhoods = list(Neighborhood.objects.all())
        nb_map = {n.id: n for n in neighborhoods}
        results = []
        for n in neighborhoods:
            risk, adj_prob = _adjusted_risk(prediction, n.resilience_score)
            pred = {'risk_level': risk, 'probability': adj_prob}
            results.append({
                'id': n.id,
                'name': n.name,
                'risk_level': risk,
                'risk_label': RISK_LABELS_MAP[risk],
                'risk_color': RISK_COLORS_MAP[risk],
                'probability': adj_prob,
                'resilience_score': n.resilience_score,
                'message': generate_alert(n, climate, pred) if risk >= 1 else None,
            })
        # Sort: highest risk first; within same risk, most vulnerable (lowest resilience) first
        results.sort(key=lambda x: (-x['risk_level'], x['resilience_score'], -x['probability']))
        ranked = [dict(r, obj=nb_map[r['id']]) for r in results if r['risk_level'] >= 1][:8]
        priority = generate_priority_list(ranked)
        return Response({'simulation': results, 'climate_input': climate, 'priority': priority})


RISK_LABELS_MAP = {0: 'Baixo', 1: 'Médio', 2: 'Alto', 3: 'Crítico'}
RISK_COLORS_MAP = {0: '#22c55e', 1: '#eab308', 2: '#f97316', 3: '#ef4444'}


class InsightsView(APIView):
    def get(self, request):
        neighborhoods = list(
            Neighborhood.objects.filter(historical_events__gte=1)
            .order_by('-historical_events', 'resilience_score')
        )[:12]
        insights = generate_historical_insights(neighborhoods)
        return Response({'insights': insights})


class ForecastView(APIView):
    def get(self, request):
        try:
            snapshots = get_forecast_snapshots()
            neighborhoods = list(Neighborhood.objects.all())
            forecast = []
            for horizon, climate in zip(HORIZONS, snapshots):
                prediction = predict_risk(climate)
                nh_list = []
                for n in neighborhoods:
                    risk, adj_prob = _adjusted_risk(prediction, n.resilience_score)
                    nh_list.append({
                        'id': n.id,
                        'name': n.name,
                        'risk_level': risk,
                        'risk_label': RISK_LABELS_MAP[risk],
                        'risk_color': RISK_COLORS_MAP[risk],
                        'probability': adj_prob,
                        'resilience_score': n.resilience_score,
                        'lat': n.lat,
                        'lon': n.lon,
                    })
                critical = [n for n in nh_list if n['risk_level'] >= 2]
                top_nb = min(critical, key=lambda x: x['resilience_score'], default=None)
                at_risk = sorted(
                    [n for n in nh_list if n['risk_level'] >= 1],
                    key=lambda x: (-x['risk_level'], x['resilience_score'])
                )[:8]
                alerts = [
                    {
                        'id': n['id'],
                        'name': n['name'],
                        'risk_level': n['risk_level'],
                        'risk_label': n['risk_label'],
                        'risk_color': n['risk_color'],
                        'probability': n['probability'],
                        'resilience_score': n['resilience_score'],
                    }
                    for n in at_risk
                ]
                nb_map = {n.id: n for n in neighborhoods}
                ranked = [dict(a, obj=nb_map[a['id']]) for a in at_risk]
                forecast.append({
                    'horizon': horizon['key'],
                    'label': horizon['label'],
                    'climate': climate,
                    'neighborhoods': nh_list,
                    'critical_count': len(critical),
                    'alerts': alerts,
                    'priority': generate_priority_list(ranked),
                })
            return Response({'forecast': forecast})
        except Exception as e:
            return Response({'error': str(e)}, status=500)
