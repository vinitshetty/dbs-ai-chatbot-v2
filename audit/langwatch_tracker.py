"""
LangWatch integration for conversation tracking and observability
FIXED: metadata/output schema-safe for LangWatch
"""

import os
import json
from typing import Optional, Dict, Any, List
import langwatch


def _to_str(value: Any) -> str:
    """Safely serialize any object to string"""
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    return json.dumps(value, default=str)


def _safe_metadata(data: Optional[Dict]) -> Dict[str, str]:
    """Flatten metadata to LangWatch-supported types"""
    safe = {}
    for k, v in (data or {}).items():
        safe[k] = _to_str(v)
    return safe


class LangWatchTracker:
    """Track conversations, RAG, LLM calls with LangWatch (schema-safe)"""

    def __init__(self):
        api_key = os.getenv("LANGWATCH_API_KEY")
        if api_key:
            langwatch.setup(api_key=api_key)
            self.enabled = True
            print("✅ LangWatch tracking enabled")
        else:
            self.enabled = False
            print("⚠️ LangWatch API key not found - tracking disabled")

        self.current_trace = None

    # ----------------------------
    # Trace lifecycle
    # ----------------------------

    def start_trace(self, user_id: str, session_id: str, metadata: Dict = None):
        if not self.enabled:
            return

        try:
            self.current_trace = langwatch.trace(
                user_id=user_id,
                thread_id=session_id,
                metadata=_safe_metadata(metadata),
            )
        except Exception as e:
            print(f"LangWatch trace start error: {e}")

    def end_trace(self):
        self.current_trace = None

    # ----------------------------
    # User & assistant messages
    # ----------------------------

    def track_user_message(self, message: str, metadata: Dict = None):
        if not self.enabled or not self.current_trace:
            return

        try:
            self.current_trace.update(
                input=message,
                metadata=_safe_metadata(metadata),
            )
        except Exception as e:
            print(f"LangWatch user message error: {e}")

    def track_final_response(self, response: str, metadata: Dict = None):
        if not self.enabled or not self.current_trace:
            return

        try:
            self.current_trace.update(
                output=response,
                metadata=_safe_metadata(metadata),
            )
        except Exception as e:
            print(f"LangWatch response tracking error: {e}")

    # ----------------------------
    # RAG tracking
    # ----------------------------

    def track_rag_retrieval(
        self,
        query: str,
        results: List[Dict],
        retrieval_time_ms: float = None,
    ):
        if not self.enabled:
            return

        try:
            with langwatch.span(name="rag_retrieval", type="rag") as span:
                span.update(
                    input=query,
                    output=f"{len(results)} documents retrieved",
                    metadata={
                        "num_results": str(len(results)),
                        "retrieval_time_ms": _to_str(retrieval_time_ms),
                    },
                )

                rag_contexts = []
                for i, result in enumerate(results):
                    rag_contexts.append(_to_str(result.get("content", "")))

                if rag_contexts:
                    span.update(contexts=rag_contexts)
        except Exception as e:
            print(f"LangWatch RAG tracking error: {e}")

    # ----------------------------
    # LLM tracking
    # ----------------------------

    def track_llm_call(
        self,
        prompt: str,
        response: str,
        model: str,
        metadata: Dict = None,
    ):
        if not self.enabled:
            return

        try:
            with langwatch.span(name="llm_generation", type="llm") as span:
                span.update(
                    model=model,
                    input=prompt,
                    output=response,
                    metadata=_safe_metadata(metadata),
                )
        except Exception as e:
            print(f"LangWatch LLM tracking error: {e}")

    # ----------------------------
    # Intent classification
    # ----------------------------

    def track_intent_classification(
        self,
        query: str,
        intent: str,
        confidence: float,
        method: str = "hybrid",
    ):
        if not self.enabled:
            return

        try:
            with langwatch.span(name="intent_classification", type="chain") as span:
                span.update(
                    input=query,
                    output=f"intent={intent}, confidence={confidence}",
                    metadata={
                        "intent": intent,
                        "confidence": str(confidence),
                        "method": method,
                    },
                )
        except Exception as e:
            print(f"LangWatch intent tracking error: {e}")

    # ----------------------------
    # Tool / action execution
    # ----------------------------

    def track_action_execution(
        self,
        action_name: str,
        params: Dict,
        result: Dict,
        execution_time_ms: float = None,
    ):
        if not self.enabled:
            return

        try:
            with langwatch.span(name=f"action_{action_name}", type="tool") as span:
                span.update(
                    input=_to_str(params),
                    output=_to_str(result),
                    metadata={
                        "action_name": action_name,
                        "success": str(bool(result.get("success", False))),
                        "execution_time_ms": _to_str(execution_time_ms),
                    },
                )
        except Exception as e:
            print(f"LangWatch action tracking error: {e}")

    # ----------------------------
    # Safety / guardrails
    # ----------------------------

    def track_safety_check(
        self,
        check_type: str,
        passed: bool,
        input_text: str,
        reason: str = None,
    ):
        if not self.enabled:
            return

        try:
            with langwatch.span(name=f"safety_{check_type}", type="guardrail") as span:
                span.update(
                    input=input_text,
                    output=f"passed={passed}, reason={reason}",
                    metadata={
                        "check_type": check_type,
                        "passed": str(passed),
                    },
                )
        except Exception as e:
            print(f"LangWatch safety tracking error: {e}")

    # ----------------------------
    # Errors & metrics
    # ----------------------------

    def track_error(self, error: Exception, context: Dict = None):
        if not self.enabled or not self.current_trace:
            return

        try:
            self.current_trace.update(
                error=str(error),
                metadata={
                    "error_type": type(error).__name__,
                    "context": _to_str(context),
                },
            )
        except Exception as e:
            print(f"LangWatch error tracking error: {e}")

    def add_custom_metric(self, name: str, value: Any, unit: str = None):
        if not self.enabled or not self.current_trace:
            return

        try:
            meta = {name: _to_str(value)}
            if unit:
                meta[f"{name}_unit"] = unit

            self.current_trace.update(metadata=meta)
        except Exception as e:
            print(f"LangWatch metric tracking error: {e}")
