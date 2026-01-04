# Audit Logger - JSONL logging
"""Simple logging and audit trail"""
import json
import os
from datetime import datetime
from pathlib import Path

class AuditLogger:
    """Log all queries, intents, actions, and responses"""
    
    def __init__(self, log_dir="logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.session_file = self.log_dir / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
    
    def log_event(self, event_type: str, data: dict):
        """Log an event to JSONL file"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "data": data
        }
        
        with open(self.session_file, "a") as f:
            f.write(json.dumps(event) + "\n")
    
    def log_query(self, user_id: str, query: str, session_id: str):
        """Log user query"""
        self.log_event("query", {
            "user_id": user_id,
            "query": query,
            "session_id": session_id
        })
    
    def log_intent(self, intent: str, confidence: float):
        """Log classified intent"""
        self.log_event("intent", {
            "intent": intent,
            "confidence": confidence
        })
    
    def log_rag_retrieval(self, query: str, results: list):
        """Log RAG retrieval results"""
        self.log_event("rag_retrieval", {
            "query": query,
            "num_results": len(results),
            "results": results
        })
    
    def log_action(self, action_name: str, params: dict, result: dict):
        """Log action execution"""
        self.log_event("action", {
            "action": action_name,
            "params": params,
            "result": result
        })
    
    def log_response(self, response: str, metadata: dict = None):
        """Log final response"""
        self.log_event("response", {
            "response": response,
            "metadata": metadata or {}
        })
    
    def log_safety_check(self, check_type: str, passed: bool, reason: str = None):
        """Log safety checks"""
        self.log_event("safety_check", {
            "check_type": check_type,
            "passed": passed,
            "reason": reason
        })