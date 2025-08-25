#!/usr/bin/env python3
"""
Test module for the universal contract workflow.

This module tests the universal contract queue data pull workflow
with 3 sample NSNs to verify functionality using real clients.
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the project root to the path so we can import the ETL modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import the workflow module and operations
from etl.workflows.adhoc.universal_contract_queue_data_pull import UniversalContractQueueDataPuller
from etl.core.operations import (
    ChromeSetupOperation,
    ConsentPageOperation,
    NsnPageNavigationOperation,
    ClosedSolicitationCheckOperation,
    AmscExtractionOperation
)


class TestUniversalContractWorkflow:
    """Test class for the universal contract workflow."""
    
    @pytest.fixture(scope="class")
    def sample_nsns(self):
        """Sample NSNs for testing."""
        return [
            "5331-00-618-5361",  # Sample NSN from the HTML you showed earlier
            "8455-01-688-7455",  # Another sample NSN
            "5310-00-382-7593"   # Third sample NSN
        ]
    
    @pytest.fixture(scope="class")
    def real_supabase_client(self):
        """Real Supabase client for testing."""
        try:
            from etl.core.uploaders.supabase_uploader import SupabaseUploader
            supabase_client = SupabaseUploader().supabase
            
            if not supabase_client:
                pytest.skip("Supabase client not available - check environment variables")
            
            return supabase_client
            
        except Exception as e:
            pytest.skip(f"Failed to initialize Supabase client: {str(e)}")
    
    def test_workflow_initialization(self, real_supabase_client):
        """Test that the workflow can be initialized with real client."""
        workflow = UniversalContractQueueDataPuller(real_supabase_client)
        assert workflow is not None
        assert hasattr(workflow, 'supabase_client')
        assert workflow.supabase_client == real_supabase_client
    
    def test_contract_query_methods(self, real_supabase_client):
        """Test that contract query methods exist and are callable."""
        workflow = UniversalContractQueueDataPuller(real_supabase_client)
        
        # Check that required methods exist
        assert hasattr(workflow, 'query_contracts_needing_processing')
        assert hasattr(workflow, 'analyze_contract_data_gaps')
        assert hasattr(workflow, 'execute_with_data_flow')
        
        # Check that methods are callable
        assert callable(workflow.query_contracts_needing_processing)
        assert callable(workflow.analyze_contract_data_gaps)
        assert callable(workflow.execute_with_data_flow)
    
    def test_contract_analysis(self, real_supabase_client):
        """Test contract data gap analysis with real client."""
        workflow = UniversalContractQueueDataPuller(real_supabase_client)
        
        # Query contracts (limit to 3 for testing)
        contracts = workflow.query_contracts_needing_processing(limit=3)
        assert len(contracts) > 0  # Should have at least some contracts
        
        # Analyze gaps
        contract_gaps = workflow.analyze_contract_data_gaps(contracts)
        assert len(contract_gaps) > 0
        
        # Check that each contract has the expected structure
        for contract_id, gaps in contract_gaps.items():
            assert 'contract_data' in gaps
            assert 'nsn' in gaps
            assert 'should_process' in gaps
            assert 'action_reason' in gaps
    
    def test_chrome_setup_operation(self):
        """Test Chrome setup operation."""
        chrome_setup = ChromeSetupOperation(headless=True)
        assert chrome_setup is not None
        assert chrome_setup.name == "chrome_setup"
        assert chrome_setup.can_apply_to_batch() is False
    
    def test_consent_page_operation(self):
        """Test consent page operation."""
        consent_page = ConsentPageOperation()
        assert consent_page is not None
        assert consent_page.name == "consent_page"
        assert consent_page.can_apply_to_batch() is True
    
    def test_nsn_navigation_operation(self):
        """Test NSN navigation operation."""
        nsn_navigation = NsnPageNavigationOperation()
        assert nsn_navigation is not None
        assert nsn_navigation.name == "nsn_page_navigation"
        assert nsn_navigation.can_apply_to_batch() is True
    
    def test_closed_solicitation_check_operation(self):
        """Test closed solicitation check operation."""
        closed_check = ClosedSolicitationCheckOperation()
        assert closed_check is not None
        assert closed_check.name == "closed_solicitation_check"
        assert closed_check.can_apply_to_batch() is True
    
    def test_amsc_extraction_operation(self):
        """Test AMSC extraction operation."""
        amsc_extraction = AmscExtractionOperation()
        assert amsc_extraction is not None
        assert amsc_extraction.name == "amsc_extraction"
        assert amsc_extraction.can_apply_to_batch() is True
    
    def test_sample_nsn_processing(self, sample_nsns):
        """Test processing of sample NSNs."""
        for nsn in sample_nsns:
            # Test that NSNs have valid format
            assert isinstance(nsn, str)
            assert len(nsn) > 0
            assert '-' in nsn  # NSNs should have dashes
            
            # Test that NSNs follow the expected pattern (4-2-2-4)
            parts = nsn.split('-')
            assert len(parts) == 4
            assert len(parts[0]) == 4  # First part should be 4 digits
            assert len(parts[1]) == 2  # Second part should be 2 digits
            assert len(parts[2]) == 2  # Third part should be 2 digits
            assert len(parts[3]) == 4  # Fourth part should be 4 digits
    
    @pytest.mark.integration
    def test_workflow_execution_without_supabase_upload(self, real_supabase_client):
        """Test workflow execution up to but excluding Supabase upload."""
        workflow = UniversalContractQueueDataPuller(real_supabase_client)
        
        # Mock the SupabaseUploadOperation to prevent actual database operations
        with patch('etl.core.operations.supabase_upload_operation.SupabaseUploadOperation') as mock_upload:
            # Configure the mock to return a successful result
            mock_instance = MagicMock()
            mock_instance.execute.return_value = MagicMock(
                success=True,
                status="completed",
                data={"uploaded": True}
            )
            mock_upload.return_value = mock_instance
            
            # Execute workflow with a small limit
            result = workflow.execute_with_data_flow(
                headless=True,
                timeout=30,
                retry_attempts=2,
                batch_size=3,
                limit=3
            )
            
            # Check that result has expected structure
            assert isinstance(result, dict)
            assert 'success' in result
            assert 'status' in result
            
            # The workflow should complete successfully
            assert result['success'] is True
            assert result['status'] == 'completed'
            
            # Check that we processed some contracts
            assert result.get('contracts_processed', 0) > 0
            assert result.get('nsns_processed', 0) > 0
            
            # Check that we have results for the processing steps
            assert 'closed_status_checks' in result
            assert 'amsc_extractions' in result
            assert 'rfq_pdfs_needed' in result
    
    @pytest.mark.integration
    def test_individual_operations_with_real_data(self, real_supabase_client, sample_nsns):
        """Test individual operations with real data from Supabase."""
        workflow = UniversalContractQueueDataPuller(real_supabase_client)
        
        # Get real contracts from the database
        contracts = workflow.query_contracts_needing_processing(limit=5)
        assert len(contracts) > 0
        
        # Test that we can analyze real contract data
        contract_gaps = workflow.analyze_contract_data_gaps(contracts)
        assert len(contract_gaps) > 0
        
        # Check that the analysis produces meaningful results
        for contract_id, gaps in contract_gaps.items():
            contract_data = gaps.get('contract_data', {})
            nsn = gaps.get('nsn')
            
            if nsn:
                # Test that NSN format is valid
                assert isinstance(nsn, str)
                assert '-' in nsn
                
                # Test that we have the required fields
                assert 'solicitation_number' in contract_data
                assert 'should_process' in gaps
                assert 'action_reason' in gaps


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])
