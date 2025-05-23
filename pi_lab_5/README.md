---
### Учебная дисциплина: Программная инженерия
### Преподаватель: Дзюба Д.В.
---

### Лабораторная работа №5

> #### Задание
1. Для данных, хранящихся в реляционной базе PotgreSQL реализуйте шаблон
сквозное чтение и сквозная запись (Пользователь/Клиент …)
2. В качестве кеша – используйте Redis
3. Замерьте производительность запросов на чтение данных с и без кеша с
использованием утилиты [wrk](https://github.com/wg/wrk) изменяя количество
потоков из которых производятся запросы (1, 5, 10)
4. Актуализируйте модель архитектуры в Structurizr DSL
5. Ваши сервисы должны запускаться через docker-compose командой `docker-compose up` (создайте Docker файлы для каждого сервиса)

---

> #### Вариант №2 (Магазин)

Что было сделано:

1. Реализован шаблон сквозного чтения и записи для реляционной базы данных PostgreSQL.
Выбран user-service, хранящий данные о пользователях (клиентах).

   Использованы шаблоны:
- read-through (чтение сначала из Redis, при промахе — из PostgreSQL с записью в Redis),
- write-through (при записи данные одновременно сохраняются в PostgreSQL и кэшируются в Redis).

  Всё реализовано в модуле `crud_cached.py`.

2. Добавлена поддержка Redis как кеша.
Redis используется для ускорения операций чтения. Подключение реализовано в `redis_utils.py`, конфигурация — через `config.py`.

4. Измерена производительность чтения с помощью утилиты `wrk`.
Были проведены тесты с различным числом потоков (-t) и соединений (-c) на GET-эндпоинтах `/users_no_cache/{user_id}` и `/users_with_cache/{user_id}`.


   Были получены метрики: Requests/sec, Latency, Transfer/sec — что позволило оценить эффективность кеша.

5. Были проведены замеры с кешем Redis и без него (результаты работы отражены в `logs.txt`). Производительность с кешем оказалась выше (больше запросов в секунду, ниже средняя задержка).

#### Docker + Docker Compose
- Каждый сервис имеет свой Dockerfile.
- Все сервисы запускаются одной командой: `docker-compose up --build`.

#### OpenAPI cпецификация
- Спецификации ко всем сервисам содержатся в директории api-specs.

