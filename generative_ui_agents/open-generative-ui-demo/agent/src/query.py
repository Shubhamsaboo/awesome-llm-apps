from langchain.tools import tool
from pathlib import Path
import csv

# Read data at module load time to avoid file I/O issues in
# LangGraph Cloud's sandboxed tool execution environment.
_csv_path = Path(__file__).parent / "db.csv"
with open(_csv_path) as _f:
    _cached_data = list(csv.DictReader(_f))

@tool
def query_data(query: str):
    """
    Query the database, takes natural language. Call this first when you need real data
    to render in an Open Generative UI sandbox (e.g., charts, dashboards, tables).
    """
    return _cached_data
