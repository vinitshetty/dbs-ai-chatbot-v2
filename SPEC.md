# SPEC: Error Handling for Mistral API Failures in LLMCore

## Overview

This specification defines the implementation of robust error handling for Mistral API failures in `LLMCore` (`llm/llm_core.py`). The current implementation has no error handling for API calls, causing application crashes on network issues, rate limits, invalid keys, or unexpected responses.

## Problem Statement

### Current Issues
1. **No timeout configuration** — `ChatMistralAI` client has no timeout, causing indefinite hangs
2. **No retry logic** — Rate limit (429) and transient failures cause immediate crash
3. **No API error handling** — Invalid keys, network errors crash the application
4. **Bare `except:` clauses** — Lines 78, 137 silently swallow all exceptions including `KeyboardInterrupt`, `SystemExit`
5. **No logging of API failures** — No visibility into why calls failed
6. **No user-friendly fallbacks** — Users see raw stack traces instead of helpful messages

### Affected Methods in `llm/llm_core.py`
| Method | Line | Issue |
|--------|------|-------|
| `generate_response()` | 44 | `self.llm.invoke(messages)` has no try/except |
| `classify_intent()` | 72-78 | Bare `except:` catches all exceptions |
| `extract_action_params()` | 131-137 | Bare `except:` catches all exceptions |
| `plan_action()` | 165-171 | Bare `except:` catches all exceptions |

## Files to Modify

### 1. `llm/llm_core.py` (PRIMARY)

**Changes:**

#### A. Constructor (`__init__`) — Add timeout and retry configuration
```python
# ADD imports at top of file:
import time
import logging
from typing import Optional, Dict, Any
from langchain_core.exceptions import LangChainError

# MODIFY __init__:
def __init__(self, model_name: str = "mistral-small-latest", 
             max_retries: int = 3, 
             timeout: int = 30,
             retry_delay: float = 1.0,
             logger: Optional[Any] = None):
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        raise ValueError("MISTRAL_API_KEY not found in environment")
    
    self.max_retries = max_retries
    self.timeout = timeout
    self.retry_delay = retry_delay
    self.logger = logger  # Accept AuditLogger instance
    
    self.llm = ChatMistralAI(
        model=model_name,
        temperature=0.3,
        mistral_api_key=api_key,
        timeout=timeout,  # Add timeout parameter
        max_retries=max_retries  # Add retry parameter
    )
```

#### B. New Helper Method — `_invoke_with_retry()`

Add a private helper method to centralize API call logic with retry and error handling:

```python
def _invoke_with_retry(self, messages: list, operation_name: str = "llm_invoke") -> Any:
    """
    Invoke LLM with retry logic and error handling.
    
    Args:
        messages: List of messages to send to LLM
        operation_name: Name of operation for logging (e.g., 'generate_response')
    
    Returns:
        LLM response object or None on failure
    
    Raises:
        LLMError: After all retries exhausted (logged, not raised to caller)
    """
    last_exception = None
    
    for attempt in range(self.max_retries + 1):
        try:
            response = self.llm.invoke(messages)
            return response
            
        except (ValueError, IndexError) as e:
            # Parse errors - re-raise for method-specific handling
            raise
            
        except Exception as e:
            last_exception = e
            
            # Log the error
            if self.logger:
                self.logger.log_event("llm_api_error", {
                    "operation": operation_name,
                    "attempt": attempt + 1,
                    "max_retries": self.max_retries,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "timestamp": datetime.now().isoformat()
                })
            
            # Retry on transient errors
            if attempt < self.max_retries:
                error_type = type(e).__name__
                
                # Check if this is a retryable error
                retryable_errors = [
                    'RateLimitError', 'TimeoutError', 'ConnectionError',
                    'Timeout', 'ConnectTimeout', 'ReadTimeout'
                ]
                
                if any(retryable in error_type for retryable in retryable_errors):
                    # Exponential backoff
                    delay = self.retry_delay * (2 ** attempt)
                    if self.logger:
                        self.logger.log_event("llm_retry", {
                            "operation": operation_name,
                            "attempt": attempt + 1,
                            "delay_seconds": delay,
                            "error_type": error_type
                        })
                    time.sleep(delay)
                    continue
                
                # Non-retryable error (e.g., invalid API key, auth error)
                # Log and fall through to return None
                break
            
            break  # No more retries
    
    # All retries exhausted or non-retryable error
    if self.logger:
        self.logger.log_event("llm_api_failure", {
            "operation": operation_name,
            "error_type": type(last_exception).__name__ if last_exception else "Unknown",
            "error_message": str(last_exception) if last_exception else "No exception recorded",
            "retries_exhausted": True
        })
    
    return None
```

