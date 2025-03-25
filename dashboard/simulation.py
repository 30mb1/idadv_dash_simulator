"""
Коллбеки для запуска и управления симуляцией.
"""

import numpy as np
import pandas as pd
import dash
from dash import Input, Output, State, callback, html, dcc, no_update, MATCH, ALL
from typing import Dict, List, Any, Tuple, Optional
import json
from dash.exceptions import PreventUpdate

from simulator import Simulator
from config.simulation_config import create_sample_config
from utils.economy import format_time, calculate_gold_per_sec
from models.config import EconomyConfig, SimulationAlgorithm, SimulationConfig, StartingBalanceConfig, TappingConfig
from dashboard import app

def create_status_message(status_type: str, message: str, details: Optional[str] = None) -> html.Div:
    """
    Создает форматированное сообщение о статусе симуляции.
    
    Args:
        status_type: Тип статуса ('success', 'info', 'warning', 'error')
        message: Основное сообщение
        details: Дополнительная информация (опционально)
        
    Returns:
        html.Div: Отформатированный блок сообщения
    """
    status_colors = {
        'success': '#28a745',
        'info': '#6c757d',
        'warning': '#ffc107',
        'error': '#dc3545'
    }
    
    components = [html.P(message, style={"color": status_colors.get(status_type, '#6c757d')})]
    
    if details:
        components.append(html.P(details, style={"fontSize": "0.9em"}))
        
    return html.Div(components)

@app.callback(
    [Output("simulation-status", "children"),
     Output("simulation-data-store", "data"),
     Output("user-levels-store", "data"),
     Output("auto-run-store", "data")],
    [Input("run-simulation-button", "n_clicks")],
    [State("base-gold-per-sec-input", "value"),
     State("earn-coefficient-input", "value"),
     State("cooldown-multiplier-slider", "value"),
     State("check-times-store", "data"),
     State("game-duration-input", "value"),
     State("simulation-algorithm-radio", "value"),
     State("starting-gold-input", "value"),
     State("starting-xp-input", "value"),
     State("starting-keys-input", "value"),
     State("is-tapping-checkbox", "value"),
     State("max-energy-input", "value"),
     State("tap-speed-input", "value"),
     State("gold-per-tap-input", "value"),
     State("auto-run-store", "data")]
)
def run_simulation(n_clicks, base_gold, earn_coefficient, cooldown_multiplier, 
                  check_times_data, game_duration, simulation_algorithm, 
                  starting_gold, starting_xp, starting_keys, 
                  is_tapping, max_energy, tap_speed, tap_coef, auto_run_data):
    """
    Запускает симуляцию и возвращает результаты.
    
    Args:
        n_clicks: Количество нажатий на кнопку
        base_gold: Базовое значение золота в секунду
        earn_coefficient: Коэффициент роста
        cooldown_multiplier: Множитель кулдауна между улучшениями
        check_times_data: Данные о временах проверок
        game_duration: Длительность игровой сессии в минутах
        simulation_algorithm: Алгоритм симуляции улучшения локаций
        starting_gold: Начальное количество золота
        starting_xp: Начальный опыт
        starting_keys: Начальное количество ключей
        is_tapping: Флаг активации тапания
        max_energy: Максимальный запас энергии
        tap_speed: Скорость тапания (тапов в секунду)
        tap_coef: Множитель тапания (уровень персонажа * tap_coef = золото за тап)
        auto_run_data: Состояние флага автозапуска
        
    Returns:
        list: [статус, данные симуляции, уровни пользователя, флаг автозапуска]
    """
    # Для первичной загрузки страницы или если кнопка не была нажата, не запускаем симуляцию
    if n_clicks is None or n_clicks == 0:
        status_message = create_status_message(
            'info', 
            "Simulation not started. Set parameters and click 'Run Simulation' button.", 
            "Simulation data will be displayed after starting."
        )
        return status_message, no_update, no_update, {"auto_run": False}
    
    # Настраиваем и запускаем симуляцию
    try:
        # Создаем конфигурацию
        config = _create_simulation_config(
            base_gold=base_gold, 
            earn_coefficient=earn_coefficient, 
            cooldown_multiplier=cooldown_multiplier, 
            check_times_data=check_times_data, 
            game_duration=game_duration, 
            simulation_algorithm=simulation_algorithm,
            starting_gold=starting_gold,
            starting_xp=starting_xp,
            starting_keys=starting_keys,
            is_tapping=is_tapping,
            max_energy=max_energy,
            tap_speed=tap_speed,
            tap_coef=tap_coef
        )
        
        # Запускаем симуляцию
        simulator = Simulator(config)
        result = simulator.run_simulation()
        
        # Формируем сообщение об успешной симуляции
        completion_message = f"Simulation completed in {result.timestamp} seconds"
        status_message = create_status_message("success", "Simulation completed successfully", completion_message)
        
        # Получаем данные для отображения
        history_data = result.history
        config_data = {
            "base_gold": base_gold,
            "earn_coefficient": earn_coefficient,
            "cooldown_multiplier": cooldown_multiplier,
            "check_times": check_times_data.get("schedule", []),
            "game_duration": game_duration,
            "simulation_algorithm": simulation_algorithm,
            "max_level": max(simulator.workflow.user_levels.keys(), default=0)
        }
        
        # Данные об уровнях для графиков
        user_levels_data = {str(k): v.gold_per_sec for k, v in simulator.workflow.user_levels.items()}
        
    except Exception as e:
        status_message = create_status_message("error", "Error during simulation execution", str(e))
        return status_message, None, None, {"auto_run": False}
        
    # Данные симуляции для хранилища
    simulation_data = {
        "history": history_data, 
        "timestamp": result.timestamp, 
        "stop_reason": result.stop_reason,
        "config": config_data
    }
    
    return status_message, simulation_data, user_levels_data, {"auto_run": True}

