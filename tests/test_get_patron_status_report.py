import pytest
import library_service as ls

def test_r7_status_has_required_keys():
    """Ensure report returns all expected fields for a valid patron."""
    report = ls.get_patron_status_report("123456")
    assert "patron_id" in report
    assert "current_borrowed" in report
    assert "total_late_fees" in report
    assert "borrow_count" in report
    assert "history" in report

def test_r7_status_books_list_contains_due_dates():
    """Each borrowed book in current list should include a due date."""
    report = ls.get_patron_status_report("123456")
    for book in report.get("current_borrowed", []):
        assert "due_date" in book
        assert "title" in book
        assert "is_overdue" in book

def test_r7_status_total_fees_nonnegative():
    """Total late fees must never be negative."""
    report = ls.get_patron_status_report("123456")
    assert report["total_late_fees"] >= 0

def test_r7_status_invalid_patron_returns_error():
    """Invalid patron ID should return an error key instead of data."""
    report = ls.get_patron_status_report("xx9999")
    assert "error" in report
    assert "invalid" in report["error"].lower()
