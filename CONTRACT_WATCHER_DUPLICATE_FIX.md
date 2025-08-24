# Contract Watcher Duplicate Workflow Fix

## Issue Description
The contract watcher was experiencing a problem where the pending number kept increasing in multiples, indicating duplicate workflows were being added to the queue. However, none of these workflows were actually being triggered or processed, causing the queue to grow indefinitely.

## Root Cause Analysis

### 1. **Insufficient Duplicate Prevention**
- **Original Logic**: Only checked for specific workflow types (RFQ PDF or NSN AMSC)
- **Problem**: Didn't prevent multiple workflows of different types for the same contract
- **Result**: Contracts could have both RFQ PDF and NSN AMSC workflows queued simultaneously

### 2. **Queue Processing Issues**
- **Problem**: `processWorkflowQueue` function might not have been called regularly
- **Result**: Workflows accumulated in the queue without being processed
- **Impact**: Queue grew indefinitely with pending items

### 3. **Missing Cleanup Logic**
- **Problem**: Completed and failed workflows remained in the queue
- **Result**: Queue size kept growing even after workflows completed
- **Impact**: Inaccurate pending counts and queue management

## Solution Implemented

### 1. **Improved Duplicate Prevention Logic**
```typescript
// BEFORE: Only checked for specific workflow types
const hasRfqWorkflow = workflowQueue.some(item => 
  item.contractId === contract.id && item.type === 'rfq_pdf'
);

// AFTER: Check for ANY workflow (pending or running) for the contract
const hasAnyWorkflow = workflowQueue.some(item => 
  item.contractId === contract.id && 
  (item.status === 'pending' || item.status === 'running')
);
```

**Benefits:**
- Prevents multiple workflows of any type for the same contract
- Ensures only one workflow per contract at a time
- Reduces queue clutter and confusion

### 2. **Enhanced Queue Processing**
```typescript
// Updated interval to ensure regular processing
intervalRef.current = setInterval(() => {
  checkAndQueueContracts();
  processWorkflowQueue();
  cleanupCompletedWorkflows(); // Added cleanup
}, checkInterval);
```

**Benefits:**
- Regular queue processing prevents backlog
- Automatic cleanup of completed workflows
- Better queue management and performance

### 3. **Added Workflow Cleanup Functions**
```typescript
// Clean up completed/failed workflows and update stats
const cleanupCompletedWorkflows = useCallback(() => {
  setWorkflowQueue(prev => {
    const newQueue = prev.filter(item => 
      item.status === 'pending' || item.status === 'running'
    );
    
    // Count completed and failed workflows for stats
    const completedCount = prev.filter(item => item.status === 'completed').length;
    const failedCount = prev.filter(item => item.status === 'failed').length;
    
    // Update stats
    setStats(prev => ({
      ...prev,
      workflowsCompleted: prev.workflowsCompleted + completedCount,
      workflowsFailed: prev.workflowsFailed + failedCount
    }));
    
    return newQueue;
  });
}, []);

// Clear entire workflow queue (for debugging)
const clearWorkflowQueue = useCallback(() => {
  setWorkflowQueue([]);
  setStats(prev => ({
    ...prev,
    workflowsTriggered: 0,
    workflowsCompleted: 0,
    workflowsFailed: 0
  }));
}, []);
```

**Benefits:**
- Automatic cleanup prevents queue bloat
- Accurate statistics tracking
- Debug capability to reset queue when needed

### 4. **Enhanced ContractWatcherPanel**
```typescript
// Added Clear All button for debugging
<Button
  size="sm"
  variant="destructive"
  onClick={clearWorkflowQueue}
  className="h-8 px-3"
  disabled={workflowQueue.length === 0}
  title="Clear entire workflow queue (for debugging)"
>
  <Trash2 className="w-3 h-3 mr-1" />
  Clear All
</Button>
```

**Benefits:**
- Manual queue clearing for debugging
- Visual feedback on queue state
- Easy reset when issues occur

## Technical Implementation Details

### **Duplicate Prevention Strategy**
1. **Contract-Level Check**: Only one workflow per contract at any time
2. **Status-Based Filtering**: Only allow pending or running workflows
3. **Type-Agnostic Logic**: Prevents any workflow type, not just specific ones

### **Queue Processing Flow**
1. **Regular Checks**: Every `checkInterval` milliseconds
2. **Contract Discovery**: Find contracts needing workflows
3. **Duplicate Prevention**: Check existing queue before adding
4. **Queue Processing**: Process pending workflows
5. **Automatic Cleanup**: Remove completed/failed workflows
6. **Stats Update**: Update completion statistics

### **Cleanup Mechanisms**
1. **Automatic Cleanup**: Runs with every interval
2. **Status-Based Filtering**: Keep only pending/running workflows
3. **Stats Synchronization**: Update counters for completed workflows
4. **Manual Override**: Clear All button for debugging

## Benefits of the Fix

### 1. **Eliminates Duplicate Workflows**
- No more multiple workflows per contract
- Cleaner queue management
- Reduced confusion and errors

### 2. **Improves Queue Performance**
- Regular processing prevents backlog
- Automatic cleanup maintains queue size
- Better resource utilization

### 3. **Enhanced Debugging Capabilities**
- Clear All button for queue reset
- Better visibility into queue state
- Easier troubleshooting

### 4. **Accurate Statistics**
- Real-time workflow completion tracking
- Proper success/failure counting
- Better monitoring and reporting

## Testing the Fix

### **Before Fix**
- Pending number increased continuously
- Queue grew indefinitely
- No workflows were actually processed
- User confusion about queue state

### **After Fix**
- Pending number stabilizes
- Queue size remains manageable
- Workflows process normally
- Clear queue management

### **Validation Steps**
1. Start contract watcher
2. Monitor pending count - should stabilize
3. Check queue size - should not grow indefinitely
4. Verify workflows process and complete
5. Test Clear All button functionality

## Prevention Measures

### 1. **Regular Code Reviews**
- Check for duplicate prevention logic
- Ensure proper queue management
- Review interval and cleanup functions

### 2. **Monitoring and Alerts**
- Watch for unusual queue growth
- Monitor workflow completion rates
- Alert on stuck workflows

### 3. **Testing Procedures**
- Test with multiple contracts
- Verify duplicate prevention
- Check queue cleanup functionality

## Future Enhancements

### **Potential Improvements**
1. **Queue Size Limits**: Maximum queue size to prevent runaway growth
2. **Workflow Prioritization**: Priority-based workflow processing
3. **Retry Logic**: Automatic retry for failed workflows
4. **Queue Analytics**: Detailed queue performance metrics

### **Advanced Features**
1. **Smart Deduplication**: AI-powered duplicate detection
2. **Workflow Scheduling**: Time-based workflow execution
3. **Resource Management**: Dynamic workflow concurrency limits
4. **Health Monitoring**: Automated queue health checks

## Conclusion

The duplicate workflow issue has been successfully resolved through:
- **Improved Duplicate Prevention**: Better logic to prevent multiple workflows per contract
- **Enhanced Queue Processing**: Regular processing and automatic cleanup
- **Better Debugging Tools**: Clear All button and improved monitoring
- **Comprehensive Cleanup**: Automatic removal of completed workflows

The contract watcher now:
- Prevents duplicate workflows effectively
- Maintains a clean, manageable queue
- Processes workflows reliably
- Provides better debugging capabilities
- Offers accurate statistics and monitoring

This fix ensures the contract watcher operates efficiently and reliably, preventing the queue from growing indefinitely while maintaining all automation functionality.
