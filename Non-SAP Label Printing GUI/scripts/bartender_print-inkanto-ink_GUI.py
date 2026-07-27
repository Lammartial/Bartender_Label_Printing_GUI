import os
import csv
import re
import urllib.request
from datetime import datetime, date
import tkinter as tk
from tkinter import messagebox, ttk

# =========================
# CONFIG 
# =========================
WATCHED_FOLDER = r"Z:"                  
PRINT_FILE_EXT = "csv"                    
DELIMITER = "\t"                          

PRINTERNAME = "LBL_PRINTER_WH_VN"
LABELFILE   = "Incoming_material_label.BTW"
LOG_FILE = r"C:\bt_watchedfolder_qr_print\qr_print_log.csv"

# --- Database Config ---
# Goes up one level from the 'scripts' folder to the project root, then into 'databases'
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATABASE_FILE = os.path.join(PROJECT_ROOT, "databases", "WH Slog 2.csv")
DB_DELIMITER = "\t"  # Change to "," if your CSV uses commas instead of tabs

HEADER = [
    "PRINTERNAME", "LABELFILE", "MATNR", "KTXT", "WEDAT", "EBELN", "EBELP",
    "BSTMG", "BSTME", "LGORT", "SSNA", "EXPDAT", "MUNDAT"
]

# =========================
# DATE & WEB SCRAPING LOGIC
# =========================
def add_one_year_keep_day_month(d: date) -> date:
    """Add +1 year and keep day/month the same (Feb 29 -> Feb 28 if needed)."""
    try:
        return date(d.year + 1, d.month, d.day)
    except ValueError:
        return date(d.year + 1, 2, 28)

