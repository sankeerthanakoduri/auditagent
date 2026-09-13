import pytest

from agent.sql_tool import SQLTool


@pytest.fixture
def sql_tool():
    return SQLTool()


def test_select_query_is_allowed(sql_tool):
    result = sql_tool.execute(
        """
        SELECT COUNT(*)
        FROM employees
        WHERE department = 'Finance';
        """
    )

    assert result == [(2,)]


def test_department_budget_query_is_allowed(sql_tool):
    result = sql_tool.execute(
        """
        SELECT budget_crore
        FROM departments
        WHERE department = 'HR';
        """
    )

    assert result == [(12.5,)]


def test_insert_is_rejected(sql_tool):
    with pytest.raises(ValueError):
        sql_tool.execute(
            """
            INSERT INTO employees
            VALUES (99, 'Attacker', 'Finance', 'Hacker', 0);
            """
        )


def test_update_is_rejected(sql_tool):
    with pytest.raises(ValueError):
        sql_tool.execute(
            """
            UPDATE employees
            SET annual_leave = 999;
            """
        )


def test_delete_is_rejected(sql_tool):
    with pytest.raises(ValueError):
        sql_tool.execute(
            """
            DELETE FROM employees;
            """
        )


def test_drop_is_rejected(sql_tool):
    with pytest.raises(ValueError):
        sql_tool.execute(
            """
            DROP TABLE employees;
            """
        )


def test_alter_is_rejected(sql_tool):
    with pytest.raises(ValueError):
        sql_tool.execute(
            """
            ALTER TABLE employees
            ADD COLUMN malicious TEXT;
            """
        )


def test_empty_query_is_rejected(sql_tool):
    with pytest.raises(ValueError):
        sql_tool.execute("")    