def _create_simulation_config(base_gold: float, earn_coefficient: float, cooldown_multiplier: float, 
                             check_times_data: dict, game_duration: int, simulation_algorithm: str, 
                             starting_gold: float, starting_xp: float, starting_keys: int,
                             is_tapping: list, max_energy: float, tap_speed: float, tap_coef: float) -> SimulationConfig:
    """
    Создает конфигурацию симуляции на основе параметров.
    
    Args:
        base_gold: Базовое значение золота в секунду
        earn_coefficient: Коэффициент роста
        cooldown_multiplier: Множитель кулдауна между улучшениями
        check_times_data: Данные о временах проверок
        game_duration: Длительность игровой сессии в минутах
        simulation_algorithm: Алгоритм симуляции
        starting_gold: Начальное количество золота
        starting_xp: Начальный опыт
        starting_keys: Начальное количество ключей
        is_tapping: Флаг активации тапания
        max_energy: Максимальный запас энергии
        tap_speed: Скорость тапания (тапов в секунду)
        tap_coef: Множитель тапания (уровень персонажа * tap_coef = золото за тап)
        
    Returns:
        SimulationConfig: Конфигурация для симуляции
    """
    # Создаем конфигурацию
    config = create_sample_config()
    
    # Проверка и приведение параметров к допустимым значениям
    if base_gold is None or base_gold <= 0:
        base_gold = config.economy.base_gold_per_sec
        
    if earn_coefficient is None or earn_coefficient <= 0:
        earn_coefficient = config.economy.earn_coefficient
        
    if cooldown_multiplier is None or cooldown_multiplier <= 0:
        cooldown_multiplier = 1.0
        
    if simulation_algorithm is None:
        simulation_algorithm = SimulationAlgorithm.SEQUENTIAL.value
        
    if starting_gold is None or starting_gold < 0:
        starting_gold = 1000.0
        
    if starting_xp is None or starting_xp < 0:
        starting_xp = 1
        
    if starting_keys is None or starting_keys < 0:
        starting_keys = 1
        
    if game_duration is None or game_duration <= 0:
        game_duration = 15  # 15 минут по умолчанию
    
    # Значения тапания с защитой от None
    max_energy_value = int(max_energy) if max_energy is not None and max_energy > 0 else 700
    tap_speed_value = float(tap_speed) if tap_speed is not None and tap_speed > 0 else 3.0
    tap_coef_value = float(tap_coef) if tap_coef is not None and tap_coef > 0 else 1.0
    
    # Преобразуем длительность игровой сессии в секунды
    game_duration_seconds = game_duration * 60
    
    # Обновляем экономические настройки с начальным балансом и длительностью сессии
    config.economy = EconomyConfig(
        base_gold_per_sec=base_gold,
        earn_coefficient=earn_coefficient,
        starting_balance=StartingBalanceConfig(
            gold=starting_gold,
            xp=int(starting_xp),
            keys=int(starting_keys)
        ),
        game_duration=game_duration_seconds
    )
    
    # Обновляем значения gold_per_sec для каждого уровня пользователя
    # в соответствии с новыми параметрами экономики
    for level, level_config in config.user_levels.items():
        config.user_levels[level].gold_per_sec = calculate_gold_per_sec(base_gold, earn_coefficient, level)
    
    # Обновляем множитель кулдауна
    for level, cooldown in config.location_cooldowns.items():
        config.location_cooldowns[level] = int(cooldown * cooldown_multiplier)
    
    # Устанавливаем алгоритм симуляции
    config.simulation_algorithm = SimulationAlgorithm(simulation_algorithm)
    
    # Добавляем конфигурацию тапания, если она включена
    if is_tapping and isinstance(is_tapping, list) and 'is_tapping' in is_tapping:
        print(f"DEBUG: Creating tapping config with tap_coef={tap_coef_value}")
        try:
            tap_coef_value = float(tap_coef_value)
            if tap_coef_value <= 0:
                tap_coef_value = 1.0
        except (TypeError, ValueError):
            tap_coef_value = 1.0
        
        config.tapping = TappingConfig(
            is_tapping=True,
            max_energy_capacity=max_energy_value,
            tap_speed=tap_speed_value,
            tap_coef=tap_coef_value
        )
    else:
        # Если тапание отключено, создаем конфигурацию с is_tapping=False
        config.tapping = TappingConfig(
            is_tapping=False,
            max_energy_capacity=max_energy_value,
            tap_speed=tap_speed_value,
            tap_coef=tap_coef_value
        )
        print("DEBUG: Tapping is disabled in config")
    
    # Обновляем расписание проверок на основе введенных времен
    _update_check_schedule_from_times(config, check_times_data)
    
    return config

