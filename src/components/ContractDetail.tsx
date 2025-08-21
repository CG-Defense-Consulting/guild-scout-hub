import React, { useState, useEffect } from 'react';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';
import { useUpdateDestinations } from '@/hooks/use-database';
import { 
  FileText, 
  Upload, 
  Zap, 
  Send, 
  Clock, 
  User,
  Calendar,
  CheckCircle2,
  AlertCircle,
  PlayCircle
} from 'lucide-react';

interface ContractDetailProps {
  contract: any;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export const ContractDetail = ({ contract, open, onOpenChange }: ContractDetailProps) => {
  const { toast } = useToast();
  const updateDestinations = useUpdateDestinations();
  const [destinations, setDestinations] = useState<Array<{ location: string; quantity: string }>>([]);
  
  // Calculate total destination quantity
  const totalDestinationQuantity = destinations.reduce((total, dest) => {
    const qty = parseInt(dest.quantity) || 0;
    return total + qty;
  }, 0);
  
  // Load existing destinations when contract changes
  useEffect(() => {
    if (contract?.destination_json && Array.isArray(contract.destination_json)) {
      setDestinations(contract.destination_json);
    } else {
      setDestinations([]);
    }
  }, [contract]);
  
  const handleSaveDestinations = async () => {
    try {
      await updateDestinations.mutateAsync({ 
        id: contract.id, 
        destinations 
      });
      toast({
        title: 'Destinations Saved',
        description: 'Destination information has been updated successfully.',
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to save destinations. Please try again.',
        variant: 'destructive',
      });
    }
  };

  if (!contract) return null;

  const handleStubAction = (actionName: string) => {
    toast({
      title: 'Action Triggered',
      description: `${actionName} functionality will be implemented later.`,
    });
  };

  const timelineEvents = [
    { date: contract.created_at, event: 'Contract added to queue', type: 'info' },
    { date: new Date().toISOString(), event: 'Analysis phase started', type: 'success' },
    // Add more synthetic timeline events as needed
  ];

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full sm:max-w-4xl overflow-y-auto">
        <SheetHeader className="pb-4">
          <SheetTitle className="flex items-center gap-2">
            <FileText className="w-5 h-5" />
            Contract Details: {contract.solicitation_number || 'Unknown Solicitation'}
          </SheetTitle>
          <SheetDescription>
            Manage contract lifecycle, documentation, and partner coordination
          </SheetDescription>
        </SheetHeader>

        <Tabs defaultValue="overview" className="space-y-4">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="documents">Documents</TabsTrigger>
            <TabsTrigger value="automations">Automations</TabsTrigger>
            <TabsTrigger value="partner">Send to Partner</TabsTrigger>
            <TabsTrigger value="timeline">Timeline</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Contract Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="solicitation-number">Solicitation Number</Label>
                    <Input 
                      id="solicitation-number" 
                      defaultValue={contract.solicitation_number} 
                      className="font-mono"
                      disabled
                    />
                  </div>
                  <div>
                    <Label htmlFor="status">Current Status</Label>
                    <Badge variant="outline" className="w-full justify-center py-2">
                      {contract.current_stage || 'Analysis'}
                    </Badge>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="part-number">NSN</Label>
                    <Input 
                      id="part-number" 
                      defaultValue={contract.national_stock_number} 
                      className="font-mono"
                      disabled
                    />
                  </div>
                  <div>
                    <Label htmlFor="quantity">Quantity</Label>
                    <Input 
                      id="quantity" 
                      defaultValue={contract.quantity?.toLocaleString() || '0'} 
                      disabled
                    />
                  </div>
                </div>

                <div>
                  <Label htmlFor="description">Description</Label>
                  <Textarea 
                    id="description" 
                    defaultValue={contract.description} 
                    rows={3}
                    disabled
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="quote-issue-date">Issue Date</Label>
                    <Input id="quote-issue-date" defaultValue={contract.quote_issue_date} disabled />
                  </div>
                  <div>
                    <Label htmlFor="added-by">Added By</Label>
                    <Input id="added-by" defaultValue={contract.added_by} disabled />
                  </div>
                </div>

                <div className="pt-4">
                  <p className="text-sm text-muted-foreground">
                    Contract details are read-only. Use the status controls above to manage the contract lifecycle.
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="documents" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Upload className="w-5 h-5" />
                  Document Management
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="border-2 border-dashed border-muted-foreground/25 rounded-lg p-8 text-center">
                  <Upload className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
                  <h3 className="text-lg font-semibold mb-2">Upload Documents</h3>
                  <p className="text-muted-foreground mb-4">
                    Drag and drop files here or click to browse
                  </p>
                  <Button onClick={() => handleStubAction('File Upload')}>
                    Select Files
                  </Button>
                </div>

                <div className="mt-6">
                  <h4 className="font-medium mb-3">Existing Documents</h4>
                  <div className="text-sm text-muted-foreground">
                    No documents uploaded yet. Technical documentation and compliance files will appear here.
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="automations" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Zap className="w-5 h-5" />
                  Automation Actions
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid gap-3">
                  <Button 
                    variant="outline" 
                    className="justify-start"
                    onClick={() => handleStubAction('Market Intelligence Scraping')}
                  >
                    <PlayCircle className="w-4 h-4 mr-2" />
                    Run Market Intelligence Scraping
                  </Button>
                  
                  <Button 
                    variant="outline" 
                    className="justify-start"
                    onClick={() => handleStubAction('Compliance Check')}
                  >
                    <CheckCircle2 className="w-4 h-4 mr-2" />
                    Perform Compliance Check
                  </Button>
                  
                  <Button 
                    variant="outline" 
                    className="justify-start"
                    onClick={() => handleStubAction('Auto-Bid Generation')}
                  >
                    <Zap className="w-4 h-4 mr-2" />
                    Generate Auto-Bid Proposal
                  </Button>
                  
                  <Button 
                    variant="outline" 
                    className="justify-start"
                    onClick={() => handleStubAction('Risk Assessment')}
                  >
                    <AlertCircle className="w-4 h-4 mr-2" />
                    Run Risk Assessment
                  </Button>
                </div>

                <div className="mt-6 p-4 bg-muted rounded-lg">
                  <h4 className="font-medium mb-2">Automation Status</h4>
                  <p className="text-sm text-muted-foreground">
                    All automation features are currently in stub mode. 
                    Real implementations will be added in future iterations.
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="partner" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Send className="w-5 h-5" />
                  Send to Partner
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label htmlFor="partner-select">Select Partner</Label>
                  <Input id="partner-select" placeholder="Choose partner organization" />
                </div>

                <div>
                  <Label htmlFor="assignment-notes">Assignment Notes</Label>
                  <Textarea 
                    id="assignment-notes" 
                    placeholder="Special instructions or requirements for the partner..."
                    rows={3}
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="due-date">Due Date</Label>
                    <Input id="due-date" type="date" />
                  </div>
                  <div>
                    <Label htmlFor="priority">Priority Level</Label>
                    <Input id="priority" placeholder="High, Medium, Low" />
                  </div>
                </div>

                {/* Destinations Section */}
                <div className="border-t pt-4">
                  <div className="flex items-center justify-between mb-3">
                    <Label className="text-base font-medium">Destinations & Quantities</Label>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        const newDestinations = [...destinations, { location: '', quantity: '' }];
                        setDestinations(newDestinations);
                      }}
                    >
                      + Add Destination
                    </Button>
                  </div>
                  
                  <div className="space-y-3">
                    {destinations.map((dest, index) => (
                      <div key={index} className="grid grid-cols-3 gap-3 items-end">
                        <div>
                          <Label htmlFor={`location-${index}`}>Location</Label>
                          <Input
                            id={`location-${index}`}
                            placeholder="e.g., Fort Hood, TX"
                            value={dest.location}
                            onChange={(e) => {
                              const newDestinations = [...destinations];
                              newDestinations[index].location = e.target.value;
                              setDestinations(newDestinations);
                            }}
                          />
                        </div>
                        <div>
                          <Label htmlFor={`quantity-${index}`}>Quantity</Label>
                          <Input
                            id={`quantity-${index}`}
                            type="number"
                            placeholder="Qty"
                            value={dest.quantity}
                            onChange={(e) => {
                              const newDestinations = [...destinations];
                              newDestinations[index].quantity = e.target.value;
                              setDestinations(newDestinations);
                            }}
                          />
                        </div>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            const newDestinations = destinations.filter((_, i) => i !== index);
                            setDestinations(newDestinations);
                          }}
                          className="h-10"
                        >
                          Remove
                        </Button>
                      </div>
                    ))}
                  </div>
                  
                  {destinations.length > 0 && (
                    <div className="mt-4 p-3 bg-muted rounded-lg">
                      <Label className="text-sm font-medium mb-2 block">Total Quantity: {totalDestinationQuantity}</Label>
                      <p className="text-xs text-muted-foreground">
                        Contract quantity: {contract.quantity?.toLocaleString() || '0'}
                      </p>
                      {totalDestinationQuantity !== contract.quantity && (
                        <p className="text-xs text-orange-600 mt-1">
                          ⚠️ Destination quantities don't match contract quantity
                        </p>
                      )}
                      
                      <Button
                        onClick={handleSaveDestinations}
                        disabled={updateDestinations.isPending}
                        className="mt-3 w-full"
                        size="sm"
                      >
                        {updateDestinations.isPending ? 'Saving...' : 'Save Destinations'}
                      </Button>
                    </div>
                  )}
                </div>

                <Button 
                  onClick={() => handleStubAction('Partner Assignment')}
                  className="w-full"
                >
                  <Send className="w-4 h-4 mr-2" />
                  Send Assignment to Partner
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="timeline" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Clock className="w-5 h-5" />
                  Contract Timeline
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {timelineEvents.map((event, index) => (
                    <div key={index} className="flex items-start gap-3 pb-4 border-b last:border-b-0">
                      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-guild-accent-1/20 flex items-center justify-center">
                        {event.type === 'success' ? (
                          <CheckCircle2 className="w-4 h-4 text-guild-success" />
                        ) : (
                          <Clock className="w-4 h-4 text-guild-accent-1" />
                        )}
                      </div>
                      <div className="flex-1">
                        <p className="font-medium">{event.event}</p>
                        <div className="flex items-center gap-2 mt-1 text-sm text-muted-foreground">
                          <Calendar className="w-3 h-3" />
                          {new Date(event.date).toLocaleDateString()}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="mt-6 p-4 bg-muted rounded-lg">
                  <h4 className="font-medium mb-2">Timeline Notes</h4>
                  <p className="text-sm text-muted-foreground">
                    This timeline shows synthetic events for demonstration. 
                    Real timeline tracking will be implemented with actual contract workflows.
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </SheetContent>
    </Sheet>
  );
};