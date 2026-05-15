import sqlite3
conn = sqlite3.connect('skillswap.db')
cursor = conn.cursor()
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='session_requests'")
row = cursor.fetchone()
if row:
    print(row[0])
else:
    print('Table not found')
conn.close()