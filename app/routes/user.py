from flask import Blueprint, render_template, request, flash, redirect, url_for, session, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from app.extensions import db
from app.models.product import Product
from app.models.transaction import Transaction
from datetime import datetime, timedelta
import json
from app.services.qris_service import QRIService

user_bp = Blueprint('user', __name__)

# Allowed file extensions for image upload
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Add timestamp to avoid filename conflicts
        timestamp = str(int(datetime.now().timestamp()))
        filename = f"{timestamp}_{filename}"
        
        # Create uploads directory if it doesn't exist
        upload_dir = os.path.join(current_app.static_folder, 'uploads')
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        return filename
    return None

@user_bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    if request.method == 'GET':
        # Get cart data from session or localStorage
        cart_data = request.args.get('cart_data')
        if cart_data:
            try:
                cart = json.loads(cart_data)
            except:
                cart = []
        else:
            cart = []
        
        # Calculate order totals
        subtotal = sum(item['price'] * item['quantity'] for item in cart)
        service_fee = subtotal * 0.02  # 2% service fee
        total_amount = subtotal + service_fee
        
        # Mock order items for template
        order_items = []
        for item in cart:
            # Mock product data - in real app, fetch from database
            order_items.append({
                'product': {
                    'name': item['name'],
                    'image': None,
                    'seller_name': 'Penjual Sample'
                },
                'quantity': item['quantity']
            })
    if request.method == 'POST':
        # Process checkout form submission
        customer_name = request.form.get('customer_name')
        customer_phone = request.form.get('customer_phone')
        customer_address = request.form.get('customer_address')
        payment_method = request.form.get('payment_method')
        
        # Get cart data from form or session
        cart_data = request.form.get('cart_data')
        if cart_data:
            try:
                cart_items = json.loads(cart_data)
            except:
                cart_items = []
        else:
            cart_items = []
        
        # Validate form
        if not customer_name or not customer_phone or not customer_address:
            flash('Silakan lengkapi semua field yang wajib diisi', 'error')
            return redirect(url_for('user.checkout'))
        
        # Create order (mock implementation)
        order_number = 'ORD' + str(int(datetime.now().timestamp()))
        total_amount = sum(item['price'] * item['quantity'] for item in cart_items)
        service_fee = total_amount * 0.02
        grand_total = total_amount + service_fee
        
        # Store order in session or database (mock)
        order_data = {
            'id': str(int(datetime.now().timestamp())),
            'order_number': order_number,
            'customer_name': customer_name,
            'customer_phone': customer_phone,
            'customer_address': customer_address,
            'payment_method': payment_method,
            'total_amount': grand_total,
            'status': 'pending',
            'created_at': datetime.now(),
            'items': cart_items
        }
        
        # Store in session for demo
        if 'orders' not in session:
            session['orders'] = []
        session['orders'].append(order_data)
        
        if payment_method == 'qris':
            flash(f'Pesanan {order_number} berhasil dibuat! Silakan scan QR untuk pembayaran.', 'success')
        elif payment_method == 'transfer':
            flash(f'Pesanan {order_number} berhasil dibuat! Silakan transfer ke rekening yang tertera.', 'success')
        elif payment_method == 'cod':
            flash(f'Pesanan {order_number} berhasil dibuat! Barang akan dikirim ke alamat Anda.', 'success')
        
        return redirect(url_for('user.transaction'))
    
    # GET request - show checkout page
    # Get cart data from URL parameter or session
    cart_data = request.args.get('cart_data')
    if cart_data:
        try:
            cart_items = json.loads(cart_data)
        except:
            cart_items = []
    else:
        cart_items = []
    
    # Mock pending orders (from session)
    pending_orders = []
    shipped_orders = []
    
    if 'orders' in session:
        for order in session['orders']:
            if order.get('status') == 'pending':
                pending_orders.append(order)
            elif order.get('shipping_status') in ['shipped', 'delivered']:
                shipped_orders.append(order)
    
    # Add some mock shipped orders for demo
    if not shipped_orders:
        shipped_orders = [
            {
                'id': 'ship1',
                'order_number': 'ORD123456',
                'created_at': datetime.now(),
                'shipping_status': 'shipped',
                'tracking_number': 'JNE001234567890',
                'shipping_address': 'Jl. Sudirman No. 123, Jakarta Pusat',
                'total_amount': 150000,
                'items': [
                    {'product': {'name': 'Laptop ASUS', 'image': 'laptop.jpg'}, 'quantity': 1},
                    {'product': {'name': 'Mouse Logitech', 'image': 'mouse.jpg'}, 'quantity': 2}
                ]
            },
            {
                'id': 'ship2',
                'order_number': 'ORD123457',
                'created_at': datetime.now(),
                'shipping_status': 'delivered',
                'tracking_number': None,
                'shipping_address': 'Jl. Thamrin No. 456, Jakarta Selatan',
                'total_amount': 75000,
                'items': [
                    {'product': {'name': 'Keyboard Mechanical', 'image': 'keyboard.jpg'}, 'quantity': 1}
                ]
            }
        ]
    
    # Calculate totals
    subtotal = sum(item['price'] * item['quantity'] for item in cart_items) if cart_items else 0
    service_fee = subtotal * 0.02
    total_amount = subtotal + service_fee
    
    return render_template('user/checkout.html', 
                         order_items=cart_items,
                         subtotal=subtotal,
                         service_fee=service_fee,
                         total_amount=total_amount,
                         pending_orders=pending_orders,
                         shipped_orders=shipped_orders)

