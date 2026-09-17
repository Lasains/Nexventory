"""
Midtrans Payment Service
Handles real Midtrans Sandbox API calls for QRIS and Bank Transfer
"""

import uuid
import base64
import requests
import logging
from datetime import datetime
from typing import Optional
from flask import current_app
from app.config.payment_config import PaymentConfig

logger = logging.getLogger(__name__)


class MidtransService:
    """Service for Midtrans payment gateway integration"""

    def __init__(self):
        self.server_key = PaymentConfig.MIDTRANS_SERVER_KEY
        self.client_key = PaymentConfig.MIDTRANS_CLIENT_KEY
        self.api_url = PaymentConfig.MIDTRANS_API_URL
        self.is_production = PaymentConfig.MIDTRANS_IS_PRODUCTION
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': PaymentConfig.get_midtrans_auth_header()
        }

    def _generate_order_id(self, prefix: str = "NXV") -> str:
        """Generate a unique order ID"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        short_uuid = str(uuid.uuid4()).replace('-', '')[:8].upper()
        return f"{prefix}-{timestamp}-{short_uuid}"

    def create_qris_charge(
        self,
        amount: int,
        order_id: Optional[str] = None,
        customer_name: str = "Customer",
        customer_email: str = "customer@nexventory.com",
        customer_phone: str = "08000000000",
        items: Optional[list] = None
    ) -> dict:
        """
        Create QRIS charge via Midtrans Core API

        Returns:
            dict with keys: order_id, qr_string, qr_url, transaction_id, expiry_time, status
        """
        if not order_id:
            order_id = self._generate_order_id("QRIS")

        if amount <= 0:
            raise ValueError("Amount must be greater than 0")

        payload = {
            "payment_type": "qris",
            "transaction_details": {
                "order_id": order_id,
                "gross_amount": int(amount)
            },
            "customer_details": {
                "first_name": customer_name.split()[0] if customer_name else "Customer",
                "last_name": " ".join(customer_name.split()[1:]) if len(customer_name.split()) > 1 else "",
                "email": customer_email,
                "phone": customer_phone
            },
            "qris": {
                "acquirer": "gopay"
            }
        }

        if items:
            payload["item_details"] = [
                {
                    "id": str(item.get("id", idx)),
                    "price": int(item.get("price", 0)),
                    "quantity": int(item.get("quantity", 1)),
                    "name": str(item.get("name", "Produk"))[:50]
                }
                for idx, item in enumerate(items)
            ]

        try:
            response = requests.post(
                f"{self.api_url}/charge",
                json=payload,
                headers=self.headers,
                timeout=30
            )
            data = response.json()

            logger.info(f"Midtrans QRIS charge response: {data.get('status_code')} - {data.get('transaction_id')}")

            if response.status_code not in (200, 201):
                error_msg = data.get('status_message', 'Unknown Midtrans error')
                raise Exception(f"Midtrans error: {error_msg} (code: {data.get('status_code')})")

            # Extract QR string and URL from response
            qr_string = data.get('qr_string', '')
            qr_url = data.get('actions', [{}])[0].get('url', '') if data.get('actions') else ''

            return {
                'order_id': order_id,
                'transaction_id': data.get('transaction_id', ''),
                'qr_string': qr_string,
                'qr_url': qr_url,
                'amount': int(amount),
                'status': data.get('transaction_status', 'pending'),
                'expiry_time': data.get('expiry_time', ''),
                'payment_type': 'qris',
                'merchant_id': data.get('merchant_id', '')
            }

        except requests.Timeout:
            raise Exception("Midtrans API timeout. Silakan coba lagi.")
        except requests.ConnectionError:
            raise Exception("Tidak dapat terhubung ke Midtrans API.")

    def create_bank_transfer_charge(
        self,
        bank: str,
        amount: int,
        order_id: Optional[str] = None,
        customer_name: str = "Customer",
        customer_email: str = "customer@nexventory.com",
        customer_phone: str = "08000000000",
        items: Optional[list] = None
    ) -> dict:
        """
        Create Bank Transfer (Virtual Account) charge via Midtrans Core API

        Args:
            bank: 'bca', 'bni', 'bri', 'mandiri', 'permata'

        Returns:
            dict with keys: order_id, va_number, bank, amount, status, expiry_time
        """
        bank = bank.lower()
        if bank not in PaymentConfig.SUPPORTED_BANKS:
            raise ValueError(f"Bank tidak didukung: {bank}. Pilih: {', '.join(PaymentConfig.SUPPORTED_BANKS)}")

        if not order_id:
            prefix = f"VA{bank.upper()}"
            order_id = self._generate_order_id(prefix)

        if amount <= 0:
            raise ValueError("Amount must be greater than 0")

        # Mandiri uses echannel, others use bank_transfer
        if bank == 'mandiri':
            payload = {
                "payment_type": "echannel",
                "transaction_details": {
                    "order_id": order_id,
                    "gross_amount": int(amount)
                },
                "echannel": {
                    "bill_info1": "Payment for Nexventory",
                    "bill_info2": "Order " + order_id
                },
                "customer_details": {
                    "first_name": customer_name.split()[0] if customer_name else "Customer",
                    "email": customer_email,
                    "phone": customer_phone
                }
            }
        else:
            payload = {
                "payment_type": "bank_transfer",
                "transaction_details": {
                    "order_id": order_id,
                    "gross_amount": int(amount)
                },
                "bank_transfer": {
                    "bank": bank
                },
                "customer_details": {
                    "first_name": customer_name.split()[0] if customer_name else "Customer",
                    "email": customer_email,
                    "phone": customer_phone
                }
            }

        if items:
            payload["item_details"] = [
                {
                    "id": str(item.get("id", idx)),
                    "price": int(item.get("price", 0)),
                    "quantity": int(item.get("quantity", 1)),
                    "name": str(item.get("name", "Produk"))[:50]
                }
                for idx, item in enumerate(items)
            ]

        try:
            response = requests.post(
                f"{self.api_url}/charge",
                json=payload,
                headers=self.headers,
                timeout=30
            )
            data = response.json()

            logger.info(f"Midtrans Bank Transfer charge: {data.get('status_code')} - {data.get('transaction_id')}")

            if response.status_code not in (200, 201):
                error_msg = data.get('status_message', 'Unknown Midtrans error')
                raise Exception(f"Midtrans error: {error_msg} (code: {data.get('status_code')})")

            # Extract VA number depending on bank
            va_number = self._extract_va_number(data, bank)

            return {
                'order_id': order_id,
                'transaction_id': data.get('transaction_id', ''),
                'va_number': va_number,
                'va_bank': bank.upper(),
                'amount': int(amount),
                'status': data.get('transaction_status', 'pending'),
                'expiry_time': data.get('expiry_time', ''),
                'payment_type': 'bank_transfer'
            }

        except requests.Timeout:
            raise Exception("Midtrans API timeout. Silakan coba lagi.")
        except requests.ConnectionError:
            raise Exception("Tidak dapat terhubung ke Midtrans API.")

    def _extract_va_number(self, data: dict, bank: str) -> str:
        """Extract VA number from Midtrans response based on bank"""
        if bank == 'mandiri':
            bill_key = data.get('bill_key', '')
            biller_code = data.get('biller_code', '')
            return f"{biller_code} / {bill_key}"

        va_numbers = data.get('va_numbers', [])
        if va_numbers:
            return va_numbers[0].get('va_number', '')

        # Fallback for permata
        return data.get('permata_va_number', data.get('payment_code', ''))

    def check_status(self, order_id: str) -> dict:
        """
        Check payment status from Midtrans

        Returns:
            dict with: order_id, transaction_id, status, payment_type, amount, transaction_time
        """
        try:
            response = requests.get(
                f"{self.api_url}/{order_id}/status",
                headers=self.headers,
                timeout=15
            )
            data = response.json()

            status_code = data.get('status_code')

            # 404 — not found
            if response.status_code == 404:
                return {
                    'order_id': order_id,
                    'status': 'pending',
                    'is_paid': False,
                    'error': 'Transaction not found'
                }

            transaction_status = data.get('transaction_status', 'pending')
            fraud_status = data.get('fraud_status', '')

            is_paid = PaymentConfig.is_paid_status(transaction_status)
            # For card payments fraud_status must be 'accept', but QRIS/VA don't have fraud_status
            if fraud_status and fraud_status != 'accept' and transaction_status == 'capture':
                is_paid = False

            return {
                'order_id': order_id,
                'transaction_id': data.get('transaction_id', ''),
                'status': transaction_status,
                'fraud_status': fraud_status,
                'is_paid': is_paid,
                'payment_type': data.get('payment_type', ''),
                'amount': data.get('gross_amount', 0),
                'transaction_time': data.get('transaction_time', ''),
                'settlement_time': data.get('settlement_time', ''),
                'expiry_time': data.get('expiry_time', '')
            }

        except requests.Timeout:
            raise Exception("Timeout saat cek status pembayaran.")
        except requests.ConnectionError:
            raise Exception("Tidak dapat terhubung ke Midtrans.")

    def cancel_transaction(self, order_id: str) -> dict:
        """Cancel a pending Midtrans transaction"""
        try:
            response = requests.post(
                f"{self.api_url}/{order_id}/cancel",
                headers=self.headers,
                timeout=15
            )
            data = response.json()

            if response.status_code not in (200, 201):
                raise Exception(f"Gagal membatalkan transaksi: {data.get('status_message')}")

            return {
                'order_id': order_id,
                'status': 'cancelled',
                'message': data.get('status_message', 'Transaction cancelled')
            }

        except requests.Timeout:
            raise Exception("Timeout saat membatalkan transaksi.")

    def verify_webhook_signature(self, order_id: str, status_code: str, gross_amount: str, signature_key: str) -> bool:
        """
        Verify Midtrans webhook notification signature
        SHA512(order_id + status_code + gross_amount + ServerKey)
        """
        import hashlib
        raw = f"{order_id}{status_code}{gross_amount}{self.server_key}"
        expected = hashlib.sha512(raw.encode()).hexdigest()
        return expected == signature_key
