"""
constants.py
============
Engine-agnostic constants shared by both Selenium and Playwright page
objects (page paths, expected titles, error message fragments, etc.).
Keeping these out of individual page objects avoids duplicating literals
across pages/selenium/ and pages/playwright/.
"""

from __future__ import annotations


class Pages:
    """Relative URL paths / fragments used for navigation assertions."""
    LOGIN = ""  # SauceDemo login is the root path
    INVENTORY = "inventory.html"
    CART = "cart.html"
    CHECKOUT_STEP_ONE = "checkout-step-one.html"
    CHECKOUT_STEP_TWO = "checkout-step-two.html"
    CHECKOUT_COMPLETE = "checkout-complete.html"


class Titles:
    """Expected page titles / headings used across assertions."""
    SITE_TITLE = "Swag Labs"
    INVENTORY_HEADING = "Products"
    CART_HEADING = "Your Cart"
    CHECKOUT_HEADING = "Checkout: Your Information"


class ErrorMessages:
    """Fragments of expected SauceDemo validation/error messages."""
    LOCKED_OUT_USER = "Sorry, this user has been locked out."
    MISSING_USERNAME = "Username is required"
    MISSING_PASSWORD = "Password is required"
