import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import numpy as np
import pymysql
import time
import warnings
import os
import sys
import json
from datetime import datetime

warnings.filterwarnings("ignore")

def resource_path(filename):
    """Ambil path file baik dari folder script maupun dari dalam EXE (PyInstaller)."""
    if getattr(sys, '_MEIPASS', None):
        return os.path.join(sys._MEIPASS, filename)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)

# ── PALETTE ──────────────────────────────────────
BG      = "#141414"
PANEL   = "#1E1E1E"
SURFACE = "#252525"
BORDER  = "#2A2A2A"

YEL  = "#F5C518"  # kuning bold
TEAL = "#00BFA5"
PINK = "#E91E63"
ORG  = "#FF6D00"
GRN  = "#00C853"
RED  = "#D32F2F"
PRP  = "#7C4DFF"

TXT    = "#F0F0F0"
TXT_DIM= "#6B6B6B"
TXT_YEL= "#F5C518"
TXT_GRN= "#00C853"
TXT_RED= "#E91E63"
TXT_ORG= "#FF6D00"

FT = ("Consolas", 9)
FT_B = ("Consolas", 9, "bold")
FT_H = ("Consolas", 11, "bold")
FT_XL= ("Consolas", 16, "bold")
FT_LG= ("Consolas", 13, "bold")

# ── KOLOM BAKU SAP ───────────────────────────────
SAP_COLS = [
    "No_Urut", "No_SAP", "Type", "Status", "Nomor_SPMSPB", "Nomor_SPPB", "Nomor_SPT", "Nomor_SPTA",
    "Nomor_SO", "Nomor_PO", "Nomor_GRPO", "Nomor_Surat_Jalan", "CardName",
    "ItemCode", "ItemName", "Batch", "Qty_SJ", "Qty_SPMSPB", "Remarks",
    "Tanggal_Masuk", "Berat_Masuk", "Jam_Masuk", "Tanggal_Keluar", "Berat_Keluar",
    "Jam_Keluar", "Tanggal_Loading_Mulai", "Jam_Loading_Mulai",
    "Tanggal_Loading_Selesai", "Jam_Loading_Selesai", "Supir", "Transportir",
    "Kendaraan", "Nopol", "Tipe", "CardCode", "Shift", "Qty_sblm_Rafaksi",
    "Persentase_Potongan_Rafaksi", "Qty_Rafaksi", "Qty_Netto", "NoSystem",
    "Kode_Pos_Insentif_Jarak", "Nama_Pos_Insentif_Jarak", "Jumlah_Karung",
    "Berat_rata2_Karung", "YEARSJ", "MONTHSJ", "DATESJ", "NOHP", "SJENTRY",
    "NOFAX", "NoDelivery", "MbsToWeighbridge", "CLEARFORM",
]

COL_W = {
    "No_Urut": 60, "No_SAP": 90,"Type":50,"Status":160,"Nomor_SPMSPB":130,"Nomor_SPPB":120,
    "Nomor_SPT":110,"Nomor_SPTA":110,"Nomor_SO":100,"Nomor_PO":100,
    "Nomor_GRPO":100,"Nomor_Surat_Jalan":130,"CardName":160,"ItemCode":90,
    "ItemName":160,"Batch":80,"Qty_SJ":70,"Qty_SPMSPB":90,"Remarks":140,
    "Tanggal_Masuk":110,"Berat_Masuk":90,"Jam_Masuk":80,
    "Tanggal_Keluar":110,"Berat_Keluar":90,"Jam_Keluar":80,
    "Tanggal_Loading_Mulai":130,"Jam_Loading_Mulai":110,
    "Tanggal_Loading_Selesai":140,"Jam_Loading_Selesai":120,
    "Supir":120,"Transportir":140,"Kendaraan":90,"Nopol":80,"Tipe":70,
    "CardCode":90,"Shift":50,"Qty_sblm_Rafaksi":120,
    "Persentase_Potongan_Rafaksi":170,"Qty_Rafaksi":90,"Qty_Netto":80,
    "NoSystem":100,"Kode_Pos_Insentif_Jarak":160,
    "Nama_Pos_Insentif_Jarak":170,"Jumlah_Karung":100,
    "Berat_rata2_Karung":130,"YEARSJ":60,"MONTHSJ":65,"DATESJ":60,
    "NOHP":100,"SJENTRY":80,"NOFAX":80,"NoDelivery":90,
    "MbsToWeighbridge":130,"CLEARFORM":80,
}


def shadow_frame(parent, bg=SURFACE, border=BORDER, bw=2, **kw):
    """Frame dengan border tebal ala neo-brutal."""
    wrap = tk.Frame(parent, bg=border, padx=bw, pady=bw)
    inner = tk.Frame(wrap, bg=bg, **kw)
    inner.pack(fill="both", expand=True)
    return wrap, inner


def neo_btn(parent, text, bg, fg="white", cmd=None, font=FT_H,
            px=18, py=9, border="#000000"):
    """Tombol neo-brutal: flat + thick border bawah/kanan (shadow efek)."""
    outer = tk.Frame(parent, bg=border, padx=0, pady=0)

    def on_enter(_):
        inner.config(bg=_darken(bg))
        outer.config(padx=2, pady=2)
    def on_leave(_):
        inner.config(bg=bg)
        outer.config(padx=0, pady=0)

    inner = tk.Button(outer, text=text, font=font, bg=bg, fg=fg,
                      activebackground=_darken(bg), activeforeground=fg,
                      relief="flat", cursor="hand2", bd=0,
                      command=cmd, padx=px, pady=py)
    inner.pack()
    outer.bind("<Enter>", on_enter)
    inner.bind("<Enter>", on_enter)
    outer.bind("<Leave>", on_leave)
    inner.bind("<Leave>", on_leave)
    return outer


