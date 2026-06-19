# Changes - Fix ChromaDB Collection Re-creation Bug

**Issue:** #13 - RAG engine re-creates ChromaDB collection on every startup

## Summary of Changes

Fixed a bug where the `RAGEngine` class was unconditionally deleting and re-creating the ChromaDB collection on every instantiation, causing unnecessary Mistral API embedding calls and defeating persistence. The fix implements knowledge file hash tracking to only re-index documents when the knowledge source (`faqs.json`) has actually changed.

## Files Modified

### 1. `rag/rag_engine.py` (Modified)
**Why:** Core fix implementation
- Replaced `delete_collection()` + `create_collection()` with `get_or_create_collection()` to preserve existing collections
- Added `self.knowledge_path` attribute to track knowledge file location
- Added `_compute_knowledge_hash()` - Computes SHA256 hash of knowledge file contents
- Added `_get_stored_hash()` - Retrieves stored hash from collection metadata
- Added `_store_knowledge_hash()` - Stores current hash in collection metadata
- Added `_knowledge_changed()` - Compares current vs stored hash to detect changes
- Added `_reindex_knowledge()` - Clears collection and reloads documents when needed
- Updated `_load_knowledge()` - Added error handling for missing/corrupted JSON files
- Updated `__init__()` - Replaced unconditional re-creation with conditional re-indexing based on hash comparison

### 2. `SPEC.md` (Created)
**Why:** Implementation specification and design document
- Complete technical specification for the fix
- Detailed explanation of the problem and solution
- Edge case analysis and handling strategies
- Testing requirements and verification checklist
- Performance impact analysis

### 3. `tests/__init__.py` (Created)
**Why:** Test package initialization
- Empty module initialization file for the tests directory

### 4. `tests/test_rag_engine.py` (Created)
**Why:** Comprehensive test suite using TDD approach
- 16 unit and integration tests covering:
  - Knowledge hash computation (consistency, different content, missing files)
  - Knowledge change detection
  - Collection persistence across instantiations
  - Re-indexing behavior on file changes
  - Error handling for missing files, corrupted JSON, empty collections
  - Edge cases (first run, no stored hash, different file paths)

## Testing Notes

### Test Execution
```bash
# Run all tests
pytest tests/test_rag_engine.py -v

# Run with coverage
pytest tests/test_rag_engine.py --cov=rag --cov-report=term
```

### Test Results
- All 16 tests pass
- Tests cover hash computation, change detection, persistence, re-indexing, and error handling
- Mocking used for ChromaDB client to enable fast, isolated unit tests

### Manual Verification
1. **Collection Persistence:** Start application twice with same knowledge file → collection NOT recreated on second start
2. **Change Detection:** Modify `faqs.json` → collection IS recreated on next start
3. **First Run:** Delete `chroma_db` directory → collection created and indexed on startup
4. **Error Resilience:** Delete `faqs.json` → application starts with empty collection, no crash

### Performance Impact
- **Before:** ~N Mistral API embedding calls on every startup (N = number of documents)
- **After:** 0 API calls on subsequent starts (collection reused)
- **Expected improvement:** 90-95% reduction in API calls and startup time for typical usage
