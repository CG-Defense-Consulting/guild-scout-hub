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
            quote_issue_date,
            cde_g,
            closed
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
        // Include the new fields
        cde_g: contract.rfq_index_extract?.cde_g,
        closed: contract.rfq_index_extract?.closed,
        // Keep the original fields for backward compatibility
        part_number: contract.rfq_index_extract?.national_stock_number,
        long_description: (() => {
          const item = contract.rfq_index_extract?.item || '';
          const desc = contract.rfq_index_extract?.desc || '';
          return item && desc ? `${item} | ${desc}` : item || desc;
        })()
      })) || [];
      
      // Sort by quote_issue_date descending to prioritize newer RFQ data
      transformedData.sort((a, b) => {
        const dateA = a.quote_issue_date ? new Date(a.quote_issue_date).getTime() : 0;
        const dateB = b.quote_issue_date ? new Date(b.quote_issue_date).getTime() : 0;
        return dateB - dateA;
      });
      
      return transformedData;
    },
  });
};

export const useAddToQueue = (userId?: string) => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (rfqData: any) => {
      // Check if contract is already in queue
      const { data: existingContract, error: checkError } = await supabase
        .from('universal_contract_queue')
        .select('id')
        .eq('id', rfqData.id)
        .single();
      
      if (checkError && checkError.code !== 'PGRST116') { // PGRST116 = no rows returned
        throw checkError;
      }
      
      if (existingContract) {
        throw new Error(`Contract ${rfqData.solicitation_number} is already in the queue`);
      }

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
        stage_timeline: initialTimeline as any
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
        (Array.isArray(currentRecord.stage_timeline) ? currentRecord.stage_timeline as any : []) : 
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
          stage_timeline: updatedTimeline as any
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

export const useUpdateMilitaryStandards = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ id, militaryStandards }: { id: string; militaryStandards: Array<{ code: string; description: string }> | null }) => {
      const { data, error } = await supabase
        .from('universal_contract_queue')
        .update({ 
          mil_std: militaryStandards
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

// Hook for fetching trends data without row limits - optimized for speed
export const useTrendsData = (startDate: string, endDate: string) => {
  return useQuery({
    queryKey: ['trends_data', startDate, endDate],
    queryFn: async () => {
      try {
        console.log(`Starting optimized data fetch for period ${startDate} to ${endDate}`);
        const startTime = Date.now();
        
        // Supabase has a hard limit of 1000 rows per query, so we use that
        const BATCH_SIZE = 1000;
        
        // First, get the total count of records to show progress
        console.log('Getting total record counts...');
        const [rfqCountResult, awardCountResult] = await Promise.all([
          supabase
            .from('rfq_index_extract')
            .select('*', { count: 'exact', head: true })
            .gte('quote_issue_date', startDate)
            .lte('quote_issue_date', endDate),
          supabase
            .from('award_history')
            .select('*', { count: 'exact', head: true })
            .gte('awd_date', startDate)
            .lte('awd_date', endDate)
        ]);
        
        const totalRfqs = rfqCountResult.count || 0;
        const totalAwards = awardCountResult.count || 0;
        
        console.log(`Total records to fetch: ${totalRfqs} RFQs, ${totalAwards} Awards`);
        
        // Fetch both datasets in parallel
        const [rfqResult, awardResult] = await Promise.all([
          // RFQ Data fetching
          (async () => {
            let allRfqData: any[] = [];
            let hasMoreRfq = true;
            let rfqOffset = 0;
            
            console.log(`Fetching ${totalRfqs} RFQ records in batches of ${BATCH_SIZE}...`);
            
            while (hasMoreRfq) {
              const { data: rfqBatch, error: rfqError } = await supabase
                .from('rfq_index_extract')
                .select('id, national_stock_number, item, quantity, quote_issue_date, solicitation_number, desc') // Only select needed fields
                .gte('quote_issue_date', startDate)
                .lte('quote_issue_date', endDate)
                .order('quote_issue_date', { ascending: false })
                .range(rfqOffset, rfqOffset + BATCH_SIZE - 1);
              
              if (rfqError) throw rfqError;
              
              if (rfqBatch && rfqBatch.length > 0) {
                allRfqData = [...allRfqData, ...rfqBatch];
                rfqOffset += BATCH_SIZE;
                
                const progress = ((allRfqData.length / totalRfqs) * 100).toFixed(1);
                console.log(`RFQ batch loaded: ${rfqBatch.length} records (total: ${allRfqData.length}/${totalRfqs} - ${progress}%)`);
                
                // If we got less than the batch size, we've reached the end
                if (rfqBatch.length < BATCH_SIZE) {
                  hasMoreRfq = false;
                }
                
                // Safety check: if we've loaded more than the total count, something's wrong
                if (allRfqData.length >= totalRfqs) {
                  hasMoreRfq = false;
                }
              } else {
                hasMoreRfq = false;
              }
            }
            
            console.log(`RFQ data loading complete: ${allRfqData.length}/${totalRfqs} records loaded`);
            
            return allRfqData;
          })(),
          
          // Award History Data fetching
          (async () => {
            let allAwardData: any[] = [];
            let hasMoreAwards = true;
            let awardOffset = 0;
            
            console.log('Fetching award data in parallel...');
            
            // First, let's check what award history data exists without date restrictions
            const { data: sampleAwards, error: sampleError } = await supabase
              .from('award_history')
              .select('*')
              .limit(5);
            
            if (sampleError) {
              console.error('Error fetching sample awards:', sampleError);
            } else {
              console.log('Sample award records:', sampleAwards);
              if (sampleAwards && sampleAwards.length > 0) {
                console.log('Sample award dates:', sampleAwards.map(a => a.awd_date));
                console.log('Sample award NSNs:', sampleAwards.map(a => a.national_stock_number));
                console.log('Sample award CAGE codes:', sampleAwards.map(a => a.cage));
              }
            }
            
            while (hasMoreAwards) {
              const { data: awardBatch, error: awardError } = await supabase
                .from('award_history')
                .select('national_stock_number, cage, total, quantity, awd_date') // Only select needed fields
                .gte('awd_date', startDate)
                .lte('awd_date', endDate)
                .order('awd_date', { ascending: false })
                .range(awardOffset, awardOffset + BATCH_SIZE - 1);
              
              if (awardError) throw awardError;
              
              if (awardBatch && awardBatch.length > 0) {
                allAwardData = [...allAwardData, ...awardBatch];
                awardOffset += BATCH_SIZE;
                
                const progress = ((allAwardData.length / totalAwards) * 100).toFixed(1);
                console.log(`Award batch loaded: ${awardBatch.length} records (total: ${allAwardData.length}/${totalAwards} - ${progress}%)`);
                
                // If we got less than the batch size, we've reached the end
                if (awardBatch.length < BATCH_SIZE) {
                  hasMoreAwards = false;
                }
                
                // Safety check: if we've loaded more than the total count, something's wrong
                if (allAwardData.length >= totalAwards) {
                  hasMoreAwards = false;
                }
              } else {
                hasMoreAwards = false;
              }
            }
            
            console.log(`Award data loading complete: ${allAwardData.length}/${totalAwards} records loaded`);
            
            return allAwardData;
          })()
        ]);
        
        const endTime = Date.now();
        const loadTime = (endTime - startTime) / 1000;
        
        console.log(`✅ Optimized data fetch completed in ${loadTime.toFixed(2)}s`);
        console.log(`📊 Fetched ${rfqResult.length} RFQ records and ${awardResult.length} award records`);
        
        return {
          rfqData: rfqResult,
          awardData: awardResult,
        };
      } catch (error) {
        console.error('Error fetching trends data:', error);
        return { rfqData: [], awardData: [] };
      }
    },
    enabled: !!startDate && !!endDate,
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes to avoid refetching
    gcTime: 10 * 60 * 1000, // Keep in cache for 10 minutes
  });
};

// Hook for fetching aggregated trends data from the materialized view
export const useTrendsAggregated = (period: string) => {
  return useQuery({
    queryKey: ['trends_aggregated_materialized', period],
    queryFn: async () => {
      try {
        console.log(`Fetching aggregated trends data for period: ${period}`);
        
        const { data, error } = await supabase
          .from('trends_aggregated_materialized')
          .select('*')
          .eq('period', period)
          .single();
        
        if (error) throw error;
        
        console.log('✅ Aggregated trends data loaded from materialized view:', data);
        return data;
      } catch (error) {
        console.error('Error fetching aggregated trends data:', error);
        throw error;
      }
    },
    enabled: !!period,
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
    gcTime: 10 * 60 * 1000, // Keep in cache for 10 minutes
  });
};

// Function to refresh the materialized view (admin use)
export const refreshTrendsView = async () => {
  try {
    console.log('🔄 Refreshing trends materialized view...');
    
    const { data, error } = await supabase.rpc('refresh_trends_view');
    
    if (error) throw error;
    
    console.log('✅ Trends materialized view refreshed successfully');
    return data;
  } catch (error) {
    console.error('❌ Error refreshing trends view:', error);
    throw error;
  }
};

export const useDeleteFromQueue = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (id: string) => {
      const { data, error } = await supabase
        .from('universal_contract_queue')
        .delete()
        .eq('id', id);
      if (error) throw error;
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['universal_contract_queue'] });
    },
  });
};

