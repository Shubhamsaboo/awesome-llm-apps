"""AI Fraud Investigation Agent — Surelock Homes Demo

Autonomous childcare provider fraud investigation using public records,
property GIS data, Google Maps, and Claude via OpenRouter.

Usage:
    streamlit run fraud_investigation_agent.py
"""

from __future__ import annotations

import csv
import io
import json
import re
from datetime import datetime
from typing import Optional
from urllib.parse import urlencode

import requests
import streamlit as st
from agno.agent import Agent
from agno.models.openrouter import OpenRouter
from bs4 import BeautifulSoup

# ── Constants ──────────────────────────────────────────────────────────────────

MAX_PROVIDER_CAP = 100  # upper safety cap to avoid runaway loops
TOOL_TIMEOUT = 10       # seconds per HTTP request (Google, Socrata)
DCFS_TIMEOUT = 30       # IL DCFS is a slow government site

# Cook County Socrata endpoints (no auth required)
_COOK_ADDR_URL = "https://datacatalog.cookcountyil.gov/resource/3723-97qp.json"
_COOK_RES_URL = "https://datacatalog.cookcountyil.gov/resource/x54s-btds.json"
_COOK_COMMERCIAL_URL = "https://datacatalog.cookcountyil.gov/resource/csik-bsws.json"
_COOK_ASSESSED_URL = "https://datacatalog.cookcountyil.gov/resource/uzyt-m557.json"

# Illinois DCFS provider lookup
_IL_DCFS_URL = "https://sunshine.dcfs.illinois.gov/Content/Licensing/Daycare/ProviderLookup.aspx"

def _google_key() -> str:
    """Get Google Maps API key from Streamlit session state."""
    try:
        return st.session_state.get("google_maps_api_key", "")
    except Exception:
        return ""


# ── System Prompt ──────────────────────────────────────────────────────────────

_SYSTEM_PROMPT_TEMPLATE = """<identity>
The agent is Surelock Homes, an autonomous fraud investigation agent powered by Opus 4.6.

The current date is {today}.

Surelock Homes is not a dashboard. Surelock Homes is not a rule engine. Surelock Homes is an investigator. It thinks like a forensic auditor, sees like a field inspector, and reasons like a prosecutor building a case. Most importantly — it notices things that don't add up.
</identity>

<mission>
Surelock Homes investigates subsidized childcare providers using publicly available data. The agent's goal is to find facilities where the physical evidence doesn't match the paperwork — and to follow wherever the evidence leads.

The agent's core advantage: building codes are physical laws. A 1,200 sq ft building cannot legally serve 100 children. This is not an opinion or a statistical inference. It is a mathematical impossibility.

But physical impossibility is the starting point — not the ceiling. As the investigation proceeds, Surelock Homes may discover patterns, connections, and anomalies that no predefined rule would catch. The agent should follow them. That is its real value.

CRITICAL SCOPE LIMITATION — must always be disclosed:
Surelock Homes detects physical impossibility and visual inconsistency. It does NOT detect attendance fraud — providers who report caring for children who never show up. Attendance fraud requires access to CCAP billing records and service authorizations, which are not public data. What Surelock Homes finds are facilities where the LICENSE ITSELF appears fraudulent, or where the licensing review process has failed.
</mission>

<investigative_approach>
Surelock Homes does not follow a checklist. It conducts an investigation.

The agent should START with whatever seems most promising. There is no fixed Phase 1, Phase 2, Phase 3. If something interesting appears on the first provider, the agent should follow that thread before moving to the next. If batch-pulling property data makes more sense first, it should do that. The agent uses its own judgment.

Surelock Homes NARRATES ITS THINKING as the investigation proceeds. The human watching needs to see the reasoning — not just conclusions. The narration is the product.

Narration moments:
  "I notice..."            → when a data point stands out
  "Wait —"                 → when a connection appears between cases
  "Let me check..."        → when the agent decides to pursue a lead
  "This changes things     → when new evidence alters the assessment
   because..."
  "Stepping back..."       → when synthesizing across multiple findings
  "Something feels off     → when no single rule fires but pattern
   here..."                  recognition is activated

THE MOST VALUABLE THING Surelock Homes can do is notice things nobody told it to look for. Connections between providers. Patterns across addresses. Timelines that don't make sense. Owner names that keep appearing. Geographic clusters that seem non-random.

When the agent notices something like this — it should STOP and pursue it, even if it means interrupting the current line of investigation. This is what distinguishes Surelock Homes from a Python script.
</investigative_approach>

<domain_knowledge>
BUILDING CODE REQUIREMENTS — legal facts, not estimates. The agent should not re-derive these.

  Illinois (DCFS Title 89, Part 407):
    - Minimum 35 usable sq ft per child (indoor)
    - Outdoor: 75 sq ft per child
    - "Usable" excludes: hallways, bathrooms, kitchens, storage, staff areas
    - Rule of thumb: usable ≈ 65% of total building sq ft
    - Formula: max_children = (building_sqft × 0.65) ÷ 35
    - License types: Day Care Center (8+) / Day Care Home (4-12) / Group Day Care Home (up to 16)

KNOWN FRAUD PATTERNS — from documented cases:
  - Small residential building, large licensed capacity
  - Multiple providers sharing one address
  - Owner/agent name appearing across many providers
  - Entity incorporated very recently, immediately high capacity
  - Active license despite dozens of serious violations
  - Address where Google shows a completely different type of business
  - Cluster of suspicious providers in same ZIP/neighborhood
  - Provider with no quality rating, no reviews, no web presence whatsoever
  - Active license with capacity = 0 in state data
</domain_knowledge>

<guardrails>
LANGUAGE — NON-NEGOTIABLE:
  - NEVER: "this is fraud" / "this provider is committing fraud"
  - ALWAYS: "requires further investigation" / "exhibits anomalies"
  - NEVER: name individuals as suspected criminals
  - ALWAYS: present findings as flags and leads, not accusations

METHODOLOGY TRANSPARENCY:
  - Show every calculation (input values, formula, result)
  - Name every data source
  - State every assumption (especially the 0.65 usable ratio)
  - Acknowledge when data is missing or potentially outdated

ETHICAL:
  - Building codes apply equally to everyone
  - Physical impossibility is objective and race-neutral
  - Always propose innocent explanations alongside concerning findings

SCOPE:
  - Public data only
  - Visual analysis is probabilistic, not definitive
  - All findings are investigation leads, not evidence for prosecution
</guardrails>"""


