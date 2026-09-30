#!/usr/bin/env python3
"""Pay an x402 request (HTTP 402 or MCP tool challenge) with the active wallet.

Over HTTP: fetches a paywalled URL, reads the server's x402 payment
requirements, signs an EIP-3009 authorization with `mm wallet sign-typed-data`,
retries with the payment header, and reports the settlement. Supports x402
protocol v1 (X-PAYMENT) and v2 (PAYMENT-SIGNATURE). Signing is delegated to
`mm`, so the private key stays in the wallet.

Over MCP (x402 v2 MCP transport): a paid MCP tool answers an unpaid call with a
tool result carrying `isError: true` and the PaymentRequired data. The MCP
session belongs to the caller, so this script does not speak MCP; it takes that
challenge, signs the same EIP-3009 authorization, and prints the PaymentPayload
to place, as a raw JSON object, in `_meta["x402/payment"]` of the retried tool
call. The settlement comes back in the response `_meta["x402/payment-response"]`.

Usage:
    python3 x402_pay.py inspect <url> [--method M] [--data BODY]
    python3 x402_pay.py pay <url> --confirm --approved <approvalId>
                                  [--method M] [--data BODY]
                                  [--asset <contract>] [--network <network>]
    python3 x402_pay.py mcp-inspect [--challenge JSON | --challenge-file PATH]
    python3 x402_pay.py mcp-sign [--challenge JSON | --challenge-file PATH]
                                 --confirm --approved <approvalId>
                                 [--asset <contract>] [--network <network>]

`inspect` fetches the URL and prints the payment requirement(s) as JSON
(asset, amount, network, payTo, resource) without signing or spending. Each
option carries an `approvalId` that fingerprints its debit terms. Show the terms
to the user and keep the `approvalId` of the option they approve.

`pay` runs the payment for a single offered option and prints the settlement
(transaction hash) and the resource body. It requires --confirm and
--approved <approvalId>. It fetches the 402 again and refuses to sign when the
fresh offer's terms no longer match the approved ones. When the 402 offers more
than one eligible option, select one with --asset or --network. A 200 response
without a decodable settlement receipt is reported as `paid_unverified`, not
`settled`; do not pay again in that case.

`mcp-inspect` parses an MCP payment challenge (the tool-call response, the tool
result, or the bare PaymentRequired object; from --challenge, --challenge-file,
or stdin via --challenge -) and prints the payment options without signing or
spending.

`mcp-sign` signs one offered option from an MCP challenge and prints the
payment payload for the retry's `_meta["x402/payment"]`. It requires --confirm
and --approved <approvalId> from `mcp-inspect`, and takes the same
--asset/--network disambiguators as `pay`.

The resource may use any HTTP method; pass --method (and --data for a request
body) and the same request is replayed with the payment attached.

The script pays the exact scheme on networks `mm` supports; which currencies
and amounts are allowed is the wallet's decision at signing. Each run makes one
payment with a single retry; rerunning makes a new payment, so guard repeated
calls at the caller. A local idempotency ledger is a possible future addition.

Examples:
    python3 x402_pay.py inspect https://paid.example.com/premium
    python3 x402_pay.py pay https://paid.example.com/premium --confirm
"""

import argparse
import base64
import hashlib
import json
import re
import secrets
import subprocess
import sys
import time
import urllib.error
import urllib.request
from decimal import Decimal
from urllib.parse import urlparse

ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}


