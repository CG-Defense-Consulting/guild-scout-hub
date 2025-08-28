# Scheduled Workflows

This directory contains scheduled workflows that run automatically at specified intervals.

## DIBBS RFQ Index Pull Workflow

### Overview
The `dibbs_rfq_index_pull.py` workflow is designed to run daily at 2:30 AM UTC to automatically pull RFQ index data from the DIBBS archive downloads and populate the `rfq_index_extract` table in Supabase.

### Workflow Steps
1. **Chrome Setup** - Initialize Chrome browser in headless mode
2. **Archive Downloads Navigation** - Navigate to the archive downloads page for a specific date
3. **Consent Page Handling** - Handle DLA consent pages if they appear
4. **Text File Download** - Download the RFQ index text file from the archive
5. **Text File Parsing** - Parse the downloaded file using the index processor
6. **Supabase Upload** - Upsert the parsed data to the `rfq_index_extract` table using the enhanced SupabaseUploadOperation

### Archive Downloads URL Format
The workflow navigates to archive downloads using the following URL format:
```
https://dibbs2.bsm.dla.mil/Downloads/RFQ/Archive/in{yy}{mm}{dd}.txt
```

Where:
- `{yy}` = Two-digit year (e.g., 24 for 2024)
- `{mm}` = Two-digit month (e.g., 01 for January)
- `{dd}` = Two-digit day (e.g., 15 for 15th)

### Date Handling
- **Scheduled runs**: Automatically uses yesterday's date
- **Manual runs**: Can specify a target date using the `--date` parameter or `TARGET_DATE` environment variable
- **Date format**: YYYY-MM-DD (e.g., 2024-01-15)
- **Fallback**: If no date is specified, defaults to yesterday's date

### Configuration
The workflow uses the following environment variables:
- `DIBBS_BASE_URL` - Base URL for the DIBBS archive (https://dibbs2.bsm.dla.mil)
- `DIBBS_DOWNLOAD_DIR` - Directory to save downloaded files
- `TARGET_DATE` - Target date for archive download (YYYY-MM-DD format)
- `VITE_SUPABASE_URL` - Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY` - Supabase service role key for database access

### GitHub Actions Integration
The workflow is triggered by the `.github/workflows/dibbs-rfq-index-scheduled.yml` file, which:
- Runs daily at 2:30 AM UTC using cron scheduling
- Supports manual triggering with optional parameters including target date
- Sets up the required environment (Python, Chrome, ChromeDriver)
- Automatically determines the target date for scheduled runs
- Executes the workflow and uploads logs and results as artifacts

### Manual Execution
You can run the workflow manually using:
```bash
cd etl
python workflows/scheduled/dibbs_rfq_index_pull.py [--force-refresh] [--verbose] [--log-level LEVEL] [--date YYYY-MM-DD]
```

### Operation Files
The workflow uses the following operations:
- `ChromeSetupOperation` - Sets up Chrome browser in headless mode
- `ArchiveDownloadsNavigationOperation` - Navigates to archive downloads pages with date-based URL construction
- `ConsentPageOperation` - Handles DLA consent pages that may appear during navigation
- `DibbsTextFileDownloadOperation` - Downloads text files from the archive
- `SupabaseUploadOperation` - Enhanced operation that supports both update and upsert operations with configurable conflict resolution

### Supabase Upload Configuration
The Supabase upload step is configured with:
- **Table**: `rfq_index_extract`
- **Operation Type**: `upsert` (insert or update based on conflicts)
- **Strategy**: `merge` (update existing records, insert new ones)
- **Conflict Resolution**: `update_existing` (update when conflicts occur)
- **Key Fields**: `["nsn"]` (use NSN for conflict detection)
- **Batch Size**: 50 records per batch

### Current Status
- **Chrome Setup**: Fully implemented with headless mode support
- **Archive Navigation**: Fully implemented with date-based URL construction
- **Consent Page Handling**: Fully implemented with retry mechanisms
- **Text Download**: Generic implementation with placeholder logic (to be filled in later)
- **Text Parsing**: Uses existing `IndexProcessor` (to be implemented later)
- **Database Upsert**: Uses enhanced `SupabaseUploadOperation` with full upsert support

### Future Implementation
The workflow is designed with placeholder implementations that will be replaced with:
1. Actual text file download logic from the archive page
2. Specific text file format parsing logic
3. Enhanced error handling and retry mechanisms
4. Data validation and quality checks

### Dependencies
- Chrome browser and ChromeDriver
- Python 3.8+
- Required Python packages (see `requirements.txt`)
- Supabase database access
- Network access to DIBBS archive (dibbs2.bsm.dla.mil)
