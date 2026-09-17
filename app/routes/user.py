from flask import Blueprint, render_template, request, flash, redirect, url_for, session, jsonify, current_app, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import logging
from app.extensions import db
from app.models.product import Product
from app.models.transaction import Transaction
from datetime import datetime, timedelta
import json
from app.services.midtrans_service import MidtransService
from app.config.payment_config import PaymentConfig

logger = logging.getLogger(__name__)

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

@user_bp.route('/checkout', methods=['GET'])
@login_required
def checkout():
    """Render checkout page with cart data from query params or product_id"""
    cart_data = request.args.get('cart_data', '')
    product_id = request.args.get('product_id', type=int)
    quantity = request.args.get('quantity', 1, type=int)

    cart_items = []
    if cart_data:
        try:
            cart_items = json.loads(cart_data)
        except Exception:
            cart_items = []
    elif product_id:
        prod = Product.query.get(product_id)
        if prod:
            cart_items = [{
                'id': prod.id,
                'name': prod.name,
                'price': int(prod.price),
                'quantity': max(1, quantity),
                'category': prod.category
            }]

    # Fallback if empty: take first active product so page is immediately functional
    if not cart_items:
        first_prod = Product.query.first()
        if first_prod:
            cart_items = [{
                'id': first_prod.id,
                'name': first_prod.name,
                'price': int(first_prod.price),
                'quantity': 1,
                'category': first_prod.category
            }]

    subtotal = sum(item.get('price', 0) * item.get('quantity', 1) for item in cart_items)
    service_fee = 0  # no service fee for now
    total_amount = subtotal + service_fee

    return render_template(
        'user/checkout.html',
        order_items=cart_items,
        subtotal=subtotal,
        service_fee=service_fee,
        total_amount=total_amount,
        midtrans_client_key=PaymentConfig.MIDTRANS_CLIENT_KEY,
        midtrans_is_production=PaymentConfig.MIDTRANS_IS_PRODUCTION
    )


