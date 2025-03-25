"""
Коллбеки для анализа локаций.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, State, callback, html

from utils.plotting import create_subplot_figure, add_time_series, create_bar_chart
from utils.data_processing import extract_location_data, extract_upgrades_timeline
from utils.export import export_location_upgrades_table
from dashboard import app
from config.simulation_config import create_sample_config

@app.callback(
    Output("locations-upgrades", "figure"),
    [Input("simulation-data-store", "data"),
     Input("auto-run-store", "data")],
    prevent_initial_call=True
)
def update_locations_analysis(data, auto_run_data):
    """
    Обновляет анализ локаций.
    
    Args:
        data: Данные симуляции
        auto_run_data: Данные о состоянии автозапуска
        
    Returns:
        go.Figure: График с анализом локаций
    """
    # Проверяем, была ли запущена симуляция
    if not auto_run_data or not auto_run_data.get("auto_run"):
        empty_figure = go.Figure()
        empty_figure.update_layout(
            title="Run simulation to display data",
            xaxis={"visible": False},
            yaxis={"visible": False},
            annotations=[{
                "text": "No data. Click 'Run simulation'",
                "xref": "paper",
                "yref": "paper",
                "showarrow": False,
                "font": {"size": 16}
            }]
        )
        return empty_figure
    
    if data is None or "history" not in data:
        return {}
    
    history = data["history"]
    if not history:
        return {}
    
    # Извлекаем данные о локациях
    locations_data = {}
    for state in history:
        for loc_id, loc_state in state["locations"].items():
            loc_id = int(loc_id)
            if loc_id not in locations_data:
                locations_data[loc_id] = {
                    "current_level": loc_state["current_level"],
                    "available": loc_state["available"],
                    "upgrades_count": 0,
                    "total_cost": 0,
                    "total_xp": 0,
                    "total_keys": 0
                }
            else:
                locations_data[loc_id].update({
                    "current_level": loc_state["current_level"],
                    "available": loc_state["available"]
                })
    
    # Извлекаем данные об улучшениях
    upgrades_timeline = extract_upgrades_timeline(history)
    
    # Обновляем данные о локациях на основе улучшений
    for upgrade in upgrades_timeline:
        loc_id = int(upgrade["location_id"])
        if loc_id in locations_data:
            locations_data[loc_id]["upgrades_count"] += 1
            locations_data[loc_id]["total_cost"] += -upgrade["gold_change"]
            locations_data[loc_id]["total_xp"] += upgrade["xp_change"]
            locations_data[loc_id]["total_keys"] += upgrade["keys_change"]
    
    # Проверяем наличие данных об улучшениях
    if not upgrades_timeline:
        # Создаем пустой график
        fig = go.Figure()
        fig.update_layout(
            title="No data about location upgrades",
            height=600
        )
        return fig
    
    # Создаем график с двумя подграфиками
    fig = create_subplot_figure(
        rows=2, cols=1,
        subplot_titles=(
            "Location upgrades progress over time",
            "Impact of Cooldown on progress"
        ),
        vertical_spacing=0.15,
        height=800,
        row_heights=[0.6, 0.4]
    )
    
    # 1. График прогресса улучшений во времени
    timeline_data = {}
    for upgrade in upgrades_timeline:
        loc_id = upgrade["location_id"]
        if loc_id not in timeline_data:
            timeline_data[loc_id] = {
                "days": [],
                "levels": [],
                "costs": [],
                "xp_rewards": []
            }
        timeline_data[loc_id]["days"].append(upgrade["day"])
        timeline_data[loc_id]["levels"].append(upgrade["new_level"])
        timeline_data[loc_id]["costs"].append(-upgrade["gold_change"])  # Стоимость - это отрицательное изменение золота
        timeline_data[loc_id]["xp_rewards"].append(upgrade["xp_change"])
    
    # Создаем цветовую схему для локаций
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
    
    for i, (loc_id, data) in enumerate(timeline_data.items()):
        color = colors[i % len(colors)]  # Циклически используем цвета
        fig.add_trace(
            go.Scatter(
                x=data["days"],
                y=data["levels"],
                name=f"Location {loc_id}",
                mode="lines+markers",
                line=dict(width=2, color=color),
                marker=dict(size=8, color=color),
                hovertemplate="Day: %{x:.1f}<br>Level: %{y}<extra>Location %{customdata}</extra>",
                legendgroup=f"Location {loc_id}",
                customdata=[loc_id] * len(data["days"])
            ),
            row=1, col=1
        )
    
    # 2. График влияния Cooldown
    cooldown_data = {}
    for upgrade in upgrades_timeline:
        loc_id = upgrade["location_id"]
        if loc_id not in cooldown_data:
            cooldown_data[loc_id] = {
                "upgrade_intervals": [],
                "levels": []
            }
        
        # Находим интервал до следующего улучшения этой локации
        next_upgrade = next(
            (u for u in upgrades_timeline 
             if u["location_id"] == loc_id and u["day"] > upgrade["day"]),
            None
        )
        if next_upgrade:
            # Преобразуем интервал из дней в минуты (дни * 24 часа * 60 минут)
            interval = (next_upgrade["day"] - upgrade["day"]) * 24
            cooldown_data[loc_id]["upgrade_intervals"].append(interval)
            cooldown_data[loc_id]["levels"].append(upgrade["new_level"])
    
    for i, (loc_id, data) in enumerate(cooldown_data.items()):
        if data["upgrade_intervals"]:
            color = colors[i % len(colors)]  # Используем тот же цвет, что и в первом графике
            fig.add_trace(
                go.Scatter(
                    x=data["levels"],
                    y=data["upgrade_intervals"],
                    name=f"Location {loc_id}",
                    mode="lines+markers",
                    line=dict(width=2, color=color),
                    marker=dict(size=8, color=color),
                    hovertemplate="Level: %{x}<br>Interval: %{y:.1f} hours<extra>Location %{customdata}</extra>",
                    legendgroup=f"Location {loc_id}",
                    showlegend=False,  # Не показываем в легенде, так как уже есть в первом графике
                    customdata=[loc_id] * len(data["upgrade_intervals"])
                ),
                row=2, col=1
            )
    
    # Обновляем оси
    fig.update_xaxes(
        title_text="Game day",
        gridcolor='lightgray',
        showgrid=True,
        row=1, col=1
    )
    fig.update_yaxes(
        title_text="Location level",
        gridcolor='lightgray',
        showgrid=True,
        row=1, col=1
    )
    
    fig.update_xaxes(
        title_text="Location level",
        gridcolor='lightgray',
        showgrid=True,
        row=2, col=1
    )
    fig.update_yaxes(
        title_text="Interval to the next upgrade (hours)",
        gridcolor='lightgray',
        showgrid=True,
        row=2, col=1
    )
    
    # Обновляем layout
    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        ),
        margin=dict(t=100, r=50, b=50, l=50),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    return fig


@app.callback(
    [Output("progress-details-table", "data"),
     Output("progress-details-table", "columns")],
    [Input("simulation-data-store", "data"),
     Input("auto-run-store", "data")],
    prevent_initial_call=True
)
def update_progress_details(data, auto_run_data):
    """
    Обновляет таблицу с детальной информацией о прогрессе.
    
    Args:
        data: Данные симуляции
        auto_run_data: Данные о состоянии автозапуска
        
    Returns:
        list: [данные таблицы, столбцы]
    """
    # Проверяем, была ли запущена симуляция
    if not auto_run_data or not auto_run_data.get("auto_run"):
        empty_columns = [
            {"name": "Day", "id": "Day"},
            {"name": "Information", "id": "Information"}
        ]
        empty_data = [{"Day": "", "Information": "Run simulation to display data"}]
        return empty_data, empty_columns
    
    if data is None or "history" not in data:
        return [], []
    
    history = data["history"]
    if not history:
        return [], []
    
    # Формируем данные для таблицы
    table_data = []
    
    for state in history:
        day = state["timestamp"] // 86400
        time = state["timestamp"] % 86400
        # Пропускаем промежуточные состояния в тот же день
        if table_data and table_data[-1]["Day"] == day:
            continue
        
        table_data.append({
            "Day": day,
            "Time": f"{time // 3600:02d}:{time % 3600 // 60:02d}:{time % 60:02d}",
            "Gold": state["balance"]["gold"],
            "XP": state["balance"]["xp"],
            "Keys": state["balance"]["keys"],
            "Level": state["balance"]["user_level"],
            "Earnings (gold/sec)": state["balance"]["earn_per_sec"],
            "Earnings (gold/day)": state["balance"]["earn_per_sec"] * 86400,
        })
    
    # Определяем столбцы
    columns = [
        {"name": "Day", "id": "Day"},
        {"name": "Time", "id": "Time"},
        {"name": "Gold", "id": "Gold", "type": "numeric", "format": {"specifier": ",.2f"}},
        {"name": "XP", "id": "XP", "type": "numeric", "format": {"specifier": ",.0f"}},
        {"name": "Keys", "id": "Keys"},
        {"name": "Level", "id": "Level"},
        {"name": "Earnings (gold/sec)", "id": "Earnings (gold/sec)", "type": "numeric", "format": {"specifier": ",.4f"}},
        {"name": "Earnings (gold/day)", "id": "Earnings (gold/day)", "type": "numeric", "format": {"specifier": ",.2f"}},
    ]
    
    return table_data, columns

@app.callback(
    [Output("location-history-table", "data"),
     Output("location-history-table", "columns")],
    [Input("simulation-data-store", "data"),
     Input("auto-run-store", "data")],
    prevent_initial_call=True
)
def update_location_history(data, auto_run_data):
    """
    Обновляет таблицу истории улучшений локаций.
    
    Args:
        data: Данные симуляции
        auto_run_data: Данные о состоянии автозапуска
        
    Returns:
        tuple: (данные таблицы, колонки таблицы)
    """
    # Проверяем, была ли запущена симуляция
    if not auto_run_data or not auto_run_data.get("auto_run"):
        empty_columns = [
            {"name": "Day", "id": "Day"},
            {"name": "Information", "id": "Information"}
        ]
        empty_data = [{"Day": "", "Information": "Run simulation to display data"}]
        return empty_data, empty_columns
    
    if data is None or "history" not in data:
        return [], []
    
    history = data["history"]
    if not history:
        return [], []
    
    # Получаем данные об улучшениях
    upgrades_timeline = extract_upgrades_timeline(history)
    
    if not upgrades_timeline:
        return [], []
    
    # Форматируем данные для таблицы
    table_data = []
    export_data = []
    
    for upgrade in upgrades_timeline:
        # Вычисляем день и время
        timestamp = upgrade["timestamp"]
        day = int(timestamp // 86400)
        time_seconds = int(timestamp % 86400)
        hours = time_seconds // 3600
        minutes = (time_seconds % 3600) // 60
        seconds = (time_seconds % 3600) % 60
        
        # Данные для отображения (отформатированные)
        table_data.append({
            "Day": day + 1,  # День начинается с 1
            "Time": f"{hours:02d}:{minutes:02d}:{seconds:02d}",
            "Location": f"Location {upgrade['location_id']}",
            "New level": upgrade["new_level"],
            "Gold before": f"{upgrade['gold_before']:,.0f}",
            "Cost": f"{-upgrade['gold_change']:,.0f}",  # Стоимость - это отрицательное изменение золота
            "Gold balance": f"{upgrade['gold_after']:,.0f}",
            "XP before": f"{upgrade['xp_before']:,.0f}",
            "XP reward": f"{upgrade['xp_change']:,.0f}",
            "XP balance": f"{upgrade['xp_after']:,.0f}",
            "Keys before": f"{upgrade['keys_before']:,.0f}",
            "Keys reward": f"{upgrade['keys_change']:,.0f}",
            "Keys balance": f"{upgrade['keys_after']:,.0f}"
        })
        
        # Данные для экспорта CSV (численные значения)
        export_data.append({
            "Day": day + 1,  # День начинается с 1
            "Time": f"{hours:02d}:{minutes:02d}:{seconds:02d}",
            "Location": f"Location {upgrade['location_id']}",
            "New level": upgrade["new_level"],
            "Gold before": upgrade['gold_before'],
            "Cost": -upgrade['gold_change'],  # Стоимость - это отрицательное изменение золота
            "Gold balance": upgrade['gold_after'],
            "XP before": upgrade['xp_before'],
            "XP reward": upgrade['xp_change'],
            "XP balance": upgrade['xp_after'],
            "Keys before": upgrade['keys_before'],
            "Keys reward": upgrade['keys_change'],
            "Keys balance": upgrade['keys_after']
        })
    
    # Сортируем по дню и времени
    table_data = sorted(table_data, key=lambda x: (x["Day"], x["Time"]))
    export_data = sorted(export_data, key=lambda x: (x["Day"], x["Time"]))
    
    # Определяем колонки
    columns = [
        {"name": "Day", "id": "Day", "type": "numeric"},
        {"name": "Time", "id": "Time"},
        {"name": "Location", "id": "Location"},
        {"name": "New level", "id": "New level", "type": "numeric"},
        {"name": "Gold before", "id": "Gold before"},
        {"name": "Cost", "id": "Cost"},
        {"name": "Gold balance", "id": "Gold balance"},
        {"name": "XP before", "id": "XP before"},
        {"name": "XP reward", "id": "XP reward"},
        {"name": "XP balance", "id": "XP balance"},
        {"name": "Keys before", "id": "Keys before"},
        {"name": "Keys reward", "id": "Keys reward"},
        {"name": "Keys balance", "id": "Keys balance"}
    ]
    
    # Экспортируем таблицу в CSV (используем данные с числовыми значениями)
    export_location_upgrades_table(export_data)
    
    return table_data, columns

@app.callback(
    [Output("locations-parameters-table", "data"),
     Output("locations-parameters-table", "columns")],
    [Input("simulation-data-store", "data"),
     Input("auto-run-store", "data")],
    prevent_initial_call=True
)
def update_locations_parameters(data, auto_run_data):
    """
    Обновляет таблицу параметров локаций.
    
    Args:
        data: Данные симуляции
        auto_run_data: Данные о состоянии автозапуска
        
    Returns:
        list: [данные таблицы, столбцы]
    """
    # Проверяем, была ли запущена симуляция
    if not auto_run_data or not auto_run_data.get("auto_run"):
        empty_columns = [
            {"name": "Location", "id": "Location"},
            {"name": "Information", "id": "Information"}
        ]
        empty_data = [{"Location": "", "Information": "Run simulation to display data"}]
        return empty_data, empty_columns
    
    if data is None or "locations" not in data:
        return [], []
    
    locations = data["locations"]
    if not locations:
        return [], []
    
    # Остальной код без изменений... 

@app.callback(
    [Output("locations-cost-table", "data"),
     Output("locations-cost-table", "columns"),
     Output("locations-cost-table", "style_data_conditional")],
    [Input("simulation-data-store", "data"),
     Input("auto-run-store", "data")],
    prevent_initial_call=True
)
def update_locations_cost_table(data, auto_run_data):
    """
    Обновляет таблицу стоимостей локаций.
    
    Args:
        data: Данные симуляции
        auto_run_data: Данные о состоянии автозапуска
        
    Returns:
        list: [данные таблицы, столбцы, условные стили]
    """
    # Проверяем, была ли запущена симуляция
    if not auto_run_data or not auto_run_data.get("auto_run") or data is None:
        empty_columns = [{"name": "Location", "id": "location_id"}, {"name": "Status", "id": "status"}]
        empty_data = [{"location_id": "", "status": "Run simulation to display data"}]
        return empty_data, empty_columns, []
    
    # Создаем новую конфигурацию, поскольку у нас есть только параметры из data
    from config.simulation_config import create_sample_config
    
    # Получаем базовую конфигурацию
    try:
        config = create_sample_config()
        locations = config.locations
        
        # Максимальное количество уровней
        max_level = 0
        for loc_id, loc_config in locations.items():
            max_level = max(max_level, max(loc_config.levels.keys()))
        
        # Создаем столбцы для таблицы
        columns = [{"name": "Location", "id": "location_id"}]
        for level in range(1, max_level + 1):
            columns.append({"name": f"Level {level}", "id": f"level_{level}"})
        
        # Создаем данные таблицы
        table_data = []
        location_rarity = {}  # Для хранения редкости локаций
        
        for loc_id, loc_config in sorted(locations.items(), key=lambda x: int(x[0])):
            row = {"location_id": f"Location {loc_id}"}
            
            # Сохраняем редкость локации
            location_rarity[loc_id] = loc_config.rarity
            
            # Заполняем стоимость уровней
            for level in range(1, max_level + 1):
                if level in loc_config.levels:
                    level_data = loc_config.levels[level]
                    row[f"level_{level}"] = f"{level_data.cost:,}".replace(",", " ")
                else:
                    row[f"level_{level}"] = ""
            
            table_data.append(row)
        
        # Создаем условные стили для раскраски строк по редкости
        style_data_conditional = []
        rarity_colors = {
            "COMMON": "#f0f8ff",  # Светло-голубой для обычных локаций
            "RARE": "#f5f0ff",    # Светло-фиолетовый для редких
            "LEGENDARY": "#fffbeb" # Светло-золотой для легендарных
        }
        
        # Добавляем условные стили для строк каждой локации
        for loc_id, rarity in location_rarity.items():
            # Получаем название редкости из enum
            rarity_name = str(rarity).split('.')[-1]
            color = rarity_colors.get(rarity_name, "#ffffff")
            
            style_data_conditional.append({
                "if": {"filter_query": f"{{location_id}} = \"Location {loc_id}\""},
                "backgroundColor": color
            })
        
        return table_data, columns, style_data_conditional
    
    except Exception as e:
        print(f"ERROR: Failed to generate locations cost table: {str(e)}")
        empty_columns = [{"name": "Location", "id": "location_id"}, {"name": "Error", "id": "error"}]
        empty_data = [{"location_id": "", "error": f"Error generating table: {str(e)}"}]
        return empty_data, empty_columns, [] 