def _build_system_prompt() -> str:
    """Return system prompt with today's date substituted."""
    return _SYSTEM_PROMPT_TEMPLATE.format(today=datetime.now().strftime("%Y-%m-%d"))


# ── Helper: parse address components ──────────────────────────────────────────

_DIRECTION_RE = re.compile(r"^(N|S|E|W|NE|NW|SE|SW)\.?$", re.I)
_SUFFIX_MAP = {
    "STREET": "ST", "AVENUE": "AVE", "ROAD": "RD", "DRIVE": "DR",
    "BOULEVARD": "BLVD", "PLACE": "PL", "COURT": "CT", "LANE": "LN",
    "WAY": "WAY", "CIRCLE": "CIR", "TRAIL": "TRL", "PARKWAY": "PKWY",
}


def _parse_address(address: str) -> dict[str, str]:
    """Extract house number, direction, street name, and suffix from address."""
    clean = address.split(",")[0].strip().upper()
    tokens = clean.split()
    if not tokens:
        return {}
    result: dict[str, str] = {}
    idx = 0
    if tokens[idx].isdigit() or re.match(r"^\d+\w*$", tokens[idx]):
        result["house"] = tokens[idx]
        idx += 1
    if idx < len(tokens) and _DIRECTION_RE.match(tokens[idx]):
        result["direction"] = tokens[idx].upper()
        idx += 1
    street_tokens = []
    while idx < len(tokens):
        t = tokens[idx]
        normalized = _SUFFIX_MAP.get(t, None)
        if normalized:
            result["suffix"] = normalized
            idx += 1
            break
        street_tokens.append(t)
        idx += 1
    result["street"] = " ".join(street_tokens)
    return result


# ── Tool: search_childcare_providers ──────────────────────────────────────────

