import json
import random
from .db import DB_PATH, init_db, get_write_connection

PLANS = [
    {
        "id": "free",
        "name": "Free",
        "price_monthly": 0,
        "event_limit": 50000,
        "storage_limit_gb": 1,
        "seat_limit": 1,
        "features": json.dumps(["ai_completions", "document_processing"]),
    },
    {
        "id": "pro",
        "name": "Pro",
        "price_monthly": 99,
        "event_limit": 500000,
        "storage_limit_gb": 50,
        "seat_limit": 10,
        "features": json.dumps(["ai_completions", "document_processing", "custom_models", "priority_support", "analytics"]),
    },
    {
        "id": "team",
        "name": "Team",
        "price_monthly": 299,
        "event_limit": 2000000,
        "storage_limit_gb": 500,
        "seat_limit": 50,
        "features": json.dumps(["ai_completions", "document_processing", "custom_models", "priority_support", "analytics", "sso", "audit_log", "custom_retention"]),
    },
]

MODELS = ["gpt-4o", "gpt-4o-mini", "claude-sonnet-4", "claude-haiku", "gemini-2.5-flash"]
MODEL_COSTS = {
    "gpt-4o": (0.0025, 0.01),
    "gpt-4o-mini": (0.00015, 0.0006),
    "claude-sonnet-4": (0.003, 0.015),
    "claude-haiku": (0.0008, 0.004),
    "gemini-2.5-flash": (0.00015, 0.0006),
}

FEATURES = ["ai_completions", "document_processing", "custom_models"]


def seed_if_needed():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    init_db()

    conn = get_write_connection()
    count = conn.execute("SELECT COUNT(*) as cnt FROM account").fetchone()["cnt"]
    if count > 0:
        conn.close()
        return

    random.seed(42)

    for plan in PLANS:
        conn.execute(
            "INSERT INTO plans (id, name, price_monthly, event_limit, storage_limit_gb, seat_limit, features) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (plan["id"], plan["name"], plan["price_monthly"], plan["event_limit"],
             plan["storage_limit_gb"], plan["seat_limit"], plan["features"]),
        )

    conn.execute(
        "INSERT INTO account (id, company_name, plan_id, email, api_key, created_at, billing_cycle_start, stripe_customer_id) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (1, "Acme AI", "pro", "admin@acme-ai.com", "sk_live_acme_xxxx",
         "2025-09-15", "2026-06-01", "cus_AcmeAI12345"),
    )

    event_id = 1
    for month in range(1, 7):
        days_in_month = 28 if month == 2 else 30
        base_daily_events = random.randint(400, 800)

        if month >= 4:
            base_daily_events = int(base_daily_events * 1.4)

        for day in range(1, days_in_month + 1):
            daily_events = random.randint(
                int(base_daily_events * 0.6),
                int(base_daily_events * 1.5),
            )

            for _ in range(daily_events):
                model = random.choices(
                    MODELS,
                    weights=[30, 35, 15, 15, 5],
                    k=1,
                )[0]

                tokens_in = random.randint(50, 4000)
                tokens_out = random.randint(20, 2000)
                cost_in, cost_out = MODEL_COSTS[model]
                cost = round((tokens_in / 1000) * cost_in + (tokens_out / 1000) * cost_out, 6)

                feature = random.choices(
                    FEATURES,
                    weights=[60, 30, 10],
                    k=1,
                )[0]

                hour = random.randint(8, 22)
                minute = random.randint(0, 59)

                conn.execute(
                    "INSERT INTO usage_events (id, account_id, feature, model, tokens_in, tokens_out, cost, timestamp) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (event_id, 1, feature, model,
                     tokens_in, tokens_out, cost,
                     f"2026-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:00Z"),
                )
                event_id += 1

                if event_id % 10000 == 0:
                    conn.commit()

    for feature in FEATURES:
        plan_limit = {"ai_completions": 500000, "document_processing": 100000, "custom_models": 50000}
        usage_count = conn.execute(
            "SELECT COUNT(*) as cnt FROM usage_events WHERE account_id = 1 AND feature = ?",
            (feature,),
        ).fetchone()["cnt"]

        conn.execute(
            "INSERT INTO entitlements (account_id, feature, limit_value, current_usage, period) "
            "VALUES (?, ?, ?, ?, ?)",
            (1, feature, plan_limit.get(feature, 500000), usage_count, "2026-06"),
        )

    invoice_id = 1
    for month in range(1, 7):
        month_cost = conn.execute(
            "SELECT COALESCE(SUM(cost), 0) as total FROM usage_events "
            "WHERE account_id = 1 AND timestamp LIKE ?",
            (f"2026-{month:02d}%",),
        ).fetchone()["total"]

        base_amount = 99.0
        overage = max(0, month_cost - 50.0)
        total = round(base_amount + overage, 2)

        status = "Paid" if month <= 4 else ("Pending" if month == 5 else "Draft")
        paid_at = f"2026-{month:02d}-18" if status == "Paid" else None

        line_items = json.dumps([
            {"description": "Pro plan - base", "amount": 99.0},
            {"description": f"Usage overage ({month_cost:.2f} cost)", "amount": round(overage, 2)},
        ])

        conn.execute(
            "INSERT INTO invoices (id, account_id, amount, status, period, due_date, paid_at, line_items) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (invoice_id, 1, total, status,
             f"2026-{month:02d}", f"2026-{month:02d}-15", paid_at, line_items),
        )
        invoice_id += 1

    conn.execute(
        "INSERT INTO alerts (account_id, feature, threshold_pct, triggered) VALUES (?, ?, ?, ?)",
        (1, "ai_completions", 80, 1),
    )
    conn.execute(
        "INSERT INTO alerts (account_id, feature, threshold_pct, triggered) VALUES (?, ?, ?, ?)",
        (1, "ai_completions", 90, 0),
    )

    conn.commit()
    conn.close()
    print(f"Seeded database: 1 account, {event_id - 1} usage events, {invoice_id - 1} invoices, 3 entitlements, 2 alerts")


if __name__ == "__main__":
    seed_if_needed()
