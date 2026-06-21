"""Tests for transaction history feature"""
import pytest
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core_banking.banking_actions import BankingActions
from datetime import datetime


class TestTransactionHistory:
    """Test cases for transaction history feature"""
    
    def setup_method(self):
        """Setup test fixtures"""
        # Initialize test transactions
        BankingActions.TRANSACTIONS = {
            "user123": [
                {"id": "TXN100001", "type": "debit", "amount": 50.00, "description": "Grocery Store", "date": "2025-06-15", "balance": 15380.50},
                {"id": "TXN100002", "type": "credit", "amount": 3000.00, "description": "Salary", "date": "2025-06-01", "balance": 18430.50},
                {"id": "TXN100003", "type": "debit", "amount": 1250.00, "description": "Credit Card Payment", "date": "2025-06-10", "balance": 17180.50},
                {"id": "TXN100004", "type": "debit", "amount": 85.50, "description": "Electricity Bill", "date": "2025-06-12", "balance": 17095.00},
                {"id": "TXN100005", "type": "debit", "amount": 200.00, "description": "Online Shopping", "date": "2025-06-14", "balance": 16895.00},
                {"id": "TXN100006", "type": "credit", "amount": 500.00, "description": "Refund", "date": "2025-06-13", "balance": 17395.00},
            ]
        }
    
    def teardown_method(self):
        """Cleanup after tests"""
        # Reset transactions
        BankingActions.TRANSACTIONS = {}
    
    def test_get_transactions_no_filters(self):
        """Test getting transactions with no filters - should return default 10"""
        result = BankingActions.get_transactions("user123")
        
        assert result["success"] is True
        assert len(result["transactions"]) == 6  # We only have 6 transactions
        assert result["count"] == 6
        assert result["total_available"] == 6
        # Should be sorted by date descending
        assert result["transactions"][0]["date"] == "2025-06-15"
    
    def test_get_transactions_with_limit(self):
        """Test getting limited number of transactions"""
        result = BankingActions.get_transactions("user123", limit=3)
        
        assert result["success"] is True
        assert len(result["transactions"]) == 3
        assert result["count"] == 3
        assert result["total_available"] == 6
    
    def test_get_transactions_filter_by_type_credit(self):
        """Test filtering transactions by credit type"""
        result = BankingActions.get_transactions("user123", transaction_type="credit")
        
        assert result["success"] is True
        assert len(result["transactions"]) == 2
        for txn in result["transactions"]:
            assert txn["type"] == "credit"
    
    def test_get_transactions_filter_by_type_debit(self):
        """Test filtering transactions by debit type"""
        result = BankingActions.get_transactions("user123", transaction_type="debit")
        
        assert result["success"] is True
        assert len(result["transactions"]) == 4
        for txn in result["transactions"]:
            assert txn["type"] == "debit"
    
    def test_get_transactions_filter_by_date_range(self):
        """Test filtering transactions by date range"""
        result = BankingActions.get_transactions(
            "user123",
            start_date="2025-06-10",
            end_date="2025-06-14"
        )
        
        assert result["success"] is True
        # Should include transactions from June 10, 12, 13, 14
        assert len(result["transactions"]) == 4
        for txn in result["transactions"]:
            assert "2025-06-10" <= txn["date"] <= "2025-06-14"
    
    def test_get_transactions_filter_by_min_amount(self):
        """Test filtering transactions by minimum amount"""
        result = BankingActions.get_transactions("user123", min_amount=100.00)
        
        assert result["success"] is True
        # Should exclude the $50 and $85.50 transactions
        assert len(result["transactions"]) == 4
        for txn in result["transactions"]:
            assert txn["amount"] >= 100.00
    
    def test_get_transactions_filter_by_max_amount(self):
        """Test filtering transactions by maximum amount"""
        result = BankingActions.get_transactions("user123", max_amount=500.00)
        
        assert result["success"] is True
        # Should exclude the $3000 salary and $1250 credit card payment
        assert len(result["transactions"]) == 4
        for txn in result["transactions"]:
            assert txn["amount"] <= 500.00
    
    def test_get_transactions_filter_by_amount_range(self):
        """Test filtering transactions by amount range"""
        result = BankingActions.get_transactions(
            "user123",
            min_amount=100.00,
            max_amount=500.00
        )
        
        assert result["success"] is True
        # Should include: $1250, $85.50, $200, $500
        # But $85.50 is below min, $1250 is above max
        # So: $200, $500
        assert len(result["transactions"]) == 2
    
    def test_get_transactions_user_not_found(self):
        """Test getting transactions for non-existent user"""
        result = BankingActions.get_transactions("nonexistent_user")
        
        assert result["success"] is True
        assert result["transactions"] == []
        assert result["message"] == "No transactions found for this account"
    
    def test_get_transactions_no_filters_with_limit_zero(self):
        """Test with limit of 0 - should use default"""
        result = BankingActions.get_transactions("user123", limit=0)
        
        assert result["success"] is True
        # Should use default limit of 10, but we only have 6
        assert len(result["transactions"]) == 6
    
    def test_get_transactions_negative_limit(self):
        """Test with negative limit - should use default"""
        result = BankingActions.get_transactions("user123", limit=-5)
        
        assert result["success"] is True
        assert len(result["transactions"]) == 6
    
    def test_get_transactions_invalid_date_format(self):
        """Test with invalid date format - should ignore date filters"""
        result = BankingActions.get_transactions(
            "user123",
            start_date="invalid-date",
            end_date="also-invalid"
        )
        
        assert result["success"] is True
        # Should return all transactions since invalid dates are ignored
        assert len(result["transactions"]) == 6
    
    def test_get_transactions_negative_amount_filters(self):
        """Test with negative amount filters - should ignore them"""
        result = BankingActions.get_transactions(
            "user123",
            min_amount=-100.00,
            max_amount=-50.00
        )
        
        assert result["success"] is True
        # Should return all transactions since negative filters are ignored
        assert len(result["transactions"]) == 6
    
    def test_get_transactions_empty_transactions(self):
        """Test with user that has no transactions"""
        BankingActions.TRANSACTIONS["user_no_txns"] = []
        
        result = BankingActions.get_transactions("user_no_txns")
        
        assert result["success"] is True
        assert result["transactions"] == []
        assert result["message"] == "No transactions found for this account"
    
    def test_get_transactions_mixed_filters(self):
        """Test with multiple filters combined"""
        result = BankingActions.get_transactions(
            "user123",
            start_date="2025-06-10",
            end_date="2025-06-14",
            transaction_type="debit",
            limit=2
        )
        
        assert result["success"] is True
        # Date range: June 10-14, type: debit
        # TXN100003 (June 10), TXN100004 (June 12), TXN100005 (June 14)
        # With limit 2, should return 2
        assert len(result["transactions"]) == 2
        for txn in result["transactions"]:
            assert txn["type"] == "debit"
            assert "2025-06-10" <= txn["date"] <= "2025-06-14"


