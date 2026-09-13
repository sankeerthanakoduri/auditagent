import sqlite3
from pathlib import Path


DB_PATH = Path("data/company.db")


class SQLTool:
    """
    Read-only SQLite tool for AuditAgent.
    """

    ALLOWED_TABLES = {
        "employees",
        "departments",
    }

    def __init__(self, db_path: str | Path = DB_PATH):
        self.db_path = Path(db_path)

    def get_schema(self) -> str:
        """
        Return the database schema.
        """

        connection = sqlite3.connect(self.db_path)

        cursor = connection.cursor()

        schema_parts = []

        for table in self.ALLOWED_TABLES:
            cursor.execute(
                f"PRAGMA table_info({table})"
            )

            columns = cursor.fetchall()

            column_text = ", ".join(
                f"{column[1]} {column[2]}"
                for column in columns
            )

            schema_parts.append(
                f"{table}({column_text})"
            )

        connection.close()

        return "\n".join(schema_parts)

    def execute(self, query: str) -> list[tuple]:
        """
        Execute a read-only SQL query.

        Only SELECT statements are allowed.
        """

        cleaned_query = query.strip()

        if not cleaned_query:
            raise ValueError(
                "SQL query cannot be empty."
            )

        if not cleaned_query.lower().startswith("select"):
            raise ValueError(
                "Only SELECT queries are allowed."
            )

        connection = sqlite3.connect(self.db_path)

        cursor = connection.cursor()

        try:
            cursor.execute(cleaned_query)

            rows = cursor.fetchall()

            return rows

        finally:
            connection.close()