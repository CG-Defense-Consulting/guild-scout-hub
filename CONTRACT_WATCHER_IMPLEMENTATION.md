# Contract Watcher Implementation

## Overview
The Contract Watcher is an automated system that monitors contracts in the `universal_contract_queue` and automatically triggers RFQ PDF and NSN AMSC workflows for contracts that don't have AMSC codes extracted.

## Features

### 🔄 **Automatic Workflow Detection**
- Monitors all contracts in the universal contract queue
- Identifies contracts missing AMSC codes (`cde_g` field is NULL)
- Automatically queues workflows for contracts needing data extraction

### 📋 **Workflow Sequencing**
- **First**: RFQ PDF workflow to download and process the solicitation document
- **Then**: NSN AMSC workflow to extract AMSC codes from the NSN details page
- Ensures proper workflow order and dependencies

### ⚡ **Smart Queue Management**
- Configurable concurrent workflow limits (default: 3)
- Automatic cleanup of completed/failed workflows
- Prevents duplicate workflow queuing
- Real-time status tracking for all workflows

### 🎛️ **Manual Controls**
- Start/Stop automatic monitoring
- Manual workflow triggering for specific contracts
- Refresh contract data and cleanup workflows
- Real-time statistics and progress tracking

## Architecture

### Core Components

#### 1. **useContractWatcher Hook** (`src/hooks/use-contract-watcher.tsx`)
- Main watcher logic and state management
- Workflow queue management
- Automatic detection and queuing
- Integration with workflow triggers

#### 2. **ContractWatcherPanel Component** (`src/components/ContractWatcherPanel.tsx`)
- UI for monitoring and controlling the watcher
- Real-time status display
- Workflow queue visualization
- Control buttons for manual operations

#### 3. **Integration with Tracker Page** (`src/pages/Tracker.tsx`)
- Embedded watcher panel
- Toggle visibility controls
- Seamless integration with contract management

#### 4. **Enhanced Kanban Board** (`src/components/KanbanBoard.tsx`)
- Visual indicators for contracts needing workflows
- Manual workflow trigger buttons
- Status badges showing workflow requirements

## Configuration

### Default Settings
```typescript
{
  enabled: true,                    // Enable/disable the watcher
  checkInterval: 30000,            // Check for new contracts every 30 seconds
  maxConcurrentWorkflows: 3,       // Maximum workflows running simultaneously
  autoTrigger: true                // Automatically start workflows
}
```

### Customization
The watcher can be configured with different settings for different use cases:
- **Development**: Shorter intervals, fewer concurrent workflows
- **Production**: Longer intervals, more concurrent workflows
- **Manual Mode**: Disable auto-trigger, use only manual controls

## Workflow Logic

### 1. **Contract Detection**
```typescript
const contractsNeedingWorkflows = contracts.filter(contract => {
  const hasNoAmsc = !contract.cde_g;                    // No AMSC code
  const notInQueue = !workflowQueue.some(/* ... */);    // Not already queued
  const hasRequiredData = contract.solicitation_number && contract.national_stock_number;
  
  return hasNoAmsc && notInQueue && hasRequiredData;
});
```

### 2. **Workflow Sequencing**
```typescript
// First: Queue RFQ PDF workflow
addToWorkflowQueue(contract, 'rfq_pdf');

// After RFQ PDF completion: Queue NSN AMSC workflow
if (result && workflow.type === 'rfq_pdf') {
  setTimeout(() => {
    checkForNsnAmscWorkflow(workflow.contractId);
  }, 5000); // 5 second delay
}
```

### 3. **Queue Management**
```typescript
const processWorkflowQueue = async () => {
  const pendingWorkflows = workflowQueue.filter(item => item.status === 'pending');
  const availableSlots = maxConcurrentWorkflows - runningWorkflowsRef.current.size;
  
  // Process available workflows up to the concurrent limit
  const workflowsToProcess = pendingWorkflows.slice(0, availableSlots);
  // ... process workflows
};
```

## User Interface

### Contract Watcher Panel
- **Status Overview**: Total contracts, contracts needing AMSC, completed/failed workflows
- **Success Rate**: Visual progress bar showing workflow success percentage
- **Workflow Queue**: Real-time list of pending, running, completed, and failed workflows
- **Controls**: Start/Stop, Refresh, Cleanup buttons

