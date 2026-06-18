# LLM Core - Mistral AI orchestration
"""LLM orchestration using Mistral AI"""
import os
import time
from datetime import datetime
from typing import Optional, Any
from langchain_mistralai import ChatMistralAI
from langchain_core.messages import HumanMessage, SystemMessage

from dotenv import load_dotenv
load_dotenv()


class LLMCore:
    """Core LLM functionality using Mistral AI"""
    
    def __init__(self, model_name: str = "mistral-small-latest",
                 max_retries: int = 3,
                 timeout: int = 30,
                 retry_delay: float = 1.0,
                 logger: Optional[Any] = None):
        """
        Initialize LLMCore with Mistral AI configuration.
        
        Args:
            model_name: Name of the Mistral model to use
            max_retries: Maximum number of retry attempts for API calls
            timeout: Request timeout in seconds
            retry_delay: Base delay between retries (exponential backoff)
            logger: Optional AuditLogger instance for error logging
        """
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            raise ValueError("MISTRAL_API_KEY not found in environment")
        
        self.max_retries = max_retries
        self.timeout = timeout
        self.retry_delay = retry_delay
        self.logger = logger
        
        self.llm = ChatMistralAI(
            model=model_name,
            temperature=0.3,
            mistral_api_key=api_key,
            timeout=timeout,
            max_retries=max_retries
        )
    
    def _invoke_with_retry(self, messages: list, operation_name: str = "llm_invoke") -> Any:
        """
        Invoke LLM with retry logic and error handling.
        
        Args:
            messages: List of messages to send to LLM
            operation_name: Name of operation for logging (e.g., 'generate_response')
        
        Returns:
            LLM response object or None on failure
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                response = self.llm.invoke(messages)
                return response
                
            except (ValueError, IndexError) as e:
                # Parse errors - re-raise for method-specific handling
                raise
                
            except Exception as e:
                last_exception = e
                
                # Log the error
                if self.logger:
                    self.logger.log_event("llm_api_error", {
                        "operation": operation_name,
                        "attempt": attempt + 1,
                        "max_retries": self.max_retries,
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                        "timestamp": datetime.now().isoformat()
                    })
                
                # Retry on transient errors
                if attempt < self.max_retries:
                    error_type = type(e).__name__
                    
                    # Check if this is a retryable error
                    retryable_errors = [
                        'RateLimitError', 'TimeoutError', 'ConnectionError',
                        'Timeout', 'ConnectTimeout', 'ReadTimeout'
                    ]
                    
                    if any(retryable in error_type for retryable in retryable_errors):
                        # Exponential backoff
                        delay = self.retry_delay * (2 ** attempt)
                        if self.logger:
                            self.logger.log_event("llm_retry", {
                                "operation": operation_name,
                                "attempt": attempt + 1,
                                "delay_seconds": delay,
                                "error_type": error_type
                            })
                        time.sleep(delay)
                        continue
                    
                    # Non-retryable error (e.g., invalid API key, auth error)
                    # Log and fall through to return None
                    break
                
                break  # No more retries
        
        # All retries exhausted or non-retryable error
        if self.logger:
            self.logger.log_event("llm_api_failure", {
                "operation": operation_name,
                "error_type": type(last_exception).__name__ if last_exception else "Unknown",
                "error_message": str(last_exception) if last_exception else "No exception recorded",
                "retries_exhausted": True
            })
        
        return None
    
    def generate_response(self, context: str, query: str, 
                         conversation_history: list = None) -> str:
        """Generate response using context from RAG"""
        
        system_prompt = """You are a helpful DBS Bank assistant. Use the provided context to answer questions accurately.
        
Rules:
- Be concise and friendly
- Use information from context only
- If unsure, say so
- For actions, confirm details clearly
- Maintain professional banking tone

Context:
{context}
"""
        
        messages = [
            SystemMessage(content=system_prompt.format(context=context))
        ]
        
        # Add conversation history if available
        if conversation_history:
            messages.extend(conversation_history[-4:])  # Last 2 turns
        
        messages.append(HumanMessage(content=query))
        
        # Use retry wrapper
        response = self._invoke_with_retry(messages, "generate_response")
        
        if response is None:
            # Return user-friendly fallback
            fallback = ("I apologize, but I'm having trouble connecting to the AI service. "
                       "Please try again in a moment.")
            if self.logger:
                self.logger.log_event("fallback_response", {
                    "operation": "generate_response",
                    "reason": "api_failure"
                })
            return fallback
        
        return response.content
    
    def classify_intent(self, query: str) -> dict:
        """Classify user intent"""
        
        prompt = """Classify the user query into ONE of these intents:
