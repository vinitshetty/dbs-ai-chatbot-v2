# Banking Actions - Simulated operations
"""Simulated banking actions (prototype - no real APIs)"""
from typing import Dict, Any, List
import random
import datetime
import tempfile
import os
from dateutil.relativedelta import relativedelta
from fpdf import FPDF

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

    # Transaction history storage
    TRANSACTIONS = {
        "user123": [
            {"id": "TXN100001", "type": "debit", "amount": 50.00, "description": "Grocery Store", "date": "2025-06-15", "balance": 15380.50},
            {"id": "TXN100002", "type": "credit", "amount": 3000.00, "description": "Salary", "date": "2025-06-01", "balance": 15430.50},
            {"id": "TXN100003", "type": "debit", "amount": 1250.00, "description": "Card Payment", "date": "2025-06-10", "balance": 14180.50},
            {"id": "TXN100004", "type": "debit", "amount": 200.00, "description": "ATM Withdrawal", "date": "2025-06-12", "balance": 13980.50},
            {"id": "TXN100005", "type": "credit", "amount": 500.00, "description": "Refund", "date": "2025-06-14", "balance": 14480.50},
        ]
    }

    @classmethod
    def get_transactions(
        cls,
        user_id: str,
        transaction_type: str = None,
        start_date: str = None,
        end_date: str = None,
        min_amount: float = None,
        max_amount: float = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Retrieve transaction history with optional filtering.
        
        Args:
            user_id: User identifier
            transaction_type: Filter by 'credit' or 'debit' (optional)
            start_date: Filter by start date (YYYY-MM-DD format, optional)
            end_date: Filter by end date (YYYY-MM-DD format, optional)
            min_amount: Minimum transaction amount (optional)
            max_amount: Maximum transaction amount (optional)
            limit: Maximum number of transactions to return (default: 10)
        
        Returns:
            Dict with 'success' boolean, 'transactions' list, and optional 'error' message
        """
        # Validate user
        if user_id not in cls.ACCOUNTS:
            return {"success": False, "error": "User not found"}
        
        # Get user transactions
        user_transactions = cls.TRANSACTIONS.get(user_id, [])
        
        if not user_transactions:
            return {"success": True, "transactions": [], "message": "No transactions found"}
        
        # Apply filters
        filtered = []
        for txn in user_transactions:
            # Type filter
            if transaction_type and txn.get("type") != transaction_type:
                continue
            
            # Date range filter
            txn_date = txn.get("date", "")
            if start_date and txn_date < start_date:
                continue
            if end_date and txn_date > end_date:
                continue
            
            # Amount range filter
            txn_amount = txn.get("amount", 0)
            if min_amount is not None and txn_amount < min_amount:
                continue
            if max_amount is not None and txn_amount > max_amount:
                continue
            
            filtered.append(txn)
        
        # Sort by date descending (newest first)
        filtered.sort(key=lambda x: x.get("date", ""), reverse=True)
        
        # Apply limit
        result_transactions = filtered[:limit]
        
        return {
            "success": True,
            "transactions": result_transactions,
            "total_count": len(filtered),
            "returned_count": len(result_transactions)
        }

    @classmethod
    def generate_transaction_pdf(cls, user_id: str, transactions: List[Dict[str, Any]], 
                                  filename: str = None) -> str:
        """
        Generate a PDF file from transaction data.
        
        Args:
            user_id: User identifier
            transactions: List of transaction dictionaries
            filename: Optional custom filename (without extension)
            
        Returns:
            Path to the generated PDF file
        """
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        
        # Title
        pdf.cell(0, 10, "DBS Bank - Transaction History", ln=True, align="C")
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, f"User ID: {user_id}", ln=True, align="C")
        pdf.cell(0, 10, f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align="C")
        pdf.ln(10)
        
        # Table headers
        pdf.set_font("Arial", "B", 10)
        pdf.set_fill_color(200, 220, 255)
        
        # Header row
        pdf.cell(30, 10, "Date", border=1, fill=True)
        pdf.cell(25, 10, "Type", border=1, fill=True)
        pdf.cell(70, 10, "Description", border=1, fill=True)
        pdf.cell(30, 10, "Amount", border=1, fill=True)
        pdf.cell(30, 10, "Balance", border=1, fill=True)
        pdf.ln(10)
        
        # Table rows
        pdf.set_font("Arial", size=10)
        pdf.set_fill_color(255, 255, 255)
        
        for txn in transactions:
            txn_date = txn.get("date", "N/A")
            txn_type = txn.get("type", "N/A").upper()
            description = txn.get("description", "N/A")
            amount = f"${txn.get('amount', 0):.2f}"
            balance = f"${txn.get('balance', 0):.2f}"
            
            pdf.cell(30, 10, txn_date, border=1)
            pdf.cell(25, 10, txn_type, border=1)
            pdf.cell(70, 10, description, border=1)
            pdf.cell(30, 10, amount, border=1)
            pdf.cell(30, 10, balance, border=1)
            pdf.ln(10)
        
        # Summary
        pdf.ln(5)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 10, f"Total Transactions: {len(transactions)}", ln=True)
        
        # Calculate totals
        total_credit = sum(txn.get("amount", 0) for txn in transactions if txn.get("type") == "credit")
        total_debit = sum(txn.get("amount", 0) for txn in transactions if txn.get("type") == "debit")
        pdf.cell(0, 10, f"Total Credits: ${total_credit:.2f}", ln=True)
        pdf.cell(0, 10, f"Total Debits: ${total_debit:.2f}", ln=True)
        
        # Save to temporary file
        if not filename:
            filename = f"transaction_history_{user_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        temp_dir = tempfile.gettempdir()
        filepath = os.path.join(temp_dir, f"{filename}.pdf")
        pdf.output(filepath)
        
        return filepath

    @staticmethod
    def _parse_date(date_str: str) -> str:
        """
        Parse and normalize date strings.
        Handles formats like 'last week', 'yesterday', '2025-06-15', etc.
        """
        date_str = date_str.strip().lower()
        today = datetime.date.today()
        
        # Handle relative dates
        if date_str == "today":
            return today.strftime("%Y-%m-%d")
        elif date_str == "yesterday":
            return (today - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        elif "last week" in date_str:
            return (today - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
        elif "this week" in date_str:
            return (today - datetime.timedelta(days=today.weekday())).strftime("%Y-%m-%d")
        elif "last month" in date_str:
            return (today - relativedelta(months=1)).strftime("%Y-%m-%d")
        
        # Validate YYYY-MM-DD format
        try:
            datetime.datetime.strptime(date_str, "%Y-%m-%d")
            return date_str
        except ValueError:
            # Try other common formats
            for fmt in ["%Y/%m/%d", "%d-%m-%Y", "%m/%d/%Y"]:
                try:
                    dt = datetime.datetime.strptime(date_str, fmt)
                    return dt.strftime("%Y-%m-%d")
                except ValueError:
                    continue
            return None