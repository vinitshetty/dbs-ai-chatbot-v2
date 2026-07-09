# Transaction History Feature - Implementation Specification

## Overview

This document specifies the implementation of transaction history viewing capability for the DBS Banking RAG + Action Agent. Users can currently check balances, lock/unlock cards, and transfer funds, but there is no way to view transaction history. This feature adds that core banking functionality.

---

## 1. Files to Modify

### 1.1 `/workspace/core_banking/banking_actions.py`
**Status:** MODIFY (existing file)

#### Changes:

1. **Add TRANSACTIONS storage** (after line 137, end of class):
```python
# Transaction history storage
TRANSACTIONS = {
    "user123": [
        {"id": "TXN100001", "type": "debit", "amount": 50.00, "description": "Grocery Store", "date": "2025-06-15", "balance": 15380.50},
        {"id": "TXN100002", "type": "credit", "amount": 3000.00, "description": "Salary", "date": "2025-06-01", "balance": 15430.50},
        {"id": "TXN100003", "type": "debit", "amount": 1250.00, "description": "Card Payment", "date": "2025-06-10", "balance": 14180.50},
        {"id": "TXN100004", "type": "debit", "amount": 200.00, "description": "ATM Withdrawal", "date": "2025-06-12", "balance": 13980.50},
        {"id": "TXN100005", "type": "credit", "amount": 500.00, "description": "Refund", "date": "2025-06-14", "balance": 14480.50},
    ]
}
```

2. **Add `get_transactions()` method** to `BankingActions` class:
```python
@classmethod
def get_transactions(
    cls,
    user_id: str,
    transaction_type: str = None,
    start_date: str = None,
    end_date: str = None,
    min_amount: float = None,
    max_amount: float = None,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Retrieve transaction history with optional filtering.
    
    Args:
        user_id: User identifier
        transaction_type: Filter by 'credit' or 'debit' (optional)
        start_date: Filter by start date (YYYY-MM-DD format, optional)
        end_date: Filter by end date (YYYY-MM-DD format, optional)
        min_amount: Minimum transaction amount (optional)
        max_amount: Maximum transaction amount (optional)
        limit: Maximum number of transactions to return (default: 10)
    
    Returns:
        Dict with 'success' boolean, 'transactions' list, and optional 'error' message
    """
    # Validate user
    if user_id not in cls.ACCOUNTS:
        return {"success": False, "error": "User not found"}
    
    # Get user transactions
    user_transactions = cls.TRANSACTIONS.get(user_id, [])
    
    if not user_transactions:
        return {"success": True, "transactions": [], "message": "No transactions found"}
    
    # Apply filters
    filtered = []
    for txn in user_transactions:
        # Type filter
        if transaction_type and txn.get("type") != transaction_type:
            continue
        
        # Date range filter
        txn_date = txn.get("date", "")
        if start_date and txn_date < start_date:
            continue
        if end_date and txn_date > end_date:
            continue
        
        # Amount range filter
        txn_amount = txn.get("amount", 0)
        if min_amount is not None and txn_amount < min_amount:
            continue
        if max_amount is not None and txn_amount > max_amount:
            continue
        
        filtered.append(txn)
    
    # Sort by date descending (newest first)
    filtered.sort(key=lambda x: x.get("date", ""), reverse=True)
    
    # Apply limit
    result_transactions = filtered[:limit]
    
    return {
        "success": True,
        "transactions": result_transactions,
        "total_count": len(filtered),
        "returned_count": len(result_transactions)
    }
```

3. **Add helper method for date parsing** (optional but recommended):
```python
@staticmethod
def _parse_date(date_str: str) -> str:
    """
    Parse and normalize date strings.
    Handles formats like 'last week', 'yesterday', '2025-06-15', etc.
    """
    import datetime
    from dateutil.relativedelta import relativedelta
    
    date_str = date_str.strip().lower()
    today = datetime.date.today()
    
    # Handle relative dates
    if date_str == "today":
        return today.strftime("%Y-%m-%d")
    elif date_str == "yesterday":
        return (today - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    elif "last week" in date_str:
        return (today - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
    elif "this week" in date_str:
        return (today - datetime.timedelta(days=today.weekday())).strftime("%Y-%m-%d")
    elif "last month" in date_str:
        return (today - relativedelta(months=1)).strftime("%Y-%m-%d")
    
    # Validate YYYY-MM-DD format
    try:
        datetime.datetime.strptime(date_str, "%Y-%m-%d")
        return date_str
    except ValueError:
        # Try other common formats
        for fmt in ["%Y/%m/%d", "%d-%m-%Y", "%m/%d/%Y"]:
            try:
                dt = datetime.datetime.strptime(date_str, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
        return None
```

