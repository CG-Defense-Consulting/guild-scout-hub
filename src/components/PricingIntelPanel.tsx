import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { TrendingUp, DollarSign, Calendar, Award } from 'lucide-react';

interface PricingIntelPanelProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  nsn: string | null;
  awardData: any[];
}

export const PricingIntelPanel = ({ open, onOpenChange, nsn, awardData }: PricingIntelPanelProps) => {
  // Calculate pricing statistics
  const prices = awardData.map(award => award.unit_cost).filter(Boolean);
  const minPrice = prices.length > 0 ? Math.min(...prices) : 0;
  const maxPrice = prices.length > 0 ? Math.max(...prices) : 0;
  const avgPrice = prices.length > 0 ? prices.reduce((a, b) => a + b, 0) / prices.length : 0;

  // Prepare chart data
  const chartData = awardData
    .sort((a, b) => new Date(a.awd_date).getTime() - new Date(b.awd_date).getTime())
    .map(award => ({
      date: new Date(award.awd_date).toLocaleDateString(),
      price: award.unit_cost,
      quantity: award.quantity,
      contractor: award.cage
    }));

  // Price distribution data
  const priceRanges = [
    { range: '$0-$100', count: prices.filter(p => p <= 100).length },
    { range: '$100-$500', count: prices.filter(p => p > 100 && p <= 500).length },
    { range: '$500-$1K', count: prices.filter(p => p > 500 && p <= 1000).length },
    { range: '$1K+', count: prices.filter(p => p > 1000).length },
  ];

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full sm:max-w-4xl overflow-y-auto">
        <SheetHeader className="pb-4">
          <SheetTitle className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5" />
            Pricing Intelligence: {nsn}
          </SheetTitle>
          <SheetDescription>
            Historical pricing data and market analysis for this NSN
          </SheetDescription>
        </SheetHeader>

        <div className="space-y-6">
          {/* Key Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-2">
                  <DollarSign className="w-4 h-4 text-guild-success" />
                  <span className="text-sm font-medium">Min Price</span>
                </div>
                <p className="text-2xl font-bold text-guild-success">
                  ${minPrice.toFixed(2)}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-2">
                  <DollarSign className="w-4 h-4 text-guild-warning" />
                  <span className="text-sm font-medium">Avg Price</span>
                </div>
                <p className="text-2xl font-bold text-guild-warning">
                  ${avgPrice.toFixed(2)}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-2">
                  <DollarSign className="w-4 h-4 text-guild-danger" />
                  <span className="text-sm font-medium">Max Price</span>
                </div>
                <p className="text-2xl font-bold text-guild-danger">
                  ${maxPrice.toFixed(2)}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-2">
                  <Award className="w-4 h-4 text-guild-accent-1" />
                  <span className="text-sm font-medium">Awards</span>
                </div>
                <p className="text-2xl font-bold text-guild-accent-1">
                  {awardData.length}
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Price Trend Chart */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Price Trend Over Time</CardTitle>
            </CardHeader>
            <CardContent>
              {chartData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip 
                      formatter={(value, name) => [`$${value}`, 'Unit Price']}
                      labelFormatter={(label) => `Date: ${label}`}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="price" 
                      stroke="#3b82f6" 
                      strokeWidth={2} 
                      dot={{ r: 4 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  No historical pricing data available
                </div>
              )}
            </CardContent>
          </Card>

          {/* Price Distribution */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Price Distribution</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={priceRanges}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="range" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="#8b5cf6" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Recent Awards Table */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Recent Awards</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {awardData.slice(0, 10).map((award, index) => (
                  <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <Badge variant="secondary" className="font-mono">
                          {award.contract_number}
                        </Badge>
                        <span className="text-sm text-muted-foreground">
                          CAGE: {award.cage}
                        </span>
                      </div>
                      <div className="flex items-center gap-4 mt-1 text-sm text-muted-foreground">
                        <div className="flex items-center gap-1">
                          <Calendar className="w-3 h-3" />
                          {new Date(award.awd_date).toLocaleDateString()}
                        </div>
                        <span>Qty: {award.quantity?.toLocaleString()}</span>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-semibold">${award.unit_cost?.toFixed(2)}</div>
                      <div className="text-sm text-muted-foreground">
                        Total: ${award.total?.toLocaleString()}
                      </div>
                    </div>
                  </div>
                ))}
                
                {awardData.length === 0 && (
                  <div className="text-center py-4 text-muted-foreground">
                    No award history available for this NSN
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </SheetContent>
    </Sheet>
  );
};