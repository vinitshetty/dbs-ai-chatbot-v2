# CHANGES: Add Error Handling for Mistral API Failures in LLMCore

**Issue:** #18
**Commit:** 27cfad0022c1001cdc3a8c95364235ff2db64ef0
**Date:** Thu Jun 18 09:07:00 2026 +0000

## Summary of Changes

This change adds comprehensive error handling for Mistral API failures in the LLMCore class. The implementation includes retry logic with exponential backoff, user-friendly fallback responses, and proper logging via AuditLogger.

## Files Modified

### 1. `llm/llm_core.py`
**Changes:**
- Added new constructor parameters: `max_retries` (default: 3), `timeout` (default: 30s), `retry_delay` (default: 1.0s), `logger` (Optional AuditLogger instance)
- Added imports: `time`, `datetime`, `Optional`, `Any` from typing
- Added `_invoke_with_retry()` helper method with:
  - Exponential backoff for retryable errors (RateLimitError, TimeoutError, ConnectionError, etc.)
  - Logging of all API errors via AuditLogger
  - Classification of retryable vs non-retryable errors
  - Returns `None` on failure after exhausting retries
- Updated `generate_response()`:
  - Uses `_invoke_with_retry()` wrapper
  - Returns user-friendly fallback message on API failure
  - Logs fallback responses
- Updated `classify_intent()`:
  - Uses `_invoke_with_retry()` wrapper
  - Returns `{"intent": "unclear", "confidence": 0.0}` on API failure
  - Replaced bare `except:` with specific `(ValueError, IndexError)`
  - Logs parse errors and API failures
- Updated `extract_action_params()`:
  - Uses `_invoke_with_retry()` wrapper
  - Returns `{}` on API failure
  - Replaced bare `except:` with specific `(ValueError, IndexError)` in transfer parsing
  - Logs parse errors and API failures
- Updated `plan_action()`:
  - Uses `_invoke_with_retry()` wrapper
  - Returns `{"action": None, "needs_auth": False}` on API failure
  - Replaced bare `except:` with specific `(ValueError, IndexError)`
  - Logs parse errors and API failures

**Why:** Addresses crashes from network issues, rate limits, invalid API keys, and unexpected responses. Provides graceful degradation with user-friendly messages instead of raw stack traces.

### 2. `ui/chainlit_app.py`
**Changes:**
- Modified `LLMCore()` initialization to pass `logger=logger`

**Why:** Ensures LLMCore has access to AuditLogger for error logging in the Chainlit UI context.

### 3. `ui/intent_router.py`
**Changes:**
- Added logic in `__init__` to ensure `llm_core.logger` is set if not already present:
  ```python
  if not llm_core.logger:
      llm_core.logger = logger
  ```

**Why:** Provides fallback logger assignment for LLMCore instances created without a logger parameter.

### 4. `llm/test_llm_core.py` (NEW FILE)
**Changes:**
- Created comprehensive test suite with 45 tests covering:
  - Constructor validation (MISTRAL_API_KEY required)
  - Retry logic with exponential backoff
  - Retryable vs non-retryable error classification
  - Fallback responses for all methods
  - Parse error handling (ValueError, IndexError)
  - Logger integration
  - Timeout and retry configuration

**Why:** Validates all error handling paths and edge cases.

### 5. `SPEC.md` (NEW FILE)
**Changes:**
- Complete specification document detailing:
  - Problem statement and current issues
  - Error classification (retryable vs non-retryable)
  - Edge cases to handle
  - Implementation details for each method
  - Dependencies (none new required)

**Why:** Provides design documentation and rationale for the implementation.

## Testing Notes

### Test Coverage
- 45 unit tests in `test_llm_core.py`
- Tests cover all error scenarios:
  - Network failures with retry
  - Rate limiting (429) with backoff
  - Invalid API key (401/403) - non-retryable
  - API timeout scenarios
  - Unexpected response formats
  - Empty/None responses
  - Partial failures (valid API response but parse error)
  - KeyboardInterrupt/SystemExit propagation
  - Memory errors

### Running Tests
```bash
# Run all LLMCore tests
python -m pytest llm/test_llm_core.py -v

# Run with coverage
python -m pytest llm/test_llm_core.py --cov=llm --cov-report=term
```

### Expected Results
- All 45 tests pass
- No crashes on API failures
- User-friendly fallback messages returned
- All errors logged via AuditLogger with context
- Retries work with exponential backoff (1s, 2s, 4s)
- Non-retryable errors fail fast without retry

### Manual Testing
- Test with invalid MISTRAL_API_KEY: should return fallback, not crash
- Test with network disconnect: should retry 3 times then fallback
- Test with malformed LLM responses: should return defaults, not crash
- Verify logs in `audit/` directory contain error details
