"""
QRIS Service
Handles QR code generation and payment processing
"""

import uuid
import qrcode
import io
import base64
import os
from datetime import datetime, timedelta
from flask import current_app
from app.config.payment_config import PaymentConfig


class QRIService:
    """Service for QRIS payment processing"""
    
    def __init__(self):
        self.merchant_name = PaymentConfig.QRIS_MERCHANT_NAME
        self.expiry_time = PaymentConfig.QRIS_EXPIRY_TIME
        self.storage_path = PaymentConfig.QR_CODE_STORAGE_PATH
    
    def generate_qr_code(self, amount, transaction_id=None, static_folder=None):
        """
        Generate QR code for payment
        
        Args:
            amount (float): Payment amount
            transaction_id (str): Optional transaction ID
            static_folder (str): Static folder path (for testing)
            
        Returns:
            dict: QR code data
        """
        if amount <= 0:
            raise ValueError("Amount must be greater than 0")
        
        # Generate transaction ID if not provided
        if not transaction_id:
            transaction_id = str(uuid.uuid4())
        
        # Create QR code data
        qr_data = f"qris://payment?merchant=nexventory&transaction_id={transaction_id}&amount={amount}"
        
        # Generate QR code image
        qr = qrcode.QRCode(
            version=1,
            error_correction=getattr(qrcode.constants, f'ERROR_CORRECT_{PaymentConfig.QR_CODE_ERROR_CORRECTION}'),
            box_size=10,
            border=PaymentConfig.QR_CODE_BORDER,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Create QR code image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert image to base64
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        
        # Save QR code to static folder (only if in app context)
        qr_filename = f"qris-{transaction_id}.png"
        qrcode_url = f"/{self.storage_path}/{qr_filename}"
        
        try:
            if static_folder:
                # Use provided static folder (for testing)
                qr_dir = os.path.join(static_folder, self.storage_path.replace('static/', ''))
            else:
                # Use Flask app static folder
                static_folder = current_app.static_folder
                qr_dir = os.path.join(static_folder, self.storage_path.replace('static/', ''))
            
            if not os.path.exists(qr_dir):
                os.makedirs(qr_dir)
            
            qr_path = os.path.join(qr_dir, qr_filename)
            img.save(qr_path)
        except RuntimeError:
            # Outside app context, skip file saving
            pass
        
        return {
            'transaction_id': transaction_id,
            'amount': amount,
            'merchant_name': self.merchant_name,
            'qr_data': qr_data,
            'qr_filename': qr_filename,
            'qr_base64': img_base64,
            'qrcode_url': qrcode_url,
            'expiry_time': self.expiry_time,
            'created_at': datetime.now()
        }
    
    def check_payment_status(self, transaction_id, created_at):
        """
        Check payment status for transaction
        
        Args:
            transaction_id (str): Transaction ID
            created_at (datetime): Transaction creation time
            
        Returns:
            dict: Payment status
        """
        # Check if transaction is expired
        if datetime.now() - created_at > timedelta(seconds=self.expiry_time):
            return {
                'paid': False,
                'status': PaymentConfig.STATUS_EXPIRED,
                'message': 'QR code has expired'
            }
        
        # For demo purposes, simulate payment after 30 seconds
        elapsed_seconds = (datetime.now() - created_at).total_seconds()
        if elapsed_seconds > 30:
            return {
                'paid': True,
                'status': PaymentConfig.STATUS_PAID,
                'message': 'Payment successful'
            }
        
        return {
            'paid': False,
            'status': PaymentConfig.STATUS_PENDING,
            'elapsed_time': elapsed_seconds
        }
    
    def validate_transaction(self, transaction_data):
        """
        Validate transaction data
        
        Args:
            transaction_data (dict): Transaction data to validate
            
        Returns:
            bool: True if valid
        """
        required_fields = ['transaction_id', 'amount', 'created_at']
        
        for field in required_fields:
            if field not in transaction_data:
                return False
        
        if transaction_data['amount'] <= 0:
            return False
        
        return True
