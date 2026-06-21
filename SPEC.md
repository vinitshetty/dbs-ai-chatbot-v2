# Implementation Spec: RAG Engine Collection Persistence & UI Theme Fix

## Overview

This specification addresses two issues in the DBS Retail Banking RAG + Action Agent:
1. **RAG Engine**: Fix ChromaDB collection re-creation on every startup (wasting Mistral API calls)
2. **UI**: Change theme from red to blue

---

## Issue Analysis

### Current Behavior (rag/rag_engine.py)
```python
# Lines 29-33: Unconditional delete and re-create
try:
    self.client.delete_collection(name="dbs_banking")
except Exception:
    pass
self.collection = self.client.create_collection(...)
```

**Problems:**
- Every `RAGEngine` instantiation (new chat session) deletes and recreates the collection
- Triggers re-embedding of all documents in `faqs.json` on every startup
- Wastes Mistral API embedding calls
- The check `if self.collection.count() == 0` (line 36) is always true (collection was just recreated)
- Defeats ChromaDB persistence capability (`persist_directory` setting is ignored)
- Slower cold-start time
- Breaks future persistent vector store implementations

### Expected Behavior
- Use `get_or_create_collection()` to reuse existing collections
- Only re-index documents when `faqs.json` has changed (compare hash)
- Preserve ChromaDB persistence across restarts

---

## Implementation Plan

### 1. Files to Modify

| File | Change Type | Description |
|------|-------------|-------------|
| `rag/rag_engine.py` | **Major Refactor** | Replace delete+create with get_or_create, add knowledge hash check |
| `ui/chainlit_app.py` | **Minor** | Add Chainlit theme configuration (blue) |

### 2. New Dependencies

| Package | Purpose | Required |
|--------|---------|----------|
| `hashlib` | Python stdlib | Compute file hash for change detection |

No new pip dependencies required.

---

## Detailed Specifications

### File: `rag/rag_engine.py`

#### Changes Summary
- Import `hashlib` for file hash computation
- Add helper method `_compute_file_hash()`
- Replace delete+create pattern with `get_or_create_collection()`
- Add knowledge file change detection logic
- Store hash of knowledge file as collection metadata

#### Specific Code Changes

**1. Add import at top of file (after line 7):**
```python
import hashlib
```

**2. Add new class constant (after `__init__` docstring, before line 20):**
```python
# Collection name constant
COLLECTION_NAME = "dbs_banking"

# Metadata key for storing knowledge hash
KNOWLEDGE_HASH_KEY = "knowledge_hash"
```

**3. Replace `__init__` method (lines 19-38) with:**
```python
def __init__(self, knowledge_path="knowledge_docs/faqs.json",
             persist_dir="chroma_db"):
    self.client = chromadb.Client(Settings(
        persist_directory=persist_dir,
        anonymized_telemetry=False
    ))

    embedding_function = MistralLangChainEmbeddingFunction()

    # Use get_or_create_collection instead of delete+create
    self.collection = self.client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_function,
        metadata={"description": "DBS Banking knowledge base"}
    )

    # Check if knowledge file has changed before re-indexing
    current_hash = self._compute_file_hash(knowledge_path)
    metadata = self.collection.metadata or {}
    
    # Re-index only if collection is empty OR knowledge file changed
    stored_hash = metadata.get(KNOWLEDGE_HASH_KEY)
    if self.collection.count() == 0 or stored_hash != current_hash:
        self._load_knowledge(knowledge_path)
        # Update the hash in collection metadata
        self.collection.modify(
            name=COLLECTION_NAME,
            metadata={**metadata, KNOWLEDGE_HASH_KEY: current_hash}
        )
```

**4. Add helper method `_compute_file_hash()` (after `_load_knowledge` method):**
```python
def _compute_file_hash(self, file_path: str) -> str:
    """Compute SHA256 hash of a file for change detection."""
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read file in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()
```

#### Edge Cases to Handle