- faq: General questions about bank services, hours, fees, policies
- read: Check balance, view account info, check transaction history
- write: Lock/unlock card, transfer money, update details
- unclear: Cannot determine intent

Query: {query}

Respond ONLY with: intent|confidence
Example: faq|0.9"""
        
        message = HumanMessage(content=prompt.format(query=query))
        response = self._invoke_with_retry([message], "classify_intent")
        
        if response is None:
            # API failure - return fallback with low confidence
            if self.logger:
                self.logger.log_event("intent_classification_failed", {
                    "reason": "api_failure",
                    "query": query[:100]  # Truncate for logging
                })
            return {"intent": "unclear", "confidence": 0.0}
        
        try:
            intent, confidence = response.content.strip().split("|")
            return {
                "intent": intent.strip(),
                "confidence": float(confidence.strip())
            }
        except (ValueError, IndexError) as e:
            # Parse error - log and return fallback
            if self.logger:
                self.logger.log_event("intent_parse_error", {
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "query": query[:100],
                    "raw_response": response.content[:200] if response else None
                })
            return {"intent": "unclear", "confidence": 0.0}
    
    def extract_action_params(self, query: str, action_type: str) -> dict:
        """Extract parameters for actions"""
        
        prompts = {
            "lock_card": "Extract the last 4 digits of the card from: {query}\nRespond with ONLY the 4 digits or 'unknown'",
            "transfer": "Extract from_account, to_account, and amount from: {query}\nFormat: from|to|amount or 'unknown'"
        }
        
        if action_type not in prompts:
            return {}
        
        message = HumanMessage(content=prompts[action_type].format(query=query))
        response = self._invoke_with_retry([message], "extract_action_params")
        
        if response is None:
            if self.logger:
                self.logger.log_event("action_param_extraction_failed", {
                    "action_type": action_type,
                    "reason": "api_failure",
                    "query": query[:100]
                })
            return {}
        
        result = response.content.strip()
        
        if action_type == "lock_card":
            return {"last4": result if result != "unknown" else None}
        
        elif action_type == "transfer":
            if result != "unknown":
                try:
                    parts = result.split("|")
                    if len(parts) == 3:
                        return {
                            "from_account": parts[0].strip(),
                            "to_account": parts[1].strip(),
                            "amount": float(parts[2].strip())
                        }
                except (ValueError, IndexError) as e:
                    if self.logger:
                        self.logger.log_event("transfer_param_parse_error", {
                            "error_type": type(e).__name__,
                            "error_message": str(e),
                            "raw_result": result,
                            "query": query[:100]
                        })
            return {}
        
        return {}
    
    def plan_action(self, query: str, intent: str) -> dict:
        """Plan action steps (simple CrewAI-like planning)"""
        
        prompt = """Given the query and intent, plan the action:

Query: {query}
Intent: {intent}

Determine:
1. Action name (lock_card, unlock_card, check_balance, transfer_funds)
2. Required parameters
3. Needs authentication? (yes/no)

Format: action_name|needs_auth
Example: lock_card|yes"""
        
        message = HumanMessage(content=prompt.format(query=query, intent=intent))
        response = self._invoke_with_retry([message], "plan_action")
        
        if response is None:
            if self.logger:
                self.logger.log_event("action_planning_failed", {
                    "reason": "api_failure",
                    "query": query[:100],
                    "intent": intent
                })
            return {"action": None, "needs_auth": False}
        
        try:
            action, needs_auth = response.content.strip().split("|")
            return {
                "action": action.strip(),
                "needs_auth": needs_auth.strip().lower() == "yes"
            }
        except (ValueError, IndexError) as e:
            if self.logger:
                self.logger.log_event("action_plan_parse_error", {
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "query": query[:100],
                    "intent": intent,
                    "raw_response": response.content[:200]
                })
            return {"action": None, "needs_auth": False}
