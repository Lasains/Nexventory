# Class Documentation

## BaseModel

BaseModel adalah kelas abstrak yang menyediakan fungsionalitas umum untuk semua model dalam database. Kelas ini menyediakan field standar seperti id, created_at, dan updated_at yang digunakan di seluruh aplikasi. BaseModel juga memiliki metode CRUD dasar seperti save(), delete(), dan berbagai metode query untuk mempermudah operasi database.

## User

User adalah model yang merepresentasikan data pengguna dalam sistem dengan fitur autentikasi dan keamanan lengkap. Kelas ini mengelola informasi pengguna seperti username, email, password hash, dan role dengan sistem keamanan termasuk lock account dan token reset. User juga menyediakan metode untuk verifikasi email, manajemen login attempts, dan konversi data ke format dictionary untuk API response.

## Product

Product adalah model yang menyimpan informasi tentang produk dalam sistem inventori dengan atribut dasar seperti nama, kategori, harga, dan stok. Kelas ini melacak jumlah stok produk dan menyediakan field min_stock untuk notifikasi stok minimum. Product juga mendukung penyimpanan nama file gambar untuk tampilan produk di interface pengguna.

## Transaction

Transaction adalah model yang mencatat semua transaksi penjualan dan pembelian produk dalam sistem dengan hubungan ke Product dan User. Kelas ini menyimpan detail transaksi seperti quantity, total_price, dan transaction_type untuk melacak alur barang. Transaction juga menyediakan audit trail lengkap dengan timestamp untuk setiap transaksi yang terjadi.
