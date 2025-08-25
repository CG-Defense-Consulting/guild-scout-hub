"""
Operations Module

This module provides a framework for building modular, chainable operations
that can be combined into efficient workflows.
"""

from .base_operation import BaseOperation
from .chrome_setup_operation import ChromeSetupOperation
from .consent_page_operation import ConsentPageOperation
from .nsn_extraction_operation import NsnExtractionOperation
from .closed_solicitation_check_operation import ClosedSolicitationCheckOperation
from .supabase_upload_operation import SupabaseUploadOperation

__all__ = [
    'BaseOperation',
    'ChromeSetupOperation',
    'ConsentPageOperation',
    'NsnExtractionOperation', 
    'ClosedSolicitationCheckOperation',
    'SupabaseUploadOperation'
]
