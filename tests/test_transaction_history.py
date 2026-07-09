"""TDD Tests for Transaction History Feature"""
import pytest
import sys
from pathlib import Path

# Add parent directory to path
PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
sys.path.append(PROJECT_ROOT)

from core_banking.banking_actions import BankingActions


class TestTransactionHistory:
    """Test suite for transaction history feature"""
    
    def test_transactions_storage_exists(self):
        """Test that TRANSACTIONS storage exists in BankingActions"""
        assert hasattr(BankingActions, 'TRANSACTIONS')
        assert isinstance(BankingActions.TRANSACTIONS, dict)
    
    def test_get_transactions_exists(self):
        """Test that get_transactions method exists"""
        assert hasattr(BankingActions, 'get_transactions')
        assert callable(BankingActions.get_transactions)
    
    def test_parse_date_exists(self):
        """Test that _parse_date helper method exists"""
        assert hasattr(BankingActions, '_parse_date')
        assert callable(BankingActions._parse_date)
    
    def test_get_transactions_invalid_user(self):
        """Test get_transactions with invalid user_id returns error"""
        result = BankingActions.get_transactions("invalid_user")
        assert result["success"] == False
        assert "error" in result
        assert "User not found" in result["error"]
    
    def test_get_transactions_valid_user_no_data(self):
        """Test get_transactions with valid user but no transactions"""
        # Create a test user without transactions
        BankingActions.ACCOUNTS["test_user_no_txn"] = {
            "savings": {"balance": 1000.00, "account_number": "001-000000-1"}
        }
        BankingActions.TRANSACTIONS["test_user_no_txn"] = []
        
        result = BankingActions.get_transactions("test_user_no_txn")
        assert result["success"] == True
        assert result["transactions"] == []
        assert "No transactions found" in result.get("message", "")
    
    def test_get_transactions_default_limit(self):
        """Test get_transactions returns at most default limit (10) transactions"""
        result = BankingActions.get_transactions("user123")
        assert result["success"] == True
        assert len(result["transactions"]) <= 10
        assert "returned_count" in result
        assert "total_count" in result
    
    def test_get_transactions_filter_by_type_credit(self):
        """Test filtering transactions by type=credit"""
        result = BankingActions.get_transactions("user123", transaction_type="credit")
        assert result["success"] == True
        for txn in result["transactions"]:
            assert txn["type"] == "credit"
    
    def test_get_transactions_filter_by_type_debit(self):
        """Test filtering transactions by type=debit"""
        result = BankingActions.get_transactions("user123", transaction_type="debit")
        assert result["success"] == True
        for txn in result["transactions"]:
            assert txn["type"] == "debit"
    
    def test_get_transactions_filter_by_date_range(self):
        """Test filtering transactions by date range"""
        result = BankingActions.get_transactions(
            "user123",
            start_date="2025-06-10",
            end_date="2025-06-15"
        )
        assert result["success"] == True
        for txn in result["transactions"]:
            assert "2025-06-10" <= txn["date"] <= "2025-06-15"
    
    def test_get_transactions_filter_by_amount_range(self):
        """Test filtering transactions by amount range"""
        result = BankingActions.get_transactions(
            "user123",
            min_amount=100.00,
            max_amount=1000.00
        )
        assert result["success"] == True
        for txn in result["transactions"]:
            assert 100.00 <= txn["amount"] <= 1000.00
    
    def test_get_transactions_limit(self):
        """Test limiting number of returned transactions"""
        result = BankingActions.get_transactions("user123", limit=3)
        assert result["success"] == True
        assert len(result["transactions"]) <= 3
    
    def test_get_transactions_sorted_by_date_desc(self):
        """Test that transactions are sorted by date descending (newest first)"""
        result = BankingActions.get_transactions("user123", limit=10)
        assert result["success"] == True
        transactions = result["transactions"]
        if len(transactions) > 1:
            for i in range(len(transactions) - 1):
                assert transactions[i]["date"] >= transactions[i + 1]["date"]
    
    def test_parse_date_today(self):
        """Test parsing 'today' returns current date in YYYY-MM-DD format"""
        import datetime
        result = BankingActions._parse_date("today")
        expected = datetime.date.today().strftime("%Y-%m-%d")
        assert result == expected
    
    def test_parse_date_yesterday(self):
        """Test parsing 'yesterday' returns previous day"""
        import datetime
        result = BankingActions._parse_date("yesterday")
        expected = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        assert result == expected
    
    def test_parse_date_last_week(self):
        """Test parsing 'last week' returns date 7 days ago"""
        import datetime
        result = BankingActions._parse_date("last week")
        expected = (datetime.date.today() - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
        assert result == expected
    
    def test_parse_date_valid_iso_format(self):
        """Test parsing valid ISO date format"""
        result = BankingActions._parse_date("2025-06-15")
        assert result == "2025-06-15"
    
    def test_parse_date_invalid_format(self):
        """Test parsing invalid date format returns None"""
        result = BankingActions._parse_date("invalid-date")
        assert result is None
    
    def test_transactions_have_required_fields(self):
        """Test that sample transactions have required fields"""
        result = BankingActions.get_transactions("user123")
        assert result["success"] == True
        for txn in result["transactions"]:
            assert "id" in txn
            assert "type" in txn
            assert "amount" in txn
            assert "description" in txn
            assert "date" in txn
            assert "balance" in txn


class TestIntentRouterTransactionKeywords:
    """Test that transaction keywords are properly recognized"""
    
    def test_read_keywords_include_transaction_terms(self):
        """Test that READ_KEYWORDS includes transaction-related terms"""
        # Directly check the file to avoid importing dependencies
        import sys
        from pathlib import Path
        PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
        sys.path.append(PROJECT_ROOT)
        
        # Read the file directly to check keywords
        intent_router_path = Path(PROJECT_ROOT) / "ui" / "intent_router.py"
        with open(intent_router_path, 'r') as f:
            content = f.read()
        
        expected_keywords = ["transactions", "history", "recent", "statement"]
        for kw in expected_keywords:
            assert kw in content, f"Keyword '{kw}' not found in intent_router.py"


class TestLLMCoreTransactionAction:
    """Test LLM core transaction action planning"""
    
    def test_transaction_history_in_plan_action_prompt(self):
        """Test that transaction_history is included in plan_action prompt"""
        # Read the file directly to check the prompt
        import sys
        from pathlib import Path
        PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
        sys.path.append(PROJECT_ROOT)
        
        llm_core_path = Path(PROJECT_ROOT) / "llm" / "llm_core.py"
        with open(llm_core_path, 'r') as f:
            content = f.read()
        
        # Check that transaction_history is in the prompt
        assert "transaction_history" in content, "transaction_history not found in llm_core.py"
        assert "transaction_history" in content, "extract_action_params doesn't include transaction_history"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
