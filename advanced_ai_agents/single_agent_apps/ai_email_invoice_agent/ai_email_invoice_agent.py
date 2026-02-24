import getpass
import os
from pprint import pprint
from igptai import IGPT
from prompts import SYSTEM_PROMPT
from schema import OUTPUT_FORMAT


def run_invoice_agent(api_key: str, user: str) -> dict:
    """Connect to iGPT and extract invoices from the user's email."""
    client = IGPT(api_key=api_key, user=user)

    # Check for connected datasources
    ds_resp = client.datasources.list()
    if ds_resp.get("error"):
        return ds_resp

    if not ds_resp.get("datasources"):
        connect = client.connectors.authorize(service="spike", scope="messages")
        if connect.get("error"):
            return connect
        return {
            "error": f"No datasources found. Open this URL to authorize your email:\n{connect.get('url')}"
        }

    # Run extraction
    return client.recall.ask(
        input=SYSTEM_PROMPT,
        quality="cef-1-normal",
        output_format=OUTPUT_FORMAT,
    )


if __name__ == "__main__":
    api_key = os.environ.get("IGPT_API_KEY") or getpass.getpass("IGPT API KEY:\n")
    user = os.environ.get("IGPT_API_USER") or getpass.getpass("IGPT API USER:\n")

    data = run_invoice_agent(api_key, user)

    if data.get("error"):
        print(data)
    else:
        pprint(data["output"], sort_dicts=False)
