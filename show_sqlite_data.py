import sqlite3

# Path to your SQLite database file
db_path = 'db.sqlite3'

# Connect to the database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all table names
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

# Print data from each table
for table_name in tables:
    table = table_name[0]
    print(f"\nTable: {table}")
    cursor.execute(f"SELECT * FROM {table}")
    rows = cursor.fetchall()
    
    # Get column names
    column_names = [description[0] for description in cursor.description]
    print(" | ".join(column_names))
    for row in rows:
        print(row)

# Close the connection
conn.close()
