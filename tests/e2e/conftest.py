"""
conftest.py — Playwright E2E testing fixtures for Nexventory.
Configured to use Chromium from D:\\backup\\Nexventory\\.browsers.
"""
import os
import pytest
from playwright.sync_api import sync_playwright, expect

# Ensure PLAYWRIGHT_BROWSERS_PATH is set
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", r"D:\backup\Nexventory\.browsers")

BASE_URL = "http://127.0.0.1:5000"
USER_CREDENTIALS = {
    "username": "angga123",
    "password": "@AnGgA123"
}

@pytest.fixture(scope="session")
def base_url():
    return BASE_URL

@pytest.fixture(scope="session")
def credentials():
    return USER_CREDENTIALS

@pytest.fixture(scope="session")
def playwright_instance():
    with sync_playwright() as p:
        yield p

@pytest.fixture(scope="session")
def browser(playwright_instance):
    browser = playwright_instance.chromium.launch(headless=True)
    yield browser
    browser.close()

@pytest.fixture
def page(browser):
    """Standard unauthenticated desktop page."""
    context = browser.new_context(viewport={"width": 1280, "height": 800})
    p = context.new_page()
    yield p
    context.close()

@pytest.fixture
def auth_page(browser):
    """Authenticated desktop page logged in as operator angga123."""
    context = browser.new_context(viewport={"width": 1280, "height": 800})
    p = context.new_page()
    p.goto(f"{BASE_URL}/login")
    p.fill("#username", USER_CREDENTIALS["username"])
    p.fill("#password", USER_CREDENTIALS["password"])
    p.click("button[type='submit']")
    p.wait_for_url(f"{BASE_URL}/user/dashboard**")
    yield p
    context.close()

@pytest.fixture
def mobile_auth_page(browser):
    """Authenticated mobile page (viewport 375x812) logged in as operator angga123."""
    context = browser.new_context(
        viewport={"width": 375, "height": 812},
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1"
    )
    p = context.new_page()
    p.goto(f"{BASE_URL}/login")
    p.fill("#username", USER_CREDENTIALS["username"])
    p.fill("#password", USER_CREDENTIALS["password"])
    p.click("button[type='submit']")
    p.wait_for_url(f"{BASE_URL}/user/dashboard**")
    yield p
    context.close()