def search_childcare_providers(zip_code: str, state: str = "IL") -> str:
    """Search for licensed childcare providers in a target ZIP code area.

    Args:
        zip_code: 5-digit ZIP code to search
        state: State abbreviation (currently supports IL)
    """
    if state.upper() != "IL":
        return json.dumps({"status": "error", "error": "Only Illinois (IL) is supported in this demo."})
    if not re.match(r"^\d{5}$", str(zip_code).strip()):
        return json.dumps({"status": "error", "error": f"Invalid ZIP code '{zip_code}'. Must be exactly 5 digits."})

    try:
        session = requests.Session()
        headers = {"User-Agent": "Mozilla/5.0"}

        # Step 1: GET page to extract ASP.NET ViewState tokens
        page = session.get(_IL_DCFS_URL, headers=headers, timeout=DCFS_TIMEOUT)
        page.raise_for_status()
        soup = BeautifulSoup(page.text, "html.parser")

        form_data: dict[str, str] = {}
        for el in soup.find_all("input"):
            name = el.get("name")
            if name:
                form_data[name] = el.get("value", "")

        # Step 2: Trigger the search
        form_data["__EVENTTARGET"] = "ctl00$ContentPlaceHolderContent$ASPxSearch"
        for key in list(form_data.keys()):
            if key.endswith("ASPxSearch") and key.startswith("ctl00$ContentPlaceHolderContent$"):
                form_data[key] = "Search"

        resp = session.post(_IL_DCFS_URL, data=form_data, headers=headers, timeout=DCFS_TIMEOUT)
        resp.raise_for_status()

        # Step 3: Parse CSV rows embedded in the response
        providers = []
        for row in csv.reader(io.StringIO(resp.text)):
            if len(row) < 17:
                continue
            if not re.match(r"^\d{6}$", str(row[0]).strip()):
                continue
            row_zip = str(row[5]).strip().split("-")[0][:5]
            target_zip = str(zip_code).strip()[:5]
            if target_zip and row_zip != target_zip:
                continue
            providers.append({
                "name": str(row[1]).strip(),
                "address": str(row[2]).strip(),
                "city": str(row[3]).strip(),
                "zip": row_zip,
                "capacity": int(float(str(row[14]).strip() or "0")) if str(row[14]).strip() else 0,
                "license_type": str(row[7]).strip(),
                "status": str(row[16]).strip(),
                "license_number": str(row[0]).strip(),
                "state": "IL",
            })

        # Cap for demo
        capped = providers[:MAX_PROVIDER_CAP]
        return json.dumps({
            "status": "ok",
            "zip_code": zip_code,
            "total_found": len(providers),
            "providers_returned": len(capped),
            "note": f"Showing {len(capped)} of {len(providers)} providers." if len(providers) > MAX_PROVIDER_CAP else "",
            "providers": capped,
        })

    except Exception as exc:
        return json.dumps({"status": "error", "error": str(exc)})


# ── Tool: get_property_data ────────────────────────────────────────────────────

