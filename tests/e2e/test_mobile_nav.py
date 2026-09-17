"""
test_mobile_nav.py — Skenario Mobile Viewport
Menjalankan tes dengan viewport 375x812 (mobile),
memverifikasi tombol hamburger menu sidebar,
dan memastikan drawer menu dapat dibuka dan ditutup (via close button & backdrop)
tanpa menutupi layout utama secara permanen.
"""
import re
from playwright.sync_api import Page, expect

def test_mobile_drawer_navigation(mobile_auth_page: Page):
    page = mobile_auth_page
    
    # 1. Pastikan tombol hamburger menu terlihat di viewport mobile
    hamburger_btn = page.locator("#sidebar-toggle")
    expect(hamburger_btn).to_be_visible()
    
    # 2. Verifikasi status awal: sidebar tersembunyi (-translate-x-full) dan backdrop hidden
    sidebar = page.locator("#sidebar")
    backdrop = page.locator("#sidebar-backdrop")
    
    expect(sidebar).to_have_class(re.compile(r"-translate-x-full"))
    expect(backdrop).to_be_hidden()
    
    # 3. Klik hamburger menu untuk membuka drawer
    hamburger_btn.click()
    
    # Verifikasi sidebar terbuka dan backdrop terlihat
    expect(sidebar).not_to_have_class(re.compile(r"-translate-x-full"))
    expect(backdrop).to_be_visible()
    
    # Verifikasi elemen menu navigasi di dalam sidebar dapat diakses
    overview_link = sidebar.locator("a[href*='/user/dashboard']")
    expect(overview_link).to_be_visible()
    
    procurement_link = sidebar.locator("a[href*='/user/beli-produk']")
    expect(procurement_link).to_be_visible()
    
    # 4. Klik tombol close (#sidebar-close) di dalam sidebar
    close_btn = page.locator("#sidebar-close")
    expect(close_btn).to_be_visible()
    close_btn.click()
    
    # Verifikasi sidebar kembali tertutup dan backdrop tersembunyi
    expect(sidebar).to_have_class(re.compile(r"-translate-x-full"))
    expect(backdrop).to_be_hidden()
    
    # 5. Uji buka kembali dan tutup menggunakan klik backdrop
    hamburger_btn.click()
    expect(sidebar).not_to_have_class(re.compile(r"-translate-x-full"))
    expect(backdrop).to_be_visible()
    
    # Klik backdrop di posisi aman di luar area sidebar (w-64 = 256px, mobile viewport width = 375px, klik di x=320, y=300)
    page.mouse.click(320, 300)
    
    # Verifikasi drawer tertutup setelah backdrop diklik
    expect(sidebar).to_have_class(re.compile(r"-translate-x-full"))
    expect(backdrop).to_be_hidden()
    
    # 6. Pastikan layout utama (main) dapat diakses tanpa terhalang
    main_content = page.locator("main")
    expect(main_content).to_be_visible()
