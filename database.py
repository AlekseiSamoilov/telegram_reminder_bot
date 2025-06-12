import sqlite3
from datetime import datetime
from typing import List, Tuple, Optional

DATABASE_PATH = 'reminders.db'


def upgrade_database():
    """Обновляет структуру базы данных при необходимости"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Проверяем есть ли колонка is_sent
    cursor.execute("PRAGMA table_info(reminders)")
    columns = [column[1] for column in cursor.fetchall()]

    if 'is_sent' not in columns:
        print("🔧 Добавляем колонку is_sent в существующую базу...")
        cursor.execute('ALTER TABLE reminders ADD COLUMN is_sent BOOLEAN DEFAULT 0')
        conn.commit()
        print("✅ Колонка is_sent добавлена")

    conn.close()


def init_database():
    """Создает таблицу для напоминаний если её нет"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            remind_time TEXT NOT NULL,
            created_at TEXT NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            is_sent BOOLEAN DEFAULT 0
        )
    ''')

    conn.commit()
    conn.close()
    print("База данных инициализирована")

    # Обновляем существующую базу если нужно
    upgrade_database()


def add_reminder(user_id: int, text: str, remind_time: datetime) -> int:
    """Добавляет новое напоминание в базу данных"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO reminders (user_id, text, remind_time, created_at, is_active, is_sent)
        VALUES (?, ?, ?, ?, 1, 0)
    ''', (user_id, text, remind_time.isoformat(), datetime.now().isoformat()))

    reminder_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return reminder_id


def get_active_reminders(user_id: int) -> List[Tuple]:
    """Получает все активные напоминания пользователя"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, text, remind_time, created_at
        FROM reminders 
        WHERE user_id = ? AND is_active = 1 AND is_sent = 0
        ORDER BY remind_time
    ''', (user_id,))

    reminders = cursor.fetchall()
    conn.close()

    return reminders


def delete_reminder(reminder_id: int, user_id: int) -> bool:
    """Помечает напоминание как отправленное"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE reminders 
        SET is_sent = 1 
        WHERE id = ? AND user_id = ?
    ''', (reminder_id, user_id))

    success = cursor.rowcount > 0
    conn.commit()
    conn.close()

    return success


def get_pending_reminders() -> List[Tuple]:
    """Получает все напоминания, время которых наступило"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()

        current_time = datetime.now().isoformat()

        cursor.execute('''
            SELECT id, user_id, text, remind_time 
            FROM reminders 
            WHERE remind_time <= ? AND is_active = 1 AND is_sent = 0
            ORDER BY remind_time
        ''', (current_time,))

        return cursor.fetchall()