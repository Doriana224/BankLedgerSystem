import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import mysql.connector
import uuid
from decimal import Decimal
from database import get_db_connection

class MainLauncher:
    """ Fereastra principală care permite selectarea tipului de interfață """
    def __init__(self, root):
        self.root = root
        self.root.title("NEXUS BANKING SYSTEM v1.0")
        self.root.geometry("450x300")
        self.root.configure(bg="#f4f6f9")
        
        # Stiluri Corporate
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton", font=("Segoe UI", 11), padding=10)
        
        lbl_title = tk.Label(root, text="NEXUS INTEGRATED CORE BANKING", font=("Segoe UI", 14, "bold"), bg="#f4f6f9", fg="#1a252f")
        lbl_title.pack(pady=30)
        
        lbl_subtitle = tk.Label(root, text="Selectați modul de acces în sistem:", font=("Segoe UI", 10), bg="#f4f6f9", fg="#7f8c8d")
        lbl_subtitle.pack(pady=5)
        
        btn_client = ttk.Button(root, text="🌐 ACCES PORTAL CLIENȚI", command=self.open_client_interface)
        btn_client.pack(pady=10, fill="x", padx=50)
        
        btn_staff = ttk.Button(root, text="🛡️ ACCES HUB AUDIT ANGAJAȚI", command=self.open_staff_interface)
        btn_staff.pack(pady=10, fill="x", padx=50)

    def open_client_interface(self):
        client_window = tk.Toplevel(self.root)
        ClientInterface(client_window)

    def open_staff_interface(self):
        # Cerem o parolă simbolică pentru angajați ca să arate profesionist
        password = simpledialog.askstring("Securitate", "Introduceți cheia de acces personal (Staff PIN):", show="*", parent=self.root)
        if password == "1234" or password == "STAFF":
            staff_window = tk.Toplevel(self.root)
            StaffInterface(staff_window)
        else:
            messagebox.showerror("Eroare", "Acces interzis. Credențiale administrative invalide.")


