"""
Симулятор игровой механики Indonesian Adventure.

Обеспечивает симуляцию игрового процесса с заданной конфигурацией.
"""

import logging
from typing import Dict, List, Optional, Union

from models.config import SimulationConfig
from models.enums import LocationRarityType
from workflow.location import Location
from workflow.workflow import Workflow
from workflow.simulation_response import SimulationResponse
from workflow.tapping import TappingEngine

from config.simulation_config import create_sample_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Simulator")

class Simulator:
    """
    Симулятор игрового процесса Indonesian Adventure.
    
    Позволяет симулировать игровой процесс с заданной конфигурацией,
    отслеживая прогресс, балансы и улучшения локаций.
    """
    
    def __init__(self, config: Optional[SimulationConfig] = None):
        """
        Инициализирует симулятор с указанной конфигурацией.
        
        Args:
            config: Конфигурация симуляции. Если не указана, используется пример конфигурации.
        """
        self.config = config or create_sample_config()
        self.workflow = Workflow()
        
    def setup_workflow(self) -> None:
        """
        Настраивает рабочий процесс (workflow) для симуляции.
        
        Инициализирует локации, кулдауны, уровни пользователя и расписание проверок
        на основе конфигурации.
        """
        # Добавляем все локации
        self._setup_locations()
        
        # Добавляем информацию о кулдаунах
        self.workflow.cooldowns.clear()
        self.workflow.cooldowns.update(self.config.location_cooldowns)
        
        # Добавляем конфигурацию уровней пользователя
        self.workflow.user_levels.clear()
        self.workflow.user_levels.update(self.config.user_levels)
        
        # Добавляем расписание проверок
        self.workflow.check_schedule.clear()
        self.workflow.check_schedule.extend(self.config.check_schedule)
        
        # Устанавливаем параметры экономики
        self.workflow.economy = self.config.economy
        
        # Устанавливаем конфигурацию тапания, если она доступна
        if hasattr(self.config, 'tapping'):
            self.workflow.tapping_config = self.config.tapping
            # Создаем движок тапания только если тапание включено
            if self.config.tapping.is_tapping:
                self.workflow.tapping_engine = TappingEngine(self.config.tapping)
                # Получаем начальный уровень персонажа из экономики
                initial_level = 1
                if self.config.economy and self.config.economy.starting_balance:
                    initial_level = max(1, self.config.economy.starting_balance.xp // 1000)
                print(f"DEBUG: Tapping engine initialized with tap_coef={self.config.tapping.tap_coef}, initial level={initial_level}")
            else:
                print("DEBUG: Tapping is disabled in workflow")
        
        # Устанавливаем алгоритм симуляции
        self.workflow.simulation_algorithm = self.config.simulation_algorithm
    
    def _setup_locations(self) -> None:
        """
        Инициализирует локации на основе конфигурации.
        Вспомогательный метод для setup_workflow.
        """
        self.workflow.locations.clear()
        for index, loc_config in self.config.locations.items():
            if not loc_config.levels:
                continue
                
            self.workflow.locations[index] = Location(
                rarity=loc_config.rarity,
                min_character_level=self.config.location_rarity_config[loc_config.rarity].user_level_required,
                levels=loc_config.levels,
                keys=self.config.location_rarity_config[loc_config.rarity].keys_reward
            )
        
    def run_simulation(self, simulation_id: Optional[str] = None) -> SimulationResponse:
        """
        Запускает симуляцию и возвращает результат.
        
        Args:
            simulation_id: Опциональный ID симуляции. Если не указан, генерируется автоматически.
            
        Returns:
            SimulationResponse: Результат симуляции с историей прогресса.
        """
        self.setup_workflow()
        return self.workflow.simulate(simulation_id)

    @property
    def result_summary(self) -> Dict[str, Union[int, float, str]]:
        """
        Возвращает краткую сводку результатов симуляции.
        
        Returns:
            Dict: Словарь с основными метриками симуляции
        """
        return {
            "user_level": self.workflow.balance.user_level,
            "gold": self.workflow.balance.gold,
            "xp": self.workflow.balance.xp,
            "keys": self.workflow.balance.keys,
            "earn_per_sec": self.workflow.balance.earn_per_sec
        }


def main():
    """Функция для тестового запуска симуляции."""
    simulator = Simulator()
    result = simulator.run_simulation()
    logger.info(f"Simulation completed. Time passed: {result.timestamp} seconds.")
    logger.info(f"Final balance: {simulator.workflow.balance}")


if __name__ == "__main__":
    main() 