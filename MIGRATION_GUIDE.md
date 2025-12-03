# Database Migration Guide

## Overview

Aplikasi Nexventory sekarang menggunakan **Flask-Migrate** untuk mengelola perubahan database secara otomatis. Setiap perubahan pada model akan langsung tersimpan ke database melalui sistem migrasi.

## Cara Kerja

### Otomatis (Recommended)
1. **Auto-migration saat startup**: Aplikasi akan otomatis mendeteksi dan menerapkan perubahan database saat dijalankan
2. **Script auto-migrate**: Jalankan `python3 auto_migrate.py` untuk migrasi manual

### Manual
1. **Buat migrasi**: `./migrate.sh "deskripsi perubahan"` atau `flask db migrate -m "deskripsi"`
2. **Terapkan migrasi**: `flask db upgrade`

## Commands

### Auto Migration
```bash
# Jalankan migrasi otomatis
python3 auto_migrate.py

# Start aplikasi dengan auto-migration
python3 app.py
```

### Manual Migration
```bash
# Buat migrasi baru
flask db migrate -m "Menambah kolom image ke product"

# Terapkan migrasi
flask db upgrade

# Cek status migrasi
flask db current

# History migrasi
flask db history
```

### Quick Migration Script
```bash
# Gunakan script helper
./migrate.sh "Deskripsi perubahan"
```

## Contoh Penggunaan

### 1. Menambah kolom baru ke model
```python
# di app/models/product.py
class Product(db.Model):
    # ... existing columns ...
    new_field = db.Column(db.String(100), nullable=True)
```

**Auto-migration akan otomatis:**
1. Mendeteksi perubahan
2. Membuat file migrasi
3. Menerapkan ke database

### 2. Mengubah tipe data kolom
```python
# Sebelum
price = db.Column(db.Float, nullable=False)

# Sesudah  
price = db.Column(db.Integer, nullable=False)
```

### 3. Menambah model baru
```python
# app/models/category.py
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
```

## Best Practices

1. **Selalu backup database** sebelum migrasi besar
2. **Test migrasi** di development dulu
3. **Gunakan deskripsi yang jelas** untuk setiap migrasi
4. **Review file migrasi** sebelum menerapkan di production

## Troubleshooting

### Error: "No changes in schema detected"
- Tidak ada perubahan pada model, database sudah up-to-date

### Error: "Target database is not up to date"
- Jalankan `flask db upgrade` untuk update ke versi terbaru

### Error: "Can't locate revision identified by"
- Database dan migrasi tidak sinkron, coba `flask db stamp head`

## File Structure

```
Nexventory/
├── migrations/                 # Folder migrasi
│   ├── versions/             # File migrasi individu
│   ├── alembic.ini          # Konfigurasi Alembic
│   └── env.py               # Environment migrasi
├── app/models/              # Model definitions
├── auto_migrate.py          # Script auto-migration
├── migrate.sh               # Script helper
└── MIGRATION_GUIDE.md       # Dokumentasi ini
```

## Login Test

Setelah migrasi, gunakan akun test:
- **Admin**: username `admin`, password `admin123`
- **User**: username `user`, password `user123`
