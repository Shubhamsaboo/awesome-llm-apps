import json
import os
import uuid
from typing import Any

from langchain.tools import tool, ToolRuntime
from langchain.messages import ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.types import Command


def _get_llm():
    model_name = os.environ.get("OPENAI_MODEL", "gpt-5.5")
    return ChatOpenAI(model=model_name, temperature=0.3)


@tool
def extract_knowledge(runtime: ToolRuntime[Any]) -> Command:
    """Extract entities and relationships from uploaded documents or source code files. ALWAYS call this tool when the user adds files. Do not extract knowledge yourself."""

    import glob
    import tempfile

    existing_nodes = runtime.state.get("nodes", [])
    existing_edges = runtime.state.get("edges", [])

    upload_dir = os.path.join(tempfile.gettempdir(), "knowledge-explorer-uploads")
    all_content = ""
    doc_names = []

    if os.path.isdir(upload_dir):
        for fpath in sorted(glob.glob(os.path.join(upload_dir, "*"))):
            try:
                with open(fpath, "r") as f:
                    content = f.read()
                name = os.path.basename(fpath).split("-", 1)[-1] if "-" in os.path.basename(fpath) else os.path.basename(fpath)
                all_content += f"\n\n--- {name} ---\n{content}"
                doc_names.append(name)
                os.remove(fpath)
            except Exception:
                continue

    if not all_content.strip():
        messages = runtime.state.get("messages", [])
        for msg in reversed(messages):
            if hasattr(msg, "content") and isinstance(msg.content, str) and len(msg.content) > 100:
                if hasattr(msg, "type") and msg.type == "human":
                    all_content = msg.content
                    doc_names = ["pasted content"]
                    break

    if not all_content.strip():
        return Command(update={
            "messages": [ToolMessage(
                content="No content to process.",
                tool_call_id=runtime.tool_call_id
            )]
        })

    doc_names = [n for n in doc_names if n]

    existing_labels = {n["label"].lower() for n in existing_nodes}

    code_extensions = {".py", ".ts", ".tsx", ".js", ".jsx", ".java", ".go", ".rs", ".rb", ".vue", ".svelte", ".c", ".cpp", ".h", ".cs", ".swift", ".kt"}
    is_code = any(
        os.path.splitext(name)[1].lower() in code_extensions
        for name in doc_names
        if "." in name
    )

    llm = _get_llm()

    if is_code:
        extraction_prompt = f"""Analyze the following source code files and extract a knowledge graph of the codebase structure.

SOURCE CODE:
{all_content}

EXISTING NODES (avoid duplicates): {json.dumps([n["label"] for n in existing_nodes])}

Return ONLY valid JSON with this exact structure:
{{
  "nodes": [
    {{
      "label": "Node Name",
      "type": "module|class|function|variable|concept",
      "description": "One sentence description"
    }}
  ],
  "edges": [
    {{
      "source_label": "Source Node Name",
      "target_label": "Target Node Name",
      "label": "relationship type",
      "weight": 1
    }}
  ]
}}

RULES:
- Extract the structural elements: modules/files, classes, key functions, important constants/variables.
- 5-10 nodes per file. Focus on the public API and architecture, not every helper.
- Node types: module (file or package), class (class or interface), function (function or method), variable (important constant, config, or export), concept (design pattern or architectural idea).
- Relationship types for code: imports, exports, extends, implements, calls, returns, depends_on, defines, instantiates, part_of.
- Edge weights: 1=weak reference, 2=direct usage, 3=core dependency.
- If a node with the same label already exists, skip it.
- Return ONLY the JSON, no explanation."""
    else:
        extraction_prompt = f"""Analyze the following documents and extract a knowledge graph.

DOCUMENTS:
{all_content}

EXISTING NODES (avoid duplicates): {json.dumps([n["label"] for n in existing_nodes])}

Return ONLY valid JSON with this exact structure:
{{
  "nodes": [
    {{
      "label": "Node Name",
      "type": "entity|concept|theme",
      "description": "One sentence description"
    }}
  ],
  "edges": [
    {{
      "source_label": "Source Node Name",
      "target_label": "Target Node Name",
      "label": "relationship type (uses, extends, contradicts, part_of, causes, etc.)",
      "weight": 1
    }}
  ]
}}

RULES:
- Extract 5-8 nodes per document. Group related items.
- Prefer interesting relationships (contradicts, extends, causes) over flat "mentions".
- If a node with the same label already exists, skip it.
- Node types: entity (person, org, product), concept (idea, pattern, technique), theme (cross-cutting topic).
- Edge weights: 1=weak, 2=moderate, 3=strong.
- Return ONLY the JSON, no explanation."""

    response = llm.invoke(extraction_prompt)
    content = response.content.strip()

    if content.startswith("```"):
        content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return Command(update={
            "messages": [ToolMessage(
                content="Failed to parse extraction results. Try again.",
                tool_call_id=runtime.tool_call_id
            )]
        })

    new_nodes = []
    label_to_id = {n["label"].lower(): n["id"] for n in existing_nodes}

    for node_data in data.get("nodes", []):
        label = node_data["label"]
        if label.lower() in existing_labels:
            continue
        node_id = str(uuid.uuid4())[:8]
        label_to_id[label.lower()] = node_id
        existing_labels.add(label.lower())
        new_nodes.append({
            "id": node_id,
            "label": label,
            "type": node_data.get("type", "concept"),
            "description": node_data.get("description", ""),
            "detail": "",
            "sourceDocuments": doc_names,
        })

    new_edges = []
    for edge_data in data.get("edges", []):
        src_id = label_to_id.get(edge_data["source_label"].lower())
        tgt_id = label_to_id.get(edge_data["target_label"].lower())
        if src_id and tgt_id:
            new_edges.append({
                "id": str(uuid.uuid4())[:8],
                "source": src_id,
                "target": tgt_id,
                "label": edge_data.get("label", "related_to"),
                "weight": edge_data.get("weight", 1),
            })

    existing_docs = runtime.state.get("documents", [])
    existing_doc_names = {d["name"] for d in existing_docs}
    updated_docs = list(existing_docs)
    for name in doc_names:
        if name not in existing_doc_names:
            section = ""
            marker = f"--- {name} ---"
            if marker in all_content:
                start = all_content.index(marker) + len(marker)
                next_marker = all_content.find("\n\n---", start)
                section = all_content[start:next_marker].strip() if next_marker != -1 else all_content[start:].strip()
            updated_docs.append({
                "id": str(uuid.uuid4())[:8],
                "name": name,
                "content": section,
                "status": "extracted",
            })

    return Command(update={
        "documents": updated_docs,
        "nodes": existing_nodes + new_nodes,
        "edges": existing_edges + new_edges,
        "processingStatus": "ready",
        "messages": [ToolMessage(
            content=f"Extracted {len(new_nodes)} nodes and {len(new_edges)} relationships from {len(doc_names)} document(s).",
            tool_call_id=runtime.tool_call_id
        )]
    })