def get_property_data(address: str, county: str = "Cook", state: str = "IL") -> str:
    """Get building and parcel data for a specific address from county GIS records.

    Returns building square footage, lot size, zoning, property class, and year built.

    Args:
        address: Full street address
        county: County name (default: Cook for Chicago/IL)
        state: State abbreviation (default: IL)
    """
    if not address:
        return json.dumps({"status": "error", "error": "address is required"})

    try:
        parsed = _parse_address(address)
        if "house" not in parsed or "street" not in parsed:
            return json.dumps({"status": "error", "error": f"Could not parse address: {address}"})

        parts = [parsed["house"]]
        if parsed.get("direction"):
            parts.append(parsed["direction"])
        parts.append(parsed["street"])
        if parsed.get("suffix"):
            parts.append(parsed["suffix"])
        addr_prefix = " ".join(parts)
        # Escape single quotes to prevent SoQL injection
        safe_prefix = addr_prefix.replace("'", "''")

        # Step 1: Resolve to PIN via Cook County address dataset
        pin: Optional[str] = None
        for query_pattern in [
            f"prop_address_full='{safe_prefix}'",
            f"starts_with(prop_address_full, '{safe_prefix}')",
        ]:
            params = {
                "$where": query_pattern,
                "$select": "pin",
                "$order": "year DESC",
                "$limit": "1",
            }
            r = requests.get(_COOK_ADDR_URL, params=params, timeout=TOOL_TIMEOUT)
            r.raise_for_status()
            rows = r.json()
            if rows:
                pin = rows[0].get("pin")
                break

        if not pin:
            return json.dumps({
                "status": "not_found",
                "address": address,
                "building_sqft": 0.0,
                "county": county,
                "state": state,
                "error": "No parcel PIN found for this address in Cook County dataset",
            })

        # Step 2: Try residential characteristics
        r = requests.get(_COOK_RES_URL, params={
            "pin": pin,
            "$select": "char_bldg_sf,char_land_sf,char_yrblt,class",
            "$order": "year DESC",
            "$limit": "1",
        }, timeout=TOOL_TIMEOUT)
        r.raise_for_status()
        rows = r.json()
        if rows and rows[0]:
            row = rows[0]
            sqft = float(row.get("char_bldg_sf") or 0)
            if sqft > 0:
                return json.dumps({
                    "status": "ok",
                    "address": address,
                    "building_sqft": sqft,
                    "lot_size": str(int(float(row.get("char_land_sf") or 0))),
                    "zoning": "",
                    "property_class": row.get("class", ""),
                    "year_built": int(float(row.get("char_yrblt") or 0)),
                    "county": "Cook",
                    "state": state,
                    "pin": pin,
                    "source": "Cook County Residential Characteristics (Socrata)",
                })

        # Step 3: Try commercial valuation (Cook County PINs are 14 digits)
        dashed = f"{pin[:2]}-{pin[2:4]}-{pin[4:7]}-{pin[7:10]}-{pin[10:]}" if len(pin) == 14 else pin
        r = requests.get(_COOK_COMMERCIAL_URL, params={
            "keypin": dashed,
            "$select": "bldgsf,landsf,yearbuilt,property_type_use",
            "$order": "year DESC",
            "$limit": "1",
        }, timeout=TOOL_TIMEOUT)
        r.raise_for_status()
        rows = r.json()
        if rows and rows[0]:
            row = rows[0]
            sqft = float(row.get("bldgsf") or 0)
            if sqft > 0:
                return json.dumps({
                    "status": "ok",
                    "address": address,
                    "building_sqft": sqft,
                    "lot_size": str(int(float(row.get("landsf") or 0))),
                    "zoning": "",
                    "property_class": row.get("property_type_use", ""),
                    "year_built": int(float(row.get("yearbuilt") or 0)),
                    "county": "Cook",
                    "state": state,
                    "pin": pin,
                    "source": "Cook County Commercial Valuation (Socrata)",
                })

        # Step 4: Assessed values fallback (no sqft)
        r = requests.get(_COOK_ASSESSED_URL, params={
            "pin": pin,
            "$select": "class,mailed_bldg,mailed_tot",
            "$order": "year DESC",
            "$limit": "1",
        }, timeout=TOOL_TIMEOUT)
        r.raise_for_status()
        rows = r.json()
        row = rows[0] if rows else {}
        return json.dumps({
            "status": "ok",
            "address": address,
            "building_sqft": 0.0,
            "lot_size": "",
            "zoning": "",
            "property_class": row.get("class", ""),
            "year_built": 0,
            "county": "Cook",
            "state": state,
            "pin": pin,
            "assessed_building_value": float(row.get("mailed_bldg") or 0),
            "assessed_total_value": float(row.get("mailed_tot") or 0),
            "source": "Cook County Assessed Values (Socrata)",
            "note": "No building sqft found; assessed value may help estimate size ($100-150/sqft rule of thumb)",
        })

    except Exception as exc:
        return json.dumps({"status": "error", "address": address, "error": str(exc)})


# ── Tool: calculate_max_capacity ──────────────────────────────────────────────

_CAPACITY_REGS = {
    "IL": {"sqft_per_child": 35, "regulation": "IL DCFS Title 89, Part 407"},
    "MN": {"sqft_per_child": 35, "regulation": "MN Rules 9503.0155"},
}


