import time
import uuid
import mysql.connector
from database import get_db_connection

def run_spam_test(number_of_transactions):
    """
    Generează un volum mare de tranzacții.
    Utilizează managementul implicit de tranzacții (autocommit=False) pentru a elimina
    complet eroarea 'Transaction already in progress'.
    """
    print(f"\n--- Inițiere Spam Test Nativ Optimizat: {number_of_transactions} Solicitări ---")
    
    connection = get_db_connection()
    if not connection:
        print("Eroare: Nu s-a putut conecta la baza de date.")
        return

    try:
        # Dezactivăm autocommit-ul. MySQL va începe automat o tranzacție la prima comandă executată.
        connection.autocommit = False
        cursor = connection.cursor(dictionary=True)
        
        # Obținerea soldurilor inițiale
        cursor.execute("SELECT balance FROM accounts WHERE id IN (1, 2)")
        accounts_before = cursor.fetchall()
        print(f"Solduri înainte de test: {accounts_before}")

        print("Se generează lotul de UUID-uri...")
        amount = 0.01
        success_count = 0
        idempotency_hits = 0
        
        generated_uuids = [str(uuid.uuid4()) for _ in range(number_of_transactions)]
        
        # Introducere duplicate controlate la fiecare 1000 de iterații pentru testarea idempotenței
        for i in range(0, len(generated_uuids), 1000):
            if i + 1 < len(generated_uuids):
                generated_uuids[i + 1] = generated_uuids[i]

        print("Se trimit tranzacțiile către ledger...")
        start_time = time.time()

        for current_uuid in generated_uuids:
            try:
                # NOTĂ: Nu mai apelăm connection.start_transaction(). 
                # Prima comandă de mai jos deschide implicit tranzacția la nivel de server.
                
                # 1. Actualizare conturi
                cursor.execute("UPDATE accounts SET balance = balance - %s WHERE id = 1", (amount,))
                cursor.execute("UPDATE accounts SET balance = balance + %s WHERE id = 2", (amount,))
                
                # 2. Încercare înregistrare în ledger (Constrângerea UNIQUE va intercepta duplicatele)
                cursor.execute(
                    "INSERT INTO transactions (transaction_id, from_account, to_account, amount) VALUES (%s, 1, 2, %s)",
                    (current_uuid, amount)
                )
                
                # Dacă toate comenzile au reușit, salvăm definitiv modificările
                connection.commit()
                success_count += 1

            except mysql.connector.Error as err:
                # Anulăm imediat modificările de sold din această iterație defectuoasă
                connection.rollback()
                
                # Codul 1062 reprezintă "Duplicate entry" (Mecanismul de idempotență funcționează)
                if err.errno == 1062:
                    idempotency_hits += 1
                else:
                    print(f"Eroare întâmpinată la UUID {current_uuid}: {err}")

        end_time = time.time()
        execution_time = end_time - start_time

        # Obținerea soldurilor finale
        cursor.execute("SELECT balance FROM accounts WHERE id IN (1, 2)")
        accounts_after = cursor.fetchall()

        print("\n--- REZULTATE FINALE PERFORMANȚĂ ---")
        print(f"⏱️ Timp total de execuție: {execution_time:.2f} secunde")
        print(f"⚡ Tranzacții unice procesate cu succes: {success_count}")
        print(f"🛡️ Retrimiteri blocate prin Idempotență nativă: {idempotency_hits}")
        print(f"📊 Viteza medie: {number_of_transactions / execution_time:.2f} tranzacții/secundă")
        print(f"💰 Solduri după test: {accounts_after}")

    except mysql.connector.Error as err:
        print(f"Eroare critică în scriptul de test: {err}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    # Rulăm testul cu un volum controlat de 5000 pentru validare finală
    run_spam_test(100000)