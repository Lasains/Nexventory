import os
import re
import logging
from datetime import datetime
from flask import (
    Blueprint, render_template, redirect, url_for, 
    request, flash, session, current_app
)
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import or_

# Import database dan model
from app.extensions import db
# ASUMSI: oauth diinisialisasi di __init__.py atau extensions.py
# Jika oauth ada di extensions.py, ubah menjadi: from app.extensions import oauth
from app import oauth 
from app.models.user import User

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, 'Password minimal 8 karakter'
    if not re.search(r'[A-Z]', password):
        return False, 'Password harus mengandung setidaknya 1 huruf besar'
    if not re.search(r'[a-z]', password):
        return False, 'Password harus mengandung setidaknya 1 huruf kecil'
    if not re.search(r'[0-9]', password):
        return False, 'Password harus mengandung setidaknya 1 angka'
    return True, ''

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
        
    if request.method == 'POST':
        try:
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            
            if not username or not password:
                flash('Username dan password harus diisi', 'error')
                return render_template('login.html', username=username), 400
            
            # Mencari user berdasarkan username ATAU email
            user = User.query.filter(
                or_(
                    User.username == username,
                    User.email == username
                )
            ).first()
            
            # Cek password menggunakan method di model User
            if not user or not user.check_password(password):
                flash('Username/email atau password salah!', 'error')
                return render_template('login.html', username=username), 401
            
            # Login menggunakan Flask-Login
            login_user(user)
            
            # Update last login
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Set session data for compatibility
            session['user_id'] = user.id
            session['role'] = user.role
            
            flash('Login berhasil!', 'success')
            
            # Redirect user ke halaman yang diminta sebelumnya atau default
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                if user.role == 'admin':
                    next_page = url_for('admin.dashboard') # Pastikan endpoint ini ada
                elif user.role == 'user':
                    next_page = url_for("user.dashboard")
                else:
                    next_page = url_for('main.index') # Default fallback
            
            return redirect(next_page)
                
        except Exception as e:
            current_app.logger.error(f'Login error: {str(e)}', exc_info=True)
            flash(str(e), 'error')
            return render_template('login.html', username=username), 500
    
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        
        errors = []
        
        # Validasi Input
        if not username: errors.append('Username wajib diisi')
        if not email: errors.append('Email wajib diisi')
        if not password: errors.append('Password wajib diisi')
        if not confirm_password: errors.append('Konfirmasi password wajib diisi')
        
        if username:
            if len(username) < 3:
                errors.append('Username minimal 3 karakter')
            if not re.match(r'^[a-zA-Z0-9_]+$', username):
                errors.append('Username hanya boleh huruf, angka, dan underscore')
            if User.query.filter(User.username.ilike(username)).first():
                errors.append('Username sudah digunakan')
        
        if email:
            if not validate_email(email):
                errors.append('Format email tidak valid')
            if User.query.filter(User.email.ilike(email)).first():
                errors.append('Email sudah terdaftar')
        
        if password:
            is_valid, pwd_error = validate_password(password)
            if not is_valid:
                errors.append(pwd_error)
            if password != confirm_password:
                errors.append('Password dan konfirmasi password tidak cocok')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('register.html', username=username, email=email, 
                                 first_name=first_name, last_name=last_name), 400
        
        try:
            # Buat object user dengan password
            new_user = User(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role='user'
            )
            
            db.session.add(new_user)
            db.session.commit()
            
            flash('Registrasi berhasil! Silakan login.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error creating user: {str(e)}', exc_info=True)
            flash(str(e), 'error')
            return render_template('register.html', username=username, email=email), 500
    
    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear() # Hapus semua session custom
    return redirect(url_for('main.index'))
