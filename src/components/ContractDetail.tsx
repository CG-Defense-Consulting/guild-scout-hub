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
import { useUpdateDestinations, useUpdateMilitaryStandards, StageTimelineEntry } from '@/hooks/use-database';
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
  const updateMilitaryStandards = useUpdateMilitaryStandards();
  const [destinations, setDestinations] = useState<Array<{ location: string; quantity: string }>>([]);
  const [militaryStandards, setMilitaryStandards] = useState<Array<{ code: string; description: string }>>([]);
  
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
  
  // Load existing military standards when contract changes
  useEffect(() => {
    if (contract?.mil_std && Array.isArray(contract.mil_std)) {
      setMilitaryStandards(contract.mil_std);
    } else {
      setMilitaryStandards([]);
    }
  }, [contract]);
  
  // Auto-save military standards when they change
  const autoSaveMilitaryStandards = async (newStandards: Array<{ code: string; description: string }>) => {
    try {
      // Set to null if no standards, otherwise use the array
      const valueToSave = newStandards.length === 0 ? null : newStandards;
      
      await updateMilitaryStandards.mutateAsync({ 
        id: contract.id, 
        militaryStandards: valueToSave 
      });
      // Don't show toast for auto-save to avoid spam
    } catch (error) {
      console.error('Auto-save failed:', error);
      // Show error toast for auto-save failures
      toast({
        title: 'Auto-save Failed',
        description: 'Failed to auto-save military standards. Please try saving manually.',
        variant: 'destructive',
      });
    }
  };
  
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

  // Parse the stage timeline from the contract data
  const stageTimeline: StageTimelineEntry[] = contract?.stage_timeline 
    ? (Array.isArray(contract.stage_timeline) ? contract.stage_timeline : [])
    : [];

  // Sort timeline by timestamp (most recent first)
  const sortedTimeline = [...stageTimeline].sort((a, b) => 
    new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );

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
                
                {/* Military Standards Section */}
                <div className="pt-4 border-t">
                  <div className="flex items-center justify-between mb-3">
                    <Label className="text-base font-semibold">Military Standards</Label>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={async () => {
                        const newStandard = { code: '', description: '' };
                        const newStandards = [...militaryStandards, newStandard];
                        setMilitaryStandards(newStandards);
                        // Auto-save the new list
                        await autoSaveMilitaryStandards(newStandards);
                      }}
                    >
                      Add Standard
                    </Button>
                  </div>
                  
                  {militaryStandards.length === 0 ? (
                    <div className="text-center py-6 border-2 border-dashed border-muted-foreground/25 rounded-lg">
                      <p className="text-sm text-muted-foreground mb-2">No military standards added yet</p>
                      <p className="text-xs text-muted-foreground">Click "Add Standard" to add the first one</p>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {militaryStandards.map((standard, index) => (
                        <div key={index} className="flex gap-2 items-start">
                          <div className="flex-1 space-y-2">
                            <Input
                              placeholder="e.g., MIL-STD-130"
                              value={standard.code}
                              onChange={async (e) => {
                                const newStandards = [...militaryStandards];
                                newStandards[index].code = e.target.value;
                                setMilitaryStandards(newStandards);
                                // Auto-save after a brief delay to avoid too many API calls
                                setTimeout(() => autoSaveMilitaryStandards(newStandards), 500);
                              }}
                              className="font-mono text-sm"
                            />
                            <Textarea
                              placeholder="Description of the standard (e.g., Marking standards for military items)"
                              value={standard.description}
                              onChange={async (e) => {
                                const newStandards = [...militaryStandards];
                                newStandards[index].description = e.target.value;
                                setMilitaryStandards(newStandards);
                                // Auto-save after a brief delay to avoid too many API calls
                                setTimeout(() => autoSaveMilitaryStandards(newStandards), 500);
                              }}
                              rows={2}
                              className="text-sm"
                            />
                          </div>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="text-red-500 hover:text-red-700 hover:bg-red-50"
                            onClick={async () => {
                              const newStandards = militaryStandards.filter((_, i) => i !== index);
                              setMilitaryStandards(newStandards);
                              // Auto-save the updated list
                              await autoSaveMilitaryStandards(newStandards);
                            }}
                          >
                            Remove
                          </Button>
                        </div>
                      ))}
                                         </div>
                   )}
                   
                   {militaryStandards.length > 0 && (
                     <div className="pt-3 border-t">
                       <Button
                         size="sm"
                         onClick={async () => {
                           try {
                             await updateMilitaryStandards.mutateAsync({ 
                               id: contract.id, 
                               militaryStandards 
                             });
                             toast({
                               title: 'Military Standards Saved',
                               description: 'Military standards have been updated successfully.',
                             });
                           } catch (error) {
                             toast({
                               title: 'Error',
                               description: 'Failed to save military standards. Please try again.',
                               variant: 'destructive',
                             });
                           }
                         }}
                         disabled={updateMilitaryStandards.isPending}
                       >
                         {updateMilitaryStandards.isPending ? 'Saving...' : 'Save Standards'}
                       </Button>
                     </div>
                   )}
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
                  {sortedTimeline.length > 0 ? (
                    sortedTimeline.map((entry, index) => (
                      <div key={index} className="flex items-start gap-3 pb-4 border-b last:border-b-0">
                        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-guild-accent-1/20 flex items-center justify-center">
                          <CheckCircle2 className="w-4 h-4 text-guild-success" />
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center justify-between mb-1">
                            <p className="font-medium">{entry.stage}</p>
                            <Badge variant="outline" className="text-xs">
                              {entry.stage}
                            </Badge>
                          </div>
                          {entry.notes && (
                            <p className="text-sm text-muted-foreground mb-2">
                              {entry.notes}
                            </p>
                          )}
                          <div className="flex items-center gap-4 text-sm text-muted-foreground">
                            <div className="flex items-center gap-1">
                              <Calendar className="w-3 h-3" />
                              {new Date(entry.timestamp).toLocaleDateString()} at {new Date(entry.timestamp).toLocaleTimeString()}
                            </div>
                            {entry.moved_by && (
                              <div className="flex items-center gap-1">
                                <User className="w-3 h-3" />
                                {entry.moved_by}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="text-center py-8">
                      <Clock className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
                      <h3 className="text-lg font-semibold mb-2">No Timeline Data</h3>
                      <p className="text-muted-foreground">
                        Stage transitions will appear here as the contract progresses.
                      </p>
                    </div>
                  )}
                </div>

                {sortedTimeline.length > 0 && (
                  <div className="mt-6 p-4 bg-muted rounded-lg">
                    <h4 className="font-medium mb-2">Timeline Summary</h4>
                    <p className="text-sm text-muted-foreground">
                      Showing {sortedTimeline.length} stage transition{sortedTimeline.length !== 1 ? 's' : ''}.
                      Most recent changes appear at the top.
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </SheetContent>
    </Sheet>
  );
};