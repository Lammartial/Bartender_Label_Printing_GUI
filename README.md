# RRC VN BarTender Label Printing Suite

A modular Python desktop application suite developed for RRC Vietnam to streamline label generation and printing via BarTender Integration Builder. The suite features a central Master Launcher GUI that spawns independent, specialized print GUI sub-scripts in isolated processes to handle specific label workflows, database lookups, and batch generation.

---

## Directory Structure

```text
project-root/
│
├── bartender_watch/                # Directory monitored by BarTender Integration for drop-files
├── databases/                      # Local CSV lookup databases (e.g., Equipment_DB.csv)
├── images/                         # UI icons, logos, and graphic assets
├── scripts/                        # Sub-process label scripts executed by the launcher
│   ├── bartender_print_q_equipments.py # Quality Equipment label generator
│   └── ...                         # Additional specialized label scripts
│
├── rrc_vn_label_printing_gui_v1.py # Main Master Launcher GUI (standard Python source)
├── RRCVN Label Printing GUI.pyw    # Windowed Master Launcher GUI (suppresses console window)
├── README.md
└── .gitignore

```

---

## Architecture Overview

```text
               ┌──────────────────────────────────────────────────┐
               │  rrc_vn_label_printing_gui_v1.py / .pyw          │
               │               (Master Launcher GUI)              │
               └────────────────────────┬─────────────────────────┘
                                        │
           ┌────────────────────────────┼────────────────────────────┐
           ▼                            ▼                            ▼
┌─────────────────────┐      ┌─────────────────────┐      ┌─────────────────────┐
│  Q-Equipment Print  │      │ Material TTR Print  │      │ Other Label Module  │
│  Script (scripts/)  │      │ Script (scripts/)   │      │ Script (scripts/)   │
└──────────┬──────────┘      └──────────┬──────────┘      └──────────┬──────────┘
           │                            │                            │
           └────────────────────────────┼────────────────────────────┘
                                        ▼
                     ┌────────────────────────────────────┐
                     │     bartender_watch/ Folder        │
                     │          (*.csv / *.tsv)           │
                     └────────────────────────────────────┘

```

* **Master Launcher (`rrc_vn_label_printing_gui_v1.py` / `RRCVN Label Printing GUI.pyw`)**: Central control panel for selecting and opening required label printing forms.
* **Child Script Modules (`scripts/`)**: Modular Python scripts executing independently. Each handles unique form validation, web scraping, or database lookups before generating BarTender drop-files.
* **Watched Directory (`bartender_watch/`)**: Destination folder where generated print trigger files are saved for BarTender to process and print automatically.

---

## Features

* **Centralized Application Hub**: Launch any factory label form from a single desktop dashboard.
* **Process Isolation**: Each label module runs in its own subprocess, preventing errors in one module from crashing the entire application suite.
* **Dual Printing Modes (Measuring Equipment Module)**:
* **Option 1 (Batch Print)**: Instant generation of print jobs using pre-configured equipment arrays.
* **Option 2 (Database Lookup)**: Real-time form interface that automatically fills inventory details upon typing or scanning a **Quality Equipment No**.


* **Atomic File Writing**: Generates temporary `.tmp` files during CSV construction and atomically renames them to `.csv` to prevent BarTender from reading incomplete files.
* **Automated Logging**: Centralized logging system recording timestamps, output file paths, status (`OK`/`ERROR`), and printed job counts to `qr_print_log.csv`.

---

## Prerequisites

* **Python**: 3.8 or higher
* **BarTender Suite**: Installed on the printing host machine with **Integration Builder** actively monitoring the `bartender_watch/` folder.
* **Standard Python Libraries**: `os`, `sys`, `csv`, `subprocess`, `datetime`, `tkinter`, `ttk`.

---

## Configuration & Database Setup

### 1. Database Configuration (`databases/`)

Store lookup files in tab-delimited (`\t`) CSV format matching the exact database header names used by BarTender `.BTW` files:

```text
QUALITY_EQUIPMENT_NO	INVENTORY_NUMBER
RRC_Q_0001	8400001
RRC_Q_0002	8400002

```

### 2. Output & Printer Paths

Ensure the paths configured in script files point to the local `bartender_watch` directory:

```python
# Directory monitored by BarTender Integration
WATCHED_FOLDER = r".\bartender_watch"

# Target Printer and BarTender Template
PRINTERNAME = "LBL_PRINTER_WH_VN"
LABELFILE   = "Measuring Equipment Label_18x38mm.BTW"

```

---

## How to Run

### Option A: Direct Windowed Execution (Recommended for End-Users)

Double-click **`RRCVN Label Printing GUI.pyw`**. Running via `.pyw` launches the interface cleanly without displaying an extra command prompt window.

### Option B: Command Line Execution (Development / Debugging)

Run the script using Python from the project root:

```bash
python rrc_vn_label_printing_gui_v1.py

```

---

## BarTender Integration Details

The drop-files written to `bartender_watch/` are exported using **UTF-8 with BOM** encoding (`utf-8-sig`) to accurately preserve special characters and formatting:

```text
PRINTERNAME	LABELFILE	MATNR	KTXT	WEDAT	EBELN	EBELP	BSTMG	BSTME	LGORT	LGPBE	SSNA	CONSIGNEE	CONSIGNEEADDRESS	WEIGHT	UNIT	CUSTOMER_REV	EXPDAT	MUNDAT	QUALITY_EQUIPMENT_NO	INVENTORY_NUMBER	RRC_PART_NUMBER	DRAWING_LINK	TYPE_MODEL	MANUFACTURER	EQUIPMENT_DESCRIPTION	SERIAL_NUMBER	LOCATED_AREA	STATION_SHELF_NO	FUNCTION	RANGE	ACCURACY	USED_FOR_TESTS	CALIBRATION_SCOPE	PLANNED_CALIBRATION_DATE	NEXT_CALIBRATION_DATE	LASER_STATUS	CALIBRATION_STATUS	REMAINING_DAYS	REMARK	FILE_NAME	TYPE	LINK	TOOL_NO
PRN-2000-3_A11-HARDPACK	R01_412117_B.BTW	210838	Glue_FB300ZW (Konishi)	20251009	4500008980	0	20	PCS	28	R4-A1	WH2-MAT-FLOW-R4	RRC POWER SOLUTIONS GMBH	GERMANY	120	KG	00	20260701	20250708	RRC_Q_0001	8400001	NA		DAQ970A	Keysight	Data-logger	MY58017467	Line 1	B01	DC volt	100 mV	0.0005 + 0.0005	Yes		45515	45880		Calibrated	107		RRC_Q_0001_Keysight_DAQ970A	01_Q-Equipments	RRC_Q_0001_Keysight_DAQ970A	RRC_F_0079

```
