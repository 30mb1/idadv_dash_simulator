import logging
import uuid
import copy
from typing import Dict, List, Optional

from models.config import UserLevelConfig, EconomyConfig, SimulationAlgorithm, TappingConfig
from workflow.balance import Balance
from workflow.location import Location
from workflow.simulation_response import SimulationResponse
from workflow.tapping import TappingEngine

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
        self.simulation_algorithm = SimulationAlgorithm.SEQUENTIAL  # По умолчанию последовательное улучшение
        self.tapping_config: TappingConfig = None  # Конфигурация тапания
        self.tapping_engine: Optional[TappingEngine] = None  # Движок для тапания
    
    def simulate(self, simulation_id: str = None) -> SimulationResponse:
        if not simulation_id:
            simulation_id = str(uuid.uuid4())
        
        timestamp = 0
        history = []
        stop_reason = ""  # Причина остановки
        
        logger.info("Starting simulation...")
        
        # Инициализируем баланс из экономической конфигурации
        if self.economy and self.economy.starting_balance:
            self.balance.gold = self.economy.starting_balance.gold
            self.balance.xp = self.economy.starting_balance.xp
            self.balance.keys = self.economy.starting_balance.keys
        
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
            stop_reason = f"Location {max_location_id} - received, reached the limit of locations"
        elif next_location:
            # Есть следующая локация, но не хватает уровня
            stop_reason = (f"Location {current_location[0]}, Current level {self.balance.user_level}, "
                         f"for opening location {next_location[0]} requires level {next_location[1].min_character_level}. "
                         f"Simulation stopped")
        else:
            stop_reason = "Simulation stopped"
        
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
            str: Отформатированное время в виде "День X, ЧЧ:ММ:СС"
        """
        total_days = timestamp // 86400
        hours = (timestamp % 86400) // 3600
        minutes = ((timestamp % 86400) % 3600) // 60
        seconds = ((timestamp % 86400) % 3600) % 60
        
        return f"День {total_days + 1}, {hours:02d}:{minutes:02d}:{seconds:02d}"

    def _do_actions(self, t: int, history: List[Dict] = None) -> None:
        # Check the game on specified timestamps (5 times per day with 8-hour sleep interval)
        if t % 86400 in self.check_schedule:
            game_time = self._format_game_time(t)
            logger.info(f"=== {game_time} === Player logged in ===")
            logger.info(f"{game_time}: Current earnings: {self.balance.earn_per_sec:.2f} gold/sec")
            
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
            
            # Проверяем, является ли это первой сессией в текущем дне
            is_first_session_of_day = t == min(self.check_schedule) + current_day_start
            
            # Если это первая сессия дня и тапание включено, добавляем доход от тапания
            if is_first_session_of_day and self.tapping_config and self.tapping_config.is_tapping:
                # Важно: дополнительная проверка, что тапание действительно включено
                if not hasattr(self.tapping_config, 'is_tapping') or self.tapping_config.is_tapping is not True:
                    logger.info(f"{game_time}: Tapping is disabled, no tapping income added")
                    pass
                else:
                    day_number = t // 86400
                    
                    # Проверяем, что все параметры тапания существуют
                    max_energy = self.tapping_config.max_energy_capacity
                    tap_coef = self.tapping_config.tap_coef
                    
                    if max_energy is None:
                        max_energy = 700
                    if tap_coef is None:
                        tap_coef = 1.0
                        
                    # Примерное количество золота, которое можно получить при полном использовании энергии
                    # Используем новую формулу: энергия * коэффициент тапа * (уровень персонажа * tap_coef)
                    gold_per_tap = self.balance.user_level * tap_coef
                    tapping_gold = max_energy * 0.7 * gold_per_tap
                    
                    old_balance = self.balance.gold
                    self.balance.gold += tapping_gold
                    
                    logger.info(
                        f"{game_time}: Added tapping income for day {day_number + 1}:\n"
                        f"  - Old balance: {old_balance:.2f} gold\n"
                        f"  - Tapping income: {tapping_gold:.2f} gold (level {self.balance.user_level} * tap_coef {tap_coef} = {gold_per_tap:.2f} gold per tap)\n"
                        f"  - New balance: {self.balance.gold:.2f} gold"
                    )
                    
                    # Записываем действие получения дохода от тапания
                    if current_history is not None:
                        action = {
                            "type": "tapping_income",
                            "timestamp": t,
                            "description": f"Tapping income for day {day_number + 1}",
                            "gold_before": old_balance,
                            "gold_change": tapping_gold,
                            "gold_after": self.balance.gold,
                            "xp_before": self.balance.xp,
                            "xp_change": 0,
                            "xp_after": self.balance.xp,
                            "keys_before": self.balance.keys,
                            "keys_change": 0,
                            "keys_after": self.balance.keys
                        }
                        current_history["actions"].append(action)
            
            # Начисляем пассивный доход за период, но только если это не первый вход в игру
            time_passed = t - last_check
            is_first_login = t == min(self.check_schedule) + current_day_start and t < 86400
            
            if time_passed > 0 and not is_first_login:  # Не начисляем доход при первом входе
                passive_income = self.balance.earn_per_sec * time_passed
                old_balance = self.balance.gold
                self.balance.gold += passive_income
                
                logger.info(
                    f"{game_time}: Earned income for {time_passed} sec:\n"
                    f"  - Old balance: {old_balance:.2f} gold\n"
                    f"  - Income: {passive_income:.2f} gold\n"
                    f"  - New balance: {self.balance.gold:.2f} gold"
                )
                
                # Записываем действие начисления дохода
                if current_history is not None:
                    action = {
                        "type": "passive_income",
                        "timestamp": t,
                        "description": f"Passive income for {time_passed} sec",
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
            elif is_first_login:
                logger.info(f"{game_time}: First login, passive income not earned")
            
            # Определяем конец игровой сессии
            session_end = t + self.economy.game_duration
            game_time = self._format_game_time(t)
            logger.info(f"{game_time}: Session duration: {self.economy.game_duration} sec (until {self._format_game_time(session_end)})")
            
            # Step 1. Try to upgrade locations while session is active
            while t < session_end:  # Продолжаем цикл пока не истечет время сессии
                # Проверяем, есть ли локации готовые для улучшения прямо сейчас
                available_locations = {idx: loc for idx, loc in self.locations.items() 
                                    if loc.available and loc.cooldown_until <= t}
                
                if not available_locations:
                    # Нет доступных локаций прямо сейчас, проверяем, будут ли они в рамках сессии
                    locations_in_cooldown = {idx: loc for idx, loc in self.locations.items() 
                                          if loc.available and loc.cooldown_until > t and loc.cooldown_until < session_end}
                    
                    if not locations_in_cooldown:
                        logger.info(f"{game_time}: No locations that will be available in this session")
                        break  # Выходим из цикла, если нет локаций, которые станут доступны в рамках сессии
                    
                    # Находим ближайшее время окончания кулдауна
                    next_available_time = min(loc.cooldown_until for loc in locations_in_cooldown.values())
                    
                    # Перематываем время вперед до окончания ближайшего кулдауна
                    old_t = t
                    t = next_available_time
                    game_time = self._format_game_time(t)
                    next_available = self._format_game_time(next_available_time)
                    logger.info(f"{game_time}: Waiting for cooldown to end ({t - old_t} sec), next action will be in {next_available}")
                    
                    # После перемотки продолжаем цикл с новой проверкой доступных локаций
                    continue
                
                # Сортируем локации в зависимости от алгоритма
                if self.simulation_algorithm == SimulationAlgorithm.SEQUENTIAL:
                    # Последовательное улучшение: сортируем по ID локации
                    sorted_locations = sorted(available_locations.items())
                else:
                    # Первое доступное улучшение (как в Kotlin): просто берем локации в том порядке, в котором они есть
                    sorted_locations = list(available_locations.items())
                
                # Флаг для отслеживания успешных улучшений
                any_upgrade_made = False
                
                for index, location in sorted_locations:
                    # Проверяем условия в зависимости от алгоритма
                    if self.simulation_algorithm == SimulationAlgorithm.SEQUENTIAL:
                        # Для последовательного алгоритма проверяем, что предыдущие локации полностью улучшены
                        previous_locations_maxed = True
                        for prev_idx, prev_loc in self.locations.items():
                            if prev_idx < index and prev_loc.available:
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
                            f"{game_time}: Location upgrade {index} "
                            f"(level {location.current_level + 1}), "
                            f"cost: {cost:.2f} gold, "
                            f"cooldown: {self.cooldowns[location.current_level + 1]} sec"
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
                                "description": f"Location upgrade {index} (level {location.current_level + 1})",
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
                            logger.info(f"{game_time}: Location {index} upgraded to the maximum level")
                        
                        # Set the cooldown
                        location.cooldown_until = t + cooldown
                        
                        # Проверяем, успеем ли мы выполнить следующее улучшение в рамках сессии
                        next_upgrade_time = t + cooldown
                        if next_upgrade_time < session_end:
                            next_available = self._format_game_time(next_upgrade_time)
                            logger.info(f"{game_time}: Cooldown: {cooldown} sec. Next location upgrade {index} will be available in {next_available} (within the current session)")
                        else:
                            next_available = self._format_game_time(next_upgrade_time)
                            logger.info(f"{game_time}: Cooldown: {cooldown} sec. Next location upgrade {index} will be available in {next_available} (after the current session)")
                        
                        # Сразу проверяем возможность повышения уровня персонажа
                        self._try_upgrade_character(t, current_history)
                        
                        any_upgrade_made = True
                        
                        # Для алгоритма "Первое доступное улучшение" завершаем цикл после первого успешного улучшения
                        if self.simulation_algorithm == SimulationAlgorithm.FIRST_AVAILABLE:
                            break
                
                if not any_upgrade_made:
                    # Если у пользователя есть деньги, но нет доступных локаций для улучшения,
                    # значит есть какие-то ограничения (например, предыдущие локации не максимальны)
                    game_time = self._format_game_time(t)
                    logger.info(f"{game_time}: No locations available for upgrade at the moment")
                    
                    # Проверяем, есть ли локации в кулдауне, которые могут стать доступными в рамках сессии
                    locations_in_cooldown = {idx: loc for idx, loc in self.locations.items() 
                                          if loc.available and loc.cooldown_until > t and loc.cooldown_until < session_end}
                    
                    if not locations_in_cooldown:
                        # Если нет локаций, которые могут стать доступными до конца сессии, выходим
                        logger.info(f"{game_time}: No more upgrades in this session")
                        break
                    
                    # Находим ближайшее время окончания кулдауна
                    next_available_time = min(loc.cooldown_until for loc in locations_in_cooldown.values())
                    
                    # Перематываем время вперед до окончания ближайшего кулдауна
                    old_t = t
                    t = next_available_time
                    game_time = self._format_game_time(t)
                    next_available = self._format_game_time(next_available_time)
                    logger.info(f"{game_time}: Waiting for cooldown to end ({t - old_t} sec), next action will be in {next_available}")
                    
                    # После перемотки продолжаем цикл без увеличения времени
                    continue
            
            game_time = self._format_game_time(t)
            remaining_time = session_end - t
            if remaining_time > 0:
                logger.info(f"{game_time}: Session ended earlier (remaining {remaining_time} sec)")
            logger.info(f"=== {game_time} === Player finished the session ===\n")
    
    def _try_upgrade_character(self, t: int, current_history: Dict = None) -> None:
        """
        Проверяет возможность повышения уровня персонажа и применяет его, если возможно.
        
        Args:
            t: Текущее игровое время
            current_history: Текущее состояние для записи истории
        """
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
                    f"{game_time}: Level up to {self.balance.user_level + 1}. "
                    f"New earnings: {self.user_levels[self.balance.user_level + 1].gold_per_sec:.2f}/sec"
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
                        "description": f"Level up to {self.balance.user_level}",
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
                    f"{game_time}: Earned {keys_reward} keys for the new level"
                )
                
                if self.balance.user_level < max(self.user_levels.keys()):
                    required_xp = self.user_levels[self.balance.user_level + 1].xp_required
                else:
                    break
    
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