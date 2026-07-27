import os
import csv
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

HEADER = [
    "PRINTERNAME", "LABELFILE", "MATNR", "KTXT", "WEDAT", "EBELN", "EBELP",
    "BSTMG", "BSTME", "LGORT", "SSNA", "EXPDAT", "MUNDAT"
]

# =========================
# DATE & PRINT LOGIC
# =========================
def add_one_year_keep_day_month(d: date) -> date:
    """Add +1 year and keep day/month the same (Feb 29 -> Feb 28 if needed)."""
    try:
        return date(d.year + 1, d.month, d.day)
    except ValueError:
        return date(d.year + 1, 2, 28)

def generate_print_file(fields_data):
    """Handles the parsing of scan text and creation of the CSV/DAT file."""
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
        if len(scan_text) < 8:
            raise ValueError("Scan too short (< 8 characters).")

        tail8 = scan_text[-8:]   
        yymmdd = tail8[:6]       

        if not yymmdd.isdigit():
            raise ValueError(f"Expected 6 digits in last-8 prefix, got '{yymmdd}' from the input '{tail8}'.")

        yy = int(yymmdd[0:2])
        mm = int(yymmdd[2:4])
        dd = int(yymmdd[4:6])

        manu = date(2000 + yy, mm, dd)
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
class KonishiGlueForm(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Print Form - Konishi Glue Label")
        self.geometry("500x650")
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

        self.build_ui()

    def build_ui(self):
        header = tk.Frame(self, bg=self.colors["navy"], height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(
            header,
            text="Incoming Material - Konishi Glue",
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
        self.add_form_row(form_frame, 0, "Material No (MATNR):", "210838", "matnr")
        self.add_form_row(form_frame, 1, "Description (KTXT):", "Glue_FB300ZW (Konishi)", "ktxt")
        self.add_form_row(form_frame, 2, "Receipt Date (WEDAT):", "20251009", "wedat")
        self.add_form_row(form_frame, 3, "PO Number (EBELN):", "7000000309", "ebeln")
        self.add_form_row(form_frame, 4, "PO Item (EBELP):", "0", "ebelp")
        self.add_form_row(form_frame, 5, "Quantity (BSTMG):", "10", "bstmg")
        self.add_form_row(form_frame, 6, "Unit (BSTME):", "PCS", "bstme")
        self.add_form_row(form_frame, 7, "Storage Loc (LGORT):", "0028", "lgort")
        self.add_form_row(form_frame, 8, "Location (SSNA):", "WH2-MAT-FEFO-R6", "ssna")
        self.add_form_row(form_frame, 9, "Number of Copies:", "1", "copies", is_number=True)

        tk.Frame(form_frame, bg=self.colors["border"], height=1).grid(row=10, column=0, columnspan=2, sticky="ew", pady=10)

        # Scan Input Field
        tk.Label(
            form_frame,
            text="Scan QR Code:",
            font=("Segoe UI", 11, "bold"),
            bg=self.colors["card"],
            fg=self.colors["blue_dark"],
            anchor="e"
        ).grid(row=11, column=0, sticky="e", pady=10, padx=(15, 5))

        scan_var = tk.StringVar()
        self.scan_entry = ttk.Entry(form_frame, textvariable=scan_var, font=("Segoe UI", 12), width=25)
        self.scan_entry.grid(row=11, column=1, sticky="w", pady=10, padx=(5, 15))
        self.fields["scan_text"] = scan_var
        
        # Bind the Enter key to automatically print when scanner finishes input
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

    def add_form_row(self, parent, row, label_text, default_val, key, is_number=False):
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
            entry = ttk.Entry(parent, textvariable=var, font=("Segoe UI", 10), width=28)
            
        entry.grid(row=row, column=1, sticky="w", pady=8, padx=(5, 15))
        self.fields[key] = var

    def execute_print(self):
        # Extract data from fields
        current_data = {}
        for key, var in self.fields.items():
            current_data[key] = var.get().strip()

        # Validate Copies
        try:
            current_data["copies"] = int(current_data["copies"])
            if current_data["copies"] < 1:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Input", "Number of copies must be a positive integer.")
            self.scan_entry.focus_set()
            return

        # Validate Required Fields
        if not all([current_data["matnr"], current_data["ktxt"], current_data["scan_text"]]):
            messagebox.showwarning("Missing Data", "Please fill out all required fields and ensure a QR code is scanned.")
            self.scan_entry.focus_set()
            return

        # Trigger file generation
        success, msg, mfg_date, exp_date = generate_print_file(current_data)

        if success:
            # Clear scan text for the next item and keep focus
            self.fields["scan_text"].set("")
            self.scan_entry.focus_set()
        else:
            messagebox.showerror("Print Failed", f"An error occurred while parsing or generating the print file:\n\n{msg}")
            self.scan_entry.focus_set()

if __name__ == "__main__":
    app = KonishiGlueForm()
    app.mainloop()