---

### 1.2 `/workspace/llm/llm_core.py`
**Status:** MODIFY (existing file)

#### Changes:

1. **Update `plan_action()` method** (around line 103):
   - Add `"transaction_history"` as a recognized action
   - Modify the prompt to include transaction_history in the action list

```python
# Change the prompt in plan_action method:
prompt = """Given the query and intent, plan the action:

Query: {query}
Intent: {intent}

Determine:
1. Action name (lock_card, unlock_card, check_balance, transfer_funds, transaction_history)
2. Required parameters
3. Needs authentication? (yes/no)

Format: action_name|needs_auth
Example: lock_card|yes"""
```

2. **Add `extract_action_params()` case for transaction_history** (around line 65):
```python
# In extract_action_params method, add to prompts dict:
prompts = {
    "lock_card": "Extract the last 4 digits of the card from: {query}\nRespond with ONLY the 4 digits or 'unknown'",
    "transfer": "Extract from_account, to_account, and amount from: {query}\nFormat: from|to|amount or 'unknown'",
    "transaction_history": "Extract filters from: {query}\nPossible filters: type (credit/debit), date range, amount range, limit\nFormat: type|start_date|end_date|min_amount|max_amount|limit or 'none'",
}

# Add handling for transaction_history:
elif action_type == "transaction_history":
    if result != "unknown" and result != "none":
        parts = result.split("|")
        # Parse up to 6 parts
        params = {}
        if len(parts) >= 1 and parts[0].strip():
            params["type"] = parts[0].strip()
        if len(parts) >= 2 and parts[1].strip():
            params["start_date"] = parts[1].strip()
        if len(parts) >= 3 and parts[2].strip():
            params["end_date"] = parts[2].strip()
        if len(parts) >= 4 and parts[3].strip():
            try:
                params["min_amount"] = float(parts[3].strip())
            except ValueError:
                pass
        if len(parts) >= 5 and parts[4].strip():
            try:
                params["max_amount"] = float(parts[4].strip())
            except ValueError:
                pass
        if len(parts) >= 6 and parts[5].strip():
            try:
                params["limit"] = int(parts[5].strip())
            except ValueError:
                pass
        return params
```

---

### 1.3 `/workspace/ui/intent_router.py`
**Status:** MODIFY (existing file)

#### Changes:

1. **Add transaction-related keywords to READ_KEYWORDS** (line 12):
```python
# Change from:
READ_KEYWORDS = ["check", "balance", "show", "view", "status"]

# To:
READ_KEYWORDS = ["check", "balance", "show", "view", "status", "transactions", "history", "recent", "statement", "transaction"]
```

---

### 1.4 `/workspace/ui/chainlit_app.py`
**Status:** MODIFY (existing file)

#### Changes:

1. **Update `handle_action()` function** (around line 207):
   - Add handler branch for `"transaction_history"` action

