import pandas as pd
import mysql.connector
from database import get_db_connection

def generate_excel_audit_report():
    print("\n📊 Inițiere generare raport de audit Excel...")
    connection = get_db_connection()
    if not connection:
        print("Eroare: Nu s-a putut conecta la baza de date.")
        return

    try:
        cursor = connection.cursor(dictionary=True)
        
        # Am scos t.timestamp și lăsăm baza de date să ruleze fără el.
        # Tragem ID-urile, UUID-ul, numele și sumele.
        query = """
            SELECT 
                t.id AS 'ID Intern',
                t.transaction_id AS 'UUID Tranzactie',
                IFNULL(acc_from.name, 'Depunere Cash / Extern') AS 'Cont Sursa (Platitor)',
                IFNULL(acc_to.name, 'Retragere Cash / Extern') AS 'Cont Destinatie (Beneficiar)',
                t.amount AS 'Suma (RON)'
            FROM transactions t
            LEFT JOIN accounts acc_from ON t.from_account = acc_from.id
            LEFT JOIN accounts acc_to ON t.to_account = acc_to.id
            ORDER BY t.id DESC
        """
        
        print("Se extrag cele 100.000+ de rânduri din baza de date...")
        cursor.execute(query)
        rows = cursor.fetchall()
        
        # Convertim direct lista de dicționare în DataFrame (fără avertismente de conexiune!)
        df = pd.DataFrame(rows)
        
        output_file = "Raport_Audit_Ledger.xlsx"
        print(f"Se scriu datele în fișierul {output_file}...")
        
        # Salvăm în Excel
        df.to_excel(output_file, index=False, sheet_name="Registru Tranzactii")
        
        print(f"✅ Succes total! Fișierul a fost generat: {output_file}")
        
    except mysql.connector.Error as err:
        print(f"Eroare SQL la generarea raportului: {err}")
    except Exception as e:
        print(f"Eroare neașteptată: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    generate_excel_audit_report()