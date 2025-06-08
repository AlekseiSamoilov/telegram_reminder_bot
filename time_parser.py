import re
from datetime import datetime, timedelta
from time import strftime
from typing import Optional

from six import add_move


def parse_time(time_string: str) -> Optional[datetime]:
    """Парсит строку времени и возвращает объект datetime

    Поддерживаемые форматы:
    - "через 30 минут", "через 2 часа"
    - "завтра в 15:00", "сегодня в 18:30"
    - "2024-06-10 14:30"

    Args:
        time_string: Строка с описанием времени

    Returns:
        datetime или None если не удалось распарсить
    """
    # Приводим к нижнему регистру и убираем лишние пробелы
    time_string = time_string.lower().strip()

    # Получаем текущее время для расчетов
    now = datetime.now()

    # 1. Паттерн "через X минут/часов"
    # re.search ищет паттерн в строке
    # \d+ означает "одна или более цифр"
    # (минут|минуты|час|часа|часов) - альтернативы через |
    relative_pattern = r'через\s+(\d+)\s+(минут|минуты|час|часа|часов)'
    match = re.search(relative_pattern, time_string)

    if match:
        amount = int(match.group(1)) # Первая группа в скобках - количество
        unit = match.group(2) # Вторая группа - единица времени

        if unit in ['минут', 'минуты']:
            delta = timedelta(minutes=amount)
        elif unit in ['час', 'часа', 'часов']:
            delta = timedelta(hours=amount)

        return now + delta

    # 2. Паттерн "завтра/сегодня в HH:MM"
    # \s* означает "ноль или более пробелов"
    # ([01]?\d|2[0-3]) - часы от 00 до 23
    # ([0-5]?\d) - минуты от 00 до 59

    day_time_pattern = r'(завтра|сегодня)\s+в\s+([01]?\d|2[0-3]):([0-5]?\d)'
    match = re.search(day_time_pattern, time_string)

    if match:
        day = match.group(1)
        hours = int(match.group(2))
        minutes = int(match.group(3))

        target_time = now.replace(hour=hours, minute=minutes, second=0, microsecond=0)

        if day == 'завтра':
            target_time += timedelta(days=1)
        elif day == 'сегодня' and target_time <= now:
            target_time += timedelta(days=1)

        return target_time

    # 3. Паттерн "YYYY-MM-DD HH:MM" (точная дата и время)
    # Пробуем распарсить как полную дату

    try:
        return datetime.strptime(time_string, '%Y-%m-%d %H:%M')
    except ValueError:
        pass # Если не удалось - продолжаем

    # 4. Паттерн "DD.MM.YYYY HH:MM" (российский формат даты)
    try:
        return datetime.strptime(time_string, '%d.%m.%Y %H:%M')
    except ValueError:
        pass

    # 5. Паттерн только "HH:MM" (время сегодня)
    time_only_pattern = r'^([01]?\d|2[0-3]):([0-5]?\d)$'
    match = re.match(time_only_pattern, time_string)

    if match:
        hours = int(match.group(1))
        minutes = int(match.group(2))

        target_time = now.replace(hour=hours, minute=minutes, second=0, microsecond=0)

        if target_time <= now:
            target_time +=timedelta(days=1)

        return target_time

    return None
# Форматируем datetime в читаемую строку
def format_time(dt: datetime) -> str:

    now = datetime.now()

    if dt.date() == now.date():
        return f"сегодня в {dt.strftime('%H:%M')}"

    elif dt.date() == (now + timedelta(days=1)).date():
        return f"завтра в {dt.strftime('%H:%M')}"

    else:
        return strftime('%d.%m.%Y в %H:%M')

def test_parser():
    """Тестовая функция для проверки работы парсера"""
    test_cases = [
        "через 30 минут",
        "через 2 часа",
        "завтра в 15:00",
        "сегодня в 18:30",
        "2024-06-10 14:30",
        "15:45"
    ]

    print("Тестирование парсера времени:")
    for case in test_cases:
        result = parse_time(case)
        if result:
            formatted = format_time(result)
            print(f"'{case}' -> {formatted}")
        else:
            print(f"'{case}' -> НЕ РАСПОЗНАНО")


if __name__ == '__main__':
    test_parser()