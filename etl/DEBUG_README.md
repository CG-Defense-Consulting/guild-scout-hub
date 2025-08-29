# Debug Programs for Supabase Upsert Error

This directory contains temporary debug programs to isolate and debug the Supabase upsert error occurring in the `universal_contract_queue_data_pull` workflow.

## Problem Description

The `universal_contract_queue_data_pull` workflow is failing at the Supabase upsert step. Everything else works correctly, but the database update operation is encountering an error.

## Debug Programs

### 1. `debug_workflow_upsert.py` (Recommended)
This program replicates the **exact** upsert step from the workflow to isolate the specific error.

**Features:**
- Uses the same Supabase client initialization
- Queries the same data from `universal_contract_queue`
- Prepares data in the exact same format
- Executes the upsert with identical parameters
- Tests individual upsert calls to isolate the issue
- Provides detailed error logging and tracebacks

### 2. `debug_upsert.py` (Comprehensive)
This program provides a comprehensive test of the Supabase upsert functionality.

**Features:**
- Tests basic Supabase connection
- Tests with sample data
- Tests with real data from the database
- Validates table schema
- Tests individual upsert operations
- Comprehensive error reporting

## How to Use

### Option 1: Run the Shell Script (Recommended)
```bash
cd etl/
./run_debug.sh
```

The shell script will:
- Check for required packages
- Activate the virtual environment if available
- Run the debug program
- Provide clear output

### Option 2: Run Directly with Python
```bash
cd etl/

# Activate virtual environment (if available)
source venv/bin/activate

# Run the focused debug program
python3 debug_workflow_upsert.py

# Or run the comprehensive debug program
python3 debug_upsert.py
```

## What to Look For

The debug programs will output detailed information about:

1. **Supabase Connection**: Whether the client initializes successfully
2. **Data Structure**: The exact data being prepared for upload
3. **Upsert Parameters**: The exact parameters being passed to the operation
4. **Error Details**: Specific error messages, codes, and tracebacks
5. **Individual Operations**: Results of testing individual upsert calls

## Expected Output

### Successful Run
```
✅ Supabase client initialized
✅ Connection test successful
✅ Database upload completed: X records
```

### Error Run
```
❌ Database upload failed: [specific error message]
❌ Individual upsert X failed: [specific error details]
```

## Common Issues to Check

1. **Environment Variables**: Ensure `VITE_SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` are set
2. **Table Schema**: Verify that `rfq_index_extract` table has the required fields
3. **Data Types**: Check if the data types match the table schema
4. **Permissions**: Ensure the service role has upsert permissions on the table
5. **Key Fields**: Verify that `solicitation_number` and `national_stock_number` exist and are unique

## After Debugging

Once you identify the specific error:

1. **Note the exact error message** and any error codes
2. **Check the data structure** being passed to the upsert
3. **Verify table schema** matches the expected data
4. **Test with a simple record** to isolate the issue
5. **Check Supabase logs** for additional error details

## Cleanup

After debugging is complete, you can remove these temporary files:
```bash
rm debug_workflow_upsert.py
rm debug_upsert.py
rm run_debug.sh
rm DEBUG_README.md
```

## Troubleshooting

### Import Errors
If you get import errors, ensure you're running from the `etl/` directory and the virtual environment is activated.

### Connection Errors
If Supabase connection fails, check:
- Environment variables are set correctly
- Network connectivity to Supabase
- Service role key permissions

### Permission Errors
If you get permission errors during upsert, verify:
- The service role has `INSERT` and `UPDATE` permissions on `rfq_index_extract`
- The key fields are properly configured for conflict resolution
