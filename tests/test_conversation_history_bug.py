"""Tests for conversation history bug fix"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage


def test_serialize_deserialize_message_history():
    """Test serialization and deserialization helpers"""
    from ui.chainlit_app import _serialize_message_history, _deserialize_message_history
    
    # Test with BaseMessage objects
    basemessage_history = [
        HumanMessage(content="What is my balance?"),
        AIMessage(content="Your balance is $100"),
        HumanMessage(content="What about fees?"),
        AIMessage(content="Fees are low")
    ]
    
    # Serialize
    serialized = _serialize_message_history(basemessage_history)
    assert len(serialized) == 4
    assert all(isinstance(msg, dict) for msg in serialized)
    assert serialized[0] == {"role": "user", "content": "What is my balance?"}
    assert serialized[1] == {"role": "assistant", "content": "Your balance is $100"}
    
    # Deserialize back
    deserialized = _deserialize_message_history(serialized)
    assert len(deserialized) == 4
    assert isinstance(deserialized[0], HumanMessage)
    assert isinstance(deserialized[1], AIMessage)
    assert deserialized[0].content == "What is my balance?"
    assert deserialized[1].content == "Your balance is $100"
    
    # Test roundtrip
    roundtrip = _serialize_message_history(deserialized)
    assert roundtrip == serialized


def test_serialize_mixed_history():
    """Test serialization with mixed dict and BaseMessage"""
    from ui.chainlit_app import _serialize_message_history, _deserialize_message_history
    
    mixed_history = [
        {"role": "user", "content": "What is my balance?"},
        AIMessage(content="Your balance is $100"),
        HumanMessage(content="What about fees?"),
        {"role": "assistant", "content": "Fees are low"}
    ]
    
    # Serialize
    serialized = _serialize_message_history(mixed_history)
    assert all(isinstance(msg, dict) for msg in serialized)
    
    # Deserialize
    deserialized = _deserialize_message_history(serialized)
    assert all(isinstance(msg, (HumanMessage, AIMessage)) for msg in deserialized)


def test_generate_response_with_dict_history():
    """Test that generate_response handles dict-based history correctly"""
    from llm.llm_core import LLMCore
    
    # Setup mock LLM
    mock_llm = Mock()
    mock_llm.invoke = Mock(return_value=Mock(content="Test response"))
    
    llm_core = LLMCore()
    llm_core.llm = mock_llm
    
    # Dict-based history (the bug scenario)
    dict_history = [
        {"role": "user", "content": "What is my balance?"},
        {"role": "assistant", "content": "Your balance is $100"},
        {"role": "user", "content": "What about fees?"},
        {"role": "assistant", "content": "Fees are low"}
    ]
    
    # This should NOT raise an error - dicts should be converted to BaseMessage
    result = llm_core.generate_response("context here", "new query", dict_history)
    
    # Verify the result
    assert result == "Test response"
    
    # Verify that invoke was called with proper BaseMessage objects
    call_args = mock_llm.invoke.call_args[0][0]
    
    # Check that all messages in the call are BaseMessage objects or SystemMessage
    for msg in call_args:
        assert isinstance(msg, (SystemMessage, HumanMessage, AIMessage)), \
            f"Expected BaseMessage, got {type(msg)}: {msg}"


def test_generate_response_with_basemessage_history():
    """Test that generate_response handles BaseMessage history correctly"""
    from llm.llm_core import LLMCore
    
    # Setup mock LLM
    mock_llm = Mock()
    mock_llm.invoke = Mock(return_value=Mock(content="Test response"))
    
    llm_core = LLMCore()
    llm_core.llm = mock_llm
    
    # BaseMessage-based history (the fixed scenario)
    basemessage_history = [
        HumanMessage(content="What is my balance?"),
        AIMessage(content="Your balance is $100"),
        HumanMessage(content="What about fees?"),
        AIMessage(content="Fees are low")
    ]
    
    result = llm_core.generate_response("context here", "new query", basemessage_history)
    
    assert result == "Test response"
    
    # Verify that invoke was called with proper BaseMessage objects
    call_args = mock_llm.invoke.call_args[0][0]
    
    for msg in call_args:
        assert isinstance(msg, (SystemMessage, HumanMessage, AIMessage)), \
            f"Expected BaseMessage, got {type(msg)}: {msg}"


def test_generate_response_with_mixed_history():
    """Test that generate_response handles mixed dict and BaseMessage history"""
    from llm.llm_core import LLMCore
    
    # Setup mock LLM
    mock_llm = Mock()
    mock_llm.invoke = Mock(return_value=Mock(content="Test response"))
    
    llm_core = LLMCore()
    llm_core.llm = mock_llm
    
    # Mixed history (transition scenario)
    mixed_history = [
        {"role": "user", "content": "What is my balance?"},
        {"role": "assistant", "content": "Your balance is $100"},
        HumanMessage(content="What about fees?"),
        AIMessage(content="Fees are low")
    ]
    
    result = llm_core.generate_response("context here", "new query", mixed_history)
    
    assert result == "Test response"
    
    # Verify that invoke was called with proper BaseMessage objects
    call_args = mock_llm.invoke.call_args[0][0]
    
    for msg in call_args:
        assert isinstance(msg, (SystemMessage, HumanMessage, AIMessage)), \
            f"Expected BaseMessage, got {type(msg)}: {msg}"


def test_generate_response_with_empty_history():
    """Test that generate_response handles empty/None history"""
    from llm.llm_core import LLMCore
    
    # Setup mock LLM
    mock_llm = Mock()
    mock_llm.invoke = Mock(return_value=Mock(content="Test response"))
    
    llm_core = LLMCore()
    llm_core.llm = mock_llm
    
    # Empty history
    result = llm_core.generate_response("context here", "new query", [])
    assert result == "Test response"
    
    # None history
    result = llm_core.generate_response("context here", "new query", None)
    assert result == "Test response"


def test_generate_response_truncates_history():
    """Test that only last 4 messages are used from history"""
    from llm.llm_core import LLMCore
    
    # Setup mock LLM
    mock_llm = Mock()
    mock_llm.invoke = Mock(return_value=Mock(content="Test response"))
    
    llm_core = LLMCore()
    llm_core.llm = mock_llm
    
    # Long history - should only use last 4
    long_history = [
        {"role": "user", "content": f"Message {i}"}
        if i % 2 == 0 else {"role": "assistant", "content": f"Response {i}"}
        for i in range(20)
    ]
    
    result = llm_core.generate_response("context here", "new query", long_history)
    
    # Verify the call
    call_args = mock_llm.invoke.call_args[0][0]
    
    # Should have system message + 4 history + 1 user query = 6 total
    # (SystemMessage + 4 from history + HumanMessage for new query)
    assert len(call_args) == 6


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
