# ETL Module

This module handles automated workflows for extracting, transforming, and loading data from the DIBBS website (dibbs.bsm.dla.mil).

## Structure

```
etl/
├── workflows/           # Workflow definitions
│   ├── adhoc/          # UI-triggered workflows
│   └── scheduled/      # Automated scheduled workflows
├── core/               # Core ETL functionality
│   ├── scrapers/       # Web scraping utilities
│   ├── processors/     # Data processing logic
│   ├── uploaders/      # Database upload handlers
│   └── validators/     # Data validation
├── config/             # Configuration files
├── utils/              # Shared utilities
├── types/              # TypeScript definitions
└── logs/               # Log files
```

## Adhoc Workflows

### `pull_single_rfq_pdf`
Grabs the RFQ PDF given a Solicitation Number.

**Usage:**
```bash
python etl/workflows/adhoc/pull_single_rfq_pdf.py <SOLICITATION_NUMBER> [--output-dir DIR] [--verbose]
```

### `pull_day_rfq_pdfs`
Grabs the batch of RFQ PDFs for a given day.

**Usage:**
```bash
python etl/workflows/adhoc/pull_day_rfq_pdfs.py <DATE> [--output-dir DIR] [--max-pdfs N] [--verbose]
```

### `pull_day_rfq_index_extract`
Grabs the batch of new solicitation info for a given day.

**Usage:**
```bash
python etl/workflows/adhoc/pull_day_rfq_index_extract.py <DATE> [--include-details] [--max-solicitations N] [--verbose]
```

### `pull_single_award_history`
Grabs the RFQ PDF given a solicitation number and parses award history.

**Usage:**
```bash
python etl/workflows/adhoc/pull_single_award_history.py <SOLICITATION_NUMBER> [--output-dir DIR] [--force-refresh] [--verbose]
```

### `pull_day_award_history`
Grabs the RFQ PDFs batch given a day and parses award history.

**Usage:**
```bash
python etl/workflows/adhoc/pull_day_award_history.py <DATE> [--output-dir DIR] [--max-solicitations N] [--force-refresh] [--verbose]
```

## Tech Stack

- **Python**: Heavy data processing and scraping
- **Node.js**: Orchestration and Supabase integration
- **Supabase**: Database storage
- **GitHub Actions**: Workflow execution

## Implementation Details

### DIBBS Scraper
The `DibbsScraper` class handles:
- **Consent Page Handling**: Automatically clicks "Ok" on DLA consent pages
- **PDF Download**: Downloads RFQ PDFs using the format: `https://dibbs2.bsm.dla.mil/Downloads/RFQ/{last_char}/{solicitation_number}.PDF`
- **Selenium Integration**: Uses Chrome WebDriver for browser automation
- **Error Handling**: Graceful fallbacks and comprehensive logging

### PDF Processing
The `PDFProcessor` class provides:
- **Text Extraction**: Uses pdfplumber (primary) and PyPDF2 (fallback)
- **Data Parsing**: Extracts solicitation numbers, titles, dates, agency info
- **Pattern Recognition**: Regex-based extraction of common RFQ fields
- **Metadata Storage**: File size, extraction timestamps, raw text samples

### Supabase Integration
The `SupabaseUploader` handles:
- **Storage Upload**: PDFs uploaded to 'docs' bucket with unique naming
- **Database Insertion**: RFQ data stored in database tables
- **Signed URLs**: Generates temporary access URLs for uploaded files
- **Duplicate Prevention**: Checks for existing records before insertion

## Setup

### Prerequisites

- Python 3.8+
- Chrome browser installed
- ChromeDriver (automatically managed by webdriver-manager)
- Access to DIBBS website
- Supabase credentials

### Installation

1. **Install Python dependencies:**
   ```bash
   cd etl
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   ```bash
   cp config/env.example config/.env
   # Edit .env with your actual values
   ```

3. **Install Chrome WebDriver:**
   ```bash
   # This is handled automatically by webdriver-manager
   # But you can install manually if needed
   ```

4. **Verify Supabase connection:**
   ```bash
   python -c "from core.uploaders.supabase_uploader import SupabaseUploader; u = SupabaseUploader()"
   ```

### Configuration

Key environment variables:
- `VITE_SUPABASE_URL`: Your Supabase project URL
- `VITE_SUPABASE_ANON_KEY`: Your Supabase anonymous key
- `DIBBS_DOWNLOAD_DIR`: Directory for downloaded PDFs
- `SELENIUM_HEADLESS`: Whether to run browser in headless mode

## Testing

Run the test script to verify the scraper:
```bash
cd etl
python test_scraper.py
```

## Usage Examples

### Download Single RFQ
```python
from core.scrapers.dibbs_scraper import DibbsScraper

with DibbsScraper() as scraper:
    result = scraper.search_solicitation("SPE7L3-24-R-0001")
    if result:
        print(f"PDF downloaded: {result['pdf_path']}")
```

### Process and Upload RFQ
```python
from core.processors.pdf_processor import PDFProcessor
from core.uploaders.supabase_uploader import SupabaseUploader

# Process PDF
processor = PDFProcessor()
rfq_data = processor.extract_rfq_data("path/to/rfq.pdf")

# Upload to Supabase
uploader = SupabaseUploader()
success = uploader.upload_rfq_data(rfq_data)
```

## Database Schema

The module expects these tables (create if they don't exist):

### rfq_documents
- `id`: Primary key
- `solicitation_number`: Solicitation identifier
- `title`: RFQ title
- `pdf_path`: Storage path
- `public_url`: Signed URL
- `uploaded_at`: Timestamp
- `status`: Upload status

### rfq_index_extract
- `id`: Primary key
- `solicitation_number`: Solicitation identifier
- `title`: RFQ title
- `date_posted`: Posting date
- `status`: Solicitation status
- `agency`: Government agency
- `url`: Source URL
- `created_at`: Timestamp

### award_history
- `id`: Primary key
- `solicitation_number`: Solicitation identifier
- `award_data`: JSON award information
- `created_at`: Timestamp

## Next Steps

1. **Implement daily solicitation fetching** in `DibbsScraper.get_daily_solicitations()`
2. **Add data validation** and error handling
3. **Create configuration management** for environment variables
4. **Set up GitHub Actions workflows** for scheduled execution
5. **Add monitoring and alerting** for workflow execution
6. **Implement award history parsing** in `AwardProcessor`
7. **Add rate limiting** and respect for website terms of service
