"""
Library Service Module - Business Logic Functions
Contains all the core business logic for the Library Management System
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from database import (
    get_book_by_id, get_book_by_isbn, get_patron_borrow_count,
    insert_book, insert_borrow_record, update_book_availability,
    update_borrow_record_return_date, get_all_books, get_db_connection
)


def add_book_to_catalog(title: str, author: str, isbn: str, total_copies: int) -> Tuple[bool, str]:
    """
    Add a new book to the catalog.
    Implements R1: Book Catalog Management
    
    Args:
        title: Book title (max 200 chars)
        author: Book author (max 100 chars)
        isbn: 13-digit ISBN
        total_copies: Number of copies (positive integer)
        
    Returns:
        tuple: (success: bool, message: str)
    """
    # Input validation
    if not title or not title.strip():
        return False, "Title is required."
    
    if len(title.strip()) > 200:
        return False, "Title must be less than 200 characters."
    
    if not author or not author.strip():
        return False, "Author is required."
    
    if len(author.strip()) > 100:
        return False, "Author must be less than 100 characters."
    
    if len(isbn) != 13:
        return False, "ISBN must be exactly 13 digits."
    
    if not isinstance(total_copies, int) or total_copies <= 0:
        return False, "Total copies must be a positive integer."
    
    # Check for duplicate ISBN
    existing = get_book_by_isbn(isbn)
    if existing:
        return False, "A book with this ISBN already exists."
    
    # Insert new book
    success = insert_book(title.strip(), author.strip(), isbn, total_copies, total_copies)
    if success:
        return True, f'Book "{title.strip()}" has been successfully added to the catalog.'
    else:
        return False, "Database error occurred while adding the book."

def borrow_book_by_patron(patron_id: str, book_id: int) -> Tuple[bool, str]:
    """
    Allow a patron to borrow a book.
    Implements R3 as per requirements  
    
    Args:
        patron_id: 6-digit library card ID
        book_id: ID of the book to borrow
        
    Returns:
        tuple: (success: bool, message: str)
    """
    # Validate patron ID
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return False, "Invalid patron ID. Must be exactly 6 digits."
    
    # Check if book exists and is available
    book = get_book_by_id(book_id)
    if not book:
        return False, "Book not found."
    
    if book['available_copies'] <= 0:
        return False, "This book is currently not available."
    
    # Check patron's current borrowed books count
    current_borrowed = get_patron_borrow_count(patron_id)
    
    if current_borrowed >= 5:
        return False, "You have reached the maximum borrowing limit of 5 books."
    
    # Create borrow record
    borrow_date = datetime.now()
    due_date = borrow_date + timedelta(days=14)
    
    # Insert borrow record and update availability
    borrow_success = insert_borrow_record(patron_id, book_id, borrow_date, due_date)
    if not borrow_success:
        return False, "Database error occurred while creating borrow record."
    
    availability_success = update_book_availability(book_id, -1)
    if not availability_success:
        return False, "Database error occurred while updating book availability."
    
    return True, f'Successfully borrowed "{book["title"]}". Due date: {due_date.strftime("%Y-%m-%d")}.'

def _get_active_borrow_record(patron_id: str, book_id: int) -> Optional[Dict]:
    """
    Internal helper to fetch the active (unreturned) borrow record for a patron/book.
    Returns None if no such record exists.
    """
    try:
        from database import get_db_connection
    except ImportError:
        return None

    conn = get_db_connection()
    row = conn.execute(
        """
        SELECT br.*, b.title, b.author
        FROM borrow_records br
        JOIN books b ON b.id = br.book_id
        WHERE br.patron_id = ? AND br.book_id = ? AND br.return_date IS NULL
        """,
        (patron_id, book_id)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def return_book_by_patron(patron_id: str, book_id: int) -> Tuple[bool, str]:
    """
    Process book return by a patron.
    
    TODO: Implement R4 as per requirements
    """

     # Validate patron ID
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return False, "Invalid patron ID. Must be exactly 6 digits."

    book = get_book_by_id(book_id)
    if not book:
        return False, "Book not found."

    # Find active borrow record
    active = _get_active_borrow_record(patron_id, book_id)
    if not active:
        return False, "Book not borrowed by this patron."

    # Compute fee before mutating state
    fee_info = calculate_late_fee_for_book(patron_id, book_id)
    fee_amount = fee_info.get('fee_amount', 0.0)
    days_overdue = fee_info.get('days_overdue', 0)

    # Record return and update availability
    now = datetime.now()
    if not update_borrow_record_return_date(patron_id, book_id, now):
        return False, "Database error occurred while updating return record."

    # Only increment availability if it won't exceed total copies
    if book['available_copies'] < book['total_copies']:
        if not update_book_availability(book_id, +1):
            return False, "Database error occurred while updating book availability."

    title = book['title']
    if days_overdue > 0 and fee_amount > 0:
        return True, (
            f'Returned "{title}". Overdue by {days_overdue} day(s). '
            f'Late fee: ${fee_amount:.2f}.'
        )
    else:
        return True, f'Returned "{title}" on time. No late fee.'



def calculate_late_fee_for_book(patron_id: str, book_id: int) -> Dict:
    """
    Calculate late fees for a specific book.
    
    TODO: Implement R5 as per requirements 
    
    
    return { // return the calculated values
        'fee_amount': 0.00,
        'days_overdue': 0,
        'status': 'Late fee calculation not implemented'
    }
    """
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return {'fee_amount': 0.00, 'days_overdue': 0, 'status': 'Invalid patron ID'}

    # Use the same active-record helper as R4
    active = _get_active_borrow_record(patron_id, book_id)
    if not active:
        return {'fee_amount': 0.00, 'days_overdue': 0, 'status': 'No active borrow record'}

    try:
        due_date = datetime.fromisoformat(active['due_date'])
    except Exception:
        return {'fee_amount': 0.00, 'days_overdue': 0, 'status': 'Invalid due date format'}

    today = datetime.now()
    days_overdue = max(0, (today.date() - due_date.date()).days)

    if days_overdue <= 0:
        return {'fee_amount': 0.00, 'days_overdue': 0, 'status': 'Not overdue'}

    first_seven = min(days_overdue, 7) * 0.50
    remaining = max(0, days_overdue - 7) * 1.00
    fee = min(15.00, first_seven + remaining)

    # Round to cents (for display correctness)
    fee = round(fee + 1e-9, 2)

    return {'fee_amount': fee, 'days_overdue': days_overdue, 'status': 'Overdue'}

def search_books_in_catalog(search_term: str, search_type: str) -> List[Dict]:
    """
    Search for books in the catalog.
    
    TODO: Implement R6 as per requirements
    """
    if not isinstance(search_term, str) or not search_term.strip():
        return []

    stype = (search_type or '').strip().lower()
    term = search_term.strip().lower()

    books = get_all_books()
    results: List[Dict] = []

    if stype in ('title', 'author'):
        key = 'title' if stype == 'title' else 'author'
        for b in books:
            value = (b.get(key) or '').lower()
            if term in value:
                results.append(b)

    elif stype == 'isbn':
        # Exact match for 13-digit ISBN
        if term.isdigit() and len(term) == 13:
            for b in books:
                if (b.get('isbn') or '').lower() == term:
                    results.append(b)
        else:
            # If an invalid ISBN is searched, return no results per spec
            return []

    else:
        # Unknown search type: return empty per spec
        return []

    return results

def _fetch_patron_history(patron_id: str) -> List[Dict]:
    """
    Helper to fetch full borrow history for a patron.
    """
    if get_db_connection is None:
        return []

    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT br.*, b.title, b.author
        FROM borrow_records br
        JOIN books b ON b.id = br.book_id
        WHERE br.patron_id = ?
        ORDER BY datetime(br.borrow_date) ASC
        """,
        (patron_id,)
    ).fetchall()
    conn.close()

    history: List[Dict] = []
    for r in rows:
        history.append({
            'book_id': r['book_id'],
            'title': r['title'],
            'author': r['author'],
            'borrow_date': r['borrow_date'],
            'due_date': r['due_date'],
            'return_date': r['return_date'],
        })
    return history


