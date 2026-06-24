"""Tests for Chainlit UI - transfer_funds handler"""
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
sys.path.append(PROJECT_ROOT)

from core_banking.banking_actions import BankingActions


# Create a simple mock for chainlit
class MockUserSession:
    def __init__(self):
        self.data = {}
    
    def get(self, key):
        return self.data.get(key)
    
    def set(self, key, value):
        self.data[key] = value

class MockChainlit:
    user_session = MockUserSession()


async def request_dummy_auth():
    """Mock for testing"""
    return True


class TestHandleActionTransferFunds:
    """Test the transfer_funds branch in handle_action()"""
    
    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        """Setup mocks for all tests"""
        # Patch chainlit module
        mock_cl = MagicMock()
        mock_cl.user_session = MockUserSession()
        
        with patch.dict('sys.modules', {'chainlit': mock_cl, 'chainlit.cl': mock_cl}):
            # Import the module after patching
            import importlib
            import ui.chainlit_app as chainlit_app
            importlib.reload(chainlit_app)
            
            # Setup module-level variables
            chainlit_app.llm_core = MagicMock()
            chainlit_app.logger = MagicMock()
            chainlit_app.langwatch_tracker = MagicMock()
            
            yield chainlit_app, mock_cl
    
    async def test_transfer_funds_not_implemented_yet(self):
        """Test that transfer_funds currently returns 'not yet implemented' message"""
        import ui.chainlit_app as chainlit_app
        
        # Setup llm_core mock
        chainlit_app.llm_core.plan_action.return_value = {
            "action": "transfer_funds",
            "needs_auth": True
        }
        
        chainlit_app.llm_core.extract_action_params.return_value = {
            "from_account": "savings",
            "to_account": "checking",
            "amount": 100.0
        }
        
        result = await chainlit_app.handle_action(
            query="Transfer $100 from savings to checking",
            intent="write",
            user_id="user123"
        )
        
        # Before implementation, this should return the "not implemented" message
        assert "not yet implemented" in result.lower() or "transfer_funds" in result
    
    async def test_transfer_funds_success(self):
        """Test successful transfer_funds execution"""
        import ui.chainlit_app as chainlit_app
        
        # Setup: user is authenticated
        chainlit_app.cl.user_session.set("authenticated", True)
        
        # Setup llm_core mock
        chainlit_app.llm_core.plan_action.return_value = {
            "action": "transfer_funds",
            "needs_auth": True
        }
        
        chainlit_app.llm_core.extract_action_params.return_value = {
            "from_account": "savings",
            "to_account": "checking",
            "amount": 100.0
        }
        
        # Mock BankingActions.transfer_funds to return success
        with patch.object(BankingActions, 'transfer_funds', return_value={
            "success": True,
            "message": "Successfully transferred $100.00 from savings",
            "transaction_id": "TXN123456",
            "new_balance": 15330.50
        }):
            result = await chainlit_app.handle_action(
                query="Transfer $100 from savings to checking",
                intent="write",
                user_id="user123"
            )
            
            # Should return success message
            assert "✅" in result
            assert "Successfully transferred" in result
            assert "TXN123456" in result
            assert "$15330.50" in result
    
    async def test_transfer_funds_auth_required(self):
        """Test transfer_funds requires authentication"""
        import ui.chainlit_app as chainlit_app
        
        # Setup: user is NOT authenticated
        chainlit_app.cl.user_session.set("authenticated", False)
        
        # Setup llm_core mock
        chainlit_app.llm_core.plan_action.return_value = {
            "action": "transfer_funds",
            "needs_auth": True
        }
        
        chainlit_app.llm_core.extract_action_params.return_value = {
            "from_account": "savings",
            "to_account": "checking",
            "amount": 100.0
        }
        
        # Mock request_dummy_auth to fail
        with patch('ui.chainlit_app.request_dummy_auth', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = False
            
            result = await chainlit_app.handle_action(
                query="Transfer $100 from savings to checking",
                intent="write",
                user_id="user123"
            )
            
            # Should return auth required message
            assert "Authentication required" in result
    
    async def test_transfer_funds_missing_from_account(self):
        """Test error when from_account is missing"""
        import ui.chainlit_app as chainlit_app
        
        chainlit_app.cl.user_session.set("authenticated", True)
        
        chainlit_app.llm_core.plan_action.return_value = {
            "action": "transfer_funds",
            "needs_auth": True
        }
        
        chainlit_app.llm_core.extract_action_params.return_value = {
            "from_account": None,
            "to_account": "checking",
            "amount": 100.0
        }
        
        result = await chainlit_app.handle_action(
            query="Transfer $100 to checking",
            intent="write",
            user_id="user123"
        )
        
        # Should return missing source account error
        assert "Missing required information" in result
        assert "source account" in result
    
    async def test_transfer_funds_missing_to_account(self):
        """Test error when to_account is missing"""
        import ui.chainlit_app as chainlit_app
        
        chainlit_app.cl.user_session.set("authenticated", True)
        
        chainlit_app.llm_core.plan_action.return_value = {
            "action": "transfer_funds",
            "needs_auth": True
        }
        
        chainlit_app.llm_core.extract_action_params.return_value = {
            "from_account": "savings",
            "to_account": None,
            "amount": 100.0
        }
        
        result = await chainlit_app.handle_action(
            query="Transfer $100 from savings",
            intent="write",
            user_id="user123"
        )
        
        assert "Missing required information" in result
        assert "destination account" in result
    
    async def test_transfer_funds_missing_amount(self):
        """Test error when amount is missing"""
        import ui.chainlit_app as chainlit_app
        
        chainlit_app.cl.user_session.set("authenticated", True)
        
        chainlit_app.llm_core.plan_action.return_value = {
            "action": "transfer_funds",
            "needs_auth": True
        }
        
        chainlit_app.llm_core.extract_action_params.return_value = {
            "from_account": "savings",
            "to_account": "checking",
            "amount": None
        }
        
        result = await chainlit_app.handle_action(
            query="Transfer from savings to checking",
            intent="write",
            user_id="user123"
        )
        
        assert "Missing required information" in result
        assert "amount" in result
    
    async def test_transfer_funds_zero_amount(self):
        """Test error when amount is zero"""
        import ui.chainlit_app as chainlit_app
        
        chainlit_app.cl.user_session.set("authenticated", True)
        
        chainlit_app.llm_core.plan_action.return_value = {
            "action": "transfer_funds",
            "needs_auth": True
        }
        
        chainlit_app.llm_core.extract_action_params.return_value = {
            "from_account": "savings",
            "to_account": "checking",
            "amount": 0.0
        }
        
        result = await chainlit_app.handle_action(
            query="Transfer $0 from savings to checking",
            intent="write",
            user_id="user123"
        )
        
        assert "amount must be greater than zero" in result
    
    async def test_transfer_funds_negative_amount(self):
        """Test error when amount is negative"""
        import ui.chainlit_app as chainlit_app
        
        chainlit_app.cl.user_session.set("authenticated", True)
        
        chainlit_app.llm_core.plan_action.return_value = {
            "action": "transfer_funds",
            "needs_auth": True
        }
        
        chainlit_app.llm_core.extract_action_params.return_value = {
            "from_account": "savings",
            "to_account": "checking",
            "amount": -50.0
        }
        
        result = await chainlit_app.handle_action(
            query="Transfer $-50 from savings to checking",
            intent="write",
            user_id="user123"
        )
        
        assert "amount must be greater than zero" in result
    
    async def test_transfer_funds_backend_error(self):
        """Test error handling when backend returns failure"""
        import ui.chainlit_app as chainlit_app
        
        chainlit_app.cl.user_session.set("authenticated", True)
        
        chainlit_app.llm_core.plan_action.return_value = {
            "action": "transfer_funds",
            "needs_auth": True
        }
        
        chainlit_app.llm_core.extract_action_params.return_value = {
            "from_account": "savings",
            "to_account": "checking",
            "amount": 100000.0
        }
        
        # Mock BankingActions.transfer_funds to return error
        with patch.object(BankingActions, 'transfer_funds', return_value={
            "success": False,
            "error": "Insufficient funds"
        }):
            result = await chainlit_app.handle_action(
                query="Transfer $100000 from savings to checking",
                intent="write",
                user_id="user123"
            )
            
            # Should return error message from backend
            assert "❌" in result
            assert "Insufficient funds" in result
    
    async def test_transfer_funds_multiple_missing_params(self):
        """Test error when multiple parameters are missing"""
        import ui.chainlit_app as chainlit_app
        
        chainlit_app.cl.user_session.set("authenticated", True)
        
        chainlit_app.llm_core.plan_action.return_value = {
            "action": "transfer_funds",
            "needs_auth": True
        }
        
        chainlit_app.llm_core.extract_action_params.return_value = {
            "from_account": None,
            "to_account": None,
            "amount": None
        }
        
        result = await chainlit_app.handle_action(
            query="Transfer",
            intent="write",
            user_id="user123"
        )
        
        # Should list all missing parameters
        assert "Missing required information" in result
        assert "source account" in result
        assert "destination account" in result
        assert "amount" in result