// Utility function to extract original filename from storage path
export const extractOriginalFileName = (storagePath: string, contractId: string): string => {
  try {
    // Expected format: contract-{contractId}-{timestamp}-{encodedOriginalName}.{extension}
    const prefix = `contract-${contractId}-`;
    if (!storagePath.startsWith(prefix)) {
      return 'Document';
    }
    
    // Remove the prefix
    const remaining = storagePath.substring(prefix.length);
    
    // Find the last dash before the encoded name (after timestamp)
    // Support multiple timestamp formats:
    // 1. ETL format: YYYY-MM-DDTHH-MM-SS-sss (no Z suffix)
    // 2. UI format: YYYY-MM-DDTHH-MM-SS-sssZ (with Z suffix)
    // 3. ETL format with dashes: YYYY-MM-DDTHH-MM-SS-sss (colons replaced with dashes)
    
    // More flexible regex to handle various timestamp formats
    const timestampRegex = /^\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}-\d{3,6}(Z?)-/;
    const match = remaining.match(timestampRegex);
    
    if (match) {
      // Extract everything after the timestamp and before the file extension
      const afterTimestamp = remaining.substring(match[0].length);
      const lastDotIndex = afterTimestamp.lastIndexOf('.');
      const encodedName = lastDotIndex > 0 ? afterTimestamp.substring(0, lastDotIndex) : afterTimestamp;
      
      // For ETL workflow files, the encodedName is actually the solicitation number
      // For UI uploaded files, it's an encoded filename that needs decoding
      if (encodedName && encodedName.length > 0) {
        // Check if this looks like a solicitation number (contains letters and numbers)
        if (/[A-Z]/.test(encodedName) && /[0-9]/.test(encodedName)) {
          // This is likely a solicitation number from ETL workflow
          return encodedName;
        } else {
          // This is likely an encoded filename from UI upload, try to decode it
          try {
            const decodedName = decodeURIComponent(encodedName.replace(/_/g, '()'));
            return decodedName || 'Document';
          } catch {
            // If decoding fails, return the encoded name as-is
            return encodedName;
          }
        }
      }
    }
    
    return 'Document';
  } catch (error) {
    console.error('❌ Error in extractOriginalFileName:', error);
    return 'Document';
  }
};

