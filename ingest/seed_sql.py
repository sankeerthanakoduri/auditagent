import sqlite3
from pathlib import Path


DB_PATH = Path("data/company.db")


def create_database():
    """
    Create the synthetic AuditAgent SQLite database.
    """

    DB_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(DB_PATH)

    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS employees (
            employee_id INTEGER PRIMARY KEY,
            employee_name TEXT NOT NULL,
            department TEXT NOT NULL,
            role TEXT NOT NULL,
            annual_leave INTEGER NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS departments (
            department TEXT PRIMARY KEY,
            headcount INTEGER NOT NULL,
            budget_crore REAL NOT NULL
        )
        """
    )

    cursor.execute(
        """
        DELETE FROM employees
        """
    )

    cursor.execute(
        """
        DELETE FROM departments
        """
    )

    employees = [
        (1, "Employee A", "Finance", "Analyst", 24),
        (2, "Employee B", "Finance", "Manager", 24),
        (3, "Employee C", "HR", "HR Executive", 24),
        (4, "Employee D", "HR", "HR Manager", 24),
        (5, "Employee E", "Operations", "Executive", 24),
    ]

    departments = [
        ("Finance", 120, 31.2),
        ("HR", 45, 12.5),
        ("Operations", 210, 48.7),
    ]

    cursor.executemany(
        """
        INSERT INTO employees
        (
            employee_id,
            employee_name,
            department,
            role,
            annual_leave
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        employees,
    )

    cursor.executemany(
        """
        INSERT INTO departments
        (
            department,
            headcount,
            budget_crore
        )
        VALUES (?, ?, ?)
        """,
        departments,
    )

    connection.commit()
    connection.close()

    print(f"SQLite database created: {DB_PATH}")


if __name__ == "__main__":
    create_database()