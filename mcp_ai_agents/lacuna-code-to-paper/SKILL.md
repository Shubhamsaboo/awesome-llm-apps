---
name: lacuna-code-to-paper
description: Trace an ML code repository, dataset, or model to its linked research papers with Lacuna. Use when a user asks which papers an implementation comes from, how code relates to a paper, or what research to read before changing it.
compatibility: Requires internet access and a connected Lacuna MCP server. The bundled Python tutorial requires Python 3.11+.
---

# Trace code to papers

If Lacuna tools are unavailable, point to the
[setup instructions](https://github.com/tiptreesystems/lacuna-research-mcp#install)
and stop the Lacuna lookup.

1. Identify the resource from the user's URL or local README and dependency
   metadata. Query public resource names only; do not send private code or URLs.
2. Use `search_lacuna` with `search_type="resource"` and the matching
   `resource_kind`: `"codebase"` for repositories, `"dataset"` for datasets, or
   `"model"` for models. Match the returned provider, key, title, and URL to the
   intended resource; rank and stars do not establish identity.
   Renames can leave old provider keys, so verify aliases against recorded URLs or
   the original repository. If no candidate matches, retry once without
   `resource_kind`, keeping `search_type="resource"` and the same identity checks.
   If no match is established or several remain plausible, show the candidates
   and stop before attributing papers.
3. Use `get_resource` to inspect `publications`, relationship labels, `evidence_url`,
   any recorded `basis`, and the collection timestamp. A README mention is not a
   recorded `official_code_for` relationship; other labels may describe different
   connections.
4. Follow relevant `paper_id` values with `get_paper`. Check original sources before
   making implementation claims, and distinguish the original paper from follow-ups.

Return the resource, relevant papers, relationship labels, recorded basis, and
evidence links.
Distinguish recorded relationships from independently verified connections or
inferences. If no publication link is recorded, say so; separate paper-search
results are candidates until verified. Search counts and detail collections can
differ; neither establishes complete coverage.
