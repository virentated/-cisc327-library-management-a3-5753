import pytest
import library_service as ls
import database as db

def test_r5_no_overdue_fee_is_zero():
    # Assuming the data given is of a parton without book being overdue, it results in no fees.
    result = ls.calculate_late_fee_for_book("123456", 1)
    assert result["fee_amount"] == 0.0
    assert result["days_overdue"] == 0

import datetime
import library_service as ls

def test_r5_overdue_five_days_half_dollar_each(monkeypatch):
    """5 days overdue → 5 * $0.50 = $2.50"""
    # Mock an active borrow record that’s 5 days overdue
    fake_record = {
        "due_date": (datetime.datetime.now() - datetime.timedelta(days=5)).isoformat()
    }
    monkeypatch.setattr(ls, "_get_active_borrow_record", lambda p, b: fake_record)

    result = ls.calculate_late_fee_for_book("123456", 2)
    assert round(result["fee_amount"], 2) == 2.50
    assert result["days_overdue"] == 5
    assert result["status"].lower() == "overdue"


def test_r5_overdue_ten_days_mixed_rate(monkeypatch):
    """10 days overdue → 7 * $0.50 + 3 * $1.00 = $6.50"""
    fake_record = {
        "due_date": (datetime.datetime.now() - datetime.timedelta(days=10)).isoformat()
    }
    monkeypatch.setattr(ls, "_get_active_borrow_record", lambda p, b: fake_record)

    result = ls.calculate_late_fee_for_book("123456", 3)
    assert round(result["fee_amount"], 2) == 6.50
    assert result["days_overdue"] == 10
    assert result["status"].lower() == "overdue"


def test_r5_fee_capped_at_15(monkeypatch):
    """Ensure maximum fee cap at $15.00"""
    fake_record = {
        "due_date": (datetime.datetime.now() - datetime.timedelta(days=40)).isoformat()
    }
    monkeypatch.setattr(ls, "_get_active_borrow_record", lambda p, b: fake_record)

    result = ls.calculate_late_fee_for_book("123456", 4)
    assert result["fee_amount"] == 15.00
    assert result["days_overdue"] >= 21  # 14 + at least 7 over cap
