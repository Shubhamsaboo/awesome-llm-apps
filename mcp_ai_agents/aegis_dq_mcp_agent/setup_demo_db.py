"""Creates a sample DuckDB database with intentional data quality issues for the demo."""

import os
import duckdb


def setup_demo_db(db_path: str = "/tmp/aegis_demo.duckdb") -> str:
    # Always start fresh to avoid schema conflicts from prior runs
    if os.path.exists(db_path):
        os.remove(db_path)
    con = duckdb.connect(db_path)
    con.execute("DROP TABLE IF EXISTS orders")
    con.execute("""
        CREATE TABLE orders (
            order_id    VARCHAR,
            customer_id VARCHAR,
            amount      DOUBLE,
            status      VARCHAR
        )
    """)
    con.execute("""
        INSERT INTO orders VALUES
        ('ORD-001', 'CUST-1', 250.00,  'delivered'),
        ('ORD-002', 'CUST-2', 89.99,   'shipped'),
        ('ORD-003', NULL,     150.00,  'pending'),
        ('ORD-004', 'CUST-4', -50.00,  'confirmed'),
        ('ORD-005', 'CUST-5', 999.50,  'refunded'),
        ('ORD-006', 'CUST-6', 320.00,  'delivered'),
        ('ORD-001', 'CUST-7', 75.00,   'pending'),
        ('ORD-008', 'CUST-8', NULL,    'shipped'),
        ('ORD-009', 'CUST-9', 410.00,  'cancelled'),
        ('ORD-010', 'CUST-10', 88.00,  'delivered')
    """)
    con.close()
    return db_path


if __name__ == "__main__":
    path = setup_demo_db()
    print(f"Demo database created at {path}")
