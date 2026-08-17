# Reference Rules — Detailed Rules for Reference Correctness

## Check Method

For each MD file, run `python3 <skill-dir>/scripts/extract_refs.py <file>` to extract and classify all reference patterns, then verify each one manually. If the script is unavailable, fall back to Grep to extract the patterns.

### Reference Pattern Matching

```
# Internal links: [text](path/to/file.md) or [text](path/to/file.md#anchor)
# Anchor links: [text](#anchor)
# Image references: ![alt](path/to/image.png)
# External links: [text](https://...)
# Auto links: <https://...>
# Reference links: [text][ref] and [ref]: url
```

## Internal Link Checks

### File References
- **MUST** `[text](relative-path.md)` — verify the target file exists
- **MUST** `[text](relative-path.md#anchor)` — verify the target file exists and the anchor exists
- **SHOULD** verify the reference path uses the correct relative base (relative between documents vs. project root path)

### Anchor Verification
- **MUST** `[text](#anchor)` — check whether a matching anchor exists in the same document
- Anchor matching rule: GitHub-style anchor generation (lowercase, strip punctuation, spaces to hyphens)
  - `## My Section` → `#my-section`
  - `## API Reference (v2)` → `#api-reference-v2`
- **SHOULD** check whether the referenced anchor is accurate (near-but-not-exact anchors may point to the wrong location)

### Image References
- **MUST** `![alt](path/to/image.png)` — does the image file exist?
- **MAY** is the image size reasonable? (shouldn't reference a huge uncompressed image)

## External Link Checks

### URL Format
- **MUST** is the URL format complete? (with `https://` or `http://` protocol header)
- **MUST** no placeholder links: `[text]()` empty parentheses
- **SHOULD** no spelling errors in `[text](url)` URLs
- **SHOULD** URLs pointing to well-known sites use HTTPS

### Link Text Quality
- **MUST** no non-descriptive link text:
  - ❌ "click here", "read more", "this page", "link"
  - ✅ descriptive text, e.g., "view the installation guide", "see the API docs"
- **SHOULD** link text match the URL content
  - Example: link text says "Pricing details" but the URL slug is `/blog/technical-post` → mismatch
- **SHOULD** no links inside headings (links in headings are hard to click and lose context when printed)

### External Link Health (MAY)
- If the environment allows, check link status with `curl -sI -o /dev/null -w "%{http_code}" <url>`
- 200/301/302: normal; 4xx/5xx: abnormal
- Note: this check is time-consuming; sample only in `--format full` mode

## Cross-Reference Checks

This skill reviews one document per invocation; only checks executable on that single document are listed here. Reference targets are verified for existence and anchors only.

### Document Reference Completeness
- [ ] Do the referenced file names exist? (target file present on disk)
- [ ] Is the case of referenced file names correct? (case-sensitive file systems)
- [ ] Do the referenced anchors/sections exist in the target file? (verified from the target file's heading outline only — never a full review of the target)
- [ ] Are version-number references internally consistent within the document?

### Duplicate References
- [ ] Does the same link appear multiple times in the same file? (consider merging)
- [ ] Do links to the same target use a consistent URL? (avoid multiple different URLs for the same target)

### Version Consistency (within the document)
- [ ] Is a version referenced in one section the same as the version stated elsewhere in the document? (cross-section contradiction = defect)
- [ ] Does the architecture diagram version match the text description? (if applicable)
- [ ] Flag versions the document itself marks as provisional, legacy, or outdated (e.g. "deprecated", "old version"); do NOT verify against external sources or the codebase

### Internal Reference Completeness
- [ ] Do the referenced section/figure numbers exist and are correct within the document?
- [ ] Are the referenced interfaces/modules defined in the document?
- [ ] Are the referenced config files/environment variables documented?

## Scoring Guide

| Finding | Deduction |
|---|---|
| Link points to a nonexistent file | -2 each |
| Anchor doesn't exist in the target file | -1 each |
| Image file doesn't exist | -2 each |
| Placeholder link | -1 each |
| "Click here"-style link text | -1 each |
| Link text mismatches URL | -1 each |
| Link inside a heading | -0.5 each |
| Broken cross-reference | -2 each |
