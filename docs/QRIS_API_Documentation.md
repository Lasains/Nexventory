# QRIS API Documentation

## Overview

Nexventory now supports QR code generation for payments using a robust API system. The implementation includes:

- **QR Code Generation API** - Generate QR codes for payments
- **Payment Status Check API** - Check payment status in real-time
- **Payment Gateway Integration** - Ready for Midtrans/Xendit integration
- **Service Layer Architecture** - Clean separation of concerns

## API Endpoints

### 1. Generate QR Code

**Endpoint:** `POST /user/api/qris/generate`

**Headers:**
- `Content-Type: application/json`
- Authentication required (login)

**Request Body:**
```json
{
    "amount": 100000
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "transaction_id": "uuid-string",
        "amount": 100000,
        "merchant_name": "Nexventory Store",
        "qr_data": "qris://payment?merchant=nexventory&transaction_id=uuid&amount=100000",
        "qr_filename": "qris-uuid.png",
        "qr_base64": "base64-encoded-image",
        "qrcode_url": "/static/qris/qris-uuid.png",
        "expiry_time": 600,
        "created_at": "2025-12-01T11:00:00"
    }
}
```

### 2. Check Payment Status

**Endpoint:** `GET /user/api/qris/check-status/{transaction_id}`

**Headers:**
- Authentication required (login)

**Response:**
```json
{
    "success": true,
    "paid": false,
    "status": "pending",
    "elapsed_time": 15.5
}
```

**Status Values:**
- `pending` - Waiting for payment
- `paid` - Payment successful
- `expired` - QR code expired (after 10 minutes)

### 3. Payment Gateway Integration (Future)

**Endpoint:** `POST /user/api/payment-gateway/generate`

**Request Body:**
```json
{
    "amount": 100000,
    "gateway": "midtrans"  // or "xendit"
}
```

## Implementation Details

### Service Layer

The QRIS functionality is implemented using a service layer pattern:

- **QRIService** (`app/services/qris_service.py`) - Core QRIS logic
- **PaymentConfig** (`app/config/payment_config.py`) - Configuration management
- **Routes** (`app/routes/user.py`) - API endpoints

### Features

1. **QR Code Generation**
   - Uses `qrcode` library with PIL support
   - Saves QR codes to `static/qris/` directory
   - Supports base64 encoding for direct display
   - Configurable size and error correction

2. **Transaction Management**
   - Session-based transaction storage
   - Automatic expiry after 10 minutes
   - Unique transaction IDs using UUID4

3. **Payment Simulation**
   - Demo mode: Auto-approves payment after 30 seconds
   - Real-time status checking every 3 seconds
   - Automatic QR code regeneration on expiry

4. **Error Handling**
   - Comprehensive error responses
   - Input validation
   - Exception handling

## Frontend Integration

The checkout page (`templates/user/checkout.html`) includes:

- **QR Code Display** - Shows generated QR code
- **Payment Timer** - 10-minute countdown timer
- **Status Polling** - Automatic status checking
- **User Feedback** - Success/error messages

## Configuration

### Environment Variables

For production deployment with real payment gateways:

```bash
# Midtrans
MIDTRANS_SERVER_KEY=your-server-key
MIDTRANS_CLIENT_KEY=your-client-key

# Xendit
XENDIT_SECRET_KEY=your-secret-key
```

### QR Code Settings

Edit `app/config/payment_config.py`:

```python
QRIS_MERCHANT_NAME = "Your Store Name"
QRIS_EXPIRY_TIME = 600  # seconds
QR_CODE_SIZE = 200  # pixels
QR_CODE_BORDER = 4  # border size
```

## Usage Example

### JavaScript Frontend

```javascript
// Generate QR code
async function generateQRCode(amount) {
    const response = await fetch('/user/api/qris/generate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ amount: amount })
    });
    
    const data = await response.json();
    
    if (data.success) {
        // Display QR code
        document.getElementById('qr-image').src = data.data.qrcode_url;
        
        // Start status checking
        checkPaymentStatus(data.data.transaction_id);
    }
}

// Check payment status
async function checkPaymentStatus(transactionId) {
    const response = await fetch(`/user/api/qris/check-status/${transactionId}`);
    const data = await response.json();
    
    if (data.success && data.paid) {
        // Payment successful
        showSuccessMessage();
    } else if (data.status === 'expired') {
        // QR code expired
        generateNewQRCode();
    }
}
```

## Security Considerations

1. **Authentication Required** - All endpoints require login
2. **Input Validation** - Amount validation and sanitization
3. **Session Management** - Secure transaction storage
4. **Rate Limiting** - Consider implementing rate limiting for production

## Future Enhancements

1. **Real Payment Gateway Integration**
   - Midtrans QRIS integration
   - Xendit QR code integration
   - Webhook support for payment notifications

2. **Database Storage**
   - Replace session storage with database
   - Transaction history and analytics
   - Refund and cancellation support

3. **Enhanced Features**
   - Multi-merchant support
   - Custom branding on QR codes
   - SMS/email notifications
   - Receipt generation

## Testing

### Unit Tests

```python
# Test QR code generation
def test_generate_qr_code():
    service = QRIService()
    result = service.generate_qr_code(100000)
    
    assert result['amount'] == 100000
    assert 'transaction_id' in result
    assert result['qrcode_url'] is not None
```

### Manual Testing

1. Navigate to checkout page
2. Select QRIS payment method
3. Click "Bayar Sekarang"
4. Verify QR code generation
5. Wait 30 seconds for demo payment success
6. Verify status checking functionality

## Troubleshooting

### Common Issues

1. **QR Code Not Displaying**
   - Check `static/qris/` directory permissions
   - Verify QR code library installation: `pip install qrcode[pil]`

2. **Payment Status Not Updating**
   - Check browser console for JavaScript errors
   - Verify API endpoints are accessible

3. **Transaction Not Found**
   - Clear browser session
   - Check session storage configuration

### Debug Mode

Enable debug mode in Flask:

```python
app.run(debug=True)
```

This will provide detailed error messages and stack traces.
