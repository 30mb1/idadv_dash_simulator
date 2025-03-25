#!/usr/bin/env python
"""
Скрипт для запуска дашборда Indonesian Adventure.

Запускает веб-сервер с дашбордом на указанном порту.
"""

import sys
import os

# Добавляем корневую директорию проекта в sys.path для корректного импорта модулей
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Импортируем параметры дашборда
from config.dashboard_config import PORT, DEBUG_MODE

# Импортируем и запускаем дашборд
from dashboard import app

if __name__ == "__main__":
    print(f"Запуск дашборда Indonesian Adventure на порту {PORT}")
    app.run_server(debug=DEBUG_MODE, port=PORT)