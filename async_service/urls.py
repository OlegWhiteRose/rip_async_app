"""
URL configuration for async_service project.
"""
from django.urls import path, include

urlpatterns = [
    path('api/', include('cavi_calculator.urls')),
]
