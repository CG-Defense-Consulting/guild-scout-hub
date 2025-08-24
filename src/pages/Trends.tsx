import React, { useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Calendar, TrendingUp, BarChart3, PieChart, Activity, DollarSign, Package, Award } from 'lucide-react';
import { useIsMobile } from '@/hooks/use-mobile';
import { useTrendsAggregated, refreshTrendsView } from '@/hooks/use-database';

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

  // Fetch aggregated trends data from the database view
  const { data: aggregatedData, isLoading: trendsLoading, error: trendsError } = useTrendsAggregated(dateRange);
  
  const rfqLoading = trendsLoading;
  const awardLoading = trendsLoading;
  const rfqError = trendsError;
  const awardError = trendsError;
  
  // Function to refresh the materialized view
  const handleRefreshTrends = async () => {
    try {
      await refreshTrendsView();
      // Refetch the data after refresh
      window.location.reload();
    } catch (error) {
      console.error('Failed to refresh trends view:', error);
    }
  };
  
  // Show data info for debugging
  const dataInfo = useMemo(() => {
    if (trendsLoading) return 'Loading aggregated trends data from materialized view...';
    if (trendsError) return 'Error loading trends data';
    
    if (aggregatedData) {
      return `Period: ${aggregatedData.period} (${aggregatedData.total_rfqs?.toLocaleString()} RFQs, ${aggregatedData.total_awards?.toLocaleString()} awards) - Data from materialized view`;
    }
    
    return 'No data available';
  }, [aggregatedData, trendsLoading, trendsError]);

  // Use aggregated metrics directly from the database view
  const metrics = useMemo(() => {
    if (!aggregatedData) return null;
    
    return {
      totalRfqs: aggregatedData.total_rfqs || 0,
      contractsWithAwardHistory: aggregatedData.contracts_with_award_history || 0,
      estimatedTotalValue: (aggregatedData.estimated_total_value || 0).toLocaleString('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 0 }),
      totalQuantity: (aggregatedData.total_quantity || 0).toLocaleString(),
      avgQuantity: Math.round(aggregatedData.avg_quantity || 0).toLocaleString(),
    };
  }, [aggregatedData]);

  // Use aggregated chart data from the database view
  const chartData = useMemo(() => {
    if (!aggregatedData?.daily_rfq_series || !aggregatedData?.daily_award_series) return [];

    // Parse the JSON data from the database view
    const rfqSeries = aggregatedData.daily_rfq_series || [];
    const awardSeries = aggregatedData.daily_award_series || [];
    
    // Create a map to combine RFQ and award data by date
    const dateGroups = new Map();
    
    // Add RFQ data
    rfqSeries.forEach((item: any) => {
      dateGroups.set(item.date, { 
        date: item.date, 
        rfqs: item.rfq_count || 0, 
        awards: 0, 
        value: 0 
      });
    });
    
    // Add award data
    awardSeries.forEach((item: any) => {
      if (dateGroups.has(item.date)) {
        const group = dateGroups.get(item.date);
        group.awards = item.award_count || 0;
        group.value = item.award_value || 0;
      } else {
        dateGroups.set(item.date, { 
          date: item.date, 
          rfqs: 0, 
          awards: item.award_count || 0, 
          value: item.award_value || 0 
        });
      }
    });

    // Convert to array and sort by date
    return Array.from(dateGroups.values())
      .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
      .map(item => ({
        ...item,
        value: Math.round((item.value || 0) / 1000), // Convert to thousands for readability
      }));
  }, [aggregatedData]);

  // Use aggregated category data from the database view
  const categoryData = useMemo(() => {
    if (!aggregatedData) return [];

    const categories = [
      { name: 'Weapons', count: aggregatedData.weapons_count || 0 },
      { name: 'Electrical/Electronic', count: aggregatedData.electrical_count || 0 },
      { name: 'Textiles', count: aggregatedData.textiles_count || 0 },
      { name: 'Fasteners', count: aggregatedData.fasteners_count || 0 },
      { name: 'Other', count: aggregatedData.other_count || 0 }
    ];

    return categories
      .filter(category => category.count > 0)
      .map(category => ({
        name: category.name,
        value: category.count,
        fill: getCategoryColor(category.name),
      }));
  }, [aggregatedData]);

  // Use aggregated item trends data from the database view
  const itemTrendsData = useMemo(() => {
    if (!aggregatedData?.top_items) return [];

    const topItems = aggregatedData.top_items || [];
    
    return topItems.map((item: any, index: number) => ({
      name: (item.item || 'Unknown Item').length > 30 ? (item.item || 'Unknown Item').substring(0, 30) + '...' : (item.item || 'Unknown Item'),
      value: item.count || 0,
      fill: `hsl(${(index * 137.5) % 360}, 70%, 50%)`, // Better color distribution
    }));
  }, [aggregatedData]);

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
            onClick={handleRefreshTrends}
            className="flex items-center gap-2"
            title="Refresh materialized view data"
          >
            <Activity className="h-4 w-4" />
            Refresh Data
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
                    {aggregatedData?.top_items && aggregatedData.top_items.length > 0 ? 'Processing item data...' : 'No item data available'}
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
                                if (!aggregatedData?.top_suppliers || aggregatedData.top_suppliers.length === 0) {
                  return <p className="text-sm text-muted-foreground">No award data available</p>;
                }
                
                const topSuppliers = aggregatedData.top_suppliers.slice(0, 5);
                
                return topSuppliers.map((supplier: any, index: number) => (
                  <div key={supplier.cage} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary" className="w-6 h-6 p-0 flex items-center justify-center text-xs">
                        {index + 1}
                      </Badge>
                      <span className="text-sm font-medium font-mono">{supplier.cage}</span>
                    </div>
                    <span className="text-sm text-muted-foreground">{supplier.award_count} awards</span>
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
                  {/* TODO: Add same day awards count to aggregated view */}
                  {0}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm">Within Week</span>
                <span className="text-sm font-medium">
                  {/* TODO: Add recent awards count to aggregated view */}
                  {0}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm">Within Month</span>
                <span className="text-sm font-medium">
                  {/* TODO: Add recent awards count to aggregated view */}
                  {0}
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
                  {aggregatedData?.awards_under_10k || 0}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm">$10K - $100K</span>
                <span className="text-sm font-medium">
                  {aggregatedData?.awards_10k_to_100k || 0}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm">$100K - $1M</span>
                <span className="text-sm font-medium">
                  {aggregatedData?.awards_100k_to_1m || 0}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm">Over $1M</span>
                <span className="text-sm font-medium">
                  {aggregatedData?.awards_over_1m || 0}
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
                  {/* TODO: Add large volume RFQs count to aggregated view */}
                  {0}
                </div>
                              <div className="text-sm text-muted-foreground">Large Volume RFQs (&gt;1K units)</div>
            </div>
            <div>
                              <div className="text-2xl font-bold text-green-600">
                  {aggregatedData?.awards_100k_to_1m || 0 + (aggregatedData?.awards_over_1m || 0)}
                </div>
                              <div className="text-sm text-muted-foreground">High Value Awards (&gt;$100K)</div>
            </div>
            <div>
                              <div className="text-2xl font-bold text-purple-600">
                  {aggregatedData?.unique_solicitations || 0}
                </div>
              <div className="text-sm text-muted-foreground">Unique Solicitations</div>
            </div>
            <div>
                              <div className="text-2xl font-bold text-orange-600">
                  {aggregatedData?.unique_suppliers || 0}
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
