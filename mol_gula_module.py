"""
Modul Input Harian Molasses & Gula
===================================
File terpisah agar tidak mengganggu app.py.
Dipanggil via:  ModuleMolGula(parent_tk, db_host)
"""

import tkinter as tk
from tkinter import ttk, messagebox
import pymysql
from datetime import datetime, date, timedelta

# ── Import palette & helpers dari theme.py ────────
from theme import (
    BG, PANEL, SURFACE, BORDER,
    YEL, TEAL, PINK, ORG, GRN, RED, PRP,
    TXT, TXT_DIM, TXT_YEL, TXT_GRN, TXT_RED, TXT_ORG,
    FT, FT_B, FT_H, FT_XL, FT_LG,
    neo_btn, shadow_frame, _darken,
)

# ── Konstanta lokal ──────────────────────────────
# Database configuration is now passed via db_config

CYAN   = "#00E5FF"
AMBER  = "#FFAB00"
LIME   = "#76FF03"

# Default list jenis reject (in-memory, bisa ditambah user via tombol '+')
DEFAULT_REJECT_TYPES = [
    "Mix Colour / Metal Detector",
    "Off Colour",
    "Cleaning Bin",
    "Lumping",
    "Flashing",
    "Sapon Bagging",
]


# ═════════════════════════════════════════════════
#  CLASS UTAMA
# ═════════════════════════════════════════════════
class ModuleMolGula(tk.Toplevel):
    """Window input harian Molasses & Gula."""

    def __init__(self, parent, db_config):
        super().__init__(parent)
        self.parent = parent
        self.db_config = db_config

        self.title("MODUL INPUT — Molasses & Gula")
        self.geometry("1200x820")
        self.minsize(1050, 700)
        self.configure(bg=BG)
        self.transient(parent)

        # Set icon sama dengan parent
        try:
            self.iconbitmap(default=parent.iconbitmap())
        except Exception:
            pass

        # In-memory list jenis reject (bisa ditambah user)
        # In-memory list jenis reject (akan di-load dari DB)
        self._reject_types = []

        # Gudang luar mapping {nama_gudang: id}
        self._gudang_luar_map = {}

        self._setup_notebook_style()
        self._build_ui()
        self._load_gudang_luar_list()
        self._load_jenis_reject_list()
        self._refresh_stock_display()
        self._refresh_delivery_table()

    # ── STYLE NOTEBOOK DARK ─────────────────────
    def _setup_notebook_style(self):
        s = ttk.Style()
        s.configure("Dark.TNotebook", background=BG, borderwidth=0,
                     tabmargins=[4, 4, 2, 0])
        s.configure("Dark.TNotebook.Tab",
                     background=SURFACE, foreground=TXT_DIM,
                     font=FT_B, padding=[16, 8],
                     borderwidth=0)
        s.map("Dark.TNotebook.Tab",
              background=[("selected", PANEL), ("active", BORDER)],
              foreground=[("selected", YEL), ("active", TXT)],
              expand=[("selected", [1, 1, 1, 0])])

    # ── BUILD UI ────────────────────────────────
    def _build_ui(self):
        # ── Header ──
        hdr = tk.Frame(self, bg=BG, height=56)
        hdr.pack(fill="x", padx=0, pady=0)
        hdr.pack_propagate(False)

        tk.Label(hdr, text="  🧪 MODUL INPUT — MOLASSES & GULA",
                 font=FT_XL, bg=BG, fg=YEL).pack(side="left", padx=12, pady=12)

        tk.Label(hdr, text=f"🌐 {self.db_config.get('host', '127.0.0.1')}",
                 font=FT_B, bg=BG, fg=TXT_DIM).pack(side="right", padx=16, pady=12)

        # Aksen garis
        tk.Frame(self, bg=ORG, height=3).pack(fill="x")

        # ── Body: Left (Notebook) + Right (Stock Summary) ──
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=8, pady=6)

        # LEFT — Notebook forms
        left = tk.Frame(body, bg=BG)
        left.pack(side="left", fill="both", expand=True, padx=(0, 4))

        self.notebook = ttk.Notebook(left, style="Dark.TNotebook")
        self.notebook.pack(fill="both", expand=True)

        self._build_tab_penerimaan()
        self._build_tab_delivery()
        self._build_tab_reject()

        # RIGHT — Stock Summary
        right = tk.Frame(body, bg=BG, width=320)
        right.pack(side="right", fill="y", padx=(4, 0))
        right.pack_propagate(False)
        self._build_stock_panel(right)

        # ── Mini Log ──
        self._build_mini_log()

    # ════════════════════════════════════════════
    #  TAB 1: PENERIMAAN & PRODUKSI
    # ════════════════════════════════════════════
    def _build_tab_penerimaan(self):
        tab = tk.Frame(self.notebook, bg=BG)
        self.notebook.add(tab, text="  📦  Penerimaan & Produksi  ")

        # Scrollable canvas
        canvas = tk.Canvas(tab, bg=BG, highlightthickness=0, bd=0)
        vsb = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=BG)
        scroll_frame.bind("<Configure>",
                          lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        cw = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=vsb.set)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(cw, width=e.width))
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        # Bind mousewheel
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        # ── Section A: Molasses Penerimaan ──
        self._section_header(scroll_frame, "🛢  PENERIMAAN MOLASSES  (Per Shift)", TEAL)

        fa = tk.Frame(scroll_frame, bg=PANEL)
        fa.pack(fill="x", padx=10, pady=(0, 10))

        row_a = tk.Frame(fa, bg=PANEL)
        row_a.pack(fill="x", padx=16, pady=(14, 6))

        self.mol_pen_tgl = self._labeled_entry(row_a, "Tanggal", 12,
                                                default=date.today().strftime("%Y-%m-%d"))
        self.mol_pen_shift = self._labeled_combo(row_a, "Shift", ["1", "2", "3"], 6)

        row_a2 = tk.Frame(fa, bg=PANEL)
        row_a2.pack(fill="x", padx=16, pady=6)

        self.mol_pen_raw = self._labeled_entry(row_a2, "Raw Sugar (ton)", 12, default="0")
        self.mol_pen_cane = self._labeled_entry(row_a2, "Cane Tebu (ton)", 12, default="0")
        self.mol_pen_tangki = self._labeled_combo(row_a2, "Tangki Tujuan",
                                                   ["Tank A", "Tank B"], 10)

        btn_a = tk.Frame(fa, bg=PANEL)
        btn_a.pack(fill="x", padx=16, pady=(4, 14))
        neo_btn(btn_a, "💾  SIMPAN PENERIMAAN MOL", TEAL, "white",
                self._save_mol_penerimaan, font=FT_B, px=14, py=7,
                border="#000").pack(side="left")

        # ── Section B: Gula Penerimaan ──
        self._section_header(scroll_frame, "🍬  PENERIMAAN GULA  (Per Shift)", PINK)

        fb = tk.Frame(scroll_frame, bg=PANEL)
        fb.pack(fill="x", padx=10, pady=(0, 10))

        row_b = tk.Frame(fb, bg=PANEL)
        row_b.pack(fill="x", padx=16, pady=(14, 6))

        self.gula_pen_tgl = self._labeled_entry(row_b, "Tanggal", 12,
                                                 default=date.today().strftime("%Y-%m-%d"))
        self.gula_pen_shift = self._labeled_combo(row_b, "Shift", ["1", "2", "3"], 6)

        row_b2 = tk.Frame(fb, bg=PANEL)
        row_b2.pack(fill="x", padx=16, pady=6)

        self.gula_pen_gkm_c = self._labeled_entry(row_b2, "GKM Crushing (ton)", 14, default="0")
        self.gula_pen_gkm_m = self._labeled_entry(row_b2, "GKM Melting (ton)", 14, default="0")

        row_b3 = tk.Frame(fb, bg=PANEL)
        row_b3.pack(fill="x", padx=16, pady=6)

        self.gula_pen_gkb_c = self._labeled_entry(row_b3, "GKB Crushing (ton)", 14, default="0")
        self.gula_pen_gkb_m = self._labeled_entry(row_b3, "GKB Melting (ton)", 14, default="0")

        btn_b = tk.Frame(fb, bg=PANEL)
        btn_b.pack(fill="x", padx=16, pady=(4, 14))
        neo_btn(btn_b, "💾  SIMPAN PENERIMAAN GULA", PINK, "white",
                self._save_gula_penerimaan, font=FT_B, px=14, py=7,
                border="#000").pack(side="left")

    # ════════════════════════════════════════════
    #  TAB 2: DELIVERY
    # ════════════════════════════════════════════
    def _build_tab_delivery(self):
        tab = tk.Frame(self.notebook, bg=BG)
        self.notebook.add(tab, text="  🚚  Delivery  ")

        canvas = tk.Canvas(tab, bg=BG, highlightthickness=0, bd=0)
        vsb = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=BG)
        scroll_frame.bind("<Configure>",
                          lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        cw = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=vsb.set)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(cw, width=e.width))
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        # ── Section A: Molasses Delivery ──
        self._section_header(scroll_frame, "🛢  DELIVERY MOLASSES  (Harian)", TEAL)

        fa = tk.Frame(scroll_frame, bg=PANEL)
        fa.pack(fill="x", padx=10, pady=(0, 10))

        row_a = tk.Frame(fa, bg=PANEL)
        row_a.pack(fill="x", padx=16, pady=(14, 6))

        self.mol_del_tgl = self._labeled_entry(row_a, "Tanggal", 12,
                                                default=date.today().strftime("%Y-%m-%d"))
        self.mol_del_plan = self._labeled_entry(row_a, "Plan Delivery (ton)", 14, default="0")

        row_a2 = tk.Frame(fa, bg=PANEL)
        row_a2.pack(fill="x", padx=16, pady=6)

        self.mol_del_act_a = self._labeled_entry(row_a2, "Actual Tank A (ton)", 14, default="0")
        self.mol_del_act_b = self._labeled_entry(row_a2, "Actual Tank B (ton)", 14, default="0")

        row_a3 = tk.Frame(fa, bg=PANEL)
        row_a3.pack(fill="x", padx=16, pady=6)

        self.mol_del_truck = self._labeled_entry(row_a3, "Jml Truck", 8, default="0")
        self.mol_del_next = self._labeled_entry(row_a3, "Next Schedule", 12, default="0")

        btn_a = tk.Frame(fa, bg=PANEL)
        btn_a.pack(fill="x", padx=16, pady=(4, 14))
        neo_btn(btn_a, "💾  SIMPAN DELIVERY MOL", TEAL, "white",
                self._save_mol_delivery, font=FT_B, px=14, py=7,
                border="#000").pack(side="left")

        # ── Section B: Gula Delivery (DIPERLUAS) ──
        self._section_header(scroll_frame, "🍬  DELIVERY GULA  (Harian)", PINK)

        fb = tk.Frame(scroll_frame, bg=PANEL)
        fb.pack(fill="x", padx=10, pady=(0, 10))

        # Baris 1: Tanggal + Plan Delivery
        row_b1 = tk.Frame(fb, bg=PANEL)
        row_b1.pack(fill="x", padx=16, pady=(14, 6))

        self.gula_del_tgl = self._labeled_entry(row_b1, "Tanggal", 12,
                                                 default=date.today().strftime("%Y-%m-%d"))
        self.gula_del_plan = self._labeled_entry(row_b1, "Plan Delivery (ton)", 14, default="0")

        # Baris 2: Delivery GKM + Delivery GKB
        row_b2 = tk.Frame(fb, bg=PANEL)
        row_b2.pack(fill="x", padx=16, pady=6)

        self.gula_del_gkm = self._labeled_entry(row_b2, "Delivery GKM (ton)", 14, default="0")
        self.gula_del_gkb = self._labeled_entry(row_b2, "Delivery GKB (ton)", 14, default="0")

        # Baris 3: Tonage Container + Jumlah Truck
        row_b3 = tk.Frame(fb, bg=PANEL)
        row_b3.pack(fill="x", padx=16, pady=6)

        self.gula_del_tonage = self._labeled_entry(row_b3, "Tonage Container (ton)", 14, default="0")
        self.gula_del_truck = self._labeled_entry(row_b3, "Jumlah Truck", 8, default="0")

        # Baris 4: Gudang Luar Tujuan (Combobox + tombol '+')
        row_b4 = tk.Frame(fb, bg=PANEL)
        row_b4.pack(fill="x", padx=16, pady=6)

        grp_gl = tk.Frame(row_b4, bg=PANEL)
        grp_gl.pack(side="left", padx=(0, 16))
        tk.Label(grp_gl, text="Gudang Luar Tujuan  (opsional)",
                 font=FT_B, bg=PANEL, fg=TXT_DIM).pack(anchor="w")

        gl_row = tk.Frame(grp_gl, bg=PANEL)
        gl_row.pack(anchor="w")

        self.gula_del_gudang = ttk.Combobox(gl_row, values=[""],
                                             state="readonly", font=FT, width=26)
        self.gula_del_gudang.pack(side="left", ipady=3)
        self.gula_del_gudang.current(0)

        add_gl_btn = tk.Button(gl_row, text=" ＋ ", font=FT_B,
                               bg=SURFACE, fg=GRN,
                               activebackground=BORDER, activeforeground=GRN,
                               relief="flat", cursor="hand2", bd=0,
                               command=self._add_gudang_luar)
        add_gl_btn.pack(side="left", padx=(6, 0), ipady=2)

        # Baris 5: Actual Delivery RMI + Actual Temp Wh
        row_b5 = tk.Frame(fb, bg=PANEL)
        row_b5.pack(fill="x", padx=16, pady=6)

        self.gula_del_actual = self._labeled_entry(row_b5, "Actual Delivery RMI (ton)", 14, default="0")
        self.gula_del_act_gl = self._labeled_entry(row_b5, "Actual Temp Wh (ton)", 14, default="0")

        btn_b = tk.Frame(fb, bg=PANEL)
        btn_b.pack(fill="x", padx=16, pady=(8, 14))
        neo_btn(btn_b, "💾  SIMPAN DELIVERY GULA", PINK, "white",
                self._save_gula_delivery, font=FT_B, px=14, py=7,
                border="#000").pack(side="left")

        # ── Treeview: Riwayat Delivery Gula ──
        self._section_header(scroll_frame, "📋  RIWAYAT DELIVERY GULA", AMBER)

        tw_del = tk.Frame(scroll_frame, bg=BORDER, padx=2, pady=2)
        tw_del.pack(fill="x", padx=10, pady=(0, 10))

        tv_del_inner = tk.Frame(tw_del, bg=PANEL)
        tv_del_inner.pack(fill="both", expand=True)

        del_cols = ("ID", "Tanggal", "GKM (ton)", "GKB (ton)",
                    "Actual RMI", "Plan Del", "Container", "Truck",
                    "Gudang Luar", "Actual GL")

        vsb_del = ttk.Scrollbar(tv_del_inner, orient="vertical")
        self.del_tree = ttk.Treeview(tv_del_inner, columns=del_cols, show="headings",
                                      style="T.Treeview", height=6,
                                      yscrollcommand=vsb_del.set)
        vsb_del.config(command=self.del_tree.yview)

        del_widths = {"ID": 40, "Tanggal": 90, "GKM (ton)": 80, "GKB (ton)": 80,
                      "Actual RMI": 85, "Plan Del": 80, "Container": 80,
                      "Truck": 50, "Gudang Luar": 130, "Actual GL": 80}
        for c in del_cols:
            self.del_tree.heading(c, text=c)
            self.del_tree.column(c, width=del_widths.get(c, 80),
                                  minwidth=40, anchor="w", stretch=False)

        self.del_tree.tag_configure("odd", background="#1A1A1A")
        self.del_tree.tag_configure("even", background="#212121")

        vsb_del.pack(side="right", fill="y")
        self.del_tree.pack(fill="both", expand=True)

    # ════════════════════════════════════════════
    #  TAB 3: LOG REJECT GULA
    # ════════════════════════════════════════════
    def _build_tab_reject(self):
        tab = tk.Frame(self.notebook, bg=BG)
        self.notebook.add(tab, text="  ⚠  Log Reject Gula  ")

        self._section_header(tab, "⚠  LOG REJECT GULA  (Detail)", RED)

        fa = tk.Frame(tab, bg=PANEL)
        fa.pack(fill="x", padx=10, pady=(0, 10))

        # Baris 1: Tanggal + Shift
        row1 = tk.Frame(fa, bg=PANEL)
        row1.pack(fill="x", padx=16, pady=(14, 6))

        self.rej_tgl = self._labeled_entry(row1, "Tanggal", 12,
                                            default=date.today().strftime("%Y-%m-%d"))
        self.rej_shift = self._labeled_combo(row1, "Shift", ["1", "2", "3"], 6)

        # Baris 2: Kategori Transaksi + Jenis Gula
        row2 = tk.Frame(fa, bg=PANEL)
        row2.pack(fill="x", padx=16, pady=6)

        self.rej_kategori = self._labeled_combo(row2, "Kategori Transaksi",
                                                 ["RECEIVED", "SUSUT/DOWNGRADE"], 18)
        self.rej_jenis_gula = self._labeled_combo(row2, "Jenis Gula",
                                                   ["GKM", "GKB"], 8)

        # Baris 3: Jenis Reject (Combobox + '+') + Jumlah (ton)
        row3 = tk.Frame(fa, bg=PANEL)
        row3.pack(fill="x", padx=16, pady=6)

        # Jenis Reject — Combobox dengan tombol '+'
        grp_jr = tk.Frame(row3, bg=PANEL)
        grp_jr.pack(side="left", padx=(0, 16))
        tk.Label(grp_jr, text="Jenis Reject", font=FT_B,
                 bg=PANEL, fg=TXT_DIM).pack(anchor="w")

        jr_row = tk.Frame(grp_jr, bg=PANEL)
        jr_row.pack(anchor="w")

        self.rej_jenis_reject = ttk.Combobox(jr_row, values=self._reject_types,
                                              state="readonly", font=FT, width=26)
        self.rej_jenis_reject.pack(side="left", ipady=3)
        if self._reject_types:
            self.rej_jenis_reject.current(0)

        add_jr_btn = tk.Button(jr_row, text=" ＋ ", font=FT_B,
                               bg=SURFACE, fg=GRN,
                               activebackground=BORDER, activeforeground=GRN,
                               relief="flat", cursor="hand2", bd=0,
                               command=self._add_jenis_reject)
        add_jr_btn.pack(side="left", padx=(6, 0), ipady=2)

        self.rej_jumlah = self._labeled_entry(row3, "Jumlah (ton)", 12, default="0")

        # Baris 4: Keterangan (lebar)
        row4 = tk.Frame(fa, bg=PANEL)
        row4.pack(fill="x", padx=16, pady=6)

        grp = tk.Frame(row4, bg=PANEL)
        grp.pack(side="left", padx=(0, 16))
        tk.Label(grp, text="Keterangan", font=FT_B, bg=PANEL, fg=TXT_DIM).pack(anchor="w")
        self.rej_ket = tk.Entry(grp, font=FT, bg="#1A1A1A", fg=TXT,
                                insertbackground=TXT, relief="flat", width=50)
        self.rej_ket.pack(ipady=5)

        btn_r = tk.Frame(fa, bg=PANEL)
        btn_r.pack(fill="x", padx=16, pady=(8, 14))
        neo_btn(btn_r, "💾  SIMPAN LOG REJECT", RED, "white",
                self._save_gula_reject, font=FT_B, px=14, py=7,
                border="#000").pack(side="left")

        # ── Tabel riwayat reject hari ini ──
        self._section_header(tab, "📋  RIWAYAT REJECT HARI INI", AMBER)

        tw = tk.Frame(tab, bg=BORDER, padx=2, pady=2)
        tw.pack(fill="both", expand=True, padx=10, pady=(0, 6))

        tv_inner = tk.Frame(tw, bg=PANEL)
        tv_inner.pack(fill="both", expand=True)

        rej_cols = ("ID", "Tanggal", "Shift", "Kategori", "Jenis Gula",
                    "Jenis Reject", "Jumlah (ton)", "Keterangan")

        vsb = ttk.Scrollbar(tv_inner, orient="vertical")
        self.rej_tree = ttk.Treeview(tv_inner, columns=rej_cols, show="headings",
                                      style="T.Treeview", height=6,
                                      yscrollcommand=vsb.set)
        vsb.config(command=self.rej_tree.yview)

        col_widths = {"ID": 40, "Tanggal": 90, "Shift": 45, "Kategori": 130,
                      "Jenis Gula": 80, "Jenis Reject": 180,
                      "Jumlah (ton)": 90, "Keterangan": 180}
        for c in rej_cols:
            self.rej_tree.heading(c, text=c)
            self.rej_tree.column(c, width=col_widths.get(c, 100),
                                  minwidth=40, anchor="w", stretch=False)

        self.rej_tree.tag_configure("odd", background="#1A1A1A")
        self.rej_tree.tag_configure("even", background="#212121")

        vsb.pack(side="right", fill="y")
        self.rej_tree.pack(fill="both", expand=True)

    # ════════════════════════════════════════════
    #  STOCK SUMMARY PANEL (RIGHT)
    # ════════════════════════════════════════════
    def _build_stock_panel(self, parent):
        tk.Label(parent, text="📊 RINGKASAN STOK", font=FT_H,
                 bg=BG, fg=YEL).pack(pady=(6, 8))

        tk.Label(parent, text=f"Tanggal: {date.today().strftime('%d/%m/%Y')}",
                 font=FT, bg=BG, fg=TXT_DIM).pack(pady=(0, 6))

        # ── Card: Molasses ──
        self._card_header(parent, "🛢  STOK MOLASSES (ton)", TEAL)
        cm = tk.Frame(parent, bg=PANEL)
        cm.pack(fill="x", padx=6, pady=(0, 6))

        self.lbl_mol_a = self._stock_row(cm, "Tank A :", "0.00")
        self.lbl_mol_b = self._stock_row(cm, "Tank B :", "0.00")

        tk.Frame(cm, bg=BORDER, height=1).pack(fill="x", padx=12, pady=3)
        self.lbl_mol_total = self._stock_row(cm, "TOTAL  :", "0.00", fg=YEL)
        tk.Frame(cm, bg=PANEL, height=4).pack()

        # ── Card: Gula ──
        self._card_header(parent, "🍬  STOK GULA (ton)", PINK)
        cg = tk.Frame(parent, bg=PANEL)
        cg.pack(fill="x", padx=6, pady=(0, 6))

        self.lbl_gula_gkm = self._stock_row(cg, "GKM    :", "0.00")
        self.lbl_gula_gkb = self._stock_row(cg, "GKB    :", "0.00")

        tk.Frame(cg, bg=BORDER, height=1).pack(fill="x", padx=12, pady=3)
        self.lbl_gula_total = self._stock_row(cg, "TOTAL  :", "0.00", fg=YEL)
        tk.Frame(cg, bg=PANEL, height=4).pack()

        # ── Card: Reject (satuan: ton) ──
        self._card_header(parent, "⚠  REJECT HARI INI (ton)", RED)
        cr = tk.Frame(parent, bg=PANEL)
        cr.pack(fill="x", padx=6, pady=(0, 6))

        self.lbl_rej_gkm = self._stock_row(cr, "GKM    :", "0.00")
        self.lbl_rej_gkb = self._stock_row(cr, "GKB    :", "0.00")

        tk.Frame(cr, bg=BORDER, height=1).pack(fill="x", padx=12, pady=3)
        self.lbl_rej_total = self._stock_row(cr, "TOTAL  :", "0.00", fg=YEL)
        tk.Frame(cr, bg=PANEL, height=4).pack()

        # ── Card: Gudang Luar (BARU) ──
        self._card_header(parent, "🏭  GUDANG LUAR (ton)", PRP)
        cgl = tk.Frame(parent, bg=PANEL)
        cgl.pack(fill="x", padx=6, pady=(0, 6))

        self.lbl_gudang_total = self._stock_row(cgl, "TOTAL  :", "0.00", fg=PRP)
        tk.Frame(cgl, bg=PANEL, height=4).pack()

        # Refresh button
        neo_btn(parent, "🔄  REFRESH STOK", PRP, "white",
                self._refresh_stock_display, font=FT_B, px=14, py=7,
                border="#000").pack(pady=8)

    # ════════════════════════════════════════════
    #  MINI LOG
    # ════════════════════════════════════════════
    def _build_mini_log(self):
        wrap = tk.Frame(self, bg=BORDER, padx=2, pady=2)
        wrap.pack(fill="x", padx=8, pady=(2, 6))

        inner = tk.Frame(wrap, bg="#0D0D0D")
        inner.pack(fill="both", expand=True)

        lh = tk.Frame(inner, bg="#0A0A0A")
        lh.pack(fill="x")
        tk.Label(lh, text="  ▸ MODULE LOG", font=FT_B,
                 bg="#0A0A0A", fg=TXT_DIM).pack(side="left", padx=10, pady=4)

        self.mini_log = tk.Text(inner, height=4, bg="#0D0D0D", fg=TXT, font=FT,
                                relief="flat", state="disabled", wrap="word",
                                highlightthickness=0, bd=0)
        self.mini_log.pack(fill="x", padx=6, pady=4)

        self.mini_log.tag_configure("T", foreground="#3A6EA5")
        self.mini_log.tag_configure("OK", foreground=TXT_GRN)
        self.mini_log.tag_configure("WARN", foreground=TXT_ORG)
        self.mini_log.tag_configure("ERR", foreground=TXT_RED)
        self.mini_log.tag_configure("MSG", foreground="#9A9A9A")

    def _mlog(self, level, msg):
        """Tulis ke mini-log."""
        tag_map = {"OK": "OK", "WARN": "WARN", "ERR": "ERR"}
        tag = tag_map.get(level, "MSG")
        now = datetime.now().strftime("%H:%M:%S")
        self.mini_log.config(state="normal")
        self.mini_log.insert("end", f"[{now}] ", "T")
        self.mini_log.insert("end", f"{level:<6}", tag)
        self.mini_log.insert("end", msg + "\n", "MSG")
        self.mini_log.config(state="disabled")
        self.mini_log.see("end")

    # ════════════════════════════════════════════
    #  UI HELPERS
    # ════════════════════════════════════════════
    def _section_header(self, parent, text, accent_color):
        """Bar judul section dengan aksen warna."""
        bar = tk.Frame(parent, bg=accent_color, height=2)
        bar.pack(fill="x", padx=10, pady=(10, 0))

        hdr = tk.Frame(parent, bg="#0A0A0A")
        hdr.pack(fill="x", padx=10)
        tk.Label(hdr, text=f"  {text}", font=FT_H,
                 bg="#0A0A0A", fg=accent_color).pack(side="left", padx=6, pady=8)

    def _card_header(self, parent, text, accent_color):
        """Header kecil untuk stock card."""
        f = tk.Frame(parent, bg=accent_color, height=28)
        f.pack(fill="x", padx=6, pady=(4, 0))
        f.pack_propagate(False)
        tk.Label(f, text=f" {text}", font=FT_B,
                 bg=accent_color, fg="#0A0A0A").pack(side="left", padx=6, pady=3)

    def _stock_row(self, parent, label, value, fg=TXT):
        """Baris label:value di stock card."""
        row = tk.Frame(parent, bg=PANEL)
        row.pack(fill="x", padx=12, pady=2)
        tk.Label(row, text=label, font=FT_B, bg=PANEL, fg=TXT_DIM,
                 width=10, anchor="w").pack(side="left")
        lbl = tk.Label(row, text=value, font=FT_LG, bg=PANEL, fg=fg)
        lbl.pack(side="right", padx=4)
        return lbl

    def _labeled_entry(self, parent, label, width=12, default=""):
        """Entry dengan label di atas."""
        grp = tk.Frame(parent, bg=PANEL)
        grp.pack(side="left", padx=(0, 16))
        tk.Label(grp, text=label, font=FT_B, bg=PANEL, fg=TXT_DIM).pack(anchor="w")
        ent = tk.Entry(grp, font=FT, bg="#1A1A1A", fg=TXT,
                       insertbackground=TXT, relief="flat", width=width)
        ent.pack(ipady=5)
        if default:
            ent.insert(0, default)
        return ent

    def _labeled_combo(self, parent, label, values, width=10):
        """Combobox dengan label di atas."""
        grp = tk.Frame(parent, bg=PANEL)
        grp.pack(side="left", padx=(0, 16))
        tk.Label(grp, text=label, font=FT_B, bg=PANEL, fg=TXT_DIM).pack(anchor="w")
        cb = ttk.Combobox(grp, values=values, state="readonly",
                          font=FT, width=width)
        cb.pack(ipady=3)
        if values:
            cb.current(0)
        return cb

    def _show_add_dialog(self, title, prompt, callback):
        """Dialog input dark-themed untuk menambah item baru."""
        dlg = tk.Toplevel(self)
        dlg.title(title)
        dlg.geometry("400x160")
        dlg.configure(bg=PANEL)
        dlg.transient(self)
        dlg.grab_set()
        dlg.resizable(False, False)

        # Posisikan di tengah parent
        dlg.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - 200
        y = self.winfo_y() + (self.winfo_height() // 2) - 80
        dlg.geometry(f"+{x}+{y}")

        tk.Label(dlg, text=prompt, font=FT_B, bg=PANEL, fg=TXT).pack(pady=(18, 8))

        entry = tk.Entry(dlg, font=FT, bg="#1A1A1A", fg=TXT,
                         insertbackground=TXT, relief="flat", width=32)
        entry.pack(ipady=5, padx=24)
        entry.focus_set()

        def do_save(event=None):
            val = entry.get().strip()
            if val:
                callback(val)
            dlg.destroy()

        entry.bind("<Return>", do_save)

        btn_frame = tk.Frame(dlg, bg=PANEL)
        btn_frame.pack(pady=14)
        neo_btn(btn_frame, "✓  SIMPAN", GRN, "white", do_save,
                font=FT_B, px=12, py=5).pack(side="left", padx=6)
        neo_btn(btn_frame, "✕  BATAL", RED, "white", dlg.destroy,
                font=FT_B, px=12, py=5).pack(side="left", padx=6)

    # ════════════════════════════════════════════
    #  DATABASE CONNECTION HELPER
    # ════════════════════════════════════════════
    def _get_conn(self):
        """Buat koneksi PyMySQL."""
        return pymysql.connect(
            host=self.db_config.get("host", "127.0.0.1"),
            port=int(self.db_config.get("port", 3306)),
            user=self.db_config.get("user", ""),
            password=self.db_config.get("password", ""),
            database=self.db_config.get("database", "timbangan"),
            autocommit=False
        )

    def _safe_float(self, entry_widget):
        """Ambil nilai float dari Entry, default 0."""
        try:
            val = entry_widget.get().strip().replace(",", ".")
            return float(val) if val else 0.0
        except ValueError:
            return 0.0

    def _safe_int(self, entry_widget):
        """Ambil nilai int dari Entry, default 0."""
        try:
            val = entry_widget.get().strip()
            return int(float(val)) if val else 0
        except ValueError:
            return 0

    def _safe_date(self, entry_widget):
        """Ambil string tanggal dari Entry dan validasi format YYYY-MM-DD."""
        val = entry_widget.get().strip()
        if not val:
            return None
        try:
            datetime.strptime(val, "%Y-%m-%d")
            return val
        except ValueError:
            return None

    # ════════════════════════════════════════════
    #  GUDANG LUAR — LOAD & ADD
    # ════════════════════════════════════════════
    def _load_gudang_luar_list(self):
        """Load daftar gudang luar dari DB → populate combobox."""
        self._gudang_luar_map = {}
        conn = None
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute("SELECT id, nama_gudang FROM mst_gudang_luar ORDER BY nama_gudang")
            rows = cur.fetchall()
            cur.close()
            for row in rows:
                self._gudang_luar_map[row[1]] = row[0]
            self._mlog("OK", f"Gudang luar dimuat: {len(rows)} item.")
        except Exception as e:
            self._mlog("WARN", f"Load gudang luar gagal (tabel belum ada?): {e}")
        finally:
            if conn:
                conn.close()

        # Update combobox values: "" (kosong) + nama-nama gudang
        names = [""] + sorted(self._gudang_luar_map.keys())
        try:
            self.gula_del_gudang["values"] = names
            self.gula_del_gudang.current(0)
        except Exception:
            pass

    def _add_gudang_luar(self):
        """Dialog tambah gudang luar baru → simpan ke DB → refresh dropdown."""
        def callback(nama):
            conn = None
            try:
                conn = self._get_conn()
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO mst_gudang_luar (nama_gudang) VALUES (%s)",
                    (nama,)
                )
                conn.commit()
                cur.close()
                self._mlog("OK", f"Gudang luar baru ditambahkan: '{nama}'")
                messagebox.showinfo("Sukses", f"Gudang '{nama}' berhasil ditambahkan!",
                                    parent=self)
            except pymysql.err.IntegrityError:
                messagebox.showwarning("Duplikat",
                                       f"Gudang '{nama}' sudah ada di database!",
                                       parent=self)
            except Exception as e:
                messagebox.showerror("Error", f"Gagal tambah gudang:\n{e}", parent=self)
                self._mlog("ERR", f"Tambah gudang gagal: {e}")
            finally:
                if conn:
                    conn.close()
            # Reload dropdown
            self._load_gudang_luar_list()

        self._show_add_dialog("Tambah Gudang Luar",
                              "Masukkan nama gudang luar baru:", callback)

    # ════════════════════════════════════════════
    #  JENIS REJECT — ADD
    # ════════════════════════════════════════════
    def _add_jenis_reject(self):
        """Dialog tambah jenis reject baru → simpan ke DB → refresh combobox."""
        def callback(nama):
            conn = None
            try:
                conn = self._get_conn()
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO mst_jenis_reject (nama_reject) VALUES (%s)",
                    (nama,)
                )
                conn.commit()
                cur.close()
                self._mlog("OK", f"Jenis reject baru ditambahkan: '{nama}'")
                messagebox.showinfo("Sukses",
                                    f"Jenis reject '{nama}' berhasil ditambahkan!",
                                    parent=self)
            except pymysql.err.IntegrityError:
                messagebox.showwarning("Duplikat",
                                       f"Jenis reject '{nama}' sudah ada di database!",
                                       parent=self)
            except Exception as e:
                messagebox.showerror("Error",
                                     f"Gagal tambah jenis reject:\n{e}", parent=self)
                self._mlog("ERR", f"Tambah jenis reject gagal: {e}")
            finally:
                if conn:
                    conn.close()
            # Reload dropdown dari DB
            self._load_jenis_reject_list()
            # Auto-select yang baru ditambahkan
            try:
                self.rej_jenis_reject.set(nama)
            except Exception:
                pass

        self._show_add_dialog("Tambah Jenis Reject",
                              "Masukkan jenis reject baru:", callback)

    # ════════════════════════════════════════════
    #  JENIS REJECT — LOAD FROM DB
    # ════════════════════════════════════════════
    def _load_jenis_reject_list(self):
        """Load daftar jenis reject dari DB → populate combobox."""
        self._reject_types = []
        conn = None
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute("SELECT nama_reject FROM mst_jenis_reject ORDER BY nama_reject")
            rows = cur.fetchall()
            cur.close()
            self._reject_types = [row[0] for row in rows]
            self._mlog("OK", f"Jenis reject dimuat: {len(rows)} item.")
        except Exception as e:
            self._mlog("WARN", f"Load jenis reject gagal: {e}")
            # Fallback ke default jika DB belum siap
            self._reject_types = list(DEFAULT_REJECT_TYPES)
        finally:
            if conn:
                conn.close()

        # Update combobox values
        try:
            self.rej_jenis_reject["values"] = self._reject_types
            if self._reject_types:
                self.rej_jenis_reject.current(0)
        except Exception:
            pass

    # ════════════════════════════════════════════
    #  SAVE: MOL PENERIMAAN
    # ════════════════════════════════════════════
    def _save_mol_penerimaan(self):
        tgl = self._safe_date(self.mol_pen_tgl)
        if not tgl:
            messagebox.showwarning("Format Salah",
                                    "Tanggal harus format YYYY-MM-DD!", parent=self)
            return

        shift = int(self.mol_pen_shift.get())
        raw_sugar = self._safe_float(self.mol_pen_raw)
        cane_tebu = self._safe_float(self.mol_pen_cane)
        tangki_raw = self.mol_pen_tangki.get()        # "Tank A" or "Tank B"
        tangki_db  = tangki_raw.replace("Tank ", "")  # → "A" or "B" (match DB ENUM)

        conn = None
        try:
            conn = self._get_conn()
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO mol_penerimaan "
                    "(tanggal, shift, raw_sugar, cane_tebu, tangki_tujuan) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    (tgl, shift, raw_sugar, cane_tebu, tangki_db)
                )
            conn.commit()
            self._mlog("OK", f"Mol Penerimaan disimpan: {tgl} Shift-{shift} "
                             f"RS={raw_sugar} CT={cane_tebu} → Tank {tangki_db}")
        except Exception as e:
            if conn:
                conn.rollback()
            messagebox.showerror("Error", f"Gagal simpan Mol Penerimaan:\n{e}", parent=self)
            self._mlog("ERR", f"Mol Penerimaan gagal: {e}")
            return
        finally:
            if conn:
                conn.close()

        # Update stok dengan koneksi baru (anti 'commands out of sync')
        self._update_mol_stok(tgl)
        self._refresh_stock_display()
        messagebox.showinfo("Sukses", "Data Penerimaan Molasses berhasil disimpan!", parent=self)

    # ════════════════════════════════════════════
    #  SAVE: MOL DELIVERY
    # ════════════════════════════════════════════
    def _save_mol_delivery(self):
        tgl = self._safe_date(self.mol_del_tgl)
        if not tgl:
            messagebox.showwarning("Format Salah",
                                    "Tanggal harus format YYYY-MM-DD!", parent=self)
            return

        plan = self._safe_float(self.mol_del_plan)
        act_a = self._safe_float(self.mol_del_act_a)
        act_b = self._safe_float(self.mol_del_act_b)
        truck = self._safe_int(self.mol_del_truck)
        next_sched = self._safe_float(self.mol_del_next)

        conn = None
        try:
            conn = self._get_conn()
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO mol_delivery "
                    "(tanggal, plan_delivery, actual_tank_a, actual_tank_b, jml_truck, next_schedule) "
                    "VALUES (%s, %s, %s, %s, %s, %s)",
                    (tgl, plan, act_a, act_b, truck, next_sched)
                )
            conn.commit()
            self._mlog("OK", f"Mol Delivery disimpan: {tgl} Plan={plan} "
                             f"A={act_a} B={act_b} Truck={truck}")
        except Exception as e:
            if conn:
                conn.rollback()
            messagebox.showerror("Error", f"Gagal simpan Mol Delivery:\n{e}", parent=self)
            self._mlog("ERR", f"Mol Delivery gagal: {e}")
            return
        finally:
            if conn:
                conn.close()

        self._update_mol_stok(tgl)
        self._refresh_stock_display()
        messagebox.showinfo("Sukses", "Data Delivery Molasses berhasil disimpan!", parent=self)

    # ════════════════════════════════════════════
    #  SAVE: GULA PENERIMAAN
    # ════════════════════════════════════════════
    def _save_gula_penerimaan(self):
        tgl = self._safe_date(self.gula_pen_tgl)
        if not tgl:
            messagebox.showwarning("Format Salah",
                                    "Tanggal harus format YYYY-MM-DD!", parent=self)
            return

        shift = int(self.gula_pen_shift.get())
        gkm_c = self._safe_float(self.gula_pen_gkm_c)
        gkm_m = self._safe_float(self.gula_pen_gkm_m)
        gkb_c = self._safe_float(self.gula_pen_gkb_c)
        gkb_m = self._safe_float(self.gula_pen_gkb_m)

        conn = None
        try:
            conn = self._get_conn()
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO gula_penerimaan "
                    "(tanggal, shift, gkm_crushing, gkm_melting, gkb_crushing, gkb_melting) "
                    "VALUES (%s, %s, %s, %s, %s, %s)",
                    (tgl, shift, gkm_c, gkm_m, gkb_c, gkb_m)
                )
            conn.commit()
            self._mlog("OK", f"Gula Penerimaan disimpan: {tgl} Shift-{shift} "
                             f"GKM(C={gkm_c},M={gkm_m}) GKB(C={gkb_c},M={gkb_m})")
        except Exception as e:
            if conn:
                conn.rollback()
            messagebox.showerror("Error", f"Gagal simpan Gula Penerimaan:\n{e}", parent=self)
            self._mlog("ERR", f"Gula Penerimaan gagal: {e}")
            return
        finally:
            if conn:
                conn.close()

        self._update_gula_stok(tgl)
        self._refresh_all_tables()
        messagebox.showinfo("Sukses", "Data Penerimaan Gula berhasil disimpan!", parent=self)

    # ════════════════════════════════════════════
    #  SAVE: GULA DELIVERY (DIPERLUAS)
    # ════════════════════════════════════════════
    def _save_gula_delivery(self):
        tgl = self._safe_date(self.gula_del_tgl)
        if not tgl:
            messagebox.showwarning("Format Salah",
                                    "Tanggal harus format YYYY-MM-DD!", parent=self)
            return

        plan_del = self._safe_float(self.gula_del_plan)
        del_gkm = self._safe_float(self.gula_del_gkm)
        del_gkb = self._safe_float(self.gula_del_gkb)
        tonage = self._safe_float(self.gula_del_tonage)
        truck = self._safe_int(self.gula_del_truck)
        actual_del = self._safe_float(self.gula_del_actual)
        actual_gl = self._safe_float(self.gula_del_act_gl)

        # Gudang Luar (opsional)
        gudang_nama = self.gula_del_gudang.get().strip()
        id_gudang = self._gudang_luar_map.get(gudang_nama) if gudang_nama else None

        conn = None
        try:
            conn = self._get_conn()
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO gula_delivery "
                    "(tanggal, delivery_gkm, delivery_gkb, "
                    "plan_delivery, tonage_container, jml_truck, "
                    "id_gudang_luar, actual_delivery, nama_gudang_luar, actual_gudang_luar) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (tgl, del_gkm, del_gkb, plan_del, tonage, truck,
                     id_gudang, actual_del,
                     gudang_nama if gudang_nama else None, actual_gl)
                )
            conn.commit()

            log_msg = (f"Gula Delivery disimpan: {tgl} "
                       f"GKM={del_gkm} GKB={del_gkb} Plan={plan_del} "
                       f"Actual={actual_del} Container={tonage} Truck={truck}")
            if gudang_nama:
                log_msg += f" → Gudang: {gudang_nama} (Actual GL={actual_gl})"
            self._mlog("OK", log_msg)

        except Exception as e:
            if conn:
                conn.rollback()
            messagebox.showerror("Error", f"Gagal simpan Gula Delivery:\n{e}", parent=self)
            self._mlog("ERR", f"Gula Delivery gagal: {e}")
            return
        finally:
            if conn:
                conn.close()

        self._update_gula_stok(tgl)

        # Jika ada gudang luar dipilih, update stok gudang luar
        if id_gudang:
            self._update_gudang_luar_stok(tgl, id_gudang)

        self._refresh_all_tables()
        messagebox.showinfo("Sukses", "Data Delivery Gula berhasil disimpan!", parent=self)

    # ════════════════════════════════════════════
    #  SAVE: GULA REJECT LOG
    # ════════════════════════════════════════════
    def _save_gula_reject(self):
        tgl = self._safe_date(self.rej_tgl)
        if not tgl:
            messagebox.showwarning("Format Salah",
                                    "Tanggal harus format YYYY-MM-DD!", parent=self)
            return

        shift = int(self.rej_shift.get())
        kategori = self.rej_kategori.get()
        jenis_gula = self.rej_jenis_gula.get()
        jenis_reject = self.rej_jenis_reject.get().strip()
        jumlah = self._safe_float(self.rej_jumlah)
        ket = self.rej_ket.get().strip()

        if not jenis_reject:
            messagebox.showwarning("Data Kosong",
                                    "Jenis Reject harus diisi!", parent=self)
            return

        conn = None
        try:
            conn = self._get_conn()
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO gula_reject_log "
                    "(tanggal, shift, kategori_transaksi, jenis_gula, "
                    "jenis_reject, jumlah_kg, keterangan) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (tgl, shift, kategori, jenis_gula, jenis_reject, jumlah, ket)
                )
            conn.commit()
            self._mlog("OK", f"Reject Log disimpan: {tgl} Shift-{shift} "
                             f"{kategori}/{jenis_gula} {jenis_reject}={jumlah} ton")
        except Exception as e:
            if conn:
                conn.rollback()
            messagebox.showerror("Error", f"Gagal simpan Reject Log:\n{e}", parent=self)
            self._mlog("ERR", f"Reject Log gagal: {e}")
            return
        finally:
            if conn:
                conn.close()

        self._update_gula_stok(tgl)
        self._refresh_all_tables()
        messagebox.showinfo("Sukses", "Log Reject Gula berhasil disimpan!", parent=self)

    # ════════════════════════════════════════════
    #  LOGIKA OTOMASI STOK — MOLASSES
    # ════════════════════════════════════════════
    def _update_mol_stok(self, tanggal):
        """
        Hitung & upsert stok molasses untuk tanggal tertentu.
        Rumus: Stok Akhir = Stok Awal + Penerimaan - Delivery
        Menggunakan koneksi baru agar tidak bentrok.
        """
        conn = None
        try:
            conn = self._get_conn()
            cur = conn.cursor()

            # 1. Ambil stok akhir hari sebelumnya sebagai stok awal
            #    Jika DB kosong → default 0.00
            cur.execute(
                "SELECT stok_akhir_tanka, stok_akhir_tankb "
                "FROM mol_stok_tangki WHERE tanggal < %s "
                "ORDER BY tanggal DESC LIMIT 1", (tanggal,)
            )
            prev = cur.fetchone()
            stok_awal_a = float(prev[0]) if prev and prev[0] is not None else 0.0
            stok_awal_b = float(prev[1]) if prev and prev[1] is not None else 0.0

            # 2. Total penerimaan hari ini per tangki
            cur.execute(
                "SELECT COALESCE(SUM(raw_sugar + cane_tebu), 0) "
                "FROM mol_penerimaan WHERE tanggal = %s AND tangki_tujuan = 'A'",
                (tanggal,)
            )
            pen_a = float(cur.fetchone()[0])

            cur.execute(
                "SELECT COALESCE(SUM(raw_sugar + cane_tebu), 0) "
                "FROM mol_penerimaan WHERE tanggal = %s AND tangki_tujuan = 'B'",
                (tanggal,)
            )
            pen_b = float(cur.fetchone()[0])

            # 3. Total delivery hari ini
            cur.execute(
                "SELECT COALESCE(SUM(actual_tank_a), 0), "
                "       COALESCE(SUM(actual_tank_b), 0) "
                "FROM mol_delivery WHERE tanggal = %s",
                (tanggal,)
            )
            del_row = cur.fetchone()
            del_a = float(del_row[0])
            del_b = float(del_row[1])

            # 4. Hitung stok akhir
            stok_akhir_a = stok_awal_a + pen_a - del_a
            stok_akhir_b = stok_awal_b + pen_b - del_b

            # 5. UPSERT ke mol_stok_tangki
            #    DB hanya punya: tanggal, stok_awal_tanka/b, stok_akhir_tanka/b
            cur.execute(
                "INSERT INTO mol_stok_tangki "
                "(tanggal, stok_awal_tanka, stok_awal_tankb, "
                "stok_akhir_tanka, stok_akhir_tankb) "
                "VALUES (%s, %s, %s, %s, %s) "
                "ON DUPLICATE KEY UPDATE "
                "stok_awal_tanka  = VALUES(stok_awal_tanka), "
                "stok_awal_tankb  = VALUES(stok_awal_tankb), "
                "stok_akhir_tanka = VALUES(stok_akhir_tanka), "
                "stok_akhir_tankb = VALUES(stok_akhir_tankb)",
                (tanggal, stok_awal_a, stok_awal_b,
                 stok_akhir_a, stok_akhir_b)
            )
            conn.commit()
            cur.close()

            self._mlog("OK", f"Stok Mol {tanggal}: "
                             f"Awal(A={stok_awal_a:.2f} B={stok_awal_b:.2f}) "
                             f"+ Pen(A={pen_a:.2f} B={pen_b:.2f}) "
                             f"- Del(A={del_a:.2f} B={del_b:.2f}) "
                             f"= Akhir(A={stok_akhir_a:.2f} B={stok_akhir_b:.2f})")

        except Exception as e:
            if conn:
                conn.rollback()
            self._mlog("ERR", f"_update_mol_stok gagal: {e}")
        finally:
            if conn:
                conn.close()

    # ════════════════════════════════════════════
    #  LOGIKA OTOMASI STOK — GULA
    # ════════════════════════════════════════════
    def _update_gula_stok(self, tanggal):
        """
        Hitung & upsert stok gula untuk tanggal tertentu.
        Rumus: Stok Akhir = Stok Awal + Penerimaan - Delivery - Reject
        Menggunakan koneksi baru agar tidak bentrok.
        """
        conn = None
        try:
            conn = self._get_conn()
            cur = conn.cursor()

            # 1. Stok akhir hari sebelumnya → stok awal hari ini
            #    Jika DB kosong → default 0.00
            cur.execute(
                "SELECT stok_akhir_gkm, stok_akhir_gkb "
                "FROM gula_stok WHERE tanggal < %s "
                "ORDER BY tanggal DESC LIMIT 1", (tanggal,)
            )
            prev = cur.fetchone()
            awal_gkm = float(prev[0]) if prev and prev[0] is not None else 0.0
            awal_gkb = float(prev[1]) if prev and prev[1] is not None else 0.0

            # 2. Total penerimaan hari ini
            cur.execute(
                "SELECT COALESCE(SUM(gkm_crushing + gkm_melting), 0), "
                "       COALESCE(SUM(gkb_crushing + gkb_melting), 0) "
                "FROM gula_penerimaan WHERE tanggal = %s",
                (tanggal,)
            )
            pen = cur.fetchone()
            pen_gkm = float(pen[0])
            pen_gkb = float(pen[1])

            # 3. Total delivery hari ini
            cur.execute(
                "SELECT COALESCE(SUM(delivery_gkm), 0), "
                "       COALESCE(SUM(delivery_gkb), 0) "
                "FROM gula_delivery WHERE tanggal = %s",
                (tanggal,)
            )
            dl = cur.fetchone()
            del_gkm = float(dl[0])
            del_gkb = float(dl[1])

            # 4. Total reject hari ini per jenis gula
            cur.execute(
                "SELECT "
                "  COALESCE(SUM(CASE WHEN jenis_gula='GKM' THEN jumlah_kg ELSE 0 END), 0), "
                "  COALESCE(SUM(CASE WHEN jenis_gula='GKB' THEN jumlah_kg ELSE 0 END), 0), "
                "  COALESCE(SUM(jumlah_kg), 0) "
                "FROM gula_reject_log WHERE tanggal = %s",
                (tanggal,)
            )
            rej = cur.fetchone()
            rej_gkm = float(rej[0])
            rej_gkb = float(rej[1])
            rej_total = float(rej[2])

            # 5. Hitung stok akhir
            akhir_gkm = awal_gkm + pen_gkm - del_gkm - rej_gkm
            akhir_gkb = awal_gkb + pen_gkb - del_gkb - rej_gkb
            akhir_reject = rej_total

            # 6. UPSERT ke gula_stok
            #    DB hanya punya: tanggal, stok_awal_gkm/gkb, stok_akhir_gkm/gkb, stok_akhir_reject
            cur.execute(
                "INSERT INTO gula_stok "
                "(tanggal, stok_awal_gkm, stok_awal_gkb, "
                "stok_akhir_gkm, stok_akhir_gkb, stok_akhir_reject) "
                "VALUES (%s, %s, %s, %s, %s, %s) "
                "ON DUPLICATE KEY UPDATE "
                "stok_awal_gkm    = VALUES(stok_awal_gkm), "
                "stok_awal_gkb    = VALUES(stok_awal_gkb), "
                "stok_akhir_gkm   = VALUES(stok_akhir_gkm), "
                "stok_akhir_gkb   = VALUES(stok_akhir_gkb), "
                "stok_akhir_reject= VALUES(stok_akhir_reject)",
                (tanggal, awal_gkm, awal_gkb,
                 akhir_gkm, akhir_gkb, akhir_reject)
            )
            conn.commit()
            cur.close()

            self._mlog("OK", f"Stok Gula {tanggal}: "
                             f"GKM={akhir_gkm:.2f} GKB={akhir_gkb:.2f} "
                             f"Reject={akhir_reject:.2f}")

        except Exception as e:
            if conn:
                conn.rollback()
            self._mlog("ERR", f"_update_gula_stok gagal: {e}")
        finally:
            if conn:
                conn.close()

    # ════════════════════════════════════════════
    #  LOGIKA OTOMASI STOK — GUDANG LUAR
    # ════════════════════════════════════════════
    def _update_gudang_luar_stok(self, tanggal, id_gudang):
        """
        Hitung & upsert stok gudang luar untuk tanggal + gudang tertentu.
        Masuk = total delivery gula ke gudang ini hari ini.
        Stok Akhir = Stok Awal + Masuk - Keluar
        """
        conn = None
        try:
            conn = self._get_conn()
            cur = conn.cursor()

            # 1. Stok akhir hari sebelumnya → stok awal
            cur.execute(
                "SELECT stok_akhir FROM gudang_luar_stok "
                "WHERE id_gudang_luar = %s AND tanggal < %s "
                "ORDER BY tanggal DESC LIMIT 1",
                (id_gudang, tanggal)
            )
            prev = cur.fetchone()
            stok_awal = float(prev[0]) if prev and prev[0] is not None else 0.0

            # 2. Total masuk hari ini (actual_gudang_luar ke gudang ini)
            cur.execute(
                "SELECT COALESCE(SUM(actual_gudang_luar), 0) "
                "FROM gula_delivery "
                "WHERE tanggal = %s AND id_gudang_luar = %s",
                (tanggal, id_gudang)
            )
            masuk = float(cur.fetchone()[0])

            # 3. Keluar (untuk sekarang belum ada fitur keluar → 0)
            keluar = 0.0

            # 4. Stok akhir
            stok_akhir = stok_awal + masuk - keluar

            # 5. UPSERT
            cur.execute(
                "INSERT INTO gudang_luar_stok "
                "(tanggal, id_gudang_luar, stok_awal, masuk, keluar, stok_akhir) "
                "VALUES (%s, %s, %s, %s, %s, %s) "
                "ON DUPLICATE KEY UPDATE "
                "stok_awal  = VALUES(stok_awal), "
                "masuk      = VALUES(masuk), "
                "keluar     = VALUES(keluar), "
                "stok_akhir = VALUES(stok_akhir)",
                (tanggal, id_gudang, stok_awal, masuk, keluar, stok_akhir)
            )
            conn.commit()
            cur.close()

            self._mlog("OK", f"Gudang Luar #{id_gudang} stok {tanggal}: "
                             f"Awal={stok_awal:.2f} +Masuk={masuk:.2f} "
                             f"= Akhir={stok_akhir:.2f}")

        except Exception as e:
            if conn:
                conn.rollback()
            self._mlog("ERR", f"_update_gudang_luar_stok gagal: {e}")
        finally:
            if conn:
                conn.close()

    # ════════════════════════════════════════════
    #  REFRESH STOCK DISPLAY
    # ════════════════════════════════════════════
    def _refresh_stock_display(self):
        """
        Tarik data stok terkini dari DB dan update label di panel kanan.
        - Cari data hari ini dulu, kalau kosong ambil record terakhir.
        - Kalau DB benar-benar kosong, tampilkan 0.00.
        """
        today = date.today().strftime("%Y-%m-%d")

        # Default semua ke 0.00 dulu (pengaman kalau DB kosong / error)
        mol_a, mol_b = 0.0, 0.0
        gula_gkm, gula_gkb = 0.0, 0.0
        rej_gkm_val, rej_gkb_val, rej_total_val = 0.0, 0.0, 0.0
        gudang_total = 0.0

        conn = None
        try:
            conn = self._get_conn()
            cur = conn.cursor()

            # ── Molasses Stok ──
            cur.execute(
                "SELECT stok_akhir_tanka, stok_akhir_tankb "
                "FROM mol_stok_tangki WHERE tanggal = %s LIMIT 1",
                (today,)
            )
            mol = cur.fetchone()

            if not mol:
                cur.execute(
                    "SELECT stok_akhir_tanka, stok_akhir_tankb "
                    "FROM mol_stok_tangki ORDER BY tanggal DESC LIMIT 1"
                )
                mol = cur.fetchone()

            if mol:
                mol_a = float(mol[0]) if mol[0] is not None else 0.0
                mol_b = float(mol[1]) if mol[1] is not None else 0.0

            # ── Gula Stok ──
            cur.execute(
                "SELECT stok_akhir_gkm, stok_akhir_gkb "
                "FROM gula_stok WHERE tanggal = %s LIMIT 1",
                (today,)
            )
            gula = cur.fetchone()

            if not gula:
                cur.execute(
                    "SELECT stok_akhir_gkm, stok_akhir_gkb "
                    "FROM gula_stok ORDER BY tanggal DESC LIMIT 1"
                )
                gula = cur.fetchone()

            if gula:
                gula_gkm = float(gula[0]) if gula[0] is not None else 0.0
                gula_gkb = float(gula[1]) if gula[1] is not None else 0.0

            # ── Reject hari ini ──
            cur.execute(
                "SELECT "
                "  COALESCE(SUM(CASE WHEN jenis_gula='GKM' THEN jumlah_kg ELSE 0 END), 0), "
                "  COALESCE(SUM(CASE WHEN jenis_gula='GKB' THEN jumlah_kg ELSE 0 END), 0), "
                "  COALESCE(SUM(jumlah_kg), 0) "
                "FROM gula_reject_log WHERE tanggal = %s",
                (today,)
            )
            r = cur.fetchone()
            if r:
                rej_gkm_val = float(r[0]) if r[0] is not None else 0.0
                rej_gkb_val = float(r[1]) if r[1] is not None else 0.0
                rej_total_val = float(r[2]) if r[2] is not None else 0.0

            # ── Gudang Luar Stok (BARU) ──
            try:
                cur.execute(
                    "SELECT COALESCE(SUM(stok_akhir), 0) "
                    "FROM gudang_luar_stok WHERE tanggal = %s",
                    (today,)
                )
                gl = cur.fetchone()
                if gl and float(gl[0]) > 0:
                    gudang_total = float(gl[0])
                else:
                    # Fallback: ambil tanggal terakhir
                    cur.execute(
                        "SELECT COALESCE(SUM(stok_akhir), 0) "
                        "FROM gudang_luar_stok WHERE tanggal = "
                        "(SELECT MAX(tanggal) FROM gudang_luar_stok)"
                    )
                    gl2 = cur.fetchone()
                    gudang_total = float(gl2[0]) if gl2 and gl2[0] is not None else 0.0
            except Exception:
                gudang_total = 0.0  # Tabel belum ada → abaikan

            cur.close()
            self._mlog("OK", "Stok berhasil di-refresh.")

        except Exception as e:
            self._mlog("WARN", f"_refresh_stock_display gagal: {e}")
        finally:
            if conn:
                conn.close()

        # ── Update label UI (selalu jalan, meski DB error → tampil 0.00) ──
        try:
            self.lbl_mol_a.config(text=f"{mol_a:,.2f}")
            self.lbl_mol_b.config(text=f"{mol_b:,.2f}")
            self.lbl_mol_total.config(text=f"{mol_a + mol_b:,.2f}")

            self.lbl_gula_gkm.config(text=f"{gula_gkm:,.2f}")
            self.lbl_gula_gkb.config(text=f"{gula_gkb:,.2f}")
            self.lbl_gula_total.config(text=f"{gula_gkm + gula_gkb:,.2f}")

            self.lbl_rej_gkm.config(text=f"{rej_gkm_val:,.2f}")
            self.lbl_rej_gkb.config(text=f"{rej_gkb_val:,.2f}")
            self.lbl_rej_total.config(text=f"{rej_total_val:,.2f}")

            self.lbl_gudang_total.config(text=f"{gudang_total:,.2f}")
        except tk.TclError as e:
            self._mlog("WARN", f"Update label UI gagal (widget destroyed?): {e}")

        # Refresh tabel reject juga
        self._refresh_reject_table()

    # ════════════════════════════════════════════
    #  REFRESH REJECT TABLE
    # ════════════════════════════════════════════
    def _refresh_reject_table(self):
        """Tarik data reject hari ini ke treeview."""
        today = date.today().strftime("%Y-%m-%d")

        try:
            self.rej_tree.delete(*self.rej_tree.get_children())
        except Exception as e:
            self._mlog("WARN", f"_refresh_reject_table: Gagal clear treeview: {e}")
            return

        conn = None
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute(
                "SELECT id_reject_log, tanggal, shift, kategori_transaksi, jenis_gula, "
                "jenis_reject, jumlah_kg, keterangan "
                "FROM gula_reject_log WHERE tanggal = %s "
                "ORDER BY id_reject_log DESC",
                (today,)
            )
            rows = cur.fetchall()
            for i, row in enumerate(rows):
                vals = [v if v is not None else "" for v in row]
                tag = "even" if i % 2 == 0 else "odd"
                self.rej_tree.insert("", "end", values=vals, tags=(tag,))

            cur.close()
            if rows:
                self._mlog("OK", f"Reject table: {len(rows)} record hari ini dimuat.")

        except Exception as e:
            self._mlog("WARN", f"_refresh_reject_table gagal: {e}")
        finally:
            if conn:
                conn.close()

    # ════════════════════════════════════════════
    #  REFRESH DELIVERY TABLE
    # ════════════════════════════════════════════
    def _refresh_delivery_table(self):
        """Tarik data delivery gula terbaru ke treeview."""
        try:
            self.del_tree.delete(*self.del_tree.get_children())
        except Exception as e:
            self._mlog("WARN", f"_refresh_delivery_table: Gagal clear treeview: {e}")
            return

        conn = None
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute(
                "SELECT id_gula_del, tanggal, delivery_gkm, delivery_gkb, "
                "COALESCE(actual_delivery, 0), COALESCE(plan_delivery, 0), "
                "COALESCE(tonage_container, 0), COALESCE(jml_truck, 0), "
                "COALESCE(nama_gudang_luar, ''), "
                "COALESCE(actual_gudang_luar, 0) "
                "FROM gula_delivery "
                "ORDER BY id_gula_del DESC LIMIT 10"
            )
            rows = cur.fetchall()
            for i, row in enumerate(rows):
                vals = [v if v is not None else "" for v in row]
                tag = "even" if i % 2 == 0 else "odd"
                self.del_tree.insert("", "end", values=vals, tags=(tag,))

            cur.close()
            if rows:
                self._mlog("OK", f"Delivery table: {len(rows)} record dimuat.")

        except Exception as e:
            self._mlog("WARN", f"_refresh_delivery_table gagal: {e}")
        finally:
            if conn:
                conn.close()

    # ════════════════════════════════════════════
    #  REFRESH ALL TABLES
    # ════════════════════════════════════════════
    def _refresh_all_tables(self):
        """Refresh semua tabel dan display stok."""
        self._refresh_stock_display()   # Juga refresh reject table di dalamnya
        self._refresh_delivery_table()