// Hook for uploading documents to Supabase storage
export const useUploadDocument = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ 
      file, 
      contractId, 
      fileName, 
      fileType 
    }: { 
      file: File; 
      contractId: string; 
      fileName: string; 
      fileType: string; 
    }) => {
      try {
        // Create a unique filename that encodes the original filename
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const fileExtension = file.name.split('.').pop();
        
        // Encode the original filename (remove extension and encode special chars)
        const originalNameWithoutExt = fileName.replace(/\.[^/.]+$/, "");
        const encodedOriginalName = encodeURIComponent(originalNameWithoutExt).replace(/[()]/g, '_');
        
        // Format: contract-{contractId}-{timestamp}-{encodedOriginalName}.{extension}
        const uniqueFileName = `contract-${contractId}-${timestamp}-${encodedOriginalName}.${fileExtension}`;
        
        // Upload file to Supabase storage bucket
        const { data, error } = await supabase.storage
          .from('docs')
          .upload(uniqueFileName, file, {
            cacheControl: '3600',
            upsert: false
          });
        
        if (error) throw error;
        
        // Create a signed URL for the uploaded file (valid for 1 hour)
        const { data: urlData, error: urlError } = await supabase.storage
          .from('docs')
          .createSignedUrl(uniqueFileName, 3600); // 1 hour expiry
        
        if (urlError) {
          console.error('Error creating signed URL:', urlError);
          throw urlError;
        }
        
        return {
          originalFileName: fileName,
          fileType: fileType,
          storagePath: uniqueFileName,
          publicUrl: urlData.signedUrl,
          uploadedAt: new Date().toISOString(),
          contractId: contractId
        };
      } catch (error) {
        console.error('Error uploading document:', error);
        throw error;
      }
    },
    onSuccess: () => {
      // Invalidate relevant queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['universal_contract_queue'] });
    },
  });
};