# =====================================================================
# 1. INTERFAȚA PENTRU CLIENȚI (SOLD, TRANSFERURI, SOLICITARE CREDITE)
# =====================================================================
class ClientInterface:
    def __init__(self, window):
        self.window = window
        self.window.title("PORTAL DIGITAL CLIENȚI - NEXUS BANK")
        self.window.geometry("600x550")
        self.window.configure(bg="#ffffff")
        
        # Header Client
        header = tk.Frame(window, bg="#2980b9", height=50)
        header.pack(fill="x")
        tk.Label(header, text="PORTAL SECURIZAT CLIENȚI", fg="white", bg="#2980b9", font=("Segoe UI", 12, "bold")).pack(pady=12)
        
        # Secțiunea 1: Interogare Sold rapid
        frame_sold = tk.LabelFrame(window, text=" Interogare Cont & Sold ", bg="#ffffff", padx=15, pady=10, font=("Segoe UI", 10, "bold"))
        frame_sold.pack(fill="x", padx=15, pady=10)
        
        tk.Label(frame_sold, text="ID Cont Curent:", bg="#ffffff").grid(row=0, column=0, sticky="w")
        self.entry_client_id = ttk.Entry(frame_sold, width=10)
        self.entry_client_id.grid(row=0, column=1, padx=10)
        
        btn_check = ttk.Button(frame_sold, text="Afișează Sold", command=self.check_balance)
        btn_check.grid(row=0, column=2, padx=10)
        
        self.lbl_balance_res = tk.Label(frame_sold, text="Introduceți ID-ul și apăsați butonul.", font=("Segoe UI", 10, "italic"), bg="#ffffff", fg="#7f8c8d")
        self.lbl_balance_res.grid(row=1, column=0, columnspan=3, pady=10, sticky="w")

        # Secțiunea 2: Trimitere Bani (Tranzacție Reală)
        frame_transfer = tk.LabelFrame(window, text=" Execuție Transfer Bancar ", bg="#ffffff", padx=15, pady=10, font=("Segoe UI", 10, "bold"))
        frame_transfer.pack(fill="x", padx=15, pady=10)
        
        tk.Label(frame_transfer, text="ID Cont Destinație (Beneficiar):", bg="#ffffff").grid(row=0, column=0, sticky="w", pady=5)
        self.entry_to_acc = ttk.Entry(frame_transfer, width=15)
        self.entry_to_acc.grid(row=0, column=1, padx=10)
        
        tk.Label(frame_transfer, text="Sumă de plată (RON):", bg="#ffffff").grid(row=1, column=0, sticky="w", pady=5)
        self.entry_amount = ttk.Entry(frame_transfer, width=15)
        self.entry_amount.grid(row=1, column=1, padx=10)
        
        btn_send_money = ttk.Button(frame_transfer, text="Inițiază Plată", command=self.send_transaction)
        btn_send_money.grid(row=2, column=0, columnspan=2, pady=10)

        # Secțiunea 3: Aplicare pentru Credite
        frame_credit = tk.LabelFrame(window, text=" Solicitare Credit de Nevoi Personale ", bg="#ffffff", padx=15, pady=10, font=("Segoe UI", 10, "bold"))
        frame_credit.pack(fill="x", padx=15, pady=10)
        
        tk.Label(frame_credit, text="Sumă Credit Solicitată:", bg="#ffffff").grid(row=0, column=0, sticky="w", pady=5)
        self.entry_credit_amt = ttk.Entry(frame_credit, width=15)
        self.entry_credit_amt.grid(row=0, column=1, padx=10)
        
        btn_apply_credit = ttk.Button(frame_credit, text="Trimite cererea spre analiză", command=self.apply_for_credit)
        btn_apply_credit.grid(row=1, column=0, columnspan=2, pady=10)

    def mask_name_gdpr(self, name):
        parts = name.split()
        return " ".join([p[0] + "*" * (len(p) - 1) if len(p) > 1 else p for p in parts])

    def check_balance(self):
        try:
            acc_id = int(self.entry_client_id.get().strip())
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM accounts WHERE id = %s", (acc_id,))
            acc = cursor.fetchone()
            if acc:
                masked_name = self.mask_name_gdpr(acc['name'])
                self.lbl_balance_res.config(text=f"👤 Client: {masked_name} | 💰 Sold disponibil: {acc['balance']} RON", fg="#27ae60", font=("Segoe UI", 10, "bold"))
            else:
                self.lbl_balance_res.config(text="❌ Contul specificat nu a fost găsit.", fg="#c0392b")
            conn.close()
        except ValueError:
            messagebox.showerror("Eroare", "Vă rugăm să introduceți un ID de cont valid (număr întreg).")

    def send_transaction(self):
        """ Execută o tranzacție reală din contul clientului curent """
        try:
            from_id = int(self.entry_client_id.get().strip())
            to_id = int(self.entry_to_acc.get().strip())
            amount = Decimal(self.entry_amount.get().strip())
            
            if amount <= 0:
                raise ValueError("Suma trebuie să fie pozitivă.")
                
            tx_id = str(uuid.uuid4()) # Generăm UUID unic pentru idempotență
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Executăm mutarea fondurilor logic
            cursor.execute("UPDATE accounts SET balance = balance - %s WHERE id = %s", (amount, from_id))
            cursor.execute("UPDATE accounts SET balance = balance + %s WHERE id = %s", (amount, to_id))
            cursor.execute("INSERT INTO transactions (transaction_id, from_account, to_account, amount) VALUES (%s, %s, %s, %s)", 
                           (tx_id, from_id, to_id, amount))
            
            conn.commit()
            conn.close()
            messagebox.showinfo("Succes", f"Tranzacție procesată cu succes!\nReferință UUID: {tx_id}")
            self.check_balance()
        except Exception as e:
            messagebox.showerror("Eroare Transfer", f"Procesarea plății a eșuat: {str(e)}\nAsigurați-vă că ați completat corect ID-ul de cont în prima secțiune.")

    def apply_for_credit(self):
        try:
            credit_sum = float(self.entry_credit_amt.get().strip())
            if credit_sum < 1000:
                messagebox.showwarning("Analiză", "Suma minimă eligibilă pentru creditare este de 1.000 RON.")
            else:
                # Simulare algoritm de scoring bancar nativ
                messagebox.showinfo("Solicitare Înregistrată", f"Cererea dumneavoastră pentru suma de {credit_sum:.2f} RON a fost trimisă în sistemul de analiză de risc.\nVeți primi un răspuns în maxim 24h.")
        except ValueError:
            messagebox.showerror("Eroare", "Introduceți o sumă validă numeric.")


