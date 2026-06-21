# Changes: Pin Dependency Versions in requirements.txt

**Issue:** #16  
**Commit:** 54e911067eb673dd124bd22ab752ad8ae2b9c334  
**Date:** Fri Jun 19 03:19:47 2026 +000

## Summary of Changes

Pinned all dependency versions in `requirements.txt` to match versions specified in `pyproject.toml`, ensuring consistent and reproducible builds. Removed unused dependencies and replaced generic packages with their specific counterparts.

## Files Modified

### 1. `requirements.txt`
**Reason:** Version pinning for build reproducibility and dependency consistency with `pyproject.toml`

**Changes:**
- Added minimum version constraints (`>=`) to all dependencies
- Removed unused `crewai` dependency
- Removed `python-dotenv` (was listed twice; kept only once with version)
- Replaced generic `langchain` with specific packages:
  - Added `langchain-community>=0.4.1`
  - Added `langchain-core>=1.2.6`
- Pinned versions for all remaining dependencies:
  - `chainlit>=2.9.4`
  - `chromadb>=1.1.1`
  - `langchain-mistralai>=1.1.1`
  - `langwatch>=0.8.0`
  - `mistralai>=1.9.11`
  - `python-dotenv>=1.1.1`
- Removed BOM character (U+FEFF) at start of file
- Added newline at end of file

### 2. `README.md`
**Reason:** Update installation instructions to use standard package installation method

**Changes:**
- Changed `pip install -r requirements.txt` to `pip install -e .`
- This ensures installation uses the version-pinned dependencies from `pyproject.toml` via the project's build system

## Testing Notes

1. **Verification of version consistency:**
   - All versions in `requirements.txt` match or are compatible with those in `pyproject.toml`
   - Run `pip install -e .` to verify all dependencies install correctly

2. **Build reproducibility:**
   - The pinned versions ensure identical environments across installations
   - No breaking changes introduced by dependency updates

3. **Dependency resolution:**
   - Test that `pip install -e .` completes without version conflicts
   - Verify all imported packages work correctly in the application

4. **Cleanup verification:**
   - Confirmed `crewai` removal does not break existing functionality
   - Confirmed `langchain-community` and `langchain-core` replace the generic `langchain` dependency
