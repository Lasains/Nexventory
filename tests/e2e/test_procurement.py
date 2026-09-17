"""
test_procurement.py — Skenario Procurement
Navigasi ke /user/beli-produk, verifikasi halaman merender daftar produk
dengan kode respons HTTP 200 (memastikan bug 500 status='active' telah teratasi).
"""
from playwright.sync_api import Page, expect

def test_procurement_page_renders_200(auth_page: Page, base_url: str):
    # 1. Navigasi ke halaman beli-produk dan tangkap HTTP response
    response = auth_page.goto(f"{base_url}/user/beli-produk")
    
    # 2. Verifikasi status code adalah 200 OK (bukan 500 Internal Server Error)
    assert response is not None, "Response object should not be None"
    assert response.status == 200, f"Expected status 200, got {response.status}"
    
    # 3. Verifikasi title dan heading halaman procurement
    expect(auth_page).to_have_title("Procure Assets - Nexventory")
    expect(auth_page.locator("h1")).to_contain_text("Warehouse Procurement Hub")
    
    # 4. Verifikasi bahwa halaman tidak menampilkan 500 error atau exception stack trace
    body_text = auth_page.locator("body").inner_text()
    assert "Internal Server Error" not in body_text
    assert "500" not in auth_page.title()
    
    # 5. Verifikasi komponen katalog produk dirender
    # Tombol "My Stock Catalog" harus terlihat di header
    catalog_btn = auth_page.locator("a:has-text('My Stock Catalog')")
    expect(catalog_btn).to_be_visible()
