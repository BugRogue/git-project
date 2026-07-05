"""
inventory_locators.py
======================
Locators for the SauceDemo post-login inventory ("Products") page.
"""

from __future__ import annotations

from selenium.webdriver.common.by import By


class InventoryLocatorsSelenium:
    PAGE_TITLE = (By.CLASS_NAME, "title")
    INVENTORY_ITEMS = (By.CLASS_NAME, "inventory_item")
    CART_ICON = (By.CLASS_NAME, "shopping_cart_link")
    MENU_BUTTON = (By.ID, "react-burger-menu-btn")
    LOGOUT_LINK = (By.ID, "logout_sidebar_link")


class InventoryLocatorsPlaywright:
    PAGE_TITLE = ".title"
    INVENTORY_ITEMS = ".inventory_item"
    CART_ICON = ".shopping_cart_link"
    MENU_BUTTON = "#react-burger-menu-btn"
    LOGOUT_LINK = "#logout_sidebar_link"
