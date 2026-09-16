"""
Payment Gateway Configuration
For QRIS and other payment methods integration
"""

import os

class PaymentConfig:
    """Payment gateway configuration settings"""
    
    # QRIS Settings
    QRIS_MERCHANT_NAME = "Nexventory Store"
    QRIS_EXPIRY_TIME = 600  # 10 minutes in seconds
    
    # Midtrans Configuration (Sandbox)
    MIDTRANS_SERVER_KEY = os.environ.get('MIDTRANS_SERVER_KEY', 'SB-Mid-server-YOUR_SERVER_KEY')
    MIDTRANS_CLIENT_KEY = os.environ.get('MIDTRANS_CLIENT_KEY', 'SB-Mid-client-YOUR_CLIENT_KEY')
    MIDTRANS_API_URL = "https://api.sandbox.midtrans.com/v2"
    
    # Xendit Configuration (Sandbox)
    XENDIT_SECRET_KEY = os.environ.get('XENDIT_SECRET_KEY', 'xnd_development_YOUR_SECRET_KEY')
    XENDIT_API_URL = "https://api.xendit.co"
    
    # QR Code Settings
    QR_CODE_SIZE = 200
    QR_CODE_BORDER = 4
    QR_CODE_ERROR_CORRECTION = 'L'  # L, M, Q, H
    
    # Supported Payment Gateways
    SUPPORTED_GATEWAYS = ['midtrans', 'xendit']
    
    # Payment Status
    STATUS_PENDING = 'pending'
    STATUS_PAID = 'paid'
    STATUS_EXPIRED = 'expired'
    STATUS_FAILED = 'failed'
    
    # QR Code Storage
    QR_CODE_STORAGE_PATH = 'static/qris'
    
    @staticmethod
    def get_gateway_config(gateway):
        """Get configuration for specific payment gateway"""
        if gateway == 'midtrans':
            return {
                'server_key': PaymentConfig.MIDTRANS_SERVER_KEY,
                'client_key': PaymentConfig.MIDTRANS_CLIENT_KEY,
                'api_url': PaymentConfig.MIDTRANS_API_URL
            }
        elif gateway == 'xendit':
            return {
                'secret_key': PaymentConfig.XENDIT_SECRET_KEY,
                'api_url': PaymentConfig.XENDIT_API_URL
            }
        else:
            raise ValueError(f"Unsupported gateway: {gateway}")
    
    @staticmethod
    def is_supported_gateway(gateway):
        """Check if gateway is supported"""
        return gateway in PaymentConfig.SUPPORTED_GATEWAYS
