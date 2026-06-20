# Auto EDA Insight

Aplikasi web berbasis Flask untuk melakukan **Exploratory Data Analysis (EDA)** secara otomatis. Pengguna dapat mengunggah dataset (CSV/XLSX), menjelajahi statistik deskriptif, membuat visualisasi interaktif, membersihkan data, dan mengekspor laporan PDF.

---

## Fitur Utama

- **Upload Dataset** — mendukung format `.csv` dan `.xlsx`
- **Statistik Deskriptif** — ringkasan otomatis tiap kolom (mean, median, std, missing values, dll.)
- **Visualisasi Interaktif** — univariat, bivariat, multivariat, serta analisis kategorik vs numerik menggunakan Plotly
- **Data Cleaning** — deteksi dan penanganan missing values, duplikat, dan outlier
- **Ekspor Laporan PDF** — laporan analisis lengkap yang bisa diunduh
- **Ekspor Data** — unduh data hasil cleaning dalam format CSV atau Excel
- **Autentikasi Pengguna** — register, login, dan lupa password berbasis SQLite

---

## Struktur Proyek

```
Auto_EDA_Insight/
├── app.py                          # Entry point — server Flask & semua route
├── requirements.txt                # Daftar dependensi Python
├── README.md                       # Dokumentasi proyek (file ini)
├── database.db                     # Database SQLite (user accounts)
├── lihat_user.py                   # Skrip utilitas — melihat daftar user di DB
│
├── backend/
│   ├── visualization.py            # Fungsi chart: univariate, bivariate, multivariate
│   ├── data_loader.py              # (placeholder) logika load data
│   ├── descriptive_stats.py        # (placeholder) kalkulasi statistik deskriptif
│   └── insight_generator.py        # (placeholder) generator insight otomatis
│
├── frontend/
│   ├── templates/
│   │   ├── dashboard.html          # Halaman utama — EDA & visualisasi
│   │   ├── login.html              # Halaman login
│   │   ├── register.html           # Halaman registrasi
│   │   ├── forgot_password.html    # Halaman lupa password
│   │   ├── settings.html           # Halaman pengaturan akun
│   │   └── team.html               # Halaman profil tim
│   └── static/
│       ├── css/
│       │   └── style.css           # Stylesheet utama
│       ├── js/
│       │   ├── script.js           # Logika frontend — upload, chart, interaksi
│       │   └── plotly.min.js       # Library Plotly (bundled)
│       └── images/
│           └── *.jpeg / *.png      # Foto profil tim & aset gambar
│
├── cleaned_data/                   # Output — file CSV hasil cleaning
│
├── data/
│   ├── uploaded/                   # File dataset yang diunggah user
│   └── sample_dataset/
│       ├── generate_data.py        # Skrip pembuat sample dataset (sales_data)
│       ├── sales_data.csv          # Contoh dataset penjualan
│       └── sales_data.xlsx         # Contoh dataset penjualan (Excel)
│
└── docs/
    ├── project_report.docx         # Laporan proyek lengkap
    └── dashboard_screenshot/       # Screenshot tampilan dashboard
        
```
---

## Instalasi & Menjalankan

### 1. Clone / Salin Proyek

```bash
git clone <url-repo>
cd Auto_EDA_Insight
```

### 2. Buat Virtual Environment (Disarankan)

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
```

### 3. Install Dependensi

```bash
pip install -r requirements.txt
```

### 4. Jalankan Aplikasi

```bash
python app.py
```

Buka browser dan akses: **http://127.0.0.1:5000**

---

## Cara Penggunaan

1. **Register / Login** — buat akun baru atau masuk dengan akun yang ada
2. **Upload Dataset** — klik tombol upload dan pilih file `.csv` atau `.xlsx`
3. **Eksplorasi Data** — lihat statistik deskriptif, distribusi kolom, dan korelasi
4. **Buat Visualisasi** — pilih jenis chart dan kolom yang ingin divisualisasikan
5. **Cleaning Data** — tangani missing values, hapus duplikat, atau filter outlier
6. **Download** — ekspor laporan PDF atau data yang telah dibersihkan (CSV/Excel)

---

## Dataset Contoh

Terdapat sample dataset penjualan di `data/sample_dataset/`. Untuk membuat ulang dataset tersebut:

```bash
cd data/sample_dataset
python generate_data.py
```

Dataset berisi 1.000 baris dengan kolom: `Date`, `Product`, `Category`, `Region`, `Payment_Method`, `Sales`, `Quantity`, `Discount`, `Profit`.

---

## Teknologi yang Digunakan

| Komponen     | Teknologi                              |
|--------------|----------------------------------------|
| Backend      | Python, Flask                          |
| Data         | Pandas, NumPy, SciPy                   |
| Visualisasi  | Plotly                                 |
| PDF Export   | ReportLab, Matplotlib                  |
| Database     | SQLite (via sqlite3)                   |
| Frontend     | HTML, CSS, JavaScript, Plotly.js       |
| Spreadsheet  | openpyxl                               |

---

## Catatan

- File `app_backup.py` adalah cadangan versi sebelumnya dari `app.py`.
- File `lihat_user.py` adalah skrip utilitas developer — tidak digunakan oleh aplikasi secara langsung.
- Folder `data/uploaded/` dan `cleaned_data/` akan terisi secara otomatis saat aplikasi dijalankan.
- Database `database.db` dibuat otomatis saat pertama kali aplikasi dijalankan.