class CeremonyError(Exception):
    """An expected failure to surface to the caller."""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Surfaces redirects instead of following them.

    A cross-host redirect on a payment request could divert payment to a host
    the user never chose, so the 3xx is returned and rejected by the caller.
    """

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_OPENER = urllib.request.build_opener(_NoRedirect)


def _check_url(url):
    """Reject plaintext URLs so a payment is never sent over http.

    Loopback is exempt to allow testing against a local resource server.
    """
    parsed = urlparse(url)
    if parsed.scheme == "https":
        return
    if parsed.scheme == "http" and parsed.hostname in LOOPBACK_HOSTS:
        return
    raise CeremonyError("resource URL must be https:// (http allowed only on loopback)")


def http(url, method="GET", headers=None, body=None):
    """Make a request. Returns (status, headers, body_bytes); no raise on 4xx/5xx."""
    _check_url(url)
    req = urllib.request.Request(url, data=body, method=method, headers=headers or {})
    try:
        resp = _OPENER.open(req, timeout=30)
        return resp.status, resp.headers, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.headers, e.read()


def request_parts(data, content_type):
    """Turn an optional request body string into (bytes, headers) for replay.

    x402 is method-agnostic, so a paid POST must be sent identically on both the
    initial request and the retry that carries the payment.
    """
    if data is None:
        return None, {}
    return data.encode("utf-8"), {"Content-Type": content_type}


def _json_objects(text):
    """Return every top-level JSON object in `text`, in order.

    `mm` may print non-JSON warnings (e.g. Node startup notices) around its
    result, and with --json it writes an MFA notice as its own NDJSON line
    before the result. Decoding object by object keeps those apart instead of
    gluing the first "{" to the last "}" into one invalid document.
    """
    decoder = json.JSONDecoder()
    objects = []
    i = text.find("{")
    while i != -1:
        try:
            obj, end = decoder.raw_decode(text, i)
        except ValueError:
            i = text.find("{", i + 1)
            continue
        if isinstance(obj, dict):
            objects.append(obj)
        i = text.find("{", end)
    return objects


def _mm_json(args):
    """Run an `mm` command and return its JSON result, skipping notices.

    Objects carrying `_notice` (such as `AWAITING_MFA`) are status lines, not
    the result. When the output holds only notices, the last one is returned
    so the caller can surface the approval state to the user.
    """
    out = subprocess.run(["mm", *args], capture_output=True, text=True)
    objects = _json_objects(out.stdout)
    if not objects:
        raise CeremonyError("mm produced no JSON (%s): %s" % (out.returncode, out.stderr.strip()))
    results = [o for o in objects if "_notice" not in o]
    return results[-1] if results else objects[-1]


_chains_cache = None


def _chains():
    """Return mm's supported chains, so network support stays the wallet's call."""
    global _chains_cache
    if _chains_cache is None:
        _chains_cache = (_mm_json(["chains", "list", "--json"]).get("data") or {}).get("chains", [])
    return _chains_cache


def chain_id_for(network):
    """Resolve an x402 network identifier to an EVM chain id.

    Accepts v2 CAIP-2 ids (e.g. "eip155:8453") directly and v1 network names
    (e.g. "base-sepolia") by matching mm's chain list.
    """
    if network.startswith("eip155:"):
        try:
            wanted = int(network.split(":", 1)[1])
        except ValueError:
            raise CeremonyError("unparseable CAIP-2 network: %s" % network)
        # A parseable id is not enough: only chains mm lists can be signed on.
        for c in _chains():
            try:
                listed = int(c.get("chainId"))
            except (TypeError, ValueError):
                listed = None
            if listed == wanted or c.get("caip2") == network:
                return wanted
        raise CeremonyError("network '%s' is not supported by mm (see `mm chains list`)" % network)
    for c in _chains():
        if (
            network in (c.get("key"), c.get("caip2"))
            or network.lower() == (c.get("name") or "").lower()
        ):
            return c.get("chainId")
    raise CeremonyError("network '%s' is not supported by mm (see `mm chains list`)" % network)


_asset_meta_cache = {}


def asset_meta(chain_id, asset):
    """Look up an asset's symbol and decimals from mm, for display only.

    Returns None when mm cannot resolve it (e.g. testnets the Token API does
    not index); the signed amount is the server's atomic value regardless.
    """
    if chain_id is None or not asset:
        return None
    key = (chain_id, asset.lower())
    if key not in _asset_meta_cache:
        meta = None
        try:
            res = _mm_json(
                [
                    "token",
                    "assets",
                    "--asset-ids",
                    "eip155:%s/erc20:%s" % (chain_id, asset),
                    "--json",
                ]
            )
            assets = (res.get("data") or {}).get("assets") or []
            if assets and assets[0].get("decimals") is not None:
                meta = {"symbol": assets[0].get("symbol"), "decimals": assets[0]["decimals"]}
        except (CeremonyError, ValueError):
            meta = None
        _asset_meta_cache[key] = meta
    return _asset_meta_cache[key]


def _normalize_accepts(accepts):
    """Turn an accepts[] array into the option dicts the rest of the flow uses.

    Reads v2 `amount` with a fallback to the v1 wire name `maxAmountRequired`;
    missing that fallback would sign a null value on a v1 offer. A non-dict
    `extra` (e.g. an explicit null) is coerced to {} so validate() reports the
    missing EIP-712 domain instead of crashing.
    """
    options = []
    for a in accepts:
        amount = a.get("amount", a.get("maxAmountRequired"))
        extra = a.get("extra")
        options.append(
            {
                "scheme": a.get("scheme"),
                "network": a.get("network"),
                "amount": str(amount) if amount is not None else None,
                "payTo": a.get("payTo"),
                "asset": a.get("asset"),
                "maxTimeoutSeconds": a.get("maxTimeoutSeconds", 3600),
                "extra": extra if isinstance(extra, dict) else {},
                "resource": a.get("resource"),
            }
        )
    return options


def parse_402(status, headers, body):
    """Return (version, [option, ...], resource_info). Raises if not a usable 402.

    resource_info is the v2 top-level ResourceInfo object (v2 forwards it into
    the payment payload); it is None for v1, which carries resource per option.
    """
    if status != 402:
        raise CeremonyError("expected HTTP 402, got %s" % status)

    # v2 carries requirements in the PAYMENT-REQUIRED header; v1 in the body.
    # The accepts[] array is what marks a response as a standard x402 challenge:
    # other paywalls also answer 402 but with their own, unsupported schemes.
    pr = headers.get("PAYMENT-REQUIRED")
    if pr:
        try:
            data = json.loads(base64.b64decode(pr))
        except (ValueError, UnicodeDecodeError) as e:
            raise CeremonyError("could not parse the PAYMENT-REQUIRED header: %s" % e)
        version = 2
    else:
        try:
            data = json.loads(body.decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as e:
            raise CeremonyError("could not parse the 402 response body: %s" % e)
        version = 1
        # No PAYMENT-REQUIRED header and no accepts[] means another paywall
        # scheme answering 402, not x402.
        if not isinstance(data, dict) or "accepts" not in data:
            raise CeremonyError(
                "received HTTP 402 but it is not a standard x402 challenge "
                "(no PAYMENT-REQUIRED header and no accepts[] in the body); "
                "this endpoint uses a payment scheme this script does not support"
            )

    accepts = (data.get("accepts") if isinstance(data, dict) else None) or []
    options = _normalize_accepts(accepts)
    if not options:
        raise CeremonyError("402 had no payment options")
    resource_info = data.get("resource") if isinstance(data, dict) else None
    return version, options, resource_info


def _payment_required_from(result):
    """Extract the PaymentRequired object from an MCP tool result, or None.

    The MCP transport spec has servers put it in both structuredContent (the
    object itself) and content[0].text (its JSON encoding), and tells clients
    to prefer structuredContent; the text form is the fallback for the spec's
    settlement-failure example, whose text is not even parseable JSON.

    Cloudflare's Agents SDK (`agents/x402` `withX402`/`paidTool`) — the most
    substantial real server implementation found in the wild — puts it in
    `_meta["x402/error"]` instead of structuredContent (verified by reading
    its source and a live local run); checked explicitly rather than relying
    on the content[].text fallback catching it by coincidence.
    """
    sc = result.get("structuredContent")
    if isinstance(sc, dict) and "accepts" in sc:
        return sc
    meta_error = (result.get("_meta") or {}).get("x402/error")
    if isinstance(meta_error, dict) and "accepts" in meta_error:
        return meta_error
    for entry in result.get("content") or []:
        if not (isinstance(entry, dict) and entry.get("type") == "text"):
            continue
        try:
            data = json.loads(entry.get("text") or "")
        except ValueError:
            continue
        if isinstance(data, dict) and "accepts" in data:
            return data
    return None


def parse_mcp_challenge(data):
    """Return ([option, ...], resource_info, error_text) from an MCP challenge.

    Accepts whichever shape the caller has at hand: the whole JSON-RPC
    response, the tool result, or the bare PaymentRequired object. The MCP
    transport is defined for x402 v2 only, so any other x402Version is
    refused rather than guessed at.
    """
    if not isinstance(data, dict):
        raise CeremonyError("challenge must be a JSON object")
    if isinstance(data.get("result"), dict):
        data = data["result"]
    if "accepts" not in data:
        pr = _payment_required_from(data)
        if pr is None:
            raise CeremonyError(
                "not an x402 payment challenge: no PaymentRequired found in "
                "structuredContent or content[].text (expected the result of "
                "an unpaid call to a paid MCP tool)"
            )
        data = pr
    version = data.get("x402Version")
    if version is None:
        raise CeremonyError(
            "challenge has an accepts[] array but no x402Version; "
            "not a valid x402 PaymentRequired object"
        )
    if version != 2:
        raise CeremonyError(
            "unsupported x402Version %r: the x402 MCP transport is defined for v2 only" % version
        )
    options = _normalize_accepts(data.get("accepts") or [])
    if not options:
        raise CeremonyError("challenge had no payment options")
    resource_info = data.get("resource")
    if isinstance(resource_info, str):
        # v1-styled servers send resource as a bare URL string; v2 wants an object.
        resource_info = {"url": resource_info}
    elif resource_info is not None and not isinstance(resource_info, dict):
        raise CeremonyError("challenge resource must be an object or a URL string")
    return options, resource_info, data.get("error")


def read_challenge(challenge, challenge_file):
    """Load the MCP challenge JSON from --challenge or --challenge-file.

    stdin is read only when explicitly requested with `--challenge -`: agents
    commonly run this script with an open non-TTY pipe on stdin, where an
    implicit stdin fallback would block forever instead of reporting the
    missing flag.
    """
    if challenge is not None and challenge_file:
        raise CeremonyError("pass --challenge or --challenge-file, not both")
    if challenge == "-":
        raw = sys.stdin.read()
    elif challenge is not None:
        raw = challenge
    elif challenge_file:
        try:
            with open(challenge_file, "r", encoding="utf-8") as f:
                raw = f.read()
        except OSError as e:
            raise CeremonyError("could not read --challenge-file: %s" % e)
    else:
        raise CeremonyError(
            "no challenge given: pass --challenge '<json>' (or '-' to read stdin) "
            "or --challenge-file <path>"
        )
    if not raw.strip():
        raise CeremonyError("challenge input is empty")
    try:
        return json.loads(raw)
    except ValueError as e:
        raise CeremonyError("challenge is not valid JSON: %s" % e)


def approval_id(option):
    """Fingerprint the debit terms the user approves.

    Covers every field that decides what is paid, to whom, and where. `pay`
    and `mcp-sign` recompute it on the offer they are about to sign and refuse
    on any mismatch, so a server that changes its offer after `inspect` cannot
    get a different debit authorized.
    """
    terms = {
        "scheme": option.get("scheme"),
        "network": option.get("network"),
        "asset": (option.get("asset") or "").lower(),
        "payTo": (option.get("payTo") or "").lower(),
        "amount": option.get("amount"),
        "assetTransferMethod": (option.get("extra") or {}).get("assetTransferMethod")
        or "eip3009",
    }
    digest = hashlib.sha256(json.dumps(terms, sort_keys=True).encode()).hexdigest()
    return "x402-" + digest[:16]


def describe(option):
    """Annotate an option with chain and display metadata; never raises."""
    out = dict(option)
    out["approvalId"] = approval_id(option)
    try:
        chain_id = chain_id_for(option["network"])
    except CeremonyError:
        chain_id = None
    out["chainId"] = chain_id
    # extra.assetTransferMethod is absent on v1 and on eip3009 v2 offers; only an
    # explicit "permit2" is ineligible, since this script signs EIP-3009 only.
    transfer = (option.get("extra") or {}).get("assetTransferMethod")
    out["assetTransferMethod"] = transfer or "eip3009"
    out["eligible"] = (
        chain_id is not None
        and option.get("scheme") == "exact"
        and out["assetTransferMethod"] == "eip3009"
    )
    meta = asset_meta(chain_id, option.get("asset"))
    if meta:
        out["symbol"] = meta["symbol"]
        out["decimals"] = meta["decimals"]
        amount = option.get("amount")
        if isinstance(amount, str) and amount.isdigit():
            out["humanAmount"] = str(Decimal(amount) / (Decimal(10) ** meta["decimals"]))
    return out


def select(options, want_asset=None, want_network=None):
    """Pick the single payable option, or raise so the caller can react.

    Requires exactly one option with the exact scheme on a network mm supports;
    --asset/--network narrow the choice when a server offers several, since
    picking one silently could spend on an asset the user did not intend.
    """
    described = [describe(o) for o in options]
    eligible = []
    for d in described:
        if not d["eligible"]:
            continue
        if want_asset and (d.get("asset") or "").lower() != want_asset.lower():
            continue
        if want_network and d.get("network") != want_network:
            continue
        eligible.append(d)
    if not eligible:
        exact_on_chain = [
            d for d in described if d.get("chainId") is not None and d.get("scheme") == "exact"
        ]
        if exact_on_chain and all(d["assetTransferMethod"] == "permit2" for d in exact_on_chain):
            raise CeremonyError(
                "the only payable options use the permit2 asset transfer method, which this "
                "script does not support (it signs EIP-3009 transferWithAuthorization only). "
                "Offered: %s" % json.dumps(described)
            )
        raise CeremonyError(
            "no eligible option (need scheme 'exact', EIP-3009, on a network mm supports). "
            "Offered: %s" % json.dumps(described)
        )
    if len(eligible) > 1:
        raise CeremonyError(
            "multiple eligible options; disambiguate with --asset/--network. "
            "Eligible: %s" % json.dumps(eligible)
        )
    return eligible[0]


def wallet_address():
    """Return the active wallet address, the payer for the authorization."""
    d = _mm_json(["wallet", "address", "--json"]).get("data")
    return d["address"] if isinstance(d, dict) else d


def sign_typed_data(chain_id, payload, intent):
    """Sign EIP-712 typed data with `mm`, keeping the key inside the wallet."""
    res = _mm_json(
        [
            "wallet",
            "sign-typed-data",
            "--chain-id",
            str(chain_id),
            "--wait",
            "--json",
            "--intent",
            intent,
            "--payload",
            json.dumps(payload),
        ]
    )
    sig = (res.get("data") or {}).get("signature")
    if not res.get("ok") or not sig:
        raise CeremonyError("signing failed: %s" % json.dumps(res))
    return sig


def build_typed_data(option, chain_id, from_addr):
    """Build the EIP-3009 TransferWithAuthorization message to sign.

    validBefore honors the server's maxTimeoutSeconds so the facilitator can
    settle within the window it asked for; any ceiling on how long an
    authorization may live is the wallet's policy, not a constant here. A random
    nonce keeps each authorization single-use.
    """
    now = int(time.time())
    nonce = "0x" + secrets.token_bytes(32).hex()
    authorization = {
        "from": from_addr,
        "to": option["payTo"],
        "value": option["amount"],
        # Backdate validAfter: the spec allows "0", and the official Python
        # client uses it, but the TypeScript reference client backdates 10
        # minutes because some facilitators reject "0" and it absorbs clock
        # skew. Follow the safer value.
        "validAfter": str(now - 600),
        "validBefore": str(now + int(option["maxTimeoutSeconds"])),
        "nonce": nonce,
    }
    typed_data = {
        "types": {
            "EIP712Domain": [
                {"name": "name", "type": "string"},
                {"name": "version", "type": "string"},
                {"name": "chainId", "type": "uint256"},
                {"name": "verifyingContract", "type": "address"},
            ],
            "TransferWithAuthorization": [
                {"name": "from", "type": "address"},
                {"name": "to", "type": "address"},
                {"name": "value", "type": "uint256"},
                {"name": "validAfter", "type": "uint256"},
                {"name": "validBefore", "type": "uint256"},
                {"name": "nonce", "type": "bytes32"},
            ],
        },
        "primaryType": "TransferWithAuthorization",
        "domain": {
            "name": option["extra"].get("name"),
            "version": option["extra"].get("version"),
            "chainId": chain_id,
            "verifyingContract": option["asset"],
        },
        "message": authorization,
    }
    return typed_data, authorization


def build_payment(version, option, resource_info, signature, authorization, url):
    """Assemble the PaymentPayload for the chosen option.

    The envelope differs by version (x402 spec section 5.2): v2 nests the chosen
    requirements under `accepted` and forwards the `resource`, while v1 puts
    `scheme`/`network` at the top level. A facilitator rejects a v2 payload that
    is missing `accepted`.
    """
    if version == 2:
        return {
            "x402Version": 2,
            "resource": resource_info or {"url": url},
            "accepted": {
                "scheme": option["scheme"],
                "network": option["network"],
                "amount": option["amount"],
                "asset": option["asset"],
                "payTo": option["payTo"],
                "maxTimeoutSeconds": option["maxTimeoutSeconds"],
                "extra": option.get("extra", {}),
            },
            "payload": {"signature": signature, "authorization": authorization},
        }
    return {
        "x402Version": 1,
        "scheme": option["scheme"],
        "network": option["network"],
        "payload": {"signature": signature, "authorization": authorization},
    }


def validate(option, chain_id):
    """Check the offer is structurally sound before signing.

    Currency and spend policy are the wallet's responsibility; this only
    guards protocol correctness so a malformed offer is never signed.
    """
    if option["scheme"] != "exact":
        raise CeremonyError("scheme must be 'exact', got %r" % option["scheme"])
    if chain_id is None:
        raise CeremonyError("network %r is not supported by mm" % option.get("network"))
    if not option["asset"] or not ADDRESS_RE.match(option["asset"]):
        raise CeremonyError("asset is not a valid contract address: %r" % option.get("asset"))
    if not option["amount"] or not option["amount"].isdigit() or int(option["amount"]) <= 0:
        raise CeremonyError(
            "amount must be a positive atomic-unit integer, got %r" % option["amount"]
        )
    if not option["payTo"] or not ADDRESS_RE.match(option["payTo"]):
        raise CeremonyError("payTo is not a valid address: %r" % option["payTo"])
    if not option["extra"].get("name") or not option["extra"].get("version"):
        raise CeremonyError("402 option missing EIP-712 domain name/version in 'extra'")


def sign_challenge(
    version, options, want_asset, want_network, resource_info, target, approved, transport=""
):
    """Run the signing ceremony for one eligible option of a challenge.

    Both transports converge here — select, validate, build and sign the
    EIP-3009 authorization, assemble the version-correct PaymentPayload — so
    the spend semantics cannot drift between them. How the challenge arrived
    and how the payment is delivered stay in the callers. `target` is what the
    user sees in the signing intent (and the v2 resource fallback over HTTP).
    """
    option = select(options, want_asset, want_network)
    if option["approvalId"] != approved:
        raise CeremonyError(
            "the offer's terms differ from the approved ones (approved %s, offered %s): "
            "%s. Nothing was signed. Show the new terms to the user and re-run with the "
            "approvalId they approve." % (approved, option["approvalId"], json.dumps(option))
        )
    chain_id = option["chainId"]
    validate(option, chain_id)

    from_addr = wallet_address()
    typed_data, authorization = build_typed_data(option, chain_id, from_addr)

    intent = "x402%s: %s %s to %s for %s" % (
        " (%s)" % transport if transport else "",
        option.get("humanAmount", option["amount"]),
        option.get("symbol", ""),
        option["payTo"],
        target,
    )
    signature = sign_typed_data(chain_id, typed_data, intent)
    payment = build_payment(version, option, resource_info, signature, authorization, target)
    return option, payment


def settlement(headers, version, body):
    """Decode the facilitator's settlement receipt.

    The spec puts it in the X-PAYMENT-RESPONSE / PAYMENT-RESPONSE header, but
    some servers return it only in the response body, so fall back to the body
    when the header is absent.
    """
    name = "X-PAYMENT-RESPONSE" if version == 1 else "PAYMENT-RESPONSE"
    raw = headers.get(name)
    if raw:
        try:
            return json.loads(base64.b64decode(raw))
        except (ValueError, UnicodeDecodeError):
            pass
    try:
        data = json.loads(body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return None
    if isinstance(data, dict) and (data.get("transaction") or data.get("txHash")):
        return data
    return None


def failure_reason(headers, body):
    """Extract why a paid retry was rejected.

    A v2 server re-challenges with the reason in the PAYMENT-REQUIRED header and
    often an empty body, so check that header before falling back to the body.
    """
    pr = headers.get("PAYMENT-REQUIRED")
    if pr:
        try:
            err = json.loads(base64.b64decode(pr)).get("error")
            if err:
                return err
        except (ValueError, UnicodeDecodeError):
            pass
    text = body.decode("utf-8", "replace").strip()
    try:
        err = json.loads(text).get("error")
        if err:
            return err
    except (ValueError, AttributeError):
        pass
    return text or "(no detail)"


def cmd_inspect(url, method, data, content_type):
    """Print the 402 payment requirement(s) without signing or spending."""
    body, headers = request_parts(data, content_type)
    status, rheaders, rbody = http(url, method, headers, body)
    version, options, resource_info = parse_402(status, rheaders, rbody)
    print(
        json.dumps(
            {
                "status": "payment_required",
                "x402Version": version,
                "resource": resource_info,
                "options": [describe(o) for o in options],
            },
            indent=2,
        )
    )


def _require_approval(confirm, approved, inspect_cmd, retry_cmd):
    """Refuse to sign unless the user approved specific terms."""
    if not confirm or not approved:
        raise CeremonyError(
            "refusing to sign without --confirm and --approved <approvalId>; run '%s' "
            "first, get user approval for one option, then re-run '%s --confirm "
            "--approved <approvalId>'" % (inspect_cmd, retry_cmd)
        )


def cmd_pay(url, method, data, content_type, confirm, approved, want_asset, want_network):
    """Run the payment for one approved option and print the settlement."""
    _require_approval(confirm, approved, "inspect", "pay <url>")
    body, headers = request_parts(data, content_type)
    # Fetch fresh so the short 402 window is never stale; sign_challenge then
    # refuses unless the fresh offer still matches the approved terms.
    status, rheaders, rbody = http(url, method, headers, body)
    version, options, resource_info = parse_402(status, rheaders, rbody)
    option, payment = sign_challenge(
        version, options, want_asset, want_network, resource_info, url, approved
    )
    b64 = base64.b64encode(json.dumps(payment).encode()).decode()
    header = "X-PAYMENT" if version == 1 else "PAYMENT-SIGNATURE"

    # Replay the same request with the payment attached.
    status, rheaders, rbody = http(url, method, dict(headers, **{header: b64}), body)
    if status != 200:
        # One attempt only: do not retry a payment.
        raise CeremonyError(
            "payment not accepted (HTTP %s): %s" % (status, failure_reason(rheaders, rbody))
        )

    settle = settlement(rheaders, version, rbody)
    transaction = (settle or {}).get("transaction") or (settle or {}).get("txHash")
    try:
        resource = json.loads(rbody.decode("utf-8"))
    except ValueError:
        resource = rbody.decode("utf-8", "replace")
    result = {
        "status": "settled" if transaction else "paid_unverified",
        "asset": option.get("symbol", option["asset"]),
        "amount": option.get("humanAmount", option["amount"]),
        "network": option["network"],
        "payTo": option["payTo"],
        "transaction": transaction,
        "settlement": settle,
        "resource": resource,
    }
    if not transaction:
        # The server accepted the signed authorization but sent no receipt, so
        # settlement cannot be confirmed here. Paying again would sign a second
        # authorization with a new nonce.
        result["note"] = (
            "The server returned HTTP 200 without a decodable settlement receipt. "
            "The authorization was sent and may settle. Do not pay again; check "
            "the wallet's transaction history before any retry."
        )
    print(json.dumps(result, indent=2))


def cmd_mcp_inspect(challenge, challenge_file):
    """Print an MCP challenge's payment options without signing or spending."""
    options, resource_info, error = parse_mcp_challenge(read_challenge(challenge, challenge_file))
    print(
        json.dumps(
            {
                "status": "payment_required",
                "x402Version": 2,
                "error": error,
                "resource": resource_info,
                "options": [describe(o) for o in options],
            },
            indent=2,
        )
    )


