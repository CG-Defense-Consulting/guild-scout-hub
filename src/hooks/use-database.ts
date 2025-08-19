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
            } else if (key === 'return_by_date') {
              query = query.lte('return_by_date', value);
            } else {
              query = query.ilike(key, `%${value}%`);
            }
          }
        });
      }
      
      const { data, error } = await query;
      if (error) throw error;
      return data;
    },
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
      const { data, error } = await supabase
        .from('universal_contract_queue')
        .select('*')
        .order('created_at', { ascending: false });
      if (error) throw error;
      return data;
    },
  });
};

export const useAddToQueue = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (rfqData: any) => {
      const { data, error } = await supabase
        .from('universal_contract_queue')
        .insert([{
          part_number: rfqData.national_stock_number,
          long_description: rfqData.desc,
          rfq_link: `RFQ-${rfqData.solicitation_number}`,
          added_by: 'system'
        }]);
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