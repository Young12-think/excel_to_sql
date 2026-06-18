"""
Shared Theme / Palette & Helper Widgets
========================================
Dipakai oleh app.py dan mol_gula_module.py agar
tidak terjadi circular import.
"""

import tkinter as tk

# ── PALETTE ──────────────────────────────────────
BG      = "#141414"
PANEL   = "#1E1E1E"
SURFACE = "#252525"
BORDER  = "#2A2A2A"

YEL  = "#F5C518"   # kuning bold
TEAL = "#00BFA5"
PINK = "#E91E63"
ORG  = "#FF6D00"
GRN  = "#00C853"
RED  = "#D32F2F"
PRP  = "#7C4DFF"

TXT     = "#F0F0F0"
TXT_DIM = "#6B6B6B"
TXT_YEL = "#F5C518"
TXT_GRN = "#00C853"
TXT_RED = "#E91E63"
TXT_ORG = "#FF6D00"

FT   = ("Consolas", 9)
FT_B = ("Consolas", 9, "bold")
FT_H = ("Consolas", 11, "bold")
FT_XL= ("Consolas", 16, "bold")
FT_LG= ("Consolas", 13, "bold")


def _darken(hex_color, amt=20):
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2],16), int(hex_color[2:4],16), int(hex_color[4:6],16)
    r, g, b = max(0,r-amt), max(0,g-amt), max(0,b-amt)
    return f"#{r:02x}{g:02x}{b:02x}"


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
