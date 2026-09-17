"""
test_sales_stock.py — Skenario Sales & Stock
Buka /user/tambah_jualan, lakukan penjualan 1 unit produk,
dan verifikasi perubahannya tercatat di /user/manage_jualan serta /user/transaction.
"""
from playwright.sync_api import Page, expect

def test_record_sale_and_verify_records(auth_page: Page, base_url: str):
    # 1. Buka halaman tambah jualan
    auth_page.goto(f"{base_url}/user/tambah_jualan")
    expect(auth_page).to_have_title("Record Sale - Nexventory")
    expect(auth_page.locator("h1")).to_contain_text("Outbound Sales Dispatch")
    
    # 2. Pilih produk dari dropdown (pilih opsi produk yang tersedia)
    product_select = auth_page.locator("#product_id")
    expect(product_select).to_be_visible()
    
    # Dapatkan seluruh opsi produk yang memiliki value (bukan placeholder disabled)
    options = product_select.locator("option:not([disabled])")
    count = options.count()
    assert count > 0, "Harus ada minimal satu produk dengan stok > 0 untuk diuji"
    
    # Pilih produk pertama
    selected_value = options.first.get_attribute("value")
    product_select.select_option(value=selected_value)
    
    # 3. Pastikan quantity diset ke 1
    qty_input = auth_page.locator("#quantity")
    qty_input.fill("1")
    
    # 4. Klik submit form (Confirm Dispatch)
    submit_btn = auth_page.locator("button[type='submit']")
    submit_btn.click()
    
    # 5. Verifikasi redirect ke halaman /user/manage_jualan
    auth_page.wait_for_url(f"{base_url}/user/manage_jualan**")
    assert "/user/manage_jualan" in auth_page.url
    expect(auth_page.locator("h1")).to_contain_text("Sales & Fulfillment Ledger")
    
    # 6. Verifikasi pencatatan di /user/transaction (Movement Ledger)
    auth_page.goto(f"{base_url}/user/transaction")
    expect(auth_page).to_have_title("Movement Ledger - Nexventory")
    expect(auth_page.locator("h1")).to_contain_text("Warehouse Movement & Audit Ledger")
    
    # Verifikasi ada minimal satu transaksi dengan badge OUTBOUND (SALE)
    sale_badge = auth_page.locator("tbody#txnTableBody span:has-text('OUTBOUND (SALE)')")
    expect(sale_badge.first).to_be_visible()
