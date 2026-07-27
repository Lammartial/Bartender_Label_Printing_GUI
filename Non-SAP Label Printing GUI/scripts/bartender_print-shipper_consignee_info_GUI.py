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
LABELFILE   = "Shipper_Consignee_information.BTW"
LOG_FILE = r"C:\bt_watchedfolder_qr_print\qr_print_log.csv"

HEADER = [
    "PRINTERNAME", "LABELFILE", "CONSIGNEE", "CONSIGNEEADDRESS", "WEIGHT", "UNIT"
]

# =========================
# PRINT LOGIC
# =========================
def generate_print_file(consignee, address, weight, unit, copies):
    """Handles the creation of the CSV/DAT file for BarTender Integration."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    os.makedirs(WATCHED_FOLDER, exist_ok=True)

    # Ensure log file exists with standard headers
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(["timestamp", "mundat", "expdat", "print_filename", "status", "message"])

    mundat_str = ""
    expdat_str = ""
    print_filename = ""
    
    try:
        row = [PRINTERNAME, LABELFILE, consignee, address, weight, unit]
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        print_filename = f"print_{ts}.{PRINT_FILE_EXT}"

        final_path = os.path.join(WATCHED_FOLDER, print_filename)
        tmp_path = os.path.join(WATCHED_FOLDER, f".{print_filename}.tmp")

        # Write to temporary file first
        with open(tmp_path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, delimiter=DELIMITER)
            w.writerow(HEADER)
            for _ in range(copies):
                w.writerow(row)

        # Move to watched folder to trigger BarTender Integration
        os.replace(tmp_path, final_path)

        msg = f"OK -> CONSIGNEE={consignee} WEIGHT={weight}{unit} FILE={final_path}"
        
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
class ShipperConsigneeForm(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Print Form - Shipper Consignee Info Label")
        self.geometry("520x460")
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
        # Header
        header = tk.Frame(self, bg=self.colors["navy"], height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(
            header,
            text="Shipper Consignee Information",
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
        
        # Grid Setup
        form_frame.columnconfigure(0, weight=1, pad=15)
        form_frame.columnconfigure(1, weight=3, pad=15)

        # Form Rows
        self.add_form_row(form_frame, 0, "Consignee:", "RRC POWER SOLUTIONS GMBH", "consignee")
        self.add_form_row(form_frame, 1, "Address:", "TECHNOLOGIEPARK 1, 66424 HOMBURG, GERMANY", "address")
        self.add_form_row(form_frame, 2, "Weight:", "120.6", "weight")
        self.add_form_row(form_frame, 3, "Unit:", "KG", "unit")
        self.add_form_row(form_frame, 4, "Number of Copies:", "1", "copies", is_number=True)

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

    def add_form_row(self, parent, row, label_text, default_val, key, is_number=False, width=35):
        tk.Label(
            parent,
            text=label_text,
            font=("Segoe UI", 10, "bold"),
            bg=self.colors["card"],
            fg=self.colors["text"],
            anchor="e"
        ).grid(row=row, column=0, sticky="e", pady=12, padx=(15, 5))

        var = tk.StringVar(value=default_val)
        if is_number:
            entry = ttk.Spinbox(parent, from_=1, to=1000, textvariable=var, font=("Segoe UI", 10), width=5)
        else:
            entry = ttk.Entry(parent, textvariable=var, font=("Segoe UI", 10), width=width)
            
        entry.grid(row=row, column=1, sticky="w", pady=15, padx=(5, 15))
        self.fields[key] = var

    def execute_print(self):
        consignee = self.fields["consignee"].get().strip()
        address = self.fields["address"].get().strip()
        unit = self.fields["unit"].get().strip()
        
        # Validate Weight
        try:
            weight = float(self.fields["weight"].get().strip())
        except ValueError:
            messagebox.showerror("Invalid Input", "Weight must be a valid number (e.g. 120.6).")
            return

        # Validate Copies
        try:
            copies = int(self.fields["copies"].get())
            if copies < 1:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Input", "Number of copies must be a positive integer.")
            return

        if not all([consignee, address, unit]):
            messagebox.showwarning("Missing Data", "Please fill out all required fields before printing.")
            return

        # Trigger file generation
        success, msg = generate_print_file(consignee, address, weight, unit, copies)

        if success:
            messagebox.showinfo("Success", f"Print job sent successfully!\n\nConsignee: {consignee}\nWeight: {weight} {unit}\nCopies: {copies}")
            self.destroy()
        else:
            messagebox.showerror("Print Failed", f"An error occurred while generating the print file:\n\n{msg}")

if __name__ == "__main__":
    app = ShipperConsigneeForm()
    app.mainloop()