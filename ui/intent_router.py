# Intent Router - Query classification
"""Intent routing logic"""
from llm.llm_core import LLMCore
from audit.logger import AuditLogger

class IntentRouter:
    """Routes queries to appropriate handlers"""
    
    # Keywords for simple rule-based classification
    FAQ_KEYWORDS = ["what", "when", "where", "how", "fee", "hours", "branch", "policy"]
    READ_KEYWORDS = ["check", "balance", "show", "view", "status"]
    WRITE_KEYWORDS = ["lock", "unlock", "transfer", "send", "pay", "update", "change"]
    
    def __init__(self, llm_core: LLMCore, logger: AuditLogger):
        self.llm = llm_core
        self.logger = logger
        # Ensure llm_core has the logger
        if not llm_core.logger:
            llm_core.logger = logger
    
    def classify(self, query: str) -> dict:
        """Classify query using rules + LLM"""
        query_lower = query.lower()
        
        # Rule-based pre-classification (fast path)
        rule_intent = self._rule_based_classify(query_lower)
        
        # Use LLM for final decision
        llm_result = self.llm.classify_intent(query)
        
        # Combine results (LLM takes precedence if confidence > 0.6)
        if llm_result["confidence"] > 0.6:
            intent = llm_result["intent"]
            confidence = llm_result["confidence"]
        else:
            intent = rule_intent
            confidence = 0.5
        
        # Log intent
        self.logger.log_intent(intent, confidence)
        
        return {
            "intent": intent,
            "confidence": confidence,
            "needs_action": intent in ["read", "write"]
        }
    
    def _rule_based_classify(self, query_lower: str) -> str:
        """Simple rule-based classification"""
        
        # Check for write actions (highest priority)
        if any(kw in query_lower for kw in self.WRITE_KEYWORDS):
            return "write"
        
        # Check for read actions
        if any(kw in query_lower for kw in self.READ_KEYWORDS):
            return "read"
        
        # Check for FAQ
        if any(kw in query_lower for kw in self.FAQ_KEYWORDS):
            return "faq"
        
        return "unclear"
    
    def route_to_handler(self, intent: str) -> str:
        """Return handler type for intent"""
        handlers = {
            "faq": "rag_handler",
            "read": "action_handler",
            "write": "action_handler",
            "unclear": "fallback_handler"
        }
        return handlers.get(intent, "fallback_handler")