import mysql.connector
from database import get_db_connection

def get_account_info(account_id):
    connection = get_db_connection()
    if not connection: 
        return " [EROARE] Conexiunea la serverul de baze de date a eșuat."
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM accounts WHERE id = %s", (account_id,))
        account = cursor.fetchone()
        if account:
            return f" [INFO] Cont ID: {account['id']} | Titular: {account['name']} | Sold Curent: {account['balance']} RON"
        return f" [AVERTISMENT] Identificatorul de cont {account_id} nu figurează în baza de date."
    finally:
        connection.close()

def get_last_transactions(limit=5):
    connection = get_db_connection()
    if not connection: 
        return " [EROARE] Conexiunea la serverul de baze de date a eșuat."
    try:
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT t.id, t.transaction_id, acc_from.name AS from_name, acc_to.name AS to_name, t.amount
            FROM transactions t
            LEFT JOIN accounts acc_from ON t.from_account = acc_from.id
            LEFT JOIN accounts acc_to ON t.to_account = acc_to.id
            ORDER BY t.id DESC LIMIT %s
        """
        cursor.execute(query, (limit,))
        txns = cursor.fetchall()
        if not txns: 
            return " [INFO] Registrul tranzacțional nu conține înregistrări active."
        
        result = f"\n--- REGISTRU AUDIT: ULTIMELE {len(txns)} OPERAȚIUNI PROCESATE ---\n"
        for t in txns:
            from_p = t['from_name'] if t['from_name'] else "Depunere Numerar"
            to_p = t['to_name'] if t['to_name'] else "Retragere Numerar"
            result += f" ▪️ [ID Intern: {t['id']}] {from_p} -> {to_p} | Sumă de transfer: {t['amount']} RON\n"
        return result
    finally:
        connection.close()

def start_bot():
    print("\n========================================================")
    print("      CORE BANKING OPERATIONS SUPPORT TERMINAL v1.0     ")
    print("========================================================")
    print("Sistem de interogare și asistență pentru operatorii bancari.")
    print("Sesiune autorizată. Introduceți comenzile administrative.\n")
    print("Comenzi disponibile: 'cont [id]', 'auditeaza', 'ajutor', 'exit'\n")

    while True:
        comanda = input("OPERATOR-CMD> ").strip().lower()

        if comanda == 'exit':
            print("Sesiune închisă securizat. Terminalul s-a deconectat.")
            break
        elif comanda == 'ajutor':
            print("\n📌 GHID DE UTILIZARE COMNDI MANAGEMENT:")
            print("  -> cont [id]    : Afișează starea soldului și datele de identificare client")
            print("  -> auditeaza    : Extrage ultimele 5 înregistrări din istoricul tranzacțiilor")
            print("  -> exit         : Terminarea sesiunii de lucru curente\n")
        elif comanda.startswith('cont '):
            try:
                parts = comanda.split()
                account_id = int(parts[1])
                print(get_account_info(account_id))
            except (ValueError, IndexError):
                print(" [EROARE FORMAT] Sintaxă incorectă. Utilizați: cont [număr] (Exemplu: cont 1)")
        elif comanda == 'auditeaza':
            print(get_last_transactions())
        else:
            print(" [EROARE SINTAXĂ] Comandă nerecunoscută. Tastați 'ajutor' pentru nomenclatorul de comenzi.")
        print("-" * 56)

if __name__ == "__main__":
    start_bot()