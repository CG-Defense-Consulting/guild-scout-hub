import React, { useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Calendar, TrendingUp, BarChart3, PieChart, Activity, DollarSign, Package, Award } from 'lucide-react';
import { useIsMobile } from '@/hooks/use-mobile';
import { useTrendsData } from '@/hooks/use-database';

// Chart components with fallback
import { LineChart, Line, BarChart, Bar, PieChart as RechartsPieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { SimpleLineChart, SimplePieChart } from '@/components/ui/chart';

export const Trends = () => {
  const isMobile = useIsMobile();
  const [dateRange, setDateRange] = useState('30d'); // 7d, 30d, 90d, 1y
  const [selectedCategory, setSelectedCategory] = useState('all');

  // Calculate date range based on selection
  const getDateRange = () => {
    const now = new Date();
    const startDate = new Date();
    
    switch (dateRange) {
      case '7d':
        startDate.setDate(now.getDate() - 7);
        break;
      case '30d':
        startDate.setDate(now.getDate() - 30);
        break;
      case '90d':
        startDate.setDate(now.getDate() - 90);
        break;
      case '1y':
        startDate.setFullYear(now.getFullYear() - 1);
        break;
      default:
        startDate.setDate(now.getDate() - 30);
    }
    
    return {
      start: startDate.toISOString().split('T')[0],
      end: now.toISOString().split('T')[0]
    };
  };

  const { start, end } = getDateRange();

  // Fetch trends data using the dedicated hook (no row limits)
  const { data: trendsData, isLoading: trendsLoading, error: trendsError } = useTrendsData(start, end);
  
  const rfqData = trendsData?.rfqData || [];
  const awardData = trendsData?.awardData || [];
  const rfqLoading = trendsLoading;
  const awardLoading = trendsLoading;
  const rfqError = trendsError;
  const awardError = trendsError;
  
  // Show data count for debugging
  const dataInfo = useMemo(() => {
    if (trendsLoading) return 'Loading data in optimized batches...';
    if (trendsError) return 'Error loading data';
    
    // Comprehensive debug logging
    console.log('=== TRENDS DATA DEBUG ===');
    console.log('RFQ Data:', {
      count: rfqData.length,
      sample: rfqData[0],
      first5Nsns: rfqData.slice(0, 5).map(r => r.national_stock_number),
      first5Dates: rfqData.slice(0, 5).map(r => r.quote_issue_date),
      first5Quantities: rfqData.slice(0, 5).map(r => r.quantity)
    });
    
    console.log('Award Data:', {
      count: awardData.length,
      sample: awardData[0],
      first5Nsns: awardData.slice(0, 5).map(a => a.national_stock_number),
      first5Dates: awardData.slice(0, 5).map(a => a.awd_date),
      first5Cages: awardData.slice(0, 5).map(a => a.cage),
      first5Totals: awardData.slice(0, 5).map(a => a.total),
      first5Quantities: awardData.slice(0, 5).map(a => a.quantity)
    });
    
    // Test the matching logic
    if (rfqData.length > 0 && awardData.length > 0) {
      const testRfq = rfqData[0];
      const testAward = awardData[0];
      
      console.log('=== MATCHING TEST ===');
      console.log('Test RFQ NSN:', testRfq.national_stock_number);
      console.log('Test Award NSN:', testAward.national_stock_number);
      console.log('NSN Match:', testRfq.national_stock_number === testAward.national_stock_number);
      
      // Check for partial matches
      const matchingAwards = awardData.filter(award => 
        award.national_stock_number === testRfq.national_stock_number
      );
      console.log('Matching awards for test RFQ:', matchingAwards.length);
      
      if (matchingAwards.length > 0) {
        console.log('Sample matching award:', matchingAwards[0]);
      }
    }
    
    return `${rfqData.length.toLocaleString()} RFQ records, ${awardData.length.toLocaleString()} award records`;
  }, [trendsLoading, trendsError, rfqData.length, awardData.length]);

  // Calculate key metrics
  const metrics = useMemo(() => {
    if (!rfqData || !awardData || !Array.isArray(rfqData) || !Array.isArray(awardData)) return null;

    const totalRfqs = rfqData.length;
    
    console.log('=== METRICS CALCULATION DEBUG ===');
    console.log('Total RFQs:', totalRfqs);
    console.log('Total Awards:', awardData.length);
    
    // Calculate contracts with award history
    const contractsWithAwardHistory = rfqData.filter(rfq => 
      awardData.some(award => award.national_stock_number === rfq.national_stock_number)
    ).length;
    
    console.log('Contracts with Award History:', contractsWithAwardHistory);
    
    // Calculate estimated total value based on award history
    let estimatedTotalValue = 0;
    let contractsWithValues = 0;
    
    rfqData.forEach((rfq, index) => {
      // Find matching awards for this NSN
      const matchingAwards = awardData.filter(award => 
        award.national_stock_number === rfq.national_stock_number
      );
      
      if (matchingAwards.length > 0) {
        contractsWithValues++;
        console.log(`RFQ ${index + 1}: Found ${matchingAwards.length} matching awards for NSN ${rfq.national_stock_number}`);
        
        // Calculate average unit cost from past awards
        const totalAwardValue = matchingAwards.reduce((sum, award) => sum + (award.total || 0), 0);
        const totalAwardQuantity = matchingAwards.reduce((sum, award) => sum + (award.quantity || 0), 0);
        
        console.log(`  Award values: ${matchingAwards.map(a => a.total).join(', ')}`);
        console.log(`  Award quantities: ${matchingAwards.map(a => a.quantity).join(', ')}`);
        console.log(`  Total award value: ${totalAwardValue}, Total award quantity: ${totalAwardQuantity}`);
        
        if (totalAwardQuantity > 0) {
          const avgUnitCost = totalAwardValue / totalAwardQuantity;
          const estimatedValue = avgUnitCost * (rfq.quantity || 0);
          estimatedTotalValue += estimatedValue;
          
          console.log(`  Avg unit cost: ${avgUnitCost}, RFQ quantity: ${rfq.quantity}, Estimated value: ${estimatedValue}`);
        }
      }
    });
    
    console.log('Total contracts with values calculated:', contractsWithValues);
    console.log('Estimated total value:', estimatedTotalValue);
    
    const totalQuantity = rfqData.reduce((sum, rfq) => sum + (rfq.quantity || 0), 0);
    const avgQuantity = totalRfqs > 0 ? totalQuantity / totalRfqs : 0;

    return {
      totalRfqs,
      contractsWithAwardHistory,
      estimatedTotalValue: estimatedTotalValue.toLocaleString('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 0 }),
      totalQuantity: totalQuantity.toLocaleString(),
      avgQuantity: Math.round(avgQuantity).toLocaleString(),
    };
  }, [rfqData, awardData]);

  // Prepare chart data
  const chartData = useMemo(() => {
    if (!rfqData || !awardData || !Array.isArray(rfqData) || !Array.isArray(awardData)) return [];

    // Group by date for time series
    const dateGroups = new Map();
    
    rfqData.forEach(rfq => {
      const date = rfq.quote_issue_date;
      if (!dateGroups.has(date)) {
        dateGroups.set(date, { date, rfqs: 0, awards: 0, value: 0 });
      }
      dateGroups.get(date).rfqs++;
    });

    awardData.forEach(award => {
      const date = award.awd_date;
      if (!dateGroups.has(date)) {
        dateGroups.set(date, { date, rfqs: 0, awards: 0, value: 0 });
      }
      const group = dateGroups.get(date);
      group.awards++;
      group.value += award.total || 0;
    });

    // Convert to array and sort by date
    return Array.from(dateGroups.values())
      .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
      .map(item => ({
        ...item,
        value: Math.round(item.value / 1000), // Convert to thousands for readability
      }));
  }, [rfqData, awardData]);

  // Category breakdown data
  const categoryData = useMemo(() => {
    if (!rfqData || !Array.isArray(rfqData)) return [];

    const categories = [
      { name: 'Weapons', prefixes: ['1005', '1010', '1015', '1020', '1025', '1030', '1035', '1040', '1045', '1055', '1070', '1080', '1090', '1095'] },
      { name: 'Electrical/Electronic', prefixes: ['5905', '5910', '5915', '5920', '5925', '5930', '5935', '5940', '5945', '5950', '5955', '5960', '5961', '5962', '5963', '5965', '5970', '5975', '5977', '5980', '5985', '5990', '5995', '5996', '5998', '5999'] },
      { name: 'Textiles', prefixes: ['83', '84', '85', '86', '87', '88', '89'] },
      { name: 'Fasteners', prefixes: ['51', '52', '53', '54', '55', '56', '57'] },
      { name: 'Other', prefixes: [] }
    ];

    return categories.map(category => {
      const count = category.prefixes.length > 0 
        ? rfqData.filter(rfq => 
            category.prefixes.some(prefix => 
              rfq.national_stock_number?.startsWith(prefix)
            )
          ).length
        : rfqData.filter(rfq => 
            !categories.slice(0, -1).some(cat => 
              cat.prefixes.some(prefix => 
                rfq.national_stock_number?.startsWith(prefix)
              )
            )
          ).length;

      return {
        name: category.name,
        value: count,
        fill: getCategoryColor(category.name),
      };
    }).filter(item => item.value > 0);
  }, [rfqData]);

  // Item name trends data (top items by frequency)
  const itemTrendsData = useMemo(() => {
    if (!rfqData || !Array.isArray(rfqData) || rfqData.length === 0) {
      console.log('No RFQ data available for item trends');
      return [];
    }

    console.log('Processing item trends data...');
    console.log('Sample RFQ items:', rfqData.slice(0, 5).map(r => r.item));

    // Count occurrences of each item name
    const itemCounts = rfqData.reduce((acc, rfq) => {
      const itemName = rfq.item?.trim() || 'Unknown Item';
      if (itemName && itemName !== '') {
        acc[itemName] = (acc[itemName] || 0) + 1;
      }
      return acc;
    }, {} as Record<string, number>);

    console.log('Item counts:', Object.keys(itemCounts).length, 'unique items');
    console.log('Top 5 items:', Object.entries(itemCounts).sort(([,a], [,b]) => b - a).slice(0, 5));

    // Get top 10 items by frequency
    const topItems = Object.entries(itemCounts)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 10)
      .map(([itemName, count], index) => ({
        name: itemName.length > 30 ? itemName.substring(0, 30) + '...' : itemName, // Truncate long names
        value: count,
        fill: `hsl(${(index * 137.5) % 360}, 70%, 50%)`, // Better color distribution
      }));

    console.log('Final item trends data:', topItems.length, 'items');
    return topItems;
  }, [rfqData]);

  // Helper function for category colors
  function getCategoryColor(categoryName: string) {
    const colors = {
      'Weapons': '#ef4444',
      'Electrical/Electronic': '#8b5cf6',
      'Textiles': '#3b82f6',
      'Fasteners': '#10b981',
      'Other': '#6b7280',
    };
    return colors[categoryName as keyof typeof colors] || '#6b7280';
  }

  // Loading state
  if (rfqLoading || awardLoading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-guild-accent-1 mx-auto mb-4"></div>
            <p className="text-muted-foreground">Loading trends data...</p>
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (rfqError || awardError) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="text-red-500 text-4xl mb-4">⚠️</div>
            <h3 className="text-lg font-semibold mb-2">Error Loading Data</h3>
            <p className="text-muted-foreground mb-4">
              {rfqError ? 'Failed to load RFQ data' : ''}
              {rfqError && awardError ? ' and ' : ''}
              {awardError ? 'Failed to load award data' : ''}
            </p>
            <Button 
              onClick={() => window.location.reload()} 
              variant="outline"
            >
              Try Again
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 md:p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-semibold text-guild-brand-fg">Contracting Trends</h1>
          <p className="text-muted-foreground">Analytics and insights from recent contract activity</p>
          <div className="text-sm text-muted-foreground mt-2">
            {dataInfo}
          </div>
        </div>
        
        {/* Controls */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Label htmlFor="date-range" className="text-sm">Time Period:</Label>
            <Select value={dateRange} onValueChange={setDateRange}>
              <SelectTrigger className="w-24">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="7d">7 Days</SelectItem>
                <SelectItem value="30d">30 Days</SelectItem>
                <SelectItem value="90d">90 Days</SelectItem>
                <SelectItem value="1y">1 Year</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          <div className="flex items-center gap-2">
            <Label htmlFor="category" className="text-sm">Category:</Label>
            <Select value={selectedCategory} onValueChange={setSelectedCategory}>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Categories</SelectItem>
                <SelectItem value="weapons">Weapons</SelectItem>
                <SelectItem value="electrical">Electrical</SelectItem>
                <SelectItem value="textiles">Textiles</SelectItem>
                <SelectItem value="fasteners">Fasteners</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              // Trigger a refresh of the data
              window.location.reload();
            }}
            className="flex items-center gap-2"
          >
            <Activity className="h-4 w-4" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total RFQs</CardTitle>
            <Package className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics?.totalRfqs.toLocaleString() || 0}</div>
            <p className="text-xs text-muted-foreground">
              Published in {dateRange === '7d' ? '7 days' : dateRange === '30d' ? '30 days' : dateRange === '90d' ? '90 days' : '1 year'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Contracts with Award History</CardTitle>
            <Award className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics?.contractsWithAwardHistory?.toLocaleString() || 0}</div>
            <p className="text-xs text-muted-foreground">
              RFQs with previous award data
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Estimated Total Value</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics?.estimatedTotalValue || '$0'}</div>
            <p className="text-xs text-muted-foreground">
              Based on award history pricing
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Quantity</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics?.totalQuantity || 0}</div>
            <p className="text-xs text-muted-foreground">
              Avg: {metrics?.avgQuantity || 0} per RFQ
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts Section */}
      <div className="space-y-6">
        {/* Main Time Series Chart - Full Width */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              RFQ Volume & Awards Over Time
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-96">
              {chartData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="date" 
                      tickFormatter={(value) => new Date(value).toLocaleDateString()}
                      angle={-45}
                      textAnchor="end"
                      height={80}
                    />
                    <YAxis />
                    <Tooltip 
                      labelFormatter={(value) => `Date: ${new Date(value).toLocaleDateString()}`}
                      formatter={(value, name) => {
                        if (name === 'rfqs') {
                          return [value, 'RFQs Published (Daily Count)'];
                        } else if (name === 'awards') {
                          return [value, 'Contracts Awarded (Daily Count)'];
                        } else if (name === 'value') {
                          return [`$${value}K`, 'Award Value (Daily Total in $K)'];
                        }
                        return [value, name];
                      }}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="rfqs" 
                      stroke="#3b82f6" 
                      strokeWidth={2}
                      name="RFQs"
                    />
                    <Line 
                      type="monotone" 
                      dataKey="awards" 
                      stroke="#10b981" 
                      strokeWidth={2}
                      name="Awards"
                    />
                    <Line 
                      type="monotone" 
                      dataKey="value" 
                      stroke="#f59e0b" 
                      strokeWidth={2}
                      name="Value"
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <SimpleLineChart data={chartData} height={384} />
              )}
            </div>
          </CardContent>
        </Card>

        {/* Distribution Charts - Side by Side */}
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          {/* Category Distribution */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <PieChart className="h-5 w-5" />
                RFQ Distribution by Category
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-80">
                {categoryData.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <RechartsPieChart>
                      <Pie
                        data={categoryData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {categoryData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.fill} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(value) => [value, 'RFQs']} />
                    </RechartsPieChart>
                  </ResponsiveContainer>
                ) : (
                  <SimplePieChart data={categoryData} height={320} />
                )}
              </div>
            </CardContent>
          </Card>

          {/* Top Items by Frequency */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Top Items by Frequency
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-80">
                {itemTrendsData.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={itemTrendsData} layout="horizontal">
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis type="number" />
                      <YAxis 
                        type="category" 
                        dataKey="name" 
                        width={150}
                        tick={{ fontSize: 11 }}
                        interval={0}
                      />
                      <Tooltip 
                        formatter={(value, name) => [value, 'RFQ Count']}
                        labelFormatter={(label) => `Item: ${label}`}
                      />
                      <Bar dataKey="value" fill="#8b5cf6" />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex items-center justify-center h-full text-muted-foreground">
                    {rfqData.length > 0 ? 'Processing item data...' : 'No item data available'}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Additional Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Top Suppliers */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Top Suppliers by Awards
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {(() => {
                if (!Array.isArray(awardData) || awardData.length === 0) {
                  return <p className="text-sm text-muted-foreground">No award data available</p>;
                }
                
                // Process CAGE data with better error handling
                const cageStats = awardData.reduce((acc, award) => {
                  const cage = award.cage;
                  if (cage && cage.trim() !== '') {
                    acc[cage] = (acc[cage] || 0) + 1;
                  }
                  return acc;
                }, {} as Record<string, number>);
                
                const topSuppliers = Object.entries(cageStats)
                  .sort(([,a], [,b]) => b - a)
                  .slice(0, 5);
                
                if (topSuppliers.length === 0) {
                  return <p className="text-sm text-muted-foreground">No valid CAGE codes found</p>;
                }
                
                return topSuppliers.map(([cage, count], index) => (
                  <div key={cage} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary" className="w-6 h-6 p-0 flex items-center justify-center text-xs">
                        {index + 1}
                      </Badge>
                      <span className="text-sm font-medium font-mono">{cage}</span>
                    </div>
                    <span className="text-sm text-muted-foreground">{count} awards</span>
                  </div>
                ));
              })()}
            </div>
          </CardContent>
        </Card>

        {/* Award Timing */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5" />
              Award Timing Analysis
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm">Same Day</span>
                <span className="text-sm font-medium">
                  {Array.isArray(awardData) ? awardData.filter(award => 
                    award.awd_date === award.awd_date
                  ).length : 0}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm">Within Week</span>
                <span className="text-sm font-medium">
                  {Array.isArray(awardData) ? awardData.filter(award => {
                    const awardDate = new Date(award.awd_date);
                    const today = new Date();
                    const diffTime = Math.abs(today.getTime() - awardDate.getTime());
                    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
                    return diffDays <= 7;
                  }).length : 0}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm">Within Month</span>
                <span className="text-sm font-medium">
                  {Array.isArray(awardData) ? awardData.filter(award => {
                    const awardDate = new Date(award.awd_date);
                    const today = new Date();
                    const diffTime = Math.abs(today.getTime() - awardDate.getTime());
                    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
                    return diffDays <= 30;
                  }).length : 0}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Value Distribution */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <DollarSign className="h-5 w-5" />
              Contract Value Distribution
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm">Under $10K</span>
                <span className="text-sm font-medium">
                  {Array.isArray(awardData) ? awardData.filter(award => (award.total || 0) < 10000).length : 0}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm">$10K - $100K</span>
                <span className="text-sm font-medium">
                  {Array.isArray(awardData) ? awardData.filter(award => (award.total || 0) >= 10000 && (award.total || 0) < 100000).length : 0}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm">$100K - $1M</span>
                <span className="text-sm font-medium">
                  {Array.isArray(awardData) ? awardData.filter(award => (award.total || 0) >= 100000 && (award.total || 0) < 1000000).length : 0}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm">Over $1M</span>
                <span className="text-sm font-medium">
                  {Array.isArray(awardData) ? awardData.filter(award => (award.total || 0) >= 1000000).length : 0}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Summary Stats */}
      <Card>
        <CardHeader>
          <CardTitle>Summary Statistics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-center">
            <div>
                              <div className="text-2xl font-bold text-blue-600">
                  {Array.isArray(rfqData) ? rfqData.filter(rfq => rfq.quantity > 1000).length : 0}
                </div>
                              <div className="text-sm text-muted-foreground">Large Volume RFQs (&gt;1K units)</div>
            </div>
            <div>
                              <div className="text-2xl font-bold text-green-600">
                  {Array.isArray(awardData) ? awardData.filter(award => (award.total || 0) > 100000).length : 0}
                </div>
                              <div className="text-sm text-muted-foreground">High Value Awards (&gt;$100K)</div>
            </div>
            <div>
                              <div className="text-2xl font-bold text-purple-600">
                  {Array.isArray(rfqData) ? new Set(rfqData.map(rfq => rfq.solicitation_number)).size : 0}
                </div>
              <div className="text-sm text-muted-foreground">Unique Solicitations</div>
            </div>
            <div>
                              <div className="text-2xl font-bold text-orange-600">
                  {Array.isArray(awardData) ? new Set(awardData.map(award => award.cage)).size : 0}
                </div>
              <div className="text-sm text-muted-foreground">Active Suppliers</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Trends;
