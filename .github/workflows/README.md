# GitHub Actions Workflows for DIBBS ETL

This directory contains GitHub Actions workflows for automating DIBBS data extraction and processing.

## Available Workflows

### 1. Pull Single RFQ PDF (`pull-single-rfq-pdf.yml`)

Downloads a single RFQ PDF for a given solicitation number.

#### Trigger Methods

1. **Manual Trigger (GitHub UI)**
   - Go to Actions → Pull Single RFQ PDF → Run workflow
   - Fill in the solicitation number
   - Optionally specify output directory and verbose logging

2. **API/Webhook Trigger**
   ```bash
   curl -X POST \
     -H "Authorization: token YOUR_GITHUB_TOKEN" \
     -H "Accept: application/vnd.github.v3+json" \
     https://api.github.com/repos/OWNER/REPO/dispatches \
     -d '{"event_type":"pull_single_rfq_pdf","client_payload":{"solicitation_number":"SPE7L3-24-R-0001"}}'
   ```

3. **Scheduled Runs** (optional)
   - Uncomment the schedule section in the workflow
   - Currently set to run daily at 9 AM UTC

#### Input Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `solicitation_number` | string | ✅ Yes | `SPE7L3-24-R-0001` | DIBBS solicitation number |
| `output_dir` | string | ❌ No | `./downloads` | Custom output directory |
| `verbose` | boolean | ❌ No | `false` | Enable verbose logging |

#### Output Artifacts

- **PDF Files**: Downloaded RFQ PDFs (retained for 7 days)
- **Logs**: ETL processing logs (retained for 30 days)

#### Example Usage

```bash
# Trigger via GitHub CLI
gh workflow run pull-single-rfq-pdf.yml -f solicitation_number=SPE7L3-24-R-0001

# Trigger via API
curl -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/OWNER/REPO/dispatches \
  -d '{"event_type":"pull_single_rfq_pdf","client_payload":{"solicitation_number":"SPE7L3-24-R-0001"}}'
```

## Setup Requirements

### GitHub Secrets

The following secrets must be configured in your repository:

1. **`VITE_SUPABASE_URL`**: Your Supabase project URL
2. **`VITE_SUPABASE_PUBLISHABLE_KEY`**: Your Supabase anonymous key

### Environment Setup

The workflows automatically:
- Set up Python 3.8 environment
- Install Chrome and ChromeDriver
- Install Python dependencies from `etl/requirements.txt`
- Create necessary directories (`downloads/`, `logs/`)
- Set environment variables

## Workflow Features

### Error Handling
- Comprehensive logging
- Error summaries on failure
- Artifact retention for debugging
- Graceful cleanup

### Performance
- 30-minute timeout limit
- Headless Chrome for efficiency
- Parallel job execution support
- Resource cleanup

### Monitoring
- Detailed step-by-step logging
- Artifact uploads for inspection
- Failure notifications
- Success/failure status tracking

## Customization

### Adding New Workflows

To create workflows for other ETL functions:

1. Copy the existing workflow file
2. Modify the job name and description
3. Update the Python script path
4. Adjust input parameters as needed
5. Modify artifact paths if necessary

### Modifying Existing Workflows

Common customizations:
- **Timeout**: Adjust `timeout-minutes` value
- **Schedule**: Modify cron expression in schedule section
- **Python Version**: Change `python-version` in setup-python step
- **Retention**: Adjust artifact retention days

## Troubleshooting

### Common Issues

1. **Chrome Setup Failures**
   - Ensure `browser-actions/setup-chrome@v1` action is used
   - Check Chrome dependency installation step

2. **Environment Variable Issues**
   - Verify GitHub secrets are properly configured
   - Check .env file creation in workflow

3. **Python Dependency Issues**
   - Ensure `etl/requirements.txt` exists and is valid
   - Check Python version compatibility

4. **Permission Issues**
   - Verify workflow has necessary permissions
   - Check repository settings for Actions

### Debugging

1. **Check Workflow Logs**: Full logs are available in the Actions tab
2. **Download Artifacts**: Logs and files are uploaded as artifacts
3. **Enable Verbose Logging**: Use the verbose input parameter
4. **Check Error Summary**: Workflow includes error summary step

## Security Considerations

- **Secrets**: Never hardcode sensitive information
- **Artifacts**: Downloaded PDFs are retained for limited time
- **Permissions**: Use minimal required permissions for workflows
- **Rate Limiting**: Respect DIBBS website terms of service

## Next Steps

1. **Configure GitHub Secrets** with your Supabase credentials
2. **Test the Workflow** with a known solicitation number
3. **Set up Monitoring** for workflow execution
4. **Create Additional Workflows** for other ETL functions
5. **Implement Scheduled Runs** for automated processing