#### C. Add datetime import
```python
from datetime import datetime
```

#### D. Update `generate_response()` — Add error handling

```python
def generate_response(self, context: str, query: str, 
                     conversation_history: list = None) -> str:
    """Generate response using context from RAG"""
    
    system_prompt = ...  # Existing prompt
    
    messages = [
        SystemMessage(content=system_prompt.format(context=context))
    ]
    
    if conversation_history:
        messages.extend(conversation_history[-4:])
    
    messages.append(HumanMessage(content=query))
    
    # Use retry wrapper
    response = self._invoke_with_retry(messages, "generate_response")
    
    if response is None:
        # Return user-friendly fallback
        fallback = ("I apologize, but I'm having trouble connecting to the AI service. "
                   "Please try again in a moment.")
        if self.logger:
            self.logger.log_event("fallback_response", {
                "operation": "generate_response",
                "reason": "api_failure"
            })
        return fallback
    
    return response.content
```

#### E. Update `classify_intent()` — Replace bare except

```python
def classify_intent(self, query: str) -> dict:
    """Classify user intent"""
    
    prompt = ...  # Existing prompt
    
    message = HumanMessage(content=prompt.format(query=query))
    response = self._invoke_with_retry([message], "classify_intent")
    
    if response is None:
        # API failure - return fallback with low confidence
        if self.logger:
            self.logger.log_event("intent_classification_failed", {
                "reason": "api_failure",
                "query": query[:100]  # Truncate for logging
            })
        return {"intent": "unclear", "confidence": 0.0}
    
    try:
        intent, confidence = response.content.strip().split("|")
        return {
            "intent": intent.strip(),
            "confidence": float(confidence.strip())
        }
    except (ValueError, IndexError) as e:
        # Parse error - log and return fallback
        if self.logger:
            self.logger.log_event("intent_parse_error", {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "query": query[:100],
                "raw_response": response.content[:200] if response else None
            })
        return {"intent": "unclear", "confidence": 0.0}
```

#### F. Update `extract_action_params()` — Replace bare except

```python
def extract_action_params(self, query: str, action_type: str) -> dict:
    """Extract parameters for actions"""
    
    prompts = { ... }  # Existing prompts
    
    if action_type not in prompts:
        return {}
    
    message = HumanMessage(content=prompts[action_type].format(query=query))
    response = self._invoke_with_retry([message], "extract_action_params")
    
    if response is None:
        if self.logger:
            self.logger.log_event("action_param_extraction_failed", {
                "action_type": action_type,
                "reason": "api_failure",
                "query": query[:100]
            })
        return {}
    
    result = response.content.strip()
    
    if action_type == "lock_card":
        return {"last4": result if result != "unknown" else None}
    
    elif action_type == "transfer":
        if result != "unknown":
            try:
                parts = result.split("|")
                if len(parts) == 3:
                    return {
                        "from_account": parts[0].strip(),
                        "to_account": parts[1].strip(),
                        "amount": float(parts[2].strip())
                    }
            except (ValueError, IndexError) as e:
                if self.logger:
                    self.logger.log_event("transfer_param_parse_error", {
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                        "raw_result": result,
                        "query": query[:100]
                    })
        return {}
    
    return {}
```

#### G. Update `plan_action()` — Replace bare except

