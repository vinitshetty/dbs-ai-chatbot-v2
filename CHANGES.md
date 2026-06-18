# Transaction History Viewing Capability - CHANGES

## Summary
This change implements **Issue #20**: Add transaction history viewing capability to the DBS Banking Assistant. Users can now query their transaction history with optional filtering by date range, transaction type, and amount.

## Changes Made

### Core Banking Layer (`core_banking/banking_actions.py`)
- **Added `TRANSACTIONS` class variable**: In-memory storage with sample transaction data for user123 (6 transactions: 4 debits, 2 credits)
- **Added `_is_valid_date()` helper method**: Validates date strings in YYYY-MM-DD format
- **Added `get_transactions()` class method**: Retrieves transaction history with filtering support:
  - `start_date` / `end_date`: Filter by date range (inclusive)
  - `transaction_type`: Filter by 'credit' or 'debit'
  - `min_amount` / `max_amount`: Filter by transaction amount
  - `limit`: Maximum number of results (default: 10)
  - Returns sorted results (newest first) with pagination metadata
- **Updated `transfer_funds()`**: Now logs both debit (source) and credit (destination) transactions to `TRANSACTIONS` storage

### LLM Integration Layer (`llm/llm_core.py`)
- **Updated `classify_intent()` prompt**: Added "view statements" to read intent description
- **Added `get_transactions` to `extract_action_params()`**: Parses query for filter parameters (start_date, end_date, type, min_amount, max_amount, limit)
- **Updated `plan_action()` prompt**: Added `get_transactions` to available action list

### UI Layer

#### `ui/intent_router.py`
- **Updated `READ_KEYWORDS`**: Added "transaction", "transactions", "history", "recent", "statement" to support rule-based classification

#### `ui/chainlit_app.py`
- **Updated welcome message**: Added "Viewing your transaction history" to capabilities list
- **Added `get_transactions` handler**: 
  - Extracts filter parameters from user query via LLM
  - Calls `BankingActions.get_transactions()` with filters
  - Formats results as Markdown table with:
    - Date, Type, Description, Amount (color-coded: red for debit, green for credit), Balance
    - Shows count and total_available metadata
  - Logs action execution and tracks in LangWatch
  - Handles errors gracefully with user-friendly messages

### Test Suite

#### New Files
- **`tests/__init__.py`**: Tests directory initialization
- **`tests/test_transaction_history.py`** (277 lines): 29 test cases covering:
  - Basic retrieval with no filters
  - Limit parameter
  - Type filtering (credit/debit)
  - Date range filtering
  - Amount filtering (min/max)
  - Combined filters
  - Invalid parameters (dates, amounts)
  - Edge cases (empty results, non-existent user)
  - Date validation

- **`tests/test_transaction_intent_router.py`** (79 lines): Tests for intent classification:
  - Transaction history queries routed to "read" intent
  - Keyword matching for "transaction", "history", "recent"

- **`tests/test_transaction_llm_extraction.py`** (42 lines): Tests for parameter extraction:
  - LLM correctly extracts date range, type, amount filters
  - Handles missing/partial parameters

- **`tests/test_transaction_ui_handler.py`** (113 lines): Tests for UI handler:
  - Table formatting
  - Result display with count metadata
  - Error handling
  - Empty results handling

## Files Modified

| File | Lines Changed | Purpose |
|------|---------------|---------|
| `core_banking/banking_actions.py` | +144 | Core transaction storage, retrieval logic, and transfer logging |
| `llm/llm_core.py` | +36 -4 | LLM intent classification and parameter extraction for transactions |
| `ui/intent_router.py` | +2 -1 | Added transaction keywords to READ_KEYWORDS |
| `ui/chainlit_app.py` | +72 | UI handler for displaying transaction history |
| `tests/__init__.py` | +1 | Tests directory initialization |
| `tests/test_transaction_history.py` | +277 | Unit tests for transaction retrieval and filtering |
| `tests/test_transaction_intent_router.py` | +79 | Tests for intent routing |
| `tests/test_transaction_llm_extraction.py` | +42 | Tests for LLM parameter extraction |
| `tests/test_transaction_ui_handler.py` | +113 | Tests for UI handler |

**Total**: 9 files changed, 762 insertions(+), 4 deletions(-)

## Acceptance Criteria Met

✅ **"Show my recent transactions"** returns formatted transaction list  
✅ **"Show transactions from last week"** filters by date range  
✅ **Transactions are logged** when `transfer_funds()` is called  
✅ **Transactions are tracked** in LangWatch via `langwatch_tracker.track_action_execution()`  

## Testing Notes

### Running Tests
```bash
# Run all transaction-related tests
pytest tests/test_transaction_*.py -v

# Run specific test modules
pytest tests/test_transaction_history.py -v
pytest tests/test_transaction_intent_router.py -v
pytest tests/test_transaction_llm_extraction.py -v
pytest tests/test_transaction_ui_handler.py -v
```

### Test Coverage
- **Transaction History**: 29 tests covering all filtering combinations and edge cases
- **Intent Router**: Tests for transaction keyword classification
- **LLM Extraction**: Tests for parameter parsing from natural language
- **UI Handler**: Tests for table formatting and error handling

### Key Test Scenarios
1. Default retrieval (no filters) returns all transactions sorted by date descending
2. Date range filters work with YYYY-MM-DD format
3. Type filters correctly separate credit vs debit
4. Amount filters (min/max) properly constrain results
5. Invalid dates are ignored (graceful degradation)
6. Negative amounts are rejected
7. Non-existent users return empty results with success=True
8. Empty results handled with appropriate message

### Known Limitations
- Transaction storage is in-memory (not persistent)
- Sample data only includes user123
- Date filtering uses string comparison (YYYY-MM-DD format required)
