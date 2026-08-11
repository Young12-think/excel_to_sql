"""
Uploader Stock Position: preview builder + executor.
Backend saja, tidak ada UI. Dipanggil dari mol_gula_module.

Alur:
  1. build_preview(parser_rows, resolver, conn) -> PreviewResult
  2. user tinjau / selesaikan unknown / konflik
  3. execute(preview, resolutions, conn, user, file_name, file_hash) -> BatchResult
"""
import hashlib
from datetime import date

STATUS_READY = 'ready'
STATUS_NEW = 'new'
STATUS_UNCHANGED = 'unchanged'
STATUS_CONFLICT_APP = 'conflict_app'
STATUS_CONFLICT_EXCEL = 'conflict_excel'
STATUS_LOCKED = 'locked'
STATUS_UNKNOWN = 'unknown_location'
STATUS_INVALID = 'invalid'
STATUS_DUPLICATE = 'duplicate'

ACTION_INSERT = 'insert'
ACTION_UPDATE = 'update'
ACTION_KEEP = 'keep_existing'
ACTION_IGNORE = 'ignore'
ACTION_CREATE_LOCATION = 'create_location'
ACTION_MAP_LOCATION = 'map_location'


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


class PreviewRow:
    __slots__ = ('date', 'excel_location', 'location_id', 'official_name',
                 'site_type', 'excel_value', 'existing_value', 'existing_source',
                 'status', 'action', 'source_reference', 'note')

    def __init__(self, **kw):
        for k in self.__slots__:
            setattr(self, k, kw.get(k))

    def to_dict(self):
        return {k: getattr(self, k) for k in self.__slots__}


class PreviewResult:
    def __init__(self):
        self.rows = []
        self.summary = {
            'dates': 0, 'locations': 0,
            'insert': 0, 'update': 0, 'unchanged': 0,
            'unknown': 0, 'conflict': 0, 'locked': 0, 'invalid': 0,
            'duplicate': 0, 'ignore': 0,
        }
        self.warnings = []

    def recompute_summary(self):
        s = self.summary
        for k in ('insert', 'update', 'unchanged', 'unknown', 'conflict',
                  'locked', 'invalid', 'duplicate', 'ignore'):
            s[k] = 0
        dates, locs = set(), set()
        for r in self.rows:
            dates.add(r.date)
            if r.location_id:
                locs.add(r.location_id)
            if r.action == ACTION_INSERT:
                s['insert'] += 1
            elif r.action == ACTION_UPDATE:
                s['update'] += 1
            elif r.action == ACTION_IGNORE:
                s['ignore'] += 1
            elif r.action == ACTION_KEEP:
                pass
            if r.status == STATUS_UNCHANGED:
                s['unchanged'] += 1
            elif r.status == STATUS_UNKNOWN:
                s['unknown'] += 1
            elif r.status in (STATUS_CONFLICT_APP, STATUS_CONFLICT_EXCEL):
                s['conflict'] += 1
            elif r.status == STATUS_LOCKED:
                s['locked'] += 1
            elif r.status == STATUS_INVALID:
                s['invalid'] += 1
            elif r.status == STATUS_DUPLICATE:
                s['duplicate'] += 1
        s['dates'] = len(dates)
        s['locations'] = len(locs)


def _existing_snapshot(conn, dates):
    """Ambil semua row gula_position untuk daftar tanggal (satu query)."""
    if not dates:
        return {}
    cur = conn.cursor()
    ph = ','.join(['%s'] * len(dates))
    cur.execute(
        f"SELECT stock_date, location_id, total_stock_ton, source "
        f"FROM gula_position WHERE stock_date IN ({ph})",
        tuple(dates)
    )
    out = {}
    for d, loc_id, val, src in cur.fetchall():
        out[(d, loc_id)] = (float(val), src)
    cur.close()
    return out


def _locked_dates(conn, dates):
    if not dates:
        return set()
    cur = conn.cursor()
    ph = ','.join(['%s'] * len(dates))
    cur.execute(
        f"SELECT report_date FROM rmi_daily_report "
        f"WHERE status='locked' AND module IN ('sugar','all') "
        f"AND report_date IN ({ph})",
        tuple(dates)
    )
    out = {r[0] for r in cur.fetchall()}
    cur.close()
    return out


