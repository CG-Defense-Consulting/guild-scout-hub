"""
Operations Module

This module provides a framework for building modular, chainable operations
that can be combined into efficient workflows.
"""

from .base_operation import BaseOperation, OperationResult, OperationStatus
from .chrome_setup_operation import ChromeSetupOperation
from .consent_page_operation import ConsentPageOperation
from .nsn_extraction_operation import NsnExtractionOperation
from .supabase_upload_operation import SupabaseUploadOperation

__all__ = [
    'BaseOperation',
    'OperationResult',
    'OperationStatus',
    'ChromeSetupOperation',
    'ConsentPageOperation',
    'NsnExtractionOperation',
    'SupabaseUploadOperation'
]
