from django.urls import path
from .views import CurrentClimateView

urlpatterns = [
    path('current/', CurrentClimateView.as_view()),
]
