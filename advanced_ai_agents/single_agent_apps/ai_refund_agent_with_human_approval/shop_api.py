"""
Example Shop's internal API - the tools the refund agent uses.

Every endpoint runs only with a Provenza permit for exactly that call: a
signature by the organization over the tool and the hash of the JSON body,
valid for a few minutes and redeemable once. The agent gets a permit only
when Provenza allowed the call, so an agent that skips the check, changes
an argument after the check, or replays an old call gets 403 here - the
decision does not depend on the agent's own code.

    uvicorn shop_api:app --port 8765        (app.py starts it for you)
"""

import os
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from provenza.permit import HEADER, PermitError, PermitVerifier

PROVENZA_URL = os.environ.get("PROVENZA_URL", "http://localhost:8080")
PROVENZA_ORG = os.environ.get("PROVENZA_ORG", "provenza")

ORDERS: Dict[str, Dict[str, Any]] = {
    "A-1001": {"customer": "Maria Lopez", "item": "Ceramic mug", "total": 18.0, "status": "delivered"},
    "A-1002": {"customer": "Tom Becker", "item": "Standing desk", "total": 240.0, "status": "lost in transit"},
    "A-1003": {"customer": "Aiko Tanaka", "item": "Headphones", "total": 59.0, "status": "delivered"},
}
CUSTOMERS = [
    {"name": "Maria Lopez", "email": "maria.lopez@mail.example", "card_last4": "4242"},
    {"name": "Tom Becker", "email": "tom.becker@mail.example", "card_last4": "1881"},
    {"name": "Aiko Tanaka", "email": "aiko.tanaka@mail.example", "card_last4": "0005"},
]
REFUNDS: Dict[str, float] = {}
OUTBOX: list = []


def create_app(verifier: Any = None) -> FastAPI:
    verifier = verifier or PermitVerifier(PROVENZA_URL, org=PROVENZA_ORG)
    api = FastAPI(title="Example Shop API")

    async def permitted(request: Request, tool: str) -> Dict[str, Any]:
        body = await request.json()
        # raises PermitError unless Provenza allowed exactly this tool with exactly this body
        verifier.verify(request.headers.get(HEADER), tool=f"shop.{tool}", input=body)
        return body

    @api.exception_handler(PermitError)
    async def refused(_: Request, exc: PermitError):
        return JSONResponse({"error": exc.code, "detail": "no valid Provenza permit for this call"}, status_code=403)

    @api.post("/lookup_order")
    async def lookup_order(request: Request):
        body = await permitted(request, "lookup_order")
        order = ORDERS.get(str(body.get("order_id")))
        return order and {"order_id": body["order_id"], **order, "refunded": REFUNDS.get(body["order_id"], 0)} \
            or {"error": "no such order"}

    @api.post("/issue_refund")
    async def issue_refund(request: Request):
        body = await permitted(request, "issue_refund")
        order = ORDERS.get(str(body.get("order_id")))
        amount = float(body.get("amount", 0))
        if not order:
            return {"error": "no such order"}
        if amount <= 0 or amount + REFUNDS.get(body["order_id"], 0) > order["total"]:
            return {"error": f"a refund of {amount:.2f} is more than what is left of the order"}
        REFUNDS[body["order_id"]] = REFUNDS.get(body["order_id"], 0) + amount
        return {"refunded": amount, "order_id": body["order_id"], "currency": "USD"}

    @api.post("/reply_to_ticket")
    async def reply_to_ticket(request: Request):
        body = await permitted(request, "reply_to_ticket")
        return {"sent": True, "ticket_id": body.get("ticket_id")}

    @api.post("/send_email")
    async def send_email(request: Request):
        body = await permitted(request, "send_email")
        OUTBOX.append(body)
        return {"sent": True, "to": body.get("to")}

    @api.post("/export_customers")
    async def export_customers(request: Request):
        await permitted(request, "export_customers")
        return {"customers": CUSTOMERS}

    return api


app = create_app()
