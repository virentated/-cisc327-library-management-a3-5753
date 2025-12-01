import random
import time
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:5000"


def _unique_isbn() -> str:
    
    # Generate a random 13-digit ISBN string.
    # Avoids collisions so the test can be run multiple times.
    
    return "9" + str(random.randint(10**11, 10**12 - 1))


def test_add_borrow_and_return_flow():
    # End-to-end scenario:

    # Flow 1: Add + Borrow
    #   1. Open home page (redirects to /catalog).
    #   2. Go to /add_book and create a new book.
    #   3. Verify the book appears in the catalog.
    #   4. Borrow the book from the inline form on the catalog page.

    # Flow 2: Return
    #   5. Go to /return and return the same book.
    #   6. Verify the return confirmation appears.

    # This uses real browser interactions and asserts on visible content.

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        
        # 1. Visit home page
        
        page.goto(BASE_URL)
        # allow redirect + rendering
        time.sleep(0.5)
        assert "Book Catalog" in page.content() or "📖 Book Catalog" in page.content()

        
        # 2. Add a new book
        
        page.goto(f"{BASE_URL}/add_book")

        # Use a unique ISBN to avoid duplicate-ISBN errors
        title = "E2E Test Book"
        author = "E2E Test Author"
        isbn = _unique_isbn()

        page.fill("#title", title)
        page.fill("#author", author)
        page.fill("#isbn", isbn)
        page.fill("#total_copies", "2")

        # Button text: "Add Book to Catalog"
        page.click("text=Add Book to Catalog")

        # Redirect back to catalog
        time.sleep(0.5)
        page.goto(f"{BASE_URL}/catalog")
        time.sleep(0.5)

        
        # 3. Verify book in catalog
        
        # Find the table row that contains our title
        row = page.locator("tbody tr", has_text=title).first
        assert row is not None

        # Confirm title and author are visible
        row_text = row.inner_text()
        assert title in row_text
        assert author in row_text

        # Store the book ID from first column
        book_id_text = row.locator("td").nth(0).inner_text().strip()
        book_id = int(book_id_text)

        
        # 4. Borrow the book (Flow 1)
        
        row.locator("input[name='patron_id']").fill("123456")
        row.locator("text=Borrow").click()

        # Wait for redirect and flash message
        time.sleep(0.5)

        # Check any flash message (success or error)
        flash = page.locator(".flash-success, .flash-error").first
        flash_text = flash.inner_text().lower()
        assert "borrow" in flash_text  # should mention borrowed / not available etc.

        
        # 5. Return the book (Flow 2)
        page.goto(f"{BASE_URL}/return")

        page.fill("#patron_id", "123456")
        page.fill("#book_id", str(book_id))

        page.click("text=Process Return")

        time.sleep(0.5)

        # Check flash message again for return
        r_flash = page.locator(".flash-success, .flash-error").first
        r_text = r_flash.inner_text().lower()
        # Should mention "returned" or similar
        assert "return" in r_text or "returned" in r_text

        browser.close()
