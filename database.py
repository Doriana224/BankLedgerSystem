import mysql.connector
from mysql.connector import Error

def get_db_connection():
    """Creează și returnează o conexiune proaspătă cu baza de date ledger_db."""
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',         # Schimbă cu utilizatorul tău dacă e altul
            password='Matematica123!',     # ⚠️ Pune AICI parola ta de la MySQL Workbench!
            database='ledger_db'
        )
        return connection
    except Error as e:
        print(f"Eroare la conectarea cu MySQL: {e}")
        return None

# Testarea conexiunii la rularea directă a scriptului
if __name__ == "__main__":
    conn = get_db_connection()
    if conn and conn.is_connected():
        print("Database connection status: SUCCESS")
        conn.close()