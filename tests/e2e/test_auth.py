"""
test_auth.py — Skenario Auth
Verifikasi alur login operator dengan kredensial angga123 / @AnGgA123
dan memastikan redirect sukses ke /user/dashboard.
"""
from playwright.sync_api import Page, expect

def test_login_success(page: Page, base_url: str, credentials: dict):
    # 1. Buka halaman login
    page.goto(f"{base_url}/login")
    expect(page).to_have_title("Sign In - Nexventory")
    
    # 2. Isi form autentikasi
    username_input = page.locator("#username")
    password_input = page.locator("#password")
    
    expect(username_input).to_be_visible()
    expect(password_input).to_be_visible()
    
    username_input.fill(credentials["username"])
    password_input.fill(credentials["password"])
    
    # 3. Klik tombol submit
    submit_btn = page.locator("button[type='submit']")
    expect(submit_btn).to_be_visible()
    submit_btn.click()
    
    # 4. Verifikasi redirect sukses ke dashboard
    page.wait_for_url(f"{base_url}/user/dashboard**")
    assert "/user/dashboard" in page.url
    
    # 5. Verifikasi elemen dashboard muncul
    expect(page.locator("h1")).to_contain_text("Operational Command Hub")
    expect(page.locator("aside#sidebar")).to_be_visible()
