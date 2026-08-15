#!/usr/bin/env python3
"""Validate a SandBase multi-source research report without network access."""

# SPDX-License-Identifier: Apache-2.0

import json
import sys
from pathlib import Path


SOURCE_TYPES = {"primary", "secondary", "aggregator"}
CLAIM_KINDS = {"sourced", "inference"}
CONFIDENCE_MINIMUMS = {"low": 1, "medium": 2, "high": 3}


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def valid_url(value):
    if not nonempty(value):
        return False
    if not (value.startswith("https://") or value.startswith("http://")):
        return False
    authority = value.split("://", 1)[1].split("/", 1)[0]
    return bool(authority) and "." in authority and not any(char.isspace() for char in authority)


def validate(report):
    errors = []
    if not isinstance(report, dict):
        return ["report must be a JSON object"]

    for field in ("question", "searched_at"):
        if not nonempty(report.get(field)):
            errors.append("%s must be a non-empty string" % field)

    providers = report.get("providers")
    if not isinstance(providers, list) or not all(nonempty(item) for item in providers):
        errors.append("providers must be an array of non-empty strings")
        providers = []
    if len(set(providers)) < 2:
        errors.append("providers must contain at least two unique capabilities")
    if len(set(providers)) != len(providers):
        errors.append("providers must not contain duplicates")

    unavailable = report.get("unavailable_providers")
    if not isinstance(unavailable, list) or not all(nonempty(item) for item in unavailable):
        errors.append("unavailable_providers must be an array of non-empty strings")

    sources = report.get("sources")
    if not isinstance(sources, list) or not sources:
        errors.append("sources must be a non-empty array")
        sources = []
    source_ids = set()
    source_urls = set()
    for index, source in enumerate(sources):
        label = "sources[%d]" % index
        if not isinstance(source, dict):
            errors.append("%s must be an object" % label)
            continue
        source_id = source.get("id")
        if not nonempty(source_id):
            errors.append("%s.id must be a non-empty string" % label)
        elif source_id in source_ids:
            errors.append("duplicate source id: %s" % source_id)
        else:
            source_ids.add(source_id)
        url = source.get("url")
        if not valid_url(url):
            errors.append("%s.url must be an HTTP(S) URL" % label)
        elif url in source_urls:
            errors.append("duplicate source URL: %s" % url)
        else:
            source_urls.add(url)
        if not nonempty(source.get("publisher")):
            errors.append("%s.publisher must be a non-empty string" % label)
        if source.get("source_type") not in SOURCE_TYPES:
            errors.append("%s.source_type must be primary, secondary, or aggregator" % label)

    claims = report.get("claims")
    if not isinstance(claims, list) or not claims:
        errors.append("claims must be a non-empty array")
        claims = []
    claim_ids = set()
    used_sources = set()
    for index, claim in enumerate(claims):
        label = "claims[%d]" % index
        if not isinstance(claim, dict):
            errors.append("%s must be an object" % label)
            continue
        claim_id = claim.get("id")
        if not nonempty(claim_id):
            errors.append("%s.id must be a non-empty string" % label)
        elif claim_id in claim_ids:
            errors.append("duplicate claim id: %s" % claim_id)
        else:
            claim_ids.add(claim_id)
        if not nonempty(claim.get("text")):
            errors.append("%s.text must be a non-empty string" % label)
        if claim.get("kind") not in CLAIM_KINDS:
            errors.append("%s.kind must be sourced or inference" % label)
        confidence = claim.get("confidence")
        if confidence not in CONFIDENCE_MINIMUMS:
            errors.append("%s.confidence must be low, medium, or high" % label)
        refs = claim.get("source_ids")
        if not isinstance(refs, list) or not refs or not all(nonempty(item) for item in refs):
            errors.append("%s.source_ids must be a non-empty string array" % label)
            refs = []
        if len(set(refs)) != len(refs):
            errors.append("%s.source_ids must not contain duplicates" % label)
        for source_id in refs:
            if source_id not in source_ids:
                errors.append("%s references unknown source id: %s" % (label, source_id))
            else:
                used_sources.add(source_id)
        count = claim.get("independent_source_count")
        if not isinstance(count, int) or isinstance(count, bool) or count < 0:
            errors.append("%s.independent_source_count must be a non-negative integer" % label)
        else:
            if count > len(set(refs)):
                errors.append("%s independent source count exceeds its source references" % label)
            minimum = CONFIDENCE_MINIMUMS.get(confidence)
            if minimum is not None and count < minimum:
                errors.append("%s confidence %s requires at least %d independent sources" % (label, confidence, minimum))
        if not isinstance(claim.get("conflict"), bool):
            errors.append("%s.conflict must be true or false" % label)
        elif claim.get("conflict") and confidence == "high":
            errors.append("%s cannot be high confidence while conflict is true" % label)

    for source_id in sorted(source_ids - used_sources):
        errors.append("source is not referenced by any claim: %s" % source_id)

    gaps = report.get("gaps")
    if not isinstance(gaps, list) or not all(nonempty(item) for item in gaps):
        errors.append("gaps must be an array of non-empty strings")

    return errors


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 1:
        print("usage: validate_report.py REPORT.json", file=sys.stderr)
        return 2
    path = Path(argv[0])
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        print("INVALID: %s" % error, file=sys.stderr)
        return 1
    errors = validate(report)
    if errors:
        for error in errors:
            print("ERROR: %s" % error, file=sys.stderr)
        print("INVALID: %d error(s)" % len(errors), file=sys.stderr)
        return 1
    print("VALID: %d source(s), %d claim(s), %d provider(s)" % (
        len(report["sources"]), len(report["claims"]), len(set(report["providers"]))
    ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
