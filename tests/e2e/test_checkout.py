"""
test_checkout.py — Skenario Checkout
Masuk ke halaman /user/checkout?product_id=1,
pastikan form identitas pemesan tersedia/terisi,
dan metode pembayaran (QRIS / Virtual Account) dapat dipilih secara interaktif.
"""
from playwright.sync_api import Page, expect

def test_checkout_identity_and_payment_methods(auth_page: Page, base_url: str):
    # 1. Buka halaman checkout untuk product_id=1
    response = auth_page.goto(f"{base_url}/user/checkout?product_id=1")
    assert response is not None
    assert response.status == 200
    
    # 2. Pastikan form identitas pemesan tersedia
    name_input = auth_page.locator("#coName")
    phone_input = auth_page.locator("#coPhone")
    email_input = auth_page.locator("#coEmail")
    
    expect(name_input).to_be_visible()
    expect(phone_input).to_be_visible()
    expect(email_input).to_be_visible()
    
    # Verifikasi input nama memiliki nilai atau dapat diisi
    current_name = name_input.input_value()
    if not current_name.strip():
        name_input.fill("Angga Operator")
    phone_input.fill("081234567890")
    
    # 3. Verifikasi metode pembayaran default (QRIS)
    qris_method = auth_page.locator("#methodQris")
    expect(qris_method).to_be_visible()
    expect(qris_method).to_have_attribute("data-method", "qris")
    expect(qris_method).to_have_attribute("aria-checked", "true")
    
    # 4. Pilih metode pembayaran Bank Transfer / Virtual Account (VA)
    bank_method = auth_page.locator("#methodBank")
    expect(bank_method).to_be_visible()
    bank_method.click()
    
    # Verifikasi Bank Transfer menjadi aktif dan panel pilihan bank muncul
    expect(bank_method).to_have_attribute("aria-checked", "true")
    expect(qris_method).to_have_attribute("aria-checked", "false")
    
    panel_bank = auth_page.locator("#panelBank")
    expect(panel_bank).to_be_visible()
    
    # Pilih salah satu opsi bank (contoh: BCA atau BNI)
    bca_btn = auth_page.locator("button.co-bank[data-bank='bca']")
    expect(bca_btn).to_be_visible()
    bca_btn.click()
    
    # 5. Beralih kembali ke QRIS
    qris_method.click()
    expect(qris_method).to_have_attribute("aria-checked", "true")
    expect(bank_method).to_have_attribute("aria-checked", "false")
    expect(panel_bank).to_be_hidden()