@user_bp.route('/api/payment/create', methods=['POST'])
@login_required
def create_payment():
    """
    Create a Midtrans charge (QRIS or Bank Transfer).
    Expected JSON body:
      {
        "payment_method": "qris" | "bank_transfer",
        "bank": "bca" | "bni" | "bri" | "mandiri",  # only for bank_transfer
        "customer_name": "John Doe",
        "customer_phone": "08123456789",
        "customer_email": "john@example.com",
        "items": [{"id":1,"quantity":2}]  # price is intentionally ignored from client
      }
    NOTE: 'amount' and item 'price' from client are IGNORED.
    Server recomputes authoritative totals from database to prevent price tampering.
    """
    data = request.get_json(silent=True) or {}

    payment_method = data.get('payment_method', 'qris')
    customer_name = data.get('customer_name', current_user.username)
    customer_phone = data.get('customer_phone', '08000000000')
    customer_email = data.get('customer_email', current_user.email or 'customer@nexventory.com')
    raw_items = data.get('items', [])

    if not raw_items:
        return jsonify({'success': False, 'error': 'Item pesanan tidak boleh kosong'}), 400

    if payment_method not in PaymentConfig.SUPPORTED_PAYMENT_METHODS:
        return jsonify({'success': False, 'error': 'Metode pembayaran tidak didukung'}), 400

    # --- Server-side price & stock validation ---
    # Never trust client-supplied price. Recompute from DB.
    validated_items = []
    server_total = 0
    for raw_item in raw_items:
        prod_id = raw_item.get('id')
        if not prod_id:
            return jsonify({'success': False, 'error': 'ID produk tidak valid'}), 400

        prod = Product.query.get(prod_id)
        if not prod:
            return jsonify({'success': False, 'error': f'Produk dengan ID {prod_id} tidak ditemukan'}), 400

        qty = int(raw_item.get('quantity', 1))
        if qty < 1:
            return jsonify({'success': False, 'error': f'Jumlah untuk produk "{prod.name}" tidak valid'}), 400

        if prod.stock < qty:
            return jsonify({
                'success': False,
                'error': f'Stok produk "{prod.name}" tidak mencukupi (tersedia: {prod.stock}, diminta: {qty})'
            }), 400

        item_total = int(prod.price) * qty
        server_total += item_total
        validated_items.append({
            'id': prod.id,
            'name': prod.name,
            'price': int(prod.price),  # authoritative price from DB
            'quantity': qty,
            'category': prod.category,
        })

    if server_total <= 0:
        return jsonify({'success': False, 'error': 'Jumlah pembayaran tidak valid'}), 400

    try:
        svc = MidtransService()

        if payment_method == 'qris':
            result = svc.create_qris_charge(
                amount=server_total,
                customer_name=customer_name,
                customer_email=customer_email,
                customer_phone=customer_phone,
                items=validated_items
            )

            _save_order_transactions(
                user_id=current_user.id,
                order_id=result['order_id'],
                txn_id=result.get('transaction_id'),
                payment_method='qris',
                validated_items=validated_items,
                qr_string=result.get('qr_string')
            )

            return jsonify({
                'success': True,
                'payment_method': 'qris',
                'order_id': result['order_id'],
                'transaction_id': result['transaction_id'],
                'qr_string': result['qr_string'],
                'qr_url': result.get('qr_url', ''),
                'amount': result['amount'],
                'expiry_time': result.get('expiry_time', '')
            })

        elif payment_method == 'bank_transfer':
            bank = data.get('bank', 'bca').lower()
            result = svc.create_bank_transfer_charge(
                bank=bank,
                amount=server_total,
                customer_name=customer_name,
                customer_email=customer_email,
                customer_phone=customer_phone,
                items=validated_items
            )

            _save_order_transactions(
                user_id=current_user.id,
                order_id=result['order_id'],
                txn_id=result.get('transaction_id'),
                payment_method='bank_transfer',
                validated_items=validated_items,
                va_number=result.get('va_number'),
                va_bank=result.get('va_bank')
            )

            return jsonify({
                'success': True,
                'payment_method': 'bank_transfer',
                'order_id': result['order_id'],
                'transaction_id': result['transaction_id'],
                'va_number': result['va_number'],
                'va_bank': result['va_bank'],
                'amount': result['amount'],
                'expiry_time': result.get('expiry_time', '')
            })

    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Payment creation error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


def _save_order_transactions(
    user_id, order_id, txn_id, payment_method, validated_items,
    va_number=None, va_bank=None, qr_string=None
):
    """
    Record transactions in database for a Midtrans order.
    Only accepts pre-validated items (product existence + stock confirmed
    by create_payment). Uses DB-authoritative price — never client price.
    """
    try:
        for item in validated_items:
            prod_id = item['id']  # guaranteed valid by create_payment guard
            qty = item['quantity']
            # Re-fetch from DB to use authoritative price (double-check)
            prod = Product.query.get(prod_id)
            if not prod:
                logger.error(f"Product {prod_id} disappeared between validation and save — skipping")
                continue
            item_total = float(prod.price) * qty
            txn = Transaction(
                product_id=prod.id,
                user_id=user_id,
                quantity=qty,
                total_price=item_total,
                transaction_type='purchase',
                payment_method=payment_method,
                payment_status='pending',
                midtrans_order_id=order_id,
                midtrans_transaction_id=txn_id,
                va_number=va_number,
                va_bank=va_bank,
                qris_string=qr_string
            )
            db.session.add(txn)
        db.session.commit()
    except Exception as e:
        logger.error(f"Error saving order transactions: {e}")
        db.session.rollback()


