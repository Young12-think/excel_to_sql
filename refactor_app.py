import sys
import json
import re

def process_file():
    filepath = r"d:\timbangan system\python\excelmysql\app.py"
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Update load/save methods
    content = content.replace(
"""    def _load_ip(self):
        \"\"\"Baca db_host dari config.json. Default 127.0.0.1 jika file belum ada.\"\"\"
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("db_host", "127.0.0.1")
        except (FileNotFoundError, json.JSONDecodeError, Exception):
            return "127.0.0.1"

    def _save_ip(self, new_ip):
        \"\"\"Simpan db_host baru ke config.json dan update attribute.\"\"\"
        self.db_host = new_ip
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump({"db_host": new_ip}, f, indent=2)
        except Exception as e:
            self._log("ERROR", f"Gagal menyimpan config: {e}")""",
"""    def _load_db_config(self):
        \"\"\"Baca db_config dari config.json.\"\"\"
        default_config = {
            "host": "127.0.0.1",
            "port": 3306,
            "user": "wb_rmi",
            "password": "12345678",
            "database": "timbangan"
        }
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "db_host" in data and "host" not in data:
                    data["host"] = data["db_host"]
                # merge default with loaded
                for k, v in default_config.items():
                    data.setdefault(k, v)
                return data
        except (FileNotFoundError, json.JSONDecodeError, Exception):
            return default_config

    def _save_db_config(self, new_config):
        \"\"\"Simpan db_config baru ke config.json dan update attribute.\"\"\"
        self.db_config = new_config
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.db_config, f, indent=2)
        except Exception as e:
            self._log("ERROR", f"Gagal menyimpan config: {e}")"""
    )

    # 2. Update __init__
    content = content.replace("self.db_host = self._load_ip()", "self.db_config = self._load_db_config()")

    # 3. Update header button
    content = content.replace(
"""        self.btn_ip = tk.Button(right, text=f"🌐 IP: {self.db_host}",
                                font=FT_B, bg=SURFACE, fg=TXT_YEL,
                                activebackground=_darken(SURFACE),
                                activeforeground=TXT_YEL,
                                relief="flat", cursor="hand2", bd=0,
                                command=self._show_ip_settings,
                                padx=10, pady=4)
        self.btn_ip.pack(side="top", pady=(0, 4))""",
"""        host_display = self.db_config.get("host", "127.0.0.1")
        self.btn_db = tk.Button(right, text=f"🌐 DB: {host_display}",
                                font=FT_B, bg=SURFACE, fg=TXT_YEL,
                                activebackground=_darken(SURFACE),
                                activeforeground=TXT_YEL,
                                relief="flat", cursor="hand2", bd=0,
                                command=self._show_db_settings,
                                padx=10, pady=4)
        self.btn_db.pack(side="top", pady=(0, 4))"""
    )

    # 4. Update _show_ip_settings -> _show_db_settings
    settings_pattern = re.compile(r'    def _show_ip_settings\(self\):.*?neo_btn\(btn_wrap, "💾 SIMPAN", GRN, "white", simpan,\s+font=FT_B, px=15, py=6, border="#000"\)\.pack\(\)', re.DOTALL)
    
    new_settings = """    def _show_db_settings(self):
        \"\"\"Pop-up untuk mengubah setting server database.\"\"\"
        db_win = tk.Toplevel(self)
        db_win.title("Setting Koneksi Database")
        db_win.geometry("400x500")
        db_win.configure(bg=BG)
        db_win.transient(self)
        db_win.grab_set()

        wrap, inner = shadow_frame(db_win, bg=SURFACE, border=BORDER, bw=2)
        wrap.pack(fill="both", expand=True, padx=10, pady=10)

        tk.Label(inner, text="Konfigurasi Database", bg=SURFACE, fg=TXT_YEL, font=FT_H).pack(pady=(10, 4))
        
        entries = {}
        fields = [("Host", "host"), ("Port", "port"), ("User", "user"), ("Password", "password"), ("Database", "database")]
        
        for label_text, key in fields:
            f_frame = tk.Frame(inner, bg=SURFACE)
            f_frame.pack(fill="x", padx=20, pady=4)
            tk.Label(f_frame, text=label_text, bg=SURFACE, fg=TXT_DIM, font=FT, width=10, anchor="w").pack(side="left")
            ent = tk.Entry(f_frame, font=FT, bg="#1A1A1A", fg=TXT, insertbackground=TXT, relief="flat")
            if key == "password":
                ent.config(show="*")
            ent.pack(side="left", fill="x", expand=True, ipady=4, padx=5)
            val = self.db_config.get(key, "")
            ent.insert(0, str(val))
            entries[key] = ent

        entries["host"].focus_set()

        def simpan(event=None):
            new_conf = {
                "host": entries["host"].get().strip(),
                "port": int(entries["port"].get().strip() or 3306),
                "user": entries["user"].get().strip(),
                "password": entries["password"].get().strip(),
                "database": entries["database"].get().strip()
            }
            if not new_conf["host"]:
                return
            self._save_db_config(new_conf)
            self.btn_db.config(text=f"🌐 DB: {new_conf['host']}")
            self._log("SUCCESS", f"DB Config diperbarui → {new_conf['host']}")
            db_win.destroy()

        for ent in entries.values():
            ent.bind("<Return>", simpan)

        btn_wrap = tk.Frame(inner, bg=SURFACE)
        btn_wrap.pack(pady=15)
        neo_btn(btn_wrap, "💾 SIMPAN", GRN, "white", simpan, font=FT_B, px=15, py=6, border="#000").pack()"""
    
    content = settings_pattern.sub(new_settings, content)

    # 5. Replace pymysql.connect(host=self.db_host, user="wb_rmi", password="12345678", database="timbangan"
    connect_str_old_1 = """            conn = pymysql.connect(host=self.db_host, user="wb_rmi",
                                   password="12345678", database="timbangan",
                                   autocommit=False)"""
    connect_str_new = """            conn = pymysql.connect(
                host=self.db_config.get("host", "127.0.0.1"),
                port=int(self.db_config.get("port", 3306)),
                user=self.db_config.get("user", "wb_rmi"),
                password=self.db_config.get("password", "12345678"),
                database=self.db_config.get("database", "timbangan"),
                autocommit=False
            )"""
    content = content.replace(connect_str_old_1, connect_str_new)
    
    connect_str_old_2 = """            conn = pymysql.connect(host=self.db_host, user="wb_rmi",
                                   password="12345678", database="timbangan")"""
    connect_str_new_2 = """            conn = pymysql.connect(
                host=self.db_config.get("host", "127.0.0.1"),
                port=int(self.db_config.get("port", 3306)),
                user=self.db_config.get("user", "wb_rmi"),
                password=self.db_config.get("password", "12345678"),
                database=self.db_config.get("database", "timbangan")
            )"""
    content = content.replace(connect_str_old_2, connect_str_new_2)

    # 6. ModuleMolGula passing
    content = content.replace("ModuleMolGula(self, self.db_host)", "ModuleMolGula(self, self.db_config)")

    # 7. Any remaining self.db_host that was just formatted in strings or variables
    content = content.replace("self.db_host", 'self.db_config.get("host", "127.0.0.1")')

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print("Refactoring complete.")

if __name__ == "__main__":
    process_file()
