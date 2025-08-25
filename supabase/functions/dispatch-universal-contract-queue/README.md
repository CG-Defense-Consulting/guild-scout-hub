# Dispatch Universal Contract Queue Edge Function

This Supabase Edge Function dispatches the Universal Contract Queue Data Pull workflow to GitHub Actions.

## Purpose

This function allows you to trigger the comprehensive data pull workflow for contracts in the universal contract queue from your application, without needing to manually trigger GitHub Actions. The workflow **internally queries the `universal_contract_queue` table** to discover which contracts need processing based on predefined conditions.

## Endpoint

```
POST /functions/v1/dispatch-universal-contract-queue
```

## Request Body

```json
{
  "force_refresh": false,
  "headless": true,
  "timeout": 30,
  "retry_attempts": 3,
  "batch_size": 50,
  "verbose": false,
  "limit": 100
}
```

### Optional Fields

- `force_refresh`: Force refresh even if data already exists (default: false)
- `headless`: Run Chrome in headless mode (default: true)
- `timeout`: Timeout for page operations in seconds (default: 30)
- `retry_attempts`: Number of retry attempts for each operation (default: 3)
- `batch_size`: Size of batches for database uploads (default: 50)
- `verbose`: Enable verbose logging (default: false)
- `limit`: Limit number of contracts to process (default: no limit)

## Response

### Success Response (200)

```json
{
  "success": true,
  "message": "Successfully dispatched universal contract queue data pull workflow",
  "workflow": "universal-contract-queue-data-pull.yml",
  "dispatched_at": "2024-01-15T10:30:00.000Z",
  "inputs": {
    "headless": "true",
    "timeout": "30",
    "limit": "100"
  },
  "note": "Workflow will internally query universal_contract_queue to discover contracts needing processing"
}
```

### Error Responses

#### Server Error (500)
```json
{
  "error": "Failed to dispatch GitHub workflow",
  "github_status": 401,
  "github_error": "Bad credentials"
}
```

## Environment Variables

The following environment variables must be set in your Supabase project:

- `GITHUB_TOKEN`: GitHub Personal Access Token with workflow dispatch permissions
- `GITHUB_OWNER`: GitHub organization/username (default: CGDC-git)
- `GITHUB_REPO`: GitHub repository name (default: guild-scout-hub)
- `GITHUB_WORKFLOW`: GitHub workflow filename (default: universal-contract-queue-data-pull.yml)

## Usage Examples

### JavaScript/TypeScript

```typescript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient('YOUR_SUPABASE_URL', 'YOUR_SUPABASE_ANON_KEY')

// Dispatch workflow - no contract IDs needed!
const { data, error } = await supabase.functions.invoke('dispatch-universal-contract-queue', {
  body: {
    force_refresh: true,
    verbose: true,
    limit: 50  // Process up to 50 contracts
  }
})

if (error) {
  console.error('Error dispatching workflow:', error)
} else {
  console.log('Workflow dispatched successfully:', data)
}
```

### cURL

```bash
curl -X POST 'https://your-project.supabase.co/functions/v1/dispatch-universal-contract-queue' \
  -H 'Authorization: Bearer YOUR_SUPABASE_ANON_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    "force_refresh": true,
    "verbose": true,
    "limit": 50
  }'
```

## How It Works

### **1. Internal Contract Discovery**
The dispatched workflow automatically queries the `universal_contract_queue` table to find contracts that need processing:

```sql
SELECT 
    ucq.id as contract_id,
    ucq.solicitation_number,
    ucq.national_stock_number,
    -- ... other fields
FROM universal_contract_queue ucq
LEFT JOIN rfq_index_extract rie ON ucq.id = rie.id
WHERE (
    -- Missing AMSC code
    rie.cde_g IS NULL
    OR
    -- Missing closed status
    rie.closed IS NULL
    OR
    -- Missing RFQ index
    rie.id IS NULL
)
AND ucq.national_stock_number IS NOT NULL
ORDER BY ucq.award_date DESC NULLS LAST
```

### **2. Automatic Data Gap Analysis**
For each discovered contract, the workflow analyzes what data is missing:
- **AMSC codes**: Extracted from DIBBS NSN pages
- **RFQ PDFs**: Downloaded when missing and AMSC code is empty
- **Closed status**: Determined while extracting AMSC codes

### **3. Conditional Processing**
The workflow applies business logic to determine what operations to run:
- **If RFQ PDF exists**: Only extract missing data (AMSC, closed status)
- **If RFQ PDF missing AND AMSC empty**: Extract both AMSC and download PDF
- **If RFQ PDF missing BUT AMSC exists**: Do nothing (PDF issue, don't touch)

## Business Logic

The dispatched workflow implements the following business logic:

1. **INTERNALLY query universal_contract_queue** for contracts with missing data
2. **Apply predefined conditions** to filter contracts that need processing
3. **If AMSC code is missing**: Extract AMSC code
4. **If RFQ PDF is missing**: Download RFQ PDF (only when AMSC is also missing)
5. **While extracting AMSC code**, if we see "no open solicitation" language, mark as closed

## Workflow Details

The dispatched workflow will:

1. **Query universal_contract_queue** to discover contracts needing processing
2. **Set up Chrome and ChromeDriver** once (shared across all operations)
3. **Analyze data gaps** for each discovered contract
4. **Apply conditional logic** to determine what needs processing
5. **Run appropriate operations** (consent handling, NSN extraction, closed status checking)
6. **Upload results to Supabase**
7. **Clean up resources**

## Monitoring

- Check GitHub Actions for workflow execution status
- Monitor Supabase Edge Function logs for dispatch status
- Review workflow results in the GitHub Actions artifacts
- Check the workflow logs to see which contracts were discovered and processed

## Security

- The function does not verify JWT tokens (set `verify_jwt = false`)
- GitHub token should have minimal required permissions (workflow dispatch only)
- No input validation needed since no user data is required
- CORS is enabled for cross-origin requests

## Troubleshooting

### Common Issues

1. **GitHub Token Invalid**: Ensure the token has workflow dispatch permissions
2. **Workflow Not Found**: Verify the workflow file exists in the repository
3. **No Contracts Found**: Check if there are contracts in `universal_contract_queue` with missing data
4. **Rate Limiting**: GitHub API has rate limits; avoid rapid successive calls

### Debug Mode

Enable verbose logging by setting `"verbose": true` in the request body to get detailed workflow information about contract discovery and processing decisions.

## Benefits of This Approach

### **1. Fully Automated**
- No need to specify contract IDs
- Workflow automatically discovers what needs processing
- Runs independently based on data gaps

### **2. Intelligent Processing**
- Only processes contracts that actually need data
- Applies business logic to avoid unnecessary operations
- Handles edge cases gracefully

### **3. Scalable**
- Can process any number of contracts
- Optional limit parameter for controlled processing
- Efficient resource usage with shared Chrome setup

### **4. Maintenance-Free**
- No need to track which contracts need processing
- Automatically adapts to new contracts added to the queue
- Self-healing as data gaps are filled
