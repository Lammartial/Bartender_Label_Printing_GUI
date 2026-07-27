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
LABELFILE   = "Incoming_material_label.BTW"
MATNR       = "210838"
KTXT        = "Glue_FB300ZW (Konishi)"
WEDAT       = "20251009"  #20250324  #20250324  #20240905
EBELN       = "7000000309"  #7000000246 #7000000246  #7000000150
EBELP       = "0"
BSTMG       = "10"
BSTME       = "PCS"
LGORT       = "0028" 
SSNA        = "WH2-MAT-FEFO-R6"

# Number of copies
PRINT_COPIES = 1       

# Log file (CSV)
LOG_FILE = r"C:\bt_watchedfolder_qr_print\qr_print_log.csv"

USE_ESC_KEY = False # if True use ESC key to stop (need admin rights) if False stop by pressing ESC and then pressing ENTER

# =========================
# END CONFIG (do not change something below!)
# =========================

HEADER = [
    "PRINTERNAME","LABELFILE","MATNR","KTXT","WEDAT","EBELN","EBELP",
    "BSTMG","BSTME","LGORT","SSNA","EXPDAT","MUNDAT"
]

def add_one_year_keep_day_month(d: date) -> date:
    """Add +1 year and keep day/month the same (Feb 29 -> Feb 28 if needed)."""
    try:
        return date(d.year + 1, d.month, d.day)
    except ValueError:
        # handles leap day (29.02) when next year is not a leap year
        return date(d.year + 1, 2, 28)

print("=== BarTender QR Print Tool ===")
print("Scan a QR code now (scanner must send ENTER).")
print("Type 'end' and press ENTER to stop.")

# Ensure folders exist + log header
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
os.makedirs(WATCHED_FOLDER, exist_ok=True)

if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(["timestamp", "scan_text", "mundat", "expdat", "print_filename", "status", "message"])

while True:
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    scan_text = input(f"[{now_str}] Scan (or type 'end' to stop): ").strip()

    if scan_text.lower() == "end":
        print("Stopping.")
        break

    print_filename = ""
    mundat_str = ""
    expdat_str = ""

    try:
        if len(scan_text) < 8:
            raise ValueError("Scan too short (< 8 characters).")

        tail8 = scan_text[-8:]   # e.g. 250708AA
        yymmdd = tail8[:6]       # e.g. 250708

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
            PRINTERNAME, LABELFILE, MATNR, KTXT, WEDAT, EBELN, EBELP,
            BSTMG, BSTME, LGORT, SSNA, expdat_str, mundat_str
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
                scan_text,
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
                scan_text,
                mundat_str,
                expdat_str,
                print_filename,
                "ERROR",
                str(e)
            ])

    time.sleep(0.05)
