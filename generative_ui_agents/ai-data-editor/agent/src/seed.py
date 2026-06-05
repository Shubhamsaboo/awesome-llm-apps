import random
from pathlib import Path
from .db import DB_PATH, init_db, get_write_connection

ACCOUNT_NAMES = [
    "Acme Corp", "Bright Query", "Brilliant Metrics", "HighFive",
    "Mathison.io", "SeekOut", "DataForge", "CloudNine Systems",
    "Prism Analytics", "NovaTech", "Apex Digital", "Meridian Labs",
    "Quantum Insights", "Stellar Data", "Zenith AI", "PulsePoint",
    "Cortex Solutions", "Beacon Analytics", "Horizon SaaS", "Atlas Computing",
    "Nimbus Data", "Vertex Systems", "Catalyst AI", "Forge Analytics",
    "Summit Cloud", "Pinnacle Tech", "Spectrum Data", "Nexus Labs",
    "Vanguard AI", "Ironclad Systems", "Aurora Analytics", "Cipher Data",
    "Dynamo Tech", "Eclipse AI", "Frontier Data", "Granite Systems",
    "Harbor Analytics", "Ionic Tech", "Jupiter Data", "Keystone AI",
    "Lighthouse Systems", "Mosaic Data", "Nordic AI", "Orbit Analytics",
    "Pioneer Tech", "Quasar Data", "Ridge Systems", "Signal AI",
    "Trident Data", "Unity Analytics",
]

OWNERS = [
    "Maria Santos", "James Reeves", "Priya Patel", "Derek Olson",
    "Alex Chen", "Jordan Park", "Morgan Blake", "Sarah Lin",
]

CSMS = [
    "Rachel Kim", "Tom Nguyen", "Lisa Huang", "Ben Torres",
    "Sophie Martin", "Kai Yamamoto",
]

TYPES = ["Enterprise", "Free", "Startup", "Scale"]
STATUSES = ["Active", "Active", "Active", "Churned", "Trial", "Suspended"]

METRICS = ["api_calls", "storage_gb", "seats", "bandwidth_gb"]
PERIODS = ["2026-01", "2026-02", "2026-03", "2026-04", "2026-05"]

INVOICE_STATUSES = ["Paid", "Paid", "Paid", "Overdue", "Draft", "Void"]


def seed_if_needed():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    init_db()

    conn = get_write_connection()
    count = conn.execute("SELECT COUNT(*) as cnt FROM accounts").fetchone()["cnt"]
    if count > 0:
        conn.close()
        return

    random.seed(42)

    for i, name in enumerate(ACCOUNT_NAMES, start=1):
        acct_type = random.choice(TYPES)
        mrr = {
            "Enterprise": random.uniform(3000, 15000),
            "Scale": random.uniform(1000, 5000),
            "Startup": random.uniform(200, 1000),
            "Free": 0,
        }[acct_type]

        conn.execute(
            "INSERT INTO accounts (id, name, type, owner, csm, status, mrr, created_at, salesforce_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                i, name, acct_type,
                random.choice(OWNERS),
                random.choice(CSMS) if acct_type != "Free" else None,
                random.choice(STATUSES),
                round(mrr, 2),
                f"2025-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
                f"SF{random.randint(100000, 999999)}" if acct_type != "Free" else None,
            ),
        )

    usage_id = 1
    for account_id in range(1, 51):
        for metric in random.sample(METRICS, k=random.randint(2, 4)):
            base_value = {
                "api_calls": random.uniform(10000, 2000000),
                "storage_gb": random.uniform(10, 1000),
                "seats": random.uniform(5, 200),
                "bandwidth_gb": random.uniform(50, 5000),
            }[metric]

            for period in PERIODS:
                drift = random.uniform(0.8, 1.3)
                conn.execute(
                    "INSERT INTO usage (id, account_id, metric, period, value, recorded_at) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (usage_id, account_id, metric, period, round(base_value * drift, 2), f"{period}-28"),
                )
                usage_id += 1

    invoice_id = 1
    for account_id in range(1, 51):
        acct = conn.execute("SELECT mrr, type FROM accounts WHERE id = ?", (account_id,)).fetchone()
        if acct["type"] == "Free":
            continue

        for month in range(1, 6):
            amount = round(acct["mrr"] * random.uniform(0.95, 1.1), 2)
            status = random.choice(INVOICE_STATUSES)
            due_date = f"2026-{month:02d}-15"
            paid_at = f"2026-{month:02d}-{random.randint(10, 20):02d}" if status == "Paid" else None

            conn.execute(
                "INSERT INTO invoices (id, account_id, amount, status, due_date, paid_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (invoice_id, account_id, amount, status, due_date, paid_at),
            )
            invoice_id += 1

    conn.commit()
    conn.close()
    print(f"Seeded database: 50 accounts, {usage_id - 1} usage rows, {invoice_id - 1} invoices")


if __name__ == "__main__":
    seed_if_needed()