def _update_check_schedule_from_times(config: SimulationConfig, check_times_data: dict) -> None:
    """
    Обновляет расписание проверок в конфигурации на основе списка времен.
    
    Args:
        config: Конфигурация симуляции
        check_times_data: Данные о временах проверок
    """
    day_seconds = 86400  # секунд в дне
    
    # Проверяем наличие данных
    if not check_times_data or "schedule" not in check_times_data or not check_times_data["schedule"]:
        # Если данных нет, используем значения по умолчанию из конфигурации
        check_schedule = [
            28800,      # 08:00
            43200,      # 12:00
            57600,      # 16:00
            72000,      # 20:00
        ]
        config.check_schedule = check_schedule
        return
    
    # Преобразуем времена в секунды от начала дня
    check_schedule = []
    for time_str in check_times_data["schedule"]:
        try:
            # Парсим время в формате "HH:MM"
            hours, minutes = map(int, time_str.split(":"))
            seconds = hours * 3600 + minutes * 60
            check_schedule.append(seconds)
        except (ValueError, IndexError):
            # В случае неправильного формата пропускаем
            continue
    
    # Если не удалось получить ни одного корректного времени, используем значение по умолчанию
    if not check_schedule:
        check_schedule = [
            28800,      # 08:00
            43200,      # 12:00
            57600,      # 16:00
            72000       # 20:00
        ]
    
    # Сортируем расписание
    check_schedule.sort()
    
    # Обновляем расписание в конфигурации
    config.check_schedule = check_schedule

