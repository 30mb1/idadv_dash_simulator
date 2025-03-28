"""
Утилиты для обработки данных симуляции.
"""

from typing import Dict, List, Any, Tuple, Optional
import pandas as pd

# Определяем константы напрямую вместо импорта из конфигурации
DEFAULT_GAME_DURATION = 15 * 60  # 15 минут в секундах
DEFAULT_SESSION_MINUTES = DEFAULT_GAME_DURATION / 60  # В минутах

# Расписание проверок по умолчанию (без импорта из конфигурации)
DEFAULT_CHECK_SCHEDULE = [
    {"hour": 9, "minute": 0},
    {"hour": 13, "minute": 0},
    {"hour": 18, "minute": 0},
    {"hour": 22, "minute": 0},
]

# Извлекает данные о локациях из истории симуляции
def extract_location_data(history: List[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
    """
    Извлекает данные о локациях из истории симуляции.
    
    Args:
        history: История симуляции
        
    Returns:
        Dict: Словарь данных о локациях
    """
    locations_data = {}
    
    # Инициализируем локации из первого состояния
    if history:
        first_state = history[0]
        for loc_id, loc_state in first_state["locations"].items():
            locations_data[int(loc_id)] = {
                "current_level": loc_state["current_level"],
                "available": loc_state["available"],
                "upgrades_count": 0,
                "total_cost": 0,
                "total_xp": 0,
                "total_keys": 0,
                "upgrade_times": []
            }
    
    # Собираем информацию об улучшениях
    for state in history:
        # Обновляем состояние локаций
        for loc_id, loc_state in state["locations"].items():
            loc_id = int(loc_id)
            locations_data[loc_id].update({
                "current_level": loc_state["current_level"],
                "available": loc_state["available"]
            })
        
        # Обрабатываем улучшения
        for action in state["actions"]:
            if action["type"] == "location_upgrade":
                loc_id = int(action["location_id"])
                locations_data[loc_id]["upgrades_count"] += 1
                locations_data[loc_id]["total_cost"] += -action["gold_change"]  # Стоимость - это отрицательное изменение золота
                locations_data[loc_id]["total_xp"] += action["xp_change"]
                locations_data[loc_id]["total_keys"] += action["keys_change"]
                locations_data[loc_id]["upgrade_times"].append(action["timestamp"])
    
    return locations_data

# Извлекает временную шкалу улучшений из истории симуляции
def extract_upgrades_timeline(history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Извлекает временную шкалу улучшений из истории симуляции.
    
    Args:
        history: История симуляции
        
    Returns:
        List: Список улучшений
    """
    upgrades_timeline = []
    
    for state in history:
        for action in state["actions"]:
            if action["type"] == "location_upgrade":
                upgrades_timeline.append({
                    "timestamp": action["timestamp"],
                    "location_id": int(action["location_id"]),
                    "new_level": action["new_level"],
                    "gold_before": action["gold_before"],
                    "gold_change": action["gold_change"],
                    "gold_after": action["gold_after"],
                    "xp_before": action["xp_before"],
                    "xp_change": action["xp_change"],
                    "xp_after": action["xp_after"],
                    "keys_before": action["keys_before"],
                    "keys_change": action["keys_change"],
                    "keys_after": action["keys_after"],
                    "day": action["timestamp"] / 86400
                })
    
    # Сортируем по времени
    upgrades_timeline.sort(key=lambda x: x["timestamp"])
    
    return upgrades_timeline

# Извлекает данные об уровне персонажа из истории симуляции
def extract_level_data(history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Извлекает данные об уровне персонажа из истории симуляции.
    
    Args:
        history: История симуляции
        
    Returns:
        List: Список данных об уровне
    """
    level_data = []
    
    for state in history:
        level_data.append({
            "timestamp": state["timestamp"],
            "level": state["balance"]["user_level"],
            "xp": state["balance"]["xp"],
            "day": state["timestamp"] / 86400
        })
        
        # Добавляем действия повышения уровня для более точного графика
        for action in state["actions"]:
            if action["type"] == "level_up":
                level_data.append({
                    "timestamp": action["timestamp"],
                    "level": action["new_level"],
                    "xp": state["balance"]["xp"],  # Используем XP из состояния
                    "day": action["timestamp"] / 86400
                })
    
    # Сортируем по времени
    level_data.sort(key=lambda x: x["timestamp"])
    
    return level_data

# Извлекает данные о ресурсах из истории симуляции
def extract_resource_data(history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Извлекает данные о ресурсах из истории симуляции.
    
    Args:
        history: История симуляции
        
    Returns:
        List: Список данных о ресурсах
    """
    resources_data = []
    
    for state in history:
        resources_data.append({
            "timestamp": state["timestamp"],
            "gold": state["balance"]["gold"],
            "keys": state["balance"]["keys"],
            "earn_per_sec": state["balance"]["earn_per_sec"],
            "day": state["timestamp"] / 86400,
            "earn_per_hour": state["balance"]["earn_per_sec"] * 3600,
            "earn_per_day": state["balance"]["earn_per_sec"] * 86400
        })
    
    # Сортируем по времени
    resources_data.sort(key=lambda x: x["timestamp"])
    
    return resources_data

# Рассчитывает периоды стагнации (без улучшений)
def calculate_stagnation_periods(upgrades_timeline: List[Dict[str, Any]], min_duration: int = 86400) -> List[Dict[str, Any]]:
    """
    Рассчитывает периоды стагнации (без улучшений).
    
    Args:
        upgrades_timeline: Временная шкала улучшений
        min_duration: Минимальная длительность периода в секундах (по умолчанию 1 день)
        
    Returns:
        List: Список периодов стагнации
    """
    stagnation_periods = []
    
    for i in range(1, len(upgrades_timeline)):
        interval = upgrades_timeline[i]["timestamp"] - upgrades_timeline[i-1]["timestamp"]
        if interval > min_duration:
            stagnation_periods.append({
                "start": upgrades_timeline[i-1]["timestamp"],
                "end": upgrades_timeline[i]["timestamp"],
                "duration": interval,
                "start_day": upgrades_timeline[i-1]["timestamp"] / 86400,
                "duration_days": interval / 86400
            })
    
    return stagnation_periods

# Рассчитывает интервалы между улучшениями в часах
def calculate_intervals(upgrades_timeline: List[Dict[str, Any]]) -> List[float]:
    """
    Рассчитывает интервалы между улучшениями в часах.
    
    Args:
        upgrades_timeline: Временная шкала улучшений
        
    Returns:
        List: Список интервалов в часах
    """
    intervals = []
    
    for i in range(1, len(upgrades_timeline)):
        interval = (upgrades_timeline[i]["timestamp"] - upgrades_timeline[i-1]["timestamp"]) / 3600  # в часах
        intervals.append(interval)
    
    return intervals

# Рассчитывает количество улучшений по дням
def calculate_upgrades_per_day(upgrades_timeline: List[Dict[str, Any]]) -> Dict[int, int]:
    """
    Рассчитывает количество улучшений по дням.
    
    Args:
        upgrades_timeline: Временная шкала улучшений
        
    Returns:
        Dict: Словарь {день: количество_улучшений}
    """
    upgrades_per_day = {}
    
    for upgrade in upgrades_timeline:
        day = int(upgrade["timestamp"] // 86400)
        upgrades_per_day[day] = upgrades_per_day.get(day, 0) + 1
    
    return upgrades_per_day

def extract_daily_events_data(history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Извлекает и группирует игровые события по дням.
    
    Args:
        history: История симуляции
        
    Returns:
        List: Список данных о событиях по дням
    """
    if not history:
        return []
    
    # Инициализируем данные по дням
    daily_data = {}
    
    # Получаем временную шкалу улучшений и повышений уровня
    upgrades_by_day = {}
    level_ups_by_day = {}
    new_locations_by_day = {}
    
    # Количество входов в игру в день по расписанию
    logins_per_day = len(DEFAULT_CHECK_SCHEDULE)
    
    # Словарь для отслеживания предыдущего баланса ресурсов по дням
    prev_day_resources = {
        "gold": 0,
        "xp": 0,
        "keys": 0
    }
    
    # Обработка данных по дням
    for state in history:
        # Извлекаем день из таймстампа
        day = int(state["timestamp"] // 86400) + 1  # Дни начинаются с 1
        
        # Инициализируем данные для дня, если их ещё нет
        if day not in daily_data:
            daily_data[day] = {
                "day": day,
                "sessions_count": logins_per_day,  # Фиксированное количество входов из расписания
                "session_minutes": logins_per_day * DEFAULT_SESSION_MINUTES,  # Время = количество сессий * длительность сессии
                "level_ups": 0,
                "level_range": (0, 0),
                "upgrades_count": 0,
                "new_locations": 0,
                "gold": 0,
                "gold_earned": 0,  # Сколько золота получено за день
                "gold_spent": 0,    # Сколько золота потрачено за день
                "xp": 0,
                "xp_earned": 0,     # Сколько XP получено за день
                "keys": 0,
                "keys_earned": 0,   # Сколько ключей получено за день
                "keys_spent": 0     # Сколько ключей потрачено за день
            }
        
        # Добавляем ресурсы в конце дня
        daily_data[day]["gold"] = state["balance"]["gold"]
        daily_data[day]["xp"] = state["balance"]["xp"]
        daily_data[day]["keys"] = state["balance"]["keys"]
        
        # Обрабатываем действия
        for action in state["actions"]:
            action_day = int(action["timestamp"] // 86400) + 1
            
            if action_day not in daily_data:
                daily_data[action_day] = {
                    "day": action_day,
                    "sessions_count": logins_per_day,  # Фиксированное количество входов из расписания
                    "session_minutes": logins_per_day * DEFAULT_SESSION_MINUTES,
                    "level_ups": 0,
                    "level_range": (0, 0),
                    "upgrades_count": 0,
                    "new_locations": 0,
                    "gold": 0,
                    "gold_earned": 0,
                    "gold_spent": 0,
                    "xp": 0,
                    "xp_earned": 0,
                    "keys": 0,
                    "keys_earned": 0,
                    "keys_spent": 0
                }
            
            # Учет изменений ресурсов для любого типа действия
            if "gold_change" in action:
                if action["gold_change"] > 0:
                    daily_data[action_day]["gold_earned"] += action["gold_change"]
                elif action["gold_change"] < 0:
                    daily_data[action_day]["gold_spent"] += abs(action["gold_change"])
                    
            if "xp_change" in action and action["xp_change"] > 0:
                daily_data[action_day]["xp_earned"] += action["xp_change"]
                
            if "keys_change" in action:
                if action["keys_change"] > 0:
                    daily_data[action_day]["keys_earned"] += action["keys_change"]
                elif action["keys_change"] < 0:
                    daily_data[action_day]["keys_spent"] += abs(action["keys_change"])
            
            # Улучшения локаций
            if action["type"] == "location_upgrade":
                daily_data[action_day]["upgrades_count"] += 1
                
                # Отслеживаем новые локации (уровень 1)
                if action["new_level"] == 1:
                    daily_data[action_day]["new_locations"] += 1
                
                # Сохраняем данные об улучшениях для каждой локации
                loc_id = action["location_id"]
                if loc_id not in upgrades_by_day:
                    upgrades_by_day[loc_id] = {}
                
                if action_day not in upgrades_by_day[loc_id]:
                    upgrades_by_day[loc_id][action_day] = {"min": action["new_level"], "max": action["new_level"]}
                else:
                    upgrades_by_day[loc_id][action_day]["min"] = min(upgrades_by_day[loc_id][action_day]["min"], action["new_level"])
                    upgrades_by_day[loc_id][action_day]["max"] = max(upgrades_by_day[loc_id][action_day]["max"], action["new_level"])
            
            # Повышения уровня
            elif action["type"] == "level_up":
                daily_data[action_day]["level_ups"] += 1
                
                # Отслеживаем диапазон уровней
                if action_day not in level_ups_by_day:
                    level_ups_by_day[action_day] = {"min": action["old_level"], "max": action["new_level"]}
                else:
                    level_ups_by_day[action_day]["min"] = min(level_ups_by_day[action_day]["min"], action["old_level"])
                    level_ups_by_day[action_day]["max"] = max(level_ups_by_day[action_day]["max"], action["new_level"])
    
    # Добавляем диапазоны уровней
    for day, level_data in level_ups_by_day.items():
        daily_data[day]["level_range"] = (level_data["min"], level_data["max"])
    
    # Проверяем разницу в золоте между днями, чтобы учесть неотслеженные поступления
    days = sorted(daily_data.keys())
    for i in range(1, len(days)):
        prev_day = days[i-1]
        curr_day = days[i]
        
        prev_gold = daily_data[prev_day]["gold"]
        curr_gold = daily_data[curr_day]["gold"]
        earned = daily_data[curr_day]["gold_earned"]
        spent = daily_data[curr_day]["gold_spent"]
        
        # Если получение золота не учтено, но баланс вырос больше, чем потрачено
        expected_gold = prev_gold + earned - spent
        if curr_gold > expected_gold:
            # Добавляем недостающее золото к заработанному
            additional_earned = curr_gold - expected_gold
            daily_data[curr_day]["gold_earned"] += additional_earned
    
    # Формируем итоговый список
    result = []
    for day in sorted(daily_data.keys()):
        result.append(daily_data[day])
    
    return result 