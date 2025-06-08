import sqlite3  # Библиотека для работы с SQLite базой данных
from datetime import datetime  # Для работы с датой и временем
from typing import List, Tuple, Optional  # Типизация для лучшего понимания кода

DATABASE_PATH = 'reminders.db'  # Путь к файлу базы данных


def init_database():
    """Создает таблицу для напоминаний если её нет"""
    # Устанавливаем соединение с базой данных (создает файл если его нет)
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()  # Курсор для выполнения SQL команд

    # SQL запрос для создания таблицы (IF NOT EXISTS = создать только если не существует)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Уникальный ID, автоувеличение
            user_id INTEGER NOT NULL,              -- ID пользователя Telegram
            text TEXT NOT NULL,                    -- Текст напоминания
            remind_time TEXT NOT NULL,             -- Время когда напомнить (ISO формат)
            created_at TEXT NOT NULL,              -- Время создания напоминания
            is_active BOOLEAN DEFAULT 1            -- Активно ли напоминание (1=да, 0=нет)
        )
    ''')

    conn.commit()  # Сохраняем изменения в базе
    conn.close()  # Закрываем соединение (важно для освобождения ресурсов)
    print("База данных инициализирована")


def add_reminder(user_id: int, text: str, remind_time: datetime) -> int:
    """Добавляет новое напоминание в базу данных

    Args:
        user_id: ID пользователя в Telegram
        text: Текст напоминания
        remind_time: Когда напомнить (объект datetime)

    Returns:
        int: ID созданного напоминания
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # INSERT INTO = добавить новую запись
    # ? = плейсхолдеры для безопасной вставки данных (защита от SQL инъекций)
    cursor.execute('''
        INSERT INTO reminders (user_id, text, remind_time, created_at)
        VALUES (?, ?, ?, ?)
    ''', (user_id, text, remind_time.isoformat(), datetime.now().isoformat()))
    # .isoformat() превращает datetime в строку формата "2024-06-07T15:30:00"

    reminder_id = cursor.lastrowid  # Получаем ID только что созданной записи
    conn.commit()  # Сохраняем изменения
    conn.close()  # Закрываем соединение

    return reminder_id  # Возвращаем ID для использования в коде


def get_active_reminders(user_id: int) -> List[Tuple]:
    """Получает все активные напоминания пользователя

    Args:
        user_id: ID пользователя

    Returns:
        List[Tuple]: Список кортежей с данными напоминаний
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # SELECT = выбрать данные, WHERE = условие, ORDER BY = сортировка
    cursor.execute('''
        SELECT id, text, remind_time, created_at
        FROM reminders 
        WHERE user_id = ? AND is_active = 1  -- Только активные напоминания этого пользователя
        ORDER BY remind_time                 -- Сортируем по времени напоминания
    ''', (user_id,))  # Кортеж с одним элементом (запятая обязательна!)

    reminders = cursor.fetchall()  # Получаем ВСЕ результаты как список кортежей
    conn.close()

    return reminders


def delete_reminder(reminder_id: int, user_id: int) -> bool:
    """Удаляет напоминание (помечает как неактивное)

    Args:
        reminder_id: ID напоминания
        user_id: ID пользователя (для безопасности)

    Returns:
        bool: True если удаление успешно, False если напоминание не найдено
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # UPDATE = обновить данные, SET = установить новое значение
    # Мы не удаляем запись физически, а помечаем как неактивную
    cursor.execute('''
        UPDATE reminders 
        SET is_active = 0 
        WHERE id = ? AND user_id = ?  -- Проверяем и ID напоминания и пользователя
    ''', (reminder_id, user_id))

    success = cursor.rowcount > 0  # rowcount = количество измененных строк
    conn.commit()
    conn.close()

    return success  # True если что-то изменилось, False если не нашли запись


def get_pending_reminders() -> List[Tuple]:
    """Получает все напоминания, которые нужно отправить прямо сейчас

    Returns:
        List[Tuple]: Список напоминаний, время которых уже наступило
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    now = datetime.now().isoformat()  # Текущее время в ISO формате
    cursor.execute('''
        SELECT id, user_id, text, remind_time
        FROM reminders 
        WHERE is_active = 1 AND remind_time <= ?  -- Время напоминания <= текущего времени
    ''', (now,))

    reminders = cursor.fetchall()
    conn.close()

    return reminders