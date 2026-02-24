# 🧾 AI Email Invoice Agent

An AI agent that automatically finds and extracts structured invoice data from your email using [iGPT](https://igpt.ai)'s Email Intelligence API. Connect your email, run the agent, and get back clean JSON with every invoice, receipt, and billing notification — vendor details, amounts, line items, payment status, and full source provenance.

## Features

- **Automatic discovery** — searches your connected email for invoices, receipts, subscription renewals, order confirmations, and credit memos
- **Structured extraction** — returns validated JSON with 30+ fields per invoice (vendor, amounts, dates, line items, payment method, etc.)
- **Attachment-aware** — treats PDF/HTML invoice attachments as the source of truth when they conflict with email body text
- **Built-in deduplication** — generates stable `dedupe_key` values so forwarded copies and reminder emails don't create duplicate records
- **Invoice classification** — categorizes each record as `subscription`, `one_time`, `usage_based`, `installment`, `credit_memo`, or `other`
- **Source tracing** — every extracted invoice links back to its source email (message ID, subject, sender, timestamp, attachment filenames)

## How It Works

1. Connects to iGPT with your API key and user ID
2. Checks for connected email datasources (prompts you to authorize if none exist)
3. Sends a detailed extraction prompt with a strict JSON schema to iGPT's `recall.ask()` endpoint
4. iGPT searches your email, reads messages and attachments, and returns structured invoice data

The entire extraction pipeline — email search, attachment parsing, thread context, deduplication, and structured output — is handled by a single API call.

## Getting Started

1. **Get your iGPT API credentials**
   - Sign up at [igpt.ai](https://igpt.ai) and get your API key
   - Note your user ID from the dashboard

2. **Clone the repository and navigate to the project**
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd awesome-llm-apps/advanced_ai_agents/single_agent_apps/ai_email_invoice_agent
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set your credentials** (or let the app prompt you)
   ```bash
   export IGPT_API_KEY="your-api-key"
   export IGPT_API_USER="your-user-id"
   ```

5. **Run the agent**
   ```bash
   python ai_email_invoice_agent.py
   ```

   On first run, if no email is connected yet, the agent will print an authorization URL. Open it to connect your email account, then run again.

## Example Output

```json
{
  "run_metadata": {
    "generated_at_utc": "2026-01-22T14:52:59Z",
    "date_range": "2025-01-01..2026-01-22",
    "query_terms": ["invoice", "receipt", "payment", "subscription"]
  },
  "invoices": [
    {
      "invoice_type": "subscription",
      "vendor_name": "Example SaaS Inc.",
      "vendor_domain": "example.com",
      "invoice_number": "INV-10492",
      "invoice_date": "2026-01-10",
      "plan_name": "Pro",
      "billing_interval": "monthly",
      "seats": 5,
      "currency": "USD",
      "total_amount": 100.0,
      "payment_status": "paid",
      "payment_method": "Visa **** 4242",
      "line_items": [
        {
          "description": "Pro plan (5 seats)",
          "quantity": 5,
          "unit_price_amount": 20.0,
          "amount": 100.0
        }
      ],
      "source_subject": "Your Example SaaS receipt (INV-10492)",
      "source_from": "billing@example.com",
      "source_attachment_filenames": ["InvoiceINV-10492.pdf"],
      "dedupe_key": "example.com_inv-10492"
    }
  ]
}
```

> The example above is abbreviated. Each invoice record includes 30+ fields — see `schema.py` for the full specification.
