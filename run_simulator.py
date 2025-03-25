#!/usr/bin/env python
"""
Скрипт для тестового запуска симулятора Indonesian Adventure.

Демонстрирует работу симулятора с настройками по умолчанию или 
с пользовательскими настройками через аргументы командной строки.
"""

import sys
import os
import argparse
import json
from pathlib import Path

# Добавляем корневую директорию проекта в sys.path для корректного импорта модулей
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from simulator import Simulator
from config.simulation_config import create_sample_config
from utils.economy import format_time
from utils.validation import is_config_valid
from models.config import EconomyConfig, SimulationAlgorithm, StartingBalanceConfig, TappingConfig

def parse_arguments():
    """
    Разбор аргументов командной строки.
    
    Returns:
        argparse.Namespace: Аргументы командной строки
    """
    parser = argparse.ArgumentParser(description="Запуск симулятора Indonesian Adventure")
    
    # Экономические параметры
    parser.add_argument(
        "--base-gold", 
        type=float, 
        help="Базовое значение золота в секунду"
    )
    
    parser.add_argument(
        "--earn-coefficient", 
        type=float, 
        help="Коэффициент роста золота"
    )
    
    # Начальный баланс
    parser.add_argument(
        "--starting-gold", 
        type=float, 
        help="Начальное количество золота",
        default=1000.0
    )
    
    parser.add_argument(
        "--starting-xp", 
        type=int, 
        help="Начальный опыт",
        default=1
    )
    
    parser.add_argument(
        "--starting-keys", 
        type=int, 
        help="Начальное количество ключей",
        default=1
    )
    
    # Параметры симуляции
    parser.add_argument(
        "--cooldown-multiplier", 
        type=float, 
        help="Множитель кулдауна между улучшениями"
    )
    
    parser.add_argument(
        "--checks-per-day", 
        type=int, 
        help="Количество проверок в день"
    )
    
    parser.add_argument(
        "--algorithm", 
        choices=["sequential", "first_available"],
        help="Алгоритм симуляции (sequential или first_available)"
    )
    
    parser.add_argument(
        "--export", 
        type=str, 
        help="Путь для экспорта результатов в JSON"
    )
    
    # Параметры тапания
    parser.add_argument(
        "--enable-tapping", 
        action="store_true", 
        help="Включить механику тапания"
    )
    
    parser.add_argument(
        "--disable-tapping", 
        action="store_true", 
        help="Выключить механику тапания"
    )
    
    parser.add_argument(
        "--max-energy", 
        type=int,
        help="Максимальный запас энергии для тапания"
    )
    
    parser.add_argument(
        "--tap-speed", 
        type=float,
        help="Скорость тапания (тапов в секунду)"
    )
    
    parser.add_argument(
        "--tap-coef", 
        type=float,
        help="Множитель золота за тап (уровень персонажа * tap_coef = золото за тап)"
    )
    
    parser.add_argument(
        "--verbose", 
        action="store_true", 
        help="Подробный вывод"
    )
    
    return parser.parse_args()

