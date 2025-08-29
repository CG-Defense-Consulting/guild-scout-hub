export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type Database = {
  // Allows to automatically instantiate createClient with right options
  // instead of createClient<Database, { PostgrestVersion: 'XX' }>(URL, KEY)
  __InternalSupabase: {
    PostgrestVersion: "12.2.3 (519615d)"
  }
  public: {
    Tables: {
      award_history: {
        Row: {
          awd_date: string
          cage: string
          contract_number: string
          id: string
          national_stock_number: string
          quantity: number
          total: number
          unit_cost: number
        }
        Insert: {
          awd_date: string
          cage: string
          contract_number: string
          id?: string
          national_stock_number: string
          quantity: number
          total: number
          unit_cost: number
        }
        Update: {
          awd_date?: string
          cage?: string
          contract_number?: string
          id?: string
          national_stock_number?: string
          quantity?: number
          total?: number
          unit_cost?: number
        }
        Relationships: []
      }
      client_pricing_queue: {
        Row: {
          client: string
          client_type: string | null
          cost_breakdown_json: Json | null
          id: string
          received_at: string | null
          submitted_at: string | null
          submitted_by: string | null
        }
        Insert: {
          client: string
          client_type?: string | null
          cost_breakdown_json?: Json | null
          id?: string
          received_at?: string | null
          submitted_at?: string | null
          submitted_by?: string | null
        }
        Update: {
          client?: string
          client_type?: string | null
          cost_breakdown_json?: Json | null
          id?: string
          received_at?: string | null
          submitted_at?: string | null
          submitted_by?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "client_pricing_queue_id_fkey"
            columns: ["id"]
            isOneToOne: false
            referencedRelation: "universal_contract_queue"
            referencedColumns: ["id"]
          },
        ]
      }
      rfq_index_extract: {
        Row: {
          cde_g: string | null
          closed: boolean | null
          desc: string | null
          id: string
          item: string
          national_stock_number: string
          purchase_request_number: string
          quantity: number
          quote_issue_date: string
          raw: string | null
          return_by_date: string
          solicitation_number: string
          unit_type: string
          unit_type_long: string
        }
        Insert: {
          cde_g?: string | null
          closed?: boolean | null
          desc?: string | null
          id?: string
          item: string
          national_stock_number: string
          purchase_request_number: string
          quantity: number
          quote_issue_date: string
          raw?: string | null
          return_by_date: string
          solicitation_number: string
          unit_type: string
          unit_type_long: string
        }
        Update: {
          cde_g?: string | null
          closed?: boolean | null
          desc?: string | null
          id?: string
          item?: string
          national_stock_number?: string
          purchase_request_number?: string
          quantity?: number
          quote_issue_date?: string
          raw?: string | null
          return_by_date?: string
          solicitation_number?: string
          unit_type?: string
          unit_type_long?: string
        }
        Relationships: []
      }
      test_table: {
        Row: {
          a: number
          b: string | null
          c: string | null
          id: string
        }
        Insert: {
          a: number
          b?: string | null
          c?: string | null
          id?: string
        }
        Update: {
          a?: number
          b?: string | null
          c?: string | null
          id?: string
        }
        Relationships: []
      }
      partner_queue: {
        Row: {
          id: string
          partner: string
          submitted_at: string
          submitted_by: string
          partner_type: 'MFG' | 'LOG' | 'SUP'
        }
        Insert: {
          id: string
          partner: string
          submitted_at?: string
          submitted_by: string
          partner_type: 'MFG' | 'LOG' | 'SUP'
        }
        Update: {
          id?: string
          partner?: string
          submitted_at?: string
          submitted_by?: string
          partner_type?: 'MFG' | 'LOG' | 'SUP'
        }
        Relationships: [
          {
            foreignKeyName: "partner_queue_id_fkey"
            columns: ["id"]
            isOneToOne: true
            referencedRelation: "universal_contract_queue"
            referencedColumns: ["id"]
          },
        ]
      }
      universal_contract_queue: {
        Row: {
          added_by: string | null
          created_at: string
          current_stage: string | null
          destination_json: Json | null
          id: string
          long_description: string | null
          mil_std: Json | null
          part_number: string | null
          stage_timeline: Json | null
        }
        Insert: {
          added_by?: string | null
          created_at?: string
          current_stage?: string | null
          destination_json?: Json | null
          id?: string
          long_description?: string | null
          mil_std?: Json | null
          part_number?: string | null
          stage_timeline?: Json | null
        }
        Update: {
          added_by?: string | null
          created_at?: string
          current_stage?: string | null
          destination_json?: Json | null
          id?: string
          long_description?: string | null
          mil_std?: Json | null
          part_number?: string | null
          stage_timeline?: Json | null
        }
        Relationships: [
          {
            foreignKeyName: "universal_contract_queue_id_fkey"
            columns: ["id"]
            isOneToOne: true
            referencedRelation: "rfq_index_extract"
            referencedColumns: ["id"]
          },
        ]
      }
      user_page_entitlements: {
        Row: {
          page_index: string | null
          user_id: string
        }
        Insert: {
          page_index?: string | null
          user_id?: string
        }
        Update: {
          page_index?: string | null
          user_id?: string
        }
        Relationships: []
      }
      workflow_errors: {
        Row: {
          error_message: string
          id: string
          job_name: string
          row_end: number | null
          row_start: number | null
          step_name: string
          timestamp: string | null
        }
        Insert: {
          error_message: string
          id?: string
          job_name: string
          row_end?: number | null
          row_start?: number | null
          step_name: string
          timestamp?: string | null
        }
        Update: {
          error_message?: string
          id?: string
          job_name?: string
          row_end?: number | null
          row_start?: number | null
          step_name?: string
          timestamp?: string | null
        }
        Relationships: []
      }
    }
    Views: {
      no_awd_hist_nsns: {
        Row: {
          national_stock_number: string | null
          solicitation_number: string | null
        }
        Insert: {
          national_stock_number?: string | null
          solicitation_number?: string | null
        }
        Update: {
          national_stock_number?: string | null
          solicitation_number?: string | null
        }
        Relationships: []
      },
      trends_aggregated: {
        Row: {
          period: string
          start_date: string
          end_date: string
          total_rfqs: number
          total_quantity: number
          avg_quantity: number
          unique_nsns: number
          unique_solicitations: number
          weapons_count: number
          electrical_count: number
          textiles_count: number
          fasteners_count: number
          other_count: number
          total_awards: number
          total_award_value: number
          avg_award_value: number
          unique_award_nsns: number
          unique_suppliers: number
          awards_under_10k: number
          awards_10k_to_100k: number
          awards_100k_to_1m: number
          awards_over_1m: number
          contracts_with_award_history: number
          estimated_total_value: number
          daily_rfq_series: Json
          daily_award_series: Json
          top_suppliers: Json
          top_items: Json
        }
        Insert: {
          period?: string
          start_date?: string
          end_date?: string
          total_rfqs?: number
          total_quantity?: number
          avg_quantity?: number
          unique_nsns?: number
          unique_solicitations?: number
          weapons_count?: number
          electrical_count?: number
          textiles_count?: number
          fasteners_count?: number
          other_count?: number
          total_awards?: number
          total_award_value?: number
          avg_award_value?: number
          unique_award_nsns?: number
          unique_suppliers?: number
          awards_under_10k?: number
          awards_10k_to_100k?: number
          awards_100k_to_1m?: number
          awards_over_1m?: number
          contracts_with_award_history?: number
          estimated_total_value?: number
          daily_rfq_series?: Json
          daily_award_series?: Json
          top_suppliers?: Json
          top_items?: Json
        }
        Update: {
          period?: string
          start_date?: string
          end_date?: string
          total_rfqs?: number
          total_quantity?: number
          avg_quantity?: number
          unique_nsns?: number
          unique_solicitations?: number
          weapons_count?: number
          electrical_count?: number
          textiles_count?: number
          fasteners_count?: number
          other_count?: number
          total_awards?: number
          total_award_value?: number
          avg_award_value?: number
          unique_award_nsns?: number
          unique_suppliers?: number
          awards_under_10k?: number
          awards_10k_to_100k?: number
          awards_100k_to_1m?: number
          awards_over_1m?: number
          contracts_with_award_history?: number
          estimated_total_value?: number
          daily_rfq_series?: Json
          daily_award_series?: Json
          top_suppliers?: Json
          top_items?: Json
        }
        Relationships: []
      },
      trends_aggregated_materialized: {
        Row: {
          period: string
          start_date: string
          end_date: string
          total_rfqs: number
          total_quantity: number
          avg_quantity: number
          unique_nsns: number
          unique_solicitations: number
          weapons_count: number
          electrical_count: number
          textiles_count: number
          fasteners_count: number
          other_count: number
          total_awards: number
          total_award_value: number
          avg_award_value: number
          unique_award_nsns: number
          unique_suppliers: number
          awards_under_10k: number
          awards_10k_to_100k: number
          awards_100k_to_1m: number
          awards_over_1m: number
          contracts_with_award_history: number
          estimated_total_value: number
          daily_rfq_series: Json
          daily_award_series: Json
          top_suppliers: Json
          top_items: Json
        }
        Insert: {
          period?: string
          start_date?: string
          end_date?: string
          total_rfqs?: number
          total_quantity?: number
          avg_quantity?: number
          unique_nsns?: number
          unique_solicitations?: number
          weapons_count?: number
          electrical_count?: number
          textiles_count?: number
          fasteners_count?: number
          other_count?: number
          total_awards?: number
          total_award_value?: number
          avg_award_value?: number
          unique_award_nsns?: number
          unique_suppliers?: number
          awards_under_10k?: number
          awards_10k_to_100k?: number
          awards_100k_to_1m?: number
          awards_over_1m?: number
          contracts_with_award_history?: number
          estimated_total_value?: number
          daily_rfq_series?: Json
          daily_award_series?: Json
          top_suppliers?: Json
          top_items?: Json
        }
        Update: {
          period?: string
          start_date?: string
          end_date?: string
          total_rfqs?: number
          total_quantity?: number
          avg_quantity?: number
          unique_nsns?: number
          unique_solicitations?: number
          weapons_count?: number
          electrical_count?: number
          textiles_count?: number
          fasteners_count?: number
          other_count?: number
          total_awards?: number
          total_award_value?: number
          avg_award_value?: number
          unique_award_nsns?: number
          unique_suppliers?: number
          awards_under_10k?: number
          awards_10k_to_100k?: number
          awards_100k_to_1m?: number
          awards_over_1m?: number
          contracts_with_award_history?: number
          estimated_total_value?: number
          daily_rfq_series?: Json
          daily_award_series?: Json
          top_suppliers?: Json
          top_items?: Json
        }
        Relationships: []
      }
    }
    Functions: {
      get_all_column_min_max: {
        Args: Record<PropertyKey, never>
        Returns: {
          quantity_max: number
          quantity_min: number
          quote_issue_date_max: string
          quote_issue_date_min: string
          return_by_date_max: string
          return_by_date_min: string
        }[]
      }
      get_db_size: {
        Args: { "": Json }
        Returns: number
      }
      refresh_trends_view: {
        Args: Record<PropertyKey, never>
        Returns: void
      }
      get_trends_for_period: {
        Args: { period_param: string }
        Returns: {
          period: string
          start_date: string
          end_date: string
          total_rfqs: number
          total_quantity: number
          avg_quantity: number
          unique_nsns: number
          unique_solicitations: number
          weapons_count: number
          electrical_count: number
          textiles_count: number
          fasteners_count: number
          other_count: number
          total_awards: number
          total_award_value: number
          avg_award_value: number
          unique_award_nsns: number
          unique_suppliers: number
          awards_under_10k: number
          awards_10k_to_100k: number
          awards_100k_to_1m: number
          awards_over_1m: number
          contracts_with_award_history: number
          estimated_total_value: number
          daily_rfq_series: Json
          daily_award_series: Json
          top_suppliers: Json
          top_items: Json
        }[]
      }
    }
    Enums: {
      [_ in never]: never
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}

type DatabaseWithoutInternals = Omit<Database, "__InternalSupabase">

type DefaultSchema = DatabaseWithoutInternals[Extract<keyof Database, "public">]

export type Tables<
  DefaultSchemaTableNameOrOptions extends
    | keyof (DefaultSchema["Tables"] & DefaultSchema["Views"])
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
        DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
      DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])[TableName] extends {
      Row: infer R
    }
    ? R
    : never
  : DefaultSchemaTableNameOrOptions extends keyof (DefaultSchema["Tables"] &
        DefaultSchema["Views"])
    ? (DefaultSchema["Tables"] &
        DefaultSchema["Views"])[DefaultSchemaTableNameOrOptions] extends {
        Row: infer R
      }
      ? R
      : never
    : never

