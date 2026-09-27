# Примитивная база данных

Консольный учебный проект на Python. База данных хранит структуру таблиц в
`db_meta.json`, а записи каждой таблицы в отдельном JSON-файле внутри `data/`.

## Возможности

- создание и удаление таблиц;
- просмотр списка таблиц;
- типы `int`, `str`, `bool`;
- автоматический столбец `ID:int`;
- CRUD-операции;
- фильтрация через `where`;
- вывод результатов через PrettyTable;
- подтверждение опасных операций;
- замер времени `insert` и `select`;
- кэширование одинаковых `select`-запросов.

## Установка

```bash
uv sync
```

Или:

```bash
make install
```

## Запуск

```bash
uv run database
```

Или:

```bash
make run
```

## Управление таблицами

```text
create_table users name:str age:int is_active:bool
list_tables
drop_table users
```

При создании таблицы столбец `ID:int` добавляется автоматически.

## CRUD-операции

Добавление записи:

```text
insert into users values ("Sergei", 28, true)
```

Просмотр всех записей:

```text
select from users
```

Просмотр по условию:

```text
select from users where age = 28
```

Обновление:

```text
update users set age = 29 where name = "Sergei"
```

Удаление:

```text
delete from users where ID = 1
```

Информация о таблице:

```text
info users
```

Для строковых значений используются кавычки.

## Проверка сценария

После запуска `uv run database` используется такой сценарий:

```text
create_table users name:str age:int
insert into users values ("Alex", 25)
select from users
update users set age = 26 where name = "Alex"
delete from users where ID = 1
y
drop_table users
y
exit
```

Сценарий проверяет создание таблицы, добавление, чтение, обновление и удаление
записи, подтверждение удаления и удаление самой таблицы.

## Проверка кода

```bash
make lint
```

## Сборка

```bash
make build
```

## Демонстрация

[![Asciinema](https://img.shields.io/badge/Asciinema-Открыть_запись-1f2020?logo=asciinema&logoColor=white)](https://asciinema.org/a/Oc82viJk8Gzj0d9D)

[Открыть запись в Asciinema](https://asciinema.org/a/Oc82viJk8Gzj0d9D)
