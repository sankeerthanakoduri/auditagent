from retrieval.acl import filter_authorized_documents


def test_acl_blocks_unauthorized_documents():
    documents = [
        {
            "id": "finance_001",
            "text": "Financial results",
            "allowed_roles": ["finance", "admin"],
        },
        {
            "id": "hr_001",
            "text": "Employee salary information",
            "allowed_roles": ["hr", "admin"],
        },
    ]

    authorized, blocked = filter_authorized_documents(
        user_role="finance",
        documents=documents,
    )

    assert len(authorized) == 1
    assert authorized[0]["id"] == "finance_001"

    assert len(blocked) == 1
    assert blocked[0]["id"] == "hr_001"