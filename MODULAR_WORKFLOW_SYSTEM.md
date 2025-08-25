# Modular Workflow System

## Overview

The Modular Workflow System is a new architecture that addresses the inefficiency of spinning up environments (Python, ChromeDriver, etc.) for each individual workflow execution. Instead, it provides a framework for chaining reusable operations together and sharing resources across multiple tasks.

## Key Benefits

### **1. Resource Efficiency**
- **Chrome Setup Once**: Chrome and ChromeDriver are initialized once and shared across multiple operations
- **Environment Reuse**: Python environment and dependencies are loaded once per workflow
- **Reduced Overhead**: Eliminates the startup time for each individual task

### **2. Modular Design**
- **Reusable Operations**: Common tasks are packaged as reusable operations
- **Flexible Chaining**: Operations can be combined in different ways to create workflows
- **Dependency Management**: Clear definition of operation dependencies and execution order

### **3. Batch Processing**
- **Efficient Iteration**: Operations can be applied to batches of items
- **Reduced API Calls**: Database operations are batched for better performance
- **Scalable Processing**: Handle large numbers of items efficiently

## Architecture Components

### **1. Base Operation (`BaseOperation`)**
The foundation class that all operations inherit from:

```python
class BaseOperation(ABC):
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.status = OperationStatus.PENDING
        self.dependencies = []
        self.required_inputs = []
        self.optional_inputs = []
    
    @abstractmethod
    def _execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> OperationResult:
        pass
    
    def can_apply_to_batch(self) -> bool:
        return hasattr(self, 'apply_to_batch')
```

**Features:**
- Input validation
- Status tracking
- Dependency management
- Batch processing support
- Comprehensive error handling

### **2. Operation Types**

#### **Chrome Setup Operation (`ChromeSetupOperation`)**
- Initializes Chrome and ChromeDriver once
- Stores driver instance in shared context
- Configurable options (headless, download directory, etc.)
- Automatic fallback to service-based initialization

#### **AMSC Extraction Operation (`AmscExtractionOperation`)**
- Extracts AMSC codes from NSN details pages
- Uses shared Chrome driver from context
- Handles consent pages and retry logic
- Supports batch processing over multiple NSNs
- Checks for closed solicitations

#### **Supabase Upload Operation (`SupabaseUploadOperation`)**
- Handles database uploads efficiently
- Processes batch results from previous operations
- Updates AMSC codes and closed status
- Configurable batch sizes for database operations

### **3. Workflow Orchestrator (`WorkflowOrchestrator`)**
Manages the execution of operation chains:

```python
class WorkflowOrchestrator:
    def __init__(self, name: str, description: str = ""):
        self.steps = []
        self.context = {}
        self.status = WorkflowStatus.PENDING
    
    def add_step(self, operation, inputs=None, depends_on=None, batch_config=None):
        # Add operation to workflow
        pass
    
    def execute(self, initial_context=None):
        # Execute workflow steps in order
        pass
```

**Features:**
- Dependency validation
- Circular dependency detection
- Context sharing between operations
- Batch step execution
- Comprehensive logging and error handling

## Workflow Example: Batch NSN AMSC Extraction

### **Workflow Definition**
```python
def create_batch_nsn_amsc_workflow(nsn_list, contract_ids=None, headless=True):
    workflow = WorkflowOrchestrator(
        name="batch_nsn_amsc_extraction",
        description=f"Extract AMSC codes for {len(nsn_list)} NSNs using shared Chrome instance"
    )
    
    # Step 1: Chrome Setup (runs once)
    chrome_setup = ChromeSetupOperation(headless=headless)
    workflow.add_step(
        operation=chrome_setup,
        inputs={},
        depends_on=[],
        batch_config={}
    )
    
    # Step 2: AMSC Extraction (applied to batch of NSNs)
    amsc_extraction = AmscExtractionOperation()
    workflow.add_step(
        operation=amsc_extraction,
        inputs={'timeout': 30, 'retry_attempts': 3},
        depends_on=['chrome_setup'],
        batch_config={'items': nsn_list, 'contract_ids': contract_ids}
    )
    
    # Step 3: Supabase Upload (processes all results)
    supabase_upload = SupabaseUploadOperation()
    workflow.add_step(
        operation=supabase_upload,
        inputs={'batch_size': 50, 'table_name': 'rfq_index_extract'},
        depends_on=['amsc_extraction'],
        batch_config={}
    )
    
    return workflow
```

### **Execution Flow**
1. **Chrome Setup**: Initialize Chrome/ChromeDriver once
2. **AMSC Extraction**: Process each NSN using shared driver
3. **Database Upload**: Batch upload all results to Supabase