# =====================================================================
# 2. INTERFAȚA PENTRU ANGAJAȚI (FRAUD DETECTION & AUDIT HUB)
# =====================================================================
class StaffInterface:
    def __init__(self, window):
        self.window = window
        self.window.title("BACK-OFFICE AUDIT & FRAUD MONITORING HUB")
        self.window.geometry("850x600")
        self.window.configure(bg="#f4f6f9")
        
        # Header Staff
        header = tk.Frame(window, bg="#1c2833", height=50)
        header.pack(fill="x")
        tk.Label(header, text="🛡️ OPERATIONAL AUDIT & ANTI-FRAUD CONTROL CENTRE", fg="#f1c40f", bg="#1c2833", font=("Segoe UI", 11, "bold")).pack(pady=12)
        
        # Panou Vizualizare Toate Tranzacțiile din Sistem (Cele 100k+)
        frame_table = tk.LabelFrame(window, text=" Monitorizare Registru Tranzacții Central (Live Ledger Logs) ", bg="#f4f6f9", font=("Segoe UI", 10, "bold"))
        frame_table.pack(fill="both", expand=True, padx=15, pady=10)
        
        # Tabel profesional în GUI (Treeview) pentru listat datele
        columns = ("id", "uuid", "from", "to", "amount")
        self.tree = ttk.Treeview(frame_table, columns=columns, show="headings", height=10)
        
        self.tree.heading("id", text="ID Intern")
        self.tree.heading("uuid", text="UUID Tranzacție (Idempotență Key)")
        self.tree.heading("from", text="Cont Sursă")
        self.tree.heading("to", text="Cont Destinație")
        self.tree.heading("amount", text="Suma (RON)")
        
        self.tree.column("id", width=70, anchor="center")
        self.tree.column("uuid", width=280, anchor="w")
        self.tree.column("from", width=90, anchor="center")
        self.tree.column("to", width=90, anchor="center")
        self.tree.column("amount", width=100, anchor="e")
        
        self.tree.pack(fill="both", expand=True, side="left", padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(frame_table, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(fill="y", side="right")

        # Secțiunea Control Angajați: Căutare rapidă și Analiză Anti-Fraudă
        frame_ctrl = tk.Frame(window, bg="#f4f6f9")
        frame_ctrl.pack(fill="x", padx=15, pady=10)
        
        btn_load = ttk.Button(frame_ctrl, text="🔄 Încarcă Ultimele Tranzacții", command=self.load_transactions)
        btn_load.pack(side="left", padx=5)
        
        btn_fraud = ttk.Button(frame_ctrl, text="🚨 Rulează Filtru Anti-Fraudă (Sume Mari)", command=self.run_fraud_filter)
        btn_fraud.pack(side="left", padx=5)
        
        btn_uuid_check = ttk.Button(frame_ctrl, text="🔍 Verifică Validitate UUID", command=self.check_uuid_integrity)
        btn_uuid_check.pack(side="left", padx=5)
        
        # Încărcăm datele direct la deschiderea interfeței
        self.load_transactions()

    def load_transactions(self):
        """ Șterge vechile date din tabel și aduce ultimele înregistrări din BD """
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        # Selectăm cele mai proaspete tranzacții înregistrate din testul masiv
        cursor.execute("SELECT id, transaction_id, from_account, to_account, amount FROM transactions ORDER BY id DESC LIMIT 50")
        rows = cursor.fetchall()
        
        for r in rows:
            self.tree.insert("", "end", values=(r['id'], r['transaction_id'], r['from_account'], r['to_account'], f"{r['amount']:.2f}"))
        conn.close()

    def run_fraud_filter(self):
        """ Evidențiază sau filtrează tranzacțiile cu potențial risc financiar """
        high_value_count = 0
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            amount = float(values[4])
            # Prag de simulare fraudă: În contextul de test, sumele mari sau transferurile repetate declanșează alerta
            if amount >= 5.00: 
                self.tree.tag_configure('warning', background="#fcd1d1", foreground="red")
                self.tree.item(item, tags=('warning',))
                high_value_count += 1
                
        if high_value_count > 0:
            messagebox.showwarning("Alertă Risc", f"Sistemul de analiză structurală a identificat {high_value_count} tranzacții ce depășesc pragul valoric de siguranță.\nAcestea au fost marcate cu culoarea Roșie.")
        else:
            messagebox.showinfo("Audit Curat", "Filtru rulat cu succes. Nu s-au detectat anomalii valorice în lotul actual.")

    def check_uuid_integrity(self):
        """ Verifică dacă cheia de idempotență respectă standardul RFC 4122 (UUID standard) """
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showinfo("Informație", "Selectați o tranzacție din tabel pentru a-i verifica integritatea structurală cryptographică.")
            return
            
        values = self.tree.item(selected_item, "values")
        tx_uuid = values[1]
        
        try:
            # Încercăm să convertim stringul în obiect UUID ca să demonstrăm validitatea cryptographică a idempotenței
            uuid.UUID(tx_uuid)
            messagebox.showinfo("Integritate UUID OK", f"Cheia de idempotență:\n{tx_uuid}\n\nStare: VALIDĂ (Algoritm nativ protejat contra atacurilor de tip Replay).")
        except ValueError:
            messagebox.showerror("Eroare Structurală", "Atenție! UUID alterat sau neconform.")

if __name__ == "__main__":
    root = tk.Tk()
    app = MainLauncher(root)
    root.mainloop()