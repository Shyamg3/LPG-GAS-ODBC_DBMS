import pyodbc

def get_db_connection():
    connection = pyodbc.connect(
        "DSN=LPG_LOCAL;UID=system;PWD=system123"
    )
    return connection