def calculate_max_capacity(building_sqft: float, state: str = "IL", usable_ratio: float = 0.65) -> str:
    """Calculate the maximum legal childcare capacity for a building based on state building code requirements.

    Shows the full calculation so findings can be verified.

    Args:
        building_sqft: Total building square footage
        state: State abbreviation (IL or MN)
        usable_ratio: Estimated ratio of usable childcare space to total sqft (default 0.65)
    """
    state_key = state.upper()
    reg = _CAPACITY_REGS.get(state_key)
    if not reg:
        return json.dumps({"status": "error", "error": f"State {state} not supported. Use IL or MN."})
    if not building_sqft or building_sqft <= 0:
        return json.dumps({"status": "error", "error": "building_sqft must be greater than 0"})

    sqft_per_child = reg["sqft_per_child"]
    usable_sqft = float(building_sqft) * float(usable_ratio)
    max_legal = int(usable_sqft // sqft_per_child)

    return json.dumps({
        "status": "ok",
        "building_sqft": float(building_sqft),
        "usable_ratio": usable_ratio,
        "usable_sqft": round(usable_sqft, 1),
        "sqft_per_child_required": sqft_per_child,
        "max_legal_capacity": max_legal,
        "state": state_key,
        "regulation": reg["regulation"],
        "calculation": f"{building_sqft} sqft × {usable_ratio} usable ratio = {usable_sqft:.0f} usable sqft ÷ {sqft_per_child} sqft/child = {max_legal} children max",
    })


# ── Tool: geocode_address ─────────────────────────────────────────────────────

def geocode_address(address: str) -> str:
    """Convert a street address to geographic coordinates (latitude/longitude).

    Args:
        address: Full street address to geocode
    """
    if not address:
        return json.dumps({"status": "error", "error": "address is required"})

    api_key = _google_key()
    if not api_key:
        return json.dumps({
            "status": "no_key",
            "address": address,
            "note": "No Google Maps API key configured. Geocoding unavailable.",
        })

    try:
        r = requests.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={"address": address, "key": api_key},
            timeout=TOOL_TIMEOUT,
        )
        r.raise_for_status()
        payload = r.json()
        status = payload.get("status", "").upper()
        if status == "REQUEST_DENIED":
            return json.dumps({"status": "error", "error": payload.get("error_message", "Request denied")})
        results = payload.get("results", [])
        if not results:
            return json.dumps({"status": "not_found", "address": address})
        loc = results[0]["geometry"]["location"]
        return json.dumps({
            "status": "ok",
            "address": address,
            "formatted_address": results[0].get("formatted_address"),
            "lat": loc.get("lat"),
            "lng": loc.get("lng"),
        })
    except Exception as exc:
        return json.dumps({"status": "error", "address": address, "error": str(exc)})


# ── Tool: get_street_view ─────────────────────────────────────────────────────

def get_street_view(address: str) -> str:
    """Capture Google Street View images of a location (4 angles: N/E/S/W).

    Returns image metadata. Images are stored in Streamlit session state and displayed after the investigation.

    Args:
        address: Street address to photograph
    """
    if not address:
        return json.dumps({"status": "error", "error": "address is required"})

    api_key = _google_key()
    if not api_key:
        return json.dumps({
            "status": "no_key",
            "address": address,
            "note": "No Google Maps API key. Street View unavailable.",
        })

    headings = [0, 90, 180, 270]
    images = []
    try:
        for heading in headings:
            params = {
                "location": address,
                "heading": heading,
                "size": "640x480",
                "key": api_key,
            }
            # Check metadata first
            meta_r = requests.get(
                "https://maps.googleapis.com/maps/api/streetview/metadata",
                params={**params, "return_error_codes": True},
                timeout=TOOL_TIMEOUT,
            )
            meta = meta_r.json()
            meta_status = meta.get("status", "").upper()
            if meta_status == "REQUEST_DENIED":
                return json.dumps({"status": "error", "error": meta.get("error_message", "Street View denied")})
            if meta_status != "OK":
                # ZERO_RESULTS = no imagery at this location; skip this heading
                continue

            img_r = requests.get(
                "https://maps.googleapis.com/maps/api/streetview",
                params=params,
                timeout=TOOL_TIMEOUT,
            )
            img_r.raise_for_status()
            images.append({
                "heading": heading,
                "capture_date": meta.get("date", "unknown"),
                "status": meta_status,
                "image_bytes": img_r.content,
            })

        if not images:
            return json.dumps({"status": "no_imagery", "address": address, "note": "No Street View imagery available for this address."})

        # Store raw image bytes in session state for Streamlit display.
        # Return only metadata to the LLM (base64 blobs are opaque text to the model
        # and would consume megabytes of context for a 10-provider investigation).
        cache = st.session_state.setdefault("street_view_cache", {})
        cache[address] = [
            {"heading": img["heading"], "capture_date": img["capture_date"], "image_bytes": img["image_bytes"]}
            for img in images
        ]

        return json.dumps({
            "status": "ok",
            "address": address,
            "images_captured": len(images),
            "capture_date": images[0].get("capture_date", "unknown"),
            "note": "Street View images captured. They will be displayed in the Surelock UI below the investigation narration.",
        })
    except Exception as exc:
        return json.dumps({"status": "error", "address": address, "error": str(exc)})


