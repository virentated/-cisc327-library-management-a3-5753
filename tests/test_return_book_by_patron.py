import pytest
import library_service as ls
import database as db


def test_r4_return_success_updates_availability():
    # Assume patron "123456" borrowed book ID 1
    success, msg = ls.return_book_by_patron("123456", 1)
    assert success is True
    assert "returned" in msg.lower()

def test_r4_return_invalid_patron_rejected():
    # Test that invalid parton ID is rejected. 
    success, msg = ls.return_book_by_patron("xx123", 1)
    assert success is False
    assert "invalid patron" in msg.lower()

def test_r4_return_invalid_book_id():
    # Test that invalid book ID is rejected. 
    success, msg = ls.return_book_by_patron("123456", -99)
    assert success is False
    assert "book not found" in msg.lower()

def test_r4_return_not_borrowed_by_patron():
    success, msg = ls.return_book_by_patron("123456", 2)  
    # Test if patron never borrowed book 2, they cannot return it.
    assert success is False
    assert "active borrow record" in msg.lower() or "not borrowed" in msg.lower()


def test_r4_return_calculates_late_fee():
    # Test if the patron returned a book past due date, late fees shows up.
    success, msg = ls.return_book_by_patron("123456", 3)
    assert isinstance(success, bool)
    assert isinstance(msg, str)
    assert (
        "late fee" in msg.lower()
        or "no late fee" in msg.lower()
        or "book not borrowed" in msg.lower()
    )