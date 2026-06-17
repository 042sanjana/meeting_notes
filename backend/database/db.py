import sqlite3

conn = sqlite3.connect(
    "meeting.db",
    check_same_thread=False
)

cursor = conn.cursor()

try:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meetings(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT,
            transcript TEXT,
            summary TEXT,
            tasks TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
except sqlite3.Error as e:
    print(f"Database error: {e}")
    conn.rollback()
finally:
    cursor.close()