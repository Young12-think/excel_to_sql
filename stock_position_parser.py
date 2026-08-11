"""
Parser Stock Position dari Excel.
Fase 4: hanya parsing + mapping lokasi. Tidak menyentuh DB untuk menyimpan.

Dua format didukung (PRD 8.4):
  Format A  : workbook lama 'Balance 1' -> blok SUGAR STOCK POSITION (tanggal horizontal)
  Format B  : sheet 'Stock Position' standar (format panjang, satu baris per tanggal+lokasi)

Deteksi berbasis LABEL struktural, bukan nomor baris tetap.
Hasil parse berupa list dict baris mentah; mapping ke master lokasi memakai
alias/kode/nama ternormalisasi. Baris tak dikenal diberi status UNKNOWN_LOCATION.
"""
import re
import openpyxl
from datetime import datetime, date


def normalize_alias(text):
    """Sama dengan ModuleMolGula._normalize_alias — dijaga konsisten."""
    s = str(text or '').strip().lower()
    s = re.sub(r'[.\-_/()]+', ' ', s)
    s = re.sub(r'\s+', ' ', s)
    return s.strip()


def _to_date(v):
    if v is None:
        return None
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    s = str(v).strip()
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%m/%d/%Y'):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    return None


def _to_number(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    if not s:
        return None
    s = s.replace(' ', '')
    if ',' in s and '.' in s:
        s = s.replace('.', '').replace(',', '.')
    else:
        s = s.replace(',', '.')
    try:
        return float(s)
    except ValueError:
        return None


class StockPositionParser:
    """
    Pemakaian:
        p = StockPositionParser(path)
        fmt = p.detect_format()        # 'balance1' | 'stock_position' | 'data1_only' | None
        rows = p.parse()               # list[dict], lihat _row_schema
        p.warnings                     # list[str]
    Baris dict:
        {date, excel_location, site_type, value, source_reference}
    """

    def __init__(self, file_path):
        self.file_path = file_path
        self.warnings = []
        self._wb_values = None
        self._wb_formula = None

    # ---------- workbook lifecycle ----------
    def _load(self):
        if self._wb_values is None:
            self._wb_values = openpyxl.load_workbook(self.file_path, read_only=True, data_only=True)
            self._wb_formula = openpyxl.load_workbook(self.file_path, read_only=True, data_only=False)

    def close(self):
        for wb in (self._wb_values, self._wb_formula):
            try:
                if wb is not None:
                    wb.close()
            except Exception:
                pass

    def _find_sheet(self, *candidates):
        """Cari sheet by nama case-insensitive; kembalikan nama asli atau None."""
        wanted = {c.lower() for c in candidates}
        for name in self._wb_values.sheetnames:
            if name.strip().lower() in wanted:
                return name
        return None

    # ---------- deteksi ----------
    def detect_format(self):
        """
        Format yang didukung:
          - 'stock_position'  : sheet 'Stock Location'/'Stock Position' format panjang
          - 'data1_embedded'  : blok Stock Position lama di Data1 (import historis one-off)
          - 'data1_only'      : Data1 tanpa blok Stock Position -> tidak ada data untuk diproses
        """
        self._load()
        if self._find_sheet('Stock Location', 'Stock Position', 'POSITION_INPUT'):
            return 'stock_position'
        d1 = self._find_sheet('Data1')
        if d1 and self._find_data1_block(d1):
            return 'data1_embedded'
        if d1:
            return 'data1_only'
        return None

    def _find_data1_block(self, sheet_name):
        """
        Cari blok 'Stock Possition/Position' yang tertanam di header Data1.
        Struktur: header gabungan di baris 2, nama lokasi sebagai sub-header baris 3,
        nilai per tanggal mulai baris 5. Lokasi dibaca dinamis dari sub-header,
        tidak di-hardcode ke kolom DR/DS/DT.
        Return (start_col, {col_index: nama_lokasi}) atau None.
        """
        ws = self._wb_values[sheet_name]
        rows = []
        for i, row in enumerate(ws.iter_rows(min_row=1, max_row=4, values_only=True)):
            rows.append(list(row))
            if i >= 3:
                break
        if len(rows) < 3:
            return None
        r2, r3 = rows[1], rows[2]
        start = None
        for c, v in enumerate(r2):
            if v and re.search(r'STOCK\s*POSS?ITION', str(v).upper()):
                start = c
                break
        if start is None:
            return None
        # kumpulkan sub-header lokasi mulai dari start sampai sub-header kosong
        loc_cols = {}
        for c in range(start, len(r3)):
            name = str(r3[c]).strip() if c < len(r3) and r3[c] is not None else ''
            if not name:
                if loc_cols:
                    break
                continue
            # berhenti kalau masuk blok header lain di baris 2
            if c > start and c < len(r2) and r2[c] and not re.search(r'STOCK\s*POSS?ITION', str(r2[c]).upper()):
                break
            loc_cols[c] = name
        if not loc_cols:
            return None
        return (start, loc_cols)

    # ---------- parse dispatcher ----------
    def parse(self):
        fmt = self.detect_format()
        if fmt == 'stock_position':
            return self._parse_format_b()
        if fmt == 'data1_embedded':
            return self._parse_data1_embedded()
        if fmt == 'data1_only':
            self.warnings.append("Workbook hanya memiliki 'Data1'. Tidak ada data Stock Position untuk diproses.")
            return []
        self.warnings.append("Format workbook tidak dikenali (tidak ada sheet 'Stock Location'/'Stock Position' atau blok Stock Position di 'Data1').")
        return []

    # ---------- Format C: blok Stock Position tertanam di Data1 ----------
    def _parse_data1_embedded(self):
        """
        Baca blok Stock Position lama yang tertanam sebagai kolom di 'Data1'
        (kolom DR/DS/DT dst, satu baris per tanggal). site_type tidak diketahui
        dari struktur ini -> diserahkan ke LocationResolver (mapping by nama/alias
        akan membawa site_type dari master).
        """
        name = self._find_sheet('Data1')
        block = self._find_data1_block(name)
        if not block:
            self.warnings.append("Blok Stock Position tertanam di 'Data1' tidak ditemukan.")
            return []
        start_col, loc_cols = block
        ws = self._wb_values[name]
        rows_out = []
        for r_idx, row in enumerate(ws.iter_rows(min_row=5, values_only=True), start=5):
            tgl = _to_date(row[1]) if len(row) > 1 else None
            if not tgl:
                continue
            for c, loc_name in loc_cols.items():
                val = _to_number(row[c]) if c < len(row) else None
                if val is None:
                    continue
                rows_out.append({
                    'date': tgl,
                    'excel_location': loc_name,
                    'site_type': '',
                    'value': val,
                    'source_reference': f'{name}!R{r_idx}C{c+1}',
                })
        if not rows_out:
            self.warnings.append("Blok Stock Position di 'Data1' ditemukan tetapi tidak ada nilai terbaca.")
        return rows_out

    # ---------- Format B: sheet Stock Location/Stock Position standar ----------
    def _parse_format_b(self):
        name = self._find_sheet('Stock Location', 'Stock Position', 'POSITION_INPUT')
        ws = self._wb_values[name]
        it = ws.iter_rows(values_only=True)
        header = None
        for row in it:
            if row and any(c is not None for c in row):
                header = [str(c).strip().lower() if c is not None else '' for c in row]
                break
        if not header:
            self.warnings.append('Sheet Stock Position kosong.')
            return []

        def col(*names):
            for n in names:
                for i, h in enumerate(header):
                    if h == n:
                        return i
            return None

        i_date = col('tanggal', 'date')
        i_code = col('kode lokasi', 'kode', 'location code', 'code')
        i_name = col('nama lokasi', 'nama', 'location name', 'name')
        i_type = col('tipe lokasi', 'tipe', 'site type', 'type')
        i_val = col(
            'stok ton', 'stok', 'stock ton', 'total stock (ton)',
            'total stock ton', 'total stock', 'quantity_ton', 'quantity'
        )

        if i_date is None or i_val is None or (i_code is None and i_name is None):
            self.warnings.append('Kolom wajib sheet Stock Location tidak lengkap (butuh Tanggal, Stok Ton/Total Stock, dan Kode/Nama Lokasi).')
            return []

        rows = []
        rownum = 1
        for r in it:
            rownum += 1
            if not r or all(c is None for c in r):
                continue
            d = _to_date(r[i_date]) if i_date < len(r) else None
            if not d:
                continue
            val = _to_number(r[i_val]) if i_val < len(r) else None
            code = str(r[i_code]).strip() if i_code is not None and i_code < len(r) and r[i_code] is not None else ''
            nm = str(r[i_name]).strip() if i_name is not None and i_name < len(r) and r[i_name] is not None else ''
            stype = str(r[i_type]).strip().lower() if i_type is not None and i_type < len(r) and r[i_type] is not None else ''
            if stype not in ('in_site', 'out_site'):
                stype = ''
            rows.append({
                'date': d,
                'location_code': code,
                'excel_location': nm or code,
                'site_type': stype,
                'value': val,
                'source_reference': f'{name}!R{rownum}',
            })
        if not rows:
            self.warnings.append('Sheet Stock Location tidak berisi baris data valid.')
        return rows


class LocationResolver:
    """
    Petakan baris hasil parse ke location_id master (PRD 8.2 prioritas):
      1. kode lokasi persis
      2. nama resmi ternormalisasi
      3. alias ternormalisasi
      4. gagal -> UNKNOWN_LOCATION
    Dibangun dari snapshot master (dibaca sekali) supaya tidak query per-baris.
    """

    def __init__(self, conn):
        self.by_code = {}
        self.by_norm_name = {}
        self.by_norm_alias = {}
        self._load(conn)

    def _load(self, conn):
        cur = conn.cursor()
        cur.execute('SELECT id, code, name, site_type FROM mst_gula_lokasi')
        for lid, code, name, stype in cur.fetchall():
            self.by_code[str(code).strip().upper()] = (lid, name, stype)
            self.by_norm_name[normalize_alias(name)] = (lid, name, stype)
        id_info = {lid: (name, stype) for lid, name, stype in self.by_code.values()}
        cur.execute('SELECT location_id, normalized_alias FROM mst_gula_lokasi_alias')
        for loc_id, norm in cur.fetchall():
            if loc_id in id_info:
                nm, st = id_info[loc_id]
                self.by_norm_alias[norm] = (loc_id, nm, st)
        cur.close()

    def resolve(self, row):
        """Return (location_id, official_name, site_type) atau (None, None, None)."""
        code = str(row.get('location_code', '') or '').strip().upper()
        if code and code in self.by_code:
            return self.by_code[code]
        norm = normalize_alias(row.get('excel_location', ''))
        if norm in self.by_norm_name:
            return self.by_norm_name[norm]
        if norm in self.by_norm_alias:
            return self.by_norm_alias[norm]
        return (None, None, None)


def _self_check():
    """Self-check ringan tanpa DB: normalisasi + parsing Format A/B pakai openpyxl in-memory."""
    import io
    from openpyxl import Workbook

    assert normalize_alias('Stock  W.F.G') == normalize_alias('STOCK W F G')
    assert normalize_alias(' Stock WFG ') == 'stock wfg'

    wb = Workbook()
    ws = wb.active
    ws.title = 'Stock Position'
    ws.append(['Tanggal', 'Kode Lokasi', 'Nama Lokasi', 'Tipe Lokasi', 'Stok Ton'])
    ws.append([date(2026, 1, 1), 'X1', 'Lokasi X1', 'in_site', 10])
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    p = StockPositionParser(buf)
    assert p.detect_format() == 'stock_position'
    rows = p.parse()
    assert len(rows) == 1 and rows[0]['value'] == 10.0 and rows[0]['location_code'] == 'X1'
    p.close()

    # test Format C: blok Stock Position tertanam di Data1
    wb2 = Workbook()
    ws2 = wb2.active
    ws2.title = 'Data1'
    ws2.cell(row=2, column=1, value='No')
    ws2.cell(row=2, column=2, value='Tgl')
    ws2.cell(row=2, column=5, value='Stock Possition')
    ws2.merge_cells(start_row=2, start_column=5, end_row=2, end_column=6)
    ws2.cell(row=3, column=5, value='Lokasi X')
    ws2.cell(row=3, column=6, value='Lokasi Y')
    ws2.cell(row=5, column=2, value=date(2026, 1, 1))
    ws2.cell(row=5, column=5, value=100)
    ws2.cell(row=5, column=6, value=200)
    ws2.cell(row=6, column=2, value=date(2026, 1, 2))
    ws2.cell(row=6, column=5, value=110)
    ws2.cell(row=6, column=6, value=210)
    buf2 = io.BytesIO()
    wb2.save(buf2)
    buf2.seek(0)

    p2 = StockPositionParser(buf2)
    assert p2.detect_format() == 'data1_embedded', p2.detect_format()
    rows2 = p2.parse()
    assert len(rows2) == 4
    x_rows = [r for r in rows2 if r['excel_location'] == 'Lokasi X']
    assert len(x_rows) == 2 and x_rows[0]['value'] == 100.0
    p2.close()

    print('stock_position_parser self-check: OK')


if __name__ == '__main__':
    _self_check()
