import { useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { usePricingQueue } from '@/hooks/use-database';
import { useAuth } from '@/hooks/use-auth';
import { Users, Filter, Calendar, CheckCircle, Clock, AlertTriangle } from 'lucide-react';

export const Hub = () => {
  const { userRole } = useAuth();
  const [partnerFilter, setPartnerFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  
  const { data: pricingQueue = [], isLoading } = usePricingQueue(
    userRole === 'PARTNER' ? 'current-user' : undefined
  );

  const getStatusIcon = (status?: string) => {
    switch (status) {
      case 'completed': return <CheckCircle className="w-4 h-4 text-guild-success" />;
      case 'overdue': return <AlertTriangle className="w-4 h-4 text-guild-danger" />;
      default: return <Clock className="w-4 h-4 text-guild-warning" />;
    }
  };

  const getStatusBadge = (status?: string) => {
    switch (status) {
      case 'completed': 
        return <Badge className="bg-guild-success/10 text-guild-success">Completed</Badge>;
      case 'overdue': 
        return <Badge className="bg-guild-danger/10 text-guild-danger">Overdue</Badge>;
      default: 
        return <Badge className="bg-guild-warning/10 text-guild-warning">In Progress</Badge>;
    }
  };

  const filteredQueue = pricingQueue.filter(item => {
    if (partnerFilter && !item.client?.toLowerCase().includes(partnerFilter.toLowerCase())) {
      return false;
    }
    if (statusFilter && statusFilter !== 'all') {
      // Add status filtering logic based on your business rules
      return true;
    }
    return true;
  });

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-guild-brand-fg flex items-center gap-2">
            <Users className="w-6 h-6" />
            {userRole === 'CGDC' ? 'Partner Hub - Super View' : 'Partner Hub'}
          </h1>
          <p className="text-muted-foreground">
            {userRole === 'CGDC' 
              ? 'Monitor all partner activities and assignments' 
              : 'Your assigned pricing requests and deliverables'
            }
          </p>
        </div>
        <Badge variant="outline" className="bg-guild-accent-1/10 text-guild-accent-1">
          {filteredQueue.length} items
        </Badge>
      </div>

      {userRole === 'CGDC' && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Filter className="w-5 h-5" />
              Filters
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <Input
                  placeholder="Filter by partner..."
                  value={partnerFilter}
                  onChange={(e) => setPartnerFilter(e.target.value)}
                />
              </div>
              <div>
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger>
                    <SelectValue placeholder="Status filter" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Status</SelectItem>
                    <SelectItem value="pending">Pending</SelectItem>
                    <SelectItem value="overdue">Overdue</SelectItem>
                    <SelectItem value="completed">Completed</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Button variant="outline" className="w-full">
                  Export Report
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="space-y-4">
        {isLoading ? (
          <div className="text-center py-8">Loading assignments...</div>
        ) : filteredQueue.length === 0 ? (
          <Card>
            <CardContent className="text-center py-8">
              <Users className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
              <h3 className="text-lg font-semibold mb-2">No assignments found</h3>
              <p className="text-muted-foreground">
                {userRole === 'CGDC' 
                  ? 'No partner assignments match your current filters.'
                  : 'You have no pending assignments at this time.'
                }
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4">
            {filteredQueue.map((item) => (
              <Card key={item.id} className="hover:shadow-md transition-shadow">
                <CardContent className="p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        {getStatusIcon(item.client_type)}
                        <h3 className="font-semibold">{item.client || 'Partner Assignment'}</h3>
                        {getStatusBadge(item.client_type)}
                      </div>
                      
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-muted-foreground">
                        <div>
                          <div className="flex items-center gap-1 mb-1">
                            <Calendar className="w-3 h-3" />
                            Received
                          </div>
                          <div>{item.received_at ? new Date(item.received_at).toLocaleDateString() : 'N/A'}</div>
                        </div>
                        
                        <div>
                          <div className="flex items-center gap-1 mb-1">
                            <Clock className="w-3 h-3" />
                            Due Date
                          </div>
                          <div>{item.submitted_at ? new Date(item.submitted_at).toLocaleDateString() : 'TBD'}</div>
                        </div>
                        
                        <div>
                          <div className="flex items-center gap-1 mb-1">
                            <Users className="w-3 h-3" />
                            Assigned By
                          </div>
                          <div>{item.submitted_by || 'System'}</div>
                        </div>
                      </div>
                      
                      {item.cost_breakdown_json && (
                        <div className="mt-3 p-2 bg-muted rounded text-sm">
                          <strong>Notes:</strong> Cost breakdown analysis required
                        </div>
                      )}
                    </div>
                    
                    <div className="ml-4 flex flex-col gap-2">
                      <Button size="sm" variant="outline">
                        View Details
                      </Button>
                      {userRole === 'PARTNER' && (
                        <Button size="sm">
                          Take Action
                        </Button>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Hub;