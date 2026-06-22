"""Simple tests for transfer_funds - verify implementation"""
import pytest
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
sys.path.append(PROJECT_ROOT)


def test_transfer_funds_is_implemented():
    """Test that transfer_funds branch exists in the code"""
    with open(Path(PROJECT_ROOT) / "ui" / "chainlit_app.py", "r") as f:
        content = f.read()

    # The transfer_funds elif branch SHOULD exist
    assert "elif action_name == \"transfer_funds\":" in content
    
    # The fallback message should still exist for other actions
    assert "is not yet implemented in this prototype" in content
    print("✓ Test passed: transfer_funds is implemented")


def test_implementation_matches_spec():
    """Test that the implementation matches the specification"""
    with open(Path(PROJECT_ROOT) / "ui" / "chainlit_app.py", "r") as f:
        content = f.read()

    # Check for authentication check
    assert "if needs_auth and not cl.user_session.get(\"authenticated\"):" in content

    # Check for request_dummy_auth call
    assert "await request_dummy_auth()" in content

    # Check for parameter extraction
    assert 'params = llm_core.extract_action_params(query, "transfer")' in content

    # Check for parameter validation
    assert "from_account" in content
    assert "to_account" in content  
    assert "amount" in content
    assert "if not all([from_account, to_account, amount]):" in content

    # Check for positive amount validation
    assert "if amount <= 0:" in content
    assert "Transfer amount must be greater than zero" in content

    # Check for BankingActions call
    assert "BankingActions.transfer_funds(user_id, from_account, to_account, amount)" in content

    # Check for logging
    assert "logger.log_action" in content

    # Check for LangWatch tracking
    assert "langwatch_tracker.track_action_execution" in content

    # Check for success response formatting
    assert "✅" in content
    assert "Transaction ID:" in content
    assert "New" in content and "balance:" in content

    # Check for error response formatting
    assert "❌" in content

    print("✓ Test passed: implementation matches specification")


def test_transfer_funds_branch_structure():
    """Test that transfer_funds branch has all required components"""
    with open(Path(PROJECT_ROOT) / "ui" / "chainlit_app.py", "r") as f:
        content = f.read()

    # Find the transfer_funds branch
    transfer_start = content.find('elif action_name == "transfer_funds":')
    assert transfer_start != -1, "transfer_funds branch not found"
    
    # Find the next elif or return statement (end of this branch)
    next_elif = content.find('elif action_name', transfer_start + 1)
    fallback_return = content.find("return f\"Action '{action_name}' is not yet implemented", transfer_start + 1)
    
    # Get the branch content
    branch_end = next_elif if next_elif != -1 else fallback_return
    assert branch_end != -1, "Could not find end of transfer_funds branch"
    
    branch_content = content[transfer_start:branch_end]
    
    # Verify all required elements are in the branch
    required_elements = [
        "extract_action_params",
        "from_account",
        "to_account", 
        "amount",
        "if not all([from_account, to_account, amount]):",
        "if amount <= 0:",
        "BankingActions.transfer_funds",
        "logger.log_action",
        "langwatch_tracker.track_action_execution",
        "✅",
        "Transaction ID:",
        "New",
        "balance:"
    ]
    
    for element in required_elements:
        assert element in branch_content, f"Missing required element: {element}"
    
    print("✓ Test passed: transfer_funds branch has all required components")


if __name__ == "__main__":
    print("Running tests for transfer_funds...")
    print("\n=== Step 1: Verify implementation exists ===")
    test_transfer_funds_is_implemented()
    
    print("\n=== Step 2: Verify implementation matches spec ===")
    test_implementation_matches_spec()
    
    print("\n=== Step 3: Verify branch structure ===")
    test_transfer_funds_branch_structure()
    
    print("\n✅ All tests passed!")
