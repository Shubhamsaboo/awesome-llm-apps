OUTPUT_FORMAT = {
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["run_metadata", "invoices"],
        "properties": {
            "run_metadata": {
                "type": "object",
                "additionalProperties": False,
                "required": ["generated_at_utc", "date_range", "query_terms"],
                "properties": {
                    "generated_at_utc": {
                        "type": "string",
                        "description": "UTC timestamp when this extraction output was generated (ISO 8601 recommended, e.g., '2026-01-21T15:09:04Z')."
                    },
                    "date_range": {
                        "type": ["string", "null"],
                        "description": "Date/time filter applied to the source search (free-text or structured, e.g., '2025-01-01..2025-12-31'); null if no range was used."
                    },
                    "query_terms": {
                        "type": ["array", "null"],
                        "description": "Search keywords/filters used to locate the source messages (e.g., ['invoice', 'receipt', 'billing']); null if none were used.",
                        "items": {"type": "string"}
                    }
                }
            },
            "invoices": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "invoice_type",
                        "vendor_name",
                        "vendor_domain",
                        "vendor_billing_email",
                        "invoice_number",
                        "order_id",
                        "invoice_date",
                        "due_date",
                        "service_period_start",
                        "service_period_end",
                        "plan_name",
                        "billing_interval",
                        "seats",
                        "usage_window_start",
                        "usage_window_end",
                        "description",
                        "currency",
                        "subtotal_amount",
                        "discount_amount",
                        "tax_amount",
                        "total_amount",
                        "payment_status",
                        "paid_date",
                        "payment_method",
                        "line_items",
                        "source_id",
                        "source_subject",
                        "source_from",
                        "source_occurred_at_utc",
                        "source_attachment_filenames",
                        "source_filename",
                        "extraction_notes",
                        "dedupe_key"
                    ],
                    "properties": {
                        "invoice_type": {
                            "type": "string",
                            "enum": ["one_time", "subscription", "usage_based", "installment", "credit_memo", "other"],
                            "description": "Classification of the invoice/charge type based on billing model (e.g., subscription renewal, usage charge, one-time purchase)."
                        },
                        "vendor_name": { 
                            "type": "string",
                            "description": "Display/legal name of the vendor issuing the invoice (e.g., 'Slack', 'Amazon Web Services')." 
                        },
                        "vendor_domain": { 
                            "type": ["string", "null"],
                            "description": "Vendor website or email domain if available (e.g., 'slack.com')."
                        },
                        "vendor_billing_email": { 
                            "type": ["string", "null"],
                            "description": "Billing/support email address shown on the invoice or billing notification (e.g., 'billing@vendor.com')."
                        },
                        "invoice_number": { 
                            "type": ["string", "null"],
                            "description": "Invoice identifier assigned by the vendor; null if not present."
                        },
                        "order_id": {
                            "type": ["string", "null"],
                            "description": "Order/receipt/transaction ID associated with the invoice; null if not present."
                        },
                        "invoice_date": {
                            "type": ["string", "null"],
                            "description": "Invoice issue date in YYYY-MM-DD format; null if missing/unknown."
                        },
                        "due_date": {
                            "type": ["string", "null"], 
                            "description": "Payment due date in YYYY-MM-DD format; null if not specified (common for auto-paid receipts)."
                        },
                        "service_period_start": {
                            "type": ["string", "null"],
                            "description": "Start date of the billed service period in YYYY-MM-DD format (primarily for subscriptions); null if not applicable."
                        },
                        "service_period_end": {
                            "type": ["string", "null"],
                            "description": "End date of the billed service period in YYYY-MM-DD format (primarily for subscriptions); null if not applicable."
                        },
                        "plan_name": {
                            "type": ["string", "null"],
                            "description": "Name of the subscription plan/SKU/tier (e.g., 'Pro', 'Business'); null if not specified."
                        },
                        "billing_interval": {
                            "type": ["string", "null"],
                            "enum": ["daily", "day", "weekly", "week", "biweekly", "monthly", "month", "bimonthly", "quarterly", "annual", "semiannual", "yearly", "year", "biennial", "triennial", None],
                            "description": "Recurring billing cadence for subscriptions; null when not applicable or not known."
                        },
                        "seats": {
                            "type": ["number", "null"],
                            "description": "Number of seats/licenses/users billed; null if not stated or not applicable."
                        },
                        "usage_window_start": {
                            "type": ["string", "null"],
                            "description": "Start date of the usage measurement window in YYYY-MM-DD format (primarily for usage-based billing); null if not applicable."
                        },
                        "usage_window_end": {
                            "type": ["string", "null"],
                            "description": "End date of the usage measurement window in YYYY-MM-DD format (primarily for usage-based billing); null if not applicable."
                        },
                        "description": {
                            "type": ["string", "null"],
                            "description": "Free-text summary of what the invoice is for (high-level description); null if none."
                        },
                        "currency": {
                            "type": ["string", "null"],
                            "description": "Currency code for amounts (ISO 4217 when possible, e.g., 'USD', 'EUR'); null if not known."
                        },
                        "subtotal_amount": {
                            "type": ["number", "null"],
                            "description": "Amount before discounts and taxes (in invoice currency); null if not provided."
                        },
                        "discount_amount": {
                            "type": ["number", "null"],
                            "description": "Total discounts/credits applied (positive number representing the discount magnitude); null if none/unknown."
                        },
                        "tax_amount": {
                            "type": ["number", "null"],
                            "description": "Total tax amount charged (e.g., VAT/GST/sales tax); null if not provided."
                        },
                        "total_amount": {
                            "type": ["number", "null"],
                            "description": "Final amount due/paid after discounts and taxes (in invoice currency); null if not provided."
                        },
                        "payment_status": {
                            "type": "string",
                            "enum": ["active", "trialing", "success", "paid", "captured", "authorized", "pending", "unprocessed", "processing", "requires_confirmation", "requires_action", "incomplete", "partially_paid", "unpaid", "overdue", "uncollectible", "refunded", "partially_refunded", "disputed", "chargeback", "canceled", "void", "voided", "expired", "failure", "failed", "declined", "unknown"],
                            "description": "Payment state as indicated by the vendor email/invoice. Use 'unknown' if not explicitly determinable."
                        },
                        "paid_date": {
                            "type": ["string", "null"],
                            "description": "Date payment was made/settled in YYYY-MM-DD format; ONLY populate if explicitly stated, else null."
                        },
                        "payment_method": {
                            "type": ["string", "null"],
                            "description": "Payment method shown (e.g., 'Visa ****1234', 'ACH', 'PayPal'); null if not provided."
                        },
                        "line_items": {
                            "type": ["array", "null"],
                            "description": "Itemized charges making up the invoice total; null if the source provides no itemization.",
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "required": ["description", "quantity", "unit_price_amount", "amount"],
                                "properties": {
                                    "description": {
                                        "type": "string",
                                        "description": "Line item label/description (e.g., 'Pro plan', 'Compute hours')."
                                    },
                                    "quantity": {
                                        "type": ["number", "null"],
                                        "description": "Quantity/units for the line item (e.g., seats, hours); null if not specified."
                                    },
                                    "unit_price_amount": {
                                        "type": ["number", "null"],
                                        "description": "Per-unit price for the line item in invoice currency; null if not specified."
                                    },
                                    "amount": {
                                        "type": ["number", "null"],
                                        "description": "Total amount for this line item in invoice currency; null if not specified."
                                    }
                                }
                            }
                        },

                        "source_id": {
                            "type": "string",
                            "description": "Unique identifier of the source entity from which the invoice data was extracted (message id or cloud file id)."
                        },
                        "source_subject": {
                            "type": ["string", "null"],
                            "description": "Subject line of the source email/message if provided; null for cloud files."
                        },
                        "source_from": {
                            "type": ["string", "null"],
                            "description": "From header/sender identity of the source email/message if provided; null for cloud files."
                        },
                        "source_occurred_at_utc": {
                            "type": ["string", "null"],
                            "description": "Event time in UTC: email/message received time OR cloud file modified/created time (ISO 8601 recommended, e.g., '2026-01-21T14:57:58Z')."
                        },
                        "source_attachment_filenames": {
                            "type": ["array", "null"],
                            "description": "Filenames of attachments (e.g., PDF invoices) associated with the source, if the source is an email/message; null otherwise.",
                            "items": { "type": "string" }
                        },
                        "source_filename": {
                            "type": ["string", "null"],
                            "description": "Filename when the source is a cloud file; null if not applicable."
                        },
                        "extraction_notes": {
                            "type": ["array", "null"],
                            "description": "Optional notes about ambiguities, assumptions, parsing issues, or confidence warnings from extraction.",
                            "items": {"type": "string"}
                        },
                        "dedupe_key": {
                            "type": ["string", "null"],
                            "description": "Stable key used to detect duplicates (e.g., vendor+invoice_number+total+date); null if not computed."
                        }
                    }
                }
            }
        }
    }
}
