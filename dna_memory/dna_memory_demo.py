#!/usr/bin/env python3
"""
DNA Memory Demo - Showcasing Human-like AI Memory

This demo demonstrates:
1. Recording memories with different types and importance
2. Recalling memories with weight reinforcement
3. Automatic pattern extraction from similar memories
4. Creating knowledge graph links
5. Forgetting mechanism over time
"""

import json
import os
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

# Memory configuration
MEMORY_DIR = Path.home() / ".dna_memory_demo"
SHORT_TERM_FILE = MEMORY_DIR / "short_term.json"
LONG_TERM_FILE = MEMORY_DIR / "long_term.json"
GRAPH_FILE = MEMORY_DIR / "graph.json"

MEMORY_TYPES = ["fact", "preference", "skill", "error", "pattern", "insight"]


def ensure_dirs():
    """Ensure memory directory exists"""
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)


def load_json(path: Path) -> Dict:
    """Load JSON file"""
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"memories": []}


def save_json(path: Path, data: Dict):
    """Save JSON file"""
    ensure_dirs()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def gen_id() -> str:
    """Generate unique ID"""
    return f"mem_{uuid.uuid4().hex[:8]}"


def now_iso() -> str:
    """Get current ISO timestamp"""
    return datetime.now().isoformat()


def remember(content: str, mem_type: str = "fact", importance: float = 0.5, source: str = "demo") -> str:
    """Record a new memory"""
    memory = {
        "id": gen_id(),
        "type": mem_type,
        "content": content,
        "source": source,
        "importance": min(max(importance, 0), 1),
        "created_at": now_iso(),
        "last_accessed": now_iso(),
        "access_count": 0,
        "tags": [],
        "links": []
    }
    
    data = load_json(SHORT_TERM_FILE)
    data["memories"].append(memory)
    save_json(SHORT_TERM_FILE, data)
    
    print(f"✅ Recorded: [{memory['id']}] {content[:50]}...")
    return memory["id"]


def recall(query: str, limit: int = 5) -> List[Dict]:
    """Recall relevant memories"""
    results = []
    query_lower = query.lower()
    
    for file in [SHORT_TERM_FILE, LONG_TERM_FILE]:
        data = load_json(file)
        for mem in data.get("memories", []):
            content = mem.get("content", "").lower()
            
            if query_lower in content:
                # Update access info (reinforcement)
                mem["last_accessed"] = now_iso()
                mem["access_count"] = mem.get("access_count", 0) + 1
                mem["importance"] = min(mem.get("importance", 0.5) + 0.1, 1.0)
                results.append((mem, file))
        save_json(file, data)
    
    # Sort by importance
    results.sort(key=lambda x: x[0].get("importance", 0), reverse=True)
    return results[:limit]


def reflect() -> int:
    """Extract patterns from similar memories"""
    data = load_json(SHORT_TERM_FILE)
    memories = data.get("memories", [])
    
    if len(memories) < 3:
        print("📝 Not enough memories for pattern extraction")
        return 0
    
    # Group by type
    by_type = {}
    for mem in memories:
        t = mem.get("type", "fact")
        by_type.setdefault(t, []).append(mem)
    
    patterns = []
    promoted = []
    
    for t, mems in by_type.items():
        if len(mems) >= 3:
            # Extract common theme
            contents = [m["content"] for m in mems]
            common_words = set(contents[0].split())
            for c in contents[1:]:
                common_words &= set(c.split())
            
            theme = " ".join(list(common_words)[:5]) if common_words else t
            
            pattern = {
                "id": gen_id(),
                "type": "pattern",
                "content": f"[{t} pattern] {theme}: Extracted from {len(mems)} memories",
                "sources": [m["id"] for m in mems],
                "created_at": now_iso(),
                "last_accessed": now_iso(),
                "access_count": 0,
                "importance": 0.8,
                "tags": [t, "pattern"],
                "links": []
            }
            patterns.append(pattern)
            
            # Promote high-weight memories to long-term
            for m in mems:
                if m.get("importance", 0) >= 0.7:
                    promoted.append(m)
    
    # Save patterns
    if patterns:
        lt = load_json(LONG_TERM_FILE)
        lt["memories"].extend(patterns)
        
        # Add promoted memories
        for m in promoted:
            if m["id"] not in [x["id"] for x in lt["memories"]]:
                lt["memories"].append(m)
        
        save_json(LONG_TERM_FILE, lt)
        print(f"💡 Extracted {len(patterns)} patterns, promoted {len(promoted)} to long-term")
        return len(patterns)
    else:
        print("📝 No new patterns found")
        return 0