def main():
    """Функция для запуска симуляции с поддержкой аргументов командной строки."""
    args = parse_arguments()
    
    # Создаем конфигурацию с настройками по умолчанию
    config = create_sample_config()
    
    # Обновляем конфигурацию на основе аргументов
    if args.base_gold is not None or args.earn_coefficient is not None:
        base_gold = args.base_gold if args.base_gold is not None else config.economy.base_gold_per_sec
        earn_coefficient = args.earn_coefficient if args.earn_coefficient is not None else config.economy.earn_coefficient
        
        # Создаем новый объект StartingBalanceConfig для начальных значений
        starting_balance = StartingBalanceConfig(
            gold=args.starting_gold,
            xp=args.starting_xp,
            keys=args.starting_keys
        )
        
        config.economy = EconomyConfig(
            base_gold_per_sec=base_gold,
            earn_coefficient=earn_coefficient,
            starting_balance=starting_balance,
            game_duration=config.economy.game_duration
        )
    
    # Обновляем множитель кулдауна
    if args.cooldown_multiplier is not None:
        for level, cooldown in config.location_cooldowns.items():
            config.location_cooldowns[level] = int(cooldown * args.cooldown_multiplier)
    
    # Обновляем алгоритм симуляции
    if args.algorithm is not None:
        config.simulation_algorithm = SimulationAlgorithm(args.algorithm)
    
    # Обновляем настройки тапания
    if hasattr(config, 'tapping'):
        # Включаем/выключаем тапание
        if args.enable_tapping:
            config.tapping.is_tapping = True
        elif args.disable_tapping:
            config.tapping.is_tapping = False
            
        # Обновляем параметры тапания, если они указаны
        if args.max_energy is not None:
            config.tapping.max_energy_capacity = args.max_energy
            
        if args.tap_speed is not None:
            config.tapping.tap_speed = args.tap_speed
            
        if args.tap_coef is not None:
            config.tapping.tap_coef = args.tap_coef
    
    # Обновляем расписание проверок
    if args.checks_per_day is not None:
        day_seconds = 86400  # секунд в дне
        checks_per_day = args.checks_per_day
        
        if checks_per_day > 0:
            # Создаем равномерное распределение проверок в течение дня (с 8:00 до 22:00)
            active_hours = 14  # с 8:00 до 22:00
            active_seconds = active_hours * 3600
            start_time = 8 * 3600  # 8:00
            
            if checks_per_day == 1:
                # Если одна проверка, ставим её в середине дня
                config.check_schedule = [start_time + active_seconds // 2]
            else:
                # Если несколько проверок, распределяем равномерно
                check_interval = active_seconds / (checks_per_day - 1) if checks_per_day > 1 else active_seconds
                config.check_schedule = [int(start_time + i * check_interval) for i in range(checks_per_day)]
    
    # Проверяем валидность конфигурации
    if not is_config_valid(config):
        print("Ошибка: некорректная конфигурация")
        sys.exit(1)
    
    # Создаем симулятор и запускаем симуляцию
    print("Запуск симуляции...")
    simulator = Simulator(config)
    result = simulator.run_simulation()
    
    # Выводим результаты
    time_passed = format_time(result.timestamp)
    print(f"Симуляция завершена за {time_passed}")
    
    # Выводим финальное состояние
    print(f"Final state:")
    print(f"  - User level: {simulator.workflow.balance.user_level}")
    print(f"  - Gold: {simulator.workflow.balance.gold:.2f}")
    print(f"  - XP: {simulator.workflow.balance.xp}")
    print(f"  - Keys: {simulator.workflow.balance.keys}")
    print(f"  - Earn per sec: {simulator.workflow.balance.earn_per_sec:.2f}")
    
    # Отображаем информацию о тапании, если оно включено
    if simulator.config.tapping and simulator.config.tapping.is_tapping:
        # Получаем значения с проверкой на None
        max_energy = simulator.config.tapping.max_energy_capacity or 700
        tap_speed = simulator.config.tapping.tap_speed or 3.0
        tap_coef = simulator.config.tapping.tap_coef or 0.1
        
        print("\nTapping information:")
        print(f"  - Status: {'Enabled' if simulator.config.tapping.is_tapping else 'Disabled'}")
        print(f"  - Energy capacity: {max_energy}")
        print(f"  - Tap speed: {tap_speed:.1f} taps/sec")
        print(f"  - Tap coef: {tap_coef:.2f}")
        
        # Расчет золота от тапания за все дни симуляции
        days_simulated = result.timestamp // 86400 + 1
        
        # Получаем финальный уровень персонажа для расчета
        final_user_level = simulator.workflow.balance.user_level
        gold_per_tap = final_user_level * tap_coef
        
        # Расчет золота от тапания с учетом уровня персонажа
        tapping_gold_per_day = max_energy * 0.7 * gold_per_tap
        total_tapping_gold = tapping_gold_per_day * days_simulated
        
        print(f"  - Final user level: {final_user_level}")
        print(f"  - Gold per tap: {gold_per_tap:.2f} (level {final_user_level} * coef {tap_coef:.2f})")
        print(f"  - Estimated tapping gold per day: {tapping_gold_per_day:.2f}")
        print(f"  - Total tapping gold for {days_simulated} days: {total_tapping_gold:.2f}")
        print(f"  - Share in total income: {(total_tapping_gold / simulator.workflow.balance.gold * 100):.1f}%")
    
    # Если указан флаг --verbose, выводим подробную информацию
    if args.verbose:
        print("\nLocation information:")
        for loc_id, location in sorted(simulator.workflow.locations.items()):
            status = "Available" if location.available else "Not available"
            print(f"  - Location {loc_id}: level {location.current_level}, {status}")
    
    # Экспортируем результат, если указан путь
    if args.export:
        export_path = Path(args.export)
        export_dir = export_path.parent
        
        # Создаем директорию, если не существует
        if not export_dir.exists() and str(export_dir) != ".":
            export_dir.mkdir(parents=True, exist_ok=True)
        
        # Добавляем информацию о тапании, если оно включено
        tapping_info = {}
        if simulator.config.tapping and simulator.config.tapping.is_tapping:
            # Получаем значения с проверкой на None
            max_energy = simulator.config.tapping.max_energy_capacity or 700
            tap_speed = simulator.config.tapping.tap_speed or 3.0
            tap_coef = simulator.config.tapping.tap_coef or 0.1
            
            days_simulated = result.timestamp // 86400 + 1
            tapping_gold_per_day = max_energy * 0.7 * tap_coef
            total_tapping_gold = tapping_gold_per_day * days_simulated
            
            tapping_info = {
                "enabled": simulator.config.tapping.is_tapping,
                "max_energy": max_energy,
                "tap_speed": tap_speed,
                "tap_coef": tap_coef,
                "gold_per_day": tapping_gold_per_day,
                "total_gold": total_tapping_gold,
                "share_in_total_income": (total_tapping_gold / simulator.workflow.balance.gold * 100)
            }
        
        with open(export_path, 'w', encoding='utf-8') as f:
            # Преобразуем историю в сериализуемый формат
            serializable_history = [state for state in result.history]
            json.dump({
                "timestamp": result.timestamp,
                "stop_reason": result.stop_reason,
                "final_state": simulator.result_summary,
                "tapping": tapping_info,
                "history": serializable_history if args.verbose else []
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\nРезультаты экспортированы в {args.export}")

if __name__ == "__main__":
    main() 