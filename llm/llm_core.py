# LLM Core - Mistral AI orchestration
"""LLM orchestration using Mistral AI"""
import os
from langchain_mistralai import ChatMistralAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def _convert_to_basemessage(msg):
    """Convert a message to BaseMessage object if it's a dict.
    
    Args:
        msg: Either a dict with 'role' and 'content' keys, or already a BaseMessage
        
    Returns:
        BaseMessage object (HumanMessage, AIMessage, or SystemMessage)
        or None if the message cannot be converted
    """
    if isinstance(msg, dict):
        role = msg.get("role", "").lower()
        content = msg.get("content", "")
        if role == "user":
            return HumanMessage(content=content)
        elif role == "assistant":
            return AIMessage(content=content)
        elif role == "system":
            return SystemMessage(content=content)
        else:
            return None
    # Already a BaseMessage object
    return msg


def _normalize_message_history(history):
    """Convert a list of messages (dicts or BaseMessage) to BaseMessage objects.
    
    Args:
        history: List of message dicts or BaseMessage objects
        
    Returns:
        List of BaseMessage objects
    """
    normalized = []
    for msg in history:
        converted = _convert_to_basemessage(msg)
        if converted is not None:
            normalized.append(converted)
    return normalized


class LLMCore:
    """Core LLM functionality using Mistral AI"""
    
    def __init__(self, model_name="mistral-small-latest"):
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            raise ValueError("MISTRAL_API_KEY not found in environment")
        
        self.llm = ChatMistralAI(
            model=model_name,
            temperature=0.3,
            mistral_api_key=api_key
        )
    
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
            # Normalize history to ensure all messages are BaseMessage objects
            # This handles both dict-based history (from old sessions) and BaseMessage objects
            normalized_history = _normalize_message_history(conversation_history[-4:])
            messages.extend(normalized_history)
        
        messages.append(HumanMessage(content=query))
        
        response = self.llm.invoke(messages)
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
        response = self.llm.invoke([message])
        
        try:
            intent, confidence = response.content.strip().split("|")
            return {
                "intent": intent.strip(),
                "confidence": float(confidence.strip())
            }
        except:
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
        response = self.llm.invoke([message])
        
        result = response.content.strip()
        
        if action_type == "lock_card":
            return {"last4": result if result != "unknown" else None}
        
        elif action_type == "transfer":
            if result != "unknown":
                parts = result.split("|")
                if len(parts) == 3:
                    return {
                        "from_account": parts[0].strip(),
                        "to_account": parts[1].strip(),
                        "amount": float(parts[2].strip())
                    }
        
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
        response = self.llm.invoke([message])
        
        try:
            action, needs_auth = response.content.strip().split("|")
            return {
                "action": action.strip(),
                "needs_auth": needs_auth.strip().lower() == "yes"
            }
        except:
            return {"action": None, "needs_auth": False}