```python
def plan_action(self, query: str, intent: str) -> dict:
    """Plan action steps (simple CrewAI-like planning)"""
    
    prompt = ...  # Existing prompt
    
    message = HumanMessage(content=prompt.format(query=query, intent=intent))
    response = self._invoke_with_retry([message], "plan_action")
    
    if response is None:
        if self.logger:
            self.logger.log_event("action_planning_failed", {
                "reason": "api_failure",
                "query": query[:100],
                "intent": intent
            })
        return {"action": None, "needs_auth": False}
    
    try:
        action, needs_auth = response.content.strip().split("|")
        return {
            "action": action.strip(),
            "needs_auth": needs_auth.strip().lower() == "yes"
        }
    except (ValueError, IndexError) as e:
        if self.logger:
            self.logger.log_event("action_plan_parse_error", {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "query": query[:100],
                "intent": intent,
                "raw_response": response.content[:200]
            })
        return {"action": None, "needs_auth": False}
```

### 2. `ui/chainlit_app.py` (SECONDARY)

Pass the logger to LLMCore during initialization:

```python
# In start() function, MODIFY:
llm_core = LLMCore()

# TO:
llm_core = LLMCore(logger=logger)
```

### 3. `ui/intent_router.py` (SECONDARY)

Pass the logger through to LLMCore:

```python
# In __init__, MODIFY:
def __init__(self, llm_core: LLMCore, logger: AuditLogger):
    self.llm = llm_core
    self.logger = logger
    # Ensure llm_core has the logger
    if not llm_core.logger:
        llm_core.logger = logger
```

## New Dependencies

### Required (Already Installed)
- `langchain-mistralai>=1.1.1` — Already in `pyproject.toml` and `requirements.txt`
- `python-dotenv>=1.1.1` — Already in `pyproject.toml` and `requirements.txt`

### No New Dependencies Required
All necessary imports (`time`, `datetime`, `logging`) are Python standard library.

## Edge Cases to Handle

### 1. Network Failures
- **Scenario**: Network connection drops mid-request
- **Handling**: Retry with exponential backoff (1s, 2s, 4s) up to `max_retries`
- **Fallback**: Return user-friendly message after retries exhausted

### 2. Rate Limiting (HTTP 429)
- **Scenario**: Mistral API returns 429 Too Many Requests
- **Handling**: Detect via exception type, retry with backoff
- **Fallback**: Return "Service temporarily busy, please try again shortly"

### 3. Invalid API Key (HTTP 401/403)
- **Scenario**: `MISTRAL_API_KEY` is invalid or expired
- **Handling**: Detect as non-retryable error, log with error type
- **Fallback**: Return "Authentication error with AI service. Please check API configuration."

### 4. API Timeout
- **Scenario**: API takes longer than `timeout` seconds
- **Handling**: Raise timeout exception, retry
- **Fallback**: Return "AI service is taking too long. Please try again."

### 5. Unexpected Response Format
- **Scenario**: LLM returns response that doesn't match expected format (e.g., no `|` in classify_intent)
- **Handling**: Catch `ValueError` and `IndexError` specifically
- **Fallback**: Return default values (intent="unclear", confidence=0.0)

### 6. Empty or None Response
- **Scenario**: API returns empty string or None
- **Handling**: Check for None/empty, return fallback
- **Fallback**: Return default/fallback values

### 7. Partial Failure
- **Scenario**: `extract_action_params` gets valid response but parse fails
- **Handling**: Return empty dict `{}` rather than crashing
- **Fallback**: Empty dict signals to caller that params couldn't be extracted

### 8. KeyboardInterrupt/SystemExit
- **Scenario**: User presses Ctrl+C or system exit
- **Handling**: Let these propagate (not caught by `except Exception`)
- **Fallback**: N/A — application should exit cleanly

### 9. Memory Errors
- **Scenario**: Out of memory during processing
- **Handling**: Not retryable, log and return fallback
- **Fallback**: User-friendly error message

### 10. ChromaDB/Embedding Errors (in RAGEngine)
- **Note**: Out of scope for this fix, but `MistralLangChainEmbeddingFunction` in `rag/rag_engine.py` has similar issues
- **Future Work**: Separate spec needed for RAG error handling

