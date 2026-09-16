"""Mock policy directory used by the live voice agent's background policy lookup.

This stands in for a carrier policy administration system. The records line up
with the demo prompts in examples.py so a live call can verify the policy the
claimant mentions while the conversation keeps going.
"""

from __future__ import annotations

import re
from typing import Any

POLICY_RECORDS: dict[str, dict[str, Any]] = {
    "H044721": {
        "policy_number": "H0-44721",
        "policyholder_name": "Maya Singh",
        "policy_line": "Homeowners (HO-3)",
        "status": "active",
        "effective_period": "2026-01-01 to 2026-12-31",
        "deductibles": {"all_perils": 1000, "wind_hail": 2500},
        "coverages": [
            "Dwelling $620,000",
            "Personal property $310,000",
            "Water backup and sump overflow endorsement $10,000",
            "Loss of use 12 months",
        ],
        "notes": ["Sump pump and water backup endorsement is on file."],
    },
    "AUTO90210": {
        "policy_number": "AUTO-90210",
        "policyholder_name": "Jordan Lee",
        "policy_line": "Personal auto",
        "status": "active",
        "effective_period": "2026-03-15 to 2026-09-15",
        "deductibles": {"collision": 500, "comprehensive": 250},
        "coverages": [
            "Bodily injury 100/300",
            "Collision",
            "Comprehensive",
            "Medical payments $5,000",
            "Rental reimbursement $40/day up to 30 days",
        ],
        "notes": ["Two listed drivers.", "Rental reimbursement is available while the vehicle is in the shop."],
    },
    "RNT3008": {
        "policy_number": "RNT-3008",
        "policyholder_name": "Priya Shah",
        "policy_line": "Renters (HO-4)",
        "status": "active",
        "effective_period": "2025-11-01 to 2026-10-31",
        "deductibles": {"all_perils": 250},
        "coverages": [
            "Personal property $25,000",
            "Theft away from premises up to 10 percent of personal property",
            "Personal liability $100,000",
        ],
        "notes": ["Theft claims require a police report number before adjuster assignment."],
    },
    "TRV7711": {
        "policy_number": "TRV-7711",
        "policyholder_name": "Alex Chen",
        "policy_line": "Single trip travel",
        "status": "active",
        "effective_period": "Trip dates 2026-01-12 to 2026-01-22",
        "deductibles": {"trip_delay": 0, "trip_cancellation": 0},
        "coverages": [
            "Trip cancellation up to $5,000",
            "Trip delay $200 per day after 6 hours, up to $1,000",
            "Baggage delay $300",
        ],
        "notes": ["Weather-related carrier cancellations are a listed covered reason."],
    },
    "MED5520": {
        "policy_number": "MED-5520",
        "policyholder_name": "Sam Rivera",
        "policy_line": "Supplemental medical reimbursement",
        "status": "active",
        "effective_period": "2026-01-01 to 2026-12-31",
        "deductibles": {"annual": 300},
        "coverages": [
            "Out-of-pocket medical reimbursement up to $7,500 per year",
            "Urgent care and emergency room copay reimbursement",
        ],
        "notes": ["Itemized provider bill and explanation of benefits are required."],
    },
    "AUTO11111": {
        "policy_number": "AUTO-11111",
        "policyholder_name": "Chris Park",
        "policy_line": "Personal auto",
        "status": "lapsed",
        "effective_period": "2025-08-01 to 2026-08-01 (not renewed)",
        "deductibles": {"collision": 1000},
        "coverages": ["Collision", "Comprehensive"],
        "notes": [
            "Policy lapsed on 2026-08-01 for non-payment.",
            "Any loss after the lapse date needs underwriting and human review before intake continues.",
        ],
    },
}


def normalize_policy_number(value: str) -> str:
    """Collapse spacing, punctuation, and letter O versus zero confusion."""

    text = re.sub(r"[^A-Za-z0-9]", "", str(value or "")).upper()
    # Voice transcripts often render zeros as the letter O inside the numeric tail.
    match = re.match(r"^([A-Z]+)([A-Z0-9]*)$", text)
    if match and match.group(2):
        prefix, tail = match.groups()
        tail = tail.replace("O", "0")
        # Keep the prefix's trailing O as a zero when the record uses one (H0-44721).
        if prefix.endswith("O") and (prefix[:-1] + "0" + tail) in POLICY_RECORDS:
            prefix = prefix[:-1] + "0"
        text = prefix + tail
    return text


def lookup_policy(policy_number: str) -> dict[str, Any]:
    """Return the policy record for a policy number, or a not-found payload."""

    key = normalize_policy_number(policy_number)
    if not key:
        return {
            "found": False,
            "policy_number": "",
            "message": "No policy number was provided. Ask the claimant to read it from their ID card or renewal notice.",
        }
    record = POLICY_RECORDS.get(key)
    if record is None:
        return {
            "found": False,
            "policy_number": str(policy_number).strip(),
            "message": (
                "No policy matched that number. Ask the claimant to confirm it digit by digit, "
                "or continue intake using their name and contact details."
            ),
        }
    return {"found": True, **record}


def policy_status_headline(record: dict[str, Any]) -> str:
    """Short human-readable status for the UI and voice summary."""

    if not record.get("found"):
        return "Not found"
    status = str(record.get("status", "unknown")).lower()
    if status == "active":
        return "Active"
    if status == "lapsed":
        return "Lapsed - human review required"
    return status.title()


__all__ = ["POLICY_RECORDS", "lookup_policy", "normalize_policy_number", "policy_status_headline"]
