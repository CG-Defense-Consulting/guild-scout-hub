import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

interface WorkflowTriggerRequest {
  workflow_name: string
  contract_id?: string
  nsn?: string
  solicitation_number?: string
  target_date?: string
  verbose?: boolean
}

interface WorkflowConfig {
  name: string
  workflow_file: string
  required_params: string[]
  optional_params?: string[]
}

const WORKFLOW_CONFIGS: Record<string, WorkflowConfig> = {
  'pull_single_rfq_pdf': {
    name: 'Pull Single RFQ PDF',
    workflow_file: 'pull-single-rfq-pdf.yml',
    required_params: ['solicitation_number'],
    optional_params: ['output_dir', 'verbose']
  },
  'extract_nsn_amsc': {
    name: 'Extract NSN AMSC Code',
    workflow_file: 'extract-nsn-amsc.yml',
    required_params: ['contract_id', 'nsn'],
    optional_params: ['verbose']
  },
  'pull_day_rfq_pdfs': {
    name: 'Pull Day RFQ PDFs',
    workflow_file: 'pull-day-rfq-pdfs.yml',
    required_params: ['target_date']
  },
  'pull_day_rfq_index_extract': {
    name: 'Pull Day RFQ Index Extract',
    workflow_file: 'pull-day-rfq-index-extract.yml',
    required_params: ['target_date']
  },
  'pull_single_award_history': {
    name: 'Pull Single Award History',
    workflow_file: 'pull-single-award-history.yml',
    required_params: ['solicitation_number']
  },
  'pull_day_award_history': {
    name: 'Pull Day Award History',
    workflow_file: 'pull-day-award-history.yml',
    required_params: ['target_date']
  }
}

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // Get environment variables (secrets)
    const githubToken = Deno.env.get('GITHUB_TOKEN')
    const githubOwner = Deno.env.get('GITHUB_OWNER') || 'CG-Defense-Consulting'
    const githubRepo = Deno.env.get('GITHUB_REPO') || 'guild-scout-hub'
    
    if (!githubToken) {
      throw new Error('GitHub token not configured. Please set GITHUB_TOKEN secret in Supabase.')
    }

    // Parse request body
    const body: WorkflowTriggerRequest = await req.json()
    const { workflow_name, ...params } = body

    // Validate workflow exists
    const workflowConfig = WORKFLOW_CONFIGS[workflow_name]
    if (!workflowConfig) {
      return new Response(
        JSON.stringify({ 
          error: 'Invalid workflow name',
          available_workflows: Object.keys(WORKFLOW_CONFIGS)
        }),
        { 
          status: 400, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      )
    }

    // Validate required parameters
    const missingParams = workflowConfig.required_params.filter(param => !params[param])
    if (missingParams.length > 0) {
      return new Response(
        JSON.stringify({ 
          error: `Missing required parameters: ${missingParams.join(', ')}`,
          required_params: workflowConfig.required_params,
          received_params: Object.keys(params)
        }),
        { 
          status: 400, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      )
    }

    // Prepare workflow dispatch payload
    // Only send the parameters that the workflow actually expects
    const expectedParams = [...workflowConfig.required_params, ...(workflowConfig.optional_params || [])]
    const filteredInputs: Record<string, any> = {}
    
    // Only include parameters that the workflow expects
    expectedParams.forEach(param => {
      if (params[param] !== undefined) {
        filteredInputs[param] = params[param]
      }
    })
    
    const workflowPayload = {
      ref: 'main', // or 'master' depending on your default branch
      inputs: filteredInputs
    }

    // Trigger GitHub Actions workflow
    const githubApiUrl = `https://api.github.com/repos/${githubOwner}/${githubRepo}/actions/workflows/${workflowConfig.workflow_file}/dispatches`
    
    const response = await fetch(githubApiUrl, {
      method: 'POST',
      headers: {
        'Authorization': `token ${githubToken}`,
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json',
        'User-Agent': 'GUILD-Scout-Hub/1.0'
      },
      body: JSON.stringify(workflowPayload)
    })

    if (!response.ok) {
      const errorText = await response.text()
      console.error('GitHub API error:', response.status, errorText)
      
      return new Response(
        JSON.stringify({ 
          error: 'Failed to trigger workflow',
          github_status: response.status,
          github_error: errorText
        }),
        { 
          status: 500, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      )
    }

    // Log successful trigger
    console.log(`Workflow ${workflow_name} triggered successfully for params:`, params)

    // Return success response
    return new Response(
      JSON.stringify({
        success: true,
        message: `Workflow ${workflowConfig.name} triggered successfully`,
        workflow: workflow_name,
        workflow_file: workflowConfig.workflow_file,
        params: params,
        triggered_at: workflowPayload.inputs.triggered_at
      }),
      { 
        status: 200, 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    )

  } catch (error) {
    console.error('Edge function error:', error)
    
    return new Response(
      JSON.stringify({ 
        error: 'Internal server error',
        message: error.message
      }),
      { 
        status: 500, 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    )
  }
})