## Error Classification

### Retryable Errors (Will Retry)
| Error Type | Condition | Retry Strategy |
|------------|-----------|----------------|
| `RateLimitError` | HTTP 429 | Exponential backoff |
| `TimeoutError` / `Timeout` | Request timeout | Immediate retry |
| `ConnectionError` | Network connection failed | Immediate retry |
| `ConnectTimeout` / `ReadTimeout` | Connection/read timeout | Immediate retry |

### Non-Retryable Errors (No Retry, Log & Fallback)
| Error Type | Condition | Action |
|------------|-----------|--------|
| `AuthenticationError` | Invalid API key | Log, fallback |
| `PermissionError` | API access denied | Log, fallback |
| `ValueError` | Invalid input to API | Log, fallback |
| `KeyError` | Missing expected key | Log, fallback |
| `MemoryError` | Out of memory | Log, fallback |

### Parse Errors (Specific Handling)
| Error Type | Condition | Action |
|------------|-----------|--------|
| `ValueError` | Response doesn't split on `|` | Return default values |
| `IndexError` | Not enough parts after split | Return default values |

## Logging Strategy

All errors logged via `AuditLogger` with structured data:

```json
{
  "timestamp": "2024-01-15T10:30:00.123456",
  "event_type": "llm_api_error",
  "data": {
    "operation": "generate_response",
    "attempt": 1,
    "max_retries": 3,
    "error_type": "ConnectionError",
    "error_message": "Connection refused",
    "timestamp": "2024-01-15T10:30:00.123456"
  }
}
```

## Fallback Responses

### By Method
| Method | Fallback Behavior |
|--------|-------------------|
| `generate_response()` | Return user-friendly error message string |
| `classify_intent()` | Return `{"intent": "unclear", "confidence": 0.0}` |
| `extract_action_params()` | Return `{}` (empty dict) |
| `plan_action()` | Return `{"action": None, "needs_auth": False}` |

### User-Friendly Messages
```
# For generate_response API failure:
"I apologize, but I'm having trouble connecting to the AI service. Please try again in a moment."

# For generate_response after all retries:
"I apologize, but the AI service is currently unavailable. Please try again later."

# For parse errors (hidden from user):
# Return default values, no user-facing message (handled by caller)
```

## Configuration Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_retries` | int | 3 | Max retry attempts for API calls |
| `timeout` | int | 30 | Request timeout in seconds |
| `retry_delay` | float | 1.0 | Base delay between retries (exponential backoff) |
| `logger` | AuditLogger | None | Optional logger instance for error logging |

## Testing Strategy

### Unit Tests to Add
1. Test `generate_response()` with mocked API failure
2. Test `classify_intent()` with mocked parse error
3. Test retry logic with exponential backoff
4. Test timeout handling
5. Test invalid API key scenario
6. Test rate limit scenario
7. Verify fallback responses are user-friendly
8. Verify all errors are logged

### Integration Tests
1. Test with invalid `MISTRAL_API_KEY`
2. Test with network connectivity disabled
3. Test with slow API (mocked delay > timeout)
4. Test concurrent requests hitting rate limit

## Backward Compatibility

- Default parameters maintain existing behavior
- No breaking changes to method signatures
- Existing callers continue to work without modification
- Only `ui/chainlit_app.py` and `ui/intent_router.py` need minor updates to pass logger

## Rollout Plan

1. **Phase 1**: Implement in development branch
2. **Phase 2**: Add comprehensive tests
3. **Phase 3**: Test with invalid API key
4. **Phase 4**: Test with network issues
5. **Phase 5**: Merge to main after verification

## Success Criteria

- [ ] No crashes on API failures
- [ ] All API errors logged via AuditLogger
- [ ] User-friendly messages displayed to users
- [ ] Retry logic works for transient errors
- [ ] Non-retryable errors fail gracefully
- [ ] Parse errors handled with specific exception types
- [ ] No bare `except:` clauses remain
- [ ] All existing tests pass
- [ ] New tests added for error scenarios
