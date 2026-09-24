import os
import csv
import re
import urllib.request
import serial
import threading
import queue
from serial.tools import list_ports
from datetime import datetime, date
import tkinter as tk
from tkinter import messagebox, ttk
from tkcalendar import DateEntry

# pyserial is required for Zebra DS22 COM-port scanning.
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
# The scanner COM port is detected automatically.
# No fixed COM number is required.
SCANNER_BAUDRATE = 9600
SCANNER_TIMEOUT = 1
SCANNER_READ_INTERVAL = 0.05
SCANNER_RECONNECT_DELAY = 3.0

# Zebra Technologies USB vendor ID.
# This is used when Windows exposes the scanner/USB interface as Zebra.
ZEBRA_VENDOR_ID = 0x05E0
ZEBRA_KEYWORDS = (
    "zebra",
    "symbol",
    "barcode scanner",
)

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


def detect_scanner_port():
    """
    Automatically detect the Zebra DS22 COM port.

    Detection order:
    1. Zebra USB vendor ID (05E0)
    2. Zebra/Symbol/Barcode Scanner keywords in Windows port information
    3. If only one COM port exists, use that port as a fallback

    Returns:
        str | None: Detected COM port such as 'COM18', or None.
    """
    try:
        ports = list(list_ports.comports())
    except Exception:
        return None

    if not ports:
        return None

    # Prefer a clearly identified Zebra scanner/USB serial device.
    zebra_candidates = []

    for port in ports:
        device = getattr(port, "device", "") or ""
        description = getattr(port, "description", "") or ""
        manufacturer = getattr(port, "manufacturer", "") or ""
        product = getattr(port, "product", "") or ""
        hwid = getattr(port, "hwid", "") or ""
        vid = getattr(port, "vid", None)

        combined = " ".join([
            str(device),
            str(description),
            str(manufacturer),
            str(product),
            str(hwid),
        ]).lower()

        is_zebra = (
            vid == ZEBRA_VENDOR_ID
            or any(keyword in combined for keyword in ZEBRA_KEYWORDS)
        )

        if is_zebra:
            zebra_candidates.append(device)

    if zebra_candidates:
        return zebra_candidates[0]

    # Safe fallback:
    # If there is exactly one COM port, assume it is the scanner.
    if len(ports) == 1:
        return ports[0].device

    # Multiple unidentified COM ports:
    # Do not randomly connect to one.
    return None

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

        self.build_ui()

        # =========================
        # SCANNER COMMUNICATION
        # =========================
        self.scanner_queue = queue.Queue()
        self.scanner_stop_event = threading.Event()
        self.scanner_serial = None
        self.scanner_port = None

        # Start Zebra DS22 scanner listener
        self.start_scanner()

        # Process scanner messages safely on the Tkinter main thread
        self.after(50, self.process_scanner_queue)

        # Cleanly close scanner when the user closes the GUI
        self.protocol("WM_DELETE_WINDOW", self.on_close)

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

        # Scanner connection status
        self.scanner_status_var = tk.StringVar(
            value="Scanner: Detecting..."
        )

        tk.Label(
            header,
            textvariable=self.scanner_status_var,
            font=("Segoe UI", 9),
            bg=self.colors["navy"],
            fg="#d8e8ff"
        ).pack(
            side="right",
            padx=20,
            pady=20
        )

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

        # Standard Fields (Identical to previous configuration)
        self.add_form_row(form_frame, 0, "Material No (MATNR):", "212875", "matnr", readonly=True)
        self.add_form_row(form_frame, 1, "Description (KTXT):", "Therm.Trans.Ribbon Armor AXR7+75mm_300m", "ktxt", readonly=True)
        
        # WEDAT field defaults to today utilizing tkcalendar 
        today = date.today()
        self.add_form_row(form_frame, 2, "Receipt Date (WEDAT):", today, "wedat", is_date=True)
        
        self.add_form_row(form_frame, 3, "PO Number (EBELN):", "7000000309", "ebeln")
        self.add_form_row(form_frame, 4, "PO Item (EBELP):", "0", "ebelp")
        self.add_form_row(form_frame, 5, "Quantity (BSTMG):", "1", "bstmg", readonly=True)
        self.add_form_row(form_frame, 6, "Unit (BSTME):", "PCS", "bstme", readonly=True)
        self.add_form_row(form_frame, 7, "Storage Loc (LGORT):", "0027", "lgort", readonly=True)
        self.add_form_row(form_frame, 8, "Location (SSNA):", "WH2-MAT-FLOW-R5", "ssna", readonly=True)
        self.add_form_row(form_frame, 9, "Number of Copies:", "1", "copies", is_number=True)

        tk.Frame(form_frame, bg=self.colors["border"], height=1).grid(row=10, column=0, columnspan=2, sticky="ew", pady=10)

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
        self.scan_entry = ttk.Entry(form_frame, textvariable=scan_var, font=("Segoe UI", 12), width=25)
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
            command=self.on_close,
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

    def scanner_worker(self):
        """
        Continuously detect and read QR/barcode data from the Zebra DS22.

        Communication:
        9600 baud
        8 data bits
        No parity
        1 stop bit

        Tkinter is not touched from this worker thread.
        Scanner messages are placed into self.scanner_queue instead.
        """

        while not self.scanner_stop_event.is_set():

            ser = None

            try:
                # Detect the COM port dynamically every time we reconnect.
                detected_port = detect_scanner_port()

                if not detected_port:
                    self.scanner_queue.put(
                        (
                            "status",
                            "Scanner: COM port not detected - retrying..."
                        )
                    )

                    self.scanner_stop_event.wait(
                        SCANNER_RECONNECT_DELAY
                    )
                    continue

                # Connect to the detected scanner
                ser = serial.Serial(
                    port=detected_port,
                    baudrate=SCANNER_BAUDRATE,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=SCANNER_TIMEOUT
                )

                self.scanner_serial = ser
                self.scanner_port = detected_port

                # Remove anything left in the receive buffer
                ser.reset_input_buffer()

                self.scanner_queue.put(
                    (
                        "status",
                        f"Scanner: Connected ({detected_port})"
                    )
                )

                # =========================
                # READ SCANNER DATA
                # =========================
                while not self.scanner_stop_event.is_set():

                    if ser.in_waiting > 0:

                        raw_data = ser.readline()

                        scanned_data = raw_data.decode(
                            "utf-8",
                            errors="ignore"
                        ).strip()

                        if scanned_data:
                            self.scanner_queue.put(
                                (
                                    "scan",
                                    scanned_data
                                )
                            )

                    # Avoid unnecessary CPU usage
                    self.scanner_stop_event.wait(
                        SCANNER_READ_INTERVAL
                    )

            except serial.SerialException:
                self.scanner_serial = None

                if self.scanner_port:
                    status_text = (
                        f"Scanner: Disconnected ({self.scanner_port}) - retrying..."
                    )
                else:
                    status_text = (
                        "Scanner: Serial connection failed - retrying..."
                    )

                self.scanner_port = None

                self.scanner_queue.put(
                    (
                        "status",
                        status_text
                    )
                )

                self.scanner_stop_event.wait(
                    SCANNER_RECONNECT_DELAY
                )

            except Exception as e:
                self.scanner_serial = None
                self.scanner_port = None

                self.scanner_queue.put(
                    (
                        "status",
                        f"Scanner error: {e}"
                    )
                )

                self.scanner_stop_event.wait(
                    SCANNER_RECONNECT_DELAY
                )

            finally:
                if ser is not None:
                    try:
                        if ser.is_open:
                            ser.close()
                    except Exception:
                        pass

                self.scanner_serial = None

    def process_scanner_queue(self):
        """
        Process scanner messages from the worker thread on the Tkinter
        main thread so GUI widgets remain thread-safe.
        """

        try:
            while True:

                message_type, value = self.scanner_queue.get_nowait()

                # =========================
                # SCANNER STATUS
                # =========================
                if message_type == "status":

                    if hasattr(self, "scanner_status_var"):
                        self.scanner_status_var.set(value)

                # =========================
                # SCANNED QR/BARCODE
                # =========================
                elif message_type == "scan":

                    # Put scanned URL into the existing scan field
                    self.fields["scan_text"].set(value)

                    # Keep scanner input focused
                    self.scan_entry.focus_set()

                    # Automatically execute the existing print routine
                    self.execute_print()

        except queue.Empty:
            pass

        # Continue monitoring the scanner queue
        if not self.scanner_stop_event.is_set():

            self.after(
                50,
                self.process_scanner_queue
            )

    def on_close(self):
        """Stop the scanner thread and close the GUI cleanly."""

        self.scanner_stop_event.set()

        if self.scanner_serial is not None:

            try:
                if self.scanner_serial.is_open:
                    self.scanner_serial.close()
            except Exception:
                pass

        self.destroy()

    def execute_print(self):
        current_data = {}
        for key, var in self.fields.items():
            if isinstance(var, DateEntry):
                # Formats to strictly YYYYMMDD 
                current_data[key] = var.get_date().strftime("%Y%m%d")
            else:
                current_data[key] = var.get().strip()

        try:
            current_data["copies"] = int(current_data["copies"])
            if current_data["copies"] < 1:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Input", "Number of copies must be a positive integer.")
            self.scan_entry.focus_set()
            return

        # Ensure form is complete before printing
        if not all([current_data["matnr"], current_data["ktxt"], current_data["scan_text"]]):
            messagebox.showwarning("Missing Data", "Please fill out all required fields and ensure a QR URL is scanned.")
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