def cmd_mcp_sign(challenge, challenge_file, confirm, approved, want_asset, want_network):
    """Sign one option from an MCP challenge and print the payment payload.

    The MCP session belongs to the caller, so delivery is the caller's move:
    place the printed `payment` object, as-is, in `_meta["x402/payment"]` of
    the retried tool call.
    """
    _require_approval(confirm, approved, "mcp-inspect", "mcp-sign")
    options, resource_info, _ = parse_mcp_challenge(read_challenge(challenge, challenge_file))
    # Fail closed before signing: the v2 payload must forward the resource, so
    # a challenge that names none could only yield a payload the facilitator
    # rejects after a real authorization was already signed.
    if not resource_info or not resource_info.get("url"):
        raise CeremonyError(
            "challenge has no resource URL; pass the full PaymentRequired object "
            "(its top-level resource is forwarded into the payment payload)"
        )
    option, payment = sign_challenge(
        2, options, want_asset, want_network, resource_info, resource_info["url"], approved, "MCP"
    )
    payment_b64 = base64.b64encode(json.dumps(payment).encode()).decode()
    print(
        json.dumps(
            {
                "status": "signed",
                "asset": option.get("symbol", option["asset"]),
                "amount": option.get("humanAmount", option["amount"]),
                "network": option["network"],
                "payTo": option["payTo"],
                "metaKey": "x402/payment",
                "payment": payment,
                "paymentBase64": payment_b64,
                "note": (
                    "Use `payment` (the raw object) for servers that follow the MCP "
                    "transport spec literally (coinbase/x402 specs/transports-v2/mcp.md). "
                    "Use `paymentBase64` for servers built with Cloudflare's Agents SDK "
                    "(`agents/x402` withX402/paidTool) — its real implementation "
                    "base64-decodes _meta[\"x402/payment\"] rather than reading it as an "
                    "inline object, diverging from the spec text."
                ),
            },
            indent=2,
        )
    )