@user_bp.route('/api/qris/generate', methods=['POST'])
@login_required
def generate_qris():
    """Generate QRIS code for payment using API"""
    try:
        # Initialize QRIS service
        qris_service = QRIService()
        
        # Get amount from request
        amount = request.json.get('amount', 0)
        
        # Generate QR code
        qr_data = qris_service.generate_qr_code(amount)
        
        # Store transaction data in session
        if 'qris_transactions' not in session:
            session['qris_transactions'] = {}
        
        session['qris_transactions'][qr_data['transaction_id']] = {
            'transaction_id': qr_data['transaction_id'],
            'amount': qr_data['amount'],
            'merchant_name': qr_data['merchant_name'],
            'created_at': qr_data['created_at'].isoformat(),
            'status': 'pending',
            'qr_filename': qr_data['qr_filename']
        }
        
        return jsonify({
            'success': True,
            'data': qr_data
        })
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@user_bp.route('/api/payment-gateway/generate', methods=['POST'])
@login_required
def generate_payment_gateway_qr():
    """Generate QR code using external payment gateway API (Midtrans/Xendit)"""
    import uuid
    import qrcode
    import io
    import base64
    import requests
    
    try:
        # Generate unique transaction ID
        transaction_id = str(uuid.uuid4())
        amount = request.json.get('amount', 0)
        gateway = request.json.get('gateway', 'midtrans')  # midtrans, xendit
        
        if amount <= 0:
            return jsonify({
                'success': False,
                'error': 'Amount must be greater than 0'
            }), 400
        
        # Mock payment gateway API call
        # In production, replace with actual Midtrans/Xendit API calls
        
        if gateway == 'midtrans':
            # Midtrans API integration (mock)
            gateway_response = {
                'transaction_id': transaction_id,
                'order_id': f'ORDER-{transaction_id[:8]}',
                'gross_amount': amount,
                'payment_type': 'qris',
                'status': 'pending',
                'qr_url': f'https://api.sandbox.midtrans.com/v2/qris/{transaction_id}',
                'expiry_time': 600
            }
        elif gateway == 'xendit':
            # Xendit API integration (mock)
            gateway_response = {
                'id': transaction_id,
                'external_id': f'nexventory-{transaction_id[:8]}',
                'amount': amount,
                'status': 'PENDING',
                'qr_code': f'https://api.xendit.co/qrcode/{transaction_id}',
                'expires_at': datetime.now().timestamp() + 600
            }
        else:
            return jsonify({
                'success': False,
                'error': 'Unsupported payment gateway'
            }), 400
        
        # Generate QR code with gateway data
        qr_data = f"qris://payment?gateway={gateway}&transaction_id={transaction_id}&amount={amount}"
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        
        # Save QR code
        static_folder = current_app.static_folder
        qr_dir = os.path.join(static_folder, 'qris')
        if not os.path.exists(qr_dir):
            os.makedirs(qr_dir)
        
        qr_filename = f"qris-{gateway}-{transaction_id}.png"
        qr_path = os.path.join(qr_dir, qr_filename)
        img.save(qr_path)
        
        # Store transaction data
        if 'gateway_transactions' not in session:
            session['gateway_transactions'] = {}
        
        session['gateway_transactions'][transaction_id] = {
            'transaction_id': transaction_id,
            'gateway': gateway,
            'amount': amount,
            'gateway_response': gateway_response,
            'created_at': datetime.now().isoformat(),
            'status': 'pending',
            'qr_filename': qr_filename
        }
        
        return jsonify({
            'success': True,
            'data': {
                'transaction_id': transaction_id,
                'gateway': gateway,
                'amount': amount,
                'gateway_response': gateway_response,
                'qrcode_url': f'/static/qris/{qr_filename}',
                'qr_base64': img_base64,
                'expiry_time': 600
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@user_bp.route('/api/qris/check-status/<transaction_id>', methods=['GET'])
@login_required
def check_qris_status(transaction_id):
    """Check QRIS payment status"""
    try:
        # Initialize QRIS service
        qris_service = QRIService()
        
        # Get transaction from session
        if 'qris_transactions' not in session or transaction_id not in session['qris_transactions']:
            return jsonify({
                'success': False,
                'error': 'Transaction not found'
            }), 404
        
        transaction = session['qris_transactions'][transaction_id]
        
        # Validate transaction data
        if not qris_service.validate_transaction(transaction):
            return jsonify({
                'success': False,
                'error': 'Invalid transaction data'
            }), 400
        
        # Parse created_at datetime
        created_at = datetime.fromisoformat(transaction['created_at'])
        
        # Check payment status
        status_data = qris_service.check_payment_status(transaction_id, created_at)
        
        # Update transaction status in session
        transaction['status'] = status_data['status']
        
        return jsonify({
            'success': True,
            **status_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@user_bp.route('/beli-produk')
@login_required
def beli_produk():
    # Get all products from all sellers for user to buy
    products = Product.query.filter_by(status='active').order_by(Product.created_at.desc()).all()
    
    # Add seller name to each product (mock data for now)
    for product in products:
        if not hasattr(product, 'seller_name'):
            product.seller_name = f"Toko {product.id}"
        if not hasattr(product, 'original_price'):
            product.original_price = None
    
    return render_template('user/beli_produk.html', products=products)

@user_bp.route('/dashboard')
@login_required
def dashboard():
    from datetime import datetime, timedelta
    from sqlalchemy import func, extract
    import calendar
    
    # Basic statistics
    total_products = Product.query.count()
    low_stock_products_query = Product.query.filter(Product.stock <= Product.min_stock)
    low_stock_products = low_stock_products_query.count()
    low_stock_products_list = low_stock_products_query.all()
    
    # Daily statistics
    today = datetime.now().date()
    today_transactions = Transaction.query.filter(
        func.date(Transaction.created_at) == today,
        Transaction.transaction_type == 'sale'
    ).all()
    
    daily_sales_count = len(today_transactions)
    daily_revenue = sum(t.total_price for t in today_transactions)
    
    # Monthly statistics
    current_month = datetime.now().replace(day=1)
    monthly_transactions = Transaction.query.filter(
        Transaction.created_at >= current_month,
        Transaction.transaction_type == 'sale'
    ).all()
    
    monthly_sales_count = len(monthly_transactions)
    monthly_revenue = sum(t.total_price for t in monthly_transactions)
    
    # Previous month for growth calculation
    if datetime.now().month == 1:
        previous_month = datetime.now().replace(year=datetime.now().year-1, month=12, day=1)
    else:
        previous_month = datetime.now().replace(month=datetime.now().month-1, day=1)
    
    previous_month_end = current_month - timedelta(days=1)
    previous_month_transactions = Transaction.query.filter(
        Transaction.created_at >= previous_month,
        Transaction.created_at < current_month,
        Transaction.transaction_type == 'sale'
    ).all()
    
    previous_month_revenue = sum(t.total_price for t in previous_month_transactions)
    
    # Calculate growth percentage
    if previous_month_revenue > 0:
        monthly_growth = round(((monthly_revenue - previous_month_revenue) / previous_month_revenue) * 100, 1)
    elif monthly_revenue > 0:
        monthly_growth = 100.0
    else:
        monthly_growth = 0.0
    
    # Average transaction value
    avg_transaction_value = round(monthly_revenue / monthly_sales_count, 0) if monthly_sales_count > 0 else 0
    
    # Chart data - Last 12 months
    chart_labels = []
    chart_sales_data = []
    chart_revenue_data = []
    
    current_year = datetime.now().year
    for i in range(12):
        # Calculate month (going back from current month)
        month_offset = (datetime.now().month - 1 - i) % 12
        year_offset = (datetime.now().month - 1 - i) // 12
        chart_month = month_offset + 1
        chart_year = current_year + year_offset
        
        # Get month name in Indonesian
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des']
        chart_labels.insert(0, month_names[month_offset])
        
        # Query sales data for this month
        month_start = datetime(chart_year, chart_month, 1)
        if chart_month == 12:
            month_end = datetime(chart_year + 1, 1, 1)
        else:
            month_end = datetime(chart_year, chart_month + 1, 1)
        
        month_transactions = Transaction.query.filter(
            Transaction.created_at >= month_start,
            Transaction.created_at < month_end,
            Transaction.transaction_type == 'sale'
        ).all()
        
        # Calculate sales count and revenue for this month
        sales_count = len(month_transactions)
        revenue = sum(t.total_price for t in month_transactions)
        
        chart_sales_data.insert(0, sales_count)
        chart_revenue_data.insert(0, revenue)
    
    return render_template('user/dashboard.html',
                         total_products=total_products,
                         low_stock_products=low_stock_products,
                         low_stock_products_list=low_stock_products_list,
                         daily_sales_count=daily_sales_count,
                         daily_revenue=daily_revenue,
                         monthly_sales_count=monthly_sales_count,
                         monthly_revenue=monthly_revenue,
                         monthly_growth=monthly_growth,
                         avg_transaction_value=avg_transaction_value,
                         chart_labels=chart_labels,
                         chart_sales_data=chart_sales_data,
                         chart_revenue_data=chart_revenue_data)

@user_bp.route('/manage_akun')
@login_required
def manage_akun():
    return render_template('user/manage_akun.html')

@user_bp.route('/manage_produk')
@login_required
def manage_produk():
    products = Product.query.all()
    return render_template('user/manage_produk.html', products=products)

@user_bp.route('/manage_produk/add', methods=['POST'])
@login_required
def add_product():
    try:
        name = request.form.get('name')
        category = request.form.get('category')
        stock = int(request.form.get('stock'))
        min_stock = int(request.form.get('min_stock'))
        price = float(request.form.get('price'))
        
        # Handle image upload
        image_filename = None
        if 'image' in request.files:
            image_file = request.files['image']
            if image_file.filename != '':
                # Check file size (max 2MB)
                if len(image_file.read()) > 2 * 1024 * 1024:
                    flash('Ukuran gambar terlalu besar! Maksimal 2MB.', 'error')
                    return redirect(url_for('user.manage_produk'))
                
                # Reset file pointer after reading
                image_file.seek(0)
                
                # Save file
                image_filename = save_uploaded_file(image_file)
                if not image_filename:
                    flash('Format gambar tidak valid! Gunakan JPG, PNG, atau GIF.', 'error')
                    return redirect(url_for('user.manage_produk'))
        
        # Validate input
        if not name or not category or stock is None or min_stock is None or price is None:
            flash('Semua field wajib diisi!', 'error')
            return redirect(url_for('user.manage_produk'))
        
        if stock < 0 or min_stock < 0 or price < 0:
            flash('Stok, stok minimum, dan harga tidak boleh negatif!', 'error')
            return redirect(url_for('user.manage_produk'))
        
        # Create new product
        product = Product(
            name=name,
            category=category,
            stock=stock,
            min_stock=min_stock,
            price=price,
            image=image_filename
        )
        
        db.session.add(product)
        db.session.commit()
        
        flash('Produk berhasil ditambahkan!', 'success')
        return redirect(url_for('user.manage_produk'))
        
    except ValueError:
        flash('Format input tidak valid!', 'error')
        return redirect(url_for('user.manage_produk'))
    except Exception as e:
        db.session.rollback()
        flash('Terjadi kesalahan saat menambahkan produk!', 'error')
        return redirect(url_for('user.manage_produk'))

@user_bp.route('/manage_produk/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            category = request.form.get('category')
            stock = int(request.form.get('stock'))
            min_stock = int(request.form.get('min_stock'))
            price = float(request.form.get('price'))
            
            # Handle image upload
            if 'image' in request.files:
                image_file = request.files['image']
                if image_file.filename != '':
                    # Check file size (max 2MB)
                    if len(image_file.read()) > 2 * 1024 * 1024:
                        flash('Ukuran gambar terlalu besar! Maksimal 2MB.', 'error')
                        return redirect(url_for('user.edit_product', product_id=product_id))
                    
                    # Reset file pointer after reading
                    image_file.seek(0)
                    
                    # Save new file
                    image_filename = save_uploaded_file(image_file)
                    if not image_filename:
                        flash('Format gambar tidak valid! Gunakan JPG, PNG, atau GIF.', 'error')
                        return redirect(url_for('user.edit_product', product_id=product_id))
                    
                    # Delete old image if exists
                    if product.image:
                        old_image_path = os.path.join(current_app.static_folder, 'uploads', product.image)
                        if os.path.exists(old_image_path):
                            os.remove(old_image_path)
                    
                    # Update image filename
                    product.image = image_filename
            
            # Validate input
            if not name or not category or stock is None or min_stock is None or price is None:
                flash('Semua field wajib diisi!', 'error')
                return redirect(url_for('user.edit_product', product_id=product_id))
            
            if stock < 0 or min_stock < 0 or price < 0:
                flash('Stok, stok minimum, dan harga tidak boleh negatif!', 'error')
                return redirect(url_for('user.edit_product', product_id=product_id))
            
            # Update product
            product.name = name
            product.category = category
            product.stock = stock
            product.min_stock = min_stock
            product.price = price
            
            db.session.commit()
            
            flash('Produk berhasil diperbarui!', 'success')
            return redirect(url_for('user.manage_produk'))
            
        except ValueError:
            flash('Format input tidak valid!', 'error')
            return redirect(url_for('user.edit_product', product_id=product_id))
        except Exception as e:
            db.session.rollback()
            flash('Terjadi kesalahan saat memperbarui produk!', 'error')
            return redirect(url_for('user.edit_product', product_id=product_id))
    
    return render_template('user/edit_product.html', product=product)

@user_bp.route('/manage_produk/delete/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        
        # Check if product has transactions
        from app.models.transaction import Transaction
        transactions = Transaction.query.filter_by(product_id=product_id).first()
        
        if transactions:
            flash('Tidak dapat menghapus produk yang memiliki transaksi!', 'error')
            return redirect(url_for('user.manage_produk'))
        
        # Delete product image if exists
        if product.image:
            image_path = os.path.join(current_app.static_folder, 'uploads', product.image)
            if os.path.exists(image_path):
                os.remove(image_path)
        
        db.session.delete(product)
        db.session.commit()
        
        flash('Produk berhasil dihapus!', 'success')
        return redirect(url_for('user.manage_produk'))
        
    except Exception as e:
        db.session.rollback()
        flash('Terjadi kesalahan saat menghapus produk!', 'error')
        return redirect(url_for('user.manage_produk'))

@user_bp.route('/manage_jualan')
@login_required
def manage_jualan():
    from datetime import datetime, timedelta
    from sqlalchemy import func
    
    # Get all products with sales statistics
    products = Product.query.all()
    
    # Calculate sales statistics for each product
    for product in products:
        # Total sold
        total_sold_query = db.session.query(func.sum(Transaction.quantity)).filter(
            Transaction.product_id == product.id,
            Transaction.transaction_type == 'sale'
        ).scalar()
        product.total_sold = total_sold_query or 0
        
        # Total revenue
        total_revenue_query = db.session.query(func.sum(Transaction.total_price)).filter(
            Transaction.product_id == product.id,
            Transaction.transaction_type == 'sale'
        ).scalar()
        product.total_revenue = total_revenue_query or 0
        
        # Today's sales
        today = datetime.now().date()
        today_sold_query = db.session.query(func.sum(Transaction.quantity)).filter(
            Transaction.product_id == product.id,
            Transaction.transaction_type == 'sale',
            func.date(Transaction.created_at) == today
        ).scalar()
        product.today_sold = today_sold_query or 0
    
    return render_template('user/manage_jualan.html', products=products)

@user_bp.route('/tambah_jualan', methods=['GET', 'POST'])
@login_required
def tambah_jualan():
    
    if request.method == 'POST':
        product_id = request.form['product_id']
        quantity = int(request.form['quantity'])
        
        product = Product.query.get(product_id)
        if product and product.stock >= quantity:
            # Kurangi stok
            product.stock -= quantity
            
            # Buat transaksi
            transaction = Transaction(
                product_id=product_id,
                user_id=current_user.id,
                quantity=quantity,
                total_price=product.price * quantity,
                transaction_type='sale'
            )
            
            db.session.add(transaction)
            db.session.commit()
            
            flash('Penjualan berhasil ditambahkan!', 'success')
            return redirect(url_for('user.manage_jualan'))
        else:
            flash('Stok tidak mencukupi!', 'error')
    
    products = Product.query.filter(Product.stock > 0).all()
    
    # Convert products to dict for JSON serialization
    products_data = []
    for product in products:
        product_dict = {
            'id': product.id,
            'name': product.name,
            'category': product.category,
            'price': product.price,
            'stock': product.stock,
            'min_stock': product.min_stock,
            'seller_name': f"Toko {product.id}",
            'original_price': None,
            'image': product.image
        }
        products_data.append(product_dict)
    
    return render_template('user/tambah_jualan.html', products=products, products_data=products_data)
@user_bp.route('/edit_jualan/<int:trans_id>', methods=['GET', 'POST'])
@login_required
def edit_jualan(trans_id):
    transaction = Transaction.query.get_or_404(trans_id)
    product = Product.query.get(transaction.product_id)

    if request.method == 'POST':
        new_qty_raw = request.form.get('quantity')

        # Validasi angka
        try:
            new_qty = int(new_qty_raw)
        except:
            flash('Jumlah tidak valid!', 'error')
            return redirect(url_for('user.edit_jualan', trans_id=trans_id))

        # Hitung perubahan stok
        selisih = new_qty - transaction.quantity  # bisa plus/minus

        if product.stock < selisih:
            flash('Stok tidak mencukupi untuk perubahan ini!', 'error')
            return redirect(url_for('user.edit_jualan', trans_id=trans_id))

        # Update stok
        product.stock -= selisih

        # Update transaksi
        transaction.quantity = new_qty
        transaction.total_price = new_qty * product.price

        try:
            db.session.commit()
            flash('Penjualan berhasil diupdate!', 'success')
        except:
            db.session.rollback()
            flash('Gagal memperbarui penjualan!', 'error')

        return redirect(url_for('user.manage_jualan'))

    return render_template('user/edit_jualan.html',
                           transaction=transaction,
                           product=product)
@user_bp.route('/hapus_jualan/<int:trans_id>', methods=['POST'])
@login_required
def hapus_jualan(trans_id):
    transaction = Transaction.query.get_or_404(trans_id)
    product = Product.query.get(transaction.product_id)

    try:
        # Kembalikan stok
        product.stock += transaction.quantity

        db.session.delete(transaction)
        db.session.commit()

        flash('Penjualan berhasil dihapus!', 'success')
    except:
        db.session.rollback()
        flash('Gagal menghapus penjualan!', 'error')

    return redirect(url_for('user.manage_jualan'))

@user_bp.route('/transaction')
@login_required
def transaction():
    transactions = Transaction.query.filter_by(user_id=current_user.id).all()
    return render_template('user/transaction.html', transactions=transactions)