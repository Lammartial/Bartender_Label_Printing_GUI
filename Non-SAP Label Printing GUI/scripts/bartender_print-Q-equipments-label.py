import os
import csv
from datetime import datetime

# =========================
# CONFIG (edit here)
# =========================

WATCHED_FOLDER = r"Z:"                  # <-- change to your watched folder
PRINT_FILE_EXT = "csv"                  # "csv" or "dat" or whatever BarTender accepts
DELIMITER = "\t"                        # Tab-separated values

# Fixed print fields
PRINTERNAME = "LBL_PRINTER_WH_VN"
LABELFILE = "Measuring Equipment Label_18x38mm.BTW"

# =========================
# DATA TO PRINT
# =========================
# Each dictionary in this list represents ONE printed label.
#
# IMPORTANT:
# The field names below must EXACTLY match the database field names
# configured in your BarTender BTW file.

PRINT_JOBS = [
    {
        "QUALITY_EQUIPMENT_NO": "RRC_Q_0001",
        "INVENTORY_NUMBER": "8400001",
    },
    {
        "QUALITY_EQUIPMENT_NO": "RRC_Q_0002",
        "INVENTORY_NUMBER": "8400002",
    }
]

# =========================
# LOG FILE
# =========================

LOG_FILE = r"C:\bt_watchedfolder_qr_print\qr_print_log.csv"

# =========================
# END CONFIG
# =========================


# Database fields used by the BarTender CSV/TSV file.
#
# IMPORTANT:
# These names must exactly match the database fields configured
# in your BarTender BTW database connection.

DATABASE_FIELDS = [
    "QUALITY_EQUIPMENT_NO",   # "Mã số thiết bị Chất lượng[Q-ID]"
    "INVENTORY_NUMBER",    # "Mã số tài sản[Inventory Number]"
]

# Final CSV/TSV header.
# PRINTERNAME and LABELFILE are used by the BarTender Integration.
HEADER = [
    "PRINTERNAME",
    "LABELFILE"
] + DATABASE_FIELDS


print("=== BarTender QR Print Tool ===")

# =========================
# PREPARE FOLDERS AND LOG
# =========================

os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
os.makedirs(WATCHED_FOLDER, exist_ok=True)

if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([
            "timestamp",
            "print_filename",
            "status",
            "message",
            "jobs_printed"
        ])


# =========================
# CREATE PRINT FILE
# =========================

print_filename = ""

try:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    print_filename = f"print_{ts}.{PRINT_FILE_EXT}"

    final_path = os.path.join(
        WATCHED_FOLDER,
        print_filename
    )

    tmp_path = os.path.join(
        WATCHED_FOLDER,
        f".{print_filename}.tmp"
    )

    # utf-8-sig adds the UTF-8 BOM.
    # This helps applications such as BarTender correctly detect
    # Vietnamese/Unicode characters if they are ever used in values.
    with open(
        tmp_path,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=HEADER,
            delimiter=DELIMITER,
            extrasaction="raise"
        )

        # Write header
        writer.writeheader()

        # Write each label/job
        for job_data in PRINT_JOBS:

            # Make a copy so the original PRINT_JOBS data is not modified.
            row = job_data.copy()

            # Add fixed BarTender Integration fields.
            row["PRINTERNAME"] = PRINTERNAME
            row["LABELFILE"] = LABELFILE

            # Write one row = one printed label
            writer.writerow(row)

    # Atomically rename temporary file to final file.
    # This prevents BarTender from detecting the file before
    # Python has finished writing it.
    os.replace(
        tmp_path,
        final_path
    )

    msg = (
        f"OK -> FILE={final_path} "
        f"JOBS={len(PRINT_JOBS)}"
    )

    print(msg)

    # Write successful result to log.
    with open(
        LOG_FILE,
        "a",
        newline="",
        encoding="utf-8"
    ) as f:

        csv.writer(f).writerow([
            datetime.now().isoformat(timespec="seconds"),
            print_filename,
            "OK",
            msg,
            len(PRINT_JOBS)
        ])


except Exception as e:

    msg = f"ERROR -> {e}"

    print(msg)

    # Write error result to log.
    with open(
        LOG_FILE,
        "a",
        newline="",
        encoding="utf-8"
    ) as f:

        csv.writer(f).writerow([
            datetime.now().isoformat(timespec="seconds"),
            print_filename,
            "ERROR",
            str(e),
            0
        ])