@tool
def find_connections(runtime: ToolRuntime[Any]) -> Command:
    """Find additional relationships between existing nodes.
    Call this after extraction to discover deeper connections."""

    nodes = runtime.state.get("nodes", [])
    existing_edges = runtime.state.get("edges", [])

    if len(nodes) < 2:
        return Command(update={
            "messages": [ToolMessage(
                content="Need at least 2 nodes to find connections.",
                tool_call_id=runtime.tool_call_id
            )]
        })

    existing_pairs = {(e["source"], e["target"]) for e in existing_edges}
    node_descriptions = "\n".join(
        f"- {n['label']} ({n['type']}): {n['description']}" for n in nodes
    )

    llm = _get_llm()
    prompt = f"""Given these knowledge graph nodes, find additional meaningful relationships between them.

NODES:
{node_descriptions}

EXISTING EDGES (don't duplicate):
{json.dumps([(e['source'], e['target'], e['label']) for e in existing_edges])}

Return ONLY valid JSON:
{{
  "edges": [
    {{
      "source_label": "Source Node Name",
      "target_label": "Target Node Name",
      "label": "relationship (contradicts, extends, causes, enables, part_of, etc.)",
      "weight": 2
    }}
  ]
}}

Focus on non-obvious connections. Prefer "contradicts", "extends", "causes" over "related_to"."""

    response = llm.invoke(prompt)
    content = response.content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return Command(update={
            "messages": [ToolMessage(
                content="Failed to parse connections.",
                tool_call_id=runtime.tool_call_id
            )]
        })

    label_to_id = {n["label"].lower(): n["id"] for n in nodes}
    new_edges = []
    for edge_data in data.get("edges", []):
        src_id = label_to_id.get(edge_data["source_label"].lower())
        tgt_id = label_to_id.get(edge_data["target_label"].lower())
        if src_id and tgt_id and (src_id, tgt_id) not in existing_pairs:
            new_edges.append({
                "id": str(uuid.uuid4())[:8],
                "source": src_id,
                "target": tgt_id,
                "label": edge_data.get("label", "related_to"),
                "weight": edge_data.get("weight", 1),
            })
            existing_pairs.add((src_id, tgt_id))

    return Command(update={
        "edges": existing_edges + new_edges,
        "messages": [ToolMessage(
            content=f"Found {len(new_edges)} additional connection(s).",
            tool_call_id=runtime.tool_call_id
        )]
    })


