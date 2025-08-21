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
└── types/              # TypeScript definitions
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

## Development

This module is designed to work alongside the React/TypeScript frontend while maintaining clear separation of concerns.

### Prerequisites

- Python 3.8+
- Node.js 18+
- Access to DIBBS website
- Supabase credentials

### Setup

1. Install Python dependencies (requirements.txt to be created)
2. Install Node.js dependencies (package.json to be created)
3. Configure environment variables for Supabase
4. Set up logging directories

## Next Steps

1. Implement actual scraping logic in `DibbsScraper`
2. Add PDF processing capabilities
3. Create Supabase integration
4. Set up GitHub Actions workflows
5. Add data validation and error handling
6. Create configuration management
7. Add monitoring and alerting
