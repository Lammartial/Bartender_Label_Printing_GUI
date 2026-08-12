import os
import csv
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk
import pandas as pd
from pathlib import Path

# =========================
# RETRIEVE LATEST DATABASE 
# =========================

USER_HOME = os.path.expanduser("~")

SOURCE_FILE = Path(
    USER_HOME + r"\RRC power solutions\RRC VN - Documents\600_Quality\640_Q-Equipments\Q-Equipments-Overview.xlsx"
)

SOURCE_SHEET = "Q-ID Overview"

OUTPUT_FILE = Path(
    USER_HOME + r"\RRC power solutions\RRC VN - Documents\999_SHARE_VN\290_IT\Non-SAP Label Printing GUI\databases\Equipment_DB.csv"
)

# ==========================================
# LOAD EXCEL
# ==========================================

print("Loading Excel file...")

df = pd.read_excel(
    SOURCE_FILE,
    sheet_name=SOURCE_SHEET,
    dtype=str
)

# Replace NaN with empty string
df = df.fillna("")

print("Detected columns:")

for col in df.columns:
    print(repr(col))


# ==========================================
# FIND REQUIRED COLUMNS
# ==========================================

qid_col = None
inventory_col = None

for col in df.columns:

    col_text = (
        str(col)
        .replace("\n", " ")
        .replace("\r", " ")
        .replace("\xa0", " ")
        .strip()
        .lower()
    )

    if "q-id" in col_text:
        qid_col = col

    if "inventory number" in col_text:
        inventory_col = col


if qid_col is None:
    raise ValueError(
        "Could not find a column containing 'Q-ID'.\n\n"
        f"Detected columns:\n{list(df.columns)}"
    )


if inventory_col is None:
    raise ValueError(
        "Could not find a column containing 'Inventory Number'.\n\n"
        f"Detected columns:\n{list(df.columns)}"
    )

print(f"Detected Q-ID column: {qid_col}")
print(f"Detected Inventory column: {inventory_col}")


# ==========================================
# SELECT & RENAME COLUMNS
# ==========================================

df = df[
    [
        qid_col,
        inventory_col
    ]
].rename(
    columns={
        qid_col: "QUALITY_EQUIPMENT_NO",
        inventory_col: "INVENTORY_NUMBER"
    }
)

# ==========================================
# CLEAN DATA
# ==========================================

df["QUALITY_EQUIPMENT_NO"] = (
    df["QUALITY_EQUIPMENT_NO"]
    .astype(str)
    .replace(["nan", "NaN"], "")
    .str.strip()
)

df["INVENTORY_NUMBER"] = (
    df["INVENTORY_NUMBER"]
    .astype(str)
    .replace(["nan", "NaN", "NA", "N/A"], "")
    .str.strip()
)

# Keep every equipment, even if Inventory Number is blank.
# Only remove rows where the Q-ID itself is missing.
df = df[
    df["QUALITY_EQUIPMENT_NO"] != ""
]

# Remove duplicate equipment/inventory combinations
df = df.drop_duplicates()

# Sort by equipment number (optional)
df = df.sort_values(
    by="QUALITY_EQUIPMENT_NO"
).reset_index(drop=True)


# ==========================================
# EXPORT CSV
# ==========================================

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

df.to_csv(
    OUTPUT_FILE,
    sep="\t",
    index=False,
    encoding="utf-8"
)

# ==========================================
# FINISHED
# ==========================================

print()
print("========================================")
print("Equipment database created successfully.")
print(f"Rows exported : {len(df)}")
print(f"Output file   : {OUTPUT_FILE}")
print("========================================")


# =========================
# Q-Equipment Label Printing 
# =========================
WATCHED_FOLDER = r"Z:"                  
PRINT_FILE_EXT = "csv"                  
DELIMITER = "\t"                        

PRINTERNAME = "LBL_PRINTER_WH_VN"
LABELFILE = "Measuring Equipment Label_18x38mm.BTW"
LOG_FILE = r"C:\bt_watchedfolder_qr_print\qr_print_log.csv"

# --- Database Config ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATABASE_FILE = os.path.join(PROJECT_ROOT, "databases", "Equipment_DB.csv")
DB_DELIMITER = "\t"  

# =========================
# DATA CONFIG
# =========================
DATABASE_FIELDS = [
    "QUALITY_EQUIPMENT_NO",   
    "INVENTORY_NUMBER",    
]

HEADER = ["PRINTERNAME", "LABELFILE"] + DATABASE_FIELDS


