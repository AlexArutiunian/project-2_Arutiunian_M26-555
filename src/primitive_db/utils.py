"""Работа с файлами"""

import json
import os

from .constants import DATA_DIR, META_FILE


def load_metadata(filepath=META_FILE):
    """Загружает метаданные"""
    try:
        with open(filepath, encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


def save_metadata(filepath, data):
    """Сохраняет метаданные"""
    with open(filepath, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def load_table_data(table_name):
    """Загружает данные таблицы"""
    filepath = os.path.join(DATA_DIR, f"{table_name}.json")
    try:
        with open(filepath, encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return []


def save_table_data(table_name, data):
    """Сохраняет данные таблицы"""
    os.makedirs(DATA_DIR, exist_ok=True)
    filepath = os.path.join(DATA_DIR, f"{table_name}.json")
    with open(filepath, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def remove_table_data(table_name):
    """Удаляет файл таблицы"""
    filepath = os.path.join(DATA_DIR, f"{table_name}.json")
    try:
        os.remove(filepath)
    except FileNotFoundError:
        pass
