"""
Коллбеки для экономического анализа.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, State, callback, html

from utils.economy import calculate_gold_per_sec
from utils.plotting import create_subplot_figure, add_time_series, create_bar_chart
from utils.data_processing import extract_upgrades_timeline, extract_resource_data
from utils.export import export_gold_balance_table
from config.dashboard_config import PLOT_COLORS, STYLE_METRICS_BOX, STYLE_FLEX_ROW
from dashboard import app

@app.callback(
    [Output("gold-per-sec-progression", "figure"),
     Output("gold-per-sec-table", "data")],
    [Input("base-gold-per-sec-input", "value"),
     Input("earn-coefficient-input", "value")]
)
def update_gold_progression(base_gold, earn_coefficient):
    """
    Обновляет график и таблицу прогрессии gold/sec.
    
    Args:
        base_gold: Базовое значение золота в секунду
        earn_coefficient: Коэффициент роста
        
    Returns:
        list: [figure, table_data]
    """
    if base_gold is None or earn_coefficient is None:
        return {}, []
    
    # Рассчитываем значения для первых 10 уровней
    levels = list(range(1, 11))
    gold_per_sec_values = [calculate_gold_per_sec(base_gold, earn_coefficient, level) for level in levels]
    
    # Создаем фигуру
    fig = go.Figure()
    
    # Добавляем линейный график с точками
    fig.add_trace(go.Scatter(
        x=levels,
        y=gold_per_sec_values,
        name="Gold/sec",
        mode='lines+markers',
        line=dict(color=PLOT_COLORS["gold"], width=2),
        marker=dict(size=8),
        hovertemplate="Уровень %{x}<br>Gold/sec: %{y:.4f}"
    ))
    
    # Настраиваем макет
    fig.update_layout(
        title={
            'text': "Progression of gold earnings by levels",
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 20}
        },
        xaxis={
            'title': "Character level",
            'title_font': {'size': 14},
            'tickfont': {'size': 12},
            'gridcolor': 'lightgray'
        },
        yaxis={
            'title': "Gold per second (Gold/sec)",
            'title_font': {'size': 14},
            'tickfont': {'size': 12},
            'gridcolor': 'lightgray',
            'tickformat': '.4f'
        },
        showlegend=False,  # Убираем легенду, так как у нас один график
        hovermode="x unified",
        plot_bgcolor='white'
    )
    
    # Подготавливаем данные для таблицы
    table_data = []
    prev_value = None
    
    for level, value in zip(levels, gold_per_sec_values):
        growth = "-"
        if prev_value is not None:
            growth_pct = (value / prev_value - 1) * 100
            growth = f"+{growth_pct:.2f}%"
        
        table_data.append({
            "level": level,
            "gold_per_sec": f"{value:.4f}",
            "gold_per_hour": f"{value * 3600:.2f}",
            "gold_per_day": f"{value * 86400:.2f}",
            "growth": growth
        })
        
        prev_value = value
    
    return fig, table_data


@app.callback(
    Output("economy-analysis", "figure"),
    [Input("simulation-data-store", "data"),
     Input("auto-run-store", "data")],
    prevent_initial_call=True
)
def update_economy_analysis(data, auto_run_data):
    """
    Обновляет анализ экономики.
    
    Args:
        data: Данные симуляции
        auto_run_data: Данные о состоянии автозапуска
        
    Returns:
        go.Figure: График с анализом экономики
    """
    # Проверяем, была ли запущена симуляция
    if not auto_run_data or not auto_run_data.get("auto_run"):
        empty_figure = go.Figure()
        empty_figure.update_layout(
            title="Start simulation to display data",
            xaxis={"visible": False},
            yaxis={"visible": False},
            annotations=[{
                "text": "No data. Click 'Start simulation' button",
                "xref": "paper",
                "yref": "paper",
                "showarrow": False,
                "font": {"size": 16}
            }]
        )
        return empty_figure

    if data is None or "history" not in data:
        empty_figure = go.Figure()
        empty_figure.update_layout(
            title="No data to display",
            xaxis={"visible": False},
            yaxis={"visible": False},
            annotations=[{
                "text": "Simulation history is empty",
                "xref": "paper",
                "yref": "paper",
                "showarrow": False,
                "font": {"size": 16}
            }]
        )
        return empty_figure
    
    history = data["history"]
    if not history:
        return {}
    
    # Создаем график с двумя подграфиками
    fig = create_subplot_figure(
        rows=2, cols=1,
        subplot_titles=(
            "Economy balance",
            "Income and expenses by day"
        ),
        vertical_spacing=0.2,
        height=800,
        row_heights=[0.6, 0.4]
    )
    
    # Собираем все действия из истории для первого графика (баланс золота)
    balance_data = []
    
    for state in history:
        for action in state["actions"]:
            # Вычисляем день и время
            timestamp = action["timestamp"]
            day = timestamp / 86400
            hours = (timestamp % 86400) // 3600
            minutes = ((timestamp % 86400) % 3600) // 60
            
            # Добавляем баланс после действия
            balance_data.append({
                "day": day,
                "time": f"{hours:02d}:{minutes:02d}",
                "balance": action["gold_after"]
            })
    
    # Если нет данных в истории действий, используем состояния
    if not balance_data:
        for state in history:
            timestamp = state["timestamp"]
            hours = (timestamp % 86400) // 3600
            minutes = ((timestamp % 86400) % 3600) // 60
            balance_data.append({
                "day": timestamp / 86400,
                "time": f"{hours:02d}:{minutes:02d}",
                "balance": state["balance"]["gold"]
            })
    
    # Сортируем по времени
    balance_data = sorted(balance_data, key=lambda x: x["day"])
    
    # 1. График баланса золота
    if balance_data:
        df_balance = pd.DataFrame(balance_data)
        
        # Добавляем график баланса
        fig.add_trace(
            go.Scatter(
                x=df_balance["day"],
                y=df_balance["balance"],
                name="Баланс золота",
                line=dict(color="#FFD700", width=2),
                mode="lines",
                hovertemplate="День %{x:.1f}<br>Время: %{customdata}<br>Баланс: %{y:,.0f} золота<extra></extra>",
                customdata=df_balance["time"]
            ),
            row=1, col=1
        )
        
        # Настраиваем оси для первого графика
        fig.update_xaxes(
            title_text="Day of game",
            gridcolor='lightgray',
            showgrid=True,
            row=1, col=1
        )
        fig.update_yaxes(
            title_text="Gold balance",
            gridcolor='lightgray',
            showgrid=True,
            tickformat=",.0f",
            row=1, col=1
        )
    
    # Извлекаем данные об улучшениях для второго графика
    upgrades_timeline = extract_upgrades_timeline(history)
    
    # Извлекаем данные о ресурсах для расчетов
    resources_data = []
    for state in history:
        resources_data.append({
            "timestamp": state["timestamp"],
            "gold": state["balance"]["gold"],
            "earn_per_sec": state["balance"]["earn_per_sec"],
            "day": state["timestamp"] / 86400,
            "earn_per_hour": state["balance"]["earn_per_sec"] * 3600,
            "earn_per_day": state["balance"]["earn_per_sec"] * 86400
        })
    
    # 2. График доходов и расходов по дням
    # Рассчитываем доходы по дням
    income_by_day = {}
    for i in range(1, len(resources_data)):
        day = int(resources_data[i]["day"])
        prev_day = int(resources_data[i-1]["day"])
        
        # Если остаемся в том же дне, пропускаем
        if day == prev_day:
            continue
        
        # Средний заработок в секунду за предыдущий день
        avg_earn = resources_data[i-1]["earn_per_sec"]
        # Доход за день (в секундах)
        day_income = avg_earn * 86400
        income_by_day[prev_day] = day_income
    
    # Рассчитываем расходы по дням
    expenses_by_day = {}
    for upgrade in upgrades_timeline:
        day = int(upgrade["day"])
        expenses_by_day[day] = expenses_by_day.get(day, 0) - upgrade["gold_change"]  # Стоимость - это отрицательное изменение золота
    
    # Преобразуем в DataFrame
    days = sorted(set(income_by_day.keys()) | set(expenses_by_day.keys()))
    df_economy = pd.DataFrame({
        "day": days,
        "income": [income_by_day.get(day, 0) for day in days],
        "expenses": [expenses_by_day.get(day, 0) for day in days]
    })
    
    # Создаем bar chart для доходов и расходов
    fig.add_trace(
        go.Bar(
            x=df_economy["day"],
            y=df_economy["income"],
            name="Доход за день",
            marker_color="#76EE00",
            hovertemplate="День %{x}<br>Доход: %{y:,.0f} золота<extra></extra>"
        ),
        row=2, col=1
    )
    
    fig.add_trace(
        go.Bar(
            x=df_economy["day"],
            y=df_economy["expenses"],
            name="Расходы за день",
            marker_color="#FF6347",
            hovertemplate="День %{x}<br>Расходы: %{y:,.0f} золота<extra></extra>"
        ),
        row=2, col=1
    )
    
    # Настраиваем оси для второго графика
    fig.update_xaxes(
        title_text="Day of game",
        gridcolor='lightgray',
        showgrid=True,
        dtick=1,  # Шаг сетки в 1 день
        row=2, col=1
    )
    fig.update_yaxes(
        title_text="Gold",
        gridcolor='lightgray',
        showgrid=True,
        tickformat=",.0f",
        row=2, col=1
    )
    
    # Обновляем общий layout
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
        paper_bgcolor='white',
        hovermode='x unified'
    )
    
    return fig


@app.callback(
    Output("economy-metrics", "children"),
    [Input("simulation-data-store", "data"),
     Input("auto-run-store", "data")],
    prevent_initial_call=True
)
def update_economy_metrics(data, auto_run_data):
    """
    Обновляет метрики экономики.
    
    Args:
        data: Данные симуляции
        auto_run_data: Данные о состоянии автозапуска
        
    Returns:
        html.Div: Блок с метриками
    """
    # Проверяем, была ли запущена симуляция
    if not auto_run_data or not auto_run_data.get("auto_run"):
        return html.Div("Start simulation to display data", 
                        style={"textAlign": "center", "padding": "20px"})

    if data is None or "history" not in data:
        return html.Div("No data", style={"textAlign": "center", "padding": "20px"})
    
    history = data["history"]
    if not history:
        return html.Div("Simulation history is empty", style={"textAlign": "center", "padding": "20px"})
    
    # Собираем данные об экономике
    total_income = 0
    total_expenses = 0
    
    for state in history:
        for action in state["actions"]:
            if action["type"] == "location_upgrade":
                total_expenses += -action["gold_change"]  # Стоимость - это отрицательное изменение золота
    
    # Приблизительный расчет дохода
    for i in range(1, len(history)):
        # Время между состояниями
        time_diff = history[i]["timestamp"] - history[i-1]["timestamp"]
        # Средний заработок в секунду за период
        avg_earn = (history[i]["balance"]["earn_per_sec"] + history[i-1]["balance"]["earn_per_sec"]) / 2
        # Доход за период
        period_income = avg_earn * time_diff
        total_income += period_income
   
    return html.Div([
        html.Div([
            html.H3(f"{total_income:,.0f}"),
            html.P("Total earned")
        ], style=STYLE_METRICS_BOX),
        
        html.Div([
            html.H3(f"{total_expenses:,.0f}"),
            html.P("Total spent")
        ], style=STYLE_METRICS_BOX),
        
    ], style=STYLE_FLEX_ROW)


@app.callback(
    Output("upgrades-history-table", "data"),
    Output("upgrades-history-table", "columns"),
    [Input("simulation-data-store", "data"),
     Input("auto-run-store", "data")],
    prevent_initial_call=True
)
def update_upgrades_history(data, auto_run_data):
    """
    Обновляет таблицу баланса золота.
    
    Args:
        data: Данные симуляции
        auto_run_data: Данные о состоянии автозапуска
        
    Returns:
        list: [данные таблицы, столбцы]
    """
    # Проверяем, была ли запущена симуляция
    if not auto_run_data or not auto_run_data.get("auto_run"):
        empty_columns = [
            {"name": "День", "id": "День"},
            {"name": "Информация", "id": "Информация"}
        ]
        empty_data = [{"День": "", "Информация": "Start simulation to display data"}]
        return empty_data, empty_columns
    
    if data is None or "history" not in data:
        return [], []
    
    history = data["history"]
    if not history:
        return [], []
    
    # Собираем все действия из истории
    actions_data = []
    export_data = []
    
    for state in history:
        for action in state["actions"]:
            # Вычисляем день и время
            timestamp = action["timestamp"]
            day = timestamp // 86400
            time_seconds = timestamp % 86400
            hours = time_seconds // 3600
            minutes = (time_seconds % 3600) // 60
            
            # Формируем описание события в зависимости от типа
            if action["type"] == "passive_income":
                event = action["description"]
            elif action["type"] == "location_upgrade":
                event = f"Location upgrade {action['location_id']} (lvl.{action['new_level']})"
            elif action["type"] == "level_up":
                event = f"Level up to {action['new_level']}"
            else:
                continue
            
            # Данные для отображения
            actions_data.append({
                "День": day + 1,  # День начинается с 1
                "Время": f"{hours:02d}:{minutes:02d}",
                "Событие": event,
                "Золото ДО": f"{action['gold_before']:,.0f}",
                "Изменение": f"{action['gold_change']:,.0f}",
                "Баланс": f"{action['gold_after']:,.0f}"
            })
            
            # Данные для экспорта CSV
            export_data.append({
                "День": day + 1,  # День начинается с 1
                "Время": f"{hours:02d}:{minutes:02d}",
                "Событие": event,
                "Золото ДО": action['gold_before'],
                "Изменение": action['gold_change'],
                "Баланс": action['gold_after']
            })
    
    # Сортируем по дню и времени
    actions_data = sorted(actions_data, key=lambda x: (x["День"], x["Время"]))
    export_data = sorted(export_data, key=lambda x: (x["День"], x["Время"]))
    
    # Определяем столбцы
    columns = [
        {"name": "День", "id": "День"},
        {"name": "Время", "id": "Время"},
        {"name": "Событие", "id": "Событие"},
        {"name": "Золото ДО", "id": "Золото ДО"},
        {"name": "Изменение", "id": "Изменение"},
        {"name": "Баланс", "id": "Баланс"}
    ]
    
    # Экспортируем таблицу в CSV (используем необработанные числовые данные)
    export_gold_balance_table(export_data)
    
    return actions_data, columns


@app.callback(
    Output("sensitivity-analysis", "figure"),
    [Input("base-gold-per-sec-input", "value"),
     Input("earn-coefficient-input", "value")]
)
def update_sensitivity_analysis(base_gold, earn_coefficient):
    """
    Обновляет график анализа чувствительности.
    
    Args:
        base_gold: Базовое значение золота в секунду
        earn_coefficient: Коэффициент роста
        
    Returns:
        go.Figure: График анализа чувствительности
    """
    if base_gold is None or earn_coefficient is None:
        return {}
    
    # Создаем вариации параметров
    base_variations = [base_gold * (1 + i*0.05) for i in range(-4, 5)]
    coef_variations = [earn_coefficient * (1 + i*0.01) for i in range(-4, 5)]
    
    # Фиксируем один параметр и варьируем другой
    levels = [1, 5, 10]
    
    # Создаем график
    fig = create_subplot_figure(
        rows=2, cols=1,
        subplot_titles=(
            "Влияние базового значения gold/sec",
            "Влияние коэффициента роста"
        ),
        vertical_spacing=0.3
    )
    
    # Анализ влияния базового значения
    for level in levels:
        values = [calculate_gold_per_sec(base, earn_coefficient, level) for base in base_variations]
        add_time_series(
            fig, 
            x=base_variations, 
            y=values, 
            name=f"Уровень {level}",
            mode="lines+markers",
            row=1, col=1
        )
    
    # Анализ влияния коэффициента
    for level in levels:
        values = [calculate_gold_per_sec(base_gold, coef, level) for coef in coef_variations]
        add_time_series(
            fig, 
            x=coef_variations, 
            y=values, 
            name=f"Уровень {level}",
            mode="lines+markers",
            row=2, col=1
        )
    
    # Обновляем макет
    fig.update_layout(
        height=700
    )
    
    # Обновляем подписи осей
    fig.update_xaxes(title="Базовое значение gold/sec", row=1, col=1)
    fig.update_yaxes(title="Итоговое значение gold/sec", row=1, col=1)
    
    fig.update_xaxes(title="Коэффициент роста", row=2, col=1)
    fig.update_yaxes(title="Итоговое значение gold/sec", row=2, col=1)
    
    return fig 