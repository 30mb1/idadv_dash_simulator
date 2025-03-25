"""
Модуль для расчета механики тапания в симуляторе игры.
Позволяет моделировать использование энергии и получение ресурсов от тапания.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from models.config import TappingConfig

logger = logging.getLogger("TappingModule")

@dataclass
class TapSession:
    """Данные одной игровой сессии тапания."""
    start_time: int  # Время начала сессии в секундах
    duration: int  # Длительность сессии в секундах
    energy_used: int = 0  # Потраченная энергия
    taps_count: int = 0  # Количество выполненных тапов
    gold_earned: float = 0  # Заработанное золото
    energy_history: List[Tuple[int, int]] = field(default_factory=list)  # История энергии (время, значение)
    user_level: int = 1  # Уровень персонажа во время сессии

@dataclass
class TapDay:
    """Агрегированные данные за один игровой день."""
    day: int  # Номер дня
    sessions: List[TapSession] = field(default_factory=list)  # Сессии в течение дня
    total_taps: int = 0  # Всего тапов за день
    total_energy: int = 0  # Всего потрачено энергии за день
    total_gold: float = 0  # Всего получено золота за день

class TappingEngine:
    """
    Движок для симуляции механики тапания.
    
    Отвечает за расчет использования энергии, получения ресурсов
    и отслеживание статистики по тапанию.
    """
    
    def __init__(self, config: TappingConfig):
        """
        Инициализирует движок тапания с заданной конфигурацией.
        
        Args:
            config: Конфигурация механики тапания
        """
        self.config = config
        # Устанавливаем значения по умолчанию, если они отсутствуют
        if self.config.tap_coef is None:
            self.config.tap_coef = 1.0
        if self.config.tap_speed is None:
            self.config.tap_speed = 3.0
        if self.config.max_energy_capacity is None:
            self.config.max_energy_capacity = 700
            
        self.days_data: List[TapDay] = []
        self.current_energy = self.config.max_energy_capacity
        self.user_level = 1  # Устанавливаем начальный уровень персонажа
    
    def simulate_sessions(self, session_times: List[int], session_duration: int, user_level: int = 1, user_levels_by_day: Dict[int, int] = None) -> List[TapDay]:
        """
        Симулирует все игровые сессии и возвращает агрегированные данные по дням.
        
        Args:
            session_times: Список времени начала сессий (в секундах)
            session_duration: Длительность каждой сессии (в минутах)
            user_level: Базовый уровень персонажа (влияет на золото за тап)
            user_levels_by_day: Словарь уровней персонажа по дням (индекс 0 = день 1)
            
        Returns:
            List[TapDay]: Список данных по дням
        """
        if not self.config.is_tapping:
            logger.info("Тапание отключено в конфигурации")
            return []
        
        self.days_data = []
        # Начинаем с полным запасом энергии
        self.current_energy = self.config.max_energy_capacity
        self.user_level = user_level
        
        # Преобразуем длительность сессии из минут в секунды
        session_duration_sec = session_duration * 60
        
        # Сортируем сессии по времени
        session_times.sort()
        
        last_session_end = 0  # Время окончания последней сессии для расчета восстановления
        
        for session_idx, session_start in enumerate(session_times):
            day_number = session_start // 86400
            
            # Определяем текущий уровень пользователя для этой сессии на основе дня
            if user_levels_by_day and day_number in user_levels_by_day:
                current_level = user_levels_by_day[day_number]
                logger.info(f"День {day_number+1}: установлен уровень пользователя {current_level}")
            else:
                current_level = self.user_level
            
            # Обновляем текущий уровень пользователя для движка
            self.user_level = current_level
            
            # Восстанавливаем энергию медленно между сессиями (0.1 ед/сек)
            if last_session_end > 0:
                time_passed = session_start - last_session_end
                # Восстановление энергии: 0.1 ед/сек (полное восстановление за 2-3 часа)
                energy_recovery_rate = 0.1
                energy_recovered = min(time_passed * energy_recovery_rate, 
                                      self.config.max_energy_capacity - self.current_energy)
                self.current_energy += energy_recovered
                
                logger.info(f"Сессия {session_idx+1}: Восстановлено {energy_recovered:.1f} энергии за {time_passed} секунд между сессиями")
            
            # Симулируем текущую сессию с текущим уровнем пользователя
            session = self._simulate_session(session_start, session_duration_sec)
            last_session_end = session_start + session_duration_sec
            
            # Добавляем сессию в соответствующий день
            day = self._get_or_create_day(day_number)
            
            # Обновляем уровень пользователя в объекте сессии, чтобы сохранить эту информацию
            session.user_level = self.user_level
            
            day.sessions.append(session)
            day.total_taps += session.taps_count
            day.total_energy += session.energy_used
            day.total_gold += session.gold_earned
            
            logger.info(f"Сессия {session_idx+1}: тапов={session.taps_count:.0f}, энергии={session.energy_used:.0f}, золота={session.gold_earned:.0f}, уровень={session.user_level}")
        
        return self.days_data
    
    def _simulate_session(self, start_time: int, duration: int) -> TapSession:
        """
        Симулирует одну игровую сессию тапания.
        
        Args:
            start_time: Время начала сессии (в секундах)
            duration: Длительность сессии (в секундах)
            
        Returns:
            TapSession: Данные сессии
        """
        session = TapSession(start_time=start_time, duration=duration, user_level=self.user_level)
        
        # Логируем информацию о текущей сессии для отладки
        day_number = start_time // 86400
        logger.info(f"Симуляция сессии для дня {day_number+1}, уровень пользователя: {self.user_level}")
        
        # Добавляем начальное состояние энергии
        session.energy_history.append((start_time, self.current_energy))
        
        # Определяем эффективное время тапания (максимум 5-7 минут)
        # Для новичков (запас энергии <= 700) - не более 5 минут
        # Для прокачанных (запас энергии > 700) - не более 7 минут
        max_tapping_time = 300 if self.config.max_energy_capacity <= 700 else 420  # в секундах
        
        # Ограничение на количество тапов для новичков (500-700)
        max_taps_for_beginners = self.config.max_energy_capacity
        if self.config.max_energy_capacity <= 700:
            # Случайное значение в диапазоне 500-700 или меньше, если энергии меньше
            max_taps_for_beginners = min(self.config.max_energy_capacity, 
                                         500 + int((700-500) * (self.config.max_energy_capacity / 700)))
        
        # Скорость восстановления энергии (медленнее, чем расход)
        # В реальных Tap-to-Earn полное восстановление занимает 2-3 часа
        # Делаем восстановление в 10 раз медленнее расхода (0.1 ед/сек)
        energy_recovery_rate = 0.1
        
        remaining_time = min(duration, max_tapping_time)
        current_time = start_time
        active_tapping = True
        
        # Симулируем тапание только в пределах эффективного времени
        total_taps_in_session = 0
        
        while remaining_time > 0:
            if active_tapping and self.current_energy > 0:
                # Сколько тапов можно сделать за 1 секунду (не больше текущей энергии и скорости тапания)
                taps_per_second = min(self.config.tap_speed, self.current_energy)
                
                # Проверка на лимит тапов для новичков
                if self.config.max_energy_capacity <= 700:
                    remaining_allowed_taps = max_taps_for_beginners - total_taps_in_session
                    taps_per_second = min(taps_per_second, remaining_allowed_taps)
                
                if taps_per_second <= 0:
                    # Энергия закончилась или достигнут лимит тапов, заканчиваем активное тапание
                    active_tapping = False
                else:
                    # Обновляем статистику
                    self.current_energy -= taps_per_second
                    session.energy_used += taps_per_second
                    session.taps_count += taps_per_second
                    total_taps_in_session += taps_per_second
                    
                    # Расчет золота за тап с учетом уровня персонажа
                    gold_per_tap = self.user_level * self.config.tap_coef
                    session.gold_earned += taps_per_second * gold_per_tap
                    
                    # Логирование для отладки
                    if taps_per_second > 0:
                        logger.info(f"Уровень пользователя: {self.user_level}, коэффициент: {self.config.tap_coef}, золото за тап: {gold_per_tap:.2f}")
                        logger.info(f"Тапов: {taps_per_second:.1f}, получено золота: {taps_per_second * gold_per_tap:.1f}")
                    
                    # Если энергия закончилась, прекращаем активное тапание
                    if self.current_energy <= 0 or (self.config.max_energy_capacity <= 700 and 
                                                  total_taps_in_session >= max_taps_for_beginners):
                        active_tapping = False
            
            # Восстанавливаем энергию медленнее (0.1 ед/сек)
            if self.current_energy < self.config.max_energy_capacity:
                energy_to_recover = min(energy_recovery_rate, 
                                        self.config.max_energy_capacity - self.current_energy)
                self.current_energy += energy_to_recover
            
            # Обновляем время и записываем состояние энергии
            current_time += 1
            remaining_time -= 1
            session.energy_history.append((current_time, self.current_energy))
        
        # Пользователь проводит в приложении всю сессию, но активно тапает только часть времени
        # Продолжаем записывать восстановление энергии до конца сессии
        remaining_session_time = duration - max_tapping_time
        if remaining_session_time > 0:
            for i in range(remaining_session_time):
                current_time += 1
                
                # Восстанавливаем энергию со скоростью 0.1 ед/сек
                if self.current_energy < self.config.max_energy_capacity:
                    energy_to_recover = min(energy_recovery_rate, 
                                           self.config.max_energy_capacity - self.current_energy)
                    self.current_energy += energy_to_recover
                    
                session.energy_history.append((current_time, self.current_energy))
        
        return session
    
    def _get_or_create_day(self, day_number: int) -> TapDay:
        """
        Получает или создает объект дня по его номеру.
        
        Args:
            day_number: Номер игрового дня
            
        Returns:
            TapDay: Объект дня
        """
        for day in self.days_data:
            if day.day == day_number:
                return day
        
        # День не найден, создаем новый
        new_day = TapDay(day=day_number)
        self.days_data.append(new_day)
        return new_day
    
    def _get_last_session(self) -> Optional[TapSession]:
        """
        Возвращает последнюю смоделированную сессию.
        
        Returns:
            Optional[TapSession]: Последняя сессия или None
        """
        if not self.days_data:
            return None
            
        last_day = max(self.days_data, key=lambda x: x.day)
        if not last_day.sessions:
            return None
            
        return max(last_day.sessions, key=lambda x: x.start_time) 