import logging
import uuid
import copy
from typing import Dict, List

from idadv_dash_simulator.models.config import UserLevelConfig, EconomyConfig
from idadv_dash_simulator.workflow.balance import Balance
from idadv_dash_simulator.workflow.location import Location
from idadv_dash_simulator.workflow.simulation_response import SimulationResponse

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Workflow")

class Workflow:
    def __init__(self):
        self.locations: Dict[int, Location] = {}
        self.cooldowns: Dict[int, int] = {}
        self.user_levels: Dict[int, UserLevelConfig] = {}
        self.check_schedule: List[int] = []
        self.balance = Balance()
        self.economy: EconomyConfig = None  # Будет установлено при настройке
    
    def simulate(self, simulation_id: str = None) -> SimulationResponse:
        if not simulation_id:
            simulation_id = str(uuid.uuid4())
        
        timestamp = 0
        history = []
        stop_reason = ""  # Причина остановки
        
        logger.info("Starting simulation...")
        
        self.balance.earn_per_sec = self.user_levels[self.balance.user_level].gold_per_sec
        
        # Создаем начальное состояние
        state = {
            "timestamp": timestamp,
            "balance": copy.deepcopy(self.__dict__["balance"].__dict__),
            "locations": {
                loc_id: {
                    "current_level": loc.current_level,
                    "available": loc.available,
                    "cooldown_until": loc.cooldown_until
                } for loc_id, loc in self.locations.items()
            },
            "actions": []
        }
        history.append(state)
        
        while any(location.available for location in self.locations.values()):
            try:
                # Проверяем, является ли текущий timestamp проверкой
                is_check_time = timestamp % 86400 in self.check_schedule
                
                self._do_actions(timestamp, history)
                
                # Если это была проверка, создаем новое состояние после всех действий
                if is_check_time:
                    state = {
                        "timestamp": timestamp,
                        "balance": copy.deepcopy(self.__dict__["balance"].__dict__),
                        "locations": {
                            loc_id: {
                                "current_level": loc.current_level,
                                "available": loc.available,
                                "cooldown_until": loc.cooldown_until
                            } for loc_id, loc in self.locations.items()
                        },
                        "actions": []  # Новый список действий для следующего периода
                    }
                    history.append(state)
                
            except Exception as e:
                logger.error(f"Error while doing actions on timestamp {timestamp}", exc_info=e)
            
            timestamp += 1
        
        # Определяем причину остановки
        max_location_id = max(self.locations.keys())
        current_location = None
        next_location = None
        
        # Находим текущую локацию (последнюю доступную) и следующую
        for loc_id in sorted(self.locations.keys()):
            if self.locations[loc_id].available:
                current_location = (loc_id, self.locations[loc_id])
            elif current_location and loc_id > current_location[0]:
                next_location = (loc_id, self.locations[loc_id])
                break
        
        if not current_location:
            # Все локации улучшены до максимума
            stop_reason = f"Локация {max_location_id} - получена, достигнут лимит по локациям"
        elif next_location:
            # Есть следующая локация, но не хватает уровня
            stop_reason = (f"Локация {current_location[0]}, Текущий уровень {self.balance.user_level}, "
                         f"для открытия локации {next_location[0]} требуется уровень {next_location[1].min_character_level}. "
                         f"Симуляция остановлена")
        else:
            stop_reason = "Симуляция остановлена"
        
        logger.info(f"Finished simulation.\nTime passed: {self._timestamp_to_human_readable(timestamp)}\nBalances:\n{self.balance}")
        logger.info(f"Stop reason: {stop_reason}")
        
        response = SimulationResponse(simulation_id, timestamp)
        response.history = history
        response.stop_reason = stop_reason
        return response
    
    @staticmethod
    def _format_game_time(timestamp: int) -> str:
        """
        Форматирует временную метку в читаемый формат игрового времени.
        
        Args:
            timestamp: Время в секундах
            
        Returns:
            str: Отформатированное время в виде "День X, ЧЧ:ММ"
        """
        total_days = timestamp // 86400
        hours = (timestamp % 86400) // 3600
        minutes = ((timestamp % 86400) % 3600) // 60
        
        return f"День {total_days + 1}, {hours:02d}:{minutes:02d}"

    def _do_actions(self, t: int, history: List[Dict] = None) -> None:
        # Check the game on specified timestamps (5 times per day with 8-hour sleep interval)
        if t % 86400 in self.check_schedule:
            game_time = self._format_game_time(t)
            logger.info(f"=== {game_time} === Игрок зашел в игру ===")
            logger.info(f"{game_time}: Текущий заработок: {self.balance.earn_per_sec:.2f} золота/сек")
            
            # Получаем текущее состояние из истории
            current_history = history[-1] if history else None
            
            # Определяем время с последней проверки
            last_check = 0
            current_day_start = t - (t % 86400)  # Начало текущего дня
            
            # Находим последнюю проверку в текущем дне
            for check_time in reversed(sorted(self.check_schedule)):
                check_timestamp = current_day_start + check_time
                if check_timestamp < t:
                    last_check = check_timestamp
                    break
            
            if last_check == 0:  # Если это первая проверка дня
                if t < 86400:  # Если это первый день симуляции
                    last_check = 0  # Начинаем с нуля
                else:
                    # Берем последнюю проверку предыдущего дня
                    prev_day_start = current_day_start - 86400
                    last_check = prev_day_start + max(self.check_schedule)
            
            # Начисляем пассивный доход за период
            time_passed = t - last_check
            if time_passed > 0:  # Защита от отрицательных значений
                passive_income = self.balance.earn_per_sec * time_passed
                old_balance = self.balance.gold
                self.balance.gold += passive_income
                
                logger.info(
                    f"{game_time}: Начислен доход за {time_passed} сек:\n"
                    f"  - Старый баланс: {old_balance:.2f} золота\n"
                    f"  - Доход: {passive_income:.2f} золота\n"
                    f"  - Новый баланс: {self.balance.gold:.2f} золота"
                )
                
                # Записываем действие начисления дохода
                if current_history is not None:
                    action = {
                        "type": "passive_income",
                        "timestamp": t,
                        "description": f"Пассивный доход за {time_passed} сек",
                        "gold_before": old_balance,
                        "gold_change": passive_income,
                        "gold_after": self.balance.gold,
                        "xp_before": self.balance.xp,
                        "xp_change": 0,
                        "xp_after": self.balance.xp,
                        "keys_before": self.balance.keys,
                        "keys_change": 0,
                        "keys_after": self.balance.keys
                    }
                    current_history["actions"].append(action)
            
            # Определяем конец игровой сессии
            session_end = t + self.economy.game_duration
            
            # Step 1. Try to upgrade locations
            while t < session_end:  # Продолжаем улучшения в течение игровой сессии
                available_locations = {idx: loc for idx, loc in self.locations.items() 
                                    if loc.available and loc.cooldown_until <= t}
                
                if not available_locations:
                    logger.info(f"{game_time}: Нет доступных локаций для улучшения")
                    break  # Если нет доступных локаций, завершаем сессию
                
                # Сортируем локации по индексу для последовательного улучшения
                sorted_locations = sorted(available_locations.items())
                
                # Флаг для отслеживания успешных улучшений
                any_upgrade_made = False
                
                # Проверяем, что предыдущие локации полностью улучшены
                for index, location in sorted_locations:
                    # Проверяем все предыдущие локации
                    previous_locations_maxed = True
                    for prev_idx, prev_loc in self.locations.items():
                        if prev_idx < index and prev_loc.available:
                            # Если предыдущая локация не улучшена до максимума, пропускаем текущую
                            previous_locations_maxed = False
                            break
                    
                    if not previous_locations_maxed:
                        continue
                    
                    # Skip locations that require higher user level
                    if self.balance.user_level < location.min_character_level:
                        continue
                    
                    # Get cost of the location upgrade
                    cost = location.get_upgrade_cost()
                    
                    if self.balance.gold >= cost:
                        game_time = self._format_game_time(t)
                        # Сохраняем состояние до улучшения
                        gold_before = self.balance.gold
                        xp_before = self.balance.xp
                        keys_before = self.balance.keys
                        
                        # Upgrade location
                        logger.info(
                            f"{game_time}: Улучшение локации {index} "
                            f"(уровень {location.current_level + 1}), "
                            f"стоимость: {cost:.2f} золота"
                        )
                        
                        reward_xp = location.get_upgrade_xp_reward()
                        reward_keys = location.get_upgrade_keys_reward()
                        cooldown = self.cooldowns[location.current_level + 1]
                        
                        # Charge the cost from the balance
                        self.balance.gold -= cost
                        
                        # Add experience
                        self.balance.xp += reward_xp
                        
                        # Add keys
                        self.balance.keys += reward_keys
                        
                        # Добавляем запись о действии в историю
                        if current_history is not None:
                            action = {
                                "type": "location_upgrade",
                                "timestamp": t,
                                "description": f"Улучшение локации {index} (уровень {location.current_level + 1})",
                                "location_id": index,
                                "new_level": location.current_level + 1,
                                "gold_before": gold_before,
                                "gold_change": -cost,
                                "gold_after": self.balance.gold,
                                "xp_before": xp_before,
                                "xp_change": reward_xp,
                                "xp_after": self.balance.xp,
                                "keys_before": keys_before,
                                "keys_change": reward_keys,
                                "keys_after": self.balance.keys
                            }
                            current_history["actions"].append(action)
                        
                        logger.info(
                            f"{game_time}: Получено: {reward_xp} опыта, "
                            f"{reward_keys} ключей. "
                            f"Баланс: {self.balance.gold:.2f} золота"
                        )
                        
                        # Update location
                        location.current_level += 1
                        
                        # If this was the last upgrade, deactivate location
                        if location.current_level >= max(location.levels.keys()):
                            location.available = False
                            logger.info(f"{game_time}: Локация {index} улучшена до максимального уровня")
                        
                        # Set the cooldown
                        location.cooldown_until = t + cooldown
                        next_available = self._format_game_time(t + cooldown)
                        logger.info(f"{game_time}: Следующее улучшение локации {index} будет доступно в {next_available}")
                        
                        any_upgrade_made = True
                        break
                
                if not any_upgrade_made:
                    logger.info(f"{game_time}: Недостаточно ресурсов для улучшений")
                    break  # Если не удалось сделать улучшений, завершаем сессию
                
                t += 1  # Увеличиваем время только если были улучшения
            
            # Step 2. Check for level ups
            if self.balance.user_level < max(self.user_levels.keys()):
                required_xp = self.user_levels[self.balance.user_level + 1].xp_required
                
                # Upgrade as many times as needed
                while self.balance.xp >= required_xp:
                    game_time = self._format_game_time(t)
                    # Сохраняем состояние до повышения уровня
                    gold_before = self.balance.gold
                    xp_before = self.balance.xp
                    keys_before = self.balance.keys
                    
                    logger.info(
                        f"{game_time}: Повышение уровня персонажа до {self.balance.user_level + 1}. "
                        f"Новый заработок: {self.user_levels[self.balance.user_level + 1].gold_per_sec:.2f}/сек"
                    )
                    
                    self.balance.user_level += 1
                    self.balance.earn_per_sec = self.user_levels[self.balance.user_level].gold_per_sec
                    keys_reward = self.user_levels[self.balance.user_level].keys_reward
                    self.balance.keys += keys_reward
                    
                    # Добавляем запись о повышении уровня в историю
                    if current_history is not None:
                        action = {
                            "type": "level_up",
                            "timestamp": t,
                            "description": f"Повышение уровня до {self.balance.user_level}",
                            "old_level": self.balance.user_level - 1,
                            "new_level": self.balance.user_level,
                            "gold_before": gold_before,
                            "gold_change": 0,
                            "gold_after": self.balance.gold,
                            "xp_before": xp_before,
                            "xp_change": 0,
                            "xp_after": self.balance.xp,
                            "keys_before": keys_before,
                            "keys_change": keys_reward,
                            "keys_after": self.balance.keys,
                            "new_earn_per_sec": self.balance.earn_per_sec
                        }
                        current_history["actions"].append(action)
                    
                    logger.info(
                        f"{game_time}: Получено {keys_reward} ключей за новый уровень"
                    )
                    
                    if self.balance.user_level < max(self.user_levels.keys()):
                        required_xp = self.user_levels[self.balance.user_level + 1].xp_required
                    else:
                        return
            
            game_time = self._format_game_time(t)
            logger.info(f"=== {game_time} === Игрок завершил сессию ===\n")
    
    @staticmethod
    def _timestamp_to_human_readable(timestamp: int) -> str:
        weeks = timestamp // 604800
        days = (timestamp % 604800) // 86400
        hours = ((timestamp % 604800) % 86400) // 3600
        minutes = (((timestamp % 604800) % 86400) % 3600) // 60
        seconds = (((timestamp % 604800) % 86400) % 3600) % 60
        
        result = []
        if weeks > 0:
            result.append(f"{weeks}W")
        if days > 0:
            result.append(f"{days}D")
        
        result.append(f"{hours}:{minutes}:{seconds}")
        
        return " ".join(result) 