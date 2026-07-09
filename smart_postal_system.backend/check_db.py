import sqlite3

def check_schema():
    conn = sqlite3.connect("smart_postal.db")
    cursor = conn.cursor()
    
    # Get list of tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables in database:", tables)
    
    for table in tables:
        table_name = table[0]
        print(f"\nSchema for table {table_name}:")
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        for col in columns:
            print(col)
            
    conn.close()

if __name__ == "__main__":
    check_schema()
