import React, { useState, useEffect } from 'react';
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
import { GITHUB_CONFIG, getGitHubToken } from '@/config/github';
import { Search, Plus, TrendingUp, Calendar, Package, Tag, Filter, X, ChevronDown, ChevronUp, ExternalLink, FileText, Database } from 'lucide-react';

// RFQ PDF Button Component
const RfqPdfButton = ({ solicitationNumber, nsn }: { solicitationNumber: string; nsn: string }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [hasPdf, setHasPdf] = useState(false);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const { toast } = useToast();

  // Check if RFQ PDF exists in Supabase
  useEffect(() => {
    const checkForRfqPdf = async () => {
      try {
        const { data: files, error } = await supabase.storage
          .from('docs')
          .list('', {
            search: `rfq-${solicitationNumber}-`
          });

        if (error) {
          console.error('Error checking for RFQ PDF:', error);
          return;
        }

        if (files && files.length > 0) {
          // Get the first RFQ PDF file
          const rfqFile = files[0];
          
          // Create a signed URL for the PDF
          const { data: urlData, error: urlError } = await supabase.storage
            .from('docs')
            .createSignedUrl(rfqFile.name, 3600); // 1 hour expiry

          if (urlError) {
            console.error('Error creating signed URL:', urlError);
            return;
          }

          setHasPdf(true);
          setPdfUrl(urlData.signedUrl);
        }
      } catch (error) {
        console.error('Error checking for RFQ PDF:', error);
      }
    };

    checkForRfqPdf();
  }, [solicitationNumber]);

  const handleClick = async () => {
    if (hasPdf && pdfUrl) {
      // Open the PDF from Supabase
      window.open(pdfUrl, '_blank');
    } else {
      // Fallback to direct DIBBS link
      const lastChar = solicitationNumber.slice(-1);
      const dibbsUrl = `https://dibbs2.bsm.dla.mil/Downloads/RFQ/${lastChar}/${solicitationNumber}.PDF`;
      window.open(dibbsUrl, '_blank');
    }
  };

  const handlePullRfqPdf = async () => {
    if (isLoading) return;
    
    setIsLoading(true);
    
    try {
      // Check if GitHub token is available
      const githubToken = getGitHubToken();
      if (!githubToken) {
        toast({
          title: 'GitHub Token Required',
          description: 'Please configure your GitHub token to trigger workflows.',
          variant: 'destructive',
        });
        return;
      }

      // Trigger GitHub Actions workflow via API
      const response = await fetch(`${GITHUB_CONFIG.API_BASE}/repos/${GITHUB_CONFIG.OWNER}/${GITHUB_CONFIG.REPO}/dispatches`, {
        method: 'POST',
        headers: {
          'Authorization': `token ${githubToken}`,
          'Accept': 'application/vnd.github.v3+json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          event_type: GITHUB_CONFIG.WORKFLOW_EVENTS.PULL_SINGLE_RFQ_PDF,
          client_payload: {
            solicitation_number: solicitationNumber
          }
        })
      });

      if (response.ok) {
        toast({
          title: 'Workflow Triggered',
          description: `RFQ PDF download workflow has been started for ${solicitationNumber}. Check the Actions tab for progress.`,
        });
        
        // Start polling for the PDF to appear
        startPollingForRfqPdf();
      } else {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Error triggering workflow:', error);
      toast({
        title: 'Error',
        description: 'Failed to trigger RFQ PDF download workflow. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const startPollingForRfqPdf = () => {
    // Poll every 10 seconds for up to 5 minutes
    let attempts = 0;
    const maxAttempts = 30;
    
    const pollInterval = setInterval(async () => {
      attempts++;
      
      try {
        const { data: files, error } = await supabase.storage
          .from('docs')
          .list('', {
            search: `rfq-${solicitationNumber}-`
          });

        if (error) {
          console.error('Error checking for RFQ PDF:', error);
        } else if (files && files.length > 0) {
          // RFQ PDF found! Stop polling
          clearInterval(pollInterval);
          
          // Get the signed URL
          const rfqFile = files[0];
          const { data: urlData, error: urlError } = await supabase.storage
            .from('docs')
            .createSignedUrl(rfqFile.name, 3600);

          if (!urlError && urlData) {
            setHasPdf(true);
            setPdfUrl(urlData.signedUrl);
            
            toast({
              title: 'RFQ PDF Ready!',
              description: 'The RFQ PDF has been downloaded and is now available.',
            });
          }
        }
      } catch (error) {
        console.error('Error during polling:', error);
      }
      
      if (attempts >= maxAttempts) {
        clearInterval(pollInterval);
        toast({
          title: 'Polling Timeout',
          description: 'RFQ PDF download is taking longer than expected. Check the Actions tab for status.',
        });
      }
    }, 10000); // 10 seconds
  };

  return (
    <div className="flex gap-1">
      <Button
        size="sm"
        variant="ghost"
        className="h-6 px-2 text-xs text-blue-600 hover:text-blue-700 hover:bg-blue-50"
        onClick={handleClick}
        title={hasPdf ? "View RFQ PDF from Supabase" : "View RFQ PDF from DIBBS"}
      >
        <FileText className="w-3 h-3 mr-1" />
        PDF
      </Button>
      
      {!hasPdf && (
        <Button
          size="sm"
          variant="ghost"
          className="h-6 px-1 text-xs text-green-600 hover:text-green-700 hover:bg-green-50"
          onClick={handlePullRfqPdf}
          disabled={isLoading}
          title="Pull RFQ PDF to Supabase"
        >
          {isLoading ? '...' : '+'}
        </Button>
      )}
    </div>
  );
};

export const Scouting = () => {
  const { toast } = useToast();
  const { user } = useAuth();
  const isMobile = useIsMobile();
  const [filters, setFilters] = useState<Record<string, any>>({});
  const [selectedNsn, setSelectedNsn] = useState<string | null>(null);
  const [showPricingPanel, setShowPricingPanel] = useState(false);
  const [showFilters, setShowFilters] = useState(!isMobile); // Hide filters by default on mobile
  
  // Desktop filter collapse state
  const [desktopFiltersCollapsed, setDesktopFiltersCollapsed] = useState(false);
  
  // Category filter state
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  
  // Search term state for server-side search
  const [searchTerm, setSearchTerm] = useState('');
  
  // Sort configuration state - now supports multi-column sorting
  // Default: sort by quote_issue_date descending (newest first) with priority 1
  const [sortConfig, setSortConfig] = useState<Array<{
    key: string;
    direction: 'asc' | 'desc';
    priority: number;
  }>>([{ key: 'quote_issue_date', direction: 'desc', priority: 1 }]);
  
  // Category definitions with NSN prefixes
  const categories = [
    {
      id: 'weapons',
      name: 'Weapons',
      description: 'Weapons and weapon systems',
      prefixes: ['1005', '1010', '1015', '1020', '1025', '1030', '1035', '1040', '1045', '1055', '1070', '1080', '1090', '1095'],
      color: 'bg-red-100 text-red-800 border-red-200'
    },
    {
      id: 'electrical',
      name: 'Electrical/Electronic',
      description: 'Electrical and electronic equipment components',
      prefixes: ['5905', '5910', '5915', '5920', '5925', '5930', '5935', '5940', '5945', '5950', '5955', '5960', '5961', '5962', '5963', '5965', '5970', '5975', '5977', '5980', '5985', '5990', '5995', '5996', '5998', '5999'],
      color: 'bg-purple-100 text-purple-800 border-purple-200'
    },
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
      (newFilters as any).nsnPrefixes = categoryPrefixes;
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

  // Calculate how many RFQ records have award history
  const rfqRecordsWithAwardHistory = allAwardHistory ? 
    filteredRfqData.filter(rfq => allAwardHistory.includes(rfq.national_stock_number)).length : 0;





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
      headerClassName: 'w-48', // Set fixed width for Actions column
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
          
          {/* External Links Row */}
          <div className={`flex ${isMobile ? 'flex-col space-y-1' : 'gap-1'} mt-1`}>
            {/* RFQ PDF Link */}
            {row.original.solicitation_number && (
              <RfqPdfButton 
                solicitationNumber={row.original.solicitation_number}
                nsn={row.original.national_stock_number}
              />
            )}
            
            {/* Tech Doc Link */}
            {row.original.solicitation_number && (
              <Button
                size="sm"
                variant="ghost"
                className="h-6 px-2 text-xs text-green-600 hover:text-green-700 hover:bg-green-50"
                onClick={() => {
                  const url = `https://pcf1x.bsm.dla.mil/cfolders/fol_de.htm?p_sol_no=${row.original.solicitation_number}`;
                  window.open(url, '_blank');
                }}
                title="View Technical Documentation"
              >
                <ExternalLink className="w-3 h-3 mr-1" />
                Tech
              </Button>
            )}
            
            {/* NSN Detail Link */}
            {row.original.national_stock_number && (
              <Button
                size="sm"
                variant="ghost"
                className="h-6 px-2 text-xs text-purple-600 hover:text-purple-700 hover:bg-purple-50"
                onClick={() => {
                  const url = `https://www.dibbs.bsm.dla.mil/RFQ/RFQNsn.aspx?value=${row.original.national_stock_number}&category=nsn`;
                  window.open(url, '_blank');
                }}
                title="View NSN Details"
              >
                <Database className="w-3 h-3 mr-1" />
                NSN
              </Button>
              )}
          </div>
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
              <div className="flex items-center gap-2">
                {!isMobile && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setDesktopFiltersCollapsed(!desktopFiltersCollapsed)}
                    className="flex items-center gap-2"
                  >
                    {desktopFiltersCollapsed ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
                    {desktopFiltersCollapsed ? 'Expand' : 'Collapse'}
                  </Button>
                )}
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
            </div>
          </CardHeader>
          {!desktopFiltersCollapsed && (
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
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
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
                      <div className="flex-1 min-w-0">
                        <Label
                          htmlFor={category.id}
                          className="text-sm font-medium cursor-pointer truncate"
                        >
                          {category.name}
                        </Label>
                        <p className="text-xs text-muted-foreground mt-1 truncate">
                          {category.description}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Existing Filters */}
              <form onSubmit={handleFilterChange} className="space-y-6">
              {/* Basic Search Fields */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="md:col-span-1">
                  <Label htmlFor="national_stock_number">NSN</Label>
                  <Input
                    id="national_stock_number"
                    name="national_stock_number"
                    placeholder="e.g. 5330-01-123"
                    maxLength={15}
                    className="font-mono"
                  />
                </div>
                <div className="md:col-span-1">
                  <Label htmlFor="solicitation_number">Solicitation Number</Label>
                  <Input
                    id="solicitation_number"
                    name="solicitation_number"
                    placeholder="e.g. N00123"
                    maxLength={15}
                    className="font-mono"
                  />
                </div>
                <div className="md:col-span-1">
                  <Label htmlFor="desc">Description</Label>
                  <Input
                    id="desc"
                    name="desc"
                    placeholder="Search description"
                  />
                </div>
              </div>

              {/* Date & Quantity Range Section */}
              <div className="space-y-3">
                <Label className="text-sm font-medium text-muted-foreground">Date & Quantity Ranges</Label>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div>
                    <Label htmlFor="quote_issue_date_from">From</Label>
                    <Input
                      id="quote_issue_date_from"
                      name="quote_issue_date_from"
                      type="date"
                      placeholder="Start date"
                      className="text-sm"
                    />
                  </div>
                  <div>
                    <Label htmlFor="quote_issue_date_to">To</Label>
                    <Input
                      id="quote_issue_date_to"
                      name="quote_issue_date_to"
                      type="date"
                      placeholder="End date"
                      className="text-sm"
                    />
                  </div>
                  <div>
                    <Label htmlFor="quantity_min">Min Qty</Label>
                    <Input
                      id="quantity_min"
                      name="quantity_min"
                      type="number"
                      placeholder="0"
                      min="0"
                      className="text-sm"
                    />
                  </div>
                  <div>
                    <Label htmlFor="quantity_max">Max Qty</Label>
                    <Input
                      id="quantity_max"
                      name="quantity_max"
                      type="number"
                      placeholder="No limit"
                      min="0"
                      className="text-sm"
                    />
                  </div>
                </div>
                <p className="text-xs text-muted-foreground">Leave date fields blank for no end limit</p>
              </div>

              {/* Award History Filter */}
              <div className="flex items-center space-x-2 p-3 bg-muted/30 rounded-lg">
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
                                  <Label htmlFor="has_award_history" className="text-sm cursor-pointer">
                    Only show contracts with award history
                  </Label>
              </div>

              {/* Action Buttons */}
              <div className="flex items-end gap-3">
                <Button type="submit" className="flex-1 md:flex-none md:w-auto px-8">
                  <Search className="w-4 h-4 mr-2" />
                  Search
                </Button>
                <Button 
                  type="button" 
                  variant="outline" 
                  onClick={() => {
                    setFilters({});
                    setSelectedCategories([]);
                    setSortConfig([{ key: 'quote_issue_date', direction: 'desc', priority: 1 }]);
                    setSearchTerm('');
                  }}
                  className="flex-1 md:flex-none md:w-auto"
                >
                  <X className="w-4 h-4 mr-2" />
                  Clear All
                </Button>
              </div>
            </form>
          </CardContent>
            )}
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