class TestTransactionLogging:
    """Test cases for transaction logging in transfer_funds"""
    
    def setup_method(self):
        """Setup test fixtures"""
        # Reset accounts and transactions
        BankingActions.ACCOUNTS = {
            "user123": {
                "savings": {"balance": 15430.50, "account_number": "001-234567-8"},
                "checking": {"balance": 2340.20, "account_number": "002-234567-8"},
                "cards": [
                    {"type": "credit", "last4": "4532", "status": "active", "balance": 1250.00},
                    {"type": "debit", "last4": "7891", "status": "active"}
                ]
            }
        }
        BankingActions.TRANSACTIONS = {}
    
    def test_transfer_funds_logs_transactions(self):
        """Test that transfer_funds logs debit and credit transactions"""
        # Clear any existing transactions
        BankingActions.TRANSACTIONS = {"user123": []}
        
        # Perform transfer
        result = BankingActions.transfer_funds(
            "user123",
            "savings",
            "checking",
            100.00
        )
        
        assert result["success"] is True
        
        # Check that transactions were logged
        user_txns = BankingActions.TRANSACTIONS.get("user123", [])
        
        # Should have at least 1 transaction (debit from savings)
        assert len(user_txns) >= 1
        
        # Check debit transaction
        debit_txns = [t for t in user_txns if t["type"] == "debit"]
        assert len(debit_txns) >= 1
        assert debit_txns[0]["amount"] == 100.00
        assert "Transfer to checking" in debit_txns[0]["description"]
        assert debit_txns[0]["date"] == datetime.now().strftime("%Y-%m-%d")
    
    def test_transfer_funds_logs_to_same_user_account(self):
        """Test that transfer to another account in same user logs credit transaction"""
        BankingActions.TRANSACTIONS = {"user123": []}
        
        initial_savings = BankingActions.ACCOUNTS["user123"]["savings"]["balance"]
        initial_checking = BankingActions.ACCOUNTS["user123"]["checking"]["balance"]
        
        # Perform transfer
        result = BankingActions.transfer_funds(
            "user123",
            "savings",
            "checking",
            100.00
        )
        
        assert result["success"] is True
        
        # Check balances
        assert BankingActions.ACCOUNTS["user123"]["savings"]["balance"] == initial_savings - 100.00
        assert BankingActions.ACCOUNTS["user123"]["checking"]["balance"] == initial_checking + 100.00
        
        # Check transactions
        user_txns = BankingActions.TRANSACTIONS.get("user123", [])
        
        # Should have both debit and credit transactions
        debit_txns = [t for t in user_txns if t["type"] == "debit"]
        credit_txns = [t for t in user_txns if t["type"] == "credit"]
        
        assert len(debit_txns) >= 1
        assert len(credit_txns) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
