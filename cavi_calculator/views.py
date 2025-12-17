"""
Views для асинхронного сервиса расчёта CAVI.
"""
import time
import random
import threading
import requests
import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

from .cavi_formula import calculate_cavi

logger = logging.getLogger(__name__)


class HealthCheckView(APIView):
    """Проверка работоспособности сервиса."""
    
    def get(self, request):
        return Response({
            'status': 'ok',
            'service': 'cavi-async-calculator',
            'version': '1.0.0'
        })


class CalculateCAVIView(APIView):
    """
    Асинхронный расчёт CAVI индекса.
    
    POST /api/calculate
    
    Принимает данные о заявке и группах, запускает расчёт в фоне
    с задержкой 5-10 секунд, затем отправляет результаты в Go бекенд.
    """
    
    def post(self, request):
        """
        Запуск асинхронного расчёта CAVI.
        
        Request body:
        {
            "calculation_id": 1,
            "systolic_pressure": 120,
            "diastolic_pressure": 80,
            "pulse_wave_velocity": 8.5,
            "groups": [
                {
                    "group_id": 1,
                    "age_group": "young",
                    "disease_type": null
                },
                ...
            ]
        }
        """
        data = request.data
        
        # Валидация входных данных
        required_fields = ['calculation_id', 'systolic_pressure', 'diastolic_pressure', 
                          'pulse_wave_velocity', 'groups']
        for field in required_fields:
            if field not in data:
                return Response(
                    {'status': 'error', 'message': f'Missing required field: {field}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        calculation_id = data['calculation_id']
        systolic = data['systolic_pressure']
        diastolic = data['diastolic_pressure']
        pwv = data['pulse_wave_velocity']
        groups = data['groups']
        
        if not groups:
            return Response(
                {'status': 'error', 'message': 'No groups provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Запускаем расчёт в отдельном потоке
        thread = threading.Thread(
            target=self._process_calculation,
            args=(calculation_id, systolic, diastolic, pwv, groups)
        )
        thread.daemon = True
        thread.start()
        
        return Response({
            'status': 'accepted',
            'message': 'Calculation started',
            'calculation_id': calculation_id,
            'groups_count': len(groups)
        }, status=status.HTTP_202_ACCEPTED)
    
    def _process_calculation(self, calculation_id, systolic, diastolic, pwv, groups):
        """
        Фоновый процесс расчёта CAVI.
        Выполняется с задержкой, затем отправляет результаты в Go бекенд.
        """
        # Случайная задержка 5-10 секунд
        delay = random.randint(
            settings.CALCULATION_DELAY_MIN,
            settings.CALCULATION_DELAY_MAX
        )
        logger.info(f"Starting CAVI calculation for calculation_id={calculation_id}, delay={delay}s")
        time.sleep(delay)
        
        results = []
        
        for group in groups:
            group_id = group.get('group_id')
            age_group = group.get('age_group', 'middle')
            disease_type = group.get('disease_type')
            
            # Рассчитываем CAVI индекс
            cavi_index = calculate_cavi(
                age_group=age_group,
                disease_type=disease_type,
                systolic_pressure=systolic,
                diastolic_pressure=diastolic,
                pulse_wave_velocity=pwv
            )
            
            results.append({
                'group_id': group_id,
                'cavi_index': cavi_index
            })
            
            logger.info(f"Calculated CAVI for group_id={group_id}: {cavi_index}")
        
        # Отправляем результаты в Go бекенд
        self._send_results_to_backend(calculation_id, results)
    
    def _send_results_to_backend(self, calculation_id, results):
        """
        Отправка результатов расчёта в Go бекенд.
        Включает groups_count для обновления в cavi_calculations.
        """
        url = f"{settings.GO_BACKEND_URL}/api/cavi-calculations/{calculation_id}/async-result"
        
        payload = {
            'token': settings.GO_BACKEND_TOKEN,
            'groups_count': len(results),
            'results': results
        }
        
        try:
            response = requests.put(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"Successfully sent results for calculation_id={calculation_id}, groups_count={len(results)}")
            else:
                logger.error(
                    f"Failed to send results for calculation_id={calculation_id}: "
                    f"status={response.status_code}, body={response.text}"
                )
        except requests.RequestException as e:
            logger.error(f"Error sending results for calculation_id={calculation_id}: {e}")
