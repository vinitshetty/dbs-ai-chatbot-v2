"""Chainlit UI for DBS Banking Agent"""
import warnings
warnings.filterwarnings("ignore", message="No trace in context")

import os
import sys
from pathlib import Path

# Add parent directory to path
PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
sys.path.append(PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(Path(PROJECT_ROOT) / ".env")

import chainlit as cl

from llm.llm_core import LLMCore
from rag.rag_engine import RAGEngine
from core_banking.banking_actions import BankingActions
from intent_router import IntentRouter
from security.safety_filters import SafetyFilter
from audit.logger import AuditLogger
from audit.langwatch_tracker import LangWatchTracker
import time

# Initialize components
llm_core = None
rag_engine = None
intent_router = None
logger = None
langwatch_tracker = None

@cl.on_chat_start
async def start():
    """Initialize chat session"""
    global llm_core, rag_engine, intent_router, logger, langwatch_tracker
    
    # Initialize components
    logger = AuditLogger()
    langwatch_tracker = LangWatchTracker()
    llm_core = LLMCore()
    rag_engine = RAGEngine()
    intent_router = IntentRouter(llm_core, logger)
    
    # Store in session
    cl.user_session.set("user_id", "user123")  # Dummy user
    cl.user_session.set("conversation_history", [])
    cl.user_session.set("authenticated", False)
    
    await cl.Message(
        content="👋 Welcome to DBS Banking Assistant!\n\nI can help you with:\n"
                "- Branch hours and fees\n"
                "- Checking your balance\n"
                "- Viewing transaction history\n"
                "- Locking/unlocking cards\n"
                "- Transferring funds\n\n"
                "How can I assist you today?"
    ).send()

@cl.on_message
async def main(message: cl.Message):
    """Handle user messages"""
    query = message.content
    user_id = cl.user_session.get("user_id")
    session_id = cl.user_session.get("id")
    history = cl.user_session.get("conversation_history")
    
    # Start LangWatch trace
    langwatch_tracker.start_trace(
        user_id=user_id,
        session_id=session_id,
        metadata={"interface": "chainlit", "source": "dbs_banking_agent"}
    )
    
    # Track user message
    langwatch_tracker.track_user_message(query)
    
    # Log query
    logger.log_query(user_id, query, session_id)
    
    start_time = time.time()
    
    try:
        # Safety check - Prompt injection
        injection_check = SafetyFilter.check_injection(query)
        langwatch_tracker.track_safety_check(
            "prompt_injection", 
            injection_check["safe"], 
            query,
            injection_check.get("reason")
        )
        
        if not injection_check["safe"]:
            logger.log_safety_check("injection", False, injection_check["reason"])
            response = ("⚠️ Your message contains content that cannot be processed. "
                       "Please rephrase your question.")
            langwatch_tracker.track_final_response(response, {"blocked": True})
            langwatch_tracker.end_trace()
            await cl.Message(content=response).send()
            return
        
        # Sanitize input
        query = SafetyFilter.sanitize_input(query)
        
        # Classify intent
        intent_result = intent_router.classify(query)
        intent = intent_result["intent"]
        
        langwatch_tracker.track_intent_classification(
            query, 
            intent, 
            intent_result["confidence"]
        )
        
        # Route to handler
        response = await handle_query(query, intent, user_id, history)
        
        # Content moderation on response using Mistral AI
        moderation = SafetyFilter.moderate_content(response)
        langwatch_tracker.track_safety_check(
            "content_moderation",
            moderation["safe"],
            str(response),
            moderation.get("reason")
        )
        
        if not moderation["safe"]:
            logger.log_safety_check("moderation", False, moderation["reason"])
            
            # Log flagged categories for analysis
            if "categories" in moderation:
                logger.log_event("moderation_detail", {
                    "flagged_categories": moderation["categories"],
                    "scores": moderation.get("category_scores", {})
                })
            
            response = "I apologize, but I cannot provide that response. Please ask a different question."
        else:
            logger.log_safety_check("moderation", True)
        
        # Log response
        logger.log_response(response, {"intent": intent})
        
        # Track final response with timing
        processing_time = (time.time() - start_time) * 1000
        langwatch_tracker.track_final_response(
            response,
            {
                "intent": intent,
                "processing_time_ms": processing_time,
                "conversation_turn": len(history) // 2 + 1
            }
        )
        
        # Add custom metrics
        langwatch_tracker.add_custom_metric("response_time_ms", processing_time, "ms")
        langwatch_tracker.add_custom_metric("intent_confidence", intent_result["confidence"])
        
    except Exception as e:
        logger.log_event("error", {"error": str(e)})
        langwatch_tracker.track_error(e, {"query": query, "intent": intent})
        response = "I apologize, but I encountered an error. Please try again."
    
    finally:
        langwatch_tracker.end_trace()
    
    # Update conversation history
    history.append({"role": "user", "content": query})
    history.append({"role": "assistant", "content": response})
    cl.user_session.set("conversation_history", history[-6:])  # Keep last 3 turns
    
    await cl.Message(content=response).send()

async def handle_query(query: str, intent: str, user_id: str, history: list) -> str:
    """Handle query based on intent"""
    
    if intent == "faq":
        return await handle_faq(query, history)
    
    elif intent in ["read", "write"]:
        return await handle_action(query, intent, user_id)
    
    else:
        return ("I'm not quite sure how to help with that. "
                "Could you please rephrase? You can ask about:\n"
                "- Branch hours, fees, policies\n"
                "- Account balances\n"
                "- Transaction history\n"
                "- Card management")

async def handle_faq(query: str, history: list) -> str:
    """Handle FAQ queries using RAG"""
    
    # Retrieve relevant context with timing
    start_time = time.time()
    context = rag_engine.get_context(query, n_results=3)
    retrieval_time = (time.time() - start_time) * 1000
    
    results = rag_engine.retrieve(query)
    logger.log_rag_retrieval(query, results)
    
    # Track RAG retrieval in LangWatch
    langwatch_tracker.track_rag_retrieval(
        query, 
        results, 
        retrieval_time_ms=retrieval_time
    )
    
    # Generate response
    start_llm = time.time()
    response = llm_core.generate_response(context, query, history)
    llm_time = (time.time() - start_llm) * 1000
    
    # Track LLM call in LangWatch
    langwatch_tracker.track_llm_call(
        prompt=f"Context: {context}\n\nQuery: {query}",
        response=response,
        model="mistral-small-latest",
        metadata={
            "generation_time_ms": llm_time,
            "context_length": len(context),
            "num_retrieved_docs": len(results)
        }
    )
    
    return response

async def handle_action(query: str, intent: str, user_id: str) -> str:
    """Handle action queries"""
    
    # Plan action
    start_plan = time.time()
    plan = llm_core.plan_action(query, intent)
    plan_time = (time.time() - start_plan) * 1000
    
    action_name = plan.get("action")
    needs_auth = plan.get("needs_auth")
    
    # Track planning in LangWatch
    langwatch_tracker.track_llm_call(
        prompt=f"Plan action for: {query} (intent: {intent})",
        response=str(plan),
        model="mistral-small-latest",
        metadata={
            "task": "action_planning",
            "planning_time_ms": plan_time
        }
    )
    
    if not action_name:
        return "I couldn't determine the specific action you want to perform. Could you please be more specific?"
    
    # Execute based on action type
    if action_name == "check_balance":
        start_exec = time.time()
        result = BankingActions.check_balance(user_id)
        exec_time = (time.time() - start_exec) * 1000
        
        logger.log_action(action_name, {}, result)
        langwatch_tracker.track_action_execution(
            action_name, 
            {}, 
            result, 
            execution_time_ms=exec_time
        )
        
        if result["success"]:
            return (f"💰 Your {result['account_type']} account balance is "
                   f"**${result['balance']:.2f}**\n"
                   f"Account: {result['account_number']}")
        else:
            return f"❌ {result['error']}"
    
    elif action_name in ["lock_card", "unlock_card"]:
        # Get authentication if needed
        if needs_auth and not cl.user_session.get("authenticated"):
            is_auth = await request_dummy_auth()
            langwatch_tracker.add_custom_metric("auth_required", True)
            langwatch_tracker.add_custom_metric("auth_completed", is_auth)
            
            if not is_auth:
                return "❌ Authentication required to proceed with this action."
        
        # Extract card number
        params = llm_core.extract_action_params(query, "lock_card")
        last4 = params.get("last4")
        
        if not last4:
            return "Please provide the last 4 digits of your card. For example: 'Lock card ending in 4532'"
        
        # Execute action
        start_exec = time.time()
        if action_name == "lock_card":
            result = BankingActions.lock_card(user_id, last4)
        else:
            result = BankingActions.unlock_card(user_id, last4)
        exec_time = (time.time() - start_exec) * 1000
        
        logger.log_action(action_name, {"last4": last4}, result)
        langwatch_tracker.track_action_execution(
            action_name,
            {"last4": last4},
            result,
            execution_time_ms=exec_time
        )
        
        if result["success"]:
            return f"✅ {result['message']}"
        else:
            return f"❌ {result.get('error') or result.get('message')}"
    
    elif action_name == "transaction_history":
        # Extract parameters
        params = llm_core.extract_action_params(query, "transaction_history")
        
        # Get filter parameters
        txn_type = params.get("type")
        start_date = params.get("start_date")
        end_date = params.get("end_date")
        min_amount = params.get("min_amount")
        max_amount = params.get("max_amount")
        limit = params.get("limit", 10)
        
        # Parse relative dates if present
        if start_date:
            start_date = BankingActions._parse_date(start_date)
        if end_date:
            end_date = BankingActions._parse_date(end_date)
        
        # Execute action
        start_exec = time.time()
        result = BankingActions.get_transactions(
            user_id,
            transaction_type=txn_type,
            start_date=start_date,
            end_date=end_date,
            min_amount=min_amount,
            max_amount=max_amount,
            limit=limit
        )
        exec_time = (time.time() - start_exec) * 1000
        
        logger.log_action("transaction_history", params, result)
        langwatch_tracker.track_action_execution(
            "transaction_history",
            params,
            result,
            execution_time_ms=exec_time
        )
        
        if result["success"]:
            transactions = result.get("transactions", [])
            if not transactions:
                return "No transactions found matching your criteria."
            
            # Format as table
            response = "📋 **Transaction History**\n\n"
            response += f"Showing {result.get('returned_count', len(transactions))} of {result.get('total_count', len(transactions))} transactions\n\n"
            
            response += "| Date | Type | Description | Amount | Balance |\n"
            response += "|------|------|-------------|--------|---------|\n"
            
            for txn in transactions:
                txn_date = txn.get("date", "N/A")
                txn_type = txn.get("type", "N/A").upper()
                description = txn.get("description", "N/A")
                amount = f"${txn.get('amount', 0):.2f}"
                balance = f"${txn.get('balance', 0):.2f}"
                
                response += f"| {txn_date} | {txn_type} | {description} | {amount} | {balance} |\n"
            
            return response
        else:
            return f"❌ {result.get('error') or result.get('message')}"
    
    return f"Action '{action_name}' is not yet implemented in this prototype."

async def request_dummy_auth() -> bool:
    """Request dummy authentication (prototype)"""
    res = await cl.AskActionMessage(
        content="🔐 This action requires authentication. Proceed?",
        actions=[
            cl.Action(name="yes", value="yes", label="✅ Authenticate"),
            cl.Action(name="no", value="no", label="❌ Cancel"),
        ],
    ).send()
    
    if res and res.get("value") == "yes":
        cl.user_session.set("authenticated", True)
        return True
    
    return False