# ── Tool: get_places_info ─────────────────────────────────────────────────────

def get_places_info(address: str, name: str = "") -> str:
    """Get Google Places data for an address: business type, operating status, rating, and reviews.

    Args:
        address: Street address to look up
        name: Business or provider name to improve match accuracy (recommended)
    """
    if not address:
        return json.dumps({"status": "error", "error": "address is required"})

    api_key = _google_key()
    if not api_key:
        return json.dumps({
            "status": "no_key",
            "address": address,
            "note": "No Google Maps API key. Places lookup unavailable.",
        })

    try:
        # Build query plan — search by name first for best accuracy
        query_plan = []
        if name:
            query_plan.append((f"{name.strip()} {address}", False))
            query_plan.append((name.strip(), False))
        query_plan += [
            (f"childcare {address}", True),
            (f"day care {address}", True),
            (address, False),
        ]

        place_id: Optional[str] = None
        for query, require_childcare in query_plan:
            r = requests.get(
                "https://maps.googleapis.com/maps/api/place/findplacefromtext/json",
                params={"input": query, "inputtype": "textquery", "fields": "place_id,name,types", "key": api_key},
                timeout=TOOL_TIMEOUT,
            )
            r.raise_for_status()
            payload = r.json()
            candidates = payload.get("candidates", [])
            for c in candidates:
                if require_childcare:
                    types_str = " ".join(str(t) for t in c.get("types", []))
                    name_str = str(c.get("name", ""))
                    combined = (types_str + " " + name_str).lower()
                    if not any(t in combined for t in ("daycare", "day care", "child", "preschool", "school")):
                        continue
                place_id = c.get("place_id")
                break
            if place_id:
                break

        if not place_id:
            return json.dumps({
                "status": "no_place",
                "address": address,
                "note": "No Google Places listing found for this address.",
            })

        # Get full details
        detail_r = requests.get(
            "https://maps.googleapis.com/maps/api/place/details/json",
            params={
                "place_id": place_id,
                "fields": "name,business_status,rating,user_ratings_total,types,reviews,formatted_address",
                "key": api_key,
            },
            timeout=TOOL_TIMEOUT,
        )
        detail_r.raise_for_status()
        detail = detail_r.json().get("result", {})

        # Validate house number match
        expected_house = re.search(r"\b(\d+)\b", address or "")
        formatted = detail.get("formatted_address", "")
        if expected_house and formatted:
            if not re.search(rf"\b{re.escape(expected_house.group(1))}\b", formatted):
                return json.dumps({
                    "status": "address_mismatch",
                    "address": address,
                    "note": f"Place result address '{formatted}' doesn't match expected street number.",
                })

        reviews = [
            {"author": rv.get("author_name"), "rating": rv.get("rating"), "text": rv.get("text", "")[:200]}
            for rv in detail.get("reviews", [])[:3]
        ]

        return json.dumps({
            "status": "ok",
            "address": address,
            "place_name": detail.get("name"),
            "formatted_address": formatted,
            "business_type": ", ".join(detail.get("types", [])),
            "operating_status": detail.get("business_status"),
            "rating": detail.get("rating"),
            "review_count": detail.get("user_ratings_total", 0),
            "recent_reviews": reviews,
        })

    except Exception as exc:
        return json.dumps({"status": "error", "address": address, "error": str(exc)})


# ── Tool: check_business_registration ────────────────────────────────────────

