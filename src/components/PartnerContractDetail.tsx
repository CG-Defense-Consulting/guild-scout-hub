import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

import { Calendar, User, Package, FileText, CheckCircle, Clock, AlertTriangle } from 'lucide-react';
import { format } from 'date-fns';

interface PartnerContractDetailProps {
  contract: {
    id: string;
    partner: string;
    submitted_at: string;
    submitted_by: string;
    partner_type: 'MFG' | 'LOG' | 'SUP';
    universal_contract_queue: {
      id: string;
      part_number: string | null;
      long_description: string | null;
      current_stage: string | null;
      created_at: string;
    };
  };
  onClose: () => void;
}

export const PartnerContractDetail: React.FC<PartnerContractDetailProps> = ({ contract, onClose }) => {
  const getPartnerTypeColor = (type: 'MFG' | 'LOG' | 'SUP') => {
    switch (type) {
      case 'MFG': return 'bg-blue-100 text-blue-800';
      case 'LOG': return 'bg-green-100 text-green-800';
      case 'SUP': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStageIcon = (stage?: string) => {
    switch (stage) {
      case 'completed': return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'overdue': return <AlertTriangle className="w-4 h-4 text-red-600" />;
      default: return <Clock className="w-4 h-4 text-yellow-600" />;
    }
  };

  const getStageBadge = (stage?: string) => {
    switch (stage) {
      case 'completed': 
        return <Badge className="bg-green-100 text-green-800">Completed</Badge>;
      case 'overdue': 
        return <Badge className="bg-red-100 text-red-800">Overdue</Badge>;
      default: 
        return <Badge className="bg-yellow-100 text-yellow-800">In Progress</Badge>;
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <Card className="w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
          <CardTitle className="text-xl font-semibold">Contract Details</CardTitle>
          <Button variant="ghost" size="sm" onClick={onClose}>
            ✕
          </Button>
        </CardHeader>
        
        <CardContent className="space-y-6">
          {/* Contract Overview */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground">Contract ID</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-lg font-mono">{contract.id}</p>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground">Partner Type</CardTitle>
              </CardHeader>
              <CardContent>
                <Badge className={getPartnerTypeColor(contract.partner_type)}>
                  {contract.partner_type}
                </Badge>
              </CardContent>
            </Card>
          </div>

          {/* Contract Details */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Package className="w-5 h-5" />
                Contract Information
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {contract.universal_contract_queue.part_number && (
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Part Number</label>
                  <p className="text-base">{contract.universal_contract_queue.part_number}</p>
                </div>
              )}
              
              {contract.universal_contract_queue.long_description && (
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Description</label>
                  <p className="text-base">{contract.universal_contract_queue.long_description}</p>
                </div>
              )}
              
              <div>
                <label className="text-sm font-medium text-muted-foreground">Current Stage</label>
                <div className="flex items-center gap-2 mt-1">
                  {getStageIcon(contract.universal_contract_queue.current_stage)}
                  {getStageBadge(contract.universal_contract_queue.current_stage)}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Timeline Information */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="w-5 h-5" />
                Timeline
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium text-muted-foreground">Contract Created</label>
                <p className="text-base">
                  {format(new Date(contract.universal_contract_queue.created_at), 'PPP')}
                </p>
              </div>
              
              <div>
                <label className="text-sm font-medium text-muted-foreground">Submitted to Partner</label>
                <p className="text-base">
                  {format(new Date(contract.submitted_at), 'PPP')}
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Partner Information */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="w-5 h-5" />
                Partner Information
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium text-muted-foreground">Partner Name</label>
                <p className="text-base">{contract.partner}</p>
              </div>
              
              <div>
                <label className="text-sm font-medium text-muted-foreground">Submitted By</label>
                <p className="text-base">{contract.submitted_by}</p>
              </div>
            </CardContent>
          </Card>

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-3 pt-4">
            <Button className="flex-1" variant="default">
              <FileText className="w-4 h-4 mr-2" />
              View Full Contract
            </Button>
            
            <Button className="flex-1" variant="outline">
              <CheckCircle className="w-4 h-4 mr-2" />
              Mark as Reviewed
            </Button>
            
            <Button className="flex-1" variant="outline">
              <Package className="w-4 h-4 mr-2" />
              Request Quote
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