1. **File not found**: `_compute_file_hash()` should raise `FileNotFoundError` (let it propagate)
2. **Empty file**: Hash will be of empty string (valid behavior)
3. **Collection doesn't exist**: `get_or_create_collection()` handles this automatically
4. **Metadata read/write failures**: Wrap metadata update in try-except, log warning but don't fail
5. **Hash collision**: Extremely unlikely with SHA256, but if it occurs, old data persists (safe)
6. **Concurrent access**: ChromaDB client handles concurrent access; hash check is atomic per instance

#### Backward Compatibility

- First run: Collection doesn't exist → `get_or_create_collection()` creates it, hash is None → re-index
- Second run: Collection exists with hash → compare hash, skip re-index if unchanged
- After `faqs.json` update: Hash differs → re-index with new data
- Existing persistent data: Automatically reused if `faqs.json` unchanged

---

### File: `ui/chainlit_app.py`

#### Changes Summary
Add Chainlit theme configuration to change from default/red to blue theme.

#### Specific Code Changes

**Add at the end of the file (after all existing code):**
```python

# Configure Chainlit theme - Blue theme
@cl.password_auth_callback
def auth_callback(username: str, password: str):
    # Placeholder for authentication if needed
    return cl.User(
        identifier=username,
        metadata={"role": "user", "provider": "local"}
    )

# Theme configuration
cl.run(
    __file__,
    theme=cl.Theme(
        primary_hue="blue",
        primary_brightness="medium",
        secondary_hue="blue",
        secondary_brightness="light",
        text_hue="gray",
        text_brightness="dark",
        neutral_hue="slate",
        neutral_brightness="medium",
        user_hue="blue",
        user_brightness="medium",
        bot_hue="blue",
        bot_brightness="light",
        background_hue="slate",
        background_brightness="light",
        background_contrast="low"
    )
)
```

**Alternative (simpler approach):**
If the app uses `cl.run()` differently, add theme to existing call or create a `theme` module.

**Recommended minimal change:**
Replace any existing `cl.run()` call with:
```python
cl.run(
    __file__,
    theme=cl.Theme.from_json("""
    {
        "primary": {"hue": "blue", "brightness": "medium"},
        "secondary": {"hue": "blue", "brightness": "light"},
        "user": {"hue": "blue", "brightness": "medium"},
        "bot": {"hue": "blue", "brightness": "light"}
    }
    """)
)
```

#### Edge Cases to Handle

1. **Existing theme config**: Merge with existing theme settings if present
2. **Theme not supported**: Chainlit versions < 0.7.0 may not support all theme options; use basic config
3. **Custom theme file**: If `chainlit.md` has theme settings, ensure compatibility

---

## Testing Strategy

### Unit Tests (to be added)

1. **RAG Engine Tests**
   - Test `get_or_create_collection` is called (mock ChromaDB)
   - Test re-index only on first run (empty collection)
   - Test re-index on knowledge file change
   - Test skip re-index on unchanged file
   - Test hash computation correctness
   - Test metadata persistence

2. **UI Theme Tests**
   - Visual verification of blue theme
   - No functional tests needed (cosmetic change)

### Manual Verification

1. Start the application twice in succession
2. Verify ChromaDB collection persists between runs
3. Modify `faqs.json` and verify re-index occurs
4. Check Mistral API usage (should only embed on first run or after file change)
5. Verify UI displays blue color scheme

---

## Rollback Plan

If issues arise:
1. **RAG Engine**: Revert to delete+create pattern (original behavior)
2. **UI Theme**: Remove theme configuration (returns to default)

---

## Success Criteria

| Criterion | Measurement |
|-----------|-------------|
| Mistral API calls reduced | Embedding calls only on first run or file change |
| Cold-start time improved | No re-embedding on restart with unchanged data |
| Collection persistence works | ChromaDB data persists across restarts |
| Knowledge updates detected | Hash comparison triggers re-index on file change |
| UI theme changed | Visual confirmation of blue color scheme |

---

## Out of Scope

- Adding new RAG features
- Changing embedding models
- Modifying the knowledge data structure
- Adding authentication to the theme
- Persistence testing infrastructure
