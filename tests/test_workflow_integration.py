#!/usr/bin/env python3
"""
Workflow Integration Tests

This test suite runs through each workflow to verify that all components work correctly
without actually uploading to Supabase. It tests the data flow and parsing logic
to ensure the workflows produce the expected outcomes.
"""

import pytest
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import the workflow modules
from etl.workflows.scheduled.dibbs_rfq_index_pull import (
    create_dibbs_rfq_index_workflow, 
    get_target_date,
    main as dibbs_main
)
from etl.workflows.adhoc.extract_nsn_amsc import (
    extract_nsn_amsc,
    main as amsc_main
)
from etl.workflows.adhoc.pull_single_rfq_pdf import (
    pull_single_rfq_pdf,
    main as pdf_main
)
from etl.workflows.adhoc.universal_contract_queue_data_pull import (
    main as ucq_main
)

# Import operations for testing
from etl.core.operations.archive_downloads_navigation_operation import ArchiveDownloadsNavigationOperation
from etl.core.operations.consent_page_operation import ConsentPageOperation
from etl.core.operations.dibbs_text_file_download_operation import DibbsTextFileDownloadOperation
from etl.core.operations.supabase_upload_operation import SupabaseUploadOperation


class TestWorkflowIntegration:
    """Test suite for workflow integration testing."""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Set up test environment with temporary directories and mocked dependencies."""
        # Create temporary directories
        self.temp_dir = tempfile.mkdtemp()
        self.downloads_dir = os.path.join(self.temp_dir, "downloads")
        self.logs_dir = os.path.join(self.temp_dir, "logs")
        os.makedirs(self.downloads_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)
        
        # Set environment variables for testing
        os.environ["DIBBS_DOWNLOAD_DIR"] = self.downloads_dir
        os.environ["LOG_FILE"] = os.path.join(self.logs_dir, "test.log")
        os.environ["VITE_SUPABASE_URL"] = "https://test.supabase.co"
        os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "test_key"
        
        yield
        
        # Cleanup
        shutil.rmtree(self.temp_dir)
    
    @pytest.fixture
    def mock_chrome_driver(self):
        """Mock Chrome driver for testing."""
        mock_driver = MagicMock()
        mock_driver.current_url = "https://test.dibbs.bsm.dla.mil"
        mock_driver.title = "Test Page"
        mock_driver.page_source = "<html><body>Test content</body></html>"
        return mock_driver
    
    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase client to prevent actual database operations."""
        with patch('etl.core.operations.supabase_upload_operation.create_client') as mock_create:
            mock_client = MagicMock()
            mock_client.table.return_value.upsert.return_value.execute.return_value.data = [{"id": 1}]
            mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [{"id": 1}]
            mock_create.return_value = mock_client
            yield mock_client

    def test_dibbs_rfq_index_workflow_creation(self):
        """Test that the DIBBS RFQ index workflow can be created successfully."""
        workflow = create_dibbs_rfq_index_workflow("2024-01-15")
        
        assert workflow is not None
        assert workflow.name == "dibbs_rfq_index_pull"
        assert len(workflow.steps) == 6  # Should have 6 steps
        
        # Verify step names
        step_names = [step.operation.name for step in workflow.steps]
        expected_steps = [
            "chrome_setup",
            "archive_downloads_navigation", 
            "consent_page",
            "dibbs_text_file_download",
            "text_file_parsing",
            "supabase_upload"
        ]
        
        for expected_step in expected_steps:
            assert expected_step in step_names, f"Missing step: {expected_step}"

    def test_date_formatting_logic(self):
        """Test the date formatting logic for archive downloads."""
        # Test various date formats
        test_cases = [
            ("2024-01-15", "in240115"),
            ("2024-12-31", "in241231"),
            ("2023-06-05", "in230605"),
            ("2025-02-28", "in250228")
        ]
        
        for input_date, expected_format in test_cases:
            formatted = get_target_date(input_date)
            assert formatted == input_date  # Should return the same date string
            
            # Test the actual formatting in the operation
            operation = ArchiveDownloadsNavigationOperation()
            formatted_url = operation._format_date_for_url(input_date)
            assert formatted_url == expected_format, f"Date {input_date} formatted incorrectly"

    def test_archive_downloads_navigation_operation(self, mock_chrome_driver):
        """Test the archive downloads navigation operation."""
        operation = ArchiveDownloadsNavigationOperation()
        
        # Test with valid date
        result = operation._execute({
            'date': '2024-01-15',
            'chrome_driver': mock_chrome_driver,
            'base_url': 'https://test.dibbs.bsm.dla.mil',
            'timeout': 10
        }, {})
        
        assert result.success is True
        assert result.data['date'] == '2024-01-15'
        assert result.data['formatted_date'] == 'in240115'
        assert 'html_content' in result.data
        
        # Test with invalid date
        result = operation._execute({
            'date': 'invalid-date',
            'chrome_driver': mock_chrome_driver
        }, {})
        
        assert result.success is False
        assert 'Invalid date format' in result.error

    def test_consent_page_operation(self, mock_chrome_driver):
        """Test the consent page operation."""
        operation = ConsentPageOperation()
        
        # Mock the context with chrome_driver
        context = {'chrome_driver': mock_chrome_driver}
        
        result = operation._execute({
            'nsn': 'test_nsn',
            'timeout': 10,
            'retry_attempts': 2,
            'base_url': 'https://test.dibbs.bsm.dla.mil'
        }, context)
        
        # Should succeed even if no consent page is found
        assert result.success is True

    def test_dibbs_text_file_download_operation(self):
        """Test the DIBBS text file download operation."""
        operation = DibbsTextFileDownloadOperation()
        
        result = operation._execute({
            'dibbs_base_url': 'https://test.dibbs.bsm.dla.mil',
            'download_dir': self.downloads_dir,
            'file_type': 'rfq_index'
        }, {})
        
        assert result.success is True
        assert 'file_path' in result.data
        assert os.path.exists(result.data['file_path'])
        
        # Verify file content
        with open(result.data['file_path'], 'r') as f:
            content = f.read()
            assert 'DIBBS RFQ Index' in content
            assert 'NSN,AMSC,Status,Description' in content

    def test_supabase_upload_operation_mocked(self, mock_supabase_client):
        """Test the Supabase upload operation with mocked client."""
        operation = SupabaseUploadOperation()
        
        # Test data
        test_results = [
            {
                'success': True,
                'data': {
                    'nsn': '5331006185361',
                    'amsc': '1',
                    'status': 'Open',
                    'description': 'Test RFQ'
                }
            }
        ]
        
        result = operation._execute({
            'results': test_results,
            'table_name': 'rfq_index_extract',
            'operation_type': 'upsert',
            'upsert_strategy': 'merge',
            'conflict_resolution': 'update_existing',
            'key_fields': ['nsn'],
            'batch_size': 50
        }, {})
        
        assert result.success is True
        assert result.data['successful_uploads'] == 1
        assert result.data['failed_uploads'] == 0

    def test_workflow_step_dependencies(self):
        """Test that workflow steps have correct dependencies."""
        workflow = create_dibbs_rfq_index_workflow("2024-01-15")
        
        # Check that steps have proper dependencies
        step_dependencies = {
            step.operation.name: step.depends_on for step in workflow.steps
        }
        
        # Verify dependencies
        assert step_dependencies['archive_downloads_navigation'] == ['chrome_setup']
        assert step_dependencies['consent_page'] == ['archive_downloads_navigation']
        assert step_dependencies['dibbs_text_file_download'] == ['consent_page']
        assert step_dependencies['text_file_parsing'] == ['dibbs_text_file_download']
        assert step_dependencies['supabase_upload'] == ['text_file_parsing']

    def test_workflow_with_mocked_operations(self, mock_chrome_driver, mock_supabase_client):
        """Test the complete workflow with mocked operations."""
        # Create workflow
        workflow = create_dibbs_rfq_index_workflow("2024-01-15")
        
        # Mock the Chrome setup to return a mock driver
        with patch('etl.core.operations.chrome_setup_operation.ChromeSetupOperation._execute') as mock_chrome_setup:
            mock_chrome_setup.return_value = MagicMock(
                success=True,
                data={'chrome_driver': mock_chrome_driver}
            )
            
            # Mock the Supabase upload to prevent actual database operations
            with patch('etl.core.operations.supabase_upload_operation.SupabaseUploadOperation._execute') as mock_upload:
                mock_upload.return_value = MagicMock(
                    success=True,
                    data={'uploaded_count': 1}
                )
                
                # Execute workflow
                result = workflow.execute()
                
                # Verify workflow execution
                assert result is not None
                # Note: The actual result structure depends on the workflow orchestrator implementation

    def test_error_handling_in_workflows(self):
        """Test error handling in workflows."""
        # Test with invalid date
        workflow = create_dibbs_rfq_index_workflow("invalid-date")
        
        # The workflow should still be created, but the date will be defaulted
        assert workflow is not None
        
        # Test archive navigation with invalid date
        operation = ArchiveDownloadsNavigationOperation()
        result = operation._execute({
            'date': 'invalid-date',
            'chrome_driver': MagicMock()
        }, {})
        
        assert result.success is False
        assert 'Invalid date format' in result.error

    def test_batch_processing_capabilities(self):
        """Test that operations support batch processing."""
        # Test archive navigation batch processing
        operation = ArchiveDownloadsNavigationOperation()
        assert operation.can_apply_to_batch() is True
        
        # Test text file download batch processing
        operation = DibbsTextFileDownloadOperation()
        assert operation.can_apply_to_batch() is True
        
        # Test Supabase upload batch processing
        operation = SupabaseUploadOperation()
        assert operation.can_apply_to_batch() is True

    def test_environment_variable_handling(self):
        """Test that workflows handle environment variables correctly."""
        # Test with missing environment variables
        with patch.dict(os.environ, {}, clear=True):
            # Should still work with defaults
            workflow = create_dibbs_rfq_index_workflow("2024-01-15")
            assert workflow is not None
            
            # Test date fallback
            date = get_target_date()
            assert date is not None
            assert isinstance(date, str)
            assert len(date) == 10  # YYYY-MM-DD format

    def test_workflow_logging_and_metadata(self):
        """Test that workflows provide proper logging and metadata."""
        workflow = create_dibbs_rfq_index_workflow("2024-01-15")
        
        # Verify workflow metadata
        assert workflow.name == "dibbs_rfq_index_pull"
        assert "2024-01-15" in workflow.description
        
        # Verify operation metadata
        for step in workflow.steps:
            assert step.operation.name is not None
            assert step.operation.description is not None
            assert step.operation.required_inputs is not None
            assert step.operation.optional_inputs is not None

    def test_adhoc_workflow_functions(self):
        """Test the adhoc workflow functions without executing them."""
        # Test that the functions exist and are callable
        assert callable(extract_nsn_amsc)
        assert callable(pull_single_rfq_pdf)
        
        # Test function signatures
        import inspect
        
        # Check extract_nsn_amsc signature
        sig = inspect.signature(extract_nsn_amsc)
        assert 'contract_id' in sig.parameters
        assert 'nsn' in sig.parameters
        
        # Check pull_single_rfq_pdf signature
        sig = inspect.signature(pull_single_rfq_pdf)
        assert 'solicitation_number' in sig.parameters
        assert 'output_dir' in sig.parameters

    def test_workflow_input_validation(self):
        """Test input validation in workflows."""
        # Test archive navigation with missing required inputs
        operation = ArchiveDownloadsNavigationOperation()
        
        # Missing date
        result = operation._execute({
            'chrome_driver': MagicMock()
        }, {})
        assert result.success is False
        assert 'Missing required input' in result.error
        
        # Missing chrome_driver
        result = operation._execute({
            'date': '2024-01-15'
        }, {})
        assert result.success is False
        assert 'Missing required input' in result.error

    def test_workflow_output_consistency(self):
        """Test that workflow outputs are consistent and well-formed."""
        workflow = create_dibbs_rfq_index_workflow("2024-01-15")
        
        # Test that all steps have consistent operation result structures
        for step in workflow.steps:
            operation = step.operation
            
            # Test that operations can be instantiated
            assert operation is not None
            assert hasattr(operation, 'name')
            assert hasattr(operation, 'description')
            assert hasattr(operation, 'required_inputs')
            assert hasattr(operation, 'optional_inputs')
            
            # Test that operations have proper names
            assert isinstance(operation.name, str)
            assert len(operation.name) > 0
            assert operation.name == operation.name.lower().replace(' ', '_')

    def test_workflow_step_ordering(self):
        """Test that workflow steps are in the correct logical order."""
        workflow = create_dibbs_rfq_index_workflow("2024-01-15")
        
        # Verify logical step ordering
        step_names = [step.operation.name for step in workflow.steps]
        
        # Chrome setup should be first
        assert step_names[0] == 'chrome_setup'
        
        # Archive navigation should be second
        assert step_names[1] == 'archive_downloads_navigation'
        
        # Consent page should be third
        assert step_names[2] == 'consent_page'
        
        # Text download should be fourth
        assert step_names[3] == 'dibbs_text_file_download'
        
        # Text parsing should be fifth
        assert step_names[4] == 'text_file_parsing'
        
        # Supabase upload should be last
        assert step_names[5] == 'supabase_upload'


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
