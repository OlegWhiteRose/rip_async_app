from django.urls import path
from . import views

urlpatterns = [
    # POST /api/calculate - запуск асинхронного расчёта CAVI
    path('calculate', views.CalculateCAVIView.as_view(), name='calculate_cavi'),
]
