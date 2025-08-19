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
          cde_g: boolean
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
          cde_g?: boolean
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
          cde_g?: boolean
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
      universal_contract_queue: {
        Row: {
          added_by: string | null
          created_at: string
          destination_json: Json | null
          id: string
          long_description: string | null
          part_number: string | null
          rfq_link: string | null
          tech_doc_link: string | null
        }
        Insert: {
          added_by?: string | null
          created_at?: string
          destination_json?: Json | null
          id?: string
          long_description?: string | null
          part_number?: string | null
          rfq_link?: string | null
          tech_doc_link?: string | null
        }
        Update: {
          added_by?: string | null
          created_at?: string
          destination_json?: Json | null
          id?: string
          long_description?: string | null
          part_number?: string | null
          rfq_link?: string | null
          tech_doc_link?: string | null
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
