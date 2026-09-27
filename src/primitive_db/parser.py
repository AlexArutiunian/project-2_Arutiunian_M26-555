"""Парсеры команд базы"""


def parse_value(text):
    """Разбирает значение"""
    value = text.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    try:
        return int(value)
    except ValueError as error:
        raise ValueError(
            f"Некорректное значение: {value}. Попробуйте снова."
        ) from error


def split_values(text):
    """Разделяет значения"""
    values = []
    current = []
    quote = None

    for char in text:
        if char in "\"'":
            if quote is None:
                quote = char
            elif quote == char:
                quote = None
            current.append(char)
        elif char == "," and quote is None:
            values.append("".join(current).strip())
            current = []
        else:
            current.append(char)

    if quote is not None:
        raise ValueError(f"Некорректное значение: {text}. Попробуйте снова.")

    values.append("".join(current).strip())
    return values


def parse_values(text):
    """Разбирает список значений"""
    value_text = text.strip()
    if not value_text.startswith("(") or not value_text.endswith(")"):
        raise ValueError(f"Некорректное значение: {text}. Попробуйте снова.")

    inner = value_text[1:-1].strip()
    if not inner:
        return []
    return [parse_value(item) for item in split_values(inner)]


def parse_clause(text):
    """Разбирает условие запроса"""
    if "=" not in text:
        raise ValueError(f"Некорректное значение: {text}. Попробуйте снова.")

    column, value = text.split("=", 1)
    column = column.strip()
    value = value.strip()
    if not column or not value:
        raise ValueError(f"Некорректное значение: {text}. Попробуйте снова.")
    return {column: parse_value(value)}
