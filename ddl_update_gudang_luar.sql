-- ═══════════════════════════════════════════════════
--  DDL — Perubahan Struktur Database untuk Modul Baru
--  Jalankan di phpMyAdmin / MySQL Workbench
-- ═══════════════════════════════════════════════════

-- ─────────────────────────────────────────────────
-- 1. ALTER TABLE gula_delivery — Tambah kolom baru
-- ─────────────────────────────────────────────────
ALTER TABLE gula_delivery
  ADD COLUMN plan_delivery DECIMAL(10,2) DEFAULT 0.00 AFTER delivery_gkb,
  ADD COLUMN tonage_container DECIMAL(10,2) DEFAULT 0.00 AFTER plan_delivery,
  ADD COLUMN jml_truck INT DEFAULT 0 AFTER tonage_container,
  ADD COLUMN id_gudang_luar INT NULL AFTER jml_truck;


-- ─────────────────────────────────────────────────
-- 2. TABEL BARU: mst_gudang_luar (Master Gudang)
-- ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS mst_gudang_luar (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nama_gudang VARCHAR(100) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- ─────────────────────────────────────────────────
-- 3. TABEL BARU: gudang_luar_stok (Stok per Gudang)
-- ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS gudang_luar_stok (
  id INT AUTO_INCREMENT PRIMARY KEY,
  tanggal DATE NOT NULL,
  id_gudang_luar INT NOT NULL,
  stok_awal DECIMAL(10,2) DEFAULT 0.00,
  masuk DECIMAL(10,2) DEFAULT 0.00,
  keluar DECIMAL(10,2) DEFAULT 0.00,
  stok_akhir DECIMAL(10,2) DEFAULT 0.00,
  UNIQUE KEY uq_tgl_gudang (tanggal, id_gudang_luar)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- ─────────────────────────────────────────────────
-- (OPSIONAL) Rename kolom jumlah_kg → jumlah_ton
-- Hanya jalankan jika Anda ingin rename. 
-- Jika tidak, kolom tetap jumlah_kg tapi nilainya = ton di UI.
-- ─────────────────────────────────────────────────
-- ALTER TABLE gula_reject_log 
--   CHANGE jumlah_kg jumlah_ton DECIMAL(12,2) DEFAULT 0.00;
