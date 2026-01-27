"""
General utility helper functions
"""

from typing import Optional
from uuid import UUID


def is_valid_uuid(uuid_string: str) -> bool:
    """
    Check if string is a valid UUID
    
    Args:
        uuid_string: String to validate
    
    Returns:
        True if valid UUID, False otherwise
    """
    try:
        UUID(uuid_string)
        return True
    except (ValueError, AttributeError):
        return False


def format_currency(amount: int, currency: str = "USD") -> str:
    """
    Format amount as currency string
    
    Args:
        amount: Amount in cents/smallest unit
        currency: Currency code
    
    Returns:
        Formatted currency string
    """
    # Convert from cents to dollars
    dollars = amount / 100.0
    return f"${dollars:,.2f}"

