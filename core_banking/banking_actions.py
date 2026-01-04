# Banking Actions - Simulated operations
"""Simulated banking actions (prototype - no real APIs)"""
from typing import Dict, Any
import random

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
        
        return {
            "success": True,
            "message": f"Successfully transferred ${amount:.2f} from {from_account}",
            "transaction_id": txn_id,
            "new_balance": user_data[from_account]["balance"]
        }