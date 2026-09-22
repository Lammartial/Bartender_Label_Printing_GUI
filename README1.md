# RRC VN Non-SAP BarTender Label Printing Suite

A modular Python desktop application suite developed for RRC Vietnam to streamline label generation and printing via BarTender Integration Builder. The suite features a central Master Launcher GUI that spawns independent, specialized print GUI sub-scripts in isolated processes to handle specific label workflows, web-scraping logic, database lookups, and batch generation.

**Central SharePoint Repository Path:**

`Shared Documents/ 999_SHARE_VN/ 290_IT/ Non-SAP Label Printing GUI`

---

## Directory Structure

```text
project-root/
│
├── bartender_watch/                # Directory monitored by BarTender Integration for drop-files (Mapped to Z:\)
├── databases/                      # CSV databases for label field population
│   ├── WH Slog 2.csv               # Static database for Flowrack labels
│   ├── Equipment_DB.csv            # Dynamic database for Quality Equipment labels
│   └── Fixture-Jig_DB.csv          # Dynamic database for Fixture/Jig labels
├── images/                         # UI icons, logos, and label sample preview images
├── scripts/                        # Sub-process label scripts executed by the launcher
│   ├── bartender_print_q_equipments.py # Quality Equipment label generator
│   ├── bartender_print_incoming_ttr.py # Incoming Material (TTR) label generator with web-scraping
│   └── ...                         # Additional specialized label scripts
│
├── rrc_vn_label_printing_gui_v1.py # Main Master Launcher GUI (standard Python source)
├── RRCVN Label Printing GUI.pyw    # Windowed Master Launcher GUI (suppresses console window)
├── README.md
└── .gitignore

```

> **Note on Dynamic Databases:** `Equipment_DB.csv` and `Fixture-Jig_DB.csv` are dynamically generated from `600_Quality/640_Q-Equipments/Q-Equipments-Overview.xlsx`.

---

## Architecture Overview

```text
[Client PC]                                           [SharePoint / Local App]                                 [BarTender Server: 172.25.5.9]
┌──────────────────────────┐        ┌──────────────────────────────────────────┐        ┌──────────────────────────────────────────┐
│  Python (Company Portal) │        │  RRCVN Label Printing GUI (.pyw)         │        │  Z:\ (\\172.25.5.9\bartender_watch)      │
│  Mapped Drive Z:         ├───────►│  - Spawns scripts/ in separate processes ├───────►│  - sample.csv / sample_static.csv        │
└──────────────────────────┘        └────────────────────┬─────────────────────┘        │  - Generated print_*.csv drop-files      │
                                                         │                              │  - *.BTW Templates                       │
                                                         ▼                              │  - BarTender Integration Builder         │
                                            ┌──────────────────────────┐                └────────────────────┬─────────────────────┘
                                            │  scripts/ (Single GUIs)  │                                     │
                                            │  databases/ (*.csv)      │                                     ▼
                                            │  images/ (Previews)      │                              [UDI_PRINTER_VN]
                                            └──────────────────────────┘

```

* **Master Launcher (`rrc_vn_label_printing_gui_v1.py` / `RRCVN Label Printing GUI.pyw`)**: Central control panel for selecting and opening required label printing forms.


* **Child Script Modules (`scripts/`)**: Modular Python scripts executing independently. Each handles unique form validation, web scraping, or database lookups before generating BarTender drop-files.


* **Watched Directory (`bartender_watch/` / Drive `Z:`)**: Network share where generated print trigger files are saved for BarTender Integration Builder to process and automatically route to printers.



---

## Key Features

* **Centralized Application Hub**: Launch any factory label form from a single desktop dashboard.


* **Process Isolation**: Each label module runs in its own subprocess, preventing errors in one module from crashing the entire application suite.


* **Web Scraping & Auto-Date Calculation**: Automatically fetches dynamic data (e.g., scanning Inkanto QR URLs via `urllib` and parsing Manufacturing Date via regex to calculate Expiration Date = Mfg Date + 1 Year).
* **Flexible Database Lookup**: Supports both static CSVs (`WH Slog 2.csv`) and dynamic databases generated from Excel overviews (`Q-Equipments-Overview.xlsx`).
* **Atomic File Writing**: Writes drop-data to a temporary file (`.print_*.tmp`) first before atomically renaming to `.csv` to prevent BarTender from reading incomplete files during write operations.


* **Client Execution Logging**: Logs execution timestamps, scanned URLs, calculated dates, file paths, status (`OK`/`ERROR`), and job details to `C:\bt_watchedfolder_qr_print\qr_print_log.csv`.

---

## Prerequisites & Workstation Setup

1. **Python 3.x**: Ensure Python is installed on the local client machine (installed via **Company Portal**).
2. **Map Network Drive `Z:**`:
* **Target Path**: `\\172.25.5.9\bartender_watch`
* **Credentials** (Stored in IT KeePass):
* **Quality Team**: Use account `BartenderQuality`
* **Warehouse Team**: Use account `BartenderWarehouse`





---

## Configuration & Database Setup

### 1. Database Configuration (`databases/`)

Lookup files in `databases/` must remain **tab-delimited** (`\t`) CSV format matching the exact header names expected by BarTender `.BTW` templates:

```text
QUALITY_EQUIPMENT_NO	INVENTORY_NUMBER
RRC_Q_0001	8400001
RRC_Q_0002	8400002

```

### 2. Output & Printer Paths

Ensure script header configurations point to mapped network drive `Z:` and specify target factory printers:

```python
# Directory monitored by BarTender Integration
WATCHED_FOLDER = r"Z:"
PRINT_FILE_EXT = "csv"
DELIMITER = "\t"

# Target Printer & Template Settings
PRINTERNAME = "UDI_PRINTER_VN"
LABELFILE   = "Incoming_material_label.BTW"

# Client Log Path
LOG_FILE = r"C:\bt_watchedfolder_qr_print\qr_print_log.csv"

```

---

## How to Run

### Option A: Direct Windowed Execution (Recommended for Users)

Double-click **`RRCVN Label Printing GUI.pyw`**. Running via `.pyw` launches the interface cleanly without displaying an extra command prompt window.

### Option B: Command Line Execution (Development / Debugging)

Run the launcher script using Python from the project root directory:

```bash
python rrc_vn_label_printing_gui_v1.py

```

---

## BarTender Integration & File Details

1. **Encoding**: Drop-files written to `Z:\` are exported using **UTF-8 with BOM** encoding (`utf-8-sig`) to preserve special characters.


2. **Drop-File Data Format**:
```text
PRINTERNAME	LABELFILE	MATNR	KTXT	WEDAT	EBELN	EBELP	BSTMG	BSTME	LGORT	SSNA	EXPDAT	MUNDAT
UDI_PRINTER_VN	Incoming_material_label.BTW	212875	Therm.Trans.Ribbon Armor AXR7+75mm_300m	20260922	7000000309	0	1	PCS	0027	WH2-MAT-FLOW-R5	20270305	20260305

```


3. **Execution Logs**: Detailed local execution records are maintained at `C:\bt_watchedfolder_qr_print\qr_print_log.csv` on the user's workstation.