@app.callback(
    [Output("completion-time", "children"),
     Output("final-resources", "children")],
    [Input("simulation-data-store", "data"),
     Input("auto-run-store", "data")],
    prevent_initial_call=True
)
def update_completion_info(data, auto_run_data):
    """
    Обновляет информацию о завершении симуляции.
    
    Args:
        data: Данные симуляции
        auto_run_data: Данные о состоянии автозапуска
        
    Returns:
        list: [информация о времени, информация о ресурсах]
    """
    # Проверяем, была ли запущена симуляция
    if not data or not auto_run_data or not auto_run_data.get("auto_run"):
        await_run_message = html.Div([
            html.H5("Data not available", style={"color": "#6c757d"}),
            html.P("Start simulation to display information", style={"fontStyle": "italic"})
        ])
        return await_run_message, await_run_message
    
    if "history" not in data or not data["history"]:
        return "No data", "No data"
    
    history = data["history"]
    last_state = history[-1]
    balance = last_state["balance"]
    
    timestamp = data.get("timestamp", last_state["timestamp"])
    days = timestamp // 86400
    hours = (timestamp % 86400) // 3600
    
    completion_info = html.Div([
        html.H5("General information:"),
        html.P(f"Time passed: {days} days, {hours} hours ({timestamp} seconds)"),
        html.P(f"Stop reason: {data.get('stop_reason', 'Not specified')}")
    ])
    
    resources_info = html.Div([
        html.H5("Final resources:"),
        html.P(f"Gold: {balance['gold']:.2f}"),
        html.P(f"XP: {balance['xp']}"),
        html.P(f"Keys: {balance['keys']}"),
        html.P(f"Level: {balance['user_level']}"),
        html.P(f"Earn per second: {balance['earn_per_sec']:.2f}")
    ])
    
    return completion_info, resources_info


