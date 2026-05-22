from django.urls import path
from .views import NeighborhoodListView, NeighborhoodDossierView, SimulateView, ForecastView, InsightsView

urlpatterns = [
    path('', NeighborhoodListView.as_view()),
    path('forecast/', ForecastView.as_view()),
    path('insights/', InsightsView.as_view()),
    path('<int:pk>/dossier/', NeighborhoodDossierView.as_view()),
    path('simulate/', SimulateView.as_view()),
]
