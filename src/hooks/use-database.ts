import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { supabase } from '@/integrations/supabase/client';

// Stage timeline entry interface
export interface StageTimelineEntry {
  stage: string;
  timestamp: string;
  moved_by?: string;
  notes?: string;
}

// RFQ Index Extract hooks
export const useRfqData = (filters?: Record<string, any>) => {
  return useQuery({
    queryKey: ['rfq_index_extract', filters],
    queryFn: async () => {
      let query = supabase.from('rfq_index_extract').select('*');
      
      if (filters) {
        Object.entries(filters).forEach(([key, value]) => {
          if (value !== undefined && value !== '') {
            if (key === 'quantity_min') {
              query = query.gte('quantity', value);
            } else if (key === 'quantity_max') {
              query = query.lte('quantity', value);
            } else if (key === 'quote_issue_date_from') {
              query = query.gte('quote_issue_date', value);
            } else if (key === 'quote_issue_date_to') {
              query = query.lte('quote_issue_date', value);
            } else if (key === 'nsnPrefixes' && Array.isArray(value) && value.length > 0) {
              // Handle NSN prefix filtering with OR conditions
              const orConditions = value.map(prefix => 
                `national_stock_number.ilike.${prefix}%`
              );
              query = query.or(orConditions.join(','));
            } else if (key !== 'nsnPrefixes') {
              // Skip nsnPrefixes as it's handled above, apply other filters normally
              query = query.ilike(key, `%${value}%`);
            }
          }
        });
      }
      
      // Set default filter to last 2 months only if NO filters are applied at all
      if (!filters || Object.keys(filters).length === 0) {
        const twoMonthsAgo = new Date();
        twoMonthsAgo.setMonth(twoMonthsAgo.getMonth() - 2);
        const twoMonthsAgoStr = twoMonthsAgo.toISOString().split('T')[0];
        query = query.gte('quote_issue_date', twoMonthsAgoStr);
      }
      
      // Apply server-side deduplication and dual-key sorting
      // This ensures we get exactly one row per unique combination, prioritizing newer records
      
      // Apply dual-key sorting: quote_issue_date DESC, then quantity DESC
      // This ensures newer records with higher quantities appear first
      query = query.order('quote_issue_date', { ascending: false }).order('quantity', { ascending: false });
      
      // Apply limit to ensure we get exactly 1000 rows (or maximum available)
      // This is crucial for consistent performance and user experience
      const targetRowCount = 1000;
      query = query.limit(targetRowCount * 2); // Get more rows initially to account for deduplication
      
      console.log('=== useRfqData Debug ===');
      console.log('Server-side deduplication enabled');
      console.log('Dual-key sorting: quote_issue_date DESC, quantity DESC');
      console.log('Target row count:', targetRowCount);
      console.log('Applied filters:', filters);
      console.log('=== End Debug ===');
      
      console.log('=== useRfqData Query Execution ===');
      console.log('Executing query with deduplication...');
      
      const { data: rawData, error } = await query;
      
      if (error) {
        console.error('Supabase query error:', error);
        throw error;
      }
      
      console.log(`Query successful, returned ${rawData?.length || 0} rows`);
      
      // Apply client-side deduplication to ensure exactly one row per unique combination
      // This preserves the server-side sort order while removing duplicates
      if (rawData && rawData.length > 0) {
        const seen = new Map();
        const deduplicatedData = rawData.filter(row => {
          // Create composite key for deduplication
          const key = `${row.solicitation_number}-${row.quote_issue_date}-${row.quantity}-${row.item}-${row.desc}-${row.unit_type}`;
          
          if (seen.has(key)) {
            // Skip duplicate - we already have the first occurrence (which maintains server-side sort order)
            return false;
          }
          
          // Store this combination and keep the row
          seen.set(key, true);
          return true;
        });
        
        // Limit to exactly targetRowCount rows (or maximum available)
        const finalData = deduplicatedData.slice(0, targetRowCount);
        
        console.log(`Deduplication complete: ${rawData.length} -> ${deduplicatedData.length} -> ${finalData.length} rows`);
        console.log('Sample data (first 2 rows):', finalData?.slice(0, 2));
        console.log('=== End Query Execution ===');
        
        return finalData;
      }
      
      console.log('No data returned from query');
      console.log('=== End Query Execution ===');
      return [];
    },
  });
};

