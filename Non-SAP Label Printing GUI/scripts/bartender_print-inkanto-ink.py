import os
import csv
import time
import re
import urllib.request
from datetime import datetime, date

# =========================
# CONFIG (edit here)
# =========================

WATCHED_FOLDER = r"Z:"                  # <-- change to your watched folder
PRINT_FILE_EXT = "csv"                    # "csv" or "dat" or whatever BarTender Server accepts
DELIMITER = "\t"                          # TAB as break between the data ... usually "\t" if needed change to "," for real CSV

'''
| Part code | Part name                                | Stock in WH |
| 212875    | Therm.Trans.Ribbon Armor AXR7+75mm_300m  | 30          |
| 212112    | Therm.Trans.Ribbon Armor AXR7+110mm_300m | 10          |   
'''

# Fixed print fields ... need to change when the layout and label fields change
PRINTERNAME = "LBL_PRINTER_WH_VN"
LABELFILE   = "Incoming_material_label.BTW"
MATNR       = "212112"     #212875
KTXT        = "Therm.Trans.Ribbon Armor AXR7+110mm_300m"   #75mm
WEDAT       = "20251009"  
EBELN       = "7000000309"  
EBELP       = "0"
BSTMG       = "1"
BSTME       = "PCS"
LGORT       = "0027"  
SSNA        = "WH2-MAT-FLOW-R5"

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


print("=== BarTender Print Tool ===")
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
        # ---- manufacturing date comes from the website from the inkanto QR code label = URL !!!           ----
        # ---- example scanned by cellphone: https://coc.inkanto.com/c?a=07474448701&b=TSA749IO&c=250510172 ----
        if not scan_text.lower().startswith(("http://", "https://")):
            raise ValueError("Input is not a URL (expected https://... from the QR code).")

        req = urllib.request.Request(
            scan_text,
            headers={"User-Agent": "Mozilla/5.0"}  # helps avoid simple blocking ... proposal from another application, hope it works :)
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="ignore")

        m = re.search(
            r'Manufacturing Date:\s*</span>\s*<span[^>]*class="specifications__value"[^>]*>\s*([0-9]{2}/[0-9]{2}/[0-9]{4})\s*</span>',
            html,
            flags=re.IGNORECASE | re.DOTALL
        )
        if not m:
            raise ValueError("Manufacturing Date not found on website (HTML pattern not matched).")

        manu_text = m.group(1)  # e.g. "05/03/2026"

        # Parse manufacturing date (assume dd/mm/yyyy; must be checked from time to time in case they change the website)
        p1, p2, p3 = manu_text.split("/")
        a = int(p1)
        b = int(p2)
        y = int(p3)

        if a > 12:
            dd, mm = a, b           # dd/mm/yyyy
        elif b > 12:
            dd, mm = b, a           # mm/dd/yyyy 
        else:
            dd, mm = a, b           # assume dd/mm/yyyy

        manu = date(y, mm, dd)
        exp = add_one_year_keep_day_month(manu)

        mundat_str = manu.strftime("%Y%m%d")
        expdat_str = exp.strftime("%Y%m%d")
        # ---- END "NEW PART" = get website data ----

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
