# Nexventory

**Nexventory** adalah aplikasi web manajemen inventori (stok barang) dan pencatatan transaksi jual-beli, dibangun dengan **Flask**. Aplikasi ini menyediakan dua peran pengguna (**Admin** dan **User/Penjual**), autentikasi berbasis sesi, serta fitur checkout dengan simulasi pembayaran **QRIS**.

## Daftar Isi

- [Fitur Utama](#fitur-utama)
- [Tech Stack](#tech-stack)
- [Struktur Proyek](#struktur-proyek)
- [Prasyarat](#prasyarat)
- [Instalasi & Menjalankan Secara Lokal](#instalasi--menjalankan-secara-lokal)
- [Environment Variables](#environment-variables)
- [Akun Default untuk Testing](#akun-default-untuk-testing)
- [Peran Pengguna & Rute Utama](#peran-pengguna--rute-utama)
- [Dokumentasi API — Pembayaran QRIS](#dokumentasi-api--pembayaran-qris)
- [Migrasi Database](#migrasi-database)
- [Deployment](#deployment)
- [Catatan Keamanan](#catatan-keamanan)
- [Kontribusi](#kontribusi)
- [Lisensi](#lisensi)

## Fitur Utama

- **Autentikasi & Otorisasi** — Register dan login dengan validasi format email, kekuatan password (huruf besar/kecil, angka, minimal 8 karakter), pengecekan duplikasi username/email, serta pembatasan akun (kunci otomatis setelah beberapa kali gagal login).
- **Manajemen Produk** — Tambah, edit, dan hapus produk lengkap dengan kategori, harga, stok, ambang batas stok minimum, dan upload gambar produk.
- **Manajemen Penjualan/Transaksi** — Catat transaksi jual/beli yang terhubung ke produk dan pengguna, lengkap dengan riwayat transaksi.
- **Dashboard Admin** — Ringkasan statistik (total user, produk, transaksi), notifikasi produk dengan stok menipis, serta daftar user dan transaksi terbaru.
- **Dashboard User** — Kelola produk dan penjualan milik sendiri, riwayat transaksi, dan pengaturan akun.
- **Checkout & Pembayaran QRIS (simulasi)** — Generate QR code pembayaran, polling status pembayaran secara berkala, kedaluwarsa otomatis setelah 10 menit, dan auto-approve demo untuk keperluan pengujian. Sudah disiapkan titik integrasi untuk payment gateway nyata (Midtrans/Xendit).
- **Auto Database Migration** — Perubahan pada model database terdeteksi dan diterapkan secara otomatis saat aplikasi dijalankan (Flask-Migrate/Alembic).
- **Koneksi Database Fleksibel** — Otomatis mendeteksi dan menyesuaikan URI database untuk MySQL lokal, Railway (`MYSQL_URL`/`MYSQLHOST`), `DATABASE_URL` (Heroku/Render), atau fallback ke SQLite jika tidak ada konfigurasi.

## Tech Stack

| Kategori | Teknologi |
|---|---|
| Bahasa & Framework | Python, Flask 2.3 |
| ORM & Migrasi | Flask-SQLAlchemy, Flask-Migrate (Alembic) |
| Autentikasi | Flask-Login, Werkzeug (password hashing `pbkdf2:sha256`), Authlib (OAuth siap pakai) |
| Database | MySQL (via PyMySQL) dengan fallback SQLite |
| Pembayaran | `qrcode[pil]` untuk generate QR code (simulasi QRIS) |
| Server Produksi | Gunicorn |
| Frontend | Jinja2 templates, HTML/CSS, JavaScript |

## Struktur Proyek

```
Nexventory/
├── app/
│   ├── __init__.py          # Application factory (create_app)
│   ├── extensions.py        # Inisialisasi db, login_manager, migrate, oauth
│   ├── config/
│   │   └── payment_config.py  # Konfigurasi QRIS (nama merchant, expiry, dsb.)
│   ├── models/
│   │   ├── db.py             # BaseModel abstrak (id, created_at, updated_at)
│   │   ├── user.py           # Model User (auth, role, lock akun, token reset)
│   │   ├── product.py        # Model Product (stok, kategori, harga)
│   │   └── transaction.py    # Model Transaction (relasi ke Product & User)
│   ├── routes/
│   │   ├── auth.py           # Blueprint: login, register, logout
│   │   ├── main.py           # Blueprint: halaman utama
│   │   ├── admin.py          # Blueprint: dashboard & manajemen admin
│   │   └── user.py           # Blueprint: dashboard, produk, penjualan, checkout, API QRIS
│   └── services/
│       └── qris_service.py   # Logika inti generate & cek status QR pembayaran
├── templates/
│   ├── admin/                # Halaman-halaman panel admin
│   └── user/                 # Halaman-halaman panel user
├── static/                   # CSS, gambar, aset QRIS & upload
├── migrations/                # File migrasi Alembic
├── docs/
│   └── QRIS_API_Documentation.md
├── app.py                    # Entry point utama (menjalankan auto-migration lalu app)
├── wsgi.py                   # Entry point untuk Gunicorn/production
├── main.py                   # Entry point fallback (untuk platform yang mencari main:app)
├── config.py                  # Konfigurasi Flask & resolusi URI database
├── auto_migrate.py            # Script auto-migrasi skema database
├── init_db.py                  # Inisialisasi tabel + akun admin default
├── migrate.sh                  # Script bantu migrasi manual
├── requirements.txt
├── Procfile                    # Untuk deployment (Railway/Render/Heroku)
├── MIGRATION_GUIDE.md
└── class.md                    # Dokumentasi ringkas tiap model/class
```

## Prasyarat

- Python 3.10 atau lebih baru
- `pip` dan `venv`
- MySQL Server (opsional — jika tidak dikonfigurasi, aplikasi otomatis fallback ke SQLite)
- Git

## Instalasi & Menjalankan Secara Lokal

**1. Clone repository**

```bash
git clone https://github.com/Lasains/Nexventory.git
cd Nexventory
```

**2. Buat dan aktifkan virtual environment**

```bash
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Konfigurasi environment variables**

Buat file `.env` di root proyek (lihat detail di bagian [Environment Variables](#environment-variables)):

```env
FLASK_APP=wsgi.py
FLASK_ENV=development
SECRET_KEY=ganti-dengan-kunci-rahasia-anda
SQLALCHEMY_DATABASE_URI=mysql+pymysql://user:password@localhost/nexventory
SQLALCHEMY_TRACK_MODIFICATIONS=False

# (Opsional) Google OAuth
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_DISCOVERY_URL=https://accounts.google.com/.well-known/openid-configuration
```

> Jika `SQLALCHEMY_DATABASE_URI` tidak diisi, aplikasi otomatis membuat database SQLite di `instance/nexventory.db`.

**5. Siapkan database**

Pilih salah satu:

```bash
# Opsi A — via migrasi Alembic
flask db upgrade

# Opsi B — inisialisasi cepat + akun admin default
python init_db.py
```

**6. Jalankan aplikasi**

```bash
python app.py
```

Saat dijalankan, aplikasi otomatis mengecek dan menerapkan perubahan skema database (`auto_migrate.py`) sebelum server aktif di `http://localhost:5000`.

Alternatif menjalankan via Flask CLI:

```bash
flask run
```

## Environment Variables

| Variabel | Wajib | Keterangan |
|---|---|---|
| `FLASK_APP` | Ya | Entry point Flask, isi `wsgi.py` |
| `FLASK_ENV` | Tidak | `development` atau `production` |
| `SECRET_KEY` | Ya (production) | Kunci rahasia untuk session & token; ganti nilai default sebelum deploy |
| `SQLALCHEMY_DATABASE_URI` | Tidak | Connection string database; jika kosong, fallback ke SQLite |
| `DATABASE_URL` | Tidak | Alternatif URI database, umum dipakai Heroku/Render |
| `MYSQL_URL` / `MYSQLHOST` dkk. | Tidak | Variabel khusus MySQL di Railway, terdeteksi otomatis oleh `config.py` |
| `SQLALCHEMY_TRACK_MODIFICATIONS` | Tidak | Disarankan `False` |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` / `GOOGLE_DISCOVERY_URL` | Tidak | Diperlukan hanya jika mengaktifkan login OAuth Google (Authlib sudah diinisialisasi, integrasi rute masih dapat dikembangkan lebih lanjut) |

## Akun Default untuk Testing

Sesuai `MIGRATION_GUIDE.md`, setelah inisialisasi database tersedia akun berikut untuk pengujian:

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `admin123` |
| User | `user` | `user123` |

> ⚠️ Ganti atau hapus akun ini sebelum aplikasi digunakan di lingkungan production.

## Peran Pengguna & Rute Utama

| Blueprint | Prefix | Contoh Rute |
|---|---|---|
| `auth` | `/` | `/login`, `/register`, `/logout` |
| `main` | `/` | `/` (halaman utama) |
| `admin` | `/admin` | `/admin/dashboard`, `/admin/manage_users`, `/admin/manage_products`, `/admin/manage_transactions` |
| `user` | `/user` | `/user/dashboard`, `/user/manage_produk`, `/user/manage_jualan`, `/user/tambah_jualan`, `/user/checkout`, `/user/transaction` |

## Dokumentasi API — Pembayaran QRIS

Nexventory menyediakan API sederhana untuk simulasi pembayaran QRIS pada proses checkout. Dokumentasi lengkap beserta contoh request/response tersedia di [`docs/QRIS_API_Documentation.md`](docs/QRIS_API_Documentation.md). Ringkasan endpoint:

| Method | Endpoint | Keterangan |
|---|---|---|
| `POST` | `/user/api/qris/generate` | Generate QR code pembayaran untuk sejumlah nominal (butuh login) |
| `GET` | `/user/api/qris/check-status/<transaction_id>` | Cek status pembayaran (`pending`, `paid`, `expired`) |
| `POST` | `/user/api/payment-gateway/generate` | Titik integrasi untuk payment gateway nyata (Midtrans/Xendit) — belum terhubung penuh |

Konfigurasi nama merchant, durasi kedaluwarsa QR, dan ukuran QR code dapat diubah di `app/config/payment_config.py`.

## Migrasi Database

Proyek ini menggunakan Flask-Migrate untuk mengelola perubahan skema. Lihat [`MIGRATION_GUIDE.md`](MIGRATION_GUIDE.md) untuk panduan lengkap. Perintah umum:

```bash
# Migrasi otomatis (mendeteksi perubahan model & menerapkannya)
python3 auto_migrate.py

# Migrasi manual
flask db migrate -m "deskripsi perubahan"
flask db upgrade

# Menggunakan script bantu
./migrate.sh "deskripsi perubahan"
```

## Deployment

Proyek sudah menyertakan `Procfile` (`web: gunicorn wsgi:app`) sehingga siap dideploy ke platform seperti **Railway**, **Render**, atau **Heroku**. `config.py` secara otomatis mendeteksi environment cloud (`RAILWAY_ENVIRONMENT`, `RENDER`, `DYNO`) dan menyesuaikan koneksi database, termasuk fallback ke SQLite bila database MySQL lokal tidak dapat dijangkau di lingkungan cloud.

Langkah umum:

1. Set environment variables yang relevan (lihat tabel di atas) di dashboard platform pilihan.
2. Pastikan `SECRET_KEY` diisi dengan nilai unik dan rahasia.
3. Deploy — platform akan menjalankan `gunicorn wsgi:app` sesuai `Procfile`.

## Catatan Keamanan

- File `.env` pada repositori ini saat ini ikut ter-commit ke Git. Sebelum publikasi lebih lanjut atau deploy ke production, sebaiknya **hapus `.env` dari version control**, tambahkan ke `.gitignore`, dan **rotasi seluruh secret** (`SECRET_KEY`, kredensial database, `GOOGLE_CLIENT_SECRET`, dsb.) yang pernah terekspos.
- Ganti kredensial akun default (`admin`/`admin123`, `user`/`user123`) sebelum digunakan di luar lingkungan pengujian.

## Kontribusi

Kontribusi sangat terbuka:

1. Fork repository ini
2. Buat branch fitur (`git checkout -b fitur/nama-fitur`)
3. Commit perubahan (`git commit -m "Menambahkan fitur X"`)
4. Push ke branch (`git push origin fitur/nama-fitur`)
5. Buka Pull Request
