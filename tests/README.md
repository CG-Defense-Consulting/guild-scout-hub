# Tests

This directory contains pytest modules for testing the ETL workflow functionality using real clients and data.

## Setup

1. Install test dependencies:
```bash
cd tests
pip install -r requirements.txt
```

2. Ensure you have the required environment variables set for Supabase:
   - `VITE_SUPABASE_URL`
   - `VITE_SUPABASE_PUBLISHABLE_KEY`
   - `SUPABASE_SERVICE_ROLE_KEY`

3. Ensure you're in the project root directory when running tests.

## Running Tests

### Run all tests:
```bash
pytest tests/ -v
```

### Run only unit tests (skip integration tests):
```bash
pytest tests/ -v -m "not integration"
```

### Run only integration tests:
```bash
pytest tests/ -v -m "integration"
```

### Run specific test file:
```bash
pytest tests/test_universal_contract_workflow.py -v
```

### Run with coverage:
```bash
pytest tests/ --cov=etl --cov-report=html
```

### Run specific test method:
```bash
pytest tests/test_universal_contract_workflow.py::TestUniversalContractWorkflow::test_workflow_initialization -v
```

## Test Structure

- `conftest.py` - Pytest configuration and shared fixtures
- `test_universal_contract_workflow.py` - Tests for the universal contract workflow
- `requirements.txt` - Test dependencies

## Test Categories

### Unit Tests
- **`test_workflow_initialization`** - Tests workflow object creation with real client
- **`test_contract_query_methods`** - Verifies required methods exist and are callable
- **`test_contract_analysis`** - Tests contract data gap analysis with real data
- **`test_chrome_setup_operation`** - Tests Chrome setup operation initialization
- **`test_consent_page_operation`** - Tests consent page operation initialization
- **`test_nsn_navigation_operation`** - Tests NSN navigation operation initialization
- **`test_closed_solicitation_check_operation`** - Tests closed status check operation
- **`test_amsc_extraction_operation`** - Tests AMSC extraction operation
- **`test_sample_nsn_processing`** - Tests NSN format validation

### Integration Tests
- **`test_workflow_execution_without_supabase_upload`** - Tests full workflow execution (excluding database operations)
- **`test_individual_operations_with_real_data`** - Tests operations with real data from Supabase

## Sample NSNs Used in Tests

The tests use 3 sample NSNs:
1. `5331-00-618-5361` - Sample NSN from the HTML example
2. `8455-01-688-7455` - Another sample NSN
3. `5310-00-382-7593` - Third sample NSN

## What Gets Tested

### ✅ Real Client Testing
- Uses actual Supabase client connection
- Queries real database for contract data
- Tests actual data analysis logic

### ✅ Full Workflow Execution
- Chrome setup and driver initialization
- Consent page handling
- NSN page navigation
- Closed solicitation status checking
- AMSC code extraction
- **Mocked Supabase upload** (prevents actual database changes)

### ✅ Operation Validation
- All individual operations are tested for proper initialization
- Batch processing capabilities are verified
- Input/output validation is tested

## Environment Requirements

- **Supabase Connection**: Must have valid environment variables
- **Chrome/ChromeDriver**: Required for workflow execution tests
- **Network Access**: Required for DIBBS website access

## Notes

- Tests use real Supabase client for authentic data testing
- Full workflow execution is tested but database operations are mocked
- Integration tests are marked with `@pytest.mark.integration`
- Tests will skip if Supabase client is not available
- Chrome setup is tested but actual browser automation requires proper environment