@tool
def expand_node(node_id: str, runtime: ToolRuntime[Any]) -> Command:
    """Deep-dive into a specific node. Extracts sub-concepts and adds
    detail from source documents. Call when the user clicks to expand a node."""

    nodes = runtime.state.get("nodes", [])
    edges = runtime.state.get("edges", [])
    docs = runtime.state.get("documents", [])

    target = next((n for n in nodes if n["id"] == node_id), None)
    if not target:
        return Command(update={
            "messages": [ToolMessage(
                content=f"Node {node_id} not found.",
                tool_call_id=runtime.tool_call_id
            )]
        })

    source_docs = [d for d in docs if d["name"] in target.get("sourceDocuments", [])]
    doc_context = "\n".join(f"[{d['name']}]: {d['content']}" for d in source_docs) if source_docs else "No source documents available."

    is_code_node = target['type'] in ("module", "class", "function", "variable")

    llm = _get_llm()

    if is_code_node:
        prompt = f"""Deep-dive into the code element "{target['label']}" ({target['type']}).
Current description: {target['description']}

Source material:
{doc_context}

Return ONLY valid JSON:
{{
  "detail": "A detailed 2-3 sentence explanation of what this code element does, its purpose, and how it fits into the codebase.",
  "sub_nodes": [
    {{
      "label": "Sub-element Name",
      "type": "function|class|variable|concept",
      "description": "One sentence"
    }}
  ],
  "sub_edges": [
    {{
      "source_label": "Parent or Sub-element Name",
      "target_label": "Sub-element Name",
      "label": "defines|calls|returns|depends_on|part_of",
      "weight": 2
    }}
  ]
}}

For modules: extract key exports, classes, and functions.
For classes: extract methods, properties, and parent classes.
For functions: extract parameters, return types, and called functions.
Extract 2-4 sub-elements that aren't already in the graph.
Existing node labels: {json.dumps([n['label'] for n in nodes])}"""
    else:
        prompt = f"""Deep-dive into the concept "{target['label']}" ({target['type']}).
Current description: {target['description']}

Source material:
{doc_context}

Return ONLY valid JSON:
{{
  "detail": "A detailed 2-3 sentence explanation of this concept based on the source material.",
  "sub_nodes": [
    {{
      "label": "Sub-concept Name",
      "type": "concept",
      "description": "One sentence"
    }}
  ],
  "sub_edges": [
    {{
      "source_label": "Parent or Sub-concept Name",
      "target_label": "Sub-concept Name",
      "label": "part_of|enables|uses",
      "weight": 2
    }}
  ]
}}

Extract 2-4 sub-concepts that aren't already in the graph.
Existing node labels: {json.dumps([n['label'] for n in nodes])}"""

    response = llm.invoke(prompt)
    content = response.content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return Command(update={
            "messages": [ToolMessage(
                content="Failed to parse expansion results.",
                tool_call_id=runtime.tool_call_id
            )]
        })

    existing_labels = {n["label"].lower() for n in nodes}
    label_to_id = {n["label"].lower(): n["id"] for n in nodes}

    updated_nodes = []
    for n in nodes:
        if n["id"] == node_id:
            updated_nodes.append({**n, "detail": data.get("detail", n.get("detail", ""))})
        else:
            updated_nodes.append(n)

    new_nodes = []
    for sub in data.get("sub_nodes", []):
        if sub["label"].lower() not in existing_labels:
            nid = str(uuid.uuid4())[:8]
            label_to_id[sub["label"].lower()] = nid
            existing_labels.add(sub["label"].lower())
            new_nodes.append({
                "id": nid,
                "label": sub["label"],
                "type": sub.get("type", "concept"),
                "description": sub.get("description", ""),
                "detail": "",
                "sourceDocuments": target.get("sourceDocuments", []),
            })

    new_edges = []
    for edge_data in data.get("sub_edges", []):
        src_id = label_to_id.get(edge_data["source_label"].lower())
        tgt_id = label_to_id.get(edge_data["target_label"].lower())
        if src_id and tgt_id:
            new_edges.append({
                "id": str(uuid.uuid4())[:8],
                "source": src_id,
                "target": tgt_id,
                "label": edge_data.get("label", "part_of"),
                "weight": edge_data.get("weight", 2),
            })

    return Command(update={
        "nodes": updated_nodes + new_nodes,
        "edges": edges + new_edges,
        "selectedNodeId": node_id,
        "messages": [ToolMessage(
            content=f"Expanded '{target['label']}' with {len(new_nodes)} sub-concept(s).",
            tool_call_id=runtime.tool_call_id
        )]
    })


knowledge_tools = [extract_knowledge, find_connections, expand_node]
