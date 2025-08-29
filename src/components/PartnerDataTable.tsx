import React, { useState } from 'react';
import { usePartnerQueue } from '@/hooks/use-database';
import { DataTable } from '@/components/DataTable';
import { PartnerContractDetail } from './PartnerContractDetail';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Calendar, Package, User } from 'lucide-react';
import { format } from 'date-fns';

interface PartnerContract {
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
}

interface PartnerDataTableProps {
  partnerName?: string;
}

export const PartnerDataTable: React.FC<PartnerDataTableProps> = ({ partnerName }) => {
  const { data: partnerQueue = [], isLoading, error } = usePartnerQueue(partnerName);
  const [selectedContract, setSelectedContract] = useState<PartnerContract | null>(null);

  // Debug logging
  console.log('PartnerDataTable render:', { partnerName, partnerQueue, isLoading, error });

  const getPartnerTypeColor = (type: 'MFG' | 'LOG' | 'SUP') => {
    switch (type) {
      case 'MFG': return 'bg-blue-100 text-blue-800';
      case 'LOG': return 'bg-green-100 text-green-800';
      case 'SUP': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
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

  const columns = [
    {
      accessorKey: 'id',
      header: 'Contract ID',
      headerClassName: 'font-semibold',
      cell: ({ getValue }: { getValue: () => string }) => (
        <span className="font-mono text-sm">{getValue()}</span>
      ),
    },
    {
      accessorKey: 'partner',
      header: 'Partner',
      headerClassName: 'font-semibold',
      cell: ({ getValue }: { getValue: () => string }) => (
        <div className="flex items-center gap-2">
          <User className="w-4 h-4 text-muted-foreground" />
          <span>{getValue()}</span>
        </div>
      ),
    },
    {
      accessorKey: 'partner_type',
      header: 'Type',
      headerClassName: 'font-semibold',
      cell: ({ getValue }: { getValue: () => 'MFG' | 'LOG' | 'SUP' }) => (
        <Badge className={getPartnerTypeColor(getValue())}>
          {getValue()}
        </Badge>
      ),
    },
    {
      accessorKey: 'universal_contract_queue.part_number',
      header: 'Part Number',
      headerClassName: 'font-semibold',
      cell: ({ getValue, row }: { getValue: () => string | null; row: { original: PartnerContract } }) => {
        const partNumber = row.original.universal_contract_queue?.part_number;
        return partNumber ? (
          <div className="flex items-center gap-2">
            <Package className="w-4 h-4 text-muted-foreground" />
            <span>{partNumber}</span>
          </div>
        ) : (
          <span className="text-muted-foreground">-</span>
        );
      },
    },
    {
      accessorKey: 'universal_contract_queue.current_stage',
      header: 'Stage',
      headerClassName: 'font-semibold',
      cell: ({ getValue, row }: { getValue: () => string | null; row: { original: PartnerContract } }) => {
        const stage = row.original.universal_contract_queue?.current_stage;
        return stage ? getStageBadge(stage) : (
          <span className="text-muted-foreground">-</span>
        );
      },
    },
    {
      accessorKey: 'submitted_at',
      header: 'Submitted',
      headerClassName: 'font-semibold',
      cell: ({ getValue }: { getValue: () => string }) => (
        <div className="flex items-center gap-2">
          <Calendar className="w-4 h-4 text-muted-foreground" />
          <span className="text-sm">
            {format(new Date(getValue()), 'MMM dd, yyyy')}
          </span>
        </div>
      ),
    },
    {
      accessorKey: 'submitted_by',
      header: 'Submitted By',
      headerClassName: 'font-semibold',
      cell: ({ getValue }: { getValue: () => string }) => (
        <span className="text-sm">{getValue()}</span>
      ),
    },
    {
      id: 'actions',
      header: 'Actions',
      headerClassName: 'font-semibold',
      cell: ({ row }: { row: { original: PartnerContract } }) => (
        <Button
          variant="outline"
          size="sm"
          onClick={() => setSelectedContract(row.original)}
          className="w-full"
        >
          View Details
        </Button>
      ),
    },
  ];



  return (
    <div className="space-y-4">
      {isLoading ? (
        <div className="text-center py-8">Loading partner assignments...</div>
      ) : error ? (
        <div className="text-center py-8 text-red-600">
          Error loading partner assignments: {error.message}
        </div>
      ) : partnerQueue.length === 0 ? (
        <div className="text-center py-8">
          <div className="text-lg font-semibold mb-2">No Partner Assignments Found</div>
          <p className="text-muted-foreground">
            There are currently no contracts assigned to partners in the queue.
          </p>
          <p className="text-sm text-muted-foreground mt-2">
            Contracts will appear here once they are sent to partners from the Contract Tracker.
          </p>
        </div>
      ) : (
        <>
          <DataTable
            data={partnerQueue}
            columns={columns}
            loading={isLoading}
            searchable={true}
            isMobile={false}
          />
          
          {selectedContract && (
            <PartnerContractDetail
              contract={selectedContract}
              onClose={() => setSelectedContract(null)}
            />
          )}
        </>
      )}
    </div>
  );
};