@user_bp.route('/api/payment/status/<order_id>', methods=['GET'])
@login_required
def check_payment_status(order_id):
    """Poll Midtrans for payment status and sync with local database"""
    try:
        svc = MidtransService()
        result = svc.check_status(order_id)

        # Synchronize local database
        txns = Transaction.query.filter_by(midtrans_order_id=order_id).all()
        if result.get('is_paid'):
            for txn in txns:
                if txn.payment_status not in ('settlement', 'capture'):
                    txn.payment_status = 'settlement'
                    txn.paid_at = datetime.utcnow()
                    if txn.product and txn.product.stock >= txn.quantity:
                        txn.product.stock -= txn.quantity
            db.session.commit()
        elif result.get('status') in ('expire', 'cancel', 'failure', 'deny'):
            for txn in txns:
                txn.payment_status = result.get('status')
            db.session.commit()

        return jsonify({'success': True, **result})
    except Exception as e:
        logger.error(f"Status check error for {order_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/api/payment/cancel/<order_id>', methods=['POST'])
@login_required
def cancel_payment(order_id):
    """Cancel a pending Midtrans transaction"""
    try:
        svc = MidtransService()
        result = svc.cancel_transaction(order_id)
        txns = Transaction.query.filter_by(midtrans_order_id=order_id).all()
        for txn in txns:
            txn.payment_status = 'cancel'
        db.session.commit()
        return jsonify({'success': True, **result})
    except Exception as e:
        logger.error(f"Cancel payment error for {order_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/payment/callback', methods=['POST'])
def payment_callback():
    """
    Midtrans server-to-server notification webhook.
    Midtrans posts JSON here when payment status changes.
    """
    try:
        notification = request.get_json(silent=True) or {}

        order_id = notification.get('order_id', '')
        status_code = notification.get('status_code', '')
        gross_amount = notification.get('gross_amount', '')
        signature_key = notification.get('signature_key', '')
        transaction_status = notification.get('transaction_status', '')
        fraud_status = notification.get('fraud_status', '')
        payment_type = notification.get('payment_type', '')

        # Verify signature
        svc = MidtransService()
        if not svc.verify_webhook_signature(order_id, status_code, gross_amount, signature_key):
            logger.warning(f"Invalid webhook signature for order {order_id}")
            return jsonify({'status': 'invalid signature'}), 403

        logger.info(f"Midtrans webhook: order={order_id} status={transaction_status} payment={payment_type}")

        # Find transactions by midtrans_order_id
        txns = Transaction.query.filter_by(midtrans_order_id=order_id).all()
        for txn in txns:
            txn.payment_status = transaction_status
            if PaymentConfig.is_paid_status(transaction_status):
                if fraud_status in ('accept', '') or not fraud_status:
                    if not txn.paid_at:
                        txn.paid_at = datetime.utcnow()
                        if txn.product and txn.product.stock >= txn.quantity:
                            txn.product.stock -= txn.quantity
        db.session.commit()

        return jsonify({'status': 'ok'}), 200

    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@user_bp.route('/payment/finish')
@login_required
def payment_finish():
    """Redirect target after Midtrans Snap payment completes"""
    order_id = request.args.get('order_id', '')
    status = request.args.get('transaction_status', 'pending')
    return render_template('user/payment_finish.html', order_id=order_id, status=status)

@user_bp.route('/beli-produk')
@login_required
def beli_produk():
    # Get all products from all sellers for user to buy
    products = Product.query.filter(Product.stock > 0).order_by(Product.created_at.desc()).all()

    
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
    
    # Recent transactions for current user
    recent_transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.created_at.desc()).limit(6).all()
    
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
                         chart_revenue_data=chart_revenue_data,
                         recent_transactions=recent_transactions)

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

    # --- IDOR / BOLA Guard ---
    # Only the owner or an admin can modify this transaction
    if transaction.user_id != current_user.id and not current_user.is_admin:
        abort(403)

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

    # --- IDOR / BOLA Guard ---
    # Only the owner or an admin can delete this transaction
    if transaction.user_id != current_user.id and not current_user.is_admin:
        abort(403)

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