"""Tests for transaction history intent routing"""
import pytest
import sys
import os
from unittest.mock import Mock, MagicMock, patch

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock the imports before importing the modules
with patch.dict('sys.modules', {
    'langchain_mistralai': MagicMock(),
    'langchain_core.messages': MagicMock(),
    'dotenv': MagicMock(),
}):
    from ui.intent_router import IntentRouter


class TestTransactionIntentRouting:
    """Test cases for transaction intent routing"""
    
    def setup_method(self):
        """Setup test fixtures"""
        # Mock LLM core
        mock_llm = Mock()
        mock_llm.classify_intent = Mock(return_value={"intent": "read", "confidence": 0.9})
        
        # Mock logger
        mock_logger = Mock()
        
        self.router = IntentRouter(mock_llm, mock_logger)
    
    def test_transaction_keywords_classify_as_read(self):
        """Test that transaction keywords are classified as read intent"""
        test_queries = [
            "Show my recent transactions",
            "Show me my transaction history",
            "View my transactions",
            "Check my statement",
            "Show recent transactions",
            "What's my transaction history?",
            "Show me my recent transactions",
            "View transaction history",
        ]
        
        for query in test_queries:
            result = self.router._rule_based_classify(query.lower())
            assert result == "read", f"Failed for query: {query}"
    
    def test_transaction_keywords_in_read_keywords(self):
        """Test that all transaction keywords are in READ_KEYWORDS"""
        expected_keywords = ["transaction", "transactions", "history", "recent", "statement"]
        
        for kw in expected_keywords:
            assert kw in IntentRouter.READ_KEYWORDS, f"Missing keyword: {kw}"
    
    def test_classify_read_intent_with_transaction_query(self):
        """Test full classification with transaction query"""
        # Mock LLM to return low confidence so rule-based kicks in
        mock_llm = Mock()
        mock_llm.classify_intent = Mock(return_value={"intent": "unclear", "confidence": 0.1})
        
        mock_logger = Mock()
        router = IntentRouter(mock_llm, mock_logger)
        
        result = router.classify("Show my recent transactions")
        
        # Since LLM confidence is low (< 0.6), should use rule-based
        assert result["intent"] == "read"
        assert result["needs_action"] is True
    
    def test_route_transaction_query_to_action_handler(self):
        """Test that transaction queries are routed to action handler"""
        result = self.router.route_to_handler("read")
        assert result == "action_handler"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
