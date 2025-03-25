"""
Функции для экспорта данных в CSV формат.
"""

import os
import pandas as pd
from datetime import datetime
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('idadv_export')


def ensure_output_dir(directory='output'):
    """
    Проверяет существование директории для экспорта и создает ее, если необходимо.
    
    Args:
        directory (str): Путь к директории
    
    Returns:
        str: Путь к директории
    """
    # Создаем абсолютный путь, если передан относительный
    if not os.path.isabs(directory):
        # Получаем путь к корню проекта (родительская директория utils)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)  # Go up only one level to stay in project
        full_path = os.path.join(project_root, directory)
    else:
        full_path = directory
        
    # Создаем директорию, если её нет
    if not os.path.exists(full_path):
        try:
            os.makedirs(full_path)
            logger.info(f"Создана директория для экспорта: {full_path}")
        except Exception as e:
            logger.error(f"Ошибка при создании директории {full_path}: {str(e)}")
            raise
    
    return full_path


def export_table_to_csv(data, filename, directory='output', include_timestamp=True):
    """
    Экспортирует таблицу в CSV файл.
    
    Args:
        data (list): Список словарей с данными
        filename (str): Имя файла (без расширения)
        directory (str): Директория для сохранения
        include_timestamp (bool): Добавлять временную метку к имени файла
    
    Returns:
        str: Путь к созданному файлу
    """
    if not data:
        logger.warning(f"Попытка экспорта пустой таблицы '{filename}' прервана.")
        return None
    
    # Создаем директорию, если её нет
    full_directory = ensure_output_dir(directory)
    
    # Преобразуем данные в DataFrame
    df = pd.DataFrame(data)
    
    # Добавляем временную метку к имени файла, если необходимо
    if include_timestamp:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        full_filename = f"{filename}_{timestamp}.csv"
    else:
        full_filename = f"{filename}.csv"
    
    # Полный путь к файлу
    filepath = os.path.join(full_directory, full_filename)
    
    try:
        # Сохраняем в CSV
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        logger.info(f"Таблица '{filename}' сохранена в '{filepath}' ({len(data)} строк)")
    except Exception as e:
        logger.error(f"Ошибка при сохранении таблицы '{filename}': {str(e)}")
        return None
    
    return filepath


def export_daily_events_table(data, directory='output'):
    """
    Экспортирует таблицу событий по дням в CSV.
    
    Args:
        data (list): Данные таблицы
        directory (str): Директория для сохранения
    
    Returns:
        str: Путь к созданному файлу
    """
    return export_table_to_csv(
        data=data,
        filename="daily_events",
        directory=directory
    )


def export_gold_balance_table(data, directory='output'):
    """
    Экспортирует таблицу баланса золота в CSV.
    
    Args:
        data (list): Данные таблицы
        directory (str): Директория для сохранения
    
    Returns:
        str: Путь к созданному файлу
    """
    return export_table_to_csv(
        data=data,
        filename="gold_balance",
        directory=directory
    )


def export_location_upgrades_table(data, directory='output'):
    """
    Экспортирует таблицу истории улучшений локаций в CSV.
    
    Args:
        data (list): Данные таблицы
        directory (str): Директория для сохранения
    
    Returns:
        str: Путь к созданному файлу
    """
    return export_table_to_csv(
        data=data,
        filename="location_upgrades_history",
        directory=directory
    )


def export_tapping_stats_table(data, directory='output'):
    """
    Экспортирует таблицу статистики тапинга в CSV.
    
    Args:
        data (list): Данные таблицы
        directory (str): Директория для сохранения
    
    Returns:
        str: Путь к созданному файлу
    """
    return export_table_to_csv(
        data=data,
        filename="tapping_stats",
        directory=directory
    ) 