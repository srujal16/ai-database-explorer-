"""
db_setup.py
Creates a sample SQLite database (company.db) with three tables:
departments, employees, products — pre-filled with sample data.

Run this file directly to (re)build the database:
    python db_setup.py
"""

import sqlite3
import os

DB_NAME = "company.db"


def build_database(db_path: str = DB_NAME, overwrite: bool = False) -> None:
    """Create the sample database and populate it with demo data."""
    if overwrite and os.path.exists(db_path):
        os.remove(db_path)

    is_new = not os.path.exists(db_path)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            location TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            salary REAL NOT NULL,
            hire_date TEXT NOT NULL,
            email TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL
        )
    """)

    # Only seed data the first time the database is created
    cur.execute("SELECT COUNT(*) FROM departments")
    if cur.fetchone()[0] == 0:
        departments = [
            ("Sales", "New York"),
            ("Engineering", "San Francisco"),
            ("Marketing", "Chicago"),
            ("Human Resources", "Austin"),
            ("Finance", "Boston"),
        ]
        cur.executemany("INSERT INTO departments (name, location) VALUES (?, ?)", departments)

        employees = [
            ("Alice Johnson", "Sales", 62000, "2021-03-14", "alice.johnson@company.com"),
            ("Brian Lee", "Engineering", 95000, "2019-07-01", "brian.lee@company.com"),
            ("Carla Gomez", "Marketing", 58000, "2022-01-20", "carla.gomez@company.com"),
            ("David Kim", "Engineering", 102000, "2018-11-05", "david.kim@company.com"),
            ("Emma Wilson", "Human Resources", 54000, "2020-06-15", "emma.wilson@company.com"),
            ("Frank Turner", "Sales", 67000, "2021-09-23", "frank.turner@company.com"),
            ("Grace Chen", "Finance", 71000, "2017-02-11", "grace.chen@company.com"),
            ("Henry Adams", "Engineering", 88000, "2023-04-02", "henry.adams@company.com"),
            ("Isla Moore", "Marketing", 60000, "2022-08-30", "isla.moore@company.com"),
            ("Jack Nguyen", "Finance", 76000, "2019-12-19", "jack.nguyen@company.com"),
        ]
        cur.executemany(
            "INSERT INTO employees (name, department, salary, hire_date, email) VALUES (?, ?, ?, ?, ?)",
            employees,
        )

        products = [
            ("Wireless Mouse", "Electronics", 19.99, 150),
            ("Mechanical Keyboard", "Electronics", 49.99, 80),
            ("Office Chair", "Furniture", 129.50, 40),
            ("Standing Desk", "Furniture", 249.00, 25),
            ("Notebook Set", "Stationery", 6.99, 300),
            ("Desk Lamp", "Electronics", 24.99, 60),
            ("Water Bottle", "Accessories", 12.49, 200),
            ("Monitor 24-inch", "Electronics", 159.99, 35),
            ("Backpack", "Accessories", 39.99, 90),
            ("Whiteboard", "Furniture", 34.99, 15),
        ]
        cur.executemany(
            "INSERT INTO products (name, category, price, stock) VALUES (?, ?, ?, ?)",
            products,
        )

    conn.commit()
    conn.close()

    if is_new:
        print(f"Database '{db_path}' created and seeded with sample data.")
    else:
        print(f"Database '{db_path}' already exists — using existing data.")


if __name__ == "__main__":
    build_database(overwrite=False)
