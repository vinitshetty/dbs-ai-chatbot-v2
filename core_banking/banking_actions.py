# Banking Actions - Simulated operations
"""Simulated banking actions (prototype - no real APIs)"""
from typing import Dict, Any
import random
from datetime import datetime


class BankingActions:
    """Dummy banking actions for prototype"""
    
    # Simulated account data
    ACCOUNTS = {
        "user123": {
            "savings": {"balance": 15430.50, "account_number": "001-234567-8"},
            "checking": {"balance": 2340.20, "account_number": "002-234567-8"},
            "cards": [
                {"type": "credit", "last4": "4532", "status": "active", "balance": 1250.00},
                {"type": "debit", "last4": "7891", "status": "active"}
            ]
        }
    }
    
    # Transaction history storage
    TRANSACTIONS = {
        "user123": [
            {"id": "TXN100001", "type": "debit", "amount": 50.00, "description": "Grocery Store", "date": "2025-06-15", "balance": 15380.50},
            {"id": "TXN100002", "type": "credit", "amount": 3000.00, "description": "Salary", "date": "2025-06-01", "balance": 18430.50},
            {"id": "TXN100003", "type": "debit", "amount": 1250.00, "description": "Credit Card Payment", "date": "2025-06-10", "balance": 17180.50},
            {"id": "TXN100004", "type": "debit", "amount": 85.50, "description": "Electricity Bill", "date": "2025-06-12", "balance": 17095.00},
            {"id": "TXN100005", "type": "debit", "amount": 200.00, "description": "Online Shopping", "date": "2025-06-14", "balance": 16895.00},
            {"id": "TXN100006", "type": "credit", "amount": 500.00, "description": "Refund", "date": "2025-06-13", "balance": 17395.00},
        ]
    }
    
    @staticmethod
    def validate_card_params(params: Dict) -> bool:
        """Validate card action parameters"""
        if "last4" not in params:
            return False
        if not params["last4"].isdigit() or len(params["last4"]) != 4:
            return False
        return True
    
    @staticmethod
    def validate_transfer_params(params: Dict) -> bool:
        """Validate transfer parameters"""
        required = ["from_account", "to_account", "amount"]
        if not all(k in params for k in required):
            return False
        if params["amount"] <= 0 or params["amount"] > 50000:
            return False
        return True
    
    @classmethod
    def lock_card(cls, user_id: str, last4: str) -> Dict[str, Any]:
        """Lock a credit/debit card"""
        # Validate input
        if not cls.validate_card_params({"last4": last4}):
            return {"success": False, "error": "Invalid card number format"}
        
        # Find card
        user_data = cls.ACCOUNTS.get(user_id, {})
        cards = user_data.get("cards", [])
        
        for card in cards:
            if card["last4"] == last4:
                if card["status"] == "locked":
                    return {"success": False, "message": "Card is already locked"}
                
                card["status"] = "locked"
                return {
                    "success": True,
                    "message": f"{card['type'].title()} card ending in {last4} has been locked successfully",
                    "card_type": card["type"]
                }
        
        return {"success": False, "error": "Card not found"}
    
    @classmethod
    def unlock_card(cls, user_id: str, last4: str) -> Dict[str, Any]:
        """Unlock a credit/debit card"""
        if not cls.validate_card_params({"last4": last4}):
            return {"success": False, "error": "Invalid card number format"}
        
        user_data = cls.ACCOUNTS.get(user_id, {})
        cards = user_data.get("cards", [])
        
        for card in cards:
            if card["last4"] == last4:
                if card["status"] == "active":
                    return {"success": False, "message": "Card is already active"}
                
                card["status"] = "active"
                return {
                    "success": True,
                    "message": f"{card['type'].title()} card ending in {last4} has been unlocked",
                    "card_type": card["type"]
                }
        
        return {"success": False, "error": "Card not found"}
    
    @classmethod
    def check_balance(cls, user_id: str, account_type: str = "savings") -> Dict[str, Any]:
        """Check account balance"""
        user_data = cls.ACCOUNTS.get(user_id, {})
        
        if account_type in user_data:
            account = user_data[account_type]
            return {
                "success": True,
                "account_type": account_type,
                "balance": account["balance"],
                "account_number": account["account_number"]
            }
        
        return {"success": False, "error": f"Account type '{account_type}' not found"}
    
    @staticmethod
    def _is_valid_date(date_str: str) -> bool:
        """Validate date format (YYYY-MM-DD)"""
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except (ValueError, TypeError):
            return False
    
    @classmethod
    def get_transactions(
        cls,
        user_id: str,
        start_date: str = None,
        end_date: str = None,
        transaction_type: str = None,
        min_amount: float = None,
        max_amount: float = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Retrieve transaction history for a user with optional filtering.
        
        Args:
            user_id: User identifier
            start_date: Filter transactions on/after this date (YYYY-MM-DD)
            end_date: Filter transactions on/before this date (YYYY-MM-DD)
            transaction_type: Filter by 'credit' or 'debit'
            min_amount: Filter transactions with amount >= this value
            max_amount: Filter transactions with amount <= this value
            limit: Maximum number of transactions to return (default: 10)
        
        Returns:
            Dict with 'success', 'transactions' list, and optional 'error' or 'message'
        """
        # Validate limit parameter
        if limit is None or limit <= 0:
            limit = 10
        
        # Validate date format - if invalid, ignore date filters
        if start_date and not cls._is_valid_date(start_date):
            start_date = None
        if end_date and not cls._is_valid_date(end_date):
            end_date = None
        
        # Validate amount filters - ignore negative values
        if min_amount is not None and min_amount < 0:
            min_amount = None
        if max_amount is not None and max_amount < 0:
            max_amount = None
        
        # Get user transactions
        user_transactions = cls.TRANSACTIONS.get(user_id, [])
        
        if not user_transactions:
            return {
                "success": True,
                "transactions": [],
                "message": "No transactions found for this account"
            }
        
        # Sort by date descending (newest first)
        sorted_txns = sorted(
            user_transactions,
            key=lambda x: x.get("date", ""),
            reverse=True
        )
        
        # Apply filters
        filtered_txns = []
        for txn in sorted_txns:
            # Date filter
            if start_date and txn.get("date", "") < start_date:
                continue
            if end_date and txn.get("date", "") > end_date:
                continue
            
            # Type filter
            if transaction_type and txn.get("type", "").lower() != transaction_type.lower():
                continue
            
            # Amount filters
            txn_amount = txn.get("amount", 0)
            if min_amount is not None and txn_amount < min_amount:
                continue
            if max_amount is not None and txn_amount > max_amount:
                continue
            
            filtered_txns.append(txn)
        
        # Apply limit
        result_txns = filtered_txns[:limit]
        
        return {
            "success": True,
            "transactions": result_txns,
            "count": len(result_txns),
            "total_available": len(filtered_txns)
        }
    
    @classmethod
    def transfer_funds(cls, user_id: str, from_account: str, 
                      to_account: str, amount: float) -> Dict[str, Any]:
        """Transfer funds between accounts"""
        params = {
            "from_account": from_account,
            "to_account": to_account,
            "amount": amount
        }
        
        if not cls.validate_transfer_params(params):
            return {"success": False, "error": "Invalid transfer parameters"}
        
        user_data = cls.ACCOUNTS.get(user_id, {})
        
        # Check source account
        if from_account not in user_data:
            return {"success": False, "error": "Source account not found"}
        
        if user_data[from_account]["balance"] < amount:
            return {"success": False, "error": "Insufficient funds"}
        
        # Simulate transfer
        user_data[from_account]["balance"] -= amount
        
        # Generate transaction ID
        txn_id = f"TXN{random.randint(100000, 999999)}"
        
        # Log debit transaction for source account
        cls.TRANSACTIONS.setdefault(user_id, []).append({
            "id": txn_id,
            "type": "debit",
            "amount": amount,
            "description": f"Transfer to {to_account}",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "balance": user_data[from_account]["balance"]
        })
        
        # If to_account exists in user_data, also log credit transaction
        if to_account in user_data:
            user_data[to_account]["balance"] += amount
            credit_txn_id = f"TXN{random.randint(100000, 999999)}"
            cls.TRANSACTIONS.setdefault(user_id, []).append({
                "id": credit_txn_id,
                "type": "credit",
                "amount": amount,
                "description": f"Transfer from {from_account}",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "balance": user_data[to_account]["balance"]
            })
            return {
                "success": True,
                "message": f"Successfully transferred ${amount:.2f} from {from_account}",
                "transaction_id": txn_id,
                "new_balance": user_data[from_account]["balance"],
                "to_account_new_balance": user_data[to_account]["balance"]
            }
        
        return {
            "success": True,
            "message": f"Successfully transferred ${amount:.2f} from {from_account}",
            "transaction_id": txn_id,
            "new_balance": user_data[from_account]["balance"]
        }