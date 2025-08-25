import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

interface RequestBody {
  force_refresh?: boolean
  headless?: boolean
  timeout?: number
  retry_attempts?: number
  batch_size?: number
  verbose?: boolean
  limit?: number
}

interface WorkflowDispatchPayload {
  ref: string
  inputs: {
    force_refresh?: string
    headless?: string
    timeout?: string
    retry_attempts?: string
    batch_size?: string
    verbose?: string
    limit?: string
  }
}

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // Parse request body
    const body: RequestBody = await req.json()
    
    // Get environment variables
    const githubToken = Deno.env.get('GITHUB_TOKEN')
    const githubOwner = Deno.env.get('GITHUB_OWNER') || 'CGDC-git'
    const githubRepo = Deno.env.get('GITHUB_REPO') || 'guild-scout-hub'
    const githubWorkflow = Deno.env.get('GITHUB_WORKFLOW') || 'universal-contract-queue-data-pull.yml'

    if (!githubToken) {
      console.error('GITHUB_TOKEN environment variable is not set')
      return new Response(
        JSON.stringify({ 
          error: 'GitHub token not configured' 
        }),
        { 
          status: 500, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }

    // Prepare workflow dispatch payload
    const workflowPayload: WorkflowDispatchPayload = {
      ref: 'main', // or 'master' depending on your default branch
      inputs: {
        ...(body.force_refresh !== undefined && { force_refresh: body.force_refresh.toString() }),
        ...(body.headless !== undefined && { headless: body.headless.toString() }),
        ...(body.timeout !== undefined && { timeout: body.timeout.toString() }),
        ...(body.retry_attempts !== undefined && { retry_attempts: body.retry_attempts.toString() }),
        ...(body.batch_size !== undefined && { batch_size: body.batch_size.toString() }),
        ...(body.verbose !== undefined && { verbose: body.verbose.toString() }),
        ...(body.limit !== undefined && { limit: body.limit.toString() })
      }
    }

    // Dispatch GitHub Actions workflow
    const githubResponse = await fetch(
      `https://api.github.com/repos/${githubOwner}/${githubRepo}/actions/workflows/${githubWorkflow}/dispatches`,
      {
        method: 'POST',
        headers: {
          'Authorization': `token ${githubToken}`,
          'Accept': 'application/vnd.github.v3+json',
          'Content-Type': 'application/json',
          'User-Agent': 'Supabase-Edge-Function'
        },
        body: JSON.stringify(workflowPayload)
      }
    )

    if (!githubResponse.ok) {
      const errorText = await githubResponse.text()
      console.error('GitHub API error:', githubResponse.status, errorText)
      
      return new Response(
        JSON.stringify({ 
          error: 'Failed to dispatch GitHub workflow',
          github_status: githubResponse.status,
          github_error: errorText
        }),
        { 
          status: 500, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }

    // Log successful dispatch
    console.log(`Successfully dispatched universal contract queue data pull workflow`)

    // Return success response
    return new Response(
      JSON.stringify({
        success: true,
        message: `Successfully dispatched universal contract queue data pull workflow`,
        workflow: githubWorkflow,
        dispatched_at: new Date().toISOString(),
        inputs: workflowPayload.inputs,
        note: "Workflow will internally query universal_contract_queue to discover contracts needing processing"
      }),
      { 
        status: 200, 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    )

  } catch (error) {
    console.error('Error in dispatch-universal-contract-queue function:', error)
    
    return new Response(
      JSON.stringify({ 
        error: 'Internal server error',
        message: error.message || 'Unknown error occurred'
      }),
      { 
        status: 500, 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    )
  }
})