// Enhanced version for very large datasets with server-side search
export const useRfqDataWithSearch = (filters?: Record<string, any>, searchTerm?: string) => {
  return useQuery({
    queryKey: ['rfq_index_extract_search', filters, searchTerm],
    queryFn: async () => {
      let query = supabase.from('rfq_index_extract').select('*');
      
      // Check if we need to filter by award history
      const hasAwardHistoryFilter = filters?.has_award_history === true;
      
      // Apply filters first
      if (filters) {
        Object.entries(filters).forEach(([key, value]) => {
          if (value !== undefined && value !== '') {
            if (key === 'quantity_min') {
              query = query.gte('quantity', value);
            } else if (key === 'quantity_max') {
              query = query.lte('quantity', value);
            } else if (key === 'quote_issue_date_from') {
              query = query.gte('quote_issue_date', value);
            } else if (key === 'quote_issue_date_to') {
              query = query.lte('quote_issue_date', value);
            } else if (key === 'nsnPrefixes' && Array.isArray(value) && value.length > 0) {
              const orConditions = value.map(prefix => 
                `national_stock_number.ilike.${prefix}%`
              );
              query = query.or(orConditions.join(','));
            } else if (key !== 'nsnPrefixes' && key !== 'has_award_history') {
              query = query.ilike(key, `%${value}%`);
            }
          }
        });
      }
      
      // Apply server-side search if provided
      if (searchTerm && searchTerm.trim()) {
        // Search across multiple columns on the server side
        query = query.or(
          `national_stock_number.ilike.%${searchTerm}%,` +
          `desc.ilike.%${searchTerm}%,` +
          `item.ilike.%${searchTerm}%,` +
          `solicitation_number.ilike.%${searchTerm}%`
        );
      }
      
      // Filter by award history if requested
      if (hasAwardHistoryFilter) {
        // Get NSNs that have award history
        const { data: awardNsns } = await supabase
          .from('award_history')
          .select('national_stock_number')
          .not('national_stock_number', 'is', null);
        
        if (awardNsns && awardNsns.length > 0) {
          const nsns = awardNsns.map(record => record.national_stock_number);
          query = query.in('national_stock_number', nsns);
        } else {
          // No award history found, return empty result
          return [];
        }
      }
      
      // Set default filter to last 2 months only if NO filters AND NO search are applied
      if ((!filters || Object.keys(filters).length === 0) && !searchTerm) {
        const twoMonthsAgo = new Date();
        twoMonthsAgo.setMonth(twoMonthsAgo.getMonth() - 2);
        const twoMonthsAgoStr = twoMonthsAgo.toISOString().split('T')[0];
        query = query.gte('quote_issue_date', twoMonthsAgoStr);
      }
      
      // Apply server-side deduplication and dual-key sorting
      // This ensures we get exactly one row per unique combination, prioritizing newer records
      // We'll use a window function approach to get the first row per group
      
      // First, get the data with all filters applied
      let baseQuery = query;
      
      // Apply dual-key sorting: quote_issue_date DESC, then quantity DESC
      // This ensures newer records with higher quantities appear first
      baseQuery = baseQuery.order('quote_issue_date', { ascending: false }).order('quantity', { ascending: false });
      
      // For server-side deduplication, we need to use a different approach
      // Since Supabase doesn't support DISTINCT ON directly, we'll use a subquery approach
      // that ensures we get the first row per unique combination based on our sort order
      
      // Apply limit to ensure we get exactly 1000 rows (or maximum available)
      // This is crucial for consistent performance and user experience
      const targetRowCount = 1000;
      baseQuery = baseQuery.limit(targetRowCount * 2); // Get more rows initially to account for deduplication
      
      console.log('=== useRfqDataWithSearch Debug ===');
      console.log('Server-side deduplication enabled');
      console.log('Dual-key sorting: quote_issue_date DESC, quantity DESC');
      console.log('Target row count:', targetRowCount);
      console.log('Applied filters:', filters);
      console.log('Search term:', searchTerm);
      console.log('=== End Debug ===');
      
      console.log('=== useRfqDataWithSearch Query Execution ===');
      console.log('Executing base query with deduplication...');
      
      const { data: rawData, error } = await baseQuery;
      
      if (error) {
        console.error('Supabase query error:', error);
        throw error;
      }
      
      console.log(`Base query successful, returned ${rawData?.length || 0} rows`);
      
      // Apply client-side deduplication to ensure exactly one row per unique combination
      // This preserves the server-side sort order while removing duplicates
      if (rawData && rawData.length > 0) {
        const seen = new Map();
        const deduplicatedData = rawData.filter(row => {
          // Create composite key for deduplication
          const key = `${row.solicitation_number}-${row.quote_issue_date}-${row.quantity}-${row.item}-${row.desc}-${row.unit_type}`;
          
          if (seen.has(key)) {
            // Skip duplicate - we already have the first occurrence (which maintains server-side sort order)
            return false;
          }
          
          // Store this combination and keep the row
          seen.set(key, true);
          return true;
        });
        
        // Limit to exactly targetRowCount rows (or maximum available)
        const finalData = deduplicatedData.slice(0, targetRowCount);
        
        console.log(`Deduplication complete: ${rawData.length} -> ${deduplicatedData.length} -> ${finalData.length} rows`);
        console.log('Sample data (first 2 rows):', finalData?.slice(0, 2));
        console.log('=== End Query Execution ===');
        
        return finalData;
      }
      
      console.log('No data returned from base query');
      console.log('=== End Query Execution ===');
      return [];
    },
    enabled: !!(filters || searchTerm), // Only run when we have filters or search
  });
};

