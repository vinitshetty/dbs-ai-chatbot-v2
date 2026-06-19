# Implementation Spec: Fix ChromaDB Collection Re-creation Bug

## Overview

### Problem
The `RAGEngine.__init__()` method in `rag/rag_engine.py` unconditionally deletes and re-creates the `dbs_banking` ChromaDB collection on every instantiation. This causes:
- **Unnecessary Mistral API embedding calls** on every new chat session
- **Defeated persistence** - the `if self.collection.count() == 0` check (line 33) is always true
- **Slower cold-start times** due to redundant document re-indexing
- **Broken persistent vector store** setup for future enhancements

### Expected Behavior
- Use `get_or_create_collection()` to retrieve existing collection
- Only re-index documents when the knowledge source (`faqs.json`) has changed
- Persist the collection across application restarts

---

## File Modifications

### 1. `rag/rag_engine.py`

#### New Imports
```python
import hashlib
from pathlib import Path
```

#### Changes to `__init__` Method

**Current (lines 18-32):**
```python
def __init__(self, knowledge_path="knowledge_docs/faqs.json",
             persist_dir="chroma_db"):
    self.client = chromadb.Client(Settings(
        persist_directory=persist_dir,
        anonymized_telemetry=False
    ))

    embedding_function = MistralLangChainEmbeddingFunction()

    # Delete the collection if it exists to ensure the new embedding function is used
    try:
        self.client.delete_collection(name="dbs_banking")
    except Exception:
        pass  # Collection doesn't exist, so no need to delete

    self.collection = self.client.create_collection(
        name="dbs_banking",
        embedding_function=embedding_function,
        metadata={"description": "DBS Banking knowledge base"}
    )

    if self.collection.count() == 0:
        self._load_knowledge(knowledge_path)
```

**New Implementation:**
```python
def __init__(self, knowledge_path="knowledge_docs/faqs.json",
             persist_dir="chroma_db"):
    self.knowledge_path = knowledge_path
    self.client = chromadb.Client(Settings(
        persist_directory=persist_dir,
        anonymized_telemetry=False
    ))

    embedding_function = MistralLangChainEmbeddingFunction()

    # Use get_or_create_collection to preserve existing collection
    self.collection = self.client.get_or_create_collection(
        name="dbs_banking",
        embedding_function=embedding_function,
        metadata={"description": "DBS Banking knowledge base"}
    )

    # Only re-index if knowledge source has changed
    if self._knowledge_changed():
        self._reindex_knowledge()
```

#### New Helper Methods

**Add after `_load_knowledge` method:**

```python
def _compute_knowledge_hash(self) -> str:
    """Compute SHA256 hash of knowledge file contents."""
    path = Path(self.knowledge_path)
    if not path.exists():
        return ""
    
    with open(path, 'rb') as f:
        content = f.read()
    
    return hashlib.sha256(content).hexdigest()


def _get_stored_hash(self) -> str:
    """Retrieve stored knowledge hash from collection metadata."""
    try:
        collection_metadata = self.collection.get(
            include=["metadatas"]
        )
        # Check if we have a stored hash in the collection's own metadata
        if "knowledge_hash" in self.collection.metadata:
            return self.collection.metadata["knowledge_hash"]
    except Exception:
        pass
    return ""


def _store_knowledge_hash(self, knowledge_hash: str):
    """Store knowledge hash in collection metadata."""
    try:
        # Update collection metadata with new hash
        self.collection.modify(
            name="dbs_banking",
            metadata={
                **self.collection.metadata,
                "knowledge_hash": knowledge_hash
            }
        )
    except Exception:
        # Fallback: log but don't fail
        pass


def _knowledge_changed(self) -> bool:
    """Check if knowledge source has changed since last indexing."""
    current_hash = self._compute_knowledge_hash()
    stored_hash = self._get_stored_hash()
    
    # If no stored hash, this is first run - need to index
    if not stored_hash:
        return True
    
    return current_hash != stored_hash


def _reindex_knowledge(self):
    """Clear existing collection and re-index all documents."""
    # Clear existing documents
    try:
        self.collection.delete(where={})  # Delete all documents
    except Exception:
        pass  # Collection may be empty, that's fine
    
    # Load fresh knowledge
    self._load_knowledge(self.knowledge_path)
    
    # Store new hash
    new_hash = self._compute_knowledge_hash()
    self._store_knowledge_hash(new_hash)
```

#### Changes to `_load_knowledge` Method

**Remove the conditional check (line 33):**
```python
# REMOVE this line:
if self.collection.count() == 0:
    self._load_knowledge(knowledge_path)

# Replace with direct call from _reindex_knowledge
```

**Update `_load_knowledge` to accept `knowledge_path` parameter:**
```python
def _load_knowledge(self, knowledge_path: str):
```
(Already has this parameter, no change needed to signature)

---

## Edge Cases & Error Handling