export type TablesInsert<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Insert: infer I
    }
    ? I
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Insert: infer I
      }
      ? I
      : never
    : never

export type TablesUpdate<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Update: infer U
    }
    ? U
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Update: infer U
      }
      ? U
      : never
    : never

export type Enums<
  DefaultSchemaEnumNameOrOptions extends
    | keyof DefaultSchema["Enums"]
    | { schema: keyof DatabaseWithoutInternals },
  EnumName extends DefaultSchemaEnumNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"]
    : never = never,
> = DefaultSchemaEnumNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"][EnumName]
  : DefaultSchemaEnumNameOrOptions extends keyof DefaultSchema["Enums"]
    ? DefaultSchema["Enums"][DefaultSchemaEnumNameOrOptions]
    : never

export type CompositeTypes<
  PublicCompositeTypeNameOrOptions extends
    | keyof DefaultSchema["CompositeTypes"]
    | { schema: keyof DatabaseWithoutInternals },
  CompositeTypeName extends PublicCompositeTypeNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"]
    : never = never,
> = PublicCompositeTypeNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"][CompositeTypeName]
  : PublicCompositeTypeNameOrOptions extends keyof DefaultSchema["CompositeTypes"]
    ? DefaultSchema["CompositeTypes"][PublicCompositeTypeNameOrOptions]
    : never

export const Constants = {
  public: {
    Enums: {},
  },
} as const
