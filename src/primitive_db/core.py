"""Логика базы данных"""

import json

from .constants import ID_COLUMN, VALID_TYPES
from .decorators import confirm_action, create_cacher, handle_db_errors, log_time
from .utils import load_table_data

_cache_result = create_cacher()


def _normalize_columns(columns):
    """Нормализует список столбцов"""
    result = []
    for column in columns:
        if isinstance(column, str):
            if ":" not in column:
                raise ValueError(
                    f"Некорректное значение: {column}. Попробуйте снова."
                )
            name, column_type = column.split(":", 1)
            name = name.strip()
            column_type = column_type.strip()
        else:
            name, column_type = column

        if not name or not column_type:
            raise ValueError(f"Некорректное значение: {column}. Попробуйте снова.")
        result.append((name, column_type))
    return result


def _value_matches_type(value, expected_type):
    """Проверяет тип значения"""
    if expected_type == "int":
        return type(value) is int
    if expected_type == "str":
        return type(value) is str
    if expected_type == "bool":
        return type(value) is bool
    return False


@handle_db_errors
def create_table(metadata, table_name, columns):
    """Создает таблицу"""
    if table_name in metadata:
        raise ValueError(f'Ошибка: Таблица "{table_name}" уже существует.')

    schema = {ID_COLUMN: "int"}
    for name, column_type in _normalize_columns(columns):
        if column_type not in VALID_TYPES:
            raise ValueError(
                f"Некорректное значение: {column_type}. Попробуйте снова."
            )
        if name == ID_COLUMN:
            if column_type != "int":
                raise ValueError(
                    f"Некорректное значение: {column_type}. Попробуйте снова."
                )
            continue
        if name in schema:
            raise ValueError(f"Некорректное значение: {name}. Попробуйте снова.")
        schema[name] = column_type

    metadata[table_name] = schema
    return metadata


@handle_db_errors
@confirm_action("удаление таблицы")
def drop_table(metadata, table_name):
    """Удаляет таблицу"""
    if table_name not in metadata:
        raise KeyError(f'Таблица "{table_name}" не существует.')
    del metadata[table_name]
    return metadata


def list_tables(metadata):
    """Возвращает список таблиц"""
    return list(metadata)


def validate_clause(schema, clause):
    """Проверяет условие запроса"""
    column, value = next(iter(clause.items()))
    if column not in schema:
        raise KeyError(f'Столбец "{column}" не существует.')
    if not _value_matches_type(value, schema[column]):
        raise ValueError(f"Некорректное значение: {value}. Попробуйте снова.")
    return True


@handle_db_errors
@log_time
def insert(metadata, table_name, values):
    """Добавляет запись"""
    if table_name not in metadata:
        raise KeyError(f'Таблица "{table_name}" не существует.')

    schema = metadata[table_name]
    user_columns = [name for name in schema if name != ID_COLUMN]
    if len(values) != len(user_columns):
        raise ValueError(
            f"Некорректное значение: {len(values)} значений. Попробуйте снова."
        )

    row = {}
    data = load_table_data(table_name)
    row[ID_COLUMN] = max((item[ID_COLUMN] for item in data), default=0) + 1

    for column, value in zip(user_columns, values, strict=True):
        if not _value_matches_type(value, schema[column]):
            raise ValueError(f"Некорректное значение: {value}. Попробуйте снова.")
        row[column] = value

    data.append(row)
    return data


@handle_db_errors
@log_time
def select(table_data, where_clause=None):
    """Выбирает записи"""
    key = json.dumps(
        {"data": table_data, "where": where_clause},
        ensure_ascii=False,
        sort_keys=True,
    )

    def get_result():
        if where_clause is None:
            return [row.copy() for row in table_data]
        column, value = next(iter(where_clause.items()))
        return [row.copy() for row in table_data if row.get(column) == value]

    result = _cache_result(key, get_result)
    return [row.copy() for row in result]


@handle_db_errors
def update(table_data, set_clause, where_clause):
    """Обновляет записи"""
    where_column, where_value = next(iter(where_clause.items()))
    for row in table_data:
        if row.get(where_column) == where_value:
            row.update(set_clause)
    return table_data


@handle_db_errors
@confirm_action("удаление записей")
def delete(table_data, where_clause):
    """Удаляет записи"""
    column, value = next(iter(where_clause.items()))
    return [row for row in table_data if row.get(column) != value]