def build_preview(parser_rows, resolver, conn, source_hint='excel'):
    """
    Bangun preview dari hasil parser + resolver + snapshot DB.
    source_hint: 'excel' untuk upload rutin, 'migration' untuk import historis.
    """
    result = PreviewResult()
    dates = {r['date'] for r in parser_rows if r.get('date')}
    existing = _existing_snapshot(conn, dates)
    locked = _locked_dates(conn, dates)
    seen_in_file = {}  # (date, location_id) -> first PreviewRow

    for raw in parser_rows:
        d = raw.get('date')
        val = raw.get('value')
        excel_loc = raw.get('excel_location', '') or ''
        src_ref = raw.get('source_reference')

        pr = PreviewRow(
            date=d, excel_location=excel_loc,
            location_id=None, official_name=None, site_type=None,
            excel_value=val, existing_value=None, existing_source=None,
            status=None, action=ACTION_IGNORE, source_reference=src_ref, note=None,
        )
        result.rows.append(pr)

        # tanggal/nilai tidak valid
        if not d:
            pr.status = STATUS_INVALID
            pr.note = 'Tanggal tidak valid'
            continue
        if val is None:
            pr.status = STATUS_INVALID
            pr.note = 'Nilai kosong (bukan nol)'
            continue
        if val < 0:
            pr.status = STATUS_INVALID
            pr.note = 'Nilai negatif ditolak'
            continue

        # locked selalu dilewati
        if d in locked:
            pr.status = STATUS_LOCKED
            pr.note = f'Tanggal {d} dikunci'
            continue

        # resolve lokasi
        loc_id, name, stype = resolver.resolve(raw)
        if loc_id is None:
            pr.status = STATUS_UNKNOWN
            pr.note = f"Lokasi '{excel_loc}' belum terdaftar/beralias"
            continue
        pr.location_id = loc_id
        pr.official_name = name
        pr.site_type = stype

        # duplikat dalam file (tanggal+lokasi sama)
        key = (d, loc_id)
        if key in seen_in_file:
            pr.status = STATUS_DUPLICATE
            pr.note = 'Duplikat dengan baris lain di file yang sama'
            continue
        seen_in_file[key] = pr

        # konflik dengan existing
        ex = existing.get(key)
        if ex is None:
            pr.status = STATUS_NEW
            pr.action = ACTION_INSERT
            continue
        ex_val, ex_src = ex
        if abs(ex_val - val) < 1e-6:
            pr.existing_value = ex_val
            pr.existing_source = ex_src
            pr.status = STATUS_UNCHANGED
            pr.action = ACTION_KEEP
            continue
        pr.existing_value = ex_val
        pr.existing_source = ex_src
        if ex_src == 'app':
            pr.status = STATUS_CONFLICT_APP
            pr.action = ACTION_KEEP
            pr.note = 'Nilai manual berbeda; Excel tidak menimpa secara default'
        else:
            pr.status = STATUS_CONFLICT_EXCEL
            pr.action = ACTION_UPDATE
            pr.note = 'Nilai Excel sebelumnya diperbarui'

    result.recompute_summary()
    return result


