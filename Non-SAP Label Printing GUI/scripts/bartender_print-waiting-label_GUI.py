import os
import csv
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk

# =========================
# CONFIG
# =========================
WATCHED_FOLDER = r"Z:\Static"                  
PRINT_FILE_EXT = "csv"                    
DELIMITER = "\t"                          

PRINTERNAME = "LBL_PRINTER_WH_VN"
LABELFILE   = "Waiting label.BTW"
LOG_FILE = r"C:\bt_watchedfolder_qr_print\qr_print_log.csv"

HEADER = ["PRINTERNAME", "LABELFILE"]

# =========================
# PRINT LOGIC
# =========================
def generate_print_file(copies):
    """Handles the creation of the CSV/DAT file for BarTender Integration."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    os.makedirs(WATCHED_FOLDER, exist_ok=True)

    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(["timestamp", "mundat", "expdat", "print_filename", "status", "message"])

    mundat_str = ""
    expdat_str = ""
    row = [PRINTERNAME, LABELFILE]
    
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    print_filename = f"print_{ts}.{PRINT_FILE_EXT}"

    final_path = os.path.join(WATCHED_FOLDER, print_filename)
    tmp_path = os.path.join(WATCHED_FOLDER, f".{print_filename}.tmp")

    try:
        with open(tmp_path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, delimiter=DELIMITER)
            w.writerow(HEADER)
            for _ in range(copies):
                w.writerow(row)

        os.replace(tmp_path, final_path)

        msg = f"OK -> FILE={final_path} COPIES={copies}"
        
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
class WaitingLabelForm(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Print Form - Waiting Label")
        self.geometry("440x350")
        self.resizable(False, False)
        self.configure(bg="#f5f8fc")

        self.colors = {
            "navy": "#062445",
            "blue": "#0b5db3",
            "blue_dark": "#084a90",
            "text": "#071a33",
            "card": "#ffffff",
            "border": "#d3dce8",
            "subtext": "#5c6f84"
        }

        self.build_ui()

    def build_ui(self):
        # Header
        header = tk.Frame(self, bg=self.colors["navy"], height=55)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(
            header,
            text="Print - Waiting Label",
            font=("Segoe UI", 15, "bold"),
            bg=self.colors["navy"],
            fg="white"
        ).pack(side="left", padx=20, pady=12)

        # Main Card Container
        card = tk.Frame(
            self, 
            bg=self.colors["card"],
            highlightbackground=self.colors["border"],
            highlightthickness=1
        )
        card.pack(fill="both", expand=True, padx=20, pady=15)

        # Label Information Card (Visual grounding for single-variable forms)
        info_frame = tk.Frame(card, bg="#f8fafc", padx=12, pady=10)
        info_frame.pack(fill="x", padx=15, pady=(15, 10))

        tk.Label(
            info_frame, 
            text=f"Template:  {LABELFILE}", 
            font=("Segoe UI", 11, "bold"), 
            bg="#f8fafc", 
            fg=self.colors["text"],
            anchor="w"
        ).pack(fill="x")
        
        tk.Label(
            info_frame, 
            text=f"Printer:      {PRINTERNAME}", 
            font=("Segoe UI", 11), 
            bg="#f8fafc", 
            fg=self.colors["subtext"],
            anchor="w"
        ).pack(fill="x", pady=(2, 0))

        # Copy Count Selection Section
        copies_frame = tk.Frame(card, bg=self.colors["card"])
        copies_frame.pack(pady=12)

        tk.Label(
            copies_frame,
            text="Number of Copies:",
            font=("Segoe UI", 11, "bold"),
            bg=self.colors["card"],
            fg=self.colors["text"]
        ).pack(side="left", padx=(0, 10))

        self.copies_var = tk.StringVar(value="1")
        
        spin = ttk.Spinbox(
            copies_frame, 
            from_=1, 
            to=1000, 
            textvariable=self.copies_var, 
            font=("Segoe UI", 12, "bold"), 
            width=6,
            justify="center"
        )
        spin.pack(side="left")

        # Preset Quick Buttons
        preset_frame = tk.Frame(card, bg=self.colors["card"])
        preset_frame.pack(pady=(0, 15))
        
        for preset in [1, 2, 5, 10]:
            btn = tk.Button(
                preset_frame,
                text=f"{preset}x",
                font=("Segoe UI", 9),
                bg="#eef2f7",
                fg=self.colors["text"],
                activebackground=self.colors["border"],
                borderwidth=0,
                cursor="hand2",
                width=5,
                command=lambda val=preset: self.copies_var.set(str(val))
            )
            btn.pack(side="left", padx=4)

        # Buttons
        btn_frame = tk.Frame(self, bg="#f5f8fc")
        btn_frame.pack(fill="x", padx=20, pady=(0, 15))

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

    def execute_print(self):
        try:
            copies = int(self.copies_var.get().strip())
            if copies < 1:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid positive integer for print copies.")
            return

        success, msg = generate_print_file(copies)

        if success:
            messagebox.showinfo("Success", f"Sent {copies} copy/copies of Waiting Label to {PRINTERNAME}.")
            self.destroy()
        else:
            messagebox.showerror("Print Failed", f"An error occurred while generating the print file:\n\n{msg}")

if __name__ == "__main__":
    app = WaitingLabelForm()
    app.mainloop()