def link_memories(id1: str, id2: str, relation: str = "related"):
    """Create link between memories"""
    graph = load_json(GRAPH_FILE)
    if "links" not in graph:
        graph["links"] = []
    
    graph["links"].append({
        "from": id1,
        "to": id2,
        "relation": relation,
        "created_at": now_iso()
    })
    save_json(GRAPH_FILE, graph)
    print(f"🔗 Linked: {id1} --[{relation}]--> {id2}")


def decay():
    """Simulate forgetting over time"""
    data = load_json(SHORT_TERM_FILE)
    now = datetime.now()
    kept, forgotten = [], []
    
    decay_days = 7
    decay_rate = 0.1
    threshold = 0.2
    
    for mem in data.get("memories", []):
        try:
            last = datetime.fromisoformat(mem.get("last_accessed", mem.get("created_at", now_iso())))
            days = (now - last).days
            
            if days >= decay_days:
                mem["importance"] = mem.get("importance", 0.5) - decay_rate
                if mem["importance"] < threshold:
                    forgotten.append(mem)
                    continue
            kept.append(mem)
        except:
            kept.append(mem)
    
    data["memories"] = kept
    save_json(SHORT_TERM_FILE, data)
    print(f"🧹 Forgot {len(forgotten)} memories, kept {len(kept)}")


def stats():
    """Show statistics"""
    st = load_json(SHORT_TERM_FILE)
    lt = load_json(LONG_TERM_FILE)
    graph = load_json(GRAPH_FILE)
    
    st_count = len(st.get("memories", []))
    lt_count = len(lt.get("memories", []))
    link_count = len(graph.get("links", []))
    
    print("\n📊 DNA Memory Statistics")
    print(f"   Short-term: {st_count} memories")
    print(f"   Long-term: {lt_count} memories")
    print(f"   Links: {link_count} connections")


def demo():
    """Run the complete demo"""
    print("=" * 60)
    print("DNA Memory Demo - Human-like AI Memory System")
    print("=" * 60)
    
    # Clean up previous demo data
    if MEMORY_DIR.exists():
        import shutil
        shutil.rmtree(MEMORY_DIR)
    
    print("\n1️⃣ Recording memories with different types and importance...")
    print("-" * 60)
    
    id1 = remember("User prefers concise responses", "preference", 0.9)
    id2 = remember("Python is the primary language", "fact", 0.7)
    id3 = remember("Always validate user input", "skill", 0.8)
    id4 = remember("GitHub API rate limit is 5000/hour", "fact", 0.6)
    id5 = remember("Never expose API keys in code", "error", 0.95)
    
    print("\n2️⃣ Recalling memories (with weight reinforcement)...")
    print("-" * 60)
    
    results = recall("Python")
    for mem, source in results:
        source_tag = "Short-term" if "short" in str(source) else "Long-term"
        print(f"[{mem['id']}] ({mem['type']}) [{source_tag}] {mem['content']} [weight: {mem['importance']:.2f}]")
    
    print("\n3️⃣ Recording similar memories for pattern extraction...")
    print("-" * 60)
    
    remember("GitHub push timed out", "error", 0.5)
    remember("GitHub clone timed out", "error", 0.5)
    remember("GitHub fetch timed out", "error", 0.5)
    
    print("\n4️⃣ Extracting patterns from similar memories...")
    print("-" * 60)
    
    reflect()
    
    print("\n5️⃣ Creating knowledge graph links...")
    print("-" * 60)
    
    link_memories(id3, id5, "reinforces")
    link_memories(id2, id4, "related_to")
    
    print("\n6️⃣ Simulating forgetting (decay)...")
    print("-" * 60)
    
    # Manually set old timestamp for demo
    data = load_json(SHORT_TERM_FILE)
    if data["memories"]:
        old_date = (datetime.now() - timedelta(days=10)).isoformat()
        data["memories"][0]["last_accessed"] = old_date
        data["memories"][0]["importance"] = 0.3
        save_json(SHORT_TERM_FILE, data)
    
    decay()
    
    print("\n7️⃣ Final statistics...")
    print("-" * 60)
    
    stats()
    
    print("\n" + "=" * 60)
    print("Demo complete! Check ~/.dna_memory_demo/ for data files.")
    print("=" * 60)


if __name__ == "__main__":
    demo()
