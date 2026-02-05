import pyodbc

conn = pyodbc.connect("DSN=LPG_LOCAL;UID=system;PWD=system123")
cur = conn.cursor()
cur.execute("SELECT 'Connected to Oracle XE via ODBC' FROM dual")
print(cur.fetchall())
conn.close()

