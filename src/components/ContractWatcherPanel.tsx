import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  Play, 
  Pause, 
  RefreshCw, 
  FileText, 
  Database, 
  Clock, 
  CheckCircle, 
  XCircle,
  AlertCircle,
  Settings,
  Trash2
} from 'lucide-react';
import { useContractWatcher } from '@/hooks/use-contract-watcher';
import { cn } from '@/lib/utils';

interface ContractWatcherPanelProps {
  className?: string;
  uploadedDocuments?: Array<{
    originalFileName: string;
    storagePath: string;
    [key: string]: any;
  }>;
}

export const ContractWatcherPanel: React.FC<ContractWatcherPanelProps> = ({ 
  className, 
  uploadedDocuments = [] 
}) => {
  const {
    isWatching,
    workflowQueue,
    stats,
    startWatching,
    stopWatching,
    cleanupWorkflowQueue,
    refreshContractData,
    clearWorkflowQueue
  } = useContractWatcher({
    enabled: true,
    checkInterval: 30000, // 30 seconds
    maxConcurrentWorkflows: 3,
    autoTrigger: true,
    uploadedDocuments
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-500';
      case 'running':
        return 'bg-blue-500';
      case 'completed':
        return 'bg-green-500';
      case 'failed':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending':
        return <Clock className="w-3 h-3" />;
      case 'running':
        return <RefreshCw className="w-3 h-3 animate-spin" />;
      case 'completed':
        return <CheckCircle className="w-3 h-3" />;
      case 'failed':
        return <XCircle className="w-3 h-3" />;
      default:
        return <AlertCircle className="w-3 h-3" />;
    }
  };

  const getWorkflowTypeIcon = (type: string) => {
    switch (type) {
      case 'rfq_pdf':
        return <FileText className="w-4 h-4" />;
      case 'nsn_amsc':
        return <Database className="w-4 h-4" />;
      default:
        return <AlertCircle className="w-4 h-4" />;
    }
  };

  const getWorkflowTypeLabel = (type: string) => {
    switch (type) {
      case 'rfq_pdf':
        return 'RFQ PDF';
      case 'nsn_amsc':
        return 'NSN AMSC';
      default:
        return 'Unknown';
    }
  };

  const pendingCount = workflowQueue.filter(item => item.status === 'pending').length;
  const runningCount = workflowQueue.filter(item => item.status === 'running').length;
  const completedCount = workflowQueue.filter(item => item.status === 'completed').length;
  const failedCount = workflowQueue.filter(item => item.status === 'failed').length;

  const totalWorkflows = workflowQueue.length;
  const successRate = totalWorkflows > 0 ? (completedCount / totalWorkflows) * 100 : 0;

  return (
    <Card className={cn("w-full", className)}>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between text-lg">
          <div className="flex items-center gap-2">
            <div className={cn(
              "w-3 h-3 rounded-full",
              isWatching ? "bg-green-500 animate-pulse" : "bg-gray-400"
            )} />
            Contract Watcher
          </div>
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant={isWatching ? "destructive" : "default"}
              onClick={isWatching ? stopWatching : startWatching}
              className="h-8 px-3"
            >
              {isWatching ? (
                <>
                  <Pause className="w-3 h-3 mr-1" />
                  Stop
                </>
              ) : (
                <>
                  <Play className="w-3 h-3 mr-1" />
                  Start
                </>
              )}
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={refreshContractData}
              className="h-8 px-3"
            >
              <RefreshCw className="w-3 h-3 mr-1" />
              Refresh
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={cleanupWorkflowQueue}
              className="h-8 px-3"
              disabled={completedCount === 0 && failedCount === 0}
            >
              <RefreshCw className="w-3 h-3 mr-1" />
              Cleanup
            </Button>
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
          </div>
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Status Overview */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{stats.totalContracts}</div>
            <div className="text-xs text-muted-foreground">Total Contracts</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-yellow-600">{stats.contractsWithoutAmsc}</div>
            <div className="text-xs text-muted-foreground">Need AMSC</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{stats.workflowsCompleted}</div>
            <div className="text-xs text-muted-foreground">Completed</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">{stats.workflowsFailed}</div>
            <div className="text-xs text-muted-foreground">Failed</div>
          </div>
        </div>

        {/* Success Rate */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span>Success Rate</span>
            <span className="font-medium">{successRate.toFixed(1)}%</span>
          </div>
          <Progress value={successRate} className="h-2" />
        </div>

        {/* Workflow Queue Status */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-medium">Workflow Queue</h4>
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <span>Pending: {pendingCount}</span>
              <span>Running: {runningCount}</span>
              <span>Completed: {completedCount}</span>
              <span>Failed: {failedCount}</span>
            </div>
          </div>
          
          {workflowQueue.length === 0 ? (
            <div className="text-center py-4 text-muted-foreground text-sm">
              No workflows in queue
            </div>
          ) : (
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {workflowQueue.map((item, index) => (
                <div
                  key={`${item.contractId}-${item.type}-${index}`}
                  className="flex items-center justify-between p-2 bg-muted/50 rounded-lg text-sm"
                >
                  <div className="flex items-center gap-2">
                    {getWorkflowTypeIcon(item.type)}
                    <div>
                      <div className="font-medium">{item.solicitationNumber}</div>
                      <div className="text-xs text-muted-foreground">
                        {getWorkflowTypeLabel(item.type)} • {item.nsn}
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <Badge 
                      variant="outline" 
                      className={cn(
                        "text-xs",
                        item.status === 'completed' && "border-green-500 text-green-700",
                        item.status === 'failed' && "border-red-500 text-red-700",
                        item.status === 'running' && "border-blue-500 text-blue-700"
                      )}
                    >
                      <div className={cn("w-2 h-2 rounded-full mr-1", getStatusColor(item.status))} />
                      {item.status}
                    </Badge>
                    <div className="text-xs text-muted-foreground">
                      {new Date(item.timestamp).toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Configuration Info */}
        <div className="pt-2 border-t">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>Check Interval: 30s</span>
            <span>Max Concurrent: 3</span>
            <span>Auto-trigger: {isWatching ? 'On' : 'Off'}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
