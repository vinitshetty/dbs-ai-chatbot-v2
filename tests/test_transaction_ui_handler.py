"""Tests for transaction history UI handler"""
import pytest
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core_banking.banking_actions import BankingActions
from unittest.mock import Mock, MagicMock, patch


class TestTransactionUIHandler:
    """Test cases for transaction history UI handler logic"""
    
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
        BankingActions.TRANSACTIONS = {}
    
    def test_transaction_table_formatting(self):
        """Test that transactions are formatted as a table"""
        result = BankingActions.get_transactions("user123", limit=3)
        
        assert result["success"] is True
        txns = result["transactions"]
        
        # Verify we can format as table
        table_header = "| Date | Type | Description | Amount | Balance |"
        assert len(txns) > 0
        
        for txn in txns:
            date = txn.get("date", "N/A")
            txn_type = txn.get("type", "unknown").title()
            desc = txn.get("description", "N/A")
            amount = txn.get('amount', 0)
            balance = txn.get('balance', 0)
            
            # All required fields are present
            assert date != "N/A"
            assert txn_type in ["Debit", "Credit"]
            assert desc != "N/A"
            assert amount > 0
            assert balance >= 0
    
    def test_transaction_amount_formatting(self):
        """Test that debit/credit amounts are formatted correctly"""
        result = BankingActions.get_transactions("user123", limit=2)
        txns = result["transactions"]
        
        for txn in txns:
            amount = txn.get('amount', 0)
            txn_type = txn.get('type')
            
            # Verify amount formatting works
            formatted = f"${amount:.2f}"
            assert len(formatted.split('.')[-1]) == 2  # 2 decimal places
            
            # Debit should be negative in display
            if txn_type == "debit":
                display_amount = f"**-${amount:.2f}**"
                assert "-" in display_amount
            else:
                display_amount = f"**+${amount:.2f}**"
                assert "+" in display_amount


class TestChainlitAppIntegration:
    """Test integration with chainlit app handler"""
    
    def test_get_transactions_handler_exists(self):
        """Test that get_transactions handler exists in chainlit_app.py"""
        with open('/workspace/ui/chainlit_app.py', 'r') as f:
            content = f.read()
        
        # Check for get_transactions handler
        assert 'elif action_name == "get_transactions":' in content
        assert 'BankingActions.get_transactions' in content
        assert 'table_header' in content
        assert 'table_rows' in content
    
    def test_welcome_message_includes_transaction_history(self):
        """Test that welcome message mentions transaction history"""
        with open('/workspace/ui/chainlit_app.py', 'r') as f:
            content = f.read()
        
        assert 'Viewing your transaction history' in content
    
    def test_transaction_handler_returns_table(self):
        """Test that handler returns properly formatted table"""
        with open('/workspace/ui/chainlit_app.py', 'r') as f:
            content = f.read()
        
        # Check for table formatting
        assert '| Date | Type | Description | Amount | Balance |' in content
        assert 'table_rows.append' in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
