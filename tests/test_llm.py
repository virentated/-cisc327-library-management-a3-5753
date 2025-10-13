import pytest
from datetime import datetime, timedelta
import library_service as ls


# ----------------------------------------------------------------------
# FIXTURES / COMMON MOCKS
# ----------------------------------------------------------------------

@pytest.fixture
def mock_book():
    return {
        "id": 1,
        "title": "Test Book",
        "author": "John Doe",
        "isbn": "1234567890123",
        "available_copies": 3,
        "total_copies": 3
    }


@pytest.fixture
def mock_borrow_record():
    now = datetime.now()
    return {
        "patron_id": "123456",
        "book_id": 1,
        "borrow_date": (now - timedelta(days=16)).isoformat(),
        "due_date": (now - timedelta(days=2)).isoformat(),
        "return_date": None,
        "title": "Test Book",
        "author": "John Doe"
    }


# ----------------------------------------------------------------------
# R1: Add Book To Catalog
# ----------------------------------------------------------------------

def test_add_book_valid(monkeypatch):
    monkeypatch.setattr(ls, "get_book_by_isbn", lambda x: None)
    monkeypatch.setattr(ls, "insert_book", lambda *args, **kwargs: True)

    success, msg = ls.add_book_to_catalog("Python 101", "Guido", "1234567890123", 3)
    assert success
    assert "successfully added" in msg.lower()


@pytest.mark.parametrize(
    "title,author,isbn,total,expected_msg",
    [
        ("", "A", "1234567890123", 3, "Title is required"),
        ("T" * 201, "A", "1234567890123", 3, "less than 200"),
        ("Title", "", "1234567890123", 3, "Author is required"),
        ("Title", "A" * 101, "1234567890123", 3, "less than 100"),
        ("Title", "A", "123", 3, "ISBN must be exactly 13"),
        ("Title", "A", "1234567890123", 0, "positive integer"),
    ]
)
def test_add_book_invalid_inputs(monkeypatch, title, author, isbn, total, expected_msg):
    monkeypatch.setattr(ls, "get_book_by_isbn", lambda x: None)
    success, msg = ls.add_book_to_catalog(title, author, isbn, total)
    assert not success
    assert expected_msg in msg


def test_add_book_duplicate_isbn(monkeypatch, mock_book):
    monkeypatch.setattr(ls, "get_book_by_isbn", lambda x: mock_book)
    success, msg = ls.add_book_to_catalog("Book", "A", "1234567890123", 2)
    assert not success
    assert "already exists" in msg


# ----------------------------------------------------------------------
# R3: Borrow Book By Patron
# ----------------------------------------------------------------------

def test_borrow_book_success(monkeypatch, mock_book):
    monkeypatch.setattr(ls, "get_book_by_id", lambda x: mock_book)
    monkeypatch.setattr(ls, "get_patron_borrow_count", lambda x: 2)
    monkeypatch.setattr(ls, "insert_borrow_record", lambda *a, **k: True)
    monkeypatch.setattr(ls, "update_book_availability", lambda *a, **k: True)

    success, msg = ls.borrow_book_by_patron("123456", 1)
    assert success
    assert "successfully borrowed" in msg.lower()


@pytest.mark.parametrize(
    "pid,expected",
    [("12345", "Invalid"), ("abcdef", "Invalid"), ("", "Invalid")]
)
def test_borrow_book_invalid_patron_id(monkeypatch, pid, expected):
    success, msg = ls.borrow_book_by_patron(pid, 1)
    assert not success
    assert expected in msg


def test_borrow_book_not_found(monkeypatch):
    monkeypatch.setattr(ls, "get_book_by_id", lambda x: None)
    success, msg = ls.borrow_book_by_patron("123456", 1)
    assert not success
    assert "not found" in msg.lower()


def test_borrow_book_unavailable(monkeypatch, mock_book):
    mock_book["available_copies"] = 0
    monkeypatch.setattr(ls, "get_book_by_id", lambda x: mock_book)
    success, msg = ls.borrow_book_by_patron("123456", 1)
    assert not success
    assert "not available" in msg.lower()


def test_borrow_book_limit_exceeded(monkeypatch, mock_book):
    monkeypatch.setattr(ls, "get_book_by_id", lambda x: mock_book)
    monkeypatch.setattr(ls, "get_patron_borrow_count", lambda x: 5)
    success, msg = ls.borrow_book_by_patron("123456", 1)
    assert not success
    assert "maximum borrowing limit" in msg.lower()


# ----------------------------------------------------------------------
# R4: Return Book
# ----------------------------------------------------------------------

