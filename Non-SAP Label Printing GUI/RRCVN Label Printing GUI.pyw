"""
RRC VN - Label Printing GUI
Non-SAP Label Printing System

This GUI is only the standardized overview / launcher.
Each button can be linked to the related Python label script.
"""

import os
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from pathlib import Path

APP_VERSION = "1.0.0"
APP_TITLE = "RRC VN – Label Printing"
PRINTER_NAME = "ZEBRA ZT411 (203 dpi)"

# All label scripts are resolved relative to this GUI file.
BASE_DIR = Path(__file__).resolve().parent
SCRIPT_DIR = BASE_DIR / "scripts"
IMAGES_DIR = BASE_DIR / "images"  

# Link your real scripts here.
LABELS = [
    {
        "no": 1,
        "title": "Material Incoming\nLabel – TTR",
        "description": "For material incoming.\nFetches serial number and\nmanufacturing date from\nInkanto and calculates\nthe EXP date.",
        "script": "bartender_print-inkanto-ink_GUI.py",
        "image": "label_inkanto.png", 
    },
    {
        "no": 2,
        "title": "Material Incoming\nLabel – Konishi Glue",
        "description": "For material incoming\nKonishi glue.",
        "script": "bartender_print-konishi-glue_GUI.py",
        "image": "label_konishi.png", 
    },
    {
        "no": 3,
        "title": "Flowrack Label",
        "description": "Prints Flowrack location\nlabel with specific\ninformation.",
        "script": "bartender_print-flowrack_GUI.py",
        "image": "label_flowrack.png", 
    },
    {
        "no": 4,
        "title": "Shipper Consignee\nInfo Label",
        "description": "Generates label with\nshipping and consignee\ninformation.",
        "script": "bartender_print-shipper_consignee_info_GUI.py",
        "image": "label_shipper_consignee_info.png", 
    },
    {
        "no": 5,
        "title": "Stocktaking\nLabel",
        "description": "Label for inventory control\nand stock taking\nprocedures.",
        "script": "bartender_print-stocking-label_GUI.py",
        "image": "label_stocking.png", 
    },
    {
        "no": 6,
        "title": "Quality – Scrap\nBox Label",
        "description": "Prints a customized label\nfor scrap box with box\nnumber and other\ninformation.",
        "script": "bartender_print-scrap-label_GUI.py",
        "image": "label_scrap.png", 
    },
    {
        "no": 7,
        "title": "Quality – Scrap\nBox Label (PE Test)",
        "description": "Specific scrap box label\nfor failed PE tests.",
        "script": "bartender_print-scrap-label-PE-test_GUI.py",
        "image": "label_scrap_PE.png", 
    },
    {
        "no": 8,
        "title": "Quality – Q\nLabel Code",
        "description": "Prints quality control\nQ label codes for QA\ninspections.",
        "script": "bartender_print-Q-label.py",
        "image": "label_Qcode.png", 
    },
    {
        "no": 9,
        "title": "Quality – Waiting\nLabel",
        "description": "Label for products waiting\nfor QA/QC clearance or\nfurther testing.",
        "script": "bartender_print-waiting-label_GUI.py",
        "image": "label_waiting.png", 
    },
]

class LabelPrintingApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1320x860")
        self.minsize(1180, 760)
        self.configure(bg="#f5f8fc")

        self.colors = {
            "navy": "#062445",
            "blue": "#0b5db3",
            "blue_dark": "#084a90",
            "text": "#071a33",
            "muted": "#34445a",
            "border": "#d3dce8",
            "card": "#ffffff",
            "soft_blue": "#eaf3ff",
            "green": "#24a148",
            "red": "#c62828",
        }

        self.active_processes = {}
        self.status_var = tk.StringVar(value="Ready")
        self.printer_var = tk.StringVar(value=PRINTER_NAME)
        self.search_var = tk.StringVar()

        self.build_header()
        self.build_main()
        self.build_footer()

    def build_header(self):
        header = tk.Frame(self, bg=self.colors["navy"], height=100)
        header.pack(fill="x")
        header.pack_propagate(False)

        icon = tk.Canvas(header, width=56, height=56, bg=self.colors["navy"], highlightthickness=0)
        icon.pack(side="left", padx=(28, 18), pady=16)
        icon.create_rectangle(8, 20, 48, 44, outline="white", width=3)
        icon.create_rectangle(14, 8, 42, 24, outline="white", width=3)
        icon.create_rectangle(18, 36, 38, 50, outline="white", width=3)
        icon.create_line(17, 31, 39, 31, fill="white", width=2)

        title_block = tk.Frame(header, bg=self.colors["navy"])
        title_block.pack(side="left", pady=14)
        tk.Label(
            title_block,
            text="RRC VN – Label Printing",
            font=("Segoe UI", 22, "bold"),
            bg=self.colors["navy"],
            fg="white",
        ).pack(anchor="w")
        tk.Label(
            title_block,
            text="Non-SAP Label Printing System",
            font=("Segoe UI", 13),
            bg=self.colors["navy"],
            fg="#d6e4f5",
        ).pack(anchor="w", pady=(4, 0))

        right = tk.Frame(header, bg=self.colors["navy"])
        right.pack(side="right", padx=28)
        tk.Button(
            right,
            text="⚙  Settings",
            command=self.show_settings,
            font=("Segoe UI", 12, "bold"),
            bg=self.colors["navy"],
            fg="white",
            activebackground=self.colors["navy"],
            activeforeground="white",
            borderwidth=0,
            cursor="hand2",
        ).pack(side="left", padx=14)
        tk.Button(
            right,
            text="ⓘ  About",
            command=self.show_about,
            font=("Segoe UI", 12, "bold"),
            bg=self.colors["navy"],
            fg="white",
            activebackground=self.colors["navy"],
            activeforeground="white",
            borderwidth=0,
            cursor="hand2",
        ).pack(side="left", padx=14)

    def build_main(self):
        main = tk.Frame(self, bg="#f5f8fc")
        main.pack(fill="both", expand=True, padx=30, pady=20) 

        # Top section container (Now holds Icon, Intro Text, AND Search Bar)
        top = tk.Frame(main, bg="#f5f8fc")
        top.pack(fill="x")

        # 1. Label/Tag Icon
        label_icon = tk.Canvas(top, width=56, height=56, bg="#f5f8fc", highlightthickness=0)
        label_icon.pack(side="left", padx=(0, 15))
        
        # Tag body (Pointed on the left, rectangular on the right)
        label_icon.create_polygon(
            6, 28, 20, 14, 48, 14, 48, 42, 20, 42, 
            outline=self.colors["navy"], width=2, fill="#f5f8fc"
        )
        # Punch hole
        label_icon.create_oval(14, 25, 20, 31, outline=self.colors["navy"], width=2)
        # Placeholder "text" lines on the label
        label_icon.create_line(26, 22, 40, 22, fill=self.colors["navy"], width=2)
        label_icon.create_line(26, 28, 42, 28, fill=self.colors["navy"], width=2)
        label_icon.create_line(26, 34, 36, 34, fill=self.colors["navy"], width=2)

        # 2. Intro Text Frame
        intro = tk.Frame(top, bg="#f5f8fc")
        intro.pack(side="left") # Removed fill="x" so it shares the row with the search bar

        tk.Label(
            intro,
            text="Select Label to Print",
            font=("Segoe UI", 20, "bold"), 
            bg="#f5f8fc",
            fg=self.colors["text"],
        ).pack(anchor="w")

        tk.Label(
            intro,
            text="Choose a label to launch its existing print workflow. "
                 "The selected Python script will prepare the BarTender print data.",
            font=("Segoe UI", 11),
            bg="#f5f8fc",
            fg="#222222",
            wraplength=600,
            justify="left",
        ).pack(anchor="w", pady=(2, 0)) 

        # 3. Search / Filter Frame 
        search_frame = tk.Frame(top, bg="#f5f8fc")
        search_frame.pack(side="right", anchor="e", pady=(10, 0)) 
        
        tk.Label(
            search_frame, 
            text="🔍 Search Labels:", 
            font=("Segoe UI", 11, "bold"), 
            bg="#f5f8fc", 
            fg=self.colors["text"]
        ).pack(side="left")
        
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, font=("Segoe UI", 11), width=35)
        search_entry.pack(side="left", padx=(10, 0))
        self.search_var.trace_add("write", self.filter_labels)

        # Divider Line (Reduced padding to pull the cards up higher)
        tk.Frame(main, bg="#c9d3df", height=1).pack(fill="x", pady=(15, 15))

        # Scrollable card area
        card_container = tk.Frame(main, bg="#f5f8fc")
        card_container.pack(fill="both", expand=True)

        self.cards_canvas = tk.Canvas(
            card_container,
            bg="#f5f8fc",
            highlightthickness=0,
            bd=0,
        )
        scrollbar = ttk.Scrollbar(
            card_container,
            orient="vertical",
            command=self.cards_canvas.yview,
        )
        self.cards_canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.cards_canvas.pack(side="left", fill="both", expand=True)

        self.cards_frame = tk.Frame(self.cards_canvas, bg="#f5f8fc")
        self.cards_window = self.cards_canvas.create_window(
            (0, 0),
            window=self.cards_frame,
            anchor="nw",
        )

        self.cards_frame.bind(
            "<Configure>",
            lambda e: self.cards_canvas.configure(
                scrollregion=self.cards_canvas.bbox("all")
            ),
        )
        self.cards_canvas.bind(
            "<Configure>",
            lambda e: self.cards_canvas.itemconfigure(
                self.cards_window,
                width=e.width,
            ),
        )

        # Initial Render
        self.render_cards()

        info = tk.Frame(
            main,
            bg=self.colors["soft_blue"],
            highlightbackground="#bdd2ed",
            highlightthickness=1,
        )
        info.pack(fill="x", pady=(18, 0), ipady=12)

        tk.Label(
            info,
            text="i",
            width=2,
            font=("Segoe UI", 20, "bold"),
            bg=self.colors["soft_blue"],
            fg=self.colors["blue"],
        ).pack(side="left", padx=(20, 10))

        text_frame = tk.Frame(info, bg=self.colors["soft_blue"])
        text_frame.pack(side="left", fill="x", expand=True)

        tk.Label(
            text_frame,
            text="How it works",
            font=("Segoe UI", 11, "bold"),
            bg=self.colors["soft_blue"],
            fg=self.colors["navy"],
        ).pack(anchor="w")

        tk.Label(
            text_frame,
            text="Select a label above. The related Python script will open and "
                 "handle the required data entry and BarTender print-file creation.",
            font=("Segoe UI", 10),
            bg=self.colors["soft_blue"],
            fg=self.colors["navy"],
            wraplength=1000,
            justify="left",
        ).pack(anchor="w", pady=(4, 0))

        self.cards_canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
    def filter_labels(self, *args):
        query = self.search_var.get().lower()
        self.render_cards(query)
        
    def render_cards(self, filter_text=""):
        # Clear existing cards
        for widget in self.cards_frame.winfo_children():
            widget.destroy()
            
        # Filter logic
        filtered_labels = [
            lbl for lbl in LABELS 
            if filter_text in lbl["title"].lower() or filter_text in lbl["description"].lower()
        ]

        # Draw matching cards
        for index, label in enumerate(filtered_labels):
            card = self.create_label_card(self.cards_frame, label)
            card.grid(
                row=index // 3,
                column=index % 3,
                sticky="nsew",
                padx=8,
                pady=8,
            )

        # Draw "More" card at the end
        more_card = self.create_more_card(self.cards_frame)
        more_index = len(filtered_labels)
        more_card.grid(
            row=more_index // 3,
            column=more_index % 3,
            sticky="nsew",
            padx=8,
            pady=8,
        )

        for column in range(3):
            self.cards_frame.grid_columnconfigure(
                column,
                weight=1,
                uniform="cards",
            )

    def _on_mousewheel(self, event):
        if self.cards_canvas.winfo_exists():
            self.cards_canvas.yview_scroll(
                int(-1 * (event.delta / 120)),
                "units",
            )

    def create_label_card(self, parent, label):
        card = tk.Frame(
            parent,
            bg=self.colors["card"],
            height=320,  # <-- Reduced height since layout is now side-by-side
            highlightbackground=self.colors["border"],
            highlightthickness=1,
        )
        card.grid_propagate(False)

        # --- Header ---
        header = tk.Frame(card, bg=self.colors["card"])
        header.pack(fill="x", padx=16, pady=(16, 12))

        number = tk.Label(
            header,
            text=str(label["no"]),
            font=("Segoe UI", 12, "bold"),
            bg=self.colors["blue"],
            fg="white",
            width=2,
        )
        number.pack(side="left")

        tk.Label(
            header,
            text=label["title"],
            font=("Segoe UI", 11, "bold"),
            bg=self.colors["card"],
            fg=self.colors["text"],
            justify="left",
            anchor="w",
            wraplength=300,
        ).pack(side="left", padx=(10, 0), fill="x", expand=True)

        # --- Middle Content (Side-by-Side) ---
        content_frame = tk.Frame(card, bg=self.colors["card"])
        content_frame.pack(fill="both", expand=True, padx=16)

        # Left Side: Description
        tk.Label(
            content_frame,
            text=label["description"],
            font=("Segoe UI", 9),
            bg=self.colors["card"],
            fg="#222222",
            justify="left",
            anchor="nw",
            wraplength=180, # Keep text wrapped nicely on the left
        ).pack(side="left", fill="both", expand=True)

        # Right Side: Image
        image_name = label.get("image", "")
        image_path = IMAGES_DIR / image_name

        img_frame = tk.Frame(content_frame, bg=self.colors["card"])
        img_frame.pack(side="right", padx=(10, 0))

        # Handle Image Loading
        try:
            if image_name and image_path.exists():
                # Note: tk.PhotoImage natively supports PNG and GIF files.
                photo = tk.PhotoImage(file=str(image_path))
                img_label = tk.Label(img_frame, image=photo, bg=self.colors["card"], bd=1, relief="solid")
                img_label.image = photo  # CRITICAL: Keep a reference so Python's garbage collector doesn't delete it
                img_label.pack()
            else:
                raise FileNotFoundError
        except Exception:
            # Fallback if image is missing or not configured
            placeholder = tk.Label(
                img_frame, 
                text="[ Image\nMissing ]", 
                font=("Segoe UI", 9, "bold"),
                bg="#f0f0f0", 
                fg="#999999", 
                width=32, 
                height=15,
                bd=1,
                relief="solid"
            )
            placeholder.pack()

        # --- Footer: Print Button ---
        button = tk.Button(
            card,
            text="▶  Print Label",
            command=lambda selected=label: self.launch_script(selected),
            font=("Segoe UI", 10, "bold"),
            bg=self.colors["blue"],
            fg="white",
            activebackground=self.colors["blue_dark"],
            activeforeground="white",
            borderwidth=0,
            cursor="hand2",
            height=2,
        )
        button.pack(side="bottom", fill="x", padx=16, pady=16)

        button.bind("<Enter>", lambda e: button.configure(bg=self.colors["blue_dark"]))
        button.bind("<Leave>", lambda e: button.configure(bg=self.colors["blue"]))

        return card

    def create_more_card(self, parent):
        card = tk.Frame(
            parent,
            bg="#f7f9fc",
            height=410,
            highlightbackground="#aeb9c7",
            highlightthickness=1,
        )
        card.grid_propagate(False)

        tk.Label(
            card,
            text="+",
            font=("Segoe UI", 38),
            bg="#f7f9fc",
            fg="#111111",
        ).pack(pady=(105, 5))

        tk.Label(
            card,
            text="More Labels",
            font=("Segoe UI", 12, "bold"),
            bg="#f7f9fc",
            fg="#111111",
        ).pack()

        tk.Label(
            card,
            text="Coming Soon",
            font=("Segoe UI", 10),
            bg="#f7f9fc",
            fg="#555555",
        ).pack(pady=(8, 0))

        return card

    def build_footer(self):
        footer = tk.Frame(
            self,
            bg="#ffffff",
            height=46,
            highlightbackground="#d5dce6",
            highlightthickness=1,
        )
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        tk.Label(
            footer,
            text="▣",
            font=("Segoe UI", 13),
            bg="#ffffff",
            fg=self.colors["muted"],
        ).pack(side="left", padx=(28, 8))

        tk.Label(
            footer,
            text="Printer:",
            font=("Segoe UI", 10, "bold"),
            bg="#ffffff",
            fg="#111111",
        ).pack(side="left")

        tk.Label(
            footer,
            textvariable=self.printer_var,
            font=("Segoe UI", 10),
            bg="#ffffff",
            fg="#111111",
        ).pack(side="left", padx=(5, 18))

        tk.Label(
            footer,
            text="●",
            font=("Segoe UI", 11),
            bg="#ffffff",
            fg=self.colors["green"],
        ).pack(side="left")

        tk.Label(
            footer,
            textvariable=self.status_var,
            font=("Segoe UI", 10),
            bg="#ffffff",
            fg="#111111",
        ).pack(side="left", padx=(7, 0))

        tk.Label(
            footer,
            text=f"Version {APP_VERSION}",
            font=("Segoe UI", 10),
            bg="#ffffff",
            fg="#111111",
        ).pack(side="right", padx=28)

    def launch_script(self, label):
        script_name = label.get("script", "")
        script_path = SCRIPT_DIR / script_name

        if not script_name:
            messagebox.showerror(
                "Script Not Configured",
                f"No Python script has been configured for:\n"
                f"{label['title'].replace(chr(10), ' ')}",
            )
            return

        if not script_path.exists():
            messagebox.showerror(
                "Script Not Found",
                f"Could not find the Python script for this label.\n\n"
                f"Label: {label['title'].replace(chr(10), ' ')}\n"
                f"Expected file:\n{script_path}\n\n"
                "Please place the script in the 'scripts' folder or update "
                "the script name in LABELS.",
            )
            self.status_var.set("Script not found")
            return

        # Prevent the same workflow from being launched twice simultaneously.
        existing = self.active_processes.get(script_name)
        if existing is not None and existing.poll() is None:
            messagebox.showinfo(
                "Already Running",
                f"The workflow for this label is already running.\n\n"
                f"{label['title'].replace(chr(10), ' ')}",
            )
            return

        try:
            process = subprocess.Popen(
                [sys.executable, str(script_path)],
                cwd=str(SCRIPT_DIR),
            )
            self.active_processes[script_name] = process

            self.status_var.set(
                f"Started: {label['title'].replace(chr(10), ' ')}"
            )
            self._monitor_process(process, label)

        except Exception as exc:
            self.status_var.set("Failed to start script")
            messagebox.showerror(
                "Script Not Started",
                f"Could not start the selected label workflow.\n\n"
                f"Label: {label['title'].replace(chr(10), ' ')}\n"
                f"Script: {script_path}\n\n"
                f"Error:\n{exc}",
            )

    def _monitor_process(self, process, label):
        if process.poll() is None:
            self.after(500, lambda: self._monitor_process(process, label))
            return

        script_name = label.get("script", "")
        self.active_processes.pop(script_name, None)

        if process.returncode == 0:
            self.status_var.set(
                f"Completed: {label['title'].replace(chr(10), ' ')}"
            )
        else:
            self.status_var.set(
                f"Workflow exited with code {process.returncode}"
            )

    def show_settings(self):
        messagebox.showinfo(
            "Settings",
            f"Default printer:\n{PRINTER_NAME}\n\n"
            f"Script directory:\n{SCRIPT_DIR}\n\n"
            "Each label card launches its configured Python script. "
            "The Python script is responsible for creating the BarTender "
            "watched-folder print data file.",
        )

    def show_about(self):
        messagebox.showinfo(
            "About",
            "RRC VN – Label Printing\n"
            "Non-SAP Label Printing System\n\n"
            f"Version {APP_VERSION}\n\n"
            "Standard GUI launcher for RRC VN label-printing workflows.\n"
            "Each label uses an existing Python script, which prepares "
            "the print data for BarTender Integration.",
        )


if __name__ == "__main__":
    app = LabelPrintingApp()
    app.mainloop()