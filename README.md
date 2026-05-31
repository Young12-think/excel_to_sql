Markdown

# REKAP DSAJA — Data Input Application 📊

Aplikasi berbasis GUI (Desktop) menggunakan Python dan Tkinter dengan gaya desain *Neo-Brutalism*. Berfungsi untuk melakukan akselerasi input data timbangan, pembersihan data otomatis dari hantu *tab* SAP, penyaringan status konfirmasi, hingga sinkronisasi data secara massal (*bulk upload*) ke database MySQL.

---

## 📁 Struktur Folder Proyek
Agar proyek berjalan dengan rapi di local maupun GitHub, pastikan strukturnya seperti ini:
```text
timbangan-system/
│
├── database/
│   └── schema.sql          # Skrip skema tabel `data_timbang`
│
├── python/
│   ├── app.py              # Source code utama aplikasi GUI
│   └── app.ico             # Icon aplikasi (opsional)
│
├── excel/
│   └── template.xlsx       # Template jika dibutuhkan
│
├── requirements.txt        # Daftar library Python pendukung
└── README.md               # Dokumentasi aplikasi
```

---
## 🛠️ Persiapan Sistem & Instalasi (PC Lokal)
1. Prasyarat (Prerequisites)

Pastikan PC Anda sudah terinstal:

    Python 3.8 ke atas

    MySQL Server (Sudah terdapat database timbangan dan tabel data_timbang).

2. Langkah Instalasi di PC Lokal
    ```text
    
    Buka Terminal / Command Prompt / PowerShell, lalu masuk ke folder proyek:
    Bash

    cd path/to/timbangan-system

    Instal semua library yang diperlukan menggunakan file requirements.txt:
    Bash

    pip install -r requirements.txt

    Pastikan file konfigurasi database config.json terbuat atau biarkan aplikasi membuatnya otomatis saat dijalankan (Default IP: 127.0.0.1).
    ```
## 🚀 Cara Penggunaan Aplikasi
1. Menjalankan Aplikasi via Source Code
```text
Di terminal Anda, jalankan perintah:
```text
python python/app.py
```
##2. Alur Kerja Utama (Workflow)
  ```text
    Copy Data: Buka data laporan Anda dari Addon SAP atau Excel, lalu blok dan Copy (Ctrl+C) baris data yang diinginkan (aplikasi mendukung pembacaan hingga 53-60 kolom SAP).

    Paste Data: Kembali ke aplikasi REKAP DSAJA, klik tombol 📋 PASTE DATA atau tekan Ctrl+V.

        Sistem otomatis mengaktifkan "Sihir Lem Besi V4" untuk menyedot baris hantu dan merapikan kolom yang bergeser.

    Validasi & Edit: Anda bisa melihat pratinjau data di tabel bawah. Jika ada sel data yang salah, Double Click (Klik 2x) pada sel tersebut untuk mengeditnya secara langsung di layar.

    Upload ke DB: Jika data dirasa sudah valid, klik tombol ⬆ UPLOAD TO DB. Sistem akan menyaring status "Timbang Keluar & Confirm", mendeteksi duplikasi NoSystem, lalu mengirimkannya ke MySQL.
```
3. Fitur Tambahan
```text
    🌐 Pengaturan IP: Klik tombol IP di pojok kanan atas untuk mengubah target IP Server Database MySQL (akan tersimpan otomatis di config.json).

    📊 Monitor DB: Membuka jendela baru untuk memantau 100 data terakhir yang ada di database MySQL secara real-time, lengkap dengan fitur Cari dan Edit Data Terpilih.
```
💻 Mengambil & Menjalankan Proyek di PC Lain

Jika Anda pindah ke PC lain dan ingin melanjutkan proyek ini, gunakan alur Git berikut:
1. Jika Belum Ada Proyek di PC Lain (Clone Pertama Kali)

Ambil seluruh source code utuh dari GitHub Anda:
```text
git clone [https://github.com/Username/timbangan-system.git](https://github.com/Username/timbangan-system.git)
cd timbangan-system
pip install -r requirements.txt
python python/app.py

2. Jika Sudah Ada Folder Lama di PC Lain (Ambil Update Baru)

Jika di PC lain tersebut sudah ada kodenya, tetapi Anda ingin menyamakan versinya dengan GitHub (menimpa ketikan lokal yang iseng):
Bash

git fetch origin master
git reset --hard origin/master
python python/app.py
```
📦 Kompilasi Menjadi File Executable (.exe)

Jika Anda ingin membuat aplikasi ini menjadi file .exe siap pakai tanpa perlu instal Python di PC Server, gunakan PyInstaller:
```text
    Instal PyInstaller terlebih dahulu: pip install pyinstaller

    Jalankan perintah build berikut:
    Bash

    pyinstaller --noconsole --onefile --add-data "app.ico;." python/app.py
```