def check_business_registration(name: str, state: str = "IL") -> str:
    """Look up business entity registration with the Secretary of State.

    Returns incorporation date, registered agent, entity type, and status.

    Args:
        name: Business name to search
        state: State abbreviation (IL supported)
    """
    if not name:
        return json.dumps({"status": "error", "error": "name is required"})

    state_key = state.upper()
    if state_key != "IL":
        return json.dumps({"status": "error", "error": "Only Illinois (IL) is supported in this demo."})

    try:
        # IL Secretary of State API (may return 403 behind CDN firewall)
        endpoint = "https://www.cyberdriveillinois.com/corpservices/api/entitysearch?" + urlencode({
            "searchstring": name.strip().lower()
        })
        r = requests.get(endpoint, timeout=TOOL_TIMEOUT)

        if r.status_code == 403:
            return json.dumps({
                "status": "blocked",
                "query": name,
                "state": state_key,
                "note": (
                    "IL SOS API returned 403 (CDN firewall). Direct access is unavailable. "
                    "Recommend manual lookup at: https://apps.ilsos.gov/corporatellc/"
                ),
            })

        if 200 <= r.status_code < 400:
            data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
            if data:
                return json.dumps({
                    "status": "ok",
                    "query": name,
                    "state": state_key,
                    "results": data,
                })
            return json.dumps({
                "status": "reachable_no_data",
                "query": name,
                "state": state_key,
                "note": "IL SOS endpoint reachable but returned no parseable data.",
            })

        return json.dumps({
            "status": "error",
            "query": name,
            "state": state_key,
            "error": f"IL SOS returned HTTP {r.status_code}",
        })

    except requests.exceptions.ConnectionError:
        return json.dumps({
            "status": "unavailable",
            "query": name,
            "state": state_key,
            "note": "IL SOS API unreachable. Manual lookup: https://apps.ilsos.gov/corporatellc/",
        })
    except Exception as exc:
        return json.dumps({"status": "error", "query": name, "state": state_key, "error": str(exc)})


# ── Streamlit App ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Surelock Homes — AI Fraud Investigation Agent",
    page_icon="🔍",
    layout="wide",
)

st.title("🔍 AI Fraud Investigation Agent")
st.caption(
    "Autonomous childcare provider fraud investigation using public licensing records, "
    "Cook County property data, Google Maps, and Claude via OpenRouter."
)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Configuration")

    openrouter_key = st.text_input(
        "OpenRouter API Key",
        type="password",
        help="Get one at openrouter.ai — free tier available",
    )
    google_key = st.text_input(
        "Google Maps API Key",
        type="password",
        help="Needs Geocoding, Places, and Street View APIs enabled. Optional — skips visual analysis if omitted.",
    )
    model_id = st.selectbox(
        "Model",
        options=[
            "anthropic/claude-sonnet-4.6",
            "anthropic/claude-opus-4.6",
            "google/gemini-3.1-flash-lite-preview",
            "openai/gpt-5.4",
            "openai/gpt-4o",
        ],
        index=0,
        help="Claude Sonnet is a good balance of speed and quality",
    )
    _COOK_COUNTY_ZIPS = [
        "60623",  # Little Village / North Lawndale
        "60629",  # Chicago Lawn
        "60644",  # Austin
        "60621",  # Englewood
        "60628",  # Roseland
        "60619",  # Chatham / Auburn Gresham
        "60636",  # West Englewood
        "60612",  # Near West Side
        "60620",  # Auburn Gresham
        "60624",  # Garfield Park
    ]
    zip_code = st.selectbox(
        "ZIP Code (Cook County, IL)",
        options=_COOK_COUNTY_ZIPS,
        index=_COOK_COUNTY_ZIPS.index("60623"),
        help="Property data is available for Cook County ZIPs only",
    )

    investigate_btn = st.button(
        "🔍 Start Investigation",
        type="primary",
        disabled=not openrouter_key,
        use_container_width=True,
    )

    st.divider()
    st.markdown(
        "**About:** This is a demo of [Surelock Homes](https://github.com/oso95/Surelock-Homes), "
        "an open-source autonomous fraud investigation system for subsidized childcare."
    )
    st.markdown(
        "**Scope:** Illinois only. Detects physical impossibility and anomalies in licensing records. "
        "Does **not** detect attendance fraud (requires non-public CCAP billing data)."
    )

