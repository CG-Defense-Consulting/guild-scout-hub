# Partner Hub - Enhanced Contract Management

## Overview

The Partner Hub has been enhanced with a new data table interface that allows partners to view and manage contracts that have been sent to them for review and action. This replaces the previous card-based interface with a more robust table view similar to the Scouting page.

## New Features

### 1. Partner Queue Table (`partner_queue`)

A new table has been added to the database schema to track contracts sent to partners:

```sql
partner_queue {
  id: string (foreign key to universal_contract_queue.id)
  partner: string (official partner name)
  submitted_at: string (timestamp when contract was sent to partner)
  submitted_by: string (user who sent the contract)
  partner_type: 'MFG' | 'LOG' | 'SUP' (partner category)
}
```

### 2. Partner Data Table Component

The new `PartnerDataTable` component provides:
- **Searchable table** with all partner queue contracts
- **Sortable columns** for easy data organization
- **Clickable rows** that open detailed contract views
- **Responsive design** that works on all devices
- **Partner type badges** with color coding (MFG=Blue, LOG=Green, SUP=Purple)

### 3. Contract Detail Modal

When a partner clicks on a row, they see a comprehensive modal with:
- **Contract overview** (ID, partner type)
- **Contract details** (part number, description, current stage)
- **Timeline information** (creation date, submission date)
- **Partner information** (name, submitted by)
- **Action buttons** (View Full Contract, Mark as Reviewed, Request Quote)

## Components

### PartnerDataTable.tsx
- Main table component for displaying partner queue data
- Integrates with the existing DataTable component
- Handles row selection and detail modal display

### PartnerContractDetail.tsx
- Modal component for detailed contract information
- Shows comprehensive contract data in organized sections
- Provides action buttons for partner interactions

## Database Integration

### New Hook: usePartnerQueue
```typescript
const { data: partnerQueue, isLoading } = usePartnerQueue(partnerName?);
```

This hook:
- Fetches data from the `partner_queue` table
- Joins with `universal_contract_queue` for contract details
- Supports filtering by partner name
- Uses React Query for caching and state management

## Usage

### For Partners
1. Navigate to the Partner Hub page
2. View all contracts assigned to them in a searchable table
3. Click on any row to see detailed contract information
4. Use action buttons to interact with contracts

### For CGDC Users
1. The Hub page shows the existing pricing queue interface
2. Partners see the new data table interface
3. Both interfaces coexist based on user role

## Styling

The new components use the existing design system:
- **Tailwind CSS** for consistent styling
- **Shadcn/ui components** for UI elements
- **Lucide React icons** for visual elements
- **Responsive design** that works on all screen sizes

## Future Enhancements

Potential improvements for the Partner Hub:
1. **Status tracking** - Add workflow status to contracts
2. **Notification system** - Alert partners of new assignments
3. **Bulk actions** - Allow multiple contract selection
4. **Export functionality** - Download contract data
5. **Integration** - Connect with external partner systems

## Technical Notes

- Built with TypeScript for type safety
- Uses React Query for data fetching and caching
- Follows existing component patterns and conventions
- Fully integrated with the existing authentication system
- Responsive design that works on mobile and desktop

## Database Schema

The `partner_queue` table has the following relationships:
- `id` → `universal_contract_queue.id` (one-to-one)
- This allows access to all contract details while maintaining data integrity

## Security

- Partners can only see contracts assigned to them
- CGDC users can see all partner assignments
- Authentication and role-based access control enforced
- Data is properly sanitized and validated
