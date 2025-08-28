"""
Operations Module

This module provides a framework for building modular, chainable operations
that can be combined into efficient workflows.
"""

from .base_operation import BaseOperation, OperationResult, OperationStatus
from .chrome_setup_operation import ChromeSetupOperation
from .consent_page_operation import ConsentPageOperation
from .amsc_extraction_operation import AmscExtractionOperation
from .closed_solicitation_check_operation import ClosedSolicitationCheckOperation
from .nsn_page_navigation_operation import NsnPageNavigationOperation
from .rfq_pdf_download_operation import RfqPdfDownloadOperation
from .supabase_upload_operation import SupabaseUploadOperation
from .dibbs_text_file_download_operation import DibbsTextFileDownloadOperation
from .archive_downloads_navigation_operation import ArchiveDownloadsNavigationOperation

__all__ = [
    'BaseOperation',
    'OperationResult',
    'OperationStatus',
    'ChromeSetupOperation',
    'ConsentPageOperation',
    'AmscExtractionOperation',
    'ClosedSolicitationCheckOperation',
    'NsnPageNavigationOperation',
    'RfqPdfDownloadOperation',
    'SupabaseUploadOperation',
    'DibbsTextFileDownloadOperation',
    'ArchiveDownloadsNavigationOperation'
]