@app.callback(
    Output("key-metrics", "children"),
    [Input("simulation-data-store", "data"),
     Input("auto-run-store", "data")],
    prevent_initial_call=True
)
def update_key_metrics(data, auto_run_data):
    """
    Обновляет ключевые метрики симуляции.
    
    Args:
        data: Данные симуляции
        auto_run_data: Данные о состоянии автозапуска
        
    Returns:
        html.Div: Блок с метриками
    """
    # Проверяем, была ли запущена симуляция
    if not data or not auto_run_data or not auto_run_data.get("auto_run"):
        return html.Div([
            html.P("Start simulation to display metrics", 
                   style={"textAlign": "center", "color": "#6c757d", "fontStyle": "italic", "padding": "20px"})
        ])
    
    if "history" not in data or not data["history"]:
        return "No data"
    
    history = data["history"]
    
    # Собираем данные о улучшениях локаций
    location_upgrades = 0
    total_spent = 0
    
    for state in history:
        actions = state.get("actions", [])
        for action in actions:
            if action.get("type") == "location_upgrade":
                location_upgrades += 1
                total_spent += -action.get("gold_change", 0)  # Стоимость - это отрицательное изменение золота
    
    # Собираем данные о стагнации
    days_with_upgrades = set()
    for state in history:
        actions = state.get("actions", [])
        for action in actions:
            if action.get("type") == "location_upgrade" and "timestamp" in action:
                days_with_upgrades.add(action["timestamp"] // 86400)
    
    total_days = data.get("timestamp", history[-1]["timestamp"]) // 86400
    if total_days < 1:
        total_days = 1  # Чтобы избежать деления на ноль
        
    days_without_upgrades = total_days - len(days_with_upgrades)
    # Убедимся, что days_without_upgrades не отрицательное число
    days_without_upgrades = max(0, days_without_upgrades)
    days_without_upgrades_percent = (days_without_upgrades / total_days * 100) if total_days > 0 else 0
    
    # Стиль для блоков метрик
    style_box = {
        "textAlign": "center", 
        "backgroundColor": "#f8f9fa", 
        "padding": "15px", 
        "borderRadius": "8px",
        "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
        "width": "30%",
        "margin": "10px"
    }
    
    return html.Div([
        html.Div([
            html.H3(f"{location_upgrades}"),
            html.P("Location upgrades")
        ], style=style_box),
        
        html.Div([
            html.H3(f"{total_spent:,.0f}"),
            html.P("Spent gold")
        ], style=style_box),
        
        html.Div([
            html.H3(f"{days_without_upgrades_percent:.1f}%"),
            html.P(f"Days without upgrades ({days_without_upgrades} of {total_days})")
        ], style=style_box)
    ], style={"display": "flex", "flexDirection": "row", "justifyContent": "space-around", "flexWrap": "wrap"}) 

def create_time_dropdown(index: int, value: str) -> dcc.Dropdown:
    """
    Создает выпадающий список для выбора времени.
    
    Args:
        index: Индекс выпадающего списка
        value: Текущее значение времени
        
    Returns:
        dcc.Dropdown: Компонент выпадающего списка
    """
    return dcc.Dropdown(
        id={"type": "check-time-dropdown", "index": index},
        options=[
            {"label": f"{h:02d}:00", "value": f"{h:02d}:00"}
            for h in range(24)
        ],
        value=value,
        clearable=False,
        style={
            "width": "120px",
            "display": "inline-block",
            "marginRight": "10px"
        }
    )

@app.callback(
    Output("check-times-container", "children"),
    Output("check-times-store", "data"),
    [
        Input("add-check-time-button", "n_clicks"),
        Input({"type": "remove-check-time", "index": ALL}, "n_clicks"),
        Input({"type": "check-time-dropdown", "index": ALL}, "value")
    ],
    [
        State("check-times-store", "data"),
        State({"type": "check-time-dropdown", "index": ALL}, "id")
    ],
    prevent_initial_call=True
)
def update_check_times(add_clicks, remove_clicks, dropdown_values, store_data, dropdown_ids):
    """
    Обновляет расписание проверок при изменении.
    
    Args:
        add_clicks: Количество нажатий на кнопку добавления
        remove_clicks: Список нажатий на кнопки удаления
        dropdown_values: Значения всех выпадающих списков
        store_data: Текущие данные расписания
        dropdown_ids: ID всех выпадающих списков
        
    Returns:
        tuple: (список компонентов UI, обновленные данные расписания)
    """
    ctx_trigger = dash.callback_context.triggered[0]
    trigger_id = ctx_trigger["prop_id"]
    
    if not store_data or "schedule" not in store_data:
        schedule = ["08:00", "12:00", "16:00", "20:00"]
    else:
        schedule = store_data["schedule"]
    
    # Обработка нажатия на кнопку добавления
    if trigger_id == "add-check-time-button.n_clicks" and add_clicks:
        # Находим все доступные часы
        used_hours = set(schedule)
        available_hours = [f"{h:02d}:00" for h in range(24) if f"{h:02d}:00" not in used_hours]
        
        if available_hours:
            schedule.append(available_hours[0])
            schedule.sort()
    
    # Обработка нажатия на кнопку удаления
    elif "remove-check-time" in trigger_id:
        try:
            button_id = json.loads(trigger_id.split(".")[0])
            index = button_id.get("index")
            if index is not None and 0 <= index < len(schedule):
                schedule.pop(index)
        except (json.JSONDecodeError, ValueError, KeyError):
            pass
    
    # Обработка изменения значения в выпадающем списке
    elif "check-time-dropdown" in trigger_id:
        for i, (value, id_dict) in enumerate(zip(dropdown_values, dropdown_ids)):
            if i < len(schedule):
                schedule[i] = value
        schedule.sort()
    
    # Создаем компоненты UI
    children = []
    for i, time in enumerate(schedule):
        children.append(html.Div([
            create_time_dropdown(i, time),
            html.Button(
                "−",
                id={"type": "remove-check-time", "index": i},
                n_clicks=0,
                style={
                    "backgroundColor": "#ff4d4d",
                    "color": "white",
                    "border": "none",
                    "borderRadius": "4px",
                    "width": "30px",
                    "height": "30px",
                    "fontSize": "18px",
                    "cursor": "pointer"
                }
            )
        ], style={
            "display": "flex",
            "alignItems": "center",
            "marginBottom": "10px"
        }))
    
    return children, {"schedule": schedule} 