# =========================
# CORE PRINT LOGIC
# =========================
def generate_print_file(jobs_list):
    """Generates the CSV file for BarTender based on a provided list of job dictionaries."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    os.makedirs(WATCHED_FOLDER, exist_ok=True)

    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(["timestamp", "print_filename", "status", "message", "jobs_printed"])

    try:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        print_filename = f"print_{ts}.{PRINT_FILE_EXT}"
        final_path = os.path.join(WATCHED_FOLDER, print_filename)
        tmp_path = os.path.join(WATCHED_FOLDER, f".{print_filename}.tmp")

        with open(tmp_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=HEADER, delimiter=DELIMITER, extrasaction="raise")
            writer.writeheader()

            for job_data in jobs_list:
                row = job_data.copy()
                row["PRINTERNAME"] = PRINTERNAME
                row["LABELFILE"] = LABELFILE
                writer.writerow(row)

        os.replace(tmp_path, final_path)
        msg = f"OK -> FILE={final_path} JOBS={len(jobs_list)}"
        
        with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([
                datetime.now().isoformat(timespec="seconds"), print_filename, "OK", msg, len(jobs_list)
            ])
            
        return True, msg

    except Exception as e:
        msg = f"ERROR -> {e}"
        with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([
                datetime.now().isoformat(timespec="seconds"), "FAILED", "ERROR", str(e), 0
            ])
        return False, msg


# =========================
# GUI APP
# =========================
class Q_Equipment_Menu(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Measuring Equipment - Label Print System")
        self.geometry("450x300")
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
        
        self.equipment_db = self.load_database()
        self.build_ui()

    def load_database(self):
        """Reads the equipment database CSV and returns a dictionary mapped by QUALITY_EQUIPMENT_NO."""
        db = {}
        if not os.path.exists(DATABASE_FILE):
            print(f"Warning: Database file not found at '{DATABASE_FILE}'. Database lookups will fail.")
            return db
        try:
            with open(DATABASE_FILE, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter=DB_DELIMITER)
                for row in reader:
                    q_id = row.get("QUALITY_EQUIPMENT_NO", "").strip()
                    if q_id:
                        inventory = (
                            row.get("INVENTORY_NUMBER","").strip()
                        )

                        if inventory.upper() == "NA":
                            inventory = ""

                        db[q_id] = {
                            "INVENTORY_NUMBER": inventory
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
            text="Measuring Equipment Labels",
            font=("Segoe UI", 14, "bold"),
            bg=self.colors["navy"],
            fg="white"
        ).pack(pady=15)

        form_frame = tk.Frame(self, bg=self.colors["card"], highlightbackground=self.colors["border"], highlightthickness=1)
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(
            form_frame,
            text="Select Print Method:",
            font=("Segoe UI", 12, "bold"),
            bg=self.colors["card"],
            fg=self.colors["text"]
        ).pack(pady=(15, 10))

        # Button 1: Auto Print predefined jobs
        tk.Button(
            form_frame,
            text="Option 1: Print All Equipment Labels",
            command=self.execute_batch_print,
            font=("Segoe UI", 10, "bold"),
            bg=self.colors["navy"],
            fg="white",
            activebackground=self.colors["blue_dark"],
            activeforeground="white",
            borderwidth=0,
            cursor="hand2",
            height=2,
            width=35
        ).pack(pady=5)

        # Button 2: Manual entry and DB lookup
        tk.Button(
            form_frame,
            text="Option 2: Manual Entry / Database Print",
            command=self.open_manual_form,
            font=("Segoe UI", 10, "bold"),
            bg=self.colors["blue"],
            fg="white",
            activebackground=self.colors["blue_dark"],
            activeforeground="white",
            borderwidth=0,
            cursor="hand2",
            height=2,
            width=35
        ).pack(pady=5)

    def execute_batch_print(self):
        """
        Batch print every equipment contained in Equipment_DB.csv.
        """

        jobs_list = []
        for quality_no, data in self.equipment_db.items():

            jobs_list.append({

                "QUALITY_EQUIPMENT_NO": quality_no,
                "INVENTORY_NUMBER": data.get(
                    "INVENTORY_NUMBER",
                    ""
                )
            })

        if not jobs_list:

            messagebox.showwarning(
                "Database Empty",
                "Equipment_DB.csv does not contain any equipment."
            )
            return
        
        # for dictionary in jobs_list:
        #     for key, item in dictionary.items():
        #         print(f"{key}: {item}")

        # =========================
        # CONFIRM PRINTING
        # =========================

        answer = messagebox.askyesno(
            "Confirm Batch Print",

            "You are about to print ALL equipment labels.\n\n"
            f"Number of labels : {len(jobs_list)}\n\n"
            "This will immediately send all labels to the BarTender "
            "print queue.\n\n"
            "Do you want to continue?"

        )

        if not answer:
            return

        # =========================
        # GENERATE PRINT FILE
        # =========================

        success, msg = generate_print_file(
            jobs_list
        )

        if success:
            messagebox.showinfo(
                "Batch Print Complete",
                f"Successfully queued {len(jobs_list)} equipment labels for printing."
            )

        else:
            messagebox.showerror(
                "Print Failed",
                f"An error occurred:\n\n{msg}"
            )

    def open_manual_form(self):
        """Opens a Toplevel window for manual DB lookup printing."""
        ManualPrintWindow(self)

class ManualPrintWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Manual Label Print")
        self.geometry("450x320")
        self.resizable(False, False)
        self.configure(bg="#f5f8fc")
        
        self.fields = {}
        self.build_ui()

    def build_ui(self):
        header = tk.Frame(self, bg=self.parent.colors["blue_dark"], height=50)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(
            header,
            text="Database Lookup Print",
            font=("Segoe UI", 12, "bold"),
            bg=self.parent.colors["blue_dark"],
            fg="white"
        ).pack(pady=12)

        form_frame = tk.Frame(self, bg=self.parent.colors["card"], highlightbackground=self.parent.colors["border"], highlightthickness=1)
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)

        form_frame.columnconfigure(0, weight=1, pad=10)
        form_frame.columnconfigure(1, weight=2, pad=10)

        # 2. Add weights to invisible top (0) and bottom (4) rows to push fields to the middle
        form_frame.rowconfigure(0, weight=1)
        form_frame.rowconfigure(4, weight=1)

        # 3. Shifted the row numbers to 1, 2, and 3
        self.add_form_row(form_frame, 1, "Quality Equipment No:", "", "q_id")
        self.add_form_row(form_frame, 2, "Inventory Number:", "", "inv_no", readonly=True)
        self.add_form_row(form_frame, 3, "Number of Copies:", "1", "copies", is_number=True)

        self.fields["q_id"].trace_add("write", self.auto_fill)

        btn_frame = tk.Frame(self, bg="#f5f8fc")
        btn_frame.pack(fill="x", padx=20, pady=(0, 20))

        tk.Button(
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
        ).pack(side="left")

        tk.Button(
            btn_frame,
            text="▶ Print Label",
            command=self.execute_manual_print,
            font=("Segoe UI", 10, "bold"),
            bg=self.parent.colors["blue"],
            fg="white",
            borderwidth=0,
            cursor="hand2",
            width=15,
            height=2
        ).pack(side="right")

    def add_form_row(self, parent, row, label_text, default_val, key, is_number=False, readonly=False):
        tk.Label(
            parent,
            text=label_text,
            font=("Segoe UI", 10, "bold"),
            bg=self.parent.colors["card"],
            fg=self.parent.colors["text"],
            anchor="e"
        ).grid(row=row, column=0, sticky="e", pady=10, padx=(10, 5))

        var = tk.StringVar(value=default_val)
        if is_number:
            entry = ttk.Spinbox(parent, from_=1, to=1000, textvariable=var, font=("Segoe UI", 10), width=5)
        else:
            entry = ttk.Entry(parent, textvariable=var, font=("Segoe UI", 10), width=22)
            if readonly:
                entry.config(state="readonly")
            
        entry.grid(row=row, column=1, sticky="w", pady=10, padx=(5, 10))
        self.fields[key] = var

    def auto_fill(self, *args):
        """Auto-fills the INVENTORY_NUMBER field if Q_ID matches the database."""
        current_q_id = self.fields["q_id"].get().strip()
        
        if current_q_id in self.parent.equipment_db:
            data = self.parent.equipment_db[current_q_id]
            self.fields["inv_no"].set(data["INVENTORY_NUMBER"])
        else:
            self.fields["inv_no"].set("")

    def execute_manual_print(self):
        q_id = self.fields["q_id"].get().strip()
        inv_no = self.fields["inv_no"].get().strip()
        
        try:
            copies = int(self.fields["copies"].get())
            if copies < 1: raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Input", "Copies must be a positive integer.")
            return

        if not q_id:
            messagebox.showwarning(
                "Missing Data",
                "Please enter a valid Quality Equipment Number."
            )
            return

        if q_id not in self.parent.equipment_db:
            messagebox.showwarning(
                "Not Found",
                "The Quality Equipment Number was not found in Equipment_DB.csv."
            )
            return

        # Construct a list of dictionaries duplicating the single job per # of copies requested.
        # This keeps the generate_print_file logic unified.
        jobs_list = []
        for _ in range(copies):
            jobs_list.append({
                "QUALITY_EQUIPMENT_NO": q_id,
                "INVENTORY_NUMBER": inv_no
            })

        success, msg = generate_print_file(jobs_list)

        if success:
            messagebox.showinfo("Success", "Label printed successfully!")
            self.fields["q_id"].set("") # clear for next scan/entry
        else:
            messagebox.showerror("Print Failed", f"An error occurred:\n\n{msg}")

if __name__ == "__main__":
    app = Q_Equipment_Menu()
    app.mainloop()