"""Обработка команд"""

import shlex

import prompt
from prettytable import PrettyTable

from .constants import META_FILE
from .core import (
    create_table,
    delete,
    drop_table,
    insert,
    list_tables,
    select,
    update,
    validate_clause,
)
from .parser import parse_clause, parse_values
from .utils import (
    load_metadata,
    load_table_data,
    remove_table_data,
    save_metadata,
    save_table_data,
)


def print_help():
    """Показывает справку"""
    print("\n***База данных***")
    print("Функции:")
    print("create_table <таблица> <столбец:тип> .. - создать таблицу")
    print("list_tables - показать список всех таблиц")
    print("drop_table <таблица> - удалить таблицу")
    print("\n***Операции с данными***")
    print("insert into <таблица> values (...) - создать запись")
    print("select from <таблица> [where <столбец> = <значение>] - прочитать")
    print("update <таблица> set <столбец> = <значение> where ... - обновить")
    print("delete from <таблица> where <столбец> = <значение> - удалить")
    print("info <таблица> - информация о таблице")
    print("help - справочная информация")
    print("exit - выход из программы\n")


def _check_arg_count(args, expected):
    """Проверяет число аргументов"""
    if len(args) != expected:
        value = " ".join(args[1:]) if len(args) > 1 else ""
        raise ValueError(f"Некорректное значение: {value}. Попробуйте снова.")


def _handle_create(metadata, args):
    """Обрабатывает создание таблицы"""
    if len(args) < 3:
        value = " ".join(args[1:]) if len(args) > 1 else ""
        raise ValueError(f"Некорректное значение: {value}. Попробуйте снова.")

    table_name = args[1]
    columns = args[2:]
    new_metadata = create_table(metadata, table_name, columns)
    if new_metadata is None:
        return

    save_metadata(META_FILE, new_metadata)
    schema = new_metadata[table_name]
    column_text = ", ".join(f"{name}:{kind}" for name, kind in schema.items())
    print(
        f'Таблица "{table_name}" успешно создана со столбцами: {column_text}'
    )


def _handle_drop(metadata, args):
    """Обрабатывает удаление таблицы"""
    _check_arg_count(args, 2)
    table_name = args[1]
    new_metadata = drop_table(metadata, table_name)
    if new_metadata is None:
        return

    save_metadata(META_FILE, new_metadata)
    remove_table_data(table_name)
    print(f'Таблица "{table_name}" успешно удалена.')


def _handle_insert(metadata, user_input):
    """Обрабатывает добавление записи"""
    args = shlex.split(user_input)
    if len(args) < 5 or args[0] != "insert" or args[1] != "into":
        raise ValueError(
            f"Некорректное значение: {user_input}. Попробуйте снова."
        )

    table_name = args[2]
    if args[3] != "values":
        raise ValueError(
            f"Некорректное значение: {args[3]}. Попробуйте снова."
        )

    values_start = user_input.lower().find("values") + len("values")
    values = parse_values(user_input[values_start:].strip())
    table_data = insert(metadata, table_name, values)
    if table_data is None:
        return

    save_table_data(table_name, table_data)
    new_id = table_data[-1]["ID"]
    print(f'Запись с ID={new_id} успешно добавлена в таблицу "{table_name}".')


def _print_rows(schema, rows):
    """Печатает таблицу"""
    table = PrettyTable()
    table.field_names = list(schema)
    for row in rows:
        table.add_row([row.get(column) for column in schema])
    print(table)


def _handle_select(metadata, user_input):
    """Обрабатывает выборку записей"""
    args = shlex.split(user_input)
    if len(args) < 3 or args[0] != "select" or args[1] != "from":
        raise ValueError(
            f"Некорректное значение: {user_input}. Попробуйте снова."
        )

    table_name = args[2]
    if table_name not in metadata:
        raise KeyError(f'Таблица "{table_name}" не существует.')

    where_clause = None
    if len(args) > 3:
        if args[3] != "where":
            raise ValueError(
                f"Некорректное значение: {args[3]}. Попробуйте снова."
            )
        where_text = user_input.split("where", 1)[1].strip()
        where_clause = parse_clause(where_text)
        validate_clause(metadata[table_name], where_clause)

    table_data = load_table_data(table_name)
    rows = select(table_data, where_clause)
    if rows is None:
        return
    _print_rows(metadata[table_name], rows)