// Award History hooks
export const useAwardHistory = (nsn?: string) => {
  return useQuery({
    queryKey: ['award_history', nsn],
    queryFn: async () => {
      let query = supabase.from('award_history').select('*');
      
      if (nsn) {
        query = query.eq('national_stock_number', nsn);
      }
      
      const { data, error } = await query.order('awd_date', { ascending: false });
      if (error) throw error;
      return data;
    },
    enabled: !!nsn,
  });
};

// Universal Contract Queue hooks
export const useContractQueue = () => {
  return useQuery({
    queryKey: ['universal_contract_queue'],
    queryFn: async () => {
      // Join universal_contract_queue with rfq_index_extract to get contract details
      const { data, error } = await supabase
        .from('universal_contract_queue')
        .select(`
          *,
          rfq_index_extract (
            solicitation_number,
            national_stock_number,
            desc,
            item,
            quantity,
            quote_issue_date
          )
        `)
        .order('created_at', { ascending: false });
      
      if (error) throw error;
      
      // Transform the data to flatten the nested structure for easier use
      let transformedData = data?.map(contract => ({
        ...contract,
        // Ensure current_stage has a default value
        current_stage: contract.current_stage || 'Analysis',
        // Flatten the nested RFQ data
        solicitation_number: contract.rfq_index_extract?.solicitation_number,
        national_stock_number: contract.rfq_index_extract?.national_stock_number,
        description: (() => {
          const item = contract.rfq_index_extract?.item || '';
          const desc = contract.rfq_index_extract?.desc || '';
          return item && desc ? `${item} | ${desc}` : item || desc;
        })(),
        quantity: contract.rfq_index_extract?.quantity,
        quote_issue_date: contract.rfq_index_extract?.quote_issue_date,
        // Keep the original fields for backward compatibility
        part_number: contract.rfq_index_extract?.national_stock_number,
        long_description: (() => {
          const item = contract.rfq_index_extract?.item || '';
          const desc = contract.rfq_index_extract?.desc || '';
          return item && desc ? `${item} | ${desc}` : item || desc;
        })()
      })) || [];
      
      // Sort by quote_issue_date descending to prioritize newer RFQ data
      if (transformedData.length > 0) {
        transformedData.sort((a, b) => {
          const dateA = a.quote_issue_date ? new Date(a.quote_issue_date) : new Date(0);
          const dateB = b.quote_issue_date ? new Date(b.quote_issue_date) : new Date(0);
          return dateB.getTime() - dateA.getTime(); // Descending order (newest first)
        });
      }
      
      return transformedData;
    },
  });
};

