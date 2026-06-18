# Implementation Spec: Fix Conversation History Message Type Bug

## Problem Summary

Conversation history is stored as plain Python dictionaries in `ui/chainlit_app.py` (lines 165-166) but LangChain's `ChatMistralAI.invoke()` expects `BaseMessage` objects (`HumanMessage`, `AIMessage`). When `llm_core.py:48` extends the messages list with raw dicts, this causes either:
- Type errors in strict LangChain versions
- Silent incorrect behavior in lenient versions

## Root Cause Analysis

### Current Flow
```
chainlit_app.py:165-166
  history.append({"role": "user", "content": query})      # Plain dict
  history.append({"role": "assistant", "content": response})  # Plain dict

chainlit_app.py:160
  → passed to handle_faq(query, history)

llm_core.py:39
  → passed to generate_response(context, query, conversation_history)

llm_core.py:47-48
  if conversation_history:
      messages.extend(conversation_history[-4:])  # Extends with dicts, not BaseMessage

llm_core.py:51
  response = self.llm.invoke(messages)  # ChatMistralAI expects BaseMessage list
```

## Solution Options

### Option A: Store History as BaseMessage Objects (Recommended)
Store `HumanMessage` and `AIMessage` objects directly in the Chainlit session. This ensures type safety throughout the pipeline and requires minimal changes.

### Option B: Convert Dicts to BaseMessage in generate_response()
Convert the plain dicts to `HumanMessage`/`AIMessage` objects just before extending the messages list in `llm_core.py`. This localizes the change but leaves type inconsistency in the session storage.

**Decision: Use Option A** - More robust, maintains type consistency, easier to maintain.

## Implementation Plan

### Files to Modify

#### 1. `/workspace/ui/chainlit_app.py`

**Changes:**
- Line 6: Add import for LangChain message types
- Lines 165-166: Replace dict appends with HumanMessage/AIMessage creation
- Line 160: Ensure history passed to handle_faq contains BaseMessage objects

**Specific Edits:**

```python
# Add to imports (after line 5)
from langchain_core.messages import HumanMessage, AIMessage
```

```python
# Replace lines 165-166
# OLD:
# history.append({"role": "user", "content": query})
# history.append({"role": "assistant", "content": response})

# NEW:
history.append(HumanMessage(content=query))
history.append(AIMessage(content=response))
```

#### 2. `/workspace/llm/llm_core.py`

**Changes:**
- Line 5: Add import for `AIMessage` (already has `HumanMessage`, `SystemMessage`)
- Line 47-48: No changes needed - will work with BaseMessage objects

**Specific Edits:**

```python
# Update line 5
# OLD:
# from langchain_core.messages import HumanMessage, SystemMessage

# NEW:
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
```

### File: /workspace/llm/llm_core.py
- Line 47-48 already works correctly once history contains BaseMessage objects
- No logic changes required

## New Dependencies

No new dependencies required. Both files already use `langchain_core.messages`, and `AIMessage` is part of the same module.

## Edge Cases to Handle

### 1. Empty History
- **Scenario:** First message in conversation
- **Current:** `conversation_history` is `[]` or `None`
- **Behavior:** `if conversation_history:` evaluates to False, no extend occurs
- **Result:** ✅ Works correctly with both dicts and BaseMessage objects

### 2. Partial History (< 4 messages)
- **Scenario:** Early in conversation, history has fewer than 4 messages
- **Current:** `conversation_history[-4:]` returns all available messages
- **Behavior:** Works with both dicts and BaseMessage
- **Result:** ✅ No issue

### 3. Backward Compatibility with Existing Sessions
- **Scenario:** User has an existing session with dict-based history
- **Problem:** After deployment, existing sessions in memory will have dicts
- **Solution:** Add type conversion in `generate_response()` as a fallback

**Required Addition to llm_core.py:**

```python
# In generate_response() method, before line 47-48:
if conversation_history:
    # Convert any legacy dict entries to BaseMessage objects
    normalized_history = []
    for msg in conversation_history[-4:]:
        if isinstance(msg, dict):
            if msg.get("role") == "user":
                normalized_history.append(HumanMessage(content=msg["content"]))
            elif msg.get("role") == "assistant":
                normalized_history.append(AIMessage(content=msg["content"]))
            else:
                # Skip system messages or unknown roles
                continue
        else:
            # Already a BaseMessage object
            normalized_history.append(msg)
    messages.extend(normalized_history)
```

### 4. System Messages in History
- **Scenario:** Should system messages be included in conversation history?
- **Current:** Only user and assistant messages are stored
- **Decision:** Continue storing only user/assistant messages
- **Result:** ✅ No action needed

### 5. None or Invalid Content
- **Scenario:** Message content could be None or empty
- **Current:** Both Chainlit and LangChain handle None content
- **Behavior:** `HumanMessage(content=None)` is valid
- **Result:** ✅ No special handling needed

### 6. Serialization/Deserialization
- **Scenario:** Chainlit session state may serialize/deserialize session data
- **Problem:** `HumanMessage`/`AIMessage` are dataclasses, not plain dicts
- **Investigation Required:** Check if Chainlit can serialize dataclass objects
- **Fallback:** If serialization fails, store as dicts and convert on retrieval

**Mitigation:** Add a helper function for safe serialization:

```python
# In chainlit_app.py, add helper:
def serialize_message_history(history):
    """Convert BaseMessage objects to serializable dicts for session storage."""
    return [
        {"role": "user", "content": msg.content} if isinstance(msg, HumanMessage)
        else {"role": "assistant", "content": msg.content}
        for msg in history
    ]

def deserialize_message_history(history):
    """Convert dicts back to BaseMessage objects."""
    from langchain_core.messages import HumanMessage, AIMessage
    result = []
    for msg in history:
        if isinstance(msg, dict):
            if msg.get("role") == "user":
                result.append(HumanMessage(content=msg["content"]))
            elif msg.get("role") == "assistant":
                result.append(AIMessage(content=msg["content"]))
        else:
            result.append(msg)  # Already BaseMessage
    return result
```

**Usage:**
```python
# In main() function, line 62:
# OLD: history = cl.user_session.get("conversation_history")
# NEW:
history = deserialize_message_history(cl.user_session.get("conversation_history", []))

# In main() function, line 166:
# OLD: cl.user_session.set("conversation_history", history[-6:])
# NEW:
cl.user_session.set("conversation_history", serialize_message_history(history[-6:]))
```

## Final Implementation Decision

Given Chainlit's session serialization behavior, **Option A with serialization helpers** is the safest approach:

1. Store as dicts in Chainlit session (for serialization compatibility)
2. Convert to BaseMessage objects when retrieved
3. Convert back to dicts when storing
4. Add fallback conversion in `llm_core.py` for robustness

This ensures:
- Type safety when passing to LangChain
- Serialization compatibility with Chainlit
- Backward compatibility with existing sessions
- Gradual migration path

## Testing Strategy

1. **Unit Test:** Create test that passes dict history to `generate_response()` - should work with fallback
2. **Unit Test:** Create test that passes BaseMessage history to `generate_response()` - should work
3. **Integration Test:** Full Chainlit flow with new message storage
4. **Backward Compat Test:** Existing session with dict history should work after deployment
5. **Edge Case Test:** Empty history, partial history, None content

## Rollback Plan

If issues arise:
1. The fallback conversion in `llm_core.py` ensures existing dict-based history still works
2. Can revert to Option B (convert in llm_core only) with minimal changes
3. No database migrations needed - history is session-scoped