def _handle_update(metadata, user_input):
    """Обрабатывает обновление записей"""
    args = shlex.split(user_input)
    if len(args) < 8 or args[0] != "update":
        raise ValueError(
            f"Некорректное значение: {user_input}. Попробуйте снова."
        )

    table_name = args[1]
    if table_name not in metadata:
        raise KeyError(f'Таблица "{table_name}" не существует.')

    lower_input = user_input.lower()
    set_pos = lower_input.find(" set ")
    where_pos = lower_input.find(" where ")
    if set_pos == -1 or where_pos == -1 or where_pos <= set_pos:
        raise ValueError(
            f"Некорректное значение: {user_input}. Попробуйте снова."
        )

    set_text = user_input[set_pos + len(" set ") : where_pos].strip()
    where_text = user_input[where_pos + len(" where ") :].strip()
    set_clause = parse_clause(set_text)
    where_clause = parse_clause(where_text)

    schema = metadata[table_name]
    validate_clause(schema, set_clause)
    validate_clause(schema, where_clause)

    table_data = load_table_data(table_name)
    changed_ids = [
        row["ID"]
        for row in table_data
        if all(row.get(key) == value for key, value in where_clause.items())
    ]
    new_data = update(table_data, set_clause, where_clause)
    if new_data is None:
        return

    save_table_data(table_name, new_data)
    for row_id in changed_ids:
        print(f'Запись с ID={row_id} в таблице "{table_name}" успешно обновлена.')


def _handle_delete(metadata, user_input):
    """Обрабатывает удаление записей"""
    args = shlex.split(user_input)
    if len(args) < 7 or args[0] != "delete" or args[1] != "from":
        raise ValueError(
            f"Некорректное значение: {user_input}. Попробуйте снова."
        )

    table_name = args[2]
    if table_name not in metadata:
        raise KeyError(f'Таблица "{table_name}" не существует.')
    if args[3] != "where":
        raise ValueError(
            f"Некорректное значение: {args[3]}. Попробуйте снова."
        )

    where_text = user_input.split("where", 1)[1].strip()
    where_clause = parse_clause(where_text)
    validate_clause(metadata[table_name], where_clause)

    table_data = load_table_data(table_name)
    deleted_ids = [
        row["ID"]
        for row in table_data
        if all(row.get(key) == value for key, value in where_clause.items())
    ]
    new_data = delete(table_data, where_clause)
    if new_data is None:
        return

    save_table_data(table_name, new_data)
    for row_id in deleted_ids:
        print(f'Запись с ID={row_id} успешно удалена из таблицы "{table_name}".')


def _handle_info(metadata, args):
    """Показывает данные таблицы"""
    _check_arg_count(args, 2)
    table_name = args[1]
    if table_name not in metadata:
        raise KeyError(f'Таблица "{table_name}" не существует.')

    schema = metadata[table_name]
    data = load_table_data(table_name)
    columns = ", ".join(f"{name}:{kind}" for name, kind in schema.items())
    print(f"Таблица: {table_name}")
    print(f"Столбцы: {columns}")
    print(f"Количество записей: {len(data)}")


def _process_command(metadata, user_input, args):
    """Выполняет команду"""
    command = args[0]

    if command == "create_table":
        _handle_create(metadata, args)
    elif command == "list_tables":
        _check_arg_count(args, 1)
        tables = list_tables(metadata)
        if tables:
            for table_name in tables:
                print(f"- {table_name}")
        else:
            print("Таблиц нет.")
    elif command == "drop_table":
        _handle_drop(metadata, args)
    elif command == "insert":
        _handle_insert(metadata, user_input)
    elif command == "select":
        _handle_select(metadata, user_input)
    elif command == "update":
        _handle_update(metadata, user_input)
    elif command == "delete":
        _handle_delete(metadata, user_input)
    elif command == "info":
        _handle_info(metadata, args)
    elif command == "help":
        print_help()
    else:
        print(f"Функции {command} нет. Попробуйте снова.")


def run():
    """Запускает цикл команд"""
    print_help()

    try:
        while True:
            metadata = load_metadata(META_FILE)
            user_input = prompt.string(">>>Введите команду: ").strip()
            if not user_input:
                continue

            try:
                args = shlex.split(user_input)
            except ValueError:
                print(f"Некорректное значение: {user_input}. Попробуйте снова.")
                continue

            if not args:
                continue
            if args[0] == "exit":
                break

            try:
                _process_command(metadata, user_input, args)
            except (KeyError, ValueError) as error:
                message = error.args[0] if isinstance(error, KeyError) else str(error)
                if isinstance(error, KeyError):
                    print(f"Ошибка: {message}")
                else:
                    print(message)
    except (KeyboardInterrupt, EOFError):
        print()