def get_patron_status_report(patron_id: str) -> Dict:
    """
    Get status report for a patron.
    
    TODO: Implement R7 as per requirements
    """
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return {
            'error': 'Invalid patron ID. Must be exactly 6 digits.'
        }

    # Current borrows (with is_overdue flags) using DB helper from database.py
    # Note: get_patron_borrowed_books returns parsed datetimes and an 'is_overdue' boolean
    from database import get_patron_borrowed_books  # local import to avoid cycle at top
    current = get_patron_borrowed_books(patron_id)

    # Compute per-item late fees for currently borrowed books only
    total_late_fees = 0.0
    for item in current:
        if item.get('is_overdue'):
            lf = calculate_late_fee_for_book(patron_id, item['book_id'])
            total_late_fees += float(lf.get('fee_amount', 0.0))
    total_late_fees = round(total_late_fees + 1e-9, 2)

    # Count currently borrowed
    borrow_count = get_patron_borrow_count(patron_id)

    # Full history (returned + current)
    history = _fetch_patron_history(patron_id)

    # Shape a clean current list for display
    current_display = []
    for item in current:
        current_display.append({
            'book_id': item['book_id'],
            'title': item['title'],
            'author': item['author'],
            'borrow_date': item['borrow_date'].isoformat(),
            'due_date': item['due_date'].isoformat(),
            'is_overdue': bool(item['is_overdue']),
        })

    return {
        'patron_id': patron_id,
        'current_borrowed': current_display,
        'total_late_fees': total_late_fees,
        'borrow_count': borrow_count,
        'history': history,
    }