### 1. Missing Knowledge File
- **Scenario:** `faqs.json` doesn't exist at specified path
- **Handling:** `_compute_knowledge_hash()` returns empty string, `_knowledge_changed()` returns True, attempt to load fails gracefully
- **Action:** Should log warning but not crash application

### 2. Corrupted Knowledge File
- **Scenario:** `faqs.json` is malformed JSON
- **Handling:** `_load_knowledge()` raises JSONDecodeError
- **Action:** Wrap in try/except in `_reindex_knowledge()`, log error, continue with empty collection

### 3. ChromaDB Metadata Limits
- **Scenario:** Some ChromaDB versions have metadata size limits
- **Handling:** Store hash in a separate small document instead of collection metadata
- **Fallback:** Use a `.knowledge_hash` file in persist_dir

### 4. Race Conditions
- **Scenario:** Multiple RAGEngine instances initializing simultaneously
- **Handling:** ChromaDB's internal locking handles collection access
- **Action:** No additional handling needed; ChromaDB is thread-safe

### 5. Embedding Function Changes
- **Scenario:** Mistral embedding model changes, making old embeddings incompatible
- **Handling:** Not addressed in this fix - requires separate migration strategy
- **Note:** This is a known limitation; future work should add embedding version to hash

### 6. First Run (No Persistent Directory)
- **Scenario:** First application run, `chroma_db` directory doesn't exist
- **Handling:** ChromaDB auto-creates directory on first client instantiation
- **Action:** No special handling needed

### 7. Read-Only Filesystem
- **Scenario:** Application running in read-only environment
- **Handling:** `get_or_create_collection` will fail, `_store_knowledge_hash` will fail gracefully
- **Action:** Log warnings, continue with in-memory collection

---

## New Dependencies

### Standard Library (None - Already Available)
- `hashlib` - For SHA256 hashing (built-in)
- `pathlib.Path` - Already imported, used for path handling

### External Dependencies
- **No new external dependencies required**
- Existing `chromadb` dependency already provides `get_or_create_collection()`

---

## Testing Requirements

### Unit Tests Needed
1. **Test `_compute_knowledge_hash()`** - Verify hash computation is consistent
2. **Test `_knowledge_changed()`** - Verify detection of file changes
3. **Test collection persistence** - Verify collection survives across instantiations
4. **Test re-indexing on change** - Verify documents re-loaded when file changes
5. **Test no re-indexing on no change** - Verify documents NOT re-loaded when file unchanged

### Integration Tests Needed
1. **Multiple chat sessions** - Verify second session doesn't re-embed
2. **File change during runtime** - Verify change is detected on next init
3. **Corrupted JSON** - Verify graceful handling
4. **Missing file** - Verify graceful handling

---

## Migration Path

### For Existing Deployments
1. **No action required** - On next startup, existing collection will be detected
2. **Hash mismatch on first run** - `_knowledge_changed()` returns True (no stored hash), triggers re-index
3. **Subsequent starts** - Hash matches, no re-indexing occurs

### Rollback Plan
If issues arise:
1. Revert to previous code
2. Clear `chroma_db` directory to force fresh start
3. No data migration needed (embeddings regenerated on demand)

---

## Future Enhancements (Out of Scope)

1. **Embedding version tracking** - Store embedding model version alongside hash
2. **Incremental updates** - Detect and index only changed documents
3. **Hot-reloading** - Watch file system for changes and re-index automatically
4. **Collection backup** - Backup old collection before re-indexing
5. **Multi-tenant support** - Different collections per user/tenant

---

## Performance Impact

### Before Fix
- **Cold start:** ~N API calls (where N = number of documents)
- **Warm start (new session):** ~N API calls (collection recreated)
- **Embedding cache:** Never used

### After Fix
- **First start:** ~N API calls (initial indexing)
- **Subsequent starts:** 0 API calls (collection reused)
- **After knowledge update:** ~N API calls (re-indexing)
- **Embedding cache:** Effectively persistent via ChromaDB

### Expected Improvement
- **API cost reduction:** ~90-95% for typical usage (1 initial load + N sessions)
- **Start time reduction:** ~80-90% (skip embedding generation)

---

## Files Summary

| File | Action | Lines Changed |
|------|--------|---------------|
| `rag/rag_engine.py` | Modify | ~40 lines added, ~10 lines removed |
| `SPEC.md` | Create | This document |

---

## Verification Checklist

- [ ] `get_or_create_collection()` used instead of delete+create
- [ ] Knowledge file hash computed and stored
- [ ] Hash comparison determines if re-indexing needed
- [ ] Re-indexing clears old documents before loading new ones
- [ ] Hash stored in collection metadata
- [ ] All edge cases handled with graceful degradation
- [ ] No new external dependencies added
- [ ] Existing tests still pass (if any)
- [ ] New behavior verified with multiple chat sessions
- [ ] File change detection verified