def generate_print_file(fields_data):
    """Fetches Mfg Date from Inkanto website URL and writes BarTender print file."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    os.makedirs(WATCHED_FOLDER, exist_ok=True)

    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(["timestamp", "scan_text", "mundat", "expdat", "print_filename", "status", "message"])

    scan_text = fields_data["scan_text"]
    mundat_str = ""
    expdat_str = ""
    print_filename = ""
    
    try:
        # Validate URL format
        if not scan_text.lower().startswith(("http://", "https://")):
            raise ValueError("Input is not a URL (expected https://... from the Inkanto QR code).")

        # Fetch HTML from Inkanto portal
        req = urllib.request.Request(
            scan_text,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="ignore")

        # Parse Manufacturing Date from HTML response
        m = re.search(
            r'Manufacturing Date:\s*</span>\s*<span[^>]*class="specifications__value"[^>]*>\s*([0-9]{2}/[0-9]{2}/[0-9]{4})\s*</span>',
            html,
            flags=re.IGNORECASE | re.DOTALL
        )
        if not m:
            raise ValueError("Manufacturing Date not found on website (HTML pattern not matched).")

        manu_text = m.group(1)  # e.g., "05/03/2026"

        # Parse manufacturing date format (dd/mm/yyyy or mm/dd/yyyy fallback)
        p1, p2, p3 = manu_text.split("/")
        a, b, y = int(p1), int(p2), int(p3)

        if a > 12:
            dd, mm = a, b
        elif b > 12:
            dd, mm = b, a
        else:
            dd, mm = a, b

        manu = date(y, mm, dd)
        exp = add_one_year_keep_day_month(manu)

        mundat_str = manu.strftime("%Y%m%d")
        expdat_str = exp.strftime("%Y%m%d")

        row = [
            PRINTERNAME, LABELFILE, fields_data["matnr"], fields_data["ktxt"], 
            fields_data["wedat"], fields_data["ebeln"], fields_data["ebelp"],
            fields_data["bstmg"], fields_data["bstme"], fields_data["lgort"], 
            fields_data["ssna"], expdat_str, mundat_str
        ]

        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        print_filename = f"print_{ts}.{PRINT_FILE_EXT}"

        final_path = os.path.join(WATCHED_FOLDER, print_filename)
        tmp_path = os.path.join(WATCHED_FOLDER, f".{print_filename}.tmp")

        with open(tmp_path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, delimiter=DELIMITER)
            w.writerow(HEADER)
            for _ in range(fields_data["copies"]):
                w.writerow(row)

        os.replace(tmp_path, final_path)

        msg = f"OK -> MUNDAT={mundat_str} EXPDAT={expdat_str} FILE={final_path}"
        
        with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([
                datetime.now().isoformat(timespec="seconds"),
                scan_text,
                mundat_str,
                expdat_str,
                print_filename,
                "OK",
                msg
            ])
        return True, msg, mundat_str, expdat_str

    except Exception as e:
        msg = f"ERROR -> {e}"
        with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([
                datetime.now().isoformat(timespec="seconds"),
                scan_text,
                mundat_str,
                expdat_str,
                print_filename,
                "ERROR",
                str(e)
            ])
        return False, msg, "", ""


# =========================
# GUI APP
# =========================
class TTRLabelForm(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Print Form - Material Incoming Label (TTR)")
        self.geometry("520x650")
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
            print(f"Warning: Database file not found at '{DATABASE_FILE}'.")
            return db

        try:
            with open(DATABASE_FILE, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter=DB_DELIMITER)
                for row in reader:
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
        header = tk.Frame(self, bg=self.colors["navy"], height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(
            header,
            text="Incoming Material - TTR Ribbon",
            font=("Segoe UI", 16, "bold"),
            bg=self.colors["navy"],
            fg="white"
        ).pack(side="left", padx=20, pady=15)

        form_frame = tk.Frame(
            self, 
            bg=self.colors["card"],
            highlightbackground=self.colors["border"],
            highlightthickness=1
        )
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.fields = {}
        
        form_frame.columnconfigure(0, weight=1, pad=10)
        form_frame.columnconfigure(1, weight=3, pad=10)

        # Standard Fields
        # KTXT, LGORT, and SSNA are set to readonly=True and default to empty
        self.add_form_row(form_frame, 0, "Material No (MATNR):", "", "matnr")
        self.add_form_row(form_frame, 1, "Description (KTXT):", "", "ktxt", readonly=True)
        self.add_form_row(form_frame, 2, "Receipt Date (WEDAT):", "20251009", "wedat")
        self.add_form_row(form_frame, 3, "PO Number (EBELN):", "7000000309", "ebeln")
        self.add_form_row(form_frame, 4, "PO Item (EBELP):", "0", "ebelp")
        self.add_form_row(form_frame, 5, "Quantity (BSTMG):", "1", "bstmg")
        self.add_form_row(form_frame, 6, "Unit (BSTME):", "PCS", "bstme")
        self.add_form_row(form_frame, 7, "Storage Loc (LGORT):", "", "lgort", readonly=True)
        self.add_form_row(form_frame, 8, "Location (SSNA):", "", "ssna", readonly=True) 
        self.add_form_row(form_frame, 9, "Number of Copies:", "1", "copies", is_number=True)
        tk.Frame(form_frame, bg=self.colors["border"], height=1).grid(row=10, column=0, columnspan=2, sticky="ew", pady=10)

        # Bind the MATNR field to the auto_fill logic
        self.fields["matnr"].trace_add("write", self.auto_fill)

        # Scan Input Field
        tk.Label(
            form_frame,
            text="Scan Inkanto URL:",
            font=("Segoe UI", 11, "bold"),
            bg=self.colors["card"],
            fg=self.colors["blue_dark"],
            anchor="e"
        ).grid(row=11, column=0, sticky="e", pady=10, padx=(15, 5))

        scan_var = tk.StringVar()
        self.scan_entry = ttk.Entry(form_frame, textvariable=scan_var, font=("Segoe UI", 11), width=30)
        self.scan_entry.grid(row=11, column=1, sticky="w", pady=10, padx=(5, 15))
        self.fields["scan_text"] = scan_var
        
        # Bind Enter key to trigger printing
        self.scan_entry.bind('<Return>', lambda event: self.execute_print())
        self.scan_entry.focus_set()

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
        tk.Label(
            parent,
            text=label_text,
            font=("Segoe UI", 10, "bold"),
            bg=self.colors["card"],
            fg=self.colors["text"],
            anchor="e"
        ).grid(row=row, column=0, sticky="e", pady=8, padx=(15, 5))

        var = tk.StringVar(value=default_val)
        if is_number:
            entry = ttk.Spinbox(parent, from_=1, to=1000, textvariable=var, font=("Segoe UI", 10), width=5)
        else:
            entry = ttk.Entry(parent, textvariable=var, font=("Segoe UI", 10), width=30)
            if readonly:
                entry.config(state="readonly")
            
        entry.grid(row=row, column=1, sticky="w", pady=8, padx=(5, 15))
        self.fields[key] = var

    def auto_fill(self, *args):
        """Triggers every time the user types in the MATNR field to search the database."""
        current_matnr = self.fields["matnr"].get().strip()
        
        if current_matnr in self.material_db:
            data = self.material_db[current_matnr]
            self.fields["ktxt"].set(data["ktxt"])
            self.fields["ssna"].set(data["ssna"])
            self.fields["lgort"].set(data["lgort"])
        else:
            self.fields["ktxt"].set("")
            self.fields["ssna"].set("")
            self.fields["lgort"].set("")

    def execute_print(self):
        current_data = {}
        for key, var in self.fields.items():
            current_data[key] = var.get().strip()

        try:
            current_data["copies"] = int(current_data["copies"])
            if current_data["copies"] < 1:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Input", "Number of copies must be a positive integer.")
            self.scan_entry.focus_set()
            return

        # Added validation to ensure the auto-filled fields are populated before printing
        if not all([current_data["matnr"], current_data["ktxt"], current_data["lgort"], current_data["ssna"], current_data["scan_text"]]):
            messagebox.showwarning("Missing Data", "Please ensure a valid Material No is entered and a QR URL is scanned.")
            self.scan_entry.focus_set()
            return

        # Trigger file generation and website scraping
        success, msg, mfg_date, exp_date = generate_print_file(current_data)

        if success:
            self.fields["scan_text"].set("")
            self.scan_entry.focus_set()
        else:
            messagebox.showerror("Print Failed", f"An error occurred while fetching date or generating print file:\n\n{msg}")
            self.scan_entry.focus_set()

if __name__ == "__main__":
    app = TTRLabelForm()
    app.mainloop()