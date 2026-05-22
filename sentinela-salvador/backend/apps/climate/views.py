from rest_framework.views import APIView
from rest_framework.response import Response
from apps.climate.services.data_loader import get_current_climate_snapshot

class CurrentClimateView(APIView):
    def get(self, request):
        reference_date = request.query_params.get('date', '2016-01-17')
        data = get_current_climate_snapshot(reference_date)
        return Response(data)
