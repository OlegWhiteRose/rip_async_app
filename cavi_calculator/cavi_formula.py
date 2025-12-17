"""
Формула расчёта индекса CAVI (Cardio-Ankle Vascular Index).
Реализация аналогична Go версии в RIP_2025.
"""
import math
from typing import Optional

# Константы возрастных групп
AGE_GROUP_YOUNG = "young"
AGE_GROUP_MIDDLE = "middle"
AGE_GROUP_ELDERLY = "elderly"

# Константы типов заболеваний
DISEASE_TYPE_DIABETES = "diabetes"
DISEASE_TYPE_HYPERTENSION = "hypertension"

# Плотность крови (г/мл)
RHO = 1.05


def calculate_cavi(
    age_group: str,
    disease_type: Optional[str],
    systolic_pressure: int,
    diastolic_pressure: int,
    pulse_wave_velocity: float
) -> float:
    """
    Рассчитывает индекс CAVI по формуле.
    
    Args:
        age_group: Возрастная группа (young, middle, elderly)
        disease_type: Тип заболевания (diabetes, hypertension, None)
        systolic_pressure: Систолическое давление (мм рт.ст.)
        diastolic_pressure: Диастолическое давление (мм рт.ст.)
        pulse_wave_velocity: Скорость пульсовой волны (м/с)
    
    Returns:
        Рассчитанный индекс CAVI
    """
    if systolic_pressure == 0 or diastolic_pressure == 0 or pulse_wave_velocity == 0:
        return 0.0
    
    ps = float(systolic_pressure)
    pd = float(diastolic_pressure)
    pwv = float(pulse_wave_velocity)
    
    if ps <= pd:
        return 0.0
    
    # Коэффициент возрастной группы M
    age_coefficients = {
        AGE_GROUP_YOUNG: 0.9,
        AGE_GROUP_MIDDLE: 1.0,
        AGE_GROUP_ELDERLY: 1.1,
    }
    M = age_coefficients.get(age_group, 1.0)
    
    # Коэффициент заболевания A
    A = 1.0
    if disease_type == DISEASE_TYPE_DIABETES:
        A = 1.2
    elif disease_type == DISEASE_TYPE_HYPERTENSION:
        A = 1.0
    
    # Разница давлений
    dp = ps - pd
    
    # Формула CAVI: M * (2 * rho / dp) * ln(ps/pd) * pwv^2 + A
    cavi = M * (2 * RHO / dp) * math.log(ps / pd) * (pwv ** 2) + A
    
    return round(cavi, 3)