```python
# Add after the transfer_funds handling, before the fallback return:
elif action_name == "transaction_history":
    # Extract parameters
    params = llm_core.extract_action_params(query, "transaction_history")
    
    # Get filter parameters
    txn_type = params.get("type")
    start_date = params.get("start_date")
    end_date = params.get("end_date")
    min_amount = params.get("min_amount")
    max_amount = params.get("max_amount")
    limit = params.get("limit", 10)
    
    # Parse relative dates if present
    if start_date:
        start_date = BankingActions._parse_date(start_date)
    if end_date:
        end_date = BankingActions._parse_date(end_date)
    
    # Execute action
    start_exec = time.time()
    result = BankingActions.get_transactions(
        user_id,
        transaction_type=txn_type,
        start_date=start_date,
        end_date=end_date,
        min_amount=min_amount,
        max_amount=max_amount,
        limit=limit
    )
    exec_time = (time.time() - start_exec) * 1000
    
    logger.log_action("transaction_history", params, result)
    langwatch_tracker.track_action_execution(
        "transaction_history",
        params,
        result,
        execution_time_ms=exec_time
    )
    
    if result["success"]:
        transactions = result.get("transactions", [])
        if not transactions:
            return "No transactions found matching your criteria."
        
        # Format as table
        response = "📋 **Transaction History**\n\n"
        response += f"Showing {result.get('returned_count', len(transactions))} of {result.get('total_count', len(transactions))} transactions\n\n"
        
        response += "| Date | Type | Description | Amount | Balance |\n"
        response += "|------|------|-------------|--------|---------|\n"
        
        for txn in transactions:
            txn_date = txn.get("date", "N/A")
            txn_type = txn.get("type", "N/A").upper()
            description = txn.get("description", "N/A")
            amount = f"${txn.get('amount', 0):.2f}"
            balance = f"${txn.get('balance', 0):.2f}"
            
            response += f"| {txn_date} | {txn_type} | {description} | {amount} | {balance} |\n"
        
        return response
    else:
        return f"❌ {result.get('error') or result.get('message')}"
```

2. **Update welcome message** (around line 34):
   - Add transaction history to the list of capabilities

```python
# Change from:
"I can help you with:\n"
"- Branch hours and fees\n"
"- Checking your balance\n"
"- Locking/unlocking cards\n"
"- Transferring funds\n"

# To:
"I can help you with:\n"
"- Branch hours and fees\n"
"- Checking your balance\n"
"- Viewing transaction history\n"
"- Locking/unlocking cards\n"
"- Transferring funds\n"
```

3. **Update fallback message** (around line 203):
```python
# Change from:
"You can ask about:\n"
"- Branch hours, fees, policies\n"
"- Account balances\n"
"- Card management"

# To:
"You can ask about:\n"
"- Branch hours, fees, policies\n"
"- Account balances\n"
"- Transaction history\n"
"- Card management"
```

---

## 2. New Dependencies

### 2.1 Required Python Package
Add to `/workspace/requirements.txt`:
```
python-dateutil>=2.8.0
```

### 2.2 New Imports Required

#### In `banking_actions.py`:
```python
from typing import Dict, Any, List
import datetime
from dateutil.relativedelta import relativedelta
```

#### In `llm_core.py`:
No new imports needed.

#### In `chainlit_app.py`:
No new imports needed (already has `time` and `BankingActions`).

#### In `intent_router.py`:
No new imports needed.

---

## 3. Edge Cases to Handle

### 3.1 Transaction History Edge Cases

| Case | Handling Strategy |
|------|-------------------|
| User has no transactions | Return success=True with empty transactions list and message |
| Invalid user_id | Return success=False with "User not found" error |
| Invalid date format | Use `_parse_date()` helper; if unparseable, ignore date filter |
| Date range where start > end | Return empty list (no transactions match) |
| Negative amount range | Treat as invalid, ignore amount filter |
| Limit > total transactions | Return all available transactions |
| Limit = 0 or negative | Default to 10 |
| Non-numeric amount filters | Catch ValueError, ignore those filters |
| Unknown transaction type | Ignore type filter (return all types) |

### 3.2 Intent Classification Edge Cases

| Case | Handling Strategy |
|------|-------------------|
| "Show my transactions" | Classify as READ intent (matches "show") |
| "transaction history" | Classify as READ intent (matches new keywords) |
| "recent activity" | Classify as READ intent (matches "recent") |
| "bank statement" | Classify as READ intent (matches "statement") |
| "view transactions from last week" | Classify as READ, plan as transaction_history |

### 3.3 Parameter Extraction Edge Cases

| Case | Handling Strategy |
|------|-------------------|
| No filters specified | Return all transactions with default limit |
| "last week" date | Parse to date 7 days ago |
| "yesterday" | Parse to previous day |
| "this month" | Parse to first day of current month |
| Partial date (e.g., "June") | Return None, ignore filter |
| Amount without currency symbol | Parse numeric value directly |
| Amount with currency symbol | Strip symbol before parsing |

---

## 4. Testing Scenarios

### 4.1 Basic Functionality Tests

