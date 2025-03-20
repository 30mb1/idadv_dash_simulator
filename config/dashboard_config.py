"""
Конфигурационный файл для настроек дашборда.
Содержит параметры интерфейса и отображения данных.
"""

# Общие настройки
APP_TITLE = "Анализ игровой механики Indonesian Adventure"
ASSETS_FOLDER = 'assets'
DEBUG_MODE = True
PORT = 8050

# Настройки экрана
DEFAULT_GRAPH_HEIGHT = 600
DEFAULT_FIGURE_LAYOUT = {
    "showlegend": True,
    "hovermode": "x unified",
    "legend": {
        "orientation": "h",
        "yanchor": "bottom",
        "y": 1.02,
        "xanchor": "center",
        "x": 0.5
    }
}

# Настройки интервалов и слайдеров
CHECKS_PER_DAY_MIN = 1
CHECKS_PER_DAY_MAX = 8
CHECKS_PER_DAY_DEFAULT = 5

COOLDOWN_MULTIPLIER_MIN = 0.5
COOLDOWN_MULTIPLIER_MAX = 2.0
COOLDOWN_MULTIPLIER_STEP = 0.1
COOLDOWN_MULTIPLIER_DEFAULT = 1.0

# Экономические параметры по умолчанию
DEFAULT_BASE_GOLD_PER_SEC = 0.56
DEFAULT_EARN_COEFFICIENT = 1.090824358

# Настройки стилей
STYLE_SECTION = {
    "marginBottom": "20px"
}

STYLE_METRICS_BOX = {
    "textAlign": "center", 
    "backgroundColor": "#f8f9fa", 
    "padding": "15px", 
    "borderRadius": "8px",
    "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
    "width": "30%",
    "margin": "10px"
}

# Стили для макета дашборда
STYLE_CONTAINER = {
    "display": "flex",
    "flexDirection": "row", 
    "height": "calc(100vh - 80px)",
    "width": "100%",
    "maxWidth": "1800px",
    "margin": "0 auto",
    "fontFamily": "Arial, sans-serif"
}

STYLE_SIDEBAR = {
    "width": "300px",
    "minWidth": "250px",
    "backgroundColor": "#f8f9fa",
    "padding": "20px",
    "boxShadow": "2px 0 10px rgba(0,0,0,0.1)",
    "overflow": "auto",
    "height": "100%",
    "position": "sticky",
    "top": "0"
}

STYLE_MAIN_CONTENT = {
    "flex": "1",
    "padding": "20px",
    "overflow": "auto",
    "height": "100%"
}

STYLE_HEADER = {
    "backgroundColor": "#343a40",
    "color": "white",
    "padding": "10px 20px",
    "marginBottom": "20px",
    "borderRadius": "5px",
    "boxShadow": "0 2px 4px rgba(0,0,0,0.2)"
}

STYLE_BUTTON = {
    "backgroundColor": "#007bff",
    "color": "white",
    "padding": "10px 15px",
    "border": "none",
    "borderRadius": "5px",
    "cursor": "pointer",
    "marginTop": "20px",
    "width": "100%",
    "fontWeight": "bold"
}

# Добавляем STYLE_FLEX_ROW, который используется в callbacks
STYLE_FLEX_ROW = {
    "display": "flex",
    "flexDirection": "row",
    "flexWrap": "wrap",
    "gap": "15px",
    "alignItems": "center"
}

# Настройки графиков
PLOT_COLORS = {
    "gold": "#ffd700",
    "xp": "#4CAF50",
    "keys": "#9c27b0",
    "income": "green",
    "expenses": "red",
    "balance": "blue",
    "level": "#FF5722"
}

# Интервалы времени для записи состояния (в секундах)
STATE_RECORD_INTERVAL = 86400  # 1 день 