import mysql.connector
import uuid
from database import get_db_connection

def create_account(owner_name, initial_balance):
    """
    Creează un cont bancar nou în baza de date.
    """
    if initial_balance < 0:
        print("Eroare: Soldul inițial nu poate fi negativ.")
        return False

    connection = get_db_connection()
    if not connection:
        print("Eroare: Nu s-a putut stabili conexiunea cu baza de date.")
        return False

    try:
        cursor = connection.cursor()
        query = "INSERT INTO accounts (name, balance) VALUES (%s, %s)"
        values = (owner_name, initial_balance)
        
        cursor.execute(query, values)
        connection.commit()
        
        print(f"Succes: Contul pentru '{owner_name}' a fost creat cu ID-ul {cursor.lastrowid}.")
        return True
    except mysql.connector.Error as error:
        print(f"Eroare la inserarea în baza de date: {error}")
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def get_account_balance(account_id):
    """
    Returnează soldul curent al unui cont pe baza ID-ului.
    """
    connection = get_db_connection()
    if not connection:
        return None

    try:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT name, balance FROM accounts WHERE id = %s"
        cursor.execute(query, (account_id,))
        account = cursor.fetchone()
        
        if account:
            return account
        else:
            print(f"Eroare: Contul cu ID-ul {account_id} nu există.")
            return None
    except mysql.connector.Error as error:
        print(f"Eroare la interogarea bazei de date: {error}")
        return None
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def deposit(account_id, amount):
    """
    Depune o sumă de bani într-un cont și înregistrează tranzacția.
    """
    if amount <= 0:
        print("Eroare: Suma pentru depunere trebuie să fie pozitivă.")
        return False

    connection = get_db_connection()
    if not connection:
        return False

    try:
        cursor = connection.cursor()
        
        # 1. Actualizăm soldul contului
        update_query = "UPDATE accounts SET balance = balance + %s WHERE id = %s"
        cursor.execute(update_query, (amount, account_id))
        
        # 2. Generăm un UUID unic pentru această tranzacție
        txn_uuid = str(uuid.uuid4())
        
        # 3. Înregistrăm tranzacția în ledger
        insert_query = """
            INSERT INTO transactions (transaction_id, from_account, to_account, amount) 
            VALUES (%s, NULL, %s, %s)
        """
        cursor.execute(insert_query, (txn_uuid, account_id, amount))
        
        connection.commit()
        print(f"Succes: S-au depus {amount} RON în contul {account_id}. (Txn UUID: {txn_uuid})")
        return True
    except mysql.connector.Error as error:
        connection.rollback()
        print(f"Eroare la depunere: {error}")
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def withdraw(account_id, amount):
    """
    Retrage o sumă de bani dintr-un cont, dacă există fonduri suficiente.
    """
    if amount <= 0:
        print("Eroare: Suma pentru retragere trebuie să fie pozitivă.")
        return False

    connection = get_db_connection()
    if not connection:
        return False

    try:
        cursor = connection.cursor(dictionary=True)
        
        # 1. Verificăm dacă există fonduri suficiente
        cursor.execute("SELECT balance FROM accounts WHERE id = %s", (account_id,))
        account = cursor.fetchone()
        
        if not account:
            print("Eroare: Contul specificat nu există.")
            return False
            
        if account['balance'] < amount:
            print("Eroare: Fonduri insuficiente.")
            return False

        # 2. Actualizăm soldul contului
        update_query = "UPDATE accounts SET balance = balance - %s WHERE id = %s"
        cursor.execute(update_query, (amount, account_id))
        
        # 3. Generăm un UUID unic
        txn_uuid = str(uuid.uuid4())
        
        # 4. Înregistrăm tranzacția
        insert_query = """
            INSERT INTO transactions (transaction_id, from_account, to_account, amount) 
            VALUES (%s, %s, NULL, %s)
        """
        cursor.execute(insert_query, (txn_uuid, account_id, amount))
        
        connection.commit()
        print(f"Succes: S-au retras {amount} RON din contul {account_id}. (Txn UUID: {txn_uuid})")
        return True
    except mysql.connector.Error as error:
        connection.rollback()
        print(f"Eroare la retragere: {error}")
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def transfer_money(transaction_uuid, from_account_id, to_account_id, amount):
    """
    Execută un transfer de bani între două conturi în mod idempotent.
    """
    if amount <= 0:
        print("Eroare: Suma transferată trebuie să fie pozitivă.")
        return False
        
    if from_account_id == to_account_id:
        print("Eroare: Contul sursă nu poate fi același cu contul destinație.")
        return False

    connection = get_db_connection()
    if not connection:
        return False

    try:
        # Inițiem tranzacția direct pe conexiune înainte de orice interogare
        connection.start_transaction()
        cursor = connection.cursor(dictionary=True)

        # --- LOGICA DE IDEMPOTENȚĂ ---
        check_query = "SELECT id FROM transactions WHERE transaction_id = %s FOR UPDATE"
        cursor.execute(check_query, (transaction_uuid,))
        existing_txn = cursor.fetchone()

        if existing_txn:
            print(f"⚠️ [IDEMPOTENȚĂ] Tranzacția cu UUID {transaction_uuid} a fost deja procesată. Cerere ignorată.")
            connection.rollback() # Închidem tranzacția curat, fără modificări
            return True

        # 1. Verificăm soldul contului sursă
        cursor.execute("SELECT balance FROM accounts WHERE id = %s FOR UPDATE", (from_account_id,))
        source_account = cursor.fetchone()

        if not source_account:
            print("Eroare: Contul sursă nu există.")
            connection.rollback()
            return False

        if source_account['balance'] < amount:
            print("Eroare: Fonduri insuficiente pentru efectuarea transferului.")
            connection.rollback()
            return False

        # 2. Debităm contul sursă
        cursor.execute("UPDATE accounts SET balance = balance - %s WHERE id = %s", (amount, from_account_id))

        # 3. Credităm contul destinație
        cursor.execute("UPDATE accounts SET balance = balance + %s WHERE id = %s", (amount, to_account_id))

        # 4. Înregistrăm tranzacția în istoric
        insert_query = """
            INSERT INTO transactions (transaction_id, from_account, to_account, amount) 
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(insert_query, (transaction_uuid, from_account_id, to_account_id, amount))

        connection.commit()
        print(f"✅ Succes: Transfer de {amount} RON realizat cu succes de la {from_account_id} la {to_account_id}.")
        return True

    except mysql.connector.Error as error:
        try:
            connection.rollback()
        except:
            pass
        print(f"Eroare critică în timpul transferului: {error}")
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    print("--- Testare Sistem Complet ---")
    
    # 1. Depunere și retragere standard
    deposit(1, 1000.00)
    withdraw(1, 200.00)
    
    # 2. Test Idempotență
    test_uuid = str(uuid.uuid4())
    
    print("\n[Trimitere 1] Se procesează transferul...")
    transfer_money(test_uuid, from_account_id=1, to_account_id=2, amount=150.00)
    
    print("\n[Trimitere 2] Se retrimite aceeași cerere...")
    transfer_money(test_uuid, from_account_id=1, to_account_id=2, amount=150.00)