def _darken(hex_color, amt=20):
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2],16), int(hex_color[2:4],16), int(hex_color[4:6],16)
    r, g, b = max(0,r-amt), max(0,g-amt), max(0,b-amt)
    return f"#{r:02x}{g:02x}{b:02x}"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("REKAP DSAJA — Data Input")
        self.geometry("1340x800")
        self.minsize(1100, 650)
        self.configure(bg=BG)
        self.resizable(True, True)
        self.current_df = None
        if getattr(sys, 'frozen', False):
            self.config_file = os.path.join(os.path.dirname(sys.executable), "config.json")
        else:
            self.config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
        self.db_host = self._load_ip()

        # Set icon aplikasi (title bar + taskbar)
        icon_path = resource_path("app.ico")
        if os.path.exists(icon_path):
            self.iconbitmap(default=icon_path)

        self._setup_style()
        self._build_header()
        self._build_table()
        self._build_log()
        self._build_footer()

        self.bind("<Control-v>", lambda e: self.paste_data())
        self.bind("<Control-V>", lambda e: self.paste_data())

        self._log("READYY", "Aplikasi siap. Tekan Ctrl+V atau klik PASTE Data.")

    # ── STYLE ────────────────────────────────────
    def _setup_style(self):
        s = ttk.Style()
        s.theme_use("clam")

        # ── Treeview body: border antar cell via clam theme elements
        s.configure("T.Treeview",
                    background="#1A1A1A", foreground=TXT,
                    fieldbackground="#1A1A1A", rowheight=26,
                    font=FT,
                    borderwidth=1, relief="solid",
                    bordercolor="#333333",
                    lightcolor="#333333",
                    darkcolor="#333333")

        # ── Heading: tombol timbul dengan border tegas
        s.configure("T.Treeview.Heading",
                    background="#0A0A0A", foreground=YEL,
                    font=FT_B, relief="raised", borderwidth=2,
                    bordercolor="#444444",
                    lightcolor="#333333",
                    darkcolor="#111111")

        # ── Modify layout untuk menampilkan separator (garis vertikal antar kolom)
        try:
            s.layout("T.Treeview", [
                ("T.Treeview.treearea", {"sticky": "nswe"})
            ])
            s.layout("T.Treeview.Item", [
                ("Treeitem.padding", {"sticky": "nswe", "children": [
                    ("Treeitem.text", {"sticky": "nswe"})
                ]})
            ])
        except tk.TclError:
            pass  # Beberapa versi tkinter tidak support custom layout

        s.map("T.Treeview",
              background=[("selected", PRP)],
              foreground=[("selected", "white")])
        s.map("T.Treeview.Heading",
              background=[("active", "#111111")])

    # ── HEADER ───────────────────────────────────
    def _build_header(self):
        hdr = tk.Frame(self, bg=BG, height=78)
        hdr.pack(fill="x", padx=12, pady=(12, 0))
        hdr.pack_propagate(False)

        # ── branding (icon + teks)
        brand = tk.Frame(hdr, bg=BG)
        brand.pack(side="left", pady=6)

        # Load icon gambar sebagai logo
        try:
            from PIL import Image, ImageTk
            ico_path = resource_path("icon_source.png")
            if os.path.exists(ico_path):
                img = Image.open(ico_path).resize((42, 42), Image.LANCZOS)
                self._brand_img = ImageTk.PhotoImage(img)
                tk.Label(brand, image=self._brand_img, bg=BG).pack(side="left", padx=(0, 6))
            else:
                tk.Label(brand, text=" C*K ", font=("Consolas",15,"bold"),
                         bg=YEL, fg="#0A0A0A", padx=6, pady=2).pack(side="left", padx=(0,6))
        except ImportError:
            tk.Label(brand, text=" C*K ", font=("Consolas",15,"bold"),
                     bg=YEL, fg="#0A0A0A", padx=6, pady=2).pack(side="left", padx=(0,6))

        tk.Label(brand, text="REKAP DSAJA", font=FT_XL,
                 bg=BG, fg=TXT).pack(side="left")

        # ── tombol kanan
        right = tk.Frame(hdr, bg=BG)
        right.pack(side="right", pady=10)

        # Baris atas: tombol IP
        self.btn_ip = tk.Button(right, text=f"🌐 IP: {self.db_host}",
                                font=FT_B, bg=SURFACE, fg=TXT_YEL,
                                activebackground=_darken(SURFACE),
                                activeforeground=TXT_YEL,
                                relief="flat", cursor="hand2", bd=0,
                                command=self._show_ip_settings,
                                padx=10, pady=4)
        self.btn_ip.pack(side="top", pady=(0, 4))

        # Baris bawah: MONITOR DB + OPTIONS + CLEAR
        bot_btn = tk.Frame(right, bg=BG)
        bot_btn.pack(side="top")
        neo_btn(bot_btn, "📊 MONITOR DB", TEAL, "white", self._show_db_monitor,
                font=FT_B, px=12, py=6, border="#000").pack(side="left", padx=4)
        neo_btn(bot_btn, "⚙ OPTIONS",   SURFACE, TXT_DIM, self._show_options,
                font=FT_B, px=12, py=6, border=BORDER).pack(side="left", padx=4)
        neo_btn(bot_btn, "✕ CLEAR",     RED,     "white",  self.clear_table,
                font=FT_B, px=12, py=6, border="#000").pack(side="left", padx=4)

        # ── status box
        sw, si = shadow_frame(hdr, bg=SURFACE, border=YEL, bw=2)
        sw.pack(side="left", padx=24, pady=12)

        top_row = tk.Frame(si, bg=SURFACE)
        top_row.pack(fill="x", padx=10, pady=(6,2))
        tk.Label(top_row, text="STATUS", font=FT_B, bg=SURFACE, fg=TXT_DIM).pack(side="left")

        mid_row = tk.Frame(si, bg=SURFACE)
        mid_row.pack(fill="x", padx=10, pady=(0,6))
        self.dot = tk.Label(mid_row, text="●", font=("Consolas",12), bg=SURFACE, fg=TXT_GRN)
        self.dot.pack(side="left")
        self.lbl_status = tk.Label(mid_row, text="Ready", font=FT_H, bg=SURFACE, fg=TXT_GRN)
        self.lbl_status.pack(side="left", padx=4)
        self.lbl_pending = tk.Label(mid_row, text="· 0 rows", font=FT_B, bg=SURFACE, fg=TXT_DIM)
        self.lbl_pending.pack(side="left")

        # ── tombol utama
        main = tk.Frame(hdr, bg=BG)
        main.pack(side="left", padx=8, pady=10)

        self.btn_paste = neo_btn(main, "📋  PASTE DATA", PRP, "white",
                                  self.paste_data, font=FT_H, px=20, py=10, border="#000")
        self.btn_paste.pack(side="left", padx=6)

        self.btn_upload = neo_btn(main, "⬆  UPLOAD TO DB", GRN, "white",
                                   self.sync_database, font=FT_H, px=20, py=10, border="#000")
        self.btn_upload.pack(side="left", padx=6)

        # ── aksen bawah header
        tk.Frame(self, bg=YEL, height=3).pack(fill="x", padx=0, pady=(8,0))

    # ── TABLE ────────────────────────────────────
    def _build_table(self):
        wrap = tk.Frame(self, bg=BORDER, padx=2, pady=2)
        wrap.pack(fill="both", expand=True, padx=12, pady=(6,4))

        inner = tk.Frame(wrap, bg=PANEL)
        inner.pack(fill="both", expand=True)

        th = tk.Frame(inner, bg="#0A0A0A", height=30)
        th.pack(fill="x")
        th.pack_propagate(False)
        tk.Label(th, text="  ▸ DATA PREVIEW", font=FT_B,
                 bg="#0A0A0A", fg=TXT_DIM).pack(side="left", padx=10, pady=6)
        self.lbl_row_count = tk.Label(th, text="", font=FT_B,
                                       bg="#0A0A0A", fg=YEL)
        self.lbl_row_count.pack(side="left")

        tv = tk.Frame(inner, bg=PANEL)
        tv.pack(fill="both", expand=True)

        vsb = ttk.Scrollbar(tv, orient="vertical")
        hsb = ttk.Scrollbar(tv, orient="horizontal")

        self.tree = ttk.Treeview(tv, style="T.Treeview",
                                  yscrollcommand=vsb.set,
                                  xscrollcommand=hsb.set)
        self.tree.tag_configure("odd",  background="#1A1A1A")
        self.tree.tag_configure("even", background="#212121")

        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        vsb.pack(side="right",  fill="y")
        hsb.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)

        self._init_columns()
        self.tree.bind("<Double-1>", self.on_double_click) #edit 

    def _init_columns(self):
        """Pasang kolom SAP bawaan."""
        self.tree["columns"] = SAP_COLS
        self.tree["show"]    = "headings"
        for col in SAP_COLS:
            w = COL_W.get(col, 100)
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, minwidth=60, anchor="w", stretch=False)

    # ── LOG ──────────────────────────────────────
    def _build_log(self):
        wrap = tk.Frame(self, bg=BORDER, padx=2, pady=2)
        wrap.pack(fill="x", padx=12, pady=(4,4))

        inner = tk.Frame(wrap, bg=PANEL)
        inner.pack(fill="both", expand=True)

        lh = tk.Frame(inner, bg="#0A0A0A")
        lh.pack(fill="x")

        tk.Label(lh, text="  ▸ PROCESS LOG", font=FT_B,
                 bg="#0A0A0A", fg=TXT_DIM).pack(side="left", padx=10, pady=6)

        tk.Button(lh, text=" CLR ", font=FT_B,
                  bg=RED, fg="white", activebackground=_darken(RED),
                  activeforeground="white", relief="flat", cursor="hand2",
                  command=self._clear_log, padx=6, pady=3).pack(side="right", padx=8, pady=4)

        body = tk.Frame(inner, bg="#0D0D0D")
        body.pack(fill="x")

        lsb = ttk.Scrollbar(body, orient="vertical")
        self.log = tk.Text(body, height=6, bg="#0D0D0D", fg=TXT, font=FT,
                           relief="flat", state="disabled", wrap="word",
                           yscrollcommand=lsb.set, highlightthickness=0, bd=0)
        lsb.config(command=self.log.yview)
        lsb.pack(side="right", fill="y")
        self.log.pack(fill="x", padx=6, pady=6)

        self.log.tag_configure("T",  foreground="#3A6EA5")
        self.log.tag_configure("INFO",    foreground="#5A7A9A")
        self.log.tag_configure("SUCCESS", foreground=TXT_GRN)
        self.log.tag_configure("WARNING", foreground=TXT_ORG)
        self.log.tag_configure("ERROR",   foreground=TXT_RED)
        self.log.tag_configure("MSG",     foreground="#9A9A9A")

    # ── FOOTER ───────────────────────────────────
    def _build_footer(self):
        foot = tk.Frame(self, bg="#0A0A0A", height=50)
        foot.pack(fill="x", side="bottom")
        foot.pack_propagate(False)

        stats = [
            ("TOTAL ROWS",      "s_total",    TXT),
            ("PENDING",         "s_pending",  YEL),
            ("READY TO UPLOAD", "s_ready",    TEAL),
            ("UPLOADED",        "s_uploaded", GRN),
        ]
        for i, (lbl, attr, col) in enumerate(stats):
            cell = tk.Frame(foot, bg="#0A0A0A")
            cell.pack(side="left", padx=22, pady=8)
            tk.Label(cell, text=lbl, font=FT_B, bg="#0A0A0A", fg=TXT_DIM).pack(side="left")
            v = tk.Label(cell, text="0", font=FT_LG, bg="#0A0A0A", fg=col)
            v.pack(side="left", padx=8)
            setattr(self, attr, v)
            if i < len(stats)-1:
                tk.Frame(foot, bg=BORDER, width=1).pack(side="left", fill="y", pady=10)

        self.lbl_ts = tk.Label(foot, text="LAST UPDATE: —", font=FT,
                                bg="#0A0A0A", fg=TXT_DIM)
        self.lbl_ts.pack(side="right", padx=20)

    # ── CONFIG IP ────────────────────────────────
    def _load_ip(self):
        """Baca db_host dari config.json. Default 127.0.0.1 jika file belum ada."""
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("db_host", "127.0.0.1")
        except (FileNotFoundError, json.JSONDecodeError, Exception):
            return "127.0.0.1"

    def _save_ip(self, new_ip):
        """Simpan db_host baru ke config.json dan update attribute."""
        self.db_host = new_ip
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump({"db_host": new_ip}, f, indent=2)
        except Exception as e:
            self._log("ERROR", f"Gagal menyimpan config: {e}")

    def _show_ip_settings(self):
        """Pop-up untuk mengubah IP server database."""
        ip_win = tk.Toplevel(self)
        ip_win.title("Setting IP Database")
        ip_win.geometry("380x200")
        ip_win.configure(bg=BG)
        ip_win.transient(self)
        ip_win.grab_set()

        wrap, inner = shadow_frame(ip_win, bg=SURFACE, border=BORDER, bw=2)
        wrap.pack(fill="both", expand=True, padx=10, pady=10)

        tk.Label(inner, text="IP Server Database", bg=SURFACE, fg=TXT_YEL,
                 font=FT_H).pack(pady=(18, 4))
        tk.Label(inner, text="Masukkan alamat IP tujuan MySQL:",
                 bg=SURFACE, fg=TXT_DIM, font=FT).pack(pady=(0, 8))

        entry_ip = tk.Entry(inner, font=FT_H, bg="#1A1A1A", fg=TXT,
                            insertbackground=TXT, relief="flat", justify="center")
        entry_ip.pack(pady=4, padx=30, fill="x", ipady=6)
        entry_ip.insert(0, self.db_host)
        entry_ip.select_range(0, tk.END)
        entry_ip.focus_set()

        def simpan(event=None):
            new_ip = entry_ip.get().strip()
            if not new_ip:
                return
            self._save_ip(new_ip)
            self.btn_ip.config(text=f"🌐 IP: {self.db_host}")
            self._log("SUCCESS", f"IP Database diperbarui → {self.db_host}")
            ip_win.destroy()

        entry_ip.bind("<Return>", simpan)

        btn_wrap = tk.Frame(inner, bg=SURFACE)
        btn_wrap.pack(pady=10)
        neo_btn(btn_wrap, "💾 SIMPAN", GRN, "white", simpan,
                font=FT_B, px=15, py=6, border="#000").pack()

    # ── LIVE DB MONITOR ─────────────────────────
    def _show_db_monitor(self):
        """Buka jendela monitor untuk melihat 100 data terakhir di DB dengan fitur pencarian & edit."""
        mon = tk.Toplevel(self)
        mon.title("Live Database Monitor")
        mon.geometry("1200x680")
        mon.configure(bg=BG)
        mon.transient(self)

        # ── Header monitor
        mhdr = tk.Frame(mon, bg=PANEL, height=50)
        mhdr.pack(fill="x", padx=0, pady=0)
        mhdr.pack_propagate(False)

        tk.Label(mhdr, text="  LIVE DATABASE MONITOR",
                 font=FT_XL, bg=PANEL, fg=TXT_YEL).pack(side="left", padx=12, pady=10)
        tk.Label(mhdr, text="(100 DATA TERAKHIR)",
                 font=FT_B, bg=PANEL, fg=TXT_DIM).pack(side="left", padx=(0, 10), pady=10)

        neo_btn(mhdr, "🔄 REFRESH DATA", PRP, "white",
                lambda: self._fetch_db_data(mon_tree, selected_col.get(), entry_key.get().strip()),
                font=FT_B, px=14, py=6, border="#000").pack(side="right", padx=12, pady=8)

        neo_btn(mhdr, "📝 EDIT DATA SELECTED", ORG, "white",
                lambda: self._edit_db_data(mon_tree),
                font=FT_B, px=14, py=6, border="#000").pack(side="right", padx=6, pady=8)

        # ── Aksen garis bawah header
        tk.Frame(mon, bg=TEAL, height=3).pack(fill="x")

        # ── Info IP
        info_bar = tk.Frame(mon, bg="#0A0A0A", height=28)
        info_bar.pack(fill="x")
        info_bar.pack_propagate(False)
        tk.Label(info_bar, text=f"  🌐 Host: {self.db_host}   │   📦 Tabel: data_timbang",
                 font=FT, bg="#0A0A0A", fg=TXT_DIM).pack(side="left", padx=8, pady=4)
        self._mon_info_lbl = tk.Label(info_bar, text="", font=FT, bg="#0A0A0A", fg=TXT_GRN)
        self._mon_info_lbl.pack(side="right", padx=12, pady=4)

        # ── Search & Filter Panel (Top Panel)
        sf = tk.Frame(mon, bg=PANEL, height=45)
        sf.pack(fill="x", padx=12, pady=(6, 2))
        sf.pack_propagate(False)

        # Mengambil kolom secara dinamis dari DB
        db_cols = []
        try:
            conn = pymysql.connect(host=self.db_host, user="wb_rmi",
                                   password="12345678", database="timbangan")
            with conn.cursor() as cursor:
                cursor.execute("SHOW COLUMNS FROM data_timbang")
                db_cols = [x[0] for x in cursor.fetchall()]
            conn.close()
        except Exception:
            db_cols = SAP_COLS.copy()

        tk.Label(sf, text="Cari:", font=FT_B, bg=PANEL, fg=TXT_DIM).pack(side="left", padx=(10, 6), pady=12)

        selected_col = tk.StringVar()
        if db_cols:
            selected_col.set(db_cols[0])

        cb_col = ttk.Combobox(sf, textvariable=selected_col, values=db_cols, state="readonly", font=FT, width=18)
        cb_col.pack(side="left", padx=4, pady=10)

        tk.Label(sf, text="Kata Kunci:", font=FT_B, bg=PANEL, fg=TXT_DIM).pack(side="left", padx=(10, 6), pady=12)

        entry_key = tk.Entry(sf, font=FT, bg="#1A1A1A", fg=TXT, insertbackground=TXT, relief="flat", width=25)
        entry_key.pack(side="left", padx=4, pady=10, ipady=3)

        def trigger_search(event=None):
            col = selected_col.get()
            q = entry_key.get().strip()
            self._fetch_db_data(mon_tree, search_col=col, search_query=q)

        entry_key.bind("<Return>", trigger_search)

        neo_btn(sf, "🔍 CARI", TEAL, "white", trigger_search, font=FT_B, px=12, py=4, border="#000").pack(side="left", padx=12, pady=6)

        # Label Total Data
        self._mon_total_lbl = tk.Label(sf, text="📊 Total Data: 0 Rows", font=FT_H, bg=PANEL, fg=YEL)
        self._mon_total_lbl.pack(side="right", padx=15, pady=12)

        # ── Statistics & Metadata Panel (Metadata Bar)
        stat_bar = tk.Frame(mon, bg="#0A0A0A", height=32)
        stat_bar.pack(fill="x", padx=12, pady=(2, 6))
        stat_bar.pack_propagate(False)

        # Label info statistik rentang tanggal
        self._mon_stat_lbl = tk.Label(stat_bar, text="📅 Tanggal Keluar: — s/d —  │  🚀 Tanggal Upload: — s/d —",
                                      font=FT_B, bg="#0A0A0A", fg=YEL)
        self._mon_stat_lbl.pack(side="left", padx=15, pady=6)

        # ── Tabel monitor
        tw = tk.Frame(mon, bg=BORDER, padx=2, pady=2)
        tw.pack(fill="both", expand=True, padx=8, pady=(6, 8))

        tv_inner = tk.Frame(tw, bg=PANEL)
        tv_inner.pack(fill="both", expand=True)

        vsb = ttk.Scrollbar(tv_inner, orient="vertical")
        hsb = ttk.Scrollbar(tv_inner, orient="horizontal")

        mon_tree = ttk.Treeview(tv_inner, style="T.Treeview",
                                yscrollcommand=vsb.set,
                                xscrollcommand=hsb.set)
        mon_tree.tag_configure("odd",  background="#1A1A1A")
        mon_tree.tag_configure("even", background="#212121")

        vsb.config(command=mon_tree.yview)
        hsb.config(command=mon_tree.xview)
        vsb.pack(side="right",  fill="y")
        hsb.pack(side="bottom", fill="x")
        mon_tree.pack(fill="both", expand=True)

        # Auto-refresh saat pertama kali buka
        self._fetch_db_data(mon_tree)

    def _fetch_db_data(self, tree_widget, search_col=None, search_query=None):
        """Tarik 100 data dari MySQL dan tampilkan di Treeview monitor."""
        conn = None
        cursor = None
        try:
            conn = pymysql.connect(host=self.db_host, user="wb_rmi",
                                   password="12345678", database="timbangan",
                                   autocommit=False)
            cursor = conn.cursor()

            # Ambil nama kolom dari tabel
            cursor.execute("SHOW COLUMNS FROM data_timbang")
            db_cols = [x[0] for x in cursor.fetchall()]

            # Setup kolom Treeview sesuai kolom DB
            tree_widget["columns"] = db_cols
            tree_widget["show"] = "headings"
            for col in db_cols:
                w = COL_W.get(col, 100)
                tree_widget.heading(col, text=col)
                tree_widget.column(col, width=w, minwidth=50, anchor="w", stretch=False)

            # Query dengan default sorting menggunakan STR_TO_DATE untuk keakuratan tanggal string
            if search_col and search_query:
                # Cari berbasis LIKE (parameterized untuk keamanan)
                query = f"SELECT * FROM data_timbang WHERE `{search_col}` LIKE %s ORDER BY STR_TO_DATE(Tanggal_Keluar, '%d/%m/%Y %H:%i') DESC LIMIT 100"
                cursor.execute(query, (f"%{search_query}%",))
            else:
                query = "SELECT * FROM data_timbang ORDER BY STR_TO_DATE(Tanggal_Keluar, '%d/%m/%Y %H:%i') DESC LIMIT 100"
                cursor.execute(query)
            
            rows = cursor.fetchall()

            # Bersihkan data lama
            tree_widget.delete(*tree_widget.get_children())

            # Masukkan data baru
            for i, row in enumerate(rows):
                vals = [v if v is not None else "" for v in row]
                tag = "even" if i % 2 == 0 else "odd"
                tree_widget.insert("", "end", values=vals, tags=(tag,))

            # Update info label jika masih ada
            ts = datetime.now().strftime("%H:%M:%S")
            try:
                self._mon_info_lbl.config(
                    text=f"✔ {len(rows)} baris dimuat  •  {ts}")
            except tk.TclError:
                pass

            # Ambil total keseluruhan baris & statistik rentang tanggal dari DB
            total_db_rows = 0
            stat_text = "📅 Rentang Tanggal Keluar: — s/d —  │  🔄 Last Update DB: —"
            try:
                # 1. Total data real di tabel 'data_timbang'
                cursor.execute("SELECT COUNT(*) FROM data_timbang")
                total_db_rows = cursor.fetchone()[0]

                # 2. Statistik tanggal Keluar & tanggal upload agregat dengan STR_TO_DATE kronologis
                cursor.execute("SELECT MIN(STR_TO_DATE(Tanggal_Keluar, '%d/%m/%Y %H:%i')), MAX(STR_TO_DATE(Tanggal_Keluar, '%d/%m/%Y %H:%i')), MAX(tanggal_upload) FROM data_timbang")
                min_keluar, max_keluar, max_upload = cursor.fetchone()

                # Format tanggal keluar jika bertipe datetime (hasil STR_TO_DATE)
                str_keluar_min = min_keluar.strftime('%d/%m/%Y %H:%M') if hasattr(min_keluar, 'strftime') else (str(min_keluar) if min_keluar else "—")
                str_keluar_max = max_keluar.strftime('%d/%m/%Y %H:%M') if hasattr(max_keluar, 'strftime') else (str(max_keluar) if max_keluar else "—")

                # Format tanggal upload ter-update
                str_upload_max = max_upload.strftime('%d/%m/%Y %H:%M') if hasattr(max_upload, 'strftime') else (str(max_upload) if max_upload else "—")

                stat_text = f"📅 Rentang Tanggal Keluar: {str_keluar_min} s/d {str_keluar_max}  │  🔄 Last Update DB: {str_upload_max}"
            except Exception as stat_err:
                self._log("WARNING", f"Gagal memuat statistik database: {stat_err}")

            # Update labels di panel atas monitor
            try:
                self._mon_total_lbl.config(text=f"📊 Total Data: {total_db_rows} Rows")
            except tk.TclError:
                pass

            try:
                self._mon_stat_lbl.config(text=stat_text)
            except tk.TclError:
                pass

            if search_col and search_query:
                self._log("SUCCESS", f"Monitor DB: Ditemukan {len(rows)} data untuk `{search_col}` = '{search_query}'.")
            else:
                self._log("SUCCESS", f"Monitor DB: {len(rows)} baris berhasil ditarik dari {self.db_host}.")

        except Exception as e:
            messagebox.showerror("Error Koneksi DB",
                                 f"Gagal menarik data dari database.\n\n"
                                 f"Host: {self.db_host}\n"
                                 f"Error: {e}")
            self._log("ERROR", f"Monitor DB gagal: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def _edit_db_data(self, tree_widget):
        """Buka jendela popup untuk mengedit data yang dipilih di Treeview monitor."""
        selected_item = tree_widget.focus()
        if not selected_item:
            messagebox.showwarning("Peringatan", "Silakan pilih data yang ingin diedit terlebih dahulu!")
            return

        values = tree_widget.item(selected_item, "values")
        cols = tree_widget["columns"]
        data_dict = dict(zip(cols, values))

        # Buat TopLevel popup
        edit_win = tk.Toplevel(self)
        edit_win.title("EDIT DATA TIMBANGAN")
        edit_win.geometry("500x600")
        edit_win.configure(bg=BG)
        edit_win.transient(self)
        edit_win.grab_set()

        # Shadow wrap untuk jendela edit
        wrap, inner = shadow_frame(edit_win, bg=SURFACE, border=BORDER, bw=2)
        wrap.pack(fill="both", expand=True, padx=10, pady=10)

        # Header Popup
        tk.Label(inner, text="📝 EDIT DATA TIMBANGAN", font=FT_H, bg=SURFACE, fg=YEL).pack(pady=(12, 6))

        # Scrollable Canvas & Frame agar muat puluhan kolom
        canvas = tk.Canvas(inner, bg=SURFACE, highlightthickness=0)
        scrollbar = ttk.Scrollbar(inner, orient="vertical", command=canvas.yview)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True, padx=(10, 2), pady=10)

        scrollable_frame = tk.Frame(canvas, bg=SURFACE)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        def _on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)
        canvas.bind('<Configure>', _on_canvas_configure)

        entry_map = {}

        # Loop setiap kolom dan buat label + entry
        for col in cols:
            row_f = tk.Frame(scrollable_frame, bg=SURFACE)
            row_f.pack(fill="x", pady=4, padx=5)

            tk.Label(row_f, text=col, font=FT_B, bg=SURFACE, fg=TXT_DIM, width=20, anchor="w").pack(side="left")

            val_str = str(data_dict.get(col, ""))

            # Khusus No_Urut jadikan readonly/disabled karena PK
            if col == "No_Urut":
                ent = tk.Entry(row_f, font=FT, bg="#1A1A1A", fg=TXT_DIM, relief="flat", state="readonly")
                ent.pack(side="left", fill="x", expand=True, ipady=3)
                ent.config(state="normal")
                ent.insert(0, val_str)
                ent.config(state="readonly")
            else:
                ent = tk.Entry(row_f, font=FT, bg="#1A1A1A", fg=TXT, insertbackground=TXT, relief="flat")
                ent.pack(side="left", fill="x", expand=True, ipady=3)
                ent.insert(0, val_str)

            entry_map[col] = ent

        # Tombol simpan di frame tersendiri paling bawah
        btn_f = tk.Frame(inner, bg=SURFACE)
        btn_f.pack(fill="x", pady=(5, 10))

        def simpan_perubahan():
            self._save_db_edit(edit_win, entry_map, tree_widget)

        neo_btn(btn_f, "💾 SIMPAN PERUBAHAN", GRN, "white", simpan_perubahan, font=FT_B, px=20, py=8, border="#000").pack(pady=4)

    def _save_db_edit(self, edit_win, entry_map, tree_widget):
        """Kirim query UPDATE ke MySQL untuk menyimpan perubahan data edit."""
        updated_data = {}
        for col, ent in entry_map.items():
            updated_data[col] = ent.get().strip()

        no_urut = updated_data.get("No_Urut")
        if not no_urut:
            messagebox.showerror("Error", "No_Urut tidak ditemukan!")
            return

        # Ambil daftar kolom yang akan di-update (selain No_Urut)
        update_cols = [c for c in updated_data.keys() if c != "No_Urut"]

        set_clause = ", ".join([f"`{c}`=%s" for c in update_cols])
        sql = f"UPDATE data_timbang SET {set_clause} WHERE No_Urut=%s"

        vals = []
        for c in update_cols:
            val = updated_data[c]
            if val == "":
                vals.append(None)
            else:
                vals.append(val)
        vals.append(no_urut)

        conn = None
        cursor = None
        try:
            conn = pymysql.connect(host=self.db_host, user="wb_rmi",
                                   password="12345678", database="timbangan",
                                   autocommit=False)
            cursor = conn.cursor()

            cursor.execute(sql, tuple(vals))
            conn.commit()

            messagebox.showinfo("Sukses", "Data Berhasil Diperbarui!", parent=edit_win)
            edit_win.destroy()

            # Refresh data di Treeview monitor
            self._fetch_db_data(tree_widget)
            self._log("SUCCESS", f"Monitor DB: Berhasil memperbarui data No_Urut {no_urut}.")

        except Exception as e:
            if conn:
                conn.rollback()
            messagebox.showerror("Error Update DB", f"Gagal menyimpan data ke database:\n\n{e}", parent=edit_win)
            self._log("ERROR", f"Monitor DB Update gagal: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    # ── HELPERS ──────────────────────────────────
    def _log(self, level, msg):
        now = datetime.now().strftime("%H:%M:%S")
        self.log.config(state="normal")
        self.log.insert("end", f"[{now}] ", "T")
        self.log.insert("end", f"{level:<9}", level)
        self.log.insert("end", msg + "\n", "MSG")
        self.log.config(state="disabled")
        self.log.see("end")

    def _clear_log(self):
        self.log.config(state="normal")
        self.log.delete("1.0", "end")
        self.log.config(state="disabled")

    def _set_status(self, text, state="ok"):
        c = {"ok": TXT_GRN, "warn": TXT_ORG, "err": TXT_RED}[state]
        self.lbl_status.config(text=text, fg=c)
        self.dot.config(fg=c)

    def _update_footer(self, total=0, pending=0, ready=0, uploaded=0):
        self.s_total.config(text=str(total))
        self.s_pending.config(text=str(pending))
        self.s_ready.config(text=str(ready))
        self.s_uploaded.config(text=str(uploaded))
        ts = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.lbl_ts.config(text=f"LAST UPDATE: {ts}")

    # ── PASTE DATA ───────────────────────────────
    def paste_data(self):
        try:
            self._set_status("Reading clipboard...", "warn")
            self._log("INFO", "Membaca clipboard...")
            self.update()

         # Buka Gerbang Anti-Crash untuk 60 kolom
            df = pd.read_clipboard(header=None, dtype=str, sep='\t', quoting=3, names=range(60))
            
            if df.empty:
                messagebox.showwarning("Kosong", "Clipboard kosong! Copy dulu dari addon/Excel.")
                self._set_status("Ready", "ok")
                self._log("WARNING", "Clipboard kosong.")
                return

            # Ubah NaN jadi string kosong biar gampang dicek
            df = df.fillna("")

            # ====================================================
            # 0. PRE-CLEANER (OBAT ANTI GHOST-TAB DARI SAP)
            # ====================================================
            for i in range(len(df)):
                # Kalau kolom ke-1 kosong (gara-gara tab gaib SAP), TAPI kolom ke-2 ada isinya
                if str(df.iloc[i, 0]).strip() == "" and str(df.iloc[i, 1]).strip() != "":
                    # Tarik paksa semua data di baris ini ke kiri 1 langkah!
                    df.iloc[i, :-1] = df.iloc[i, 1:].values
                    df.iloc[i, -1] = ""
            # ====================================================

            # 1. POTONG KELEBIHAN KOLOM (Ambil 53 kolom asli dari SAP)
            if len(df.columns) > 53:
                df = df.iloc[:, :53]
                
            # 2. BERI NAMA 53 KOLOM (Sekaligus menamai kolom ke-1 jadi "No_SAP")
            df.columns = SAP_COLS[1:]

           # ====================================================
            # 🛠️ SIHIR LEM BESI V4 (Sedot Karung Hantu - ANTI GESER)
            # ====================================================
            if "No_SAP" in df.columns and "Remarks" in df.columns:
                df = df.reset_index(drop=True)
                rows_to_drop = []
                
                idx_sap = list(df.columns).index("No_SAP")
                idx_remarks = list(df.columns).index("Remarks")
                last_valid_head = -1
                
                for i in range(len(df)):
                    val_col_0 = str(df.iloc[i, idx_sap]).strip()
                    
                    if val_col_0.isdigit() and val_col_0 != "":
                        last_valid_head = i
                    else:
                        if last_valid_head != -1:
                            row_vals = df.iloc[i].values
                            
                            # Cari index kolom pertama yang ADA ISINYA
                            first_filled = -1
                            for c_idx, val in enumerate(row_vals):
                                if pd.notna(val) and str(val).strip() != "":
                                    first_filled = c_idx
                                    break
                                    
                            if first_filled != -1:
                                tump_awal = str(row_vals[first_filled]).strip()
                                is_date = "/" in tump_awal and len(tump_awal) >= 8 and tump_awal[:1].isdigit()
                                
                                col_target = idx_remarks + 1
                                start_copy = first_filled + 1
                                
                                if not is_date:
                                    # Sedot teks (misal "1. BIRU") ke Remarks
                                    prev_rmk = str(df.iat[last_valid_head, idx_remarks]).strip()
                                    df.iat[last_valid_head, idx_remarks] = f"{prev_rmk} {tump_awal}".strip()
                                else:
                                    # Kalau tumpahan awal adalah Tanggal, taruh di kolom target
                                    if col_target < len(df.columns):
                                        df.iat[last_valid_head, col_target] = tump_awal
                                        col_target += 1
                                        
                                # PINDAHKAN SISA GERBONG (TERMASUK SEL KOSONG BIAR GAK GESER!)
                                for s_val in row_vals[start_copy:]:
                                    if col_target < len(df.columns):
                                        # Pakai pd.notna untuk nangkep NaN jadi string kosong
                                        df.iat[last_valid_head, col_target] = s_val if pd.notna(s_val) else ""
                                        col_target += 1
                                        
                            rows_to_drop.append(i)

                if rows_to_drop:
                    df = df.drop(index=rows_to_drop).reset_index(drop=True)
                    self._log("SUCCESS", f"✨ {len(rows_to_drop)} baris hantu disedot bersih TANPA GESER!")
            # ====================================================
            
            # 3. BIKIN KOLOM PENOMORAN OTOMATIS DI PALING KIRI
            df.insert(0, "No_Urut", range(1, len(df) + 1))
            self.current_df = df
            n = len(df)

            self.tree.delete(*self.tree.get_children())

            # ── Selalu gunakan SAP_COLS sebagai header tabel ──
            self.tree["columns"] = SAP_COLS
            self.tree["show"]    = "headings"
            for col in SAP_COLS:
                self.tree.heading(col, text=col)

            # Konversi ke list untuk performa maksimal
            rows = df.to_numpy().tolist()
            sap_len = len(SAP_COLS)
            
            # Array untuk melacak panjang teks maksimal tiap kolom (awal = panjang nama header)
            col_max_lens = [len(str(c)) for c in SAP_COLS]

            for i, row in enumerate(rows):
                # Ekstrak data dan pad dengan string kosong jika kurang
                mapped = row[:sap_len]
                if len(mapped) < sap_len:
                    mapped.extend([""] * (sap_len - len(mapped)))
                
                # Cek teks terpanjang di tiap kolom
                for j in range(sap_len):
                    cell_len = len(str(mapped[j]))
                    if cell_len > col_max_lens[j]:
                        col_max_lens[j] = cell_len

                tag = "even" if i % 2 == 0 else "odd"
                self.tree.insert("", "end", values=mapped, tags=(tag,))

            # Terapkan perhitungan lebar kolom ke Treeview (1 char ~ 8px + padding 20px)
            for j, col in enumerate(SAP_COLS):
                calc_w = min(400, max(50, col_max_lens[j] * 8 + 20))
                self.tree.column(col, width=calc_w, minwidth=50, anchor="w", stretch=False)

            clip_cols = list(df.columns)
            self.lbl_row_count.config(text=f"  {n} baris")
            self.lbl_pending.config(text=f"· {n} rows")
            self._set_status("Ready", "ok")
            self._update_footer(total=n, pending=n, ready=n, uploaded=0)
            self._log("SUCCESS", f"Paste OK — {n} baris dimuat.")
            self._log("INFO", f"Pemetaan posisional: {len(clip_cols)} kolom disalin ke tabel.")

        except Exception as e:
            messagebox.showerror("Error Paste", f"Gagal baca clipboard.\n{e}")
            self._set_status("Error!", "err")
            self._log("ERROR", f"Gagal paste: {e}")

    # ── FITUR EDIT LANGSUNG DI TABEL (DOUBLE CLICK) ──
    def on_double_click(self, event):
        if self.current_df is None or self.current_df.empty: return
        
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell": return
        
        column = self.tree.identify_column(event.x)
        item = self.tree.identify_row(event.y)
        col_idx = int(column[1:]) - 1
        col_name = self.tree["columns"][col_idx]
        
        # Ambil posisi dan nilai saat ini
        x, y, width, height = self.tree.bbox(item, column)
        current_value = self.tree.set(item, column)
        
        # Bikin kotak input melayang di atas sel
        entry = tk.Entry(self.tree, font=FT, justify="center")
        entry.place(x=x, y=y, width=width, height=height)
        entry.insert(0, current_value)
        entry.focus_set()
        entry.select_range(0, tk.END)
        
        def save_edit(e):
            new_val = entry.get()
            self.tree.set(item, column, new_val) # Update tampilan tabel
            
            # ==========================================
            # 🎯 JURUS ANTI BARIS HANTU (TEMBAK POSISI MUTLAK)
            # ==========================================
            df_idx = int(self.tree.index(item)) # Paksa jadi angka bulat mutlak
            col_pos = self.current_df.columns.get_loc(col_name) # Cari posisi asli kolomnya
            
            # Gunakan .iat untuk menimpa SEL secara spesifik berdasarkan index posisi
            self.current_df.iat[df_idx, col_pos] = new_val 
            
            entry.destroy()
            self._log("MSG", f"📝 Edit No. Tabel {df_idx + 1}: '{col_name}' diubah jadi '{new_val}'")

        def cancel_edit(e):
            entry.destroy()

        entry.bind("<Return>", save_edit)      # Tekan Enter untuk Simpan
        entry.bind("<Escape>", cancel_edit)    # Tekan Esc untuk Batal
        entry.bind("<FocusOut>", save_edit)    # Klik di luar untuk Simpan

    # ── UPLOAD DB ────────────────────────────────
    def sync_database(self):
        if self.current_df is None or self.current_df.empty:
            messagebox.showwarning("Kosong", "Paste data dulu!")
            return

        self._set_status("Uploading...", "warn")
        self._log("INFO", "Upload dimulai...")
        self.update()

        start = time.time()
        df    = self.current_df.copy()
        # =============================================================
        # --- BUANG KOLOM URUT & BALIKIN NAMA KHUSUS BUAT UPLOAD DB ---
        # =============================================================
        df = df.drop(columns=["No_Urut"], errors="ignore")
        if "No_SAP" in df.columns:
            df.rename(columns={"No_SAP": "No"}, inplace=True)
        # =============================================================

        conn  = None
        cursor = None
        try:
            if "Status" in df.columns:
                before = len(df)
                df["Status"] = df["Status"].astype(str).str.strip()
                
                # --- CCTV: NANGKAP HANTU PASTE ---
                ditendang_status = df[df["Status"] != "Timbang Keluar & Confirm"]
                if not ditendang_status.empty:
                    self._log("WARNING", f"👻 CCTV: {len(ditendang_status)} baris hantu ditendang filter Status!")
                    for idx, r in ditendang_status.iterrows():
                        isi_status = repr(r.get("Status", "")) # Pakai repr biar kelihatan kalau isinya spasi/enter
                        nopol = r.get("Nopol", "?")
                        self._log("ERROR", f"   ► Nopol: {nopol} | Isi Statusnya: {isi_status}")

                df = df[df["Status"] == "Timbang Keluar & Confirm"]
                self._log("INFO", f"Filter status: {before} → {len(df)} baris.")

            if df.empty:
                messagebox.showinfo("Info", "Tidak ada data valid.")
                self._set_status("Dibatalkan", "warn")
                self._log("WARNING", "Tidak ada data valid setelah filter.")
                return

            # ==========================================
            # FIX DATETIME & KEMBALIKAN WUJUD ASLI (DD/MM/YYYY HH:MM)
            # ==========================================
            
            # --- Proses untuk Tanggal_Keluar ---
            # --- Proses untuk Tanggal_Keluar ---
            if 'Tanggal_Keluar' in df.columns and 'Jam_Keluar' in df.columns:
                tgl_k_str = df["Tanggal_Keluar"].astype(str).str[:10]
                jam_k_str = df["Jam_Keluar"].astype(str).str[-8:]
                
                # Mesin waktu anti-bug
                df["Datetime_Keluar"] = pd.to_datetime(tgl_k_str + " " + jam_k_str, dayfirst=True, errors="coerce")
                
               # ====================================================
                # 🎥 CCTV X-RAY: BONGKAR TOTAL POSISI KOLOM YANG GESER
                # ====================================================
                cacat_dt = df[df["Datetime_Keluar"].isna()]
                if not cacat_dt.empty:
                    self._log("WARNING", f"🗑️ INVESTIGASI: {len(cacat_dt)} data ditendang karena Tanggal Keluar KOSONG!")
                    for idx, r in cacat_dt.iterrows():
                        no_sap = str(r.get("No", "?")).strip()
                        
                        self._log("ERROR", f"🚨 BONGKAR POSISI KOLOM UNTUK NO SAP: {no_sap}")
                        
                        dump_text = []
                        # Ambil semua kolom dari index 0 sampai akhir
                        for col_name in df.columns:
                            val = str(r.get(col_name, "")).strip()
                            if val: # Biar log gak penuh, kita log yang ada isinya aja
                                dump_text.append(f"{col_name}='{val}'")
                                
                        # Cetak berjejer tiap 4 kolom biar gampang dibaca
                        for i in range(0, len(dump_text), 4):
                            self._log("MSG", " ➔ ".join(dump_text[i:i+4]))
                # ====================================================

                df = df.dropna(subset=["Datetime_Keluar"])
                
                # Kembalikan ke wujud teks asli biar Web/DB nggak pusing
                df["Tanggal_Keluar"] = df["Datetime_Keluar"].dt.strftime('%d/%m/%Y %H:%M')

            # --- Proses untuk Tanggal_Masuk (Jika ada di SAP) ---
            if 'Tanggal_Masuk' in df.columns and 'Jam_Masuk' in df.columns:
                tgl_m_str = df["Tanggal_Masuk"].astype(str).str[:10]
                jam_m_str = df["Jam_Masuk"].astype(str).str[-8:]
                
                dt_masuk = pd.to_datetime(tgl_m_str + " " + jam_m_str, dayfirst=True, errors="coerce")
                
                # Kembalikan ke wujud teks asli
                df["Tanggal_Masuk"] = dt_masuk.dt.strftime('%d/%m/%Y %H:%M')

            df = df.sort_values(["Nopol","Datetime_Keluar"]).reset_index(drop=True)
            bt = df["Nopol"] != df["Nopol"].shift(1)
            bw = (df["Datetime_Keluar"]-df["Datetime_Keluar"].shift(1)).dt.total_seconds()/60 > 30
            df["truck_event_id"] = (bt|bw).cumsum()
            df["is_master_weight"] = (~df.duplicated(subset=["truck_event_id"])).astype(int)
            if "Nomor_SPT" in df.columns:
                df["reference_spt"] = df.groupby("truck_event_id")["Nomor_SPT"].transform("first")
            df["event_type"] = "OUT"

            # ====================================================
            # 🛡️ TAMENG MYSQL ERROR 1366 (AUTO-CONVERT STRING KOSONG KE 0)
            # ====================================================
            # Daftar kolom di tabel MySQL lu yang wajib Angka (INT / Float)
            kolom_angka = [
                'Kode_Pos_Insentif_Jarak', 'Jumlah_Karung', 'NoSystem', 
                'Shift', 'YEARSJ', 'MONTHSJ', 'Nomor_SPTA', 'Nomor_GRPO',
                'Qty_SJ', 'Qty_SPMSPB', 'Berat_Masuk', 'Berat_Keluar', 'Berat_rata2_Karung'
            ]
            
            for col in kolom_angka:
                if col in df.columns:
                    # Bersihkan koma ribuan (kalau ada), ubah ke numeric, yang kosong/error jadi 0
                    df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
                    
                    # Konversi khusus untuk kolom yang murni INT (Tanpa desimal)
                    if col in ['Kode_Pos_Insentif_Jarak', 'Jumlah_Karung', 'NoSystem', 'Shift', 'YEARSJ', 'MONTHSJ']:
                        df[col] = df[col].astype(int)
            # ====================================================

            # ====================================================
            # 🚨 ALARM DUPLIKAT: JANGAN ASAL TENDANG, KASIH TAHU USER!
            # ====================================================
            if "NoSystem" in df.columns:
                # Cari data yang NoSystem-nya muncul lebih dari 1 kali di layar
                df_valid = df[df["NoSystem"].astype(str).str.strip() != ""] # Abaikan yang kosong
                duplikat = df_valid[df_valid.duplicated(subset=["NoSystem"], keep=False)]
                
                if not duplikat.empty:
                    contoh_dup = []
                    # Ambil baris-baris yang kembar buat ditampilin di popup
                    for _, r in duplikat.head(6).iterrows():
                        nopol = r.get("Nopol", "?")
                        nosys = r.get("NoSystem", "?")
                        try:
                            no_tabel = int(float(r.get("No", 0)))
                        except:
                            no_tabel = r.get("No", "?")
                        contoh_dup.append(f"  • No. Tabel: {no_tabel} | Nopol: {nopol} (NoSystem: {nosys})")
                    
                    msg = (f"🛑 UPLOAD DIBATALKAN!\n\n"
                           f"SAP MENGELUARKAN DATA KEMBAR!\n"
                           f"Ditemukan {len(duplikat)} baris yang memiliki 'NoSystem' kembar/identik.\n\n"
                           f"Baris yang bentrok:\n" + "\n".join(contoh_dup) + "\n\n"
                           f"TINDAKAN:\n"
                           f"Ketik NoSystem atau No. Tabel di kotak SEARCH untuk menginvestigasi data tersebut.\n"
                           f"Silakan perbaiki/hapus baris yang salah, lalu klik UPLOAD kembali.")
                    
                    messagebox.showerror("Terdeteksi Data Kembar", msg)
                    self._set_status("Menunggu Koreksi", "warn")
                    self._log("ERROR", f"Upload dibatalkan! Ada {len(duplikat)} baris NoSystem kembar.")
                    return # 🛑 STOP UPLOAD! BIAR USER YANG MENGHAKIMI DATANYA!
            # ====================================================

            # --- MESIN ABS: JADIKAN POSITIF MUTLAK (pakai abs() bukan hapus karakter '-') ---
            for col in [c for c in df.columns if any(x in c for x in ["Qty","Berat","Jumlah","Persentase"])]:
                s = df[col].astype(str)
                s = s.str.replace(',', '', regex=False)  # Buang koma ribuan
                s = s.str.replace('(', '-', regex=False).str.replace(')', '', regex=False)  # Kurung akuntansi → minus
                df[col] = pd.to_numeric(s.str.strip(), errors="coerce").abs()  # Konversi + ABS
            
            df = df.replace({np.nan: None, pd.NaT: None})

            # ====================================================
            # RADAR DETEKTIF: Cari Shift yang Kosong / Bukan Angka
            # ====================================================
            bad_shift = df[df["Shift"].astype(str).str.strip().isin(["", "nan", "None"])]
            
            if not bad_shift.empty:
                self._log("WARNING", f"🚨 DETEKTIF: Ketemu {len(bad_shift)} baris dengan Shift kosong!")
                # Tampilkan maksimal 10 baris pertama yang error biar log nggak kepenuhan
                for idx, row in bad_shift.head(10).iterrows():
                    no_urut = row.get("No", "?")
                    nopol = row.get("Nopol", "?")
                    supir = row.get("Supir", "?")
                    isi = repr(row.get("Shift", "")) # repr() biar kelihatan kalau teksnya isinya cuma spasi
                    self._log("ERROR", f"► Nopol: {nopol} | Supir: {supir} | Shift aslinya: {isi} | (Cek No Urut Layar: {no_urut})")
                
                messagebox.showerror("Data Nyangkut", f"Ketemu {len(bad_shift)} data Shift kosong!\nCek Log di bawah untuk detailnya.")
                return # HENTIKAN UPLOAD, biar lu bisa ngecek dulu!
            # ====================================================

            self._log("INFO", f"Mencoba koneksi ke database di {self.db_host}...")
            conn = pymysql.connect(host=self.db_host, user="wb_rmi",
                                   password="12345678", database="timbangan", autocommit=False)
            cursor = conn.cursor()

            cursor.execute("SHOW COLUMNS FROM data_timbang")
            db_cols   = [x[0] for x in cursor.fetchall()]
            df_up     = df[[c for c in df.columns if c in db_cols]]

            cursor.execute("SELECT Nomor_SPMSPB, NoSystem FROM data_timbang")
            def ck(k):
                if pd.isna(k) or k is None: return ""
                s = str(k).strip()
                return s[:-2] if s.endswith(".0") else s
            db_keys = set((ck(r[0]), ck(r[1])) for r in cursor.fetchall())

            E = sum(1 for v in df_up[["Nomor_SPMSPB","NoSystem"]].to_numpy()
                    if (ck(v[0]),ck(v[1])) in db_keys)
            N = len(df_up); I = N - E

            cols_s = ", ".join(f"`{c}`" for c in df_up.columns)
            vals_s = ", ".join(["%s"]*len(df_up.columns))
            upd_s  = ", ".join(f"`{c}`=VALUES(`{c}`)" for c in df_up.columns
                               if c not in ["Nomor_SPT","Nomor_SPTA"])
            sql = f"INSERT INTO data_timbang ({cols_s}) VALUES ({vals_s}) ON DUPLICATE KEY UPDATE {upd_s}"
            cursor.executemany(sql, [tuple(r) for r in df_up.to_numpy()])
            R = cursor.rowcount
            conn.commit()

            U = max(0, int((R-I)/2) if (R-I)>0 else 0)
            S = max(0, E-U)
            elapsed = round(time.time()-start, 2)

            self._log("SUCCESS", f"Upload selesai {elapsed}s — Baru:{I} Timpa:{U} Skip:{S} Total:{N}")
            self._set_status(f"Uploaded {N} rows ({elapsed}s)", "ok")
            self._update_footer(total=N, pending=0, ready=0, uploaded=N)
            self.lbl_pending.config(text="· 0 rows")

            messagebox.showinfo("Berhasil",
                f"✅ Baru   : {I}\n🔄 Timpa  : {U}\n⏸ Skip   : {S}\n────────\n📦 Total  : {N}")
            self.clear_table()

        except Exception as e:
            if conn: conn.rollback()
            messagebox.showerror("Error DB", str(e))
            self._set_status("Upload gagal!", "err")
            self._log("ERROR", str(e))
        finally:
            if cursor: cursor.close()
            if conn: conn.close()

    # ── CLEAR ────────────────────────────────────
    def clear_table(self):
        self.tree.delete(*self.tree.get_children())
        self._init_columns()
        self.current_df = None
        self.lbl_row_count.config(text="")
        self.lbl_pending.config(text="· 0 rows")
        self._set_status("Ready", "ok")
        self._update_footer()
        self._log("INFO", "Layar dibersihkan.")

    def _show_options(self):
        if self.current_df is None or self.current_df.empty:
            messagebox.showwarning("Kosong", "Tidak ada data untuk dicari.")
            return

        search_win = tk.Toplevel(self)
        search_win.title("Cari Data")
        search_win.geometry("350x250")
        search_win.configure(bg=BG)
        search_win.transient(self)
        search_win.grab_set()

        wrap, inner = shadow_frame(search_win, bg=SURFACE, border=BORDER, bw=2)
        wrap.pack(fill="both", expand=True, padx=10, pady=10)

        tk.Label(inner, text="Cari Berdasarkan:", bg=SURFACE, fg=TXT_DIM, font=FT_B).pack(pady=(15, 2))
        
        search_options = ["No", "Nopol", "Supir", "Nomor_Surat_Jalan", "Nomor_SPMSPB", "Nomor_SPT"]
        selected_option = tk.StringVar()
        selected_option.set(search_options[0])

        cb_opt = ttk.Combobox(inner, textvariable=selected_option, values=search_options, state="readonly", font=FT)
        cb_opt.pack(pady=5)

        tk.Label(inner, text="Kata Kunci:", bg=SURFACE, fg=TXT_DIM, font=FT_B).pack(pady=(10, 2))
        
        entry_keyword = tk.Entry(inner, font=FT, bg="#1A1A1A", fg=TXT, insertbackground=TXT, relief="flat")
        entry_keyword.pack(pady=5, padx=20, fill="x", ipady=4)
        entry_keyword.focus_set()

        def do_search(event=None):
            col = selected_option.get()
            keyword = entry_keyword.get().strip().lower()

            if not keyword:
                return

            found = False
            try:
                col_idx = SAP_COLS.index(col)
                for item in self.tree.get_children():
                    row_vals = self.tree.item(item, "values")
                    if col_idx < len(row_vals):
                        val = str(row_vals[col_idx]).strip().lower()
                        if keyword == val or keyword in val:
                            # Tampilkan dan highlight baris yang ketemu
                            self.tree.selection_set(item)
                            self.tree.focus(item)
                            self.tree.see(item)
                            found = True
                            search_win.destroy()
                            self._log("INFO", f"Data ketemu: {col} = {val}")
                            break
            except Exception as e:
                self._log("ERROR", f"Error pencarian: {e}")
            
            if not found:
                messagebox.showinfo("Pencarian", f"Data dengan {col} '{keyword}' tidak ditemukan.", parent=search_win)

        entry_keyword.bind("<Return>", do_search)

        btn_wrap = tk.Frame(inner, bg=SURFACE)
        btn_wrap.pack(pady=15)
        neo_btn(btn_wrap, "🔍 CARI", PRP, "white", do_search, font=FT_B, px=15, py=6).pack()

if __name__ == "__main__":
    app = App()
    app.mainloop()