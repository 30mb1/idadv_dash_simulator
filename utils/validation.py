"""
Утилиты для валидации конфигураций и данных симуляции.
"""

from typing import Dict, List, Optional, Union, Any
import logging
from models.config import SimulationConfig, LocationConfig, UserLevelConfig

logger = logging.getLogger(__name__)

def validate_simulation_config(config: SimulationConfig) -> List[str]:
    """
    Проверяет корректность конфигурации симуляции.
    
    Args:
        config: Конфигурация для проверки
        
    Returns:
        List[str]: Список ошибок или пустой список, если ошибок нет
    """
    errors = []
    
    # Проверка экономических параметров
    if config.economy.base_gold_per_sec <= 0:
        errors.append("Базовое значение золота в секунду должно быть положительным")
    
    if config.economy.earn_coefficient <= 0:
        errors.append("Коэффициент роста должен быть положительным")
    
    if config.economy.game_duration <= 0:
        errors.append("Длительность игры должна быть положительной")
    
    # Проверка локаций
    if not config.locations:
        errors.append("Должна быть определена хотя бы одна локация")
    
    for loc_id, location in config.locations.items():
        loc_errors = validate_location_config(loc_id, location, config.location_rarity_config)
        errors.extend(loc_errors)
    
    # Проверка уровней пользователя
    if not config.user_levels:
        errors.append("Должен быть определен хотя бы один уровень пользователя")
    
    if 1 not in config.user_levels:
        errors.append("Уровень 1 должен быть определен в user_levels")
    
    # Проверка расписания проверок
    if not config.check_schedule:
        errors.append("Расписание проверок не должно быть пустым")
    
    for check_time in config.check_schedule:
        if check_time < 0 or check_time >= 86400:
            errors.append(f"Время проверки {check_time} выходит за пределы дня (0-86399)")
    
    return errors

def validate_location_config(loc_id: int, location: LocationConfig, 
                           rarity_config: Dict) -> List[str]:
    """
    Проверяет корректность конфигурации локации.
    
    Args:
        loc_id: ID локации
        location: Конфигурация локации
        rarity_config: Конфигурация редкостей
        
    Returns:
        List[str]: Список ошибок
    """
    errors = []
    
    if location.rarity not in rarity_config:
        errors.append(f"Локация {loc_id}: Неизвестная редкость {location.rarity}")
        return errors
    
    if not location.levels:
        errors.append(f"Локация {loc_id}: Не определены уровни")
        return errors
    
    # Проверяем корректность уровней (должны быть последовательными)
    expected_level = 1
    for level_id in sorted(location.levels.keys()):
        if level_id != expected_level:
            errors.append(f"Локация {loc_id}: Отсутствует уровень {expected_level}")
        
        level = location.levels[level_id]
        if level.cost <= 0:
            errors.append(f"Локация {loc_id}, уровень {level_id}: Стоимость должна быть положительной")
        
        if level.xp_reward < 0:
            errors.append(f"Локация {loc_id}, уровень {level_id}: Награда XP не может быть отрицательной")
        
        expected_level += 1
    
    return errors

def validate_simulation_data(data: Dict[str, Any]) -> List[str]:
    """
    Проверяет корректность данных симуляции.
    
    Args:
        data: Данные симуляции для проверки
        
    Returns:
        List[str]: Список ошибок или пустой список, если ошибок нет
    """
    errors = []
    
    if 'history' not in data:
        errors.append("Отсутствует история симуляции")
        return errors
    
    history = data['history']
    if not history:
        errors.append("История симуляции пуста")
        return errors
    
    # Проверяем первое состояние
    first_state = history[0]
    required_fields = ["timestamp", "balance", "locations", "actions"]
    for field in required_fields:
        if field not in first_state:
            errors.append(f"В состоянии отсутствует поле {field}")
    
    # Проверяем хронологию
    prev_time = -1
    for i, state in enumerate(history):
        if 'timestamp' not in state:
            errors.append(f"В состоянии {i} отсутствует timestamp")
            continue
            
        timestamp = state['timestamp']
        if timestamp < prev_time:
            errors.append(f"Нарушена хронология: timestamp {timestamp} меньше предыдущего {prev_time}")
        
        prev_time = timestamp
    
    return errors

def is_config_valid(config: SimulationConfig) -> bool:
    """
    Быстрая проверка валидности конфигурации.
    
    Args:
        config: Конфигурация для проверки
        
    Returns:
        bool: True, если конфигурация валидна
    """
    errors = validate_simulation_config(config)
    if errors:
        for error in errors:
            logger.error(f"Ошибка конфигурации: {error}")
        return False
    return True 