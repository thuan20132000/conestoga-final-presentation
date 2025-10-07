# Appointment Management System

A comprehensive appointment management system built for the Bookngon AI project, designed to handle appointment scheduling, client management, and business operations for service-based businesses.

## Features

### Core Models

1. **Client** - Client information and contact details
2. **Appointment** - Main appointment entity with scheduling, pricing, and status tracking
3. **AppointmentStatus** - Configurable appointment statuses (scheduled, confirmed, completed, etc.)
4. **AppointmentReminder** - Track reminder notifications sent to clients
5. **AppointmentConflict** - Detect and manage scheduling conflicts

### Key Features

- **Smart Scheduling**: Automatic conflict detection and staff availability checking
- **Client Management**: Comprehensive client profiles with contact information
- **Status Tracking**: Multiple appointment statuses with visual indicators
- **Payment Tracking**: Built-in payment status and method tracking
- **Reminder System**: Automated reminder notifications (email, SMS, push)
- **Recurring Appointments**: Support for recurring appointment patterns
- **Conflict Resolution**: Automatic detection and manual resolution of scheduling conflicts
- **Statistics & Analytics**: Comprehensive reporting and analytics
- **Multi-business Support**: Each appointment is tied to a specific business

## API Endpoints

### Clients
- `GET /api/appointment/clients/` - List all clients
- `POST /api/appointment/clients/` - Create new client
- `GET /api/appointment/clients/{id}/` - Get client details
- `PUT/PATCH /api/appointment/clients/{id}/` - Update client
- `DELETE /api/appointment/clients/{id}/` - Delete client

### Appointments
- `GET /api/appointment/appointments/` - List appointments (with filtering)
- `POST /api/appointment/appointments/` - Create new appointment
- `GET /api/appointment/appointments/{id}/` - Get appointment details
- `PUT/PATCH /api/appointment/appointments/{id}/` - Update appointment
- `DELETE /api/appointment/appointments/{id}/` - Delete appointment

#### Special Appointment Endpoints
- `GET /api/appointment/appointments/today/` - Get today's appointments
- `GET /api/appointment/appointments/upcoming/` - Get upcoming appointments
- `GET /api/appointment/appointments/by_staff/` - Get appointments by staff member
- `GET /api/appointment/appointments/by_client/` - Get appointments by client
- `POST /api/appointment/appointments/check_availability/` - Check availability
- `POST /api/appointment/appointments/{id}/confirm/` - Confirm appointment
- `POST /api/appointment/appointments/{id}/cancel/` - Cancel appointment
- `POST /api/appointment/appointments/{id}/complete/` - Mark as completed
- `GET /api/appointment/appointments/stats/` - Get appointment statistics

### Appointment Statuses
- `GET /api/appointment/statuses/` - List all appointment statuses
- `POST /api/appointment/statuses/` - Create new status
- `GET /api/appointment/statuses/{id}/` - Get status details
- `PUT/PATCH /api/appointment/statuses/{id}/` - Update status
- `DELETE /api/appointment/statuses/{id}/` - Delete status

### Reminders
- `GET /api/appointment/reminders/` - List appointment reminders
- `POST /api/appointment/reminders/` - Create new reminder
- `GET /api/appointment/reminders/{id}/` - Get reminder details
- `PUT/PATCH /api/appointment/reminders/{id}/` - Update reminder
- `DELETE /api/appointment/reminders/{id}/` - Delete reminder

### Conflicts
- `GET /api/appointment/conflicts/` - List appointment conflicts
- `POST /api/appointment/conflicts/` - Create conflict record
- `GET /api/appointment/conflicts/{id}/` - Get conflict details
- `POST /api/appointment/conflicts/{id}/resolve/` - Resolve conflict

## Filtering and Search

### Appointment Filtering
- `business` - Filter by business ID
- `client` - Filter by client ID
- `service` - Filter by service ID
- `staff` - Filter by staff member ID
- `status` - Filter by status name
- `appointment_date` - Filter by appointment date
- `start_date` - Filter appointments from date
- `end_date` - Filter appointments to date
- `is_paid` - Filter by payment status
- `booking_source` - Filter by booking source
- `is_recurring` - Filter recurring appointments

### Search Fields
- Client name (first_name, last_name)
- Service name
- Staff name (first_name, last_name)
- Appointment notes

### Ordering
- `appointment_date` - Order by appointment date
- `start_time` - Order by start time
- `created_at` - Order by creation date
- `total_price` - Order by total price

## Usage Examples

### Create a New Appointment

```json
POST /api/appointment/appointments/
{
    "business": 1,
    "client": 1,
    "service": 1,
    "staff": 1,
    "appointment_date": "2024-01-15",
    "start_time": "10:00:00",
    "end_time": "11:00:00",
    "duration_minutes": 60,
    "notes": "First time client",
    "service_price": "75.00",
    "booking_source": "online"
}
```

### Check Availability

```json
POST /api/appointment/appointments/check_availability/
{
    "business": 1,
    "service": 1,
    "appointment_date": "2024-01-15",
    "staff": 1
}
```

### Get Appointment Statistics

```json
GET /api/appointment/appointments/stats/?business=1
```

Response:
```json
{
    "total_appointments": 150,
    "completed_appointments": 120,
    "cancelled_appointments": 15,
    "upcoming_appointments": 25,
    "today_appointments": 8,
    "revenue_today": "600.00",
    "revenue_this_month": "15000.00",
    "average_appointment_value": "85.50",
    "no_show_rate": "8.5"
}
```

## Integration with Existing Systems

### Business Integration
- Appointments are tied to specific businesses
- Uses business operating hours for availability checking
- Respects business settings for booking rules

### Service Integration
- Links to existing service catalog
- Uses service duration and pricing
- Supports staff-service relationships

### Staff Integration
- Assigns appointments to specific staff members
- Checks staff availability and working hours
- Tracks staff performance and workload

### Notification Integration
- Integrates with existing notification system
- Supports email, SMS, and push notifications
- Automated reminder scheduling

## Database Schema

### Key Relationships
- `Appointment` → `Business` (Many-to-One)
- `Appointment` → `Client` (Many-to-One)
- `Appointment` → `Service` (Many-to-One)
- `Appointment` → `Staff` (Many-to-One)
- `Appointment` → `AppointmentStatus` (Many-to-One)
- `AppointmentReminder` → `Appointment` (Many-to-One)
- `AppointmentConflict` → `Appointment` (Many-to-One, self-referencing)

### Indexes
- Composite index on `(business, appointment_date, start_time)` for quick availability checks
- Index on `(staff, appointment_date)` for staff schedule queries
- Index on `client` for client appointment history
- Index on `appointment_date` for date-based filtering

## Admin Interface

The Django admin interface provides comprehensive management capabilities:

- **Client Management**: View and edit client information
- **Appointment Management**: Full CRUD operations with inline reminders and conflicts
- **Status Management**: Configure appointment statuses with colors
- **Reminder Tracking**: Monitor reminder delivery status
- **Conflict Resolution**: View and resolve scheduling conflicts

## Security and Permissions

- All endpoints require proper authentication
- Business-based access control (users can only access their business appointments)
- Staff-based permissions for appointment management
- Admin-only access for system-wide operations

## Performance Considerations

- Optimized database queries with select_related and prefetch_related
- Efficient indexing for common query patterns
- Pagination support for large datasets
- Caching for frequently accessed data

## Future Enhancements

- Real-time availability updates
- Advanced conflict resolution algorithms
- Integration with external calendar systems
- Automated rescheduling suggestions
- Client portal for self-service booking
- Advanced analytics and reporting
- Mobile app support
- Payment gateway integration