def execute_upload(preview, conn, user, file_name, file_hash, workbook_type, source='excel'):
    """
    Simpan hasil upload atomic. Rollback jika error.
    Return dict {batch_id, inserted, updated, unchanged, skipped, error}.
    """
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO gula_import_batch "
            "(file_name, file_hash, workbook_type, status, uploaded_by) "
            "VALUES (%s,%s,%s,'preview',%s)",
            (file_name, file_hash, workbook_type, user)
        )
        batch_id = cur.lastrowid

        counts = {'inserted': 0, 'updated': 0, 'unchanged': 0, 'skipped': 0, 'error': 0}
        for pr in preview.rows:
            if pr.action == ACTION_INSERT:
                cur.execute(
                    "INSERT INTO gula_position "
                    "(stock_date, location_id, total_stock_ton, detail_status, source, "
                    " import_batch_id, source_sheet, source_reference, created_by, updated_by) "
                    "VALUES (%s,%s,%s,'none',%s,%s,%s,%s,%s,%s)",
                    (pr.date, pr.location_id, pr.excel_value, source, batch_id,
                     _sheet_from_ref(pr.source_reference), pr.source_reference, user, user)
                )
                counts['inserted'] += 1
            elif pr.action == ACTION_UPDATE:
                cur.execute(
                    "UPDATE gula_position SET total_stock_ton=%s, source=%s, "
                    "import_batch_id=%s, source_sheet=%s, source_reference=%s, updated_by=%s "
                    "WHERE stock_date=%s AND location_id=%s",
                    (pr.excel_value, source, batch_id,
                     _sheet_from_ref(pr.source_reference), pr.source_reference, user,
                     pr.date, pr.location_id)
                )
                counts['updated'] += 1
            elif pr.action == ACTION_KEEP:
                counts['unchanged'] += 1
            else:
                counts['skipped'] += 1
                if pr.status == STATUS_INVALID:
                    counts['error'] += 1

        final_status = 'completed'
        if counts['error'] > 0 or preview.summary['unknown'] > 0:
            final_status = 'completed_with_warning'
        cur.execute(
            "UPDATE gula_import_batch SET status=%s, inserted_count=%s, updated_count=%s, "
            "unchanged_count=%s, skipped_count=%s, error_count=%s, completed_at=NOW() "
            "WHERE id=%s",
            (final_status, counts['inserted'], counts['updated'],
             counts['unchanged'], counts['skipped'], counts['error'], batch_id)
        )
        conn.commit()
        counts['batch_id'] = batch_id
        counts['final_status'] = final_status
        return counts
    except Exception as e:
        conn.rollback()
        try:
            cur.execute("UPDATE gula_import_batch SET status='failed', error_message=%s WHERE id=%s",
                        (str(e)[:5000], batch_id))
            conn.commit()
        except Exception:
            pass
        raise
    finally:
        cur.close()


def _sheet_from_ref(ref):
    if not ref or '!' not in ref:
        return None
    return ref.split('!', 1)[0][:100]


def create_location_and_alias(conn, code, name, site_type, capacity_ton, sort_order,
                              excel_alias_raw, user):
    """
    Untuk workflow UNKNOWN_LOCATION: buat master lokasi baru + simpan nama asli
    dari Excel sebagai alias. Atomic.
    """
    from stock_position_parser import normalize_alias
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO mst_gula_lokasi (code, name, site_type, capacity_ton, sort_order, "
            "created_by, updated_by) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (code.upper(), name, site_type, capacity_ton, sort_order, user, user)
        )
        loc_id = cur.lastrowid
        if excel_alias_raw and excel_alias_raw.strip() and normalize_alias(excel_alias_raw) != normalize_alias(name):
            cur.execute(
                "INSERT INTO mst_gula_lokasi_alias "
                "(location_id, alias_name, normalized_alias, source_format, created_by) "
                "VALUES (%s,%s,%s,'excel',%s) "
                "ON DUPLICATE KEY UPDATE alias_name=VALUES(alias_name)",
                (loc_id, excel_alias_raw.strip(), normalize_alias(excel_alias_raw), user)
            )
        conn.commit()
        return loc_id
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


def add_alias(conn, location_id, alias_raw, user):
    """Tambah alias untuk existing location (untuk workflow map)."""
    from stock_position_parser import normalize_alias
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO mst_gula_lokasi_alias "
            "(location_id, alias_name, normalized_alias, source_format, created_by) "
            "VALUES (%s,%s,%s,'excel',%s) "
            "ON DUPLICATE KEY UPDATE alias_name=VALUES(alias_name)",
            (location_id, alias_raw.strip(), normalize_alias(alias_raw), user)
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