### Kanban Board Enhancements
- **"Needs Workflow" Badge**: Yellow badge for contracts without AMSC codes
- **Manual Trigger Button**: Blue play button for manual workflow initiation
- **Status Indicators**: Visual feedback for workflow requirements

### Contract Detail Integration
- **AMSC Code Field**: Shows extracted code or "Not extracted"
- **Solicitation Status**: Displays closed/open/unknown status
- **Workflow History**: Tracks workflow execution status

## Error Handling

### Workflow Failures
- Failed workflows are marked and tracked
- Error messages are displayed to users
- Failed workflows can be retried manually
- Statistics track failure rates

### Data Validation
- Checks for required contract data before queuing
- Prevents workflows for contracts with missing information
- Validates workflow prerequisites

### Network Issues
- Graceful handling of API failures
- Retry mechanisms for failed requests
- User notifications for connectivity issues

## Monitoring and Statistics

### Real-time Metrics
- **Total Contracts**: Number of contracts in the queue
- **Contracts Needing AMSC**: Contracts without extracted AMSC codes
- **Workflows Triggered**: Total workflows started
- **Workflows Completed**: Successfully completed workflows
- **Workflows Failed**: Failed workflow attempts

### Performance Tracking
- Success rate calculation
- Workflow execution time monitoring
- Queue depth and processing speed
- Resource utilization tracking

## Security and Permissions

### Access Control
- Only authenticated users can access the watcher
- Workflow triggering requires proper permissions
- Contract data access is restricted by user role

### Audit Trail
- All workflow actions are logged
- User actions are tracked
- Workflow history is maintained
- Change tracking for contract status updates

## Future Enhancements

### Planned Features
1. **Bulk Operations**: Process multiple contracts simultaneously
2. **Advanced Scheduling**: Configurable workflow timing and priorities
3. **Workflow Templates**: Customizable workflow configurations
4. **Integration APIs**: Webhook support for external systems
5. **Advanced Analytics**: Detailed performance metrics and reporting

### Scalability Improvements
1. **Distributed Processing**: Support for multiple watcher instances
2. **Queue Persistence**: Persistent workflow queue storage
3. **Load Balancing**: Intelligent workflow distribution
4. **Resource Optimization**: Dynamic concurrent workflow limits

## Usage Examples

### Starting the Watcher
```typescript
const { startWatching, stopWatching } = useContractWatcher({
  enabled: true,
  autoTrigger: true
});

// Automatically starts monitoring
// Manually control if needed
startWatching();
stopWatching();
```

### Manual Workflow Trigger
```typescript
const { triggerWorkflowsForContract } = useContractWatcher();

// Trigger workflows for a specific contract
await triggerWorkflowsForContract(contract);
```

### Custom Configuration
```typescript
const watcher = useContractWatcher({
  enabled: true,
  checkInterval: 60000,        // Check every minute
  maxConcurrentWorkflows: 5,   // Allow 5 concurrent workflows
  autoTrigger: false           // Manual control only
});
```

## Troubleshooting

### Common Issues
1. **Workflows Not Starting**: Check if watcher is enabled and auto-trigger is on
2. **High Failure Rate**: Verify network connectivity and API endpoints
3. **Queue Not Processing**: Check concurrent workflow limits and running workflows
4. **Missing Data**: Ensure contracts have required solicitation numbers and NSNs

### Debug Information
- Check browser console for error messages
- Monitor workflow queue status in real-time
- Review contract data completeness
- Verify workflow trigger permissions

## Conclusion

The Contract Watcher provides a robust, automated solution for ensuring all contracts in the queue have the necessary data extracted. It combines intelligent detection, efficient queue management, and comprehensive monitoring to streamline the contract processing workflow.

The system is designed to be:
- **Automated**: Requires minimal manual intervention
- **Reliable**: Handles errors gracefully and provides clear feedback
- **Scalable**: Configurable for different workloads and environments
- **User-Friendly**: Clear visual indicators and intuitive controls
- **Maintainable**: Well-structured code with comprehensive error handling
