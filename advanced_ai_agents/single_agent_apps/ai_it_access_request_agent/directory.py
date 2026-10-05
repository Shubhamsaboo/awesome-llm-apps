"""Fictional company directory, app catalog and approval records.

Everything here is made up and kept in memory, so the agent can be run and
tested without touching a real identity provider.
"""

EMPLOYEES = {
    "E101": {"name": "Harish", "title": "Backend Engineer", "department": "Engineering", "manager": "E201"},
    "E102": {"name": "Marco Silva", "title": "Account Executive", "department": "Sales", "manager": "E202"},
    "E103": {"name": "Aisha Khan", "title": "Financial Analyst", "department": "Finance", "manager": "E203"},
    "E201": {"name": "Dana Lee", "title": "Engineering Manager", "department": "Engineering", "manager": None},
    "E202": {"name": "Tom Becker", "title": "Sales Director", "department": "Sales", "manager": None},
    "E203": {"name": "Lena Ortiz", "title": "Finance Director", "department": "Finance", "manager": None},
}

# sensitivity "high" means every role needs a recorded manager approval.
# The "admin" role always needs one, whatever the sensitivity.
APPS = {
    "github": {"sensitivity": "low", "departments": ["Engineering"], "roles": ["read", "write"]},
    "jira": {"sensitivity": "low", "departments": ["Engineering", "Sales", "Finance"], "roles": ["user"]},
    "salesforce": {"sensitivity": "medium", "departments": ["Sales", "Finance"], "roles": ["user", "admin"]},
    "aws-console": {"sensitivity": "high", "departments": ["Engineering"], "roles": ["readonly", "admin"]},
    "prod-database": {"sensitivity": "high", "departments": ["Engineering"], "roles": ["read", "admin"]},
    "netsuite": {"sensitivity": "high", "departments": ["Finance"], "roles": ["user", "admin"]},
}

# Approval tickets a manager has actually recorded.
APPROVALS = {
    "APR-1042": {"employee": "E101", "app": "prod-database", "role": "read", "approver": "E201"},
    "APR-1077": {"employee": "E103", "app": "netsuite", "role": "user", "approver": "E203"},
}

# Access each employee already holds: employee -> {app: role}.
INITIAL_GRANTS = {
    "E101": {"github": "write", "jira": "user"},
    "E102": {"salesforce": "user", "jira": "user"},
    "E103": {"jira": "user"},
}