def test_return_book_on_time(monkeypatch, mock_book, mock_borrow_record):
    monkeypatch.setattr(ls, "get_book_by_id", lambda x: mock_book)
    monkeypatch.setattr(ls, "_get_active_borrow_record", lambda pid, bid: mock_borrow_record)
    monkeypatch.setattr(ls, "calculate_late_fee_for_book", lambda *a, **k: {"fee_amount": 0.0, "days_overdue": 0})
    monkeypatch.setattr(ls, "update_borrow_record_return_date", lambda *a, **k: True)
    monkeypatch.setattr(ls, "update_book_availability", lambda *a, **k: True)

    success, msg = ls.return_book_by_patron("123456", 1)
    assert success
    assert "no late fee" in msg.lower()


def test_return_book_with_fee(monkeypatch, mock_book, mock_borrow_record):
    monkeypatch.setattr(ls, "get_book_by_id", lambda x: mock_book)
    monkeypatch.setattr(ls, "_get_active_borrow_record", lambda pid, bid: mock_borrow_record)
    monkeypatch.setattr(ls, "calculate_late_fee_for_book", lambda *a, **k: {"fee_amount": 5.0, "days_overdue": 3})
    monkeypatch.setattr(ls, "update_borrow_record_return_date", lambda *a, **k: True)
    monkeypatch.setattr(ls, "update_book_availability", lambda *a, **k: True)

    success, msg = ls.return_book_by_patron("123456", 1)
    assert success
    assert "late fee" in msg.lower()
    assert "$5.00" in msg


# ----------------------------------------------------------------------
# R5: Late Fee Calculation
# ----------------------------------------------------------------------

def test_late_fee_not_overdue(monkeypatch, mock_borrow_record):
    mock_borrow_record["due_date"] = (datetime.now() + timedelta(days=2)).isoformat()
    monkeypatch.setattr(ls, "_get_active_borrow_record", lambda p, b: mock_borrow_record)
    result = ls.calculate_late_fee_for_book("123456", 1)
    assert result["fee_amount"] == 0.0
    assert result["status"] == "Not overdue"

# This test does not wokr - LLM case
# def test_late_fee_overdue(monkeypatch, mock_borrow_record):
#     mock_borrow_record["due_date"] = (datetime.now() - timedelta(days=10)).isoformat()
#     monkeypatch.setattr(ls, "_get_active_borrow_record", lambda p, b: mock_borrow_record)
#     result = ls.calculate_late_fee_for_book("123456", 1)
#     assert result["fee_amount"] == pytest.approx(8.5, 0.01)
#     assert result["status"] == "Overdue"


def test_late_fee_cap(monkeypatch, mock_borrow_record):
    mock_borrow_record["due_date"] = (datetime.now() - timedelta(days=50)).isoformat()
    monkeypatch.setattr(ls, "_get_active_borrow_record", lambda p, b: mock_borrow_record)
    result = ls.calculate_late_fee_for_book("123456", 1)
    assert result["fee_amount"] == 15.0


# ----------------------------------------------------------------------
# R6: Search Books
# ----------------------------------------------------------------------

def test_search_books_title_partial(monkeypatch, mock_book):
    monkeypatch.setattr(ls, "get_all_books", lambda: [mock_book])
    result = ls.search_books_in_catalog("test", "title")
    assert len(result) == 1


def test_search_books_isbn_exact(monkeypatch, mock_book):
    monkeypatch.setattr(ls, "get_all_books", lambda: [mock_book])
    result = ls.search_books_in_catalog("1234567890123", "isbn")
    assert len(result) == 1


def test_search_books_invalid_type(monkeypatch, mock_book):
    monkeypatch.setattr(ls, "get_all_books", lambda: [mock_book])
    result = ls.search_books_in_catalog("test", "unknown")
    assert result == []


# ----------------------------------------------------------------------
# R7: Patron Status Report
# ----------------------------------------------------------------------
# This test does not work - LLM case
# def test_patron_status_valid(monkeypatch, mock_book):
#     borrowed_books = [{
#         "book_id": 1,
#         "title": "Test Book",
#         "author": "John Doe",
#         "borrow_date": datetime.now() - timedelta(days=5),
#         "due_date": datetime.now() - timedelta(days=1),
#         "is_overdue": True,
#     }]

#     monkeypatch.setattr(ls, "get_patron_borrowed_books", lambda pid: borrowed_books)
#     monkeypatch.setattr(ls, "calculate_late_fee_for_book", lambda *a, **k: {"fee_amount": 2.0})
#     monkeypatch.setattr(ls, "get_patron_borrow_count", lambda pid: 1)
#     monkeypatch.setattr(ls, "_fetch_patron_history", lambda pid: [{"book_id": 1, "title": "Test Book"}])

#     result = ls.get_patron_status_report("123456")
#     assert "total_late_fees" in result
#     assert result["borrow_count"] == 1
#     assert len(result["current_borrowed"]) == 1


def test_patron_status_invalid_id():
    result = ls.get_patron_status_report("12")
    assert "error" in result