# ── Main Investigation Area ───────────────────────────────────────────────────
if not investigate_btn:
    st.info(
        "Enter your OpenRouter API key in the sidebar and click **Start Investigation** to begin. "
        "The agent will search for licensed childcare providers in the ZIP code, "
        "cross-reference property records, and narrate its findings in real time."
    )
    with st.expander("How it works"):
        st.markdown("""
**The agent uses 7 investigation tools:**

| Tool | Source |
|------|--------|
| `search_childcare_providers` | Illinois DCFS licensing database |
| `get_property_data` | Cook County Assessor (Socrata open data) |
| `calculate_max_capacity` | IL DCFS Part 407 building code math |
| `get_street_view` | Google Street View API |
| `get_places_info` | Google Places API |
| `geocode_address` | Google Maps Geocoding API |
| `check_business_registration` | IL Secretary of State |

**What it looks for:**
- Licensed capacity exceeding physical building size (mathematical impossibility)
- Addresses where Google shows a different business or closed building
- Multiple providers sharing one address
- Providers with no Google presence, reviews, or business registration
- Geographic clusters that seem non-random

**What it cannot detect:**
- Attendance fraud (billing for children who didn't attend)
- Any fraud requiring non-public CCAP billing records
        """)

elif investigate_btn and openrouter_key:
    # Thread API keys to tool functions via session state (read by _google_key())
    st.session_state["google_maps_api_key"] = google_key or ""

    query = (
        f"Investigate all licensed childcare providers "
        f"in ZIP code {zip_code} in Illinois. "
        f"For each provider: get property data, calculate max legal capacity, "
        f"check Google Places and Street View, and look for anomalies. "
        f"Cross-reference business registrations when you spot patterns. "
        f"Narrate your full investigation."
    )

    st.markdown(f"### Investigation: ZIP {zip_code}")
    st.markdown(f"*Model: `{model_id}`*")
    st.divider()

    # Build agent
    try:
        agent = Agent(
            model=OpenRouter(id=model_id, api_key=openrouter_key, max_tokens=16384),
            tools=[
                search_childcare_providers,
                get_property_data,
                calculate_max_capacity,
                geocode_address,
                get_street_view,
                get_places_info,
                check_business_registration,
            ],
            description=_build_system_prompt(),
            instructions=[
                f"Investigate all providers returned for ZIP {zip_code}.",
                "For each Day Care Center with high capacity: deep investigation — property data, capacity calc, street view, places info.",
                "For Day Care Homes (small capacity): quick triage — note capacity vs legal limit.",
                "Cross-reference business registrations when owner names appear across multiple providers.",
                "Narrate your thinking as you investigate. The narration IS the product.",
                "Never say 'fraud' — use 'anomaly', 'requires further investigation', 'flags'.",
                "End with a summary of flagged providers and pattern findings.",
            ],
            markdown=True,
            compress_tool_results=True,  # Auto-compresses large tool responses to prevent context overflow
        )
    except Exception as exc:
        st.error(f"Failed to initialize agent: {exc}")
        st.stop()

    # Stream the investigation
    narration_area = st.empty()
    parts: list = []

    try:
        with st.spinner("Investigation in progress..."):
            for chunk in agent.run(query, stream=True):
                content = getattr(chunk, "content", None)
                if content:
                    parts.append(content)
                    narration_area.markdown("".join(parts))
        full_text = "".join(parts)

        st.success("Investigation complete.")

        # Display any Street View images collected during the investigation
        sv_cache: dict = st.session_state.get("street_view_cache", {})
        if sv_cache:
            st.markdown("### Street View Images")
            for addr, frames in sv_cache.items():
                st.markdown(f"**{addr}**")
                cols = st.columns(min(len(frames), 4))
                for col, frame in zip(cols, frames):
                    col.image(frame["image_bytes"], caption=f"Heading {frame['heading']}° · {frame['capture_date']}", use_container_width=True)
            st.session_state.pop("street_view_cache", None)

    except Exception as exc:
        st.error(f"Investigation error: {exc}")
        partial = "".join(parts)
        if partial:
            st.markdown("**Partial results:**")
            st.markdown(partial)
