import pandas as pd
from pathlib import Path
import os

# ==========================================
# CONFIGURATION
# ==========================================

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
    header=1,
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