```python
# Test 1: Get all transactions (default)
result = BankingActions.get_transactions("user123")
assert result["success"] == True
assert len(result["transactions"]) <= 10  # Default limit

# Test 2: Filter by type
result = BankingActions.get_transactions("user123", transaction_type="credit")
assert all(txn["type"] == "credit" for txn in result["transactions"])

# Test 3: Filter by date range
result = BankingActions.get_transactions(
    "user123",
    start_date="2025-06-10",
    end_date="2025-06-15"
)
assert all("2025-06-10" <= txn["date"] <= "2025-06-15" 
           for txn in result["transactions"])

# Test 4: Filter by amount range
result = BankingActions.get_transactions(
    "user123",
    min_amount=100.00,
    max_amount=1000.00
)
assert all(100.00 <= txn["amount"] <= 1000.00 
           for txn in result["transactions"])

# Test 5: Limit
result = BankingActions.get_transactions("user123", limit=3)
assert len(result["transactions"]) <= 3

# Test 6: Invalid user
result = BankingActions.get_transactions("invalid_user")
assert result["success"] == False
```

### 4.2 Integration Tests

```python
# Test via Chainlit flow
# Query: "Show my recent transactions"
# Expected: Formatted table of transactions

# Test via Chainlit flow  
# Query: "Show transactions from last week"
# Expected: Filtered table showing only last week's transactions

# Test via Chainlit flow
# Query: "Show credit transactions over $100"
# Expected: Filtered table showing credit transactions > $100
```

---

## 5. LangWatch Integration

All transaction history actions must be tracked in LangWatch:

1. **Trace Context**: Each `transaction_history` action execution tracked via `track_action_execution()`
2. **Parameters**: All filter parameters (type, dates, amounts, limit) logged in metadata
3. **Result**: Success/failure status and transaction count logged
4. **Timing**: Execution time measured and logged

Example tracking call:
```python
langwatch_tracker.track_action_execution(
    "transaction_history",
    {"type": "credit", "start_date": "2025-06-01", "limit": 5},
    {"success": True, "returned_count": 3, "total_count": 5},
    execution_time_ms=45.2
)
```

---

## 6. Acceptance Criteria Checklist

- [ ] `TRANSACTIONS` dictionary added to `BankingActions` with sample data
- [ ] `get_transactions()` method implemented with filtering support
- [ ] `_parse_date()` helper method for relative date handling
- [ ] `"transaction_history"` added to `plan_action()` prompt
- [ ] Parameter extraction for transaction_history in `extract_action_params()`
- [ ] Transaction keywords added to `READ_KEYWORDS`
- [ ] Handler branch for transaction_history in `handle_action()`
- [ ] Transaction history formatted as markdown table
- [ ] Welcome message updated to include transaction history
- [ ] Fallback message updated to include transaction history
- [ ] All actions logged to AuditLogger
- [ ] All actions tracked in LangWatch
- [ ] Edge cases handled (empty results, invalid users, date parsing)
- [ ] "Show my recent transactions" returns formatted list
- [ ] "Show transactions from last week" filters by date
- [ ] python-dateutil dependency added to requirements.txt

---

## 7. File Summary

| File | Action | Lines Changed (approx) |
|------|--------|----------------------|
| `/workspace/core_banking/banking_actions.py` | MODIFY | +120 |
| `/workspace/llm/llm_core.py` | MODIFY | +30 |
| `/workspace/ui/intent_router.py` | MODIFY | +2 |
| `/workspace/ui/chainlit_app.py` | MODIFY | +50 |
| `/workspace/requirements.txt` | MODIFY | +1 |
| **Total** | | **~203** |

---

## 8. Rollback Plan

If implementation needs to be rolled back:
1. Remove `TRANSACTIONS` dictionary from `banking_actions.py`
2. Remove `get_transactions()` method from `BankingActions`
3. Remove `_parse_date()` method from `BankingActions`
4. Revert `plan_action()` prompt in `llm_core.py`
5. Remove transaction_history case from `extract_action_params()`
6. Revert `READ_KEYWORDS` in `intent_router.py`
7. Remove transaction_history handler from `handle_action()`
8. Revert welcome and fallback messages in `chainlit_app.py`
9. Remove python-dateutil from requirements.txt
