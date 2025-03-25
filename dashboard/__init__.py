"""
Модуль дашборда для симулятора Indonesian Adventure.
"""

from dash import Dash
from dash import html, dcc


def create_dash_app():
    """
    Создаёт и настраивает экземпляр приложения Dash.
    
    Returns:
        dash.Dash: Настроенное приложение Dash
    """
    from config.dashboard_config import APP_TITLE, ASSETS_FOLDER
    from dashboard.layout import create_layout

    app_instance = Dash(
        __name__,
        title=APP_TITLE,
        assets_folder=ASSETS_FOLDER,
        suppress_callback_exceptions=True
    )
    
    # Устанавливаем макет с хранилищем auto-run
    full_layout = create_layout(APP_TITLE)
    full_layout.children.insert(0, dcc.Store(id="auto-run-store", data={"auto_run": False}))
    app_instance.layout = full_layout
    
    return app_instance

# Создаем экземпляр приложения
app = create_dash_app()

from dashboard import callbacks
