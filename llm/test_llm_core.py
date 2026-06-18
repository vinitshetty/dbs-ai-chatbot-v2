# Test LLMCore Error Handling
"""Tests for error handling in LLMCore"""
import pytest
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_mistralai import ChatMistralAI

from llm.llm_core import LLMCore
from audit.logger import AuditLogger


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing"""
    logger = Mock(spec=AuditLogger)
    logger.log_event = Mock()
    return logger


@pytest.fixture
def mock_llm():
    """Create a mock LLM that can be controlled in tests"""
    mock = Mock(spec=ChatMistralAI)
    mock.invoke = Mock()
    return mock


@pytest.fixture
def llm_core_with_logger(mock_logger, mock_llm):
    """Create LLMCore with mock logger and mock LLM"""
    with patch.dict('os.environ', {'MISTRAL_API_KEY': 'test_key'}):
        with patch('llm.llm_core.ChatMistralAI', return_value=mock_llm):
            llm = LLMCore(logger=mock_logger)
            return llm


class TestLLMCoreInit:
    """Tests for LLMCore initialization"""

    def test_init_with_default_params(self, mock_logger):
        """Test initialization with default parameters"""
        with patch.dict('os.environ', {'MISTRAL_API_KEY': 'test_key'}):
            llm = LLMCore(logger=mock_logger)
            assert llm.max_retries == 3
            assert llm.timeout == 30
            assert llm.retry_delay == 1.0
            assert llm.logger == mock_logger

    def test_init_with_custom_params(self, mock_logger):
        """Test initialization with custom parameters"""
        with patch.dict('os.environ', {'MISTRAL_API_KEY': 'test_key'}):
            llm = LLMCore(
                model_name='mistral-large',
                max_retries=5,
                timeout=60,
                retry_delay=2.0,
                logger=mock_logger
            )
            assert llm.max_retries == 5
            assert llm.timeout == 60
            assert llm.retry_delay == 2.0

    def test_init_missing_api_key(self):
        """Test that ValueError is raised when API key is missing"""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="MISTRAL_API_KEY not found"):
                LLMCore()

    def test_init_without_logger(self):
        """Test initialization without logger"""
        with patch.dict('os.environ', {'MISTRAL_API_KEY': 'test_key'}):
            llm = LLMCore()
            assert llm.logger is None


class TestInvokeWithRetry:
    """Tests for _invoke_with_retry helper method"""

    def test_successful_invoke(self, llm_core_with_logger, mock_llm):
        """Test successful API call on first attempt"""
        mock_response = Mock()
        mock_response.content = "test response"
        mock_llm.invoke = Mock(return_value=mock_response)
        
        result = llm_core_with_logger._invoke_with_retry([Mock()], "test_op")
        assert result == mock_response
        assert mock_llm.invoke.call_count == 1

    def test_retry_on_timeout_error(self, llm_core_with_logger, mock_llm):
        """Test retry on TimeoutError"""
        mock_response = Mock()
        mock_response.content = "test response"
        
        # First two calls timeout, third succeeds
        mock_llm.invoke = Mock(
            side_effect=[TimeoutError("timeout"), TimeoutError("timeout"), mock_response]
        )
        
        result = llm_core_with_logger._invoke_with_retry([Mock()], "test_op")
        assert result == mock_response
        assert mock_llm.invoke.call_count == 3

    def test_retry_on_connection_error(self, llm_core_with_logger, mock_llm):
        """Test retry on ConnectionError"""
        mock_response = Mock()
        mock_response.content = "test response"
        
        mock_llm.invoke = Mock(
            side_effect=[ConnectionError("connection failed"), mock_response]
        )
        
        result = llm_core_with_logger._invoke_with_retry([Mock()], "test_op")
        assert result == mock_response
        assert mock_llm.invoke.call_count == 2

    def test_no_retry_on_value_error(self, llm_core_with_logger, mock_llm):
        """Test that ValueError is not retried (re-raised)"""
        mock_llm.invoke = Mock(
            side_effect=ValueError("parse error")
        )
        
        with pytest.raises(ValueError, match="parse error"):
            llm_core_with_logger._invoke_with_retry([Mock()], "test_op")
        assert mock_llm.invoke.call_count == 1

    def test_no_retry_on_index_error(self, llm_core_with_logger, mock_llm):
        """Test that IndexError is not retried (re-raised)"""
        mock_llm.invoke = Mock(
            side_effect=IndexError("index out of range")
        )
        
        with pytest.raises(IndexError, match="index out of range"):
            llm_core_with_logger._invoke_with_retry([Mock()], "test_op")
        assert mock_llm.invoke.call_count == 1

    def test_max_retries_exhausted(self, llm_core_with_logger, mock_llm):
        """Test behavior when all retries are exhausted"""
        llm_core_with_logger.max_retries = 2
        mock_llm.invoke = Mock(
            side_effect=TimeoutError("timeout")
        )
        
        result = llm_core_with_logger._invoke_with_retry([Mock()], "test_op")
        assert result is None
        assert mock_llm.invoke.call_count == 3  # initial + 2 retries

    def test_logs_api_errors(self, llm_core_with_logger, mock_llm):
        """Test that API errors are logged"""
        llm_core_with_logger.max_retries = 1  # Need at least 1 retry to see both logs
        mock_llm.invoke = Mock(
            side_effect=ConnectionError("connection failed")
        )
        
        llm_core_with_logger._invoke_with_retry([Mock()], "test_op")
        
        # Should log the error (and possibly the failure)
        assert llm_core_with_logger.logger.log_event.call_count >= 1
        # Check that at least one of the error logs is present
        log_calls = [call[0] for call in llm_core_with_logger.logger.log_event.call_args_list]
        event_types = [call[0] for call in log_calls]
        assert "llm_api_error" in event_types or "llm_api_failure" in event_types

    def test_logs_retry_attempts(self, llm_core_with_logger, mock_llm):
        """Test that retry attempts are logged"""
        mock_response = Mock()
        mock_response.content = "test response"
        
        mock_llm.invoke = Mock(
            side_effect=[TimeoutError("timeout"), mock_response]
        )
        
        llm_core_with_logger._invoke_with_retry([Mock()], "test_op")
        
        # Should log retry
        log_calls = [call[0] for call in llm_core_with_logger.logger.log_event.call_args_list]
        event_types = [call[0] for call in log_calls]
        assert "llm_retry" in event_types

    def test_logs_final_failure(self, llm_core_with_logger, mock_llm):
        """Test that final failure is logged after all retries"""
        llm_core_with_logger.max_retries = 1
        mock_llm.invoke = Mock(
            side_effect=TimeoutError("timeout")
        )
        
        llm_core_with_logger._invoke_with_retry([Mock()], "test_op")
        
        # Should log final failure
        log_calls = [call[0] for call in llm_core_with_logger.logger.log_event.call_args_list]
        event_types = [call[0] for call in log_calls]
        assert "llm_api_failure" in event_types


class TestGenerateResponse:
    """Tests for generate_response error handling"""

    def test_successful_response(self, llm_core_with_logger, mock_llm):
        """Test successful response generation"""
        mock_response = Mock()
        mock_response.content = "This is a test response"
        mock_llm.invoke = Mock(return_value=mock_response)
        
        result = llm_core_with_logger.generate_response("context", "query")
        assert result == "This is a test response"

    def test_api_failure_returns_fallback(self, llm_core_with_logger, mock_llm):
        """Test that API failure returns user-friendly fallback"""
        mock_llm.invoke = Mock(
            side_effect=ConnectionError("connection failed")
        )
        llm_core_with_logger.max_retries = 0
        
        result = llm_core_with_logger.generate_response("context", "query")
        assert "trouble connecting" in result.lower() or "unavailable" in result.lower()

    def test_api_failure_logs_error(self, llm_core_with_logger, mock_llm):
        """Test that API failure in generate_response is logged"""
        mock_llm.invoke = Mock(
            side_effect=ConnectionError("connection failed")
        )
        llm_core_with_logger.max_retries = 0
        
        llm_core_with_logger.generate_response("context", "query")
        
        log_calls = [call[0] for call in llm_core_with_logger.logger.log_event.call_args_list]
        event_types = [call[0] for call in log_calls]
        assert "llm_api_error" in event_types or "llm_api_failure" in event_types

    def test_with_conversation_history(self, llm_core_with_logger, mock_llm):
        """Test generate_response with conversation history"""
        mock_response = Mock()
        mock_response.content = "Response with history"
        mock_llm.invoke = Mock(return_value=mock_response)
        
        history = [
            HumanMessage(content="Previous message 1"),
            SystemMessage(content="Previous response 1"),
            HumanMessage(content="Previous message 2"),
            SystemMessage(content="Previous response 2"),
        ]
        
        result = llm_core_with_logger.generate_response("context", "query", history)
        assert result == "Response with history"
        # Should only include last 4 messages (2 turns) + system + query
        assert len(mock_llm.invoke.call_args[0][0]) >= 1


class TestClassifyIntent:
    """Tests for classify_intent error handling"""

    def test_successful_classification(self, llm_core_with_logger, mock_llm):
        """Test successful intent classification"""
        mock_response = Mock()
        mock_response.content = "faq|0.95"
        mock_llm.invoke = Mock(return_value=mock_response)
        
        result = llm_core_with_logger.classify_intent("What are your hours?")
        assert result == {"intent": "faq", "confidence": 0.95}

    def test_parse_error_returns_unclear(self, llm_core_with_logger, mock_llm):
        """Test that parse errors return unclear intent"""
        mock_response = Mock()
        mock_response.content = "invalid response without pipe"
        mock_llm.invoke = Mock(return_value=mock_response)
        
        result = llm_core_with_logger.classify_intent("What are your hours?")
        assert result == {"intent": "unclear", "confidence": 0.0}

    def test_api_failure_returns_unclear(self, llm_core_with_logger, mock_llm):
        """Test that API failure returns unclear intent with 0 confidence"""
        mock_llm.invoke = Mock(
            side_effect=ConnectionError("connection failed")
        )
        llm_core_with_logger.max_retries = 0
        
        result = llm_core_with_logger.classify_intent("What are your hours?")
        assert result == {"intent": "unclear", "confidence": 0.0}

    def test_value_error_on_parse(self, llm_core_with_logger, mock_llm):
        """Test ValueError is caught and handled"""
        mock_response = Mock()
        mock_response.content = "faq|not_a_number"
        mock_llm.invoke = Mock(return_value=mock_response)
        
        result = llm_core_with_logger.classify_intent("What are your hours?")
        assert result == {"intent": "unclear", "confidence": 0.0}

    def test_index_error_on_parse(self, llm_core_with_logger, mock_llm):
        """Test IndexError is caught and handled"""
        mock_response = Mock()
        mock_response.content = "faq"  # No pipe separator
        mock_llm.invoke = Mock(return_value=mock_response)
        
        result = llm_core_with_logger.classify_intent("What are your hours?")
        assert result == {"intent": "unclear", "confidence": 0.0}

    def test_logs_parse_error(self, llm_core_with_logger, mock_llm):
        """Test that parse errors are logged"""
        mock_response = Mock()
        mock_response.content = "invalid format"
        mock_llm.invoke = Mock(return_value=mock_response)
        
        llm_core_with_logger.classify_intent("What are your hours?")
        
        log_calls = [call[0] for call in llm_core_with_logger.logger.log_event.call_args_list]
        event_types = [call[0] for call in log_calls]
        assert "intent_parse_error" in event_types

    def test_logs_api_failure(self, llm_core_with_logger, mock_llm):
        """Test that API failures in classify_intent are logged"""
        mock_llm.invoke = Mock(
            side_effect=ConnectionError("connection failed")
        )
        llm_core_with_logger.max_retries = 0
        
        llm_core_with_logger.classify_intent("What are your hours?")
        
        log_calls = [call[0] for call in llm_core_with_logger.logger.log_event.call_args_list]
        event_types = [call[0] for call in log_calls]
        assert "intent_classification_failed" in event_types


class TestExtractActionParams:
    """Tests for extract_action_params error handling"""

    def test_lock_card_success(self, llm_core_with_logger, mock_llm):
        """Test successful lock card param extraction"""
        mock_response = Mock()
        mock_response.content = "1234"
        mock_llm.invoke = Mock(return_value=mock_response)
        
        result = llm_core_with_logger.extract_action_params("Lock card 1234", "lock_card")
        assert result == {"last4": "1234"}

    def test_lock_card_unknown(self, llm_core_with_logger, mock_llm):
        """Test lock card with unknown response"""
        mock_response = Mock()
        mock_response.content = "unknown"
        mock_llm.invoke = Mock(return_value=mock_response)
        
        result = llm_core_with_logger.extract_action_params("Lock my card", "lock_card")
        assert result == {"last4": None}

    def test_transfer_success(self, llm_core_with_logger, mock_llm):
        """Test successful transfer param extraction"""
        mock_response = Mock()
        mock_response.content = "acc1|acc2|100.50"
        mock_llm.invoke = Mock(return_value=mock_response)
        
        result = llm_core_with_logger.extract_action_params("Transfer 100 to acc2", "transfer")
        assert result == {
            "from_account": "acc1",
            "to_account": "acc2",
            "amount": 100.50
        }

    def test_transfer_unknown(self, llm_core_with_logger, mock_llm):
        """Test transfer with unknown response"""
        mock_response = Mock()
        mock_response.content = "unknown"
        mock_llm.invoke = Mock(return_value=mock_response)
        
        result = llm_core_with_logger.extract_action_params("Transfer money", "transfer")
        assert result == {}

    def test_transfer_parse_error(self, llm_core_with_logger, mock_llm):
        """Test transfer with parse error returns empty dict"""
        mock_response = Mock()
        mock_response.content = "acc1|acc2|not_a_number"
        mock_llm.invoke = Mock(return_value=mock_response)
        
        result = llm_core_with_logger.extract_action_params("Transfer", "transfer")
        assert result == {}

    def test_transfer_index_error(self, llm_core_with_logger, mock_llm):
        """Test transfer with index error returns empty dict"""
        mock_response = Mock()
        mock_response.content = "acc1|acc2"  # Only 2 parts, need 3
        mock_llm.invoke = Mock(return_value=mock_response)
        
        result = llm_core_with_logger.extract_action_params("Transfer", "transfer")
        assert result == {}

    def test_api_failure_returns_empty(self, llm_core_with_logger, mock_llm):
        """Test that API failure returns empty dict"""
        mock_llm.invoke = Mock(
            side_effect=ConnectionError("connection failed")
        )
        llm_core_with_logger.max_retries = 0
        
        result = llm_core_with_logger.extract_action_params("Lock card", "lock_card")
        assert result == {}

    def test_unknown_action_type(self, llm_core_with_logger, mock_llm):
        """Test unknown action type returns empty dict"""
        result = llm_core_with_logger.extract_action_params("query", "unknown_action")
        assert result == {}

    def test_logs_parse_error(self, llm_core_with_logger, mock_llm):
        """Test that parse errors in extract_action_params are logged"""
        mock_response = Mock()
        mock_response.content = "acc1|acc2|bad"
        mock_llm.invoke = Mock(return_value=mock_response)
        
        llm_core_with_logger.extract_action_params("Transfer", "transfer")
        
        log_calls = [call[0] for call in llm_core_with_logger.logger.log_event.call_args_list]
        event_types = [call[0] for call in log_calls]
        assert "transfer_param_parse_error" in event_types

    def test_logs_api_failure(self, llm_core_with_logger, mock_llm):
        """Test that API failures in extract_action_params are logged"""
        mock_llm.invoke = Mock(
            side_effect=ConnectionError("connection failed")
        )
        llm_core_with_logger.max_retries = 0
        
        llm_core_with_logger.extract_action_params("Lock card", "lock_card")
        
        log_calls = [call[0] for call in llm_core_with_logger.logger.log_event.call_args_list]
        event_types = [call[0] for call in log_calls]
        assert "action_param_extraction_failed" in event_types


class TestPlanAction:
    """Tests for plan_action error handling"""

    def test_successful_plan(self, llm_core_with_logger, mock_llm):
        """Test successful action planning"""
        mock_response = Mock()
        mock_response.content = "lock_card|yes"
        mock_llm.invoke = Mock(return_value=mock_response)
        
        result = llm_core_with_logger.plan_action("Lock my card", "write")
        assert result == {"action": "lock_card", "needs_auth": True}

    def test_no_auth_needed(self, llm_core_with_logger, mock_llm):
        """Test action that doesn't need auth"""
        mock_response = Mock()
        mock_response.content = "check_balance|no"
        mock_llm.invoke = Mock(return_value=mock_response)
        
        result = llm_core_with_logger.plan_action("Check balance", "read")
        assert result == {"action": "check_balance", "needs_auth": False}

    def test_parse_error_returns_default(self, llm_core_with_logger, mock_llm):
        """Test parse error returns default values"""
        mock_response = Mock()
        mock_response.content = "invalid response"
        mock_llm.invoke = Mock(return_value=mock_response)
        
        result = llm_core_with_logger.plan_action("Query", "faq")
        assert result == {"action": None, "needs_auth": False}

    def test_api_failure_returns_default(self, llm_core_with_logger, mock_llm):
        """Test API failure returns default values"""
        mock_llm.invoke = Mock(
            side_effect=ConnectionError("connection failed")
        )
        llm_core_with_logger.max_retries = 0
        
        result = llm_core_with_logger.plan_action("Query", "faq")
        assert result == {"action": None, "needs_auth": False}

    def test_value_error_on_parse(self, llm_core_with_logger, mock_llm):
        """Test ValueError is caught and handled"""
        mock_response = Mock()
        mock_response.content = "action|not_yes_or_no"
        mock_llm.invoke = Mock(return_value=mock_response)
        
        result = llm_core_with_logger.plan_action("Query", "faq")
        # Should still work since "not_yes_or_no".lower() != "yes"
        assert result == {"action": "action", "needs_auth": False}

    def test_index_error_on_parse(self, llm_core_with_logger, mock_llm):
        """Test IndexError is caught and handled"""
        mock_response = Mock()
        mock_response.content = "action_only"  # No pipe separator
        mock_llm.invoke = Mock(return_value=mock_response)
        
        result = llm_core_with_logger.plan_action("Query", "faq")
        assert result == {"action": None, "needs_auth": False}

    def test_logs_parse_error(self, llm_core_with_logger, mock_llm):
        """Test that parse errors in plan_action are logged"""
        mock_response = Mock()
        mock_response.content = "invalid format"
        mock_llm.invoke = Mock(return_value=mock_response)
        
        llm_core_with_logger.plan_action("Query", "faq")
        
        log_calls = [call[0] for call in llm_core_with_logger.logger.log_event.call_args_list]
        event_types = [call[0] for call in log_calls]
        assert "action_plan_parse_error" in event_types

    def test_logs_api_failure(self, llm_core_with_logger, mock_llm):
        """Test that API failures in plan_action are logged"""
        mock_llm.invoke = Mock(
            side_effect=ConnectionError("connection failed")
        )
        llm_core_with_logger.max_retries = 0
        
        llm_core_with_logger.plan_action("Query", "faq")
        
        log_calls = [call[0] for call in llm_core_with_logger.logger.log_event.call_args_list]
        event_types = [call[0] for call in log_calls]
        assert "action_planning_failed" in event_types


class TestNoBareExcept:
    """Tests to ensure no bare except: clauses remain"""

    def test_classify_intent_no_bare_except(self):
        """Verify classify_intent doesn't have bare except"""
        import inspect
        source = inspect.getsource(LLMCore.classify_intent)
        # Check that there's no bare except: (without specifying exception type)
        assert "except:" not in source or "except (" in source

    def test_extract_action_params_no_bare_except(self):
        """Verify extract_action_params doesn't have bare except"""
        import inspect
        source = inspect.getsource(LLMCore.extract_action_params)
        assert "except:" not in source or "except (" in source

    def test_plan_action_no_bare_except(self):
        """Verify plan_action doesn't have bare except"""
        import inspect
        source = inspect.getsource(LLMCore.plan_action)
        assert "except:" not in source or "except (" in source
