import pytest
import library_service as ls
import database as db

def test_r6_search_title_partial_match():
    # Test that all partial matches show up when a book is searched using title.
    results = ls.search_books_in_catalog("great", "title")
    assert any("great" in b["title"].lower() for b in results)

def test_r6_search_author_partial_match():
    # Test that all partial matches show up when a book is searched using author.
    results = ls.search_books_in_catalog("lee", "author")
    assert any("lee" in b["author"].lower() for b in results)

def test_r6_search_isbn_exact_match():
    # Test that the ISBN gives exact match for the searched book.
    results = ls.search_books_in_catalog("9780451524935", "isbn")
    # First assert that we actually got results
    assert results != [], "Expected at least one search result but got none"
    # Then check all returned ISBNs match
    assert all(b["isbn"] == "9780451524935" for b in results)


def test_r6_search_invalid_type_returns_empty():
    # Test that invalid search type is empty. 
    results = ls.search_books_in_catalog("abcde", "random")
    assert results == []