### **Resource Sharing**
- **Chrome Driver**: Single instance shared across all NSN processing
- **Context**: Results from each step stored in shared context
- **Database Connection**: Single Supabase connection for all uploads

## Usage Examples

### **1. Command Line Usage**
```bash
# Process multiple NSNs
python workflows/adhoc/batch_nsn_amsc_extraction.py \
    1234567890123 \
    9876543210987 \
    5556667778889 \
    --contract-ids abc123 def456 ghi789 \
    --timeout 45 \
    --retry-attempts 5 \
    --batch-size 100 \
    --verbose
```

### **2. Programmatic Usage**
```python
from core.operations import ChromeSetupOperation, AmscExtractionOperation, SupabaseUploadOperation
from core.workflow_orchestrator import WorkflowOrchestrator

# Create workflow
workflow = WorkflowOrchestrator("custom_workflow")

# Add operations
workflow.add_step(ChromeSetupOperation(headless=True))
workflow.add_step(
    AmscExtractionOperation(),
    depends_on=['chrome_setup'],
    batch_config={'items': ['NSN1', 'NSN2', 'NSN3']}
)
workflow.add_step(
    SupabaseUploadOperation(),
    depends_on=['amsc_extraction']
)

# Execute
results = workflow.execute()
```

### **3. GitHub Actions Integration**
```yaml
name: Batch NSN AMSC Code Extraction
on:
  workflow_dispatch:
    inputs:
      nsns:
        description: 'Comma-separated list of NSNs to process'
        required: true
        type: string
      contract_ids:
        description: 'Optional comma-separated list of contract IDs'
        required: false
        type: string
```

## Performance Improvements

### **Before (Individual Workflows)**
```
NSN 1: Setup Chrome → Extract AMSC → Upload → Cleanup
NSN 2: Setup Chrome → Extract AMSC → Upload → Cleanup
NSN 3: Setup Chrome → Extract AMSC → Upload → Cleanup
...
Total: 3 × (Setup + Extract + Upload + Cleanup) = 12 operations
```

### **After (Modular Workflow)**
```
Setup Chrome → Extract AMSC (Batch) → Upload (Batch) → Cleanup
Total: 4 operations
```

### **Efficiency Gains**
- **Chrome Setup**: 1 time instead of N times
- **Environment Loading**: 1 time instead of N times
- **Database Connections**: 1 connection instead of N connections
- **Overall Time**: ~60-80% reduction for batch operations

## Configuration Options

### **Chrome Setup**
- `headless`: Run in headless mode (default: True)
- `download_dir`: Directory for downloads
- `chrome_options`: Custom Chrome options

### **AMSC Extraction**
- `timeout`: Page operation timeout (default: 30s)
- `retry_attempts`: Number of retry attempts (default: 3)
- `batch_config`: Configuration for batch processing

### **Supabase Upload**
- `batch_size`: Database upload batch size (default: 50)
- `table_name`: Target table name (default: 'rfq_index_extract')

## Error Handling and Recovery

### **Operation-Level Error Handling**
- Input validation
- Graceful failure with detailed error messages
- Status tracking (pending, running, completed, failed)

### **Workflow-Level Error Handling**
- Dependency validation
- Circular dependency detection
- Step failure propagation
- Comprehensive logging

### **Recovery Strategies**
- Retry logic for transient failures
- Graceful degradation for partial failures
- Resource cleanup on failure

## Monitoring and Logging

### **Operation Status Tracking**
```python
class OperationStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
```

### **Comprehensive Logging**
- Operation execution details
- Performance metrics
- Error details and stack traces
- Context information

### **Result Aggregation**
```python
@dataclass
class OperationResult:
    success: bool
    status: OperationStatus
    data: Optional[Any] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
```

## Future Enhancements

### **1. Additional Operations**
- PDF processing operations
- Data validation operations
- Notification operations
- File management operations

### **2. Advanced Features**
- Parallel execution of independent operations
- Conditional execution based on previous results
- Dynamic workflow generation
- Workflow templates

### **3. Integration Features**
- Webhook notifications
- Real-time status updates
- Performance analytics
- Resource monitoring

## Conclusion

The Modular Workflow System provides a robust, efficient framework for building complex workflows that:

1. **Eliminate Resource Waste**: Share expensive resources across operations
2. **Improve Performance**: Reduce setup/teardown overhead
3. **Enhance Maintainability**: Modular, reusable components
4. **Support Scalability**: Efficient batch processing
5. **Ensure Reliability**: Comprehensive error handling and validation

This system addresses the core inefficiency of the previous approach while providing a foundation for building more sophisticated automation workflows in the future.
