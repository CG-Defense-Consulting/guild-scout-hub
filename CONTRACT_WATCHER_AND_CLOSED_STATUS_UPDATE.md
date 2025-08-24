# Contract Watcher and Closed Status Update

## Overview
This update makes the contract watcher hidden by default and enhances the NSN AMSC workflow to automatically detect and update the `closed` field based on DIBBS responses.

## Changes Made

### 1. **Contract Watcher Hidden by Default**
- **File**: `src/pages/Tracker.tsx`
- **Change**: Changed `useState(false)` for `showWatcher` instead of `useState(true)`
- **Result**: Users must manually click "Show Watcher" to see the contract watcher panel
- **Benefit**: Cleaner default interface, watcher available when needed

### 2. **Enhanced NSN AMSC Workflow**
- **File**: `etl/workflows/adhoc/extract_nsn_amsc.py`
- **Enhancement**: Now automatically detects closed solicitations and updates the `closed` field
- **Return Value**: Updated from `(success, amsc_code)` to `(success, amsc_code, is_closed)`

### 3. **New Supabase Uploader Method**
- **File**: `etl/core/uploaders/supabase_uploader.py`
- **New Method**: `update_rfq_closed_status(contract_id, is_closed)`
- **Purpose**: Updates the `closed` field in the `rfq_index_extract` table

### 4. **Enhanced DibbsScraper**
- **File**: `etl/core/scrapers/dibbs_scraper.py`
- **New Method**: `check_nsn_closed_status(nsn)`
- **Logic**: Detects the specific HTML message indicating no open RFQ solicitations

## Technical Implementation

### Closed Status Detection Logic

The system now looks for this specific HTML text pattern in the DIBBS response:
```html
"No record of National Stock Number: {NSN} with open DIBBS Request For Quotes (RFQ) solicitations."
```

**When this message is found:**
- `closed` field is set to `True`
- Indicates the solicitation is closed (no open RFQs)

**When this message is NOT found:**
- `closed` field is set to `False`
- Indicates the solicitation may have open RFQs

### Workflow Sequence

1. **NSN AMSC Workflow Starts**
2. **Check Closed Status**: Navigate to NSN details page and check for "no open RFQ" message
3. **Update Closed Field**: Set `closed` field based on detection result
4. **Extract AMSC Code**: Continue with existing AMSC extraction logic
5. **Update AMSC Field**: Set `cde_g` field with extracted code

### Database Updates

The workflow now updates two fields in `rfq_index_extract`:
- `cde_g`: The extracted AMSC code
- `closed`: Whether the solicitation is closed (based on DIBBS response)

## User Experience Changes

### Default Interface
- **Before**: Contract watcher panel visible by default
- **After**: Contract watcher panel hidden by default
- **Access**: Users can click "Show Watcher" button to reveal the panel

### Automatic Status Updates
- **Before**: `closed` field had to be manually updated
- **After**: `closed` field automatically updated when NSN workflow runs
- **Benefit**: More accurate and up-to-date solicitation status

## Code Examples

### New Workflow Return Value
```python
# Before
success, amsc_code = extract_nsn_amsc(contract_id, nsn)

# After
success, amsc_code, is_closed = extract_nsn_amsc(contract_id, nsn)
```

### Closed Status Detection
```python
def check_nsn_closed_status(self, nsn: str) -> Optional[bool]:
    # Navigate to NSN details page
    nsn_url = f"https://www.dibbs.bsm.dla.mil//rfq/rfqnsn.aspx?value={nsn}"
    
    # Handle consent page
    if not self._handle_consent_page(nsn_url):
        return None
    
    # Check page source for specific message
    page_source = self.driver.page_source
    no_open_message = f"No record of National Stock Number: {nsn} with open DIBBS Request For Quotes (RFQ) solicitations."
    
    if no_open_message in page_source:
        return True   # Closed - no open solicitations
    else:
        return False  # Open - solicitations may exist
```

### Database Update
```python
# Update closed status
if is_closed:
    uploader.update_rfq_closed_status(contract_id, True)
else:
    uploader.update_rfq_closed_status(contract_id, False)

# Update AMSC code
uploader.update_rfq_amsc(contract_id, amsc_code)
```

## Benefits

### 1. **Cleaner Default Interface**
- Contract watcher doesn't clutter the main interface
- Users can focus on contract management first
- Watcher available when automation is needed

### 2. **Automatic Status Detection**
- No manual intervention required for closed status
- Real-time updates based on DIBBS responses
- More accurate contract status tracking

### 3. **Improved Data Quality**
- `closed` field automatically populated
- Consistent with actual DIBBS status
- Better reporting and analytics

### 4. **Enhanced Workflow Intelligence**
- Workflow now handles both AMSC extraction and status detection
- Single workflow execution updates multiple fields
- More efficient processing

## Testing Recommendations

### Test Cases
1. **NSN with Open Solicitations**
   - Expected: `closed = False`
   - Verify: No "no open RFQ" message found

2. **NSN with No Open Solicitations**
   - Expected: `closed = True`
   - Verify: "no open RFQ" message found

3. **Workflow Execution**
   - Verify: Both `cde_g` and `closed` fields updated
   - Check: Database reflects correct values

4. **UI Updates**
   - Verify: Contract watcher hidden by default
   - Check: Can be shown/hidden with button
   - Confirm: Closed status indicators work correctly

### Validation Steps
1. Run NSN AMSC workflow on test contracts
2. Check database for updated `closed` values
3. Verify UI displays correct closed status colors
4. Test contract watcher show/hide functionality

## Future Enhancements

### Potential Improvements
1. **Batch Processing**: Update multiple contracts simultaneously
2. **Scheduled Updates**: Regular status checks for existing contracts
3. **Status History**: Track when and why status changed
4. **Notification System**: Alert users to status changes

### Advanced Features
1. **Status Validation**: Cross-reference with other data sources
2. **Trend Analysis**: Track closure patterns over time
3. **Predictive Analytics**: Estimate likelihood of future closures
4. **Integration APIs**: Webhook notifications for status changes

## Conclusion

These updates significantly improve the contract management system by:
- Providing a cleaner, less cluttered default interface
- Automatically detecting and updating solicitation status
- Ensuring data accuracy through automated DIBBS integration
- Maintaining the existing workflow while adding new capabilities

The system now provides more accurate and up-to-date information about contract status, reducing manual work and improving data quality for better decision-making.
