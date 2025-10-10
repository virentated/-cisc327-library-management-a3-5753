import pytest
import library_service as ls
import database as db

def test_r3_invalid_patron_id():
    # Patron ID should be a number, this wil test if function will accept a string
    success, msg = ls.borrow_book_by_patron("abc", 1)
    assert success is False
    assert "patron" in msg.lower()

def test_r3_book_not_found():
    # Testing if function can find a book with a negative number of copies.
    success, msg = ls.borrow_book_by_patron("123456", -99)
    assert success is False
    assert "book" in msg.lower()


def test_r3_valid_id_structure(): 
    # Checking for function outputting boolean and string 
    success, msg = ls.borrow_book_by_patron("123456", 1)
    assert isinstance(success, bool)
    assert isinstance(msg, str)

def test_r3_output_message_contains_title_or_due():
    # Checking if the output message is truly what we set it to be
    success, msg = ls.borrow_book_by_patron("123456", 1)
    assert isinstance(msg, str)
    assert "due" in msg.lower() or "success" in msg.lower() or "not available" in msg.lower()


def test_r3_borrow_limit_enforced():
    # Try borrowing a book with a valid patron ID
    success, msg = ls.borrow_book_by_patron("123456", 1)
    
    # The function should not allow borrowing if the patron already has 5 books
    if not success:
        assert "maximum borrowing limit" in msg.lower() or "not available" in msg.lower() or "book not found" in msg.lower()
