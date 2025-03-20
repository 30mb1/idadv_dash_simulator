from idadv_dash_simulator.models.enums import LocationRarityType
from idadv_dash_simulator.models.config import (
    LocationLevel,
    LocationRarityConfig,
    LocationConfig,
    UserLevelConfig,
    SimulationConfig,
    EconomyConfig
)

def calculate_gold_per_sec(base_gold: float, earn_coefficient: float, level: int) -> float:
    """Рассчитывает значение gold_per_sec для заданного уровня.
    
    Args:
        base_gold: Базовое значение золота для первого уровня
        earn_coefficient: Коэффициент роста (например, 1.091 для роста на 9.1%)
        level: Уровень персонажа
    
    Returns:
        float: Значение gold_per_sec для указанного уровня
    """
    if level == 1:
        return base_gold
        
    # Получаем значение предыдущего уровня
    prev_value = calculate_gold_per_sec(base_gold, earn_coefficient, level - 1)
    # Умножаем предыдущее значение на коэффициент
    return prev_value * (earn_coefficient** (level - 1))

def create_sample_config() -> SimulationConfig:
    """Создает пример конфигурации для симуляции."""
    
    # Параметры экономики
    economy = EconomyConfig(
        base_gold_per_sec=0.56,
        earn_coefficient=1.091  # Коэффициент для роста на 9.1%
    )
    
    # Уровни локаций
    location_levels = {
        1: LocationLevel(cost=100, xp_reward=10),
        2: LocationLevel(cost=300, xp_reward=30),
        3: LocationLevel(cost=600, xp_reward=60),
        4: LocationLevel(cost=1200, xp_reward=120),
        5: LocationLevel(cost=2400, xp_reward=240),
    }
    
    # Конфигурация локаций по редкости
    location_rarity_config = {
        LocationRarityType.COMMON: LocationRarityConfig(user_level_required=1, keys_reward=1),
        LocationRarityType.RARE: LocationRarityConfig(user_level_required=2, keys_reward=2),
        LocationRarityType.EPIC: LocationRarityConfig(user_level_required=3, keys_reward=3),
        LocationRarityType.LEGENDARY: LocationRarityConfig(user_level_required=4, keys_reward=5),
    }
    
    # Локации
    locations = {
        1: LocationConfig(rarity=LocationRarityType.COMMON, levels=location_levels.copy()),
        2: LocationConfig(rarity=LocationRarityType.COMMON, levels=location_levels.copy()),
        3: LocationConfig(rarity=LocationRarityType.COMMON, levels=location_levels.copy()),
        4: LocationConfig(rarity=LocationRarityType.RARE, levels=location_levels.copy()),
        5: LocationConfig(rarity=LocationRarityType.LEGENDARY, levels=location_levels.copy()),
    }
    
    # Кулдауны для уровней локаций (в секундах)
    location_cooldowns = {
        1: 3600,      # 1 час
        2: 7200,      # 2 часа
        3: 14400,     # 4 часа
        4: 28800,     # 8 часов
        5: 43200,     # 12 часов
    }
    
    # Уровни пользователя с автоматическим расчетом gold_per_sec
    user_levels = {
        level: UserLevelConfig(
            xp_required=xp_required,
            gold_per_sec=calculate_gold_per_sec(economy.base_gold_per_sec, economy.earn_coefficient, level),
            keys_reward=keys_reward
        )
        for level, (xp_required, keys_reward) in enumerate([
            (0, 0),        # level 1
            (100, 5),      # level 2
            (300, 10),     # level 3
            (900, 15),     # level 4
            (2700, 25),    # level 5
            (8100, 35),    # level 6
            (24300, 45),   # level 7
            (72900, 55),   # level 8
            (218700, 65),  # level 9
            (656100, 75),  # level 10
        ], 1)  # start enumeration from 1
    }
    
    # Расписание проверок
    check_schedule = [
        8 * 3600,     # 8:00
        12 * 3600,    # 12:00
        16 * 3600,    # 16:00
        20 * 3600,    # 20:00
        22 * 3600,    # 22:00
    ]
    
    return SimulationConfig(
        locations=locations,
        location_cooldowns=location_cooldowns,
        location_rarity_config=location_rarity_config,
        user_levels=user_levels,
        check_schedule=check_schedule,
        economy=economy
    ) 