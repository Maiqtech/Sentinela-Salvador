from django.urls import path, include

urlpatterns = [
    path('api/neighborhoods/', include('apps.neighborhoods.urls')),
    path('api/climate/', include('apps.climate.urls')),
]
