import pytest
import library_service as ls
import database as db

def test_add_book_valid_input():
    #Test adding a book with valid input.
   
    success, message = ls.add_book_to_catalog("Test Book", "TestAuthor", "1111181111811", 5)
    assert success == True
    assert "successfully added" in message.lower()
    

def test_add_book_invalid_isbn_too_short():
    #Test adding a book with ISBN too short
    success, message = ls.add_book_to_catalog("Test Book", "Test Author", "123456789", 5)
    
    assert success == False
    assert "13 digits" in message

def test_r1_missing_title():
    #Test adding book with no title"
    success, msg = ls.add_book_to_catalog("", "Author", "1234567890123", 5)
    assert success is False
    assert "title" in msg.lower()

def test_r1_author_too_long():
    #Testing if the function will accept authror name being too long.
    long_author = "A" * 101
    success, msg = ls.add_book_to_catalog("Book", long_author, "1234567890123", 5)
    assert success is False
    assert "author" in msg.lower()

def test_r1_invalid_copies():
    # Testting if the function will accept negative copies of a book.
    success, msg = ls.add_book_to_catalog("Book", "Author", "1234567890123", -2)
    assert success is False
    assert "positive" in msg.lower()
