"""Tests for chainlit_app.py - TDD for transfer_funds action handler"""
import pytest
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============================================================
# TDD Tests - These verify the implementation is correct
# ============================================================

@pytest.mark.asyncio
async def test_transfer_funds_branch_exists():
    """Test that after implementation, transfer_funds branch exists."""
    with open('/workspace/ui/chainlit_app.py', 'r') as f:
        content = f.read()
    
    # Check that transfer_funds IS handled in handle_action
    assert 'elif action_name == "transfer_funds":' in content
    assert 'BankingActions.transfer_funds' in content
    assert 'extract_action_params(query, "transfer")' in content


@pytest.mark.asyncio
async def test_transfer_funds_auth_handling():
    """Test that transfer_funds handles authentication."""
    with open('/workspace/ui/chainlit_app.py', 'r') as f:
        content = f.read()
    
    # Find the transfer_funds branch
    transfer_start = content.find('elif action_name == "transfer_funds":')
    assert transfer_start > 0, "transfer_funds branch not found"
    
    # Get a section after the branch start (next 1500 chars should be enough)
    transfer_section = content[transfer_start:transfer_start + 1500]
    
    # Check for authentication handling in transfer_funds branch
    assert 'needs_auth' in transfer_section
    assert 'request_dummy_auth' in transfer_section


@pytest.mark.asyncio
async def test_transfer_funds_param_extraction():
    """Test that transfer_funds extracts parameters correctly."""
    with open('/workspace/ui/chainlit_app.py', 'r') as f:
        content = f.read()
    
    # Check for parameter extraction
    assert 'from_account = params.get("from_account")' in content
    assert 'to_account = params.get("to_account")' in content
    assert 'amount = params.get("amount")' in content


@pytest.mark.asyncio
async def test_transfer_funds_validation():
    """Test that transfer_funds validates parameters."""
    with open('/workspace/ui/chainlit_app.py', 'r') as f:
        content = f.read()
    
    # Check for parameter validation
    assert 'if not all([from_account, to_account, amount]):' in content
    assert 'missing = []' in content
    assert 'source account' in content
    assert 'destination account' in content


@pytest.mark.asyncio
async def test_transfer_funds_execution():
    """Test that transfer_funds calls BankingActions.transfer_funds."""
    with open('/workspace/ui/chainlit_app.py', 'r') as f:
        content = f.read()
    
    # Check for action execution
    assert 'BankingActions.transfer_funds(user_id, from_account, to_account, amount)' in content


@pytest.mark.asyncio
async def test_transfer_funds_logging():
    """Test that transfer_funds logs the action."""
    with open('/workspace/ui/chainlit_app.py', 'r') as f:
        content = f.read()
    
    # Find the transfer_funds branch
    transfer_start = content.find('elif action_name == "transfer_funds":')
    transfer_section = content[transfer_start:transfer_start + 2000] if transfer_start > 0 else ""
    
    # Check for logging
    assert 'logger.log_action' in transfer_section
    assert 'langwatch_tracker.track_action_execution' in transfer_section


@pytest.mark.asyncio
async def test_transfer_funds_success_response():
    """Test that transfer_funds returns formatted success message."""
    with open('/workspace/ui/chainlit_app.py', 'r') as f:
        content = f.read()
    
    # Check for success response formatting
    assert 'Transaction ID: **{result[\'transaction_id\']}**' in content
    assert 'New balance: **${result[\'new_balance\']:.2f}**' in content


@pytest.mark.asyncio
async def test_transfer_funds_error_response():
    """Test that transfer_funds returns formatted error message."""
    with open('/workspace/ui/chainlit_app.py', 'r') as f:
        content = f.read()
    
    # Find the transfer_funds branch and get enough content
    transfer_start = content.find('elif action_name == "transfer_funds":')
    # Get 3000 chars to include the error handling at the end
    transfer_section = content[transfer_start:transfer_start + 3000] if transfer_start > 0 else ""
    
    # Check for error response handling
    assert '❌' in transfer_section
    assert 'result.get' in transfer_section or "result['error']" in content


@pytest.mark.asyncio
async def test_transfer_funds_before_fallback():
    """Test that transfer_funds branch is before the fallback message."""
    with open('/workspace/ui/chainlit_app.py', 'r') as f:
        content = f.read()
    
    transfer_pos = content.find('elif action_name == "transfer_funds":')
    fallback_pos = content.find("Action '{action_name}' is not yet implemented")
    
    assert transfer_pos > 0, "transfer_funds branch not found"
    assert fallback_pos > 0, "fallback message not found"
    assert transfer_pos < fallback_pos, "transfer_funds branch must be before fallback"
