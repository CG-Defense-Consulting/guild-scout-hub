import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { supabase } from '@/integrations/supabase/client';

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
      
      // Always sort by quote_issue_date descending (most recent first), then by quantity descending
      query = query.order('quote_issue_date', { ascending: false }).order('quantity', { ascending: false });
      
      // Only apply limit if no filters are inputted (to allow full search across all data)
      if (!filters || Object.keys(filters).length === 0) {
        // Apply reasonable limit for default view (last 2 months)
        query = query.limit(10000);
      } else {
        // No limit when filters are applied - allow full dataset search
        console.log('=== useRfqData Debug ===');
        console.log('Filters applied, removing query limit to allow full dataset search');
        console.log('Applied filters:', filters);
        console.log('=== End Debug ===');
      }
      
      console.log('=== useRfqData Query Execution ===');
      console.log('Final query constructed, executing...');
      
      const { data, error } = await query;
      
      if (error) {
        console.error('Supabase query error:', error);
        throw error;
      }
      
      console.log(`Query successful, returned ${data?.length || 0} rows`);
      console.log('Sample data (first 2 rows):', data?.slice(0, 2));
      console.log('=== End Query Execution ===');
      
      return data;
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
      
      // Always sort by quote_issue_date descending (most recent first), then by quantity descending
      query = query.order('quote_issue_date', { ascending: false }).order('quantity', { ascending: false });
      
      // Only apply limit if no filters or search terms are inputted
      if ((!filters || Object.keys(filters).length === 0) && !searchTerm) {
        // Apply reasonable limit for default view (last 2 months)
        query = query.limit(10000);
      } else {
        // No limit when filters or search are applied - allow full dataset search
        console.log('=== useRfqDataWithSearch Debug ===');
        console.log('Filters or search applied, removing query limit to allow full dataset search');
        console.log('Applied filters:', filters);
        console.log('Search term:', searchTerm);
        console.log('=== End Debug ===');
      }
      
      console.log('=== useRfqDataWithSearch Query Execution ===');
      console.log('Final query constructed, executing...');
      
      const { data, error } = await query;
      
      if (error) {
        console.error('Supabase query error:', error);
        throw error;
      }
      
      console.log(`Query successful, returned ${data?.length || 0} rows`);
      console.log('Sample data (first 2 rows):', data?.slice(0, 2));
      console.log('=== End Query Execution ===');
      
      return data;
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
      return data?.map(contract => ({
        ...contract,
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
    },
  });
};

export const useAddToQueue = (userId?: string) => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (rfqData: any) => {
      // Create a minimal record - only store user ID and timestamp
      const queueRecord = {
        // Set the id to reference the rfq_index_extract record
        id: rfqData.id,
        // Leave these fields blank as requested
        part_number: null,
        long_description: null,
        rfq_link: null,
        destination_json: null,
        added_by: userId,
        created_at: new Date().toISOString()
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
    mutationFn: async ({ id, status }: { id: string; status: string }) => {
      const { data, error } = await supabase
        .from('universal_contract_queue')
        .update({ 
          // Add status field to queue items when updating lifecycle
          tech_doc_link: status // Using tech_doc_link as temp status field
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