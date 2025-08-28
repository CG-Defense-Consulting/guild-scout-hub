# Testing

This directory contains tests for the ETL system to ensure all components work correctly.

## Test Files

### `test_workflow_integration.py`
Comprehensive integration tests for all workflows (scheduled and adhoc) that verify:
- Workflow creation and configuration
- Operation dependencies and ordering
- Data flow through workflow steps
- Error handling and validation
- Mocked operations (no actual database uploads)

### `test_universal_contract_workflow.py`
Tests for the universal contract queue workflow.

### `conftest.py`
Pytest configuration and shared fixtures.

## Running Tests

### Prerequisites
- Python 3.8+
- pytest (will be installed automatically if missing)
- All ETL dependencies installed

### Quick Start
```bash
# From the project root directory
cd tests
python run_workflow_tests.py
```

### Using Pytest Directly
```bash
# From the project root directory
pytest tests/test_workflow_integration.py -v

# Run a specific test
pytest tests/test_workflow_integration.py::TestWorkflowIntegration::test_dibbs_rfq_index_workflow_creation -v

# Run with coverage
pytest tests/test_workflow_integration.py --cov=etl --cov-report=html
```

### Test Runner Script
The `run_workflow_tests.py` script provides a convenient way to run tests:

```bash
# Run all tests
python tests/run_workflow_tests.py

# Run a specific test
python tests/run_workflow_tests.py TestWorkflowIntegration::test_date_formatting_logic
```

## What the Tests Cover

### Workflow Integration Tests
1. **Workflow Creation**: Verifies workflows can be created with correct step configuration
2. **Date Handling**: Tests date formatting for archive downloads (YYYY-MM-DD → in{yy}{mm}{dd})
3. **Operation Testing**: Tests individual operations with mocked dependencies
4. **Dependency Validation**: Ensures workflow steps have correct dependencies
5. **Error Handling**: Tests error scenarios and validation
6. **Batch Processing**: Verifies operations support batch processing
7. **Environment Variables**: Tests environment variable handling
8. **Metadata Validation**: Ensures operations have proper metadata
9. **Step Ordering**: Verifies logical workflow step ordering

### Tested Workflows
- **Scheduled**: DIBBS RFQ Index Pull (daily at 2:30 AM)
- **Adhoc**: 
  - Extract NSN AMSC Code
  - Pull Single RFQ PDF
  - Universal Contract Queue Data Pull

### Tested Operations
- Chrome Setup
- Archive Downloads Navigation
- Consent Page Handling
- DIBBS Text File Download
- Text File Parsing (inline)
- Supabase Upload (mocked)

## Test Environment

### Mocked Dependencies
- **Chrome Driver**: Mocked to prevent actual browser operations
- **Supabase Client**: Mocked to prevent actual database operations
- **File System**: Uses temporary directories for testing

### Environment Variables
Tests set up a safe testing environment:
- `TESTING=true`
- `DIBBS_DOWNLOAD_DIR=./test_downloads`
- `LOG_FILE=./test_logs/test.log`
- `VITE_SUPABASE_URL=https://test.supabase.co`
- `SUPABASE_SERVICE_ROLE_KEY=test_key`

### Temporary Files
Tests create temporary directories and files that are automatically cleaned up:
- Test downloads directory
- Test logs directory
- Sample data files

## Test Results

### Success Criteria
- All workflow steps can be created and configured
- Date formatting produces correct URL patterns
- Operations handle errors gracefully
- Dependencies are correctly configured
- Mocked operations return expected results

### What Tests Don't Do
- **No Real Browser Operations**: Chrome operations are mocked
- **No Database Uploads**: Supabase operations are mocked
- **No External API Calls**: All external dependencies are mocked
- **No File Downloads**: File operations use temporary test data

## Troubleshooting

### Common Issues
1. **Import Errors**: Ensure you're running from the project root
2. **Missing Dependencies**: Install ETL requirements first
3. **Path Issues**: Check that the ETL directory structure is correct

### Debug Mode
Run tests with verbose output:
```bash
pytest tests/test_workflow_integration.py -v -s
```

### Running Individual Tests
To debug specific functionality:
```bash
# Test only date formatting
pytest tests/test_workflow_integration.py::TestWorkflowIntegration::test_date_formatting_logic -v

# Test only workflow creation
pytest tests/test_workflow_integration.py::TestWorkflowIntegration::test_dibbs_rfq_index_workflow_creation -v
```

## Adding New Tests

### For New Workflows
1. Import the workflow module
2. Test workflow creation and configuration
3. Test step dependencies and ordering
4. Mock any external dependencies

### For New Operations
1. Test operation instantiation
2. Test input validation
3. Test execution with mocked inputs
4. Test error handling

### Test Structure
```python
def test_new_feature(self):
    """Test description."""
    # Arrange
    # Act
    # Assert
```

## Continuous Integration

These tests are designed to run in CI/CD pipelines:
- No external dependencies
- Fast execution
- Comprehensive coverage
- Clear pass/fail criteria

The tests ensure that workflow changes don't break existing functionality and that new features work as expected.
