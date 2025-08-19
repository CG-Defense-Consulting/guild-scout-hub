# Guild - Defense Contracting Platform

A modern web application for defense contracting workflow management, built with React, TypeScript, Tailwind CSS, and Supabase.

## Features

### Authentication & Authorization
- Supabase Auth integration
- Role-based access control (CGDC and PARTNER roles)
- Protected routes based on user permissions

### Contract Scouting (/scouting)
- Browse RFQ opportunities from `rfq_index_extract` table
- Advanced filtering by NSN, description, quantity, and dates
- Historical pricing intelligence with charts and statistics
- Add contracts to processing queue
- CGDC users only

### Contract Tracker (/tracker)
- Kanban-style contract lifecycle management
- Drag-and-drop status updates across 8 lifecycle stages
- Detailed contract views with tabbed interface
- Document management and automation triggers
- Partner assignment workflow
- CGDC users only

### Partner Hub (/hub)
- Partner-specific assignment dashboard
- Mobile-first design with status indicators
- CGDC users see "Super View" with filtering options
- Partner users see only their assigned work

## Setup Instructions

1. **Install dependencies**: `npm install`
2. **Set up user roles** in Supabase `user_page_entitlements` table
3. **Start development**: `npm run dev`
4. **Visit `/auth`** to create accounts and sign in

The Guild app is now fully functional with authentication, role-based routing, and all three main pages connected to your Supabase backend.