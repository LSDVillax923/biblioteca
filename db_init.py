# db_init.py
import sqlite3
import random
from datetime import datetime, timedelta

DB = "library.db"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    # tables
    c.execute('''CREATE TABLE IF NOT EXISTS books (
        code TEXT PRIMARY KEY,
        title TEXT,
        total_copies INTEGER,
        available_copies INTEGER
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS loans (
        loan_id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_code TEXT,
        user_id TEXT,
        due_date TEXT,
        renewals INTEGER DEFAULT 0,
        FOREIGN KEY(book_code) REFERENCES books(code)
    )''')

    # populate books
    c.execute("DELETE FROM loans")
    c.execute("DELETE FROM books")
    total_books = 1000
    for i in range(1, total_books+1):
        code = f"B{i:04d}"
        title = f"Libro {i}"
        total = random.choice([1,1,1,2,3,4])  # some unique, some multiple copies
        available = total
        c.execute("INSERT INTO books(code,title,total_copies,available_copies) VALUES (?,?,?,?)",
                  (code, title, total, available))

    # Create 200 initial loans (mark as lent -> reduce available)
    users = [f"user{i%50}" for i in range(200)]
    lent_books = random.sample(range(1,total_books+1), 200)
    for idx, book_idx in enumerate(lent_books):
        code = f"B{book_idx:04d}"
        user = users[idx]
        due = datetime.now() + timedelta(days=7)  # due in 1 week
        due_str = due.isoformat()
        # decrement available if possible
        c.execute("SELECT available_copies FROM books WHERE code = ?", (code,))
        row = c.fetchone()
        if row and row[0] > 0:
            c.execute("INSERT INTO loans(book_code,user_id,due_date,renewals) VALUES (?,?,?,?)",
                      (code, user, due_str, 0))
            c.execute("UPDATE books SET available_copies = available_copies - 1 WHERE code = ?", (code,))
    conn.commit()
    conn.close()
    print("DB inicializada:", DB)

if __name__ == "__main__":
    init_db()
