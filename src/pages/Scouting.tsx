import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { DataTable } from '@/components/DataTable';
import { PricingIntelPanel } from '@/components/PricingIntelPanel';
import { useRfqData, useRfqDataWithSearch, useAwardHistory, useAddToQueue } from '@/hooks/use-database';
import { useToast } from '@/hooks/use-toast';
import { useAuth } from '@/hooks/use-auth';
import { useIsMobile } from '@/hooks/use-mobile';
import { useQuery } from '@tanstack/react-query';
import { supabase } from '@/integrations/supabase/client';
import { Search, Plus, TrendingUp, Calendar, Package, Tag, Filter, X } from 'lucide-react';

export const Scouting = () => {
  const { toast } = useToast();
  const { user } = useAuth();
  const isMobile = useIsMobile();
  const [filters, setFilters] = useState({});
  const [selectedNsn, setSelectedNsn] = useState<string | null>(null);
  const [showPricingPanel, setShowPricingPanel] = useState(false);
  const [showFilters, setShowFilters] = useState(!isMobile); // Hide filters by default on mobile
  
  // Category filter state
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  
  // Search term state for server-side search
  const [searchTerm, setSearchTerm] = useState('');
  
  // Sort configuration state
  const [sortConfig, setSortConfig] = useState<{
    key: string | null;
    direction: 'asc' | 'desc';
  }>({ key: null, direction: 'asc' });
  
  // Category definitions with NSN prefixes
  const categories = [
    {
      id: 'textiles',
      name: 'Textiles',
      description: 'Fabric, clothing, and textile materials',
      prefixes: ['83', '84', '85', '86', '87', '88', '89'],
      color: 'bg-blue-100 text-blue-800 border-blue-200'
    },
    {
      id: 'fasteners',
      name: 'Nuts, Bolts, Screws',
      description: 'Fasteners and hardware components',
      prefixes: ['51', '52', '53', '54', '55', '56', '57'],
      color: 'bg-green-100 text-green-800 border-green-200'
    }
  ];
  
  // Use server-side search when there's a search term, otherwise use regular filters
  const { data: rfqData = [], isLoading: rfqLoading } = useRfqDataWithSearch(filters, searchTerm);
  const { data: awardData = [] } = useAwardHistory(selectedNsn || undefined);
  const addToQueue = useAddToQueue(user?.id);
  
  // Get all award history NSNs to check availability for each row
  const { data: allAwardHistory } = useQuery({
    queryKey: ['all_award_history'],
    queryFn: async () => {
      const { data, error } = await supabase
        .from('award_history')
        .select('national_stock_number');
      if (error) throw error;
      return data?.map(record => record.national_stock_number) || [];
    },
    enabled: true, // Always fetch to check pricing availability
  });
  
  // Helper function to check if a row has award history
  const hasAwardHistory = (nsn: string) => {
    // If the award history filter is applied, all visible rows have award history
    if (filters.has_award_history) {
      return true;
    }
    // Otherwise, check against the full award history dataset
    return allAwardHistory?.includes(nsn) || false;
  };

  const handleFilterChange = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    
    const formData = new FormData(e.currentTarget);
    const newFilters = Object.fromEntries(formData.entries());
    
    // Apply category filters to NSN prefixes
    if (selectedCategories.length > 0) {
      const categoryPrefixes = selectedCategories.flatMap(catId => {
        const category = categories.find(cat => cat.id === catId);
        return category ? category.prefixes : [];
      });
      newFilters.nsnPrefixes = categoryPrefixes;
    }
    
    setFilters(newFilters);
  };

  // Helper function to check if NSN matches selected category prefixes
  const matchesCategoryFilter = (nsn: string) => {
    if (selectedCategories.length === 0) return true;
    
    const categoryPrefixes = selectedCategories.flatMap(catId => {
      const category = categories.find(cat => cat.id === catId);
      return category ? category.prefixes : [];
    });
    
    return categoryPrefixes.some(prefix => nsn.startsWith(prefix));
  };

  // Filter the data based on selected categories
  const filteredRfqData = rfqData.filter(rfq => matchesCategoryFilter(rfq.national_stock_number));



  // Set default sort to quote_issue_date descending to prioritize most recent opportunities
  React.useEffect(() => {
    if (!sortConfig.key) {
      setSortConfig({ key: 'quote_issue_date', direction: 'desc' });
    }
  }, []);

  // Handle mobile state changes
  React.useEffect(() => {
    setShowFilters(!isMobile);
  }, [isMobile]);



  const handleCategoryToggle = (categoryId: string) => {
    setSelectedCategories(prev => {
      const newSelection = prev.includes(categoryId) 
        ? prev.filter(id => id !== categoryId)
        : [...prev, categoryId];
      
      return newSelection;
    });
  };

  // Update filters when categories change
  React.useEffect(() => {
    if (selectedCategories.length > 0) {
      const categoryPrefixes = selectedCategories.flatMap(catId => {
        const category = categories.find(cat => cat.id === catId);
        return category ? category.prefixes : [];
      });
      setFilters(prev => ({ ...prev, nsnPrefixes: categoryPrefixes }));
    } else {
      setFilters(prev => {
        const { nsnPrefixes, ...rest } = prev;
        return rest;
      });
    }
  }, [selectedCategories]);

  const clearCategoryFilters = () => {
    setSelectedCategories([]);
    setFilters(prev => {
      const { nsnPrefixes, ...rest } = prev;
      return rest;
    });
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
      cell: ({ row }: any) => {
        const item = row.original.item || '';
        const desc = row.original.desc || '';
        const combinedText = item && desc ? `${item} | ${desc}` : item || desc;
        
        return (
          <div className={isMobile ? "line-clamp-2" : "max-w-xs truncate"} title={combinedText}>
            {combinedText}
          </div>
        );
      },
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
      accessorKey: 'quote_issue_date',
      header: 'Issue Date',
      cell: ({ row }: any) => (
        <div className="flex items-center gap-1">
          <Calendar className="w-3 h-3 text-muted-foreground" />
          {isMobile ? (
            <span className="text-sm">{row.original.quote_issue_date}</span>
          ) : (
            row.original.quote_issue_date
          )}
        </div>
      ),
    },
    {
      id: 'actions',
      header: 'Actions',
      cell: ({ row }: any) => (
        <div className={`flex ${isMobile ? 'flex-col space-y-2' : 'gap-2'}`}>
          <Button
            size="sm"
            variant="outline"
            onClick={() => handleViewPricing(row.original.national_stock_number)}
            disabled={!hasAwardHistory(row.original.national_stock_number)}
            className={`${!hasAwardHistory(row.original.national_stock_number) ? 'opacity-50 cursor-not-allowed' : ''} ${isMobile ? 'w-full' : ''}`}
            title={!hasAwardHistory(row.original.national_stock_number) ? 'No pricing history available' : 'View pricing history'}
          >
            <TrendingUp className="w-3 h-3 mr-1" />
            {isMobile ? 'View Pricing' : 'Pricing'}
          </Button>
          <Button
            size="sm"
            onClick={() => handleAddToQueue(row.original)}
            disabled={addToQueue.isPending}
            className={isMobile ? 'w-full' : ''}
          >
            <Plus className="w-3 h-3 mr-1" />
            {isMobile ? 'Add to Queue' : 'Queue'}
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div className="p-4 md:p-6 space-y-4 md:space-y-6">
      {/* Mobile Header */}
      {isMobile && (
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold text-guild-brand-fg">Contract Scouting</h1>
            <p className="text-sm text-muted-foreground">Discover and analyze defense contracting opportunities</p>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center gap-2"
          >
            <Filter className="w-4 h-4" />
            {showFilters ? 'Hide' : 'Show'} Filters
          </Button>
        </div>
      )}

      {/* Desktop Header */}
      {!isMobile && (
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-guild-brand-fg">Contract Scouting</h1>
            <p className="text-muted-foreground">Discover and analyze defense contracting opportunities</p>
          </div>
          <div className="flex items-center gap-3">
            {selectedCategories.length > 0 && (
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">Filtered by:</span>
                {selectedCategories.map((catId) => {
                  const category = categories.find(cat => cat.id === catId);
                  return (
                    <Badge
                      key={catId}
                      variant="secondary"
                      className="bg-guild-accent-1/20 text-guild-accent-1 border-guild-accent-1/30"
                    >
                      {category?.name}
                    </Badge>
                  );
                })}
              </div>
            )}
            <Badge variant="outline" className="bg-guild-accent-1/10 text-guild-accent-1">
              {filteredRfqData.length} opportunities
            </Badge>
          </div>
        </div>
      )}

      {/* Mobile Category Badges */}
      {isMobile && selectedCategories.length > 0 && (
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm text-muted-foreground">Filtered by:</span>
          {selectedCategories.map((catId) => {
            const category = categories.find(cat => cat.id === catId);
            return (
              <Badge
                key={catId}
                variant="secondary"
                className="bg-guild-accent-1/20 text-guild-accent-1 border-guild-accent-1/30"
              >
                {category?.name}
              </Badge>
            );
          })}
          <Badge variant="outline" className="bg-guild-accent-1/10 text-guild-accent-1">
            {filteredRfqData.length} opportunities
          </Badge>
        </div>
      )}

      {/* Filters Card - Conditionally shown on mobile */}
      {(showFilters || !isMobile) && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Search className="w-5 h-5" />
                Filters
              </CardTitle>
              {isMobile && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowFilters(false)}
                  className="p-1 h-8 w-8"
                >
                  <X className="w-4 h-4" />
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent className="space-y-4 md:space-y-6">
            {/* Category Filters */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <Label className="text-sm font-medium flex items-center gap-2">
                  <Tag className="w-4 h-4" />
                  Category Filters
                </Label>
                {selectedCategories.length > 0 && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={clearCategoryFilters}
                    className="text-xs text-muted-foreground hover:text-foreground"
                  >
                    Clear All
                  </Button>
                )}
              </div>
              <div className="grid grid-cols-1 gap-3">
                {categories.map((category) => (
                  <div
                    key={category.id}
                    className={`flex items-center space-x-3 p-3 rounded-lg border-2 transition-all cursor-pointer hover:shadow-sm ${
                      selectedCategories.includes(category.id)
                        ? 'border-guild-accent-1 bg-guild-accent-1/5'
                        : 'border-border hover:border-guild-accent-1/30'
                    }`}
                    onClick={() => handleCategoryToggle(category.id)}
                  >
                    <Checkbox
                      id={category.id}
                      checked={selectedCategories.includes(category.id)}
                      onChange={() => handleCategoryToggle(category.id)}
                      className="data-[state=checked]:bg-guild-accent-1 data-[state=checked]:border-guild-accent-1"
                    />
                    <div className="flex-1">
                      <Label
                        htmlFor={category.id}
                        className="text-sm font-medium cursor-pointer"
                      >
                        {category.name}
                      </Label>
                      <p className="text-xs text-muted-foreground mt-1">
                        {category.description}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Existing Filters */}
            <form onSubmit={handleFilterChange} className="grid grid-cols-1 gap-4">
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
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="quantity_min">Min Quantity</Label>
                  <Input
                    id="quantity_min"
                    name="quantity_min"
                    type="number"
                    placeholder="0"
                  />
                </div>
                <div>
                  <Label htmlFor="quote_issue_date_from">Issue Date From</Label>
                  <Input
                    id="quote_issue_date_from"
                    name="quote_issue_date_from"
                    type="date"
                    placeholder="Start date"
                  />
                </div>
              </div>
              <div>
                <Label htmlFor="quote_issue_date_to">Issue Date To</Label>
                <Input
                  id="quote_issue_date_to"
                  name="quote_issue_date_to"
                  type="date"
                  placeholder="End date"
                />
                <p className="text-xs text-muted-foreground mt-1">Leave blank for no end limit</p>
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="has_award_history"
                  name="has_award_history"
                  checked={filters.has_award_history || false}
                  onCheckedChange={(checked) => {
                    setFilters(prev => ({
                      ...prev,
                      has_award_history: checked === true
                    }));
                  }}
                />
                <Label htmlFor="has_award_history" className="text-sm">
                  Only show contracts with award history
                  {allAwardHistory && (
                    <span className="ml-1 text-xs text-muted-foreground">
                      ({allAwardHistory.length} available)
                    </span>
                  )}
                </Label>
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
      )}

      <Card>
        <CardContent className="p-0">
          <DataTable
            data={filteredRfqData}
            columns={columns}
            loading={rfqLoading}
            onSearchChange={setSearchTerm}
            externalSearchTerm={searchTerm}
            externalSortConfig={sortConfig}
            onSortChange={setSortConfig}
            isMobile={isMobile}
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