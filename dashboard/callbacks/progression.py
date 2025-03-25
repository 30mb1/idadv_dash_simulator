"""
Коллбеки для анализа прогресса игрока.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash import Input, Output, State, callback, html

from utils.plotting import create_subplot_figure, add_time_series, create_bar_chart
from utils.data_processing import (
    extract_upgrades_timeline, 
    calculate_intervals,
    calculate_upgrades_per_day,
    calculate_stagnation_periods,
    extract_level_data,
    extract_resource_data,
    extract_daily_events_data
)
from utils.export import export_daily_events_table
from config.dashboard_config import PLOT_COLORS
from dashboard import app

@app.callback(
    [Output("progression-pace", "figure"),
     Output("stagnation-analysis", "figure"),
     Output("progression-stats", "children")],
    [Input("simulation-data-store", "data"),
     Input("auto-run-store", "data")],
    prevent_initial_call=True
)
def update_progression_analysis(data, auto_run_data):
    """
    Обновляет анализ темпа прогрессии.
    
    Args:
        data: Данные симуляции
        auto_run_data: Данные о состоянии автозапуска
        
    Returns:
        list: [график темпа, график стагнации, статистика]
    """
    # Проверяем, была ли запущена симуляция
    if not auto_run_data or not auto_run_data.get("auto_run"):
        empty_figure = go.Figure()
        empty_figure.update_layout(
            title="Run simulation to display data",
            xaxis={"visible": False},
            yaxis={"visible": False},
            annotations=[{
                "text": "No data. Click 'Run simulation' button",
                "xref": "paper",
                "yref": "paper",
                "showarrow": False,
                "font": {"size": 16}
            }]
        )
        return empty_figure, empty_figure, "Run simulation to display data"
    
    if data is None or "history" not in data:
        return {}, {}, "No data"
    
    history = data["history"]
    if not history:
        return {}, {}, "No data"
    
    # Анализ времени между улучшениями
    pace_fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=(
            "Time between upgrades (hours)",
            "Number of upgrades per day"
        ),
        vertical_spacing=0.15
    )
    
    # Собираем данные о времени между улучшениями
    upgrades_timeline = extract_upgrades_timeline(history)
    intervals = calculate_intervals(upgrades_timeline)
    
    # Статистика интервалов
    avg_interval = np.mean(intervals) if intervals else 0
    median_interval = np.median(intervals) if intervals else 0
    max_interval = np.max(intervals) if intervals else 0
    
    # График времени между улучшениями
    pace_fig.add_trace(
        go.Scatter(
            x=list(range(len(intervals))),
            y=intervals,
            mode="lines+markers",
            name="Interval",
            line=dict(color="royalblue"),
            hovertemplate="Upgrade %{x}<br>Interval: %{y:.2f} hours"
        ),
        row=1, col=1
    )
    
    # Добавляем средний интервал
    pace_fig.add_trace(
        go.Scatter(
            x=[0, len(intervals)-1],
            y=[avg_interval, avg_interval],
            mode="lines",
            name="Average interval",
            line=dict(color="red", dash="dash"),
            hovertemplate="Average interval: %{y:.2f} hours"
        ),
        row=1, col=1
    )
    
    # Количество улучшений в день
    upgrades_per_day = calculate_upgrades_per_day(upgrades_timeline)
    days = sorted(upgrades_per_day.keys())
    counts = [upgrades_per_day[day] for day in days]
    
    pace_fig.add_trace(
        go.Bar(
            x=days,
            y=counts,
            name="Upgrades per day",
            marker_color="green",
            hovertemplate="Day %{x}<br>Upgrades: %{y}"
        ),
        row=2, col=1
    )
    
    # Средние улучшения в день
    avg_upgrades = np.mean(counts) if counts else 0
    pace_fig.add_trace(
        go.Scatter(
            x=[min(days), max(days)] if days else [0, 0],
            y=[avg_upgrades, avg_upgrades],
            mode="lines",
            name="Average number of upgrades",
            line=dict(color="red", dash="dash"),
            hovertemplate="Average: %{y:.2f}"
        ),
        row=2, col=1
    )
    
    pace_fig.update_layout(
        height=600,
        hovermode="x unified"
    )
    
    # Анализ периодов стагнации
    stagnation_fig = go.Figure()
    
    # Находим периоды стагнации
    stagnation_periods = calculate_stagnation_periods(upgrades_timeline)
    
    if stagnation_periods:
        # Сортируем по длительности
        stagnation_periods.sort(key=lambda x: x["duration"], reverse=True)
        
        # Добавляем столбцы
        days = [period["start_day"] for period in stagnation_periods]
        durations = [period["duration_days"] for period in stagnation_periods]
        
        stagnation_fig.add_trace(
            go.Bar(
                x=days,
                y=durations,
                name="Duration",
                marker_color="indianred",
                hovertemplate="Start: Day %{x:.1f}<br>Duration: %{y:.1f} days"
            )
        )
        
        # Добавляем границу для значимых периодов стагнации (> 1 дня)
        stagnation_fig.add_trace(
            go.Scatter(
                x=[min(days), max(days)],
                y=[1, 1],
                mode="lines",
                name="Border (1 day)",
                line=dict(color="black", dash="dash")
            )
        )
        
        stagnation_fig.update_layout(
            title="Stagnation periods",
            xaxis_title="Start day",
            yaxis_title="Duration (days)",
            hovermode="x unified"
        )
    else:
        stagnation_fig.add_trace(
            go.Scatter(
                x=[0],
                y=[0],
                mode="markers",
                marker=dict(opacity=0),
                hoverinfo="none"
            )
        )
        stagnation_fig.update_layout(
            title="No stagnation periods",
            xaxis_title="Day",
            yaxis_title="Duration (days)"
        )
    
    # Статистика прогресса
    days_with_upgrades = len(set(int(upgrade["day"]) for upgrade in upgrades_timeline))
    total_days = int(history[-1]["timestamp"] // 86400)
    efficiency = days_with_upgrades / total_days * 100 if total_days > 0 else 0
    
    stats = html.Div([
        html.Div([
            html.H4("Progress statistics:"),
            html.Ul([
                html.Li(f"Average time between upgrades: {avg_interval:.2f} hours"),
                html.Li(f"Median time between upgrades: {median_interval:.2f} hours"),
                html.Li(f"Maximum time between upgrades: {max_interval:.2f} hours"),
                html.Li(f"Average number of upgrades per day: {avg_upgrades:.2f}"),
                html.Li(f"Days with upgrades: {days_with_upgrades} from {total_days} ({efficiency:.1f}%)"),
                html.Li(f"Number of stagnation periods (>1 day): {len([p for p in stagnation_periods if p['duration_days'] > 1])}"),
            ])
        ])
    ])
    
    return pace_fig, stagnation_fig, stats


@app.callback(
    Output("user-level-progress", "figure"),
    [Input("simulation-data-store", "data"),
     Input("auto-run-store", "data")],
    prevent_initial_call=True
)
def update_user_level_progress(data, auto_run_data):
    """
    Обновляет график прогресса уровня пользователя.
    
    Args:
        data: Данные симуляции
        auto_run_data: Данные о состоянии автозапуска
        
    Returns:
        go.Figure: График прогресса уровня
    """
    # Проверяем, была ли запущена симуляция
    if not auto_run_data or not auto_run_data.get("auto_run"):
        empty_figure = go.Figure()
        empty_figure.update_layout(
            title="Run simulation to display data",
            xaxis={"visible": False},
            yaxis={"visible": False},
            annotations=[{
                "text": "No data. Click 'Run simulation' button",
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
    
    # Извлекаем данные об уровне
    level_data = extract_level_data(history)
    
    # Создаем график
    fig = create_subplot_figure(
        rows=2, cols=1,
        subplot_titles=("Character level", "Character XP"),
        vertical_spacing=0.3
    )
    
    # Добавляем график уровня
    days = [entry["day"] for entry in level_data]
    levels = [entry["level"] for entry in level_data]
    
    add_time_series(
        fig, 
        x=days, 
        y=levels, 
        name="Level", 
        color=PLOT_COLORS["level"],
        mode="lines+markers",
        row=1, col=1
    )
    
    # Добавляем график опыта
    xp = [entry["xp"] for entry in level_data]
    
    add_time_series(
        fig, 
        x=days, 
        y=xp, 
        name="XP", 
        color=PLOT_COLORS["xp"],
        row=2, col=1
    )
    
    # Настраиваем оси
    fig.update_yaxes(title="Level", row=1, col=1)
    fig.update_xaxes(title="Day", row=1, col=1)
    
    fig.update_yaxes(title="XP", row=2, col=1)
    fig.update_xaxes(title="Day", row=2, col=1)
    
    return fig


@app.callback(
    Output("resources-over-time", "figure"),
    [Input("simulation-data-store", "data"),
     Input("auto-run-store", "data")],
    prevent_initial_call=True
)
def update_resources_over_time(data, auto_run_data):
    """
    Обновляет график ресурсов во времени.
    
    Args:
        data: Данные симуляции
        auto_run_data: Данные о состоянии автозапуска
        
    Returns:
        go.Figure: График ресурсов
    """
    # Проверяем, была ли запущена симуляция
    if not auto_run_data or not auto_run_data.get("auto_run"):
        empty_figure = go.Figure()
        empty_figure.update_layout(
            title="Run simulation to display data",
            xaxis={"visible": False},
            yaxis={"visible": False},
            annotations=[{
                "text": "No data. Click 'Run simulation' button",
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
    
    # Извлекаем данные о ресурсах
    resource_data = extract_resource_data(history)
    
    # Создаем график
    fig = create_subplot_figure(
        rows=3, cols=1,
        subplot_titles=("Gold", "Keys", "Earnings (gold/sec)"),
        row_heights=[0.33, 0.33, 0.33],
        vertical_spacing=0.15
    )
    
    # Добавляем график золота
    days = [r["day"] for r in resource_data]
    gold = [r["gold"] for r in resource_data]
    keys = [r["keys"] for r in resource_data]
    earn_per_sec = [r["earn_per_sec"] for r in resource_data]
    
    add_time_series(
        fig, 
        x=days, 
        y=gold, 
        name="Gold", 
        color=PLOT_COLORS["gold"],
        row=1, col=1
    )
    
    add_time_series(
        fig, 
        x=days, 
        y=keys, 
        name="Keys", 
        color=PLOT_COLORS["keys"],
        row=2, col=1
    )
    
    add_time_series(
        fig, 
        x=days, 
        y=earn_per_sec, 
        name="Gold/sec", 
        color=PLOT_COLORS["income"],
        row=3, col=1
    )
    
    # Настраиваем оси
    for row in range(1, 4):
        fig.update_xaxes(title="Day", row=row, col=1)
    
    fig.update_yaxes(title="Gold", row=1, col=1)
    fig.update_yaxes(title="Keys", row=2, col=1)
    fig.update_yaxes(title="Gold/sec", row=3, col=1)
    
    return fig


@app.callback(
    Output("coins-per-level-table", "children"),
    Input("user-levels-store", "data"),
    prevent_initial_call=True
)
def update_coins_per_level_table(user_levels_data):
    """
    Обновляет таблицу gold/sec по уровням.
    
    Args:
        user_levels_data: Данные об уровнях пользователя
        
    Returns:
        html.Table: Таблица с gold/sec
    """
    if not user_levels_data:
        return "Нет данных"
    
    # Создаем таблицу
    header = html.Tr([
        html.Th("Level"),
        html.Th("XP required"),
        html.Th("Gold/sec"),
        html.Th("Keys reward"),
        html.Th("Gold/hour"),
        html.Th("Gold/day")
    ])
    
    rows = []
    prev_gold_per_sec = None
    
    for level, level_data in sorted(user_levels_data.items(), key=lambda x: int(x[0])):
        gold_per_sec = level_data["gold_per_sec"]
        xp_required = level_data["xp_required"]
        keys_reward = level_data["keys_reward"]
        
        growth = ""
        if prev_gold_per_sec is not None:
            growth_pct = (gold_per_sec / prev_gold_per_sec - 1) * 100
            growth = f" (+{growth_pct:.1f}%)"
        
        gold_per_hour = gold_per_sec * 3600
        gold_per_day = gold_per_sec * 86400
        
        row = html.Tr([
            html.Td(f"{level}"),
            html.Td(f"{xp_required:,}"),
            html.Td(f"{gold_per_sec:.4f}{growth}"),
            html.Td(f"{keys_reward}"),
            html.Td(f"{gold_per_hour:.2f}"),
            html.Td(f"{gold_per_day:.2f}")
        ])
        
        rows.append(row)
        prev_gold_per_sec = gold_per_sec
    
    return html.Table([
        html.Thead(header),
        html.Tbody(rows)
    ], style={"borderCollapse": "collapse", "width": "100%"})


@app.callback(
    [Output("daily-events-table", "data"),
     Output("daily-events-table", "columns")],
    [Input("simulation-data-store", "data"),
     Input("auto-run-store", "data")],
    prevent_initial_call=True
)
def update_daily_events_table(data, auto_run_data):
    """
    Обновляет таблицу с ежедневными событиями игры.
    
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
    
    # Получаем данные о событиях по дням
    daily_events = extract_daily_events_data(history)
    
    if not daily_events:
        return [], []
    
    # Форматируем данные для таблицы
    table_data = []
    # Данные для экспорта в CSV (сохраняем числовые значения)
    export_data = []
    
    for event in daily_events:
        # Форматируем диапазон уровней
        level_range = event["level_range"]
        if level_range[0] == 0 and level_range[1] == 0:
            level_range_str = "-"
        else:
            level_range_str = f"{level_range[0]} → {level_range[1]}"
        
        # Добавляем строку в таблицу для отображения (с форматированием)
        table_data.append({
            "Day": event["day"],
            "Sessions count": event["sessions_count"],
            "Session minutes": round(event["session_minutes"], 1),
            "Level ups": event["level_ups"],
            "Level range": level_range_str,
            "Upgrades count": event["upgrades_count"],
            "New locations": event["new_locations"],
            "Gold (balance)": f"{event['gold']:,.0f}",
            "Gold (earned)": f"{event['gold_earned']:,.0f}",
            "Gold (spent)": f"{event['gold_spent']:,.0f}",
            "XP (balance)": f"{event['xp']:,.0f}",
            "XP (earned)": f"{event['xp_earned']:,.0f}",
            "Keys (balance)": event["keys"],
            "Keys (earned)": event["keys_earned"],
            "Keys (spent)": event["keys_spent"]
        })
        
        # Добавляем строку для экспорта (с числовыми значениями)
        export_data.append({
            "Day": event["day"],
            "Sessions count": event["sessions_count"],
            "Session minutes": round(event["session_minutes"], 1),
            "Level ups": event["level_ups"],
            "Level range": level_range_str,
            "Upgrades count": event["upgrades_count"],
            "New locations": event["new_locations"],
            "Gold (balance)": event["gold"],
            "Gold (earned)": event["gold_earned"],
            "Gold (spent)": event["gold_spent"],
            "XP (balance)": event["xp"],
            "XP (earned)": event["xp_earned"],
            "Keys (balance)": event["keys"],
            "Keys (earned)": event["keys_earned"],
            "Keys (spent)": event["keys_spent"]
        })
    
    # Определяем колонки
    columns = [
        {"name": "Day", "id": "Day", "type": "numeric"},
        {"name": "Sessions count", "id": "Sessions count", "type": "numeric"},
        {"name": "Session minutes", "id": "Session minutes", "type": "numeric"},
        {"name": "Level ups", "id": "Level ups", "type": "numeric"},
        {"name": "Level range", "id": "Level range"},
        {"name": "Upgrades count", "id": "Upgrades count", "type": "numeric"},
        {"name": "New locations", "id": "New locations", "type": "numeric"},
        {"name": "Gold (balance)", "id": "Gold (balance)"},
        {"name": "Gold (earned)", "id": "Gold (earned)"},
        {"name": "Gold (spent)", "id": "Gold (spent)"},
        {"name": "XP (balance)", "id": "XP (balance)"},
        {"name": "XP (earned)", "id": "XP (earned)"},
        {"name": "Keys (balance)", "id": "Keys (balance)", "type": "numeric"},
        {"name": "Keys (earned)", "id": "Keys (earned)", "type": "numeric"},
        {"name": "Keys (spent)", "id": "Keys (spent)", "type": "numeric"}
    ]
    
    # Экспортируем таблицу в CSV (используем неформатированные данные)
    export_daily_events_table(export_data)
    
    return table_data, columns 