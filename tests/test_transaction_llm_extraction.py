"""Tests for transaction history LLM parameter extraction"""
import pytest
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_llm_core_has_get_transactions_extraction():
    """Test that LLMCore source includes get_transactions in extract_action_params"""
    # Read the llm_core.py file directly to check for get_transactions
    with open('/workspace/llm/llm_core.py', 'r') as f:
        content = f.read()
    
    # Check for get_transactions in extract_action_params
    assert '"get_transactions"' in content or "'get_transactions'" in content
    assert 'start_date|end_date|type|min_amount|max_amount|limit' in content


def test_llm_core_plan_action_includes_get_transactions():
    """Test that plan_action includes get_transactions"""
    with open('/workspace/llm/llm_core.py', 'r') as f:
        content = f.read()
    
    # Check for get_transactions in plan_action
    assert 'get_transactions' in content
    # Check it's in the action list
    assert 'lock_card, unlock_card, check_balance, transfer_funds, get_transactions' in content


def test_llm_core_classify_intent_includes_transaction_history():
    """Test that classify_intent includes transaction history in read intent"""
    with open('/workspace/llm/llm_core.py', 'r') as f:
        content = f.read()
    
    # Check for transaction history in read intent description
    assert 'check transaction history' in content or 'transaction history' in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
