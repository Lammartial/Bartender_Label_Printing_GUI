import os
import csv
import serial
from serial.tools import list_ports
import threading
import queue
from datetime import datetime, date
import tkinter as tk
from tkinter import messagebox, ttk
from tkcalendar import DateEntry

# =========================
# CONFIG 
# =========================
WATCHED_FOLDER = r"Z:"                  
PRINT_FILE_EXT = "csv"                    
DELIMITER = "\t"                          

PRINTERNAME = "UDI_PRINTER_VN"
LABELFILE   = "Incoming_material_label.BTW"
LOG_FILE = r"C:\bt_watchedfolder_qr_print\qr_print_log.csv"

# =========================
# ZEBRA DS22 SERIAL SCANNER
# =========================
# Leave this as None to let the program detect the scanner automatically.
# If a Zebra scanner is exposed by Windows as a serial device, the program
# will prefer it automatically.
SCANNER_PORT = None
SCANNER_BAUDRATE = 9600
SCANNER_TIMEOUT = 1
SCANNER_READ_INTERVAL_MS = 50
SCANNER_RECONNECT_DELAY_MS = 3000
ZEBRA_VENDOR_ID = 0x05E0

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

        # Scanner communication state
        self.scanner_queue = queue.Queue()
        self.scanner_stop_event = threading.Event()
        self.scanner_serial = None

        # Start Zebra DS22 serial scanner in the background
        self.start_scanner()

        # Check for scanned data without blocking the Tkinter GUI
        self.after(SCANNER_READ_INTERVAL_MS, self.process_scanner_queue)

        # Make sure the scanner thread is stopped when the window is closed
        self.protocol("WM_DELETE_WINDOW", self.on_close)

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

        self.scanner_status_var = tk.StringVar(value="Scanner: Detecting COM port...")
        tk.Label(
            header,
            textvariable=self.scanner_status_var,
            font=("Segoe UI", 9),
            bg=self.colors["navy"],
            fg="#d8e8ff"
        ).pack(side="right", padx=20, pady=20)

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

        # Standard Fields (Readonly set for requested fields)
        self.add_form_row(form_frame, 0, "Material No (MATNR):", "210838", "matnr", readonly=True)
        self.add_form_row(form_frame, 1, "Description (KTXT):", "Glue_FB300ZW (Konishi)", "ktxt", readonly=True)
        
        # WEDAT field defaults to today
        today = date.today()
        self.add_form_row(form_frame, 2, "Receipt Date (WEDAT):", today, "wedat", is_date=True)
        
        self.add_form_row(form_frame, 3, "PO Number (EBELN):", "7000000309", "ebeln")
        self.add_form_row(form_frame, 4, "PO Item (EBELP):", "0", "ebelp")
        self.add_form_row(form_frame, 5, "Quantity (BSTMG):", "10", "bstmg")
        self.add_form_row(form_frame, 6, "Unit (BSTME):", "PCS", "bstme", readonly=True)
        self.add_form_row(form_frame, 7, "Storage Loc (LGORT):", "0028", "lgort", readonly=True)
        self.add_form_row(form_frame, 8, "Location (SSNA):", "WH2-MAT-FEFO-R6", "ssna", readonly=True)
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

    # =========================
    # ZEBRA DS22 SCANNER
    # =========================
    def start_scanner(self):
        """Start the Zebra DS22 serial scanner listener in a background thread."""
        self.scanner_thread = threading.Thread(
            target=self.scanner_worker,
            daemon=True
        )
        self.scanner_thread.start()

    def find_scanner_ports(self):
        """
        Detect the most likely COM port for the Zebra scanner.

        Detection priority:
        1. Explicit SCANNER_PORT, if configured.
        2. Zebra USB vendor ID / Zebra-related device information.
        3. If only one COM port exists, use that port.
        4. Otherwise return no port because blindly opening an arbitrary COM
           port could interfere with another serial device.
        """
        try:
            ports = list(list_ports.comports())
        except Exception:
            return []

        if not ports:
            return []

        # Manual override remains available for unusual installations.
        if SCANNER_PORT:
            available = {p.device for p in ports}
            if SCANNER_PORT in available:
                return [SCANNER_PORT]

        zebra_ports = []

        for port in ports:
            device_text = " ".join([
                str(getattr(port, "description", "") or ""),
                str(getattr(port, "manufacturer", "") or ""),
                str(getattr(port, "product", "") or ""),
                str(getattr(port, "hwid", "") or "")
            ]).lower()

            is_zebra = (
                getattr(port, "vid", None) == ZEBRA_VENDOR_ID
                or "zebra" in device_text
                or "symbol" in device_text
                or "barcode scanner" in device_text
                or "barcode" in device_text
            )

            if is_zebra:
                zebra_ports.append(port.device)

        if zebra_ports:
            return zebra_ports

        # Safe fallback: if this PC has exactly one COM port, it is very
        # likely to be the scanner in a dedicated label-printing workstation.
        if len(ports) == 1:
            return [ports[0].device]

        return []

    def scanner_worker(self):
        """Continuously detect and read QR/barcode data from the Zebra DS22."""

        while not self.scanner_stop_event.is_set():
            ser = None

            detected_ports = self.find_scanner_ports()

            if not detected_ports:
                try:
                    available = [p.device for p in list_ports.comports()]
                except Exception:
                    available = []

                if available:
                    self.scanner_queue.put((
                        "status",
                        "Scanner: COM port not uniquely identified"
                    ))
                else:
                    self.scanner_queue.put((
                        "status",
                        "Scanner: No COM port detected"
                    ))

                self.scanner_stop_event.wait(
                    SCANNER_RECONNECT_DELAY_MS / 1000
                )
                continue

            # Normally there will be one Zebra port. If several are exposed
            # by Zebra software, try them in the order returned by Windows.
            connected = False

            for port_name in detected_ports:
                if self.scanner_stop_event.is_set():
                    break

                try:
                    ser = serial.Serial(
                        port=port_name,
                        baudrate=SCANNER_BAUDRATE,
                        bytesize=serial.EIGHTBITS,
                        parity=serial.PARITY_NONE,
                        stopbits=serial.STOPBITS_ONE,
                        timeout=SCANNER_TIMEOUT
                    )

                    self.scanner_serial = ser
                    ser.reset_input_buffer()
                    connected = True

                    self.scanner_queue.put((
                        "status",
                        f"Scanner: Connected ({port_name})"
                    ))

                    while not self.scanner_stop_event.is_set():
                        if ser.in_waiting > 0:
                            raw_data = ser.readline()

                            scanned_data = raw_data.decode(
                                "utf-8",
                                errors="ignore"
                            ).strip()

                            if scanned_data:
                                self.scanner_queue.put((
                                    "scan",
                                    scanned_data
                                ))

                        # Avoid unnecessary CPU usage.
                        self.scanner_stop_event.wait(0.05)

                    break

                except serial.SerialException:
                    # This port could be busy or disappear. Try the next
                    # detected candidate.
                    self.scanner_serial = None

                except Exception as e:
                    self.scanner_serial = None
                    self.scanner_queue.put((
                        "status",
                        f"Scanner error on {port_name}: {e}"
                    ))

                finally:
                    if ser is not None:
                        try:
                            if ser.is_open:
                                ser.close()
                        except Exception:
                            pass
                        ser = None

                    self.scanner_serial = None

            if not connected and not self.scanner_stop_event.is_set():
                self.scanner_queue.put((
                    "status",
                    "Scanner: Unable to open detected COM port - retrying..."
                ))

                self.scanner_stop_event.wait(
                    SCANNER_RECONNECT_DELAY_MS / 1000
                )

    def process_scanner_queue(self):
        """Process scanner messages safely on the Tkinter main thread."""
        try:
            while True:
                message_type, value = self.scanner_queue.get_nowait()

                if message_type == "status":
                    self.scanner_status_var.set(value)

                elif message_type == "scan":
                    # Put scanner data into the same GUI field used for manual entry
                    self.fields["scan_text"].set(value)
                    self.scan_entry.focus_set()

                    # Automatically print once the scan is received
                    self.execute_print()

        except queue.Empty:
            pass

        # Keep polling while the GUI is running
        if not self.scanner_stop_event.is_set():
            self.after(SCANNER_READ_INTERVAL_MS, self.process_scanner_queue)

    def on_close(self):
        """Stop the scanner thread and close the application cleanly."""
        self.scanner_stop_event.set()

        if self.scanner_serial is not None:
            try:
                if self.scanner_serial.is_open:
                    self.scanner_serial.close()
            except Exception:
                pass

        self.destroy()

    def add_form_row(self, parent, row, label_text, default_val, key, is_number=False, readonly=False, is_date=False):
        tk.Label(
            parent,
            text=label_text,
            font=("Segoe UI", 10, "bold"),
            bg=self.colors["card"],
            fg=self.colors["text"],
            anchor="e"
        ).grid(row=row, column=0, sticky="e", pady=8, padx=(15, 5))

        if is_date:
            # Set to a standard format with separators so the UI doesn't crash
            entry = DateEntry(parent, font=("Segoe UI", 10), width=26, date_pattern='dd/mm/yyyy')
            entry.set_date(default_val)
        else:
            var = tk.StringVar(value=default_val)
            
            if is_number:
                entry = ttk.Spinbox(parent, from_=1, to=1000, textvariable=var, font=("Segoe UI", 10), width=5)
            else:
                entry = ttk.Entry(parent, textvariable=var, font=("Segoe UI", 10), width=28)
                if readonly:
                    entry.config(state="readonly")
            
        entry.grid(row=row, column=1, sticky="w", pady=8, padx=(5, 15))
        
        if is_date:
            self.fields[key] = entry
        else:
            self.fields[key] = var

    def execute_print(self):
        # Extract data from fields
        current_data = {}
        for key, var in self.fields.items():
            if isinstance(var, DateEntry):
                # This pulls the date object and converts it to strictly YYYYMMDD for Bartender
                current_data[key] = var.get_date().strftime("%Y%m%d")
            else:
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