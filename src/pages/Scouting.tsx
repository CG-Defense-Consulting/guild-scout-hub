import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { DataTable } from '@/components/DataTable';
import { PricingIntelPanel } from '@/components/PricingIntelPanel';
import { useRfqData, useAwardHistory, useAddToQueue } from '@/hooks/use-database';
import { useToast } from '@/hooks/use-toast';
import { Search, Plus, TrendingUp, Calendar, Package } from 'lucide-react';

export const Scouting = () => {
  const { toast } = useToast();
  const [filters, setFilters] = useState({});
  const [selectedNsn, setSelectedNsn] = useState<string | null>(null);
  const [showPricingPanel, setShowPricingPanel] = useState(false);
  
  const { data: rfqData = [], isLoading: rfqLoading } = useRfqData(filters);
  const { data: awardData = [] } = useAwardHistory(selectedNsn || undefined);
  const addToQueue = useAddToQueue();

  const handleFilterChange = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const newFilters = Object.fromEntries(formData.entries());
    setFilters(newFilters);
  };

  const handleAddToQueue = async (rfq: any) => {
    try {
      await addToQueue.mutateAsync(rfq);
      toast({
        title: 'Added to Queue',
        description: `${rfq.national_stock_number} has been added to the contract queue.`,
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to add to queue. Please try again.',
        variant: 'destructive',
      });
    }
  };

  const handleViewPricing = (nsn: string) => {
    setSelectedNsn(nsn);
    setShowPricingPanel(true);
  };

  const columns = [
    {
      accessorKey: 'solicitation_number',
      header: 'Solicitation',
      cell: ({ getValue }: any) => (
        <div className="font-mono text-sm">{getValue()}</div>
      ),
    },
    {
      accessorKey: 'national_stock_number',
      header: 'NSN',
      cell: ({ getValue }: any) => (
        <Badge variant="secondary" className="font-mono">
          {getValue()}
        </Badge>
      ),
    },
    {
      accessorKey: 'desc',
      header: 'Description',
      cell: ({ getValue }: any) => (
        <div className="max-w-xs truncate" title={getValue()}>
          {getValue()}
        </div>
      ),
    },
    {
      accessorKey: 'quantity',
      header: 'Quantity',
      cell: ({ getValue }: any) => (
        <div className="flex items-center gap-1">
          <Package className="w-3 h-3 text-muted-foreground" />
          {getValue()?.toLocaleString()}
        </div>
      ),
    },
    {
      accessorKey: 'return_by_date',
      header: 'Close Date',
      cell: ({ getValue }: any) => (
        <div className="flex items-center gap-1">
          <Calendar className="w-3 h-3 text-muted-foreground" />
          {getValue()}
        </div>
      ),
    },
    {
      id: 'actions',
      header: 'Actions',
      cell: ({ row }: any) => (
        <div className="flex gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={() => handleViewPricing(row.original.national_stock_number)}
          >
            <TrendingUp className="w-3 h-3 mr-1" />
            Pricing
          </Button>
          <Button
            size="sm"
            onClick={() => handleAddToQueue(row.original)}
            disabled={addToQueue.isPending}
          >
            <Plus className="w-3 h-3 mr-1" />
            Queue
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-guild-brand-fg">Contract Scouting</h1>
          <p className="text-muted-foreground">Discover and analyze defense contracting opportunities</p>
        </div>
        <Badge variant="outline" className="bg-guild-accent-1/10 text-guild-accent-1">
          {rfqData.length} opportunities
        </Badge>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="w-5 h-5" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleFilterChange} className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <Label htmlFor="national_stock_number">NSN</Label>
              <Input
                id="national_stock_number"
                name="national_stock_number"
                placeholder="e.g. 5330-01-123"
              />
            </div>
            <div>
              <Label htmlFor="desc">Description</Label>
              <Input
                id="desc"
                name="desc"
                placeholder="Search description"
              />
            </div>
            <div>
              <Label htmlFor="quantity_min">Min Quantity</Label>
              <Input
                id="quantity_min"
                name="quantity_min"
                type="number"
                placeholder="0"
              />
            </div>
            <div className="flex items-end">
              <Button type="submit" className="w-full">
                <Search className="w-4 h-4 mr-2" />
                Search
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0">
          <DataTable
            data={rfqData}
            columns={columns}
            loading={rfqLoading}
          />
        </CardContent>
      </Card>

      <PricingIntelPanel
        open={showPricingPanel}
        onOpenChange={setShowPricingPanel}
        nsn={selectedNsn}
        awardData={awardData}
      />
    </div>
  );
};

export default Scouting;