export const useAddToQueue = (userId?: string) => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (rfqData: any) => {
      // Initialize the stage timeline with the first entry
      const initialTimeline: StageTimelineEntry[] = [{
        stage: 'Analysis',
        timestamp: new Date().toISOString(),
        moved_by: userId || null,
        notes: 'Contract added to queue'
      }];

      // Create a minimal record - only store user ID and timestamp
      const queueRecord = {
        // Set the id to reference the rfq_index_extract record
        id: rfqData.id,
        // Leave these fields blank as requested
        part_number: null,
        long_description: null,
        destination_json: null,
        added_by: userId,
        created_at: new Date().toISOString(),
        current_stage: 'Analysis',
        stage_timeline: initialTimeline
      };

      // Insert new record - the id field will automatically reference rfq_index_extract.id
      const { data, error } = await supabase
        .from('universal_contract_queue')
        .insert([queueRecord]);
      
      if (error) throw error;
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['universal_contract_queue'] });
    },
  });
};

// Partner Pricing Queue hooks (formerly client_pricing_queue)
export const usePricingQueue = (clientFilter?: string) => {
  return useQuery({
    queryKey: ['client_pricing_queue', clientFilter],
    queryFn: async () => {
      let query = supabase.from('client_pricing_queue').select('*');
      
      if (clientFilter) {
        query = query.eq('client', clientFilter);
      }
      
      const { data, error } = await query.order('received_at', { ascending: false });
      if (error) throw error;
      return data;
    },
  });
};

export const useUpdateQueueStatus = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ id, status, userId }: { id: string; status: string; userId?: string }) => {
      // First, get the current record to retrieve existing timeline
      const { data: currentRecord, error: fetchError } = await supabase
        .from('universal_contract_queue')
        .select('stage_timeline, current_stage')
        .eq('id', id)
        .single();
      
      if (fetchError) throw fetchError;
      
      // Parse existing timeline or create new array
      const existingTimeline: StageTimelineEntry[] = currentRecord?.stage_timeline ? 
        (Array.isArray(currentRecord.stage_timeline) ? currentRecord.stage_timeline as StageTimelineEntry[] : []) : 
        [];
      
      // Create new timeline entry
      const newTimelineEntry: StageTimelineEntry = {
        stage: status,
        timestamp: new Date().toISOString(),
        moved_by: userId || null,
        notes: `Moved from ${currentRecord?.current_stage || 'Unknown'} to ${status}`
      };
      
      // Add new entry to timeline
      const updatedTimeline = [...existingTimeline, newTimelineEntry];
      
      // Update the record with new stage and timeline
      const { data, error } = await supabase
        .from('universal_contract_queue')
        .update({ 
          current_stage: status,
          stage_timeline: updatedTimeline
        })
        .eq('id', id);
        
      if (error) throw error;
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['universal_contract_queue'] });
    },
  });
};

export const useUpdateDestinations = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ id, destinations }: { id: string; destinations: Array<{ location: string; quantity: string }> }) => {
      const { data, error } = await supabase
        .from('universal_contract_queue')
        .update({ 
          destination_json: destinations
        })
        .eq('id', id);
      if (error) throw error;
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['universal_contract_queue'] });
    },
  });
};