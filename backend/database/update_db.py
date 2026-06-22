import sqlite3

conn = sqlite3.connect("meeting.db")

cursor = conn.cursor()

cursor.execute("""
ALTER TABLE meetings
ADD COLUMN user_id INTEGER
""")

conn.commit()
conn.close()

print("user_id added successfully")