import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { Calendar, User, Package, FileText, ExternalLink, Download, Eye } from 'lucide-react';
import { format } from 'date-fns';
import { supabase } from '@/integrations/supabase/client';
import { useToast } from '@/hooks/use-toast';

interface PartnerAssignmentDetailProps {
  assignment: {
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
  };
  onClose: () => void;
}

export const PartnerAssignmentDetail: React.FC<PartnerAssignmentDetailProps> = ({ assignment, onClose }) => {
  const { toast } = useToast();
  const [documents, setDocuments] = useState<Array<{
    name: string;
    size: number;
    url: string;
    type: string;
  }>>([]);
  const [isLoadingDocuments, setIsLoadingDocuments] = useState(false);

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

  // Load documents for this contract
  useEffect(() => {
    const loadDocuments = async () => {
      if (!assignment.id) return;
      
      setIsLoadingDocuments(true);
      try {
        const { data: files, error } = await supabase.storage
          .from('docs')
          .list('', {
            search: `contract-${assignment.id}-`
          });

        if (error) {
          console.error('Error loading documents:', error);
          return;
        }

        if (files && files.length > 0) {
          const documentPromises = files.map(async (file) => {
            try {
              const { data: urlData } = await supabase.storage
                .from('docs')
                .createSignedUrl(file.name, 3600); // 1 hour expiry

              return {
                name: file.name,
                size: file.metadata?.size || 0,
                url: urlData?.signedUrl || '',
                type: file.metadata?.mimetype || 'application/octet-stream'
              };
            } catch (error) {
              console.error('Error getting signed URL for file:', file.name, error);
              return null;
            }
          });

          const documentResults = await Promise.all(documentPromises);
          const validDocuments = documentResults.filter(doc => doc !== null);
          setDocuments(validDocuments);
        }
      } catch (error) {
        console.error('Error loading documents:', error);
      } finally {
        setIsLoadingDocuments(false);
      }
    };

    loadDocuments();
  }, [assignment.id]);

  const handleViewDocument = (url: string, name: string) => {
    window.open(url, '_blank');
  };

  const handleDownloadDocument = async (url: string, name: string) => {
    try {
      const response = await fetch(url);
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = name;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
    } catch (error) {
      console.error('Error downloading document:', error);
      toast({
        title: 'Download Failed',
        description: 'Failed to download the document. Please try again.',
        variant: 'destructive',
      });
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <Card className="w-full max-w-6xl max-h-[90vh] overflow-y-auto">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
          <CardTitle className="text-xl font-semibold">Partner Assignment Details</CardTitle>
          <Button variant="ghost" size="sm" onClick={onClose}>
            ✕
          </Button>
        </CardHeader>
        
        <CardContent className="space-y-6">
          {/* Assignment Overview */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground">Contract ID</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-lg font-mono">{assignment.id}</p>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground">Partner</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-lg font-semibold">{assignment.partner}</p>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground">Partner Type</CardTitle>
              </CardHeader>
              <CardContent>
                <Badge className={getPartnerTypeColor(assignment.partner_type)}>
                  {assignment.partner_type}
                </Badge>
              </CardContent>
            </Card>
          </div>

          {/* Contract Information */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Package className="w-5 h-5" />
                Contract Information
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {assignment.universal_contract_queue.part_number && (
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Part Number</label>
                  <p className="text-base">{assignment.universal_contract_queue.part_number}</p>
                </div>
              )}
              
              {assignment.universal_contract_queue.long_description && (
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Description</label>
                  <p className="text-base">{assignment.universal_contract_queue.long_description}</p>
                </div>
              )}
              
              <div>
                <label className="text-sm font-medium text-muted-foreground">Current Stage</label>
                <div className="flex items-center gap-2 mt-1">
                  {getStageBadge(assignment.universal_contract_queue.current_stage)}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Timeline Information */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="w-5 h-5" />
                Timeline
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium text-muted-foreground">Contract Created</label>
                <p className="text-base">
                  {format(new Date(assignment.universal_contract_queue.created_at), 'PPP')}
                </p>
              </div>
              
              <div>
                <label className="text-sm font-medium text-muted-foreground">Submitted to Partner</label>
                <p className="text-base">
                  {format(new Date(assignment.submitted_at), 'PPP')}
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Partner Information */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="w-5 h-5" />
                Partner Information
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium text-muted-foreground">Partner Name</label>
                <p className="text-base">{assignment.partner}</p>
              </div>
              
              <div>
                <label className="text-sm font-medium text-muted-foreground">Submitted By</label>
                <p className="text-base">{assignment.submitted_by}</p>
              </div>
            </CardContent>
          </Card>

          {/* Documents Section */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="w-5 h-5" />
                Related Documents
              </CardTitle>
            </CardHeader>
            <CardContent>
              {isLoadingDocuments ? (
                <div className="text-center py-8">Loading documents...</div>
              ) : documents.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <FileText className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>No documents found for this contract</p>
                  <p className="text-sm">Documents will appear here once they are uploaded</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {documents.map((doc, index) => (
                    <div key={index} className="flex items-center justify-between p-3 border rounded-lg bg-muted/50">
                      <div className="flex items-center gap-3">
                        <FileText className="w-5 h-5 text-blue-600" />
                        <div>
                          <p className="font-medium text-sm">{doc.name}</p>
                          <p className="text-xs text-muted-foreground">
                            {formatFileSize(doc.size)} • {doc.type}
                          </p>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleViewDocument(doc.url, doc.name)}
                        >
                          <Eye className="w-4 h-4 mr-2" />
                          View
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleDownloadDocument(doc.url, doc.name)}
                        >
                          <Download className="w-4 h-4 mr-2" />
                          Download
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-3 pt-4">
            <Button 
              variant="outline" 
              onClick={() => {
                // Navigate to the contract tracker for this contract
                window.open(`/tracker?contract=${assignment.id}`, '_blank');
              }}
            >
              <ExternalLink className="w-4 h-4 mr-2" />
              View in Contract Tracker
            </Button>
            
            <Button 
              variant="outline"
              onClick={() => {
                // Copy contract ID to clipboard
                navigator.clipboard.writeText(assignment.id);
                toast({
                  title: 'Copied',
                  description: 'Contract ID copied to clipboard',
                });
              }}
            >
              Copy Contract ID
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
