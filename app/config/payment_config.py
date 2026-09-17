"""
Payment Gateway Configuration
Midtrans Sandbox integration for QRIS and Bank Transfer
"""

import os


class PaymentConfig:
    """Payment gateway configuration settings"""

    # QRIS Settings
    QRIS_MERCHANT_NAME = "Nexventory Store"
    QRIS_EXPIRY_TIME = 600  # 10 minutes in seconds

    # Midtrans Configuration (Sandbox)
    MIDTRANS_SERVER_KEY = os.environ.get('MIDTRANS_SERVER_KEY', 'Mid-server-2MeFj8sHTXv4iFs2uZ5GXS9T')
    MIDTRANS_CLIENT_KEY = os.environ.get('MIDTRANS_CLIENT_KEY', 'Mid-client-YTcdp07QE4IXCQCN')
    MIDTRANS_MERCHANT_ID = os.environ.get('MIDTRANS_MERCHANT_ID', 'M747448055')
    MIDTRANS_IS_PRODUCTION = os.environ.get('MIDTRANS_IS_PRODUCTION', 'false').lower() == 'true'

    # Midtrans API URLs
    MIDTRANS_API_URL = "https://api.sandbox.midtrans.com/v2" if not MIDTRANS_IS_PRODUCTION else "https://api.midtrans.com/v2"
    MIDTRANS_SNAP_URL = "https://app.sandbox.midtrans.com/snap/snap.js" if not MIDTRANS_IS_PRODUCTION else "https://app.midtrans.com/snap/snap.js"

    # QR Code Settings
    QR_CODE_SIZE = 200
    QR_CODE_BORDER = 4
    QR_CODE_ERROR_CORRECTION = 'L'  # L, M, Q, H

    # Supported Payment Methods
    SUPPORTED_PAYMENT_METHODS = ['qris', 'bank_transfer']
    SUPPORTED_BANKS = ['bca', 'bni', 'bri', 'mandiri', 'permata']

    # Payment Status (mirroring Midtrans transaction_status)
    STATUS_PENDING = 'pending'
    STATUS_PAID = 'settlement'
    STATUS_CAPTURE = 'capture'
    STATUS_EXPIRED = 'expire'
    STATUS_FAILED = 'failure'
    STATUS_CANCELLED = 'cancel'
    STATUS_DENY = 'deny'

    # QR Code Storage
    QR_CODE_STORAGE_PATH = 'static/qris'

    @staticmethod
    def get_midtrans_auth_header() -> str:
        """Return Basic Auth header value for Midtrans API"""
        import base64
        key_bytes = f"{PaymentConfig.MIDTRANS_SERVER_KEY}:".encode('utf-8')
        return "Basic " + base64.b64encode(key_bytes).decode('utf-8')

    @staticmethod
    def is_paid_status(status: str) -> bool:
        """Check if a Midtrans status represents a successful payment"""
        return status in [PaymentConfig.STATUS_PAID, PaymentConfig.STATUS_CAPTURE]