def main(argv=None):
    """Parse arguments and report CeremonyError as JSON on stderr."""
    parser = argparse.ArgumentParser(
        description="Pay an HTTP 402 (x402) request with the active wallet."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # The skill tells agents to "always use --toon"; this is a script, not an mm
    # command, and always prints JSON. Accept and ignore those format flags so
    # the reflex does not error.
    fmt = argparse.ArgumentParser(add_help=False)
    fmt.add_argument("--toon", action="store_true", help=argparse.SUPPRESS)
    fmt.add_argument("--json", action="store_true", help=argparse.SUPPRESS)
    fmt.add_argument("-f", "--format", help=argparse.SUPPRESS)

    # Shared spend flags for the two signing subcommands, defined once so the
    # confirm ceremony and disambiguators cannot drift between transports.
    spend = argparse.ArgumentParser(add_help=False)
    spend.add_argument(
        "--confirm", action="store_true", help="Required. Explicit user approval to sign and spend."
    )
    spend.add_argument(
        "--approved",
        metavar="APPROVAL_ID",
        help="Required. The approvalId of the option the user approved, from inspect/mcp-inspect. "
        "Signing is refused if the offer's terms no longer match.",
    )
    spend.add_argument("--asset", help="Disambiguate by asset contract when multiple are offered.")
    spend.add_argument("--network", help="Disambiguate by network when multiple are offered.")

    for p in (
        sub.add_parser("inspect", parents=[fmt], help="Fetch and parse a 402 (read-only)."),
        sub.add_parser("pay", parents=[fmt, spend], help="Run the full payment ceremony."),
    ):
        p.add_argument("url")
        p.add_argument(
            "--method",
            default="GET",
            help="HTTP method to request the resource with (default GET).",
        )
        p.add_argument("--data", help="Request body to send (and replay on the paid retry).")
        p.add_argument(
            "--content-type",
            default="application/json",
            help="Content-Type for --data (default application/json).",
        )

    for p in (
        sub.add_parser(
            "mcp-inspect", parents=[fmt], help="Parse an MCP payment challenge (read-only)."
        ),
        sub.add_parser(
            "mcp-sign",
            parents=[fmt, spend],
            help="Sign one option from an MCP challenge and print the payment payload.",
        ),
    ):
        p.add_argument(
            "--challenge",
            help="The challenge JSON: the tool-call response, the tool result, or the bare "
            "PaymentRequired object; pass '-' to read it from stdin.",
        )
        p.add_argument("--challenge-file", help="Path to a file holding the challenge JSON.")

    args = parser.parse_args(argv)
    try:
        if args.command == "inspect":
            cmd_inspect(args.url, args.method.upper(), args.data, args.content_type)
        elif args.command == "pay":
            cmd_pay(
                args.url,
                args.method.upper(),
                args.data,
                args.content_type,
                args.confirm,
                args.approved,
                args.asset,
                args.network,
            )
        elif args.command == "mcp-inspect":
            cmd_mcp_inspect(args.challenge, args.challenge_file)
        elif args.command == "mcp-sign":
            cmd_mcp_sign(
                args.challenge,
                args.challenge_file,
                args.confirm,
                args.approved,
                args.asset,
                args.network,
            )
    except CeremonyError as e:
        print(json.dumps({"status": "error", "error": str(e)}), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
