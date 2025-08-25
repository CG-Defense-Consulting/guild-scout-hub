"""
Operations Module

This module provides a framework for building modular, chainable operations
that can be combined into efficient workflows.
"""

from .base_operation import BaseOperation
from .chrome_setup_operation import ChromeSetupOperation
from .amsc_extraction_operation import AmscExtractionOperation
from .supabase_upload_operation import SupabaseUploadOperation

__all__ = [
    'BaseOperation',
    'ChromeSetupOperation', 
    'AmscExtractionOperation',
    'SupabaseUploadOperation'
]
