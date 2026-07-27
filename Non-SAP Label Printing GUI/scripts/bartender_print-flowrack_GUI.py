import os
import csv
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk

# =========================
# CONFIG (edit here)
# =========================
WATCHED_FOLDER = r"Z:"                  
PRINT_FILE_EXT = "csv"                    
DELIMITER = "\t"                          

PRINTERNAME = "LBL_PRINTER_WH_VN"
LABELFILE   = "Flow_rack_label.BTW"
LOG_FILE = r"C:\bt_watchedfolder_qr_print\qr_print_log.csv"

# --- Database Config ---
# Goes up one level from the 'scripts' folder to the project root, then into 'databases'
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATABASE_FILE = os.path.join(PROJECT_ROOT, "databases", "WH Slog 2.csv")
DB_DELIMITER = "\t"  

HEADER = ["PRINTERNAME", "LABELFILE", "MATNR", "KTXT", "SSNA", "LGORT"]

# =========================
# PRINT LOGIC
# =========================
def generate_print_file(matnr, ktxt, ssna, lgort, copies):
    """Handles the creation of the CSV/DAT file for BarTender Integration."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    os.makedirs(WATCHED_FOLDER, exist_ok=True)

    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(["timestamp", "mundat", "expdat", "print_filename", "status", "message"])

    mundat_str = ""
    expdat_str = ""
    print_filename = ""
    
    try:
        row = [PRINTERNAME, LABELFILE, matnr, ktxt, ssna, lgort]
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        print_filename = f"print_{ts}.{PRINT_FILE_EXT}"

        final_path = os.path.join(WATCHED_FOLDER, print_filename)
        tmp_path = os.path.join(WATCHED_FOLDER, f".{print_filename}.tmp")

        with open(tmp_path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, delimiter=DELIMITER)
            w.writerow(HEADER)
            for _ in range(copies):
                w.writerow(row)

        os.replace(tmp_path, final_path)

        msg = f"OK -> MATNR={matnr} SSNA={ssna} COPIES={copies} FILE={final_path}"
        
        with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([
                datetime.now().isoformat(timespec="seconds"),
                mundat_str,
                expdat_str,
                print_filename,
                "OK",
                msg
            ])
        return True, msg

    except Exception as e:
        msg = f"ERROR -> {e}"
        with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([
                datetime.now().isoformat(timespec="seconds"),
                mundat_str,
                expdat_str,
                print_filename,
                "ERROR",
                str(e)
            ])
        return False, msg


# =========================
# GUI APP
# =========================
class FlowRackForm(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Print Form - Flow Rack Label")
        self.geometry("460x420")
        self.resizable(False, False)
        self.configure(bg="#f5f8fc")

        self.colors = {
            "navy": "#062445",
            "blue": "#0b5db3",
            "blue_dark": "#084a90",
            "text": "#071a33",
            "card": "#ffffff",
            "border": "#d3dce8"
        }

        # Load the CSV database into memory
        self.material_db = self.load_database()

        self.build_ui()

    def load_database(self):
        """Reads the material database CSV and returns a dictionary mapped by MATNR."""
        db = {}
        if not os.path.exists(DATABASE_FILE):
            print(f"Warning: Database file '{DATABASE_FILE}' not found.")
            return db

        try:
            with open(DATABASE_FILE, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter=DB_DELIMITER)
                for row in reader:
                    # Strip whitespace to prevent matching errors
                    matnr = row.get("MATNR", "").strip()
                    if matnr:
                        db[matnr] = {
                            "ktxt": row.get("KTXT", "").strip(),
                            "ssna": row.get("SSNA", "").strip(),
                            "lgort": row.get("LGORT", "").strip()
                        }
        except Exception as e:
            print(f"Error reading database: {e}")
            
        return db

    def build_ui(self):
        # Header
        header = tk.Frame(self, bg=self.colors["navy"], height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(
            header,
            text="Flow Rack Label Data",
            font=("Segoe UI", 16, "bold"),
            bg=self.colors["navy"],
            fg="white"
        ).pack(side="left", padx=20, pady=15)

        # Main Form Container
        form_frame = tk.Frame(
            self, 
            bg=self.colors["card"],
            highlightbackground=self.colors["border"],
            highlightthickness=1
        )
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.fields = {}
        
        # Grid Setup for Form
        form_frame.columnconfigure(0, weight=1, pad=15)
        form_frame.columnconfigure(1, weight=3, pad=15)

        # Added 'readonly' argument to lock fields that are auto-populated
        self.add_form_row(form_frame, 0, "Material No (MATNR):", "", "matnr")
        self.add_form_row(form_frame, 1, "Description (KTXT):", "", "ktxt", readonly=True)
        self.add_form_row(form_frame, 2, "Location (SSNA):", "", "ssna", readonly=True)
        self.add_form_row(form_frame, 3, "Storage Loc (LGORT):", "", "lgort", readonly=True)
        self.add_form_row(form_frame, 4, "Number of Copies:", "1", "copies", is_number=True)

        # Bind the MATNR field to the auto_fill logic
        self.fields["matnr"].trace_add("write", self.auto_fill)

        # Buttons
        btn_frame = tk.Frame(self, bg="#f5f8fc")
        btn_frame.pack(fill="x", padx=20, pady=(0, 20))

        cancel_btn = tk.Button(
            btn_frame,
            text="Cancel",
            command=self.destroy,
            font=("Segoe UI", 10),
            bg="#e2e6eb",
            fg="#333333",
            borderwidth=0,
            cursor="hand2",
            width=10,
            height=2
        )
        cancel_btn.pack(side="left")

        print_btn = tk.Button(
            btn_frame,
            text="▶ Print Label",
            command=self.execute_print,
            font=("Segoe UI", 10, "bold"),
            bg=self.colors["blue"],
            fg="white",
            activebackground=self.colors["blue_dark"],
            activeforeground="white",
            borderwidth=0,
            cursor="hand2",
            width=15,
            height=2
        )
        print_btn.pack(side="right")

    def add_form_row(self, parent, row, label_text, default_val, key, is_number=False, readonly=False):
        # Label
        tk.Label(
            parent,
            text=label_text,
            font=("Segoe UI", 10, "bold"),
            bg=self.colors["card"],
            fg=self.colors["text"],
            anchor="e"
        ).grid(row=row, column=0, sticky="e", pady=15, padx=(15, 5))

        # Entry
        var = tk.StringVar(value=default_val)
        if is_number:
            entry = ttk.Spinbox(parent, from_=1, to=1000, textvariable=var, font=("Segoe UI", 11), width=5)
        else:
            entry = ttk.Entry(parent, textvariable=var, font=("Segoe UI", 11), width=25)
            if readonly:
                entry.config(state="readonly")
            
        entry.grid(row=row, column=1, sticky="w", pady=15, padx=(5, 15))
        self.fields[key] = var

    def auto_fill(self, *args):
        """Triggers every time the user types in the MATNR field to search the database."""
        current_matnr = self.fields["matnr"].get().strip()
        
        if current_matnr in self.material_db:
            # Match found: populate fields
            data = self.material_db[current_matnr]
            self.fields["ktxt"].set(data["ktxt"])
            self.fields["ssna"].set(data["ssna"])
            self.fields["lgort"].set(data["lgort"])
        else:
            # No match: clear fields
            self.fields["ktxt"].set("")
            self.fields["ssna"].set("")
            self.fields["lgort"].set("")

    def execute_print(self):
        matnr = self.fields["matnr"].get().strip()
        ktxt = self.fields["ktxt"].get().strip()
        ssna = self.fields["ssna"].get().strip()
        lgort = self.fields["lgort"].get().strip()
        
        try:
            copies = int(self.fields["copies"].get())
            if copies < 1:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Input", "Number of copies must be a positive integer.")
            return

        if not all([matnr, ktxt, ssna, lgort]):
            messagebox.showwarning("Missing Data", "Please fill out all required fields before printing. Make sure you entered a valid Material No.")
            return

        success, msg = generate_print_file(matnr, ktxt, ssna, lgort, copies)

        if success:
            messagebox.showinfo("Success", f"Print job sent successfully!\n\nDetails:\nMATNR: {matnr}\nCopies: {copies}")
            self.destroy()  
        else:
            messagebox.showerror("Print Failed", f"An error occurred while generating the print file:\n\n{msg}")

if __name__ == "__main__":
    app = FlowRackForm()
    app.mainloop()