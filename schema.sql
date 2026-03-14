CREATE DATABASE IF NOT EXISTS timbangan;
USE timbangan;

DROP TABLE IF EXISTS data_timbang;

CREATE TABLE data_timbang (

id INT AUTO_INCREMENT PRIMARY KEY,
tanggal_upload DATETIME DEFAULT CURRENT_TIMESTAMP,

No INT,
Type VARCHAR(50),
Status VARCHAR(50),

Nomor_SPMSPB INT,
Nomor_SPPB INT,
Nomor_SPT VARCHAR(50),
Nomor_SPTA VARCHAR(50),
Nomor_SO VARCHAR(50),
Nomor_PO VARCHAR(50),
Nomor_GRPO VARCHAR(50),
Nomor_Surat_Jalan VARCHAR(100),

CardName VARCHAR(255),
ItemCode VARCHAR(50),
ItemName VARCHAR(255),
Batch VARCHAR(50),

Qty_SJ INT,
Qty_SPMSPB INT,

Remarks TEXT,

Tanggal_Masuk VARCHAR(50),
Berat_Masuk INT,
Jam_Masuk VARCHAR(50),

Tanggal_Keluar VARCHAR(50),
Berat_Keluar INT,
Jam_Keluar VARCHAR(50),

Tanggal_Loading_Mulai VARCHAR(50),
Jam_Loading_Mulai VARCHAR(50),

Tanggal_Loading_Selesai VARCHAR(50),
Jam_Loading_Selesai VARCHAR(50),

Supir VARCHAR(50),
Transportir VARCHAR(50),
Kendaraan VARCHAR(50),
Nopol VARCHAR(50),

Tipe INT,
CardCode VARCHAR(50),
Shift INT,

Qty_sblm_Rafaksi INT,
Persentase_Potongan_Rafaksi INT,
Qty_Rafaksi INT,
Qty_Netto INT,

NoSystem INT,

Kode_Pos_Insentif_Jarak INT,
Nama_Pos_Insentif_Jarak VARCHAR(50),

Jumlah_Karung INT,
Berat_rata2_Karung VARCHAR(50),

YEARSJ INT,
MONTHSJ INT,
DATESJ INT,

NOHP VARCHAR(50),
SJENTRY INT,
NOFAX VARCHAR(50),
NoDelivery INT,

`MbsToWeighbridge(Minute)` INT

) ENGINE=InnoDB
CHARSET=utf8mb4
COLLATE=utf8mb4_0900_ai_ci;