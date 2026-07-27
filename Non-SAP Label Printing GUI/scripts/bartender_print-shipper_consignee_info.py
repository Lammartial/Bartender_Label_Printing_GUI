import os
import csv
import time
from datetime import datetime, date

# =========================
# CONFIG (edit here)
# =========================

WATCHED_FOLDER = r"Z:"                  # <-- change to your watched folder
PRINT_FILE_EXT = "csv"                    # "csv" or "dat" or whatever BarTender Server accepts
DELIMITER = "\t"                          # TAB as break between the data ... usually "\t" if needed change to "," for real CSV

# Fixed print fields ... need to change when the layout and label fields change
PRINTERNAME = "LBL_PRINTER_WH_VN"
LABELFILE   = "Shipper_Consignee_information.BTW"
CONSIGNEE   = "RRC POWER SOLUTIONS GMBH"
CONSIGNEEADDRESS = "TECHNOLOGIEPARK 1, 66424 HOMBURG, GERMANY"
WEIGHT      = 120.6
UNIT        = "KG"

# Number of copies
PRINT_COPIES = 1  

# Log file (CSV)
LOG_FILE = r"C:\bt_watchedfolder_qr_print\qr_print_log.csv"

USE_ESC_KEY = False # if True use ESC key to stop (need admin rights) if False stop by pressing ESC and then pressing ENTER

# =========================
# END CONFIG (do not change something below!)
# =========================


HEADER = [
    "PRINTERNAME","LABELFILE","CONSIGNEE","CONSIGNEEADDRESS","WEIGHT","UNIT"
]

print("=== BarTender QR Print Tool ===")

# Ensure folders exist + log header
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
os.makedirs(WATCHED_FOLDER, exist_ok=True)

if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(["timestamp", "mundat", "expdat", "print_filename", "status", "message"])

print_filename = ""
mundat_str = ""
expdat_str = ""

try:

    row = [
        PRINTERNAME, LABELFILE, CONSIGNEE, CONSIGNEEADDRESS, WEIGHT, UNIT
    ]

    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    print_filename = f"print_{ts}.{PRINT_FILE_EXT}"

    final_path = os.path.join(WATCHED_FOLDER, print_filename)
    tmp_path = os.path.join(WATCHED_FOLDER, f".{print_filename}.tmp")

    with open(tmp_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=DELIMITER)
        w.writerow(HEADER)
        # w.writerow(row)
        for _ in range(PRINT_COPIES):
            w.writerow(row)

    os.replace(tmp_path, final_path)

    msg = f"OK -> MUNDAT={mundat_str} EXPDAT={expdat_str} FILE={final_path}"
    print(msg)

    with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([
            datetime.now().isoformat(timespec="seconds"),
            mundat_str,
            expdat_str,
            print_filename,
            "OK",
            msg
        ])

except Exception as e:
    msg = f"ERROR -> {e}"
    print(msg)
    with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([
            datetime.now().isoformat(timespec="seconds"),
            mundat_str,
            expdat_str,
            print_filename,
            "ERROR",
            str(e)
        ])

