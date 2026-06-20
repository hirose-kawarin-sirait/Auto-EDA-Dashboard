import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

cursor.execute("SELECT sql FROM sqlite_master WHERE name='users'")
print(cursor.fetchone()[0])
print()

cursor.execute("SELECT * FROM users")

data = cursor.fetchall()

print("\nDAFTAR USER\n")

for row in data:
    print(f"ID       : {row[0]}")
    print(f"Username : {row[1]}")
    print(f"Email    : {row[2]}")
    print(f"Password : {row[3]}")
    print("-" * 30)

conn.close()