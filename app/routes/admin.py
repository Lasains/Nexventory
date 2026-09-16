from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from app.models import db, User, Product, Transaction
from datetime import datetime

# Definisi Blueprint
# Pastikan ini diekspor sebagai 'admin_bp' agar dapat diimpor di app.py
admin_bp = Blueprint('admin', __name__)

# Fungsi helper untuk memeriksa status admin (Mocks: Di lingkungan nyata, ini akan lebih aman)
def is_admin():
    # Asumsi: Kami menyimpan is_admin=True/False di session saat login
    return session.get('is_admin', False)

# === Admin Dashboard ===
@admin_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session or not is_admin():
        flash('Akses ditolak. Anda harus login sebagai Admin.', 'error')
        return redirect(url_for('auth.login'))
    
    # Statistik Global
    total_users = User.query.count()
    total_products = Product.query.count()
    total_transactions = Transaction.query.count()
    low_stock_products = Product.query.filter(Product.stock <= Product.min_stock).all()
    
    # Data untuk dashboard
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_transactions = Transaction.query.order_by(Transaction.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         total_products=total_products,
                         total_transactions=total_transactions,
                         low_stock_products=low_stock_products,
                         recent_users=recent_users,
                         recent_transactions=recent_transactions)

# === Manajemen Pengguna (CRUD) ===
@admin_bp.route('/manage_users')
def manage_users():
    if 'user_id' not in session or not is_admin():
        flash('Akses ditolak.', 'error')
        return redirect(url_for('auth.login'))
    
    # Ambil semua pengguna
    users = User.query.all()
    return render_template('admin/manage_users.html', users=users)

@admin_bp.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if 'user_id' not in session or not is_admin():
        flash('Akses ditolak.', 'error')
        return redirect(url_for('auth.login'))

    user = User.query.get_or_404(user_id)
    
    try:
        db.session.delete(user)
        db.session.commit()
        flash(f'Pengguna {user.username} berhasil dihapus.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Gagal menghapus pengguna: {e}', 'error')
        
    return redirect(url_for('admin.manage_users'))


# === Manajemen Produk (Tambah dan Edit) ===
@admin_bp.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if 'user_id' not in session or not is_admin():
        flash('Akses ditolak.', 'error')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        try:
            # Ambil data dari form
            name = request.form['name']
            description = request.form.get('description', '')
            category = request.form.get('category', '')
            price = float(request.form['price'])
            stock = int(request.form['stock'])
            min_stock = int(request.form['min_stock'])
            sku = request.form.get('sku', '')
            
            # Handle image upload
            image = None
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename != '':
                    # Save file logic here
                    image = file.filename

            new_product = Product(name=name, description=description, category=category, 
                                  price=price, stock=stock, min_stock=min_stock, sku=sku, image=image)
            
            db.session.add(new_product)
            db.session.commit()
            flash(f'Produk "{name}" berhasil ditambahkan.', 'success')
            return redirect(url_for('admin.manage_products'))
        except Exception as e:
            db.session.rollback()
            flash(f'Gagal menambahkan produk. Pastikan format input benar: {e}', 'error')

    return render_template('admin/add_product.html')

@admin_bp.route('/manage_products')
def manage_products():
    if 'user_id' not in session or not is_admin():
        flash('Akses ditolak.', 'error')
        return redirect(url_for('auth.login'))
    
    products = Product.query.all()
    
    # Statistik produk
    total_products = Product.query.count()
    available_products = Product.query.filter(Product.stock > 0).count()
    low_stock_products = Product.query.filter(Product.stock <= Product.min_stock, Product.stock > 0).count()
    out_of_stock_products = Product.query.filter(Product.stock == 0).count()
    
    return render_template('admin/manage_products.html', 
                         products=products,
                         total_products=total_products,
                         available_products=available_products,
                         low_stock_products=low_stock_products,
                         out_of_stock_products=out_of_stock_products)


# === Manajemen Transaksi Global ===
@admin_bp.route('/manage_transactions')
def manage_transactions():
    if 'user_id' not in session or not is_admin():
        flash('Akses ditolak.', 'error')
        return redirect(url_for('auth.login'))
    
    # Ambil semua transaksi dari semua pengguna
    transactions = Transaction.query.all()
    
    # Statistik transaksi
    total_transactions = Transaction.query.count()
    total_purchases = Transaction.query.filter_by(transaction_type='purchase').count()
    total_returns = Transaction.query.filter_by(transaction_type='return').count()
    total_revenue = db.session.query(db.func.sum(Transaction.total_price)).filter_by(transaction_type='purchase').scalar() or 0
    
    return render_template('admin/manage_transactions.html', 
                         transactions=transactions,
                         total_transactions=total_transactions,
                         total_purchases=total_purchases,
                         total_returns=total_returns,
                         total_revenue=total_revenue)