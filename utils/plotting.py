"""
Утилиты для построения графиков.
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Any, Tuple, Optional
import pandas as pd

from config.dashboard_config import PLOT_COLORS, DEFAULT_FIGURE_LAYOUT

def create_subplot_figure(
    rows: int, 
    cols: int, 
    subplot_titles: Tuple[str, ...], 
    row_heights: Optional[List[float]] = None,
    vertical_spacing: float = 0.15,
    horizontal_spacing: float = 0.1,
    height: int = 600,
    specs: Optional[List[List[Dict[str, Any]]]] = None
) -> go.Figure:
    """
    Создает фигуру с подграфиками.
    
    Args:
        rows: Количество строк
        cols: Количество столбцов
        subplot_titles: Заголовки подграфиков
        row_heights: Высоты строк
        vertical_spacing: Вертикальный интервал между графиками
        horizontal_spacing: Горизонтальный интервал между графиками
        height: Высота фигуры
        specs: Спецификации для каждого подграфика (тип, вторичная ось и т.д.)
        
    Returns:
        go.Figure: Фигура с подграфиками
    """
    fig = make_subplots(
        rows=rows, 
        cols=cols, 
        subplot_titles=subplot_titles,
        row_heights=row_heights,
        vertical_spacing=vertical_spacing,
        horizontal_spacing=horizontal_spacing,
        specs=specs
    )
    
    # Применяем базовые настройки
    fig.update_layout(
        height=height,
        **DEFAULT_FIGURE_LAYOUT
    )
    
    return fig

def add_time_series(
    fig: go.Figure, 
    x: List[float], 
    y: List[float], 
    name: str, 
    color: str = None,
    mode: str = "lines",
    row: int = 1, 
    col: int = 1,
    hovertemplate: str = None
) -> go.Figure:
    """
    Добавляет временной ряд на график.
    
    Args:
        fig: Фигура для добавления графика
        x: Значения оси X
        y: Значения оси Y
        name: Название ряда
        color: Цвет линии
        mode: Режим отображения (lines, markers, lines+markers)
        row: Номер строки в сетке подграфиков
        col: Номер столбца в сетке подграфиков
        hovertemplate: Шаблон для всплывающей подсказки
        
    Returns:
        go.Figure: Обновленная фигура
    """
    if color is None and name.lower() in PLOT_COLORS:
        color = PLOT_COLORS[name.lower()]
    elif color is None:
        color = "blue"
        
    if hovertemplate is None:
        hovertemplate = f"{name}: %{{y}}<br>День %{{x:.1f}}"
    
    fig.add_trace(
        go.Scatter(
            x=x,
            y=y,
            mode=mode,
            name=name,
            line=dict(color=color, width=2),
            hovertemplate=hovertemplate
        ),
        row=row, col=col
    )
    
    return fig

def create_bar_chart(
    fig: go.Figure, 
    x: List[str], 
    y: List[float], 
    name: str, 
    color: str = None,
    text: List = None,
    row: int = 1, 
    col: int = 1,
    hovertemplate: str = None
) -> go.Figure:
    """
    Добавляет столбчатую диаграмму на график.
    
    Args:
        fig: Фигура для добавления графика
        x: Значения оси X
        y: Значения оси Y
        name: Название ряда
        color: Цвет столбцов
        text: Текст для отображения на столбцах
        row: Номер строки в сетке подграфиков
        col: Номер столбца в сетке подграфиков
        hovertemplate: Шаблон для всплывающей подсказки
        
    Returns:
        go.Figure: Обновленная фигура
    """
    if color is None and name.lower() in PLOT_COLORS:
        color = PLOT_COLORS[name.lower()]
    elif color is None:
        color = "blue"
        
    if hovertemplate is None:
        hovertemplate = f"{name}: %{{y}}<br>%{{x}}"
    
    bar_trace = go.Bar(
        x=x,
        y=y,
        name=name,
        marker_color=color,
        hovertemplate=hovertemplate
    )
    
    if text is not None:
        bar_trace.text = text
        bar_trace.textposition = "auto"
    
    fig.add_trace(bar_trace, row=row, col=col)
    
    return fig 