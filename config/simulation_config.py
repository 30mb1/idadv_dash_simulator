"""
Конфигурационный файл для настроек симуляции.
"""

from models.enums import LocationRarityType
from models.config import (
    LocationLevel,
    LocationRarityConfig,
    LocationConfig,
    UserLevelConfig,
    SimulationConfig,
    EconomyConfig,
    TappingConfig
)
from utils.economy import calculate_gold_per_sec

def create_sample_config() -> SimulationConfig:
    """
    Создает пример конфигурации для симуляции.
    
    Returns:
        SimulationConfig: Конфигурация симуляции с значениями по умолчанию
    """
    
    # Параметры экономики
    economy = EconomyConfig(
        base_gold_per_sec=0.555556,  # Обновлено согласно Game balance.json
        earn_coefficient=1.091,
        game_duration=900
    )
    
    # Конфигурация локаций по редкости
    location_rarity_config = {
        LocationRarityType.COMMON: LocationRarityConfig(
            user_level_required=1,
            keys_reward=1,
            cost_growth_ratio=1.2
        ),
        LocationRarityType.RARE: LocationRarityConfig(
            user_level_required=5,
            keys_reward=2,
            cost_growth_ratio=1.225
        ),
        LocationRarityType.LEGENDARY: LocationRarityConfig(
            user_level_required=8,
            keys_reward=3,
            cost_growth_ratio=1.25
        ),
    }
    
    # Локации
    locations = {}
    
    # Common locations (1-15)
    common_base_costs = {
        1: 1000, 2: 1050, 3: 1103, 4: 1158, 5: 1216,
        6: 1276, 7: 1340, 8: 1407, 9: 1477, 10: 1551,
        11: 1629, 12: 1710, 13: 1796, 14: 1886, 15: 1980
    }
    
    common_xp_rewards = {
        1: 10, 2: 11, 3: 11, 4: 12, 5: 14,
        6: 16, 7: 19, 8: 24, 9: 30, 10: 39,
        11: 51, 12: 68, 13: 91, 14: 125, 15: 172,
        16: 238, 17: 331, 18: 462, 19: 645, 20: 903
    }
    
    for loc_id in range(1, 16):
        levels = {}
        base_cost = common_base_costs[loc_id]
        for level in range(1, 21):
            cost = int(base_cost * (1.2 ** (level - 1)))
            xp_reward = common_xp_rewards[level]
            levels[level] = LocationLevel(cost=cost, xp_reward=xp_reward)
        locations[loc_id] = LocationConfig(
            rarity=LocationRarityType.COMMON,
            levels=levels
        )
    
    # Rare locations (16-25)
    rare_base_costs = {
        16: 5000, 17: 5250, 18: 5513, 19: 5788, 20: 6078,
        21: 6381, 22: 6700, 23: 7036, 24: 7387, 25: 7757
    }
    
    rare_xp_rewards = {
        1: 20, 2: 21, 3: 23, 4: 25, 5: 28,
        6: 33, 7: 39, 8: 48, 9: 60, 10: 77,
        11: 101, 12: 135, 13: 183, 14: 250, 15: 344,
        16: 477, 17: 663, 18: 924, 19: 1291, 20: 1806
    }
    
    for loc_id in range(16, 26):
        levels = {}
        base_cost = rare_base_costs[loc_id]
        for level in range(1, 21):
            cost = int(base_cost * (1.225 ** (level - 1)))
            xp_reward = rare_xp_rewards[level]
            levels[level] = LocationLevel(cost=cost, xp_reward=xp_reward)
        locations[loc_id] = LocationConfig(
            rarity=LocationRarityType.RARE,
            levels=levels
        )
    
    # Legendary locations (26-30)
    legendary_base_costs = {
        26: 15000, 27: 15750, 28: 16538, 29: 17364, 30: 18233
    }
    legendary_xp_rewards = {
        1: 40, 2: 42, 3: 45, 4: 50, 5: 56,
        6: 65, 7: 78, 8: 95, 9: 120, 10: 154,
        11: 202, 12: 270, 13: 366, 14: 500, 15: 689,
        16: 953, 17: 1325, 18: 1847, 19: 2581, 20: 3612
    }
    
    for loc_id in range(26, 31):
        levels = {}
        base_cost = legendary_base_costs[loc_id]
        for level in range(1, 21):
            cost = int(base_cost * (1.25 ** (level - 1)))
            xp_reward = legendary_xp_rewards[level]
            levels[level] = LocationLevel(cost=cost, xp_reward=xp_reward)
        locations[loc_id] = LocationConfig(
            rarity=LocationRarityType.LEGENDARY,
            levels=levels
        )
    
    # Кулдауны для уровней локаций (в секундах)
    location_cooldowns = {
        1: 10,      # 10 секунд
        2: 20,      # 20 секунд
        3: 20,      # 20 секунд
        4: 30,      # 30 секунд
        5: 45,      # 45 секунд
        6: 60,      # 1 минута
        7: 90,      # 1.5 минуты
        8: 150,     # 2.5 минуты
        9: 210,     # 3.5 минуты
        10: 300,    # 5 минут
        11: 450,    # 7.5 минут
        12: 600,    # 10 минут
        13: 900,    # 15 минут
        14: 1200,   # 20 минут
        15: 1800,   # 30 минут
        16: 2700,   # 45 минут
        17: 3600,   # 1 час
        18: 5400,   # 1.5 часа
        19: 7200,   # 2 часа
        20: 14400,  # 4 часа        
    }
    
    # Уровни пользователя
    user_levels = {
        1: UserLevelConfig(xp_required=0, gold_per_sec=0.555556, keys_reward=0),
        2: UserLevelConfig(xp_required=1000, gold_per_sec=0.606014, keys_reward=2),
        3: UserLevelConfig(xp_required=3200, gold_per_sec=0.721094, keys_reward=3),
        4: UserLevelConfig(xp_required=5800, gold_per_sec=0.935958, keys_reward=4),
        5: UserLevelConfig(xp_required=10500, gold_per_sec=1.325183, keys_reward=5),
        6: UserLevelConfig(xp_required=19000, gold_per_sec=2.046680, keys_reward=6),
        7: UserLevelConfig(xp_required=34000, gold_per_sec=3.448092, keys_reward=7),
        8: UserLevelConfig(xp_required=61000, gold_per_sec=6.336693, keys_reward=8),
        9: UserLevelConfig(xp_required=110000, gold_per_sec=12.702853, keys_reward=9),
        10: UserLevelConfig(xp_required=200000, gold_per_sec=27.777600, keys_reward=10),
    }
    
    # Расписание проверок (в секундах от начала дня)
    check_schedule = [
        0,          # 00:00
        28800,      # 08:00
        43200,      # 12:00
        57600,      # 16:00
        72000,      # 20:00
    ]
    
    # Конфигурация механики тапания
    tapping_config = TappingConfig(
        is_tapping=True,  # Включаем тапание по умолчанию
        max_energy_capacity=700,  # Максимальный запас энергии
        tap_speed=3.0,  # Скорость тапания (тапов в секунду)
        tap_coef=1.0  # Множитель золота за тап (уровень персонажа * tap_coef)
    )
    
    return SimulationConfig(
        locations=locations,
        location_cooldowns=location_cooldowns,
        location_rarity_config=location_rarity_config,
        user_levels=user_levels,
        check_schedule=check_schedule,
        economy=economy,
        tapping=tapping_config
    ) 