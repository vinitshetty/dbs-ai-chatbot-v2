# Implementation Spec: Fix transfer_funds Action Handler

## Task
Fix: transfer_funds action not wired up in the UI handler

## Bug Description
The `handle_action()` function in `ui/chainlit_app.py` handles `check_balance`, `lock_card`, and `unlock_card`, but there is no branch for `transfer_funds` even though:
- `BankingActions.transfer_funds()` is fully implemented in `core_banking/banking_actions.py`
- `LLMCore.extract_action_params()` supports the `"transfer"` action type in `llm/llm_core.py`
- The `plan_action()` LLM prompt lists `transfer_funds` as a valid action

Users asking to transfer money currently receive: *"Action 'transfer_funds' is not yet implemented in this prototype."*

---

## 1. Files to Modify

| File | Change Type | Description |
|------|-------------|-------------|
| `ui/chainlit_app.py` | Modify | Add `transfer_funds` branch in `handle_action()` function |

**No new files need to be created.**

---

## 2. Specific Changes

### File: `ui/chainlit_app.py`

**Location:** `handle_action()` function, after the `lock_card`/`unlock_card` branch (around line 240-260)

**Add a new elif branch:**

```python
elif action_name == "transfer_funds":
    # Get authentication if needed
    if needs_auth and not cl.user_session.get("authenticated"):
        is_auth = await request_dummy_auth()
        langwatch_tracker.add_custom_metric("auth_required", True)
        langwatch_tracker.add_custom_metric("auth_completed", is_auth)
        
        if not is_auth:
            return "❌ Authentication required to proceed with this action."
    
    # Extract transfer parameters
    params = llm_core.extract_action_params(query, "transfer")
    from_account = params.get("from_account")
    to_account = params.get("to_account")
    amount = params.get("amount")
    
    # Validate required parameters
    if not all([from_account, to_account, amount]):
        missing = []
        if not from_account:
            missing.append("source account")
        if not to_account:
            missing.append("destination account")
        if not amount:
            missing.append("amount")
        return f"❌ Missing required information: {', '.join(missing)}"
    
    # Execute action
    start_exec = time.time()
    result = BankingActions.transfer_funds(user_id, from_account, to_account, amount)
    exec_time = (time.time() - start_exec) * 1000
    
    # Log and track execution
    logger.log_action(action_name, {"from_account": from_account, "to_account": to_account, "amount": amount}, result)
    langwatch_tracker.track_action_execution(
        action_name,
        {"from_account": from_account, "to_account": to_account, "amount": amount},
        result,
        execution_time_ms=exec_time
    )
    
    # Return formatted response
    if result["success"]:
        return (f"✅ {result['message']}\n"
                f"Transaction ID: **{result['transaction_id']}**\n"
                f"New balance: **${result['new_balance']:.2f}**")
    else:
        return f"❌ {result.get('error') or result.get('message')}"
```

**Place this branch before the final fallback return statement:**
```python
return f"Action '{action_name}' is not yet implemented in this prototype."
```

---

## 3. Dependencies and Imports

### No New Dependencies Required
- All required modules (`time`, `cl`, `llm_core`, `BankingActions`, `logger`, `langwatch_tracker`) are already imported in the file
- No new imports are needed

---

## 4. Edge Cases to Handle

### 4.1 Authentication
- **Case:** User not authenticated, `needs_auth=True`
- **Handling:** Prompt for authentication via `request_dummy_auth()`. If denied, return error message.
- **Same pattern as:** `lock_card`/`unlock_card` actions

### 4.2 Missing Parameters
- **Case:** LLM fails to extract `from_account`, `to_account`, or `amount`
- **Handling:** Check all three parameters exist. Return specific error listing missing fields.
- **Example error:** "❌ Missing required information: source account, amount"

### 4.3 Parameter Validation (handled by BankingActions)
The `BankingActions.transfer_funds()` method already validates:
- All required parameters present (`from_account`, `to_account`, `amount`)
- `amount` > 0 and `amount` <= 50000
- Source account exists in user's accounts
- Source account has sufficient balance

**Error responses from BankingActions:**
- `"Invalid transfer parameters"` - missing/invalid params
- `"Source account not found"` - from_account doesn't exist
- `"Insufficient funds"` - balance too low

### 4.4 Empty or Malformed LLM Extraction
- **Case:** `extract_action_params()` returns empty dict or partial data
- **Handling:** The explicit parameter check (`if not all([from_account, to_account, amount])`) catches this before calling `BankingActions`

### 4.5 Type Safety
- **Case:** `amount` is extracted as string instead of float
- **Note:** `LLMCore.extract_action_params()` already converts amount to float: `"amount": float(parts[2].strip())`
- **Fallback:** If conversion fails, `extract_action_params()` returns empty dict, caught by parameter validation

### 4.6 Action Name Mismatch
- **Case:** `plan_action()` returns action name as `"transfer"` instead of `"transfer_funds"`
- **Handling:** The spec in `llm/llm_core.py` prompt lists `transfer_funds` as the action name. If LLM returns `"transfer"`, the branch won't match. However, the existing pattern in `handle_action()` uses `action_name` from `plan_action()` which should return consistent names.

---

## 5. Implementation Notes

### Pattern Consistency
The implementation follows the exact same pattern as existing actions:
1. Check authentication if `needs_auth=True`
2. Extract parameters using `llm_core.extract_action_params()`
3. Validate parameters exist
4. Execute via `BankingActions.method()`
5. Log action with `logger.log_action()`
6. Track with `langwatch_tracker.track_action_execution()`
7. Return formatted success/error message

### Error Message Format
- Success: ✅ prefix, multi-line with transaction details
- Error: ❌ prefix with specific error message
- Matches existing pattern for `lock_card`/`unlock_card`

### Metrics Tracking
- Authentication metrics: `auth_required`, `auth_completed`
- Execution metrics: tracked via `langwatch_tracker.track_action_execution()` with timing

### Testing Considerations
After implementation, test with:
- "Transfer $100 from savings to checking"
- "Send money from my savings account to checking for 50 dollars"
- Missing parameters: "Transfer money"
- Unauthenticated user attempting transfer
- Invalid accounts: "Transfer $100 from savings to investment"
- Insufficient funds scenario
