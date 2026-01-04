# LangWatch Tracker - Observability
"""LangWatch integration for conversation tracking and observability"""
import os
from typing import Optional, Dict, Any, List
import langwatch

class LangWatchTracker:
    """Track all conversations, RAG retrievals, and LLM calls with LangWatch"""
    
    def __init__(self):
        api_key = os.getenv("LANGWATCH_API_KEY")
        if api_key:
            langwatch.api_key = api_key
            self.enabled = True
            print("✅ LangWatch tracking enabled")
        else:
            self.enabled = False
            print("⚠️ LangWatch API key not found - tracking disabled")
        
        self.current_trace = None
        self.current_span = None
    
    def start_trace(self, user_id: str, session_id: str, metadata: Dict = None):
        """Start a new trace for a conversation turn"""
        if not self.enabled:
            return
        
        try:
            self.current_trace = langwatch.get_current_trace()
            if not self.current_trace:
                self.current_trace = langwatch.trace(
                    user_id=user_id,
                    thread_id=session_id,
                    metadata=metadata or {}
                )
        except Exception as e:
            print(f"LangWatch trace start error: {e}")
    
    def track_user_message(self, message: str, metadata: Dict = None):
        """Track user input message"""
        if not self.enabled or not self.current_trace:
            return
        
        try:
            langwatch.get_current_trace().update(
                input=message,
                metadata=metadata or {}
            )
        except Exception as e:
            print(f"LangWatch user message error: {e}")
    
    def track_rag_retrieval(self, query: str, results: List[Dict], 
                           retrieval_time_ms: float = None):
        """Track RAG retrieval operation"""
        if not self.enabled:
            return
        
        try:
            with langwatch.span(
                name="rag_retrieval",
                type="rag"
            ) as span:
                span.update(
                    input=query,
                    output=results,
                    metadata={
                        "num_results": len(results),
                        "retrieval_time_ms": retrieval_time_ms
                    }
                )
                
                # Track each retrieved document
                for i, result in enumerate(results):
                    span.add_context(
                        content=result.get("content", ""),
                        metadata={
                            "rank": i + 1,
                            **result.get("metadata", {})
                        }
                    )
        except Exception as e:
            print(f"LangWatch RAG tracking error: {e}")
    
    def track_llm_call(self, prompt: str, response: str, 
                       model: str, metadata: Dict = None):
        """Track LLM generation call"""
        if not self.enabled:
            return
        
        try:
            with langwatch.span(
                name="llm_generation",
                type="llm"
            ) as span:
                span.update(
                    model=model,
                    input=prompt,
                    output=response,
                    metadata=metadata or {}
                )
        except Exception as e:
            print(f"LangWatch LLM tracking error: {e}")
    
    def track_intent_classification(self, query: str, intent: str, 
                                    confidence: float, method: str = "hybrid"):
        """Track intent classification"""
        if not self.enabled:
            return
        
        try:
            with langwatch.span(
                name="intent_classification",
                type="chain"
            ) as span:
                span.update(
                    input=query,
                    output={"intent": intent, "confidence": confidence},
                    metadata={
                        "classification_method": method,
                        "confidence_score": confidence
                    }
                )
        except Exception as e:
            print(f"LangWatch intent tracking error: {e}")
    
    def track_action_execution(self, action_name: str, params: Dict, 
                              result: Dict, execution_time_ms: float = None):
        """Track banking action execution"""
        if not self.enabled:
            return
        
        try:
            with langwatch.span(
                name=f"action_{action_name}",
                type="tool"
            ) as span:
                span.update(
                    input=params,
                    output=result,
                    metadata={
                        "action_name": action_name,
                        "success": result.get("success", False),
                        "execution_time_ms": execution_time_ms
                    }
                )
        except Exception as e:
            print(f"LangWatch action tracking error: {e}")
    
    def track_safety_check(self, check_type: str, passed: bool, 
                          input_text: str, reason: str = None):
        """Track safety filter checks"""
        if not self.enabled:
            return
        
        try:
            with langwatch.span(
                name=f"safety_{check_type}",
                type="guardrail"
            ) as span:
                span.update(
                    input=input_text,
                    output={"passed": passed, "reason": reason},
                    metadata={
                        "check_type": check_type,
                        "passed": passed
                    }
                )
        except Exception as e:
            print(f"LangWatch safety tracking error: {e}")
    
    def track_final_response(self, response: str, metadata: Dict = None):
        """Track final response to user"""
        if not self.enabled:
            return
        
        try:
            langwatch.get_current_trace().update(
                output=response,
                metadata=metadata or {}
            )
        except Exception as e:
            print(f"LangWatch response tracking error: {e}")
    
    def track_error(self, error: Exception, context: Dict = None):
        """Track errors in the conversation flow"""
        if not self.enabled:
            return
        
        try:
            langwatch.get_current_trace().update(
                error=str(error),
                metadata={
                    "error_type": type(error).__name__,
                    "context": context or {}
                }
            )
        except Exception as e:
            print(f"LangWatch error tracking error: {e}")
    
    def add_custom_metric(self, name: str, value: Any, unit: str = None):
        """Add custom metrics to current trace"""
        if not self.enabled:
            return
        
        try:
            metadata = {name: value}
            if unit:
                metadata[f"{name}_unit"] = unit
            
            langwatch.get_current_trace().update(
                metadata=metadata
            )
        except Exception as e:
            print(f"LangWatch metric tracking error: {e}")
    
    def end_trace(self):
        """End current trace"""
        if not self.enabled:
            return
        
        try:
            # Trace is automatically ended by LangWatch
            self.current_trace = None
        except Exception as e:
            print(f"LangWatch trace end error: {e}")