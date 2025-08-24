# Database Schema and Workflow Changes Summary

## Overview
This document summarizes the changes made to implement the new `cde_g` field logic and the new `closed` field for solicitations.

## Changes Made

### 1. Database Schema Updates

#### `rfq_index_extract` Table
- **Added `cde_g` field**: Changed from boolean to text field in `universal_contract_queue` to text field in `rfq_index_extract`
  - Type: `string | null`
  - Purpose: Stores the actual AMSC code value (e.g., 'G', 'A', 'B', etc.)
  - Default: `NULL` (indicating AMSC code has not been extracted yet)

- **Added `closed` field**: New boolean field
  - Type: `boolean | null`
  - Purpose: Indicates whether a solicitation is closed
  - Values:
    - `NULL`: Unknown status (default)
    - `FALSE`: Known to be open
    - `TRUE`: Known to be closed

#### `universal_contract_queue` Table
- **Removed `cde_g` field**: This field is no longer used and has been moved to `rfq_index_extract`

### 2. ETL Workflow Updates

#### `extract_nsn_amsc.py` Workflow
- **Updated return type**: Changed from `(success: bool, is_g_level: bool)` to `(success: bool, amsc_code: str)`
- **Updated logic**: Now stores the actual AMSC code value instead of just a boolean
- **Updated target table**: Now updates `rfq_index_extract.cde_g` instead of `universal_contract_queue.cde_g`

#### `supabase_uploader.py`
- **Added `update_rfq_amsc()` method**: New method to update `rfq_index_extract.cde_g` with actual AMSC code
- **Updated `update_contract_amsc()` method**: Now delegates to `update_rfq_amsc()` for backward compatibility
  - Converts boolean input to AMSC code string ('G' for true, 'N' for false)

### 3. Frontend UI Updates

#### Database Hooks (`use-database.ts`)
- **Updated `useContractQueue`**: Now includes `cde_g` and `closed` fields from `rfq_index_extract`
- **Data transformation**: Properly maps the new fields to the contract data structure

#### Kanban Board (`KanbanBoard.tsx`)
- **AMSC Status Indicator**: Updated to show actual AMSC code value instead of just "G-Level/Non-G"
  - Green dot for 'G' codes, blue dot for other codes
  - Displays the actual code value (e.g., "AMSC: G", "AMSC: A")
- **Closed Status Indicator**: Added new indicator for closed solicitations
  - Red dot with "Closed" label when `closed === true`

#### Contract Detail (`ContractDetail.tsx`)
- **Added AMSC Code field**: Shows the extracted AMSC code value or "Not extracted" if NULL
- **Added Solicitation Status field**: Shows closed/open/unknown status with appropriate badge colors
  - Red badge for closed
  - Secondary badge for open
  - Outline badge for unknown

#### Scouting Page (`Scouting.tsx`)
- **Added AMSC column**: Shows AMSC code with appropriate badge styling
  - Default badge for 'G' codes
  - Secondary badge for other codes
  - "Not extracted" text for NULL values
- **Added Status column**: Shows solicitation status (Closed/Open/Unknown) with appropriate badge colors

### 4. Backward Compatibility

- **Legacy support**: The old `update_contract_amsc()` method still works but now delegates to the new logic
- **Data migration**: Existing contracts will show "Not extracted" for AMSC until the workflow is run
- **UI fallbacks**: All UI components handle NULL values gracefully

## Migration Notes

### For Existing Data
- Existing contracts in `universal_contract_queue` will no longer have AMSC information displayed
- The AMSC extraction workflow must be re-run for existing contracts to populate the new `cde_g` field
- The `closed` field will be NULL for all existing records until manually updated

### For New Workflows
- AMSC extraction now stores the actual code value instead of just a boolean
- The workflow can be enhanced in the future to also determine and set the `closed` status
- Both fields are now stored in the `rfq_index_extract` table for better data organization

## Testing Recommendations

1. **Test AMSC extraction workflow** with a new contract to ensure it populates the `cde_g` field correctly
2. **Verify UI displays** show the new fields appropriately in all components
3. **Test backward compatibility** with existing contracts that don't have the new fields
4. **Verify database queries** work correctly with the new field structure

## Future Enhancements

1. **Automated closed status detection**: Could be added to the AMSC extraction workflow
2. **AMSC code validation**: Could add validation to ensure only valid AMSC codes are stored
3. **Bulk updates**: Could add workflows to update multiple contracts at once
4. **Historical tracking**: Could add audit trails for when AMSC codes or closed status change
