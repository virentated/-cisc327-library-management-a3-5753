import pytest
import library_service as ls
import database as db

def test_r2_get_all_books_returns_list():
    # Test to ensure the output is a list as intended.
    books = db.get_all_books()
    assert isinstance(books, list)

def test_r2_books_have_fields_if_not_empty():
    # Test to ensure the books cannot have empty fields
    books = db.get_all_books()
    if books:  # only run checks if DB has data
        book = books[0]
        assert "title" in book
        assert "author" in book
        assert "isbn" in book

def test_r2_books_are_dicts():
    # Check to see if each book itself is a dict as intended. 
    books = db.get_all_books()
    for book in books:
        assert isinstance(book, dict)

def test_r2_books_have_copy_counts():
    # Ensure each book has total and available copy counts
    books = db.get_all_books()
    if books:
        for book in books:
            assert "total_copies" in book
            assert "available_copies" in book
            # available should never be greater than total
            assert book["available_copies"] <= book["total_copies"]