def _self_check():
    """Self-check: preview logic dengan input sintetis, tanpa DB nyata."""
    class FakeResolver:
        def resolve(self, row):
            code = (row.get('location_code') or '').upper()
            loc_name = row.get('excel_location', '')
            table = {'WFG_MAIN': (1, 'Stock WFG', 'in_site'),
                     'KEPANJEN': (2, 'Stock Kepanjen', 'out_site')}
            if code in table:
                return table[code]
            for lid, nm, st in table.values():
                if nm.lower() == loc_name.lower():
                    return (lid, nm, st)
            return (None, None, None)

    class FakeCursor:
        def __init__(self, existing, locked):
            self.existing = existing
            self.locked = locked
            self._result = []
        def execute(self, sql, params=()):
            if 'gula_position' in sql:
                self._result = [(d, lid, v, s) for (d, lid), (v, s) in self.existing.items()
                                if d in params]
            elif 'rmi_daily_report' in sql:
                self._result = [(d,) for d in self.locked if d in params]
            else:
                self._result = []
        def fetchall(self):
            return self._result
        def close(self):
            pass

    class FakeConn:
        def __init__(self, existing, locked):
            self.existing = existing
            self.locked = locked
        def cursor(self):
            return FakeCursor(self.existing, self.locked)

    d1 = date(2026, 1, 1)
    d2 = date(2026, 1, 2)
    d3 = date(2026, 1, 3)  # locked

    parser_rows = [
        # ready-new (no existing)
        {'date': d1, 'location_code': 'WFG_MAIN', 'excel_location': 'Stock WFG', 'value': 100.0, 'source_reference': 'X!R1'},
        # unchanged (existing sama)
        {'date': d1, 'location_code': 'KEPANJEN', 'excel_location': 'Stock Kepanjen', 'value': 50.0, 'source_reference': 'X!R2'},
        # conflict app
        {'date': d2, 'location_code': 'WFG_MAIN', 'excel_location': 'Stock WFG', 'value': 200.0, 'source_reference': 'X!R3'},
        # conflict excel
        {'date': d2, 'location_code': 'KEPANJEN', 'excel_location': 'Stock Kepanjen', 'value': 75.0, 'source_reference': 'X!R4'},
        # locked
        {'date': d3, 'location_code': 'WFG_MAIN', 'excel_location': 'Stock WFG', 'value': 999.0, 'source_reference': 'X!R5'},
        # unknown
        {'date': d1, 'location_code': '', 'excel_location': 'Gudang Baru', 'value': 10.0, 'source_reference': 'X!R6'},
        # invalid: negative
        {'date': d1, 'location_code': 'WFG_MAIN', 'excel_location': 'Stock WFG', 'value': -5.0, 'source_reference': 'X!R7'},
        # duplicate (WFG_MAIN d1 sudah masuk baris pertama)
        {'date': d1, 'location_code': 'WFG_MAIN', 'excel_location': 'Stock WFG', 'value': 100.0, 'source_reference': 'X!R8'},
    ]
    existing = {
        (d1, 2): (50.0, 'app'),        # kepanjen d1 -> unchanged
        (d2, 1): (150.0, 'app'),       # WFG d2 = 150 (app), Excel 200 -> conflict_app
        (d2, 2): (60.0, 'excel'),      # kepanjen d2 = 60 (excel), Excel 75 -> conflict_excel
    }
    conn = FakeConn(existing, {d3})
    preview = build_preview(parser_rows, FakeResolver(), conn)

    statuses = [r.status for r in preview.rows]
    expected = [STATUS_NEW, STATUS_UNCHANGED, STATUS_CONFLICT_APP, STATUS_CONFLICT_EXCEL,
                STATUS_LOCKED, STATUS_UNKNOWN, STATUS_INVALID, STATUS_INVALID]
    # baris terakhir sebenarnya duplicate, tapi karena baris ke-7 juga WFG d1 dan invalid dulu,
    # tergantung urutan. WFG d1 pertama masuk seen_in_file (STATUS_NEW), lalu baris ke-7 negatif
    # jadi INVALID (di-check sebelum resolve), baris ke-8 duplicate.
    expected[-1] = STATUS_DUPLICATE
    assert statuses == expected, f'statuses:\n  got={statuses}\n  exp={expected}'
    s = preview.summary
    assert s['insert'] == 1, s
    assert s['update'] == 1, s   # conflict_excel -> update
    assert s['unchanged'] == 1, s
    assert s['unknown'] == 1, s
    assert s['conflict'] == 2, s
    assert s['locked'] == 1, s
    assert s['invalid'] == 1, s
    assert s['duplicate'] == 1, s
    print('stock_position_uploader self-check: OK')


if __name__ == '__main__':
    _self_check()
