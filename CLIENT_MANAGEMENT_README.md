# Client Management System

A comprehensive client management system built for the Bookngon AI project, designed to handle client information, preferences, and history tracking for service-based businesses.

## Features

### Core Models

1. **Client** - Comprehensive client information with contact details, address, and preferences
2. **ClientHistory** - Track all changes and actions performed on client records
3. **ClientPreference** - Store client preferences for services, staff, communication, etc.

### Key Features

- **Complete Client Profiles**: Full contact information, address, emergency contacts
- **Preference Management**: Store client preferences for services, staff, communication methods
- **History Tracking**: Automatic tracking of all client changes and actions
- **VIP Status**: Mark important clients with VIP status
- **Business Association**: Link clients to their primary business
- **Advanced Search**: Search clients by name, email, phone, location
- **Statistics & Analytics**: Comprehensive reporting and analytics
- **Data Management**: Tools for cleaning up and managing client data

## API Endpoints

### Clients
- `GET /api/client/clients/` - List all clients
- `POST /api/client/clients/` - Create new client
- `GET /api/client/clients/{id}/` - Get client details
- `PUT/PATCH /api/client/clients/{id}/` - Update client
- `DELETE /api/client/clients/{id}/` - Delete client
- `GET /api/client/clients/{id}/history/` - Get client history
- `GET/POST /api/client/clients/{id}/preferences/` - Manage client preferences
- `POST /api/client/clients/{id}/add_preference/` - Add new preference
- `POST /api/client/clients/{id}/toggle_vip/` - Toggle VIP status
- `POST /api/client/clients/{id}/toggle_active/` - Toggle active status
- `GET /api/client/clients/stats/` - Get client statistics
- `GET /api/client/clients/search/` - Advanced client search

### Client Preferences
- `GET /api/client/preferences/` - List all preferences
- `POST /api/client/preferences/` - Create new preference
- `GET /api/client/preferences/{id}/` - Get preference details
- `PUT/PATCH /api/client/preferences/{id}/` - Update preference
- `DELETE /api/client/preferences/{id}/` - Delete preference

### Client History
- `GET /api/client/history/` - List all history entries
- `GET /api/client/history/{id}/` - Get history entry details

## Model Structure

### Client Model
```python
class Client(models.Model):
    # Personal Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    
    # Address Information
    address_line1 = models.CharField(max_length=255, blank=True, null=True)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state_province = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    
    # Emergency Contact
    emergency_contact_name = models.CharField(max_length=200, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True, null=True)
    emergency_contact_relation = models.CharField(max_length=100, blank=True, null=True)
    
    # Preferences and Status
    preferred_contact_method = models.CharField(max_length=20, choices=[...])
    notes = models.TextField(blank=True, null=True)
    medical_notes = models.TextField(blank=True, null=True)
    primary_business = models.ForeignKey('business.Business', ...)
    is_active = models.BooleanField(default=True)
    is_vip = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### ClientHistory Model
```python
class ClientHistory(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    action = models.CharField(max_length=50)
    description = models.TextField()
    changed_by = models.ForeignKey('staff.Staff', ...)
    changed_at = models.DateTimeField(auto_now_add=True)
```

### ClientPreference Model
```python
class ClientPreference(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    preference_type = models.CharField(max_length=50, choices=[...])
    preference_key = models.CharField(max_length=100)
    preference_value = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

## Management Commands

### Create Sample Clients
```bash
python manage.py create_sample_clients --count 50 --business-id 1
```

### Client Statistics
```bash
python manage.py client_stats --detailed --business-id 1
```

### Cleanup Clients
```bash
python manage.py cleanup_clients --dry-run --remove-duplicates --remove-inactive
```

## Admin Interface

The client management system includes a comprehensive Django admin interface with:

- **Client List View**: Display clients with search and filtering
- **Client Detail View**: Complete client information with inline preferences and history
- **Bulk Actions**: Mark clients as VIP, activate/deactivate clients
- **History Tracking**: View all changes made to client records
- **Preference Management**: Manage client preferences inline

## Integration

### With Appointment System
- Clients are referenced in appointments via `client.Client` foreign key
- Client history tracks appointment-related changes
- Client preferences can influence appointment scheduling

### With Business System
- Clients can be associated with a primary business
- Business-specific client filtering and management
- Multi-business support for client operations

### With Staff System
- Staff members can be tracked as the user who made changes
- Client preferences can specify preferred staff members
- Staff can view and manage clients within their business

## Data Migration

The client management system has been refactored from the appointment app. The migration process:

1. **New Client App**: Created dedicated client management app
2. **Enhanced Models**: Expanded client model with additional fields
3. **History Tracking**: Added automatic change tracking
4. **Preference System**: Added flexible preference management
5. **Updated References**: Updated all foreign key references to use new client app

## Usage Examples

### Creating a Client
```python
from client.models import Client

client = Client.objects.create(
    first_name="John",
    last_name="Doe",
    email="john.doe@example.com",
    phone="+1234567890",
    primary_business=business,
    preferred_contact_method="email"
)
```

### Adding Client Preferences
```python
from client.models import ClientPreference

ClientPreference.objects.create(
    client=client,
    preference_type="service",
    preference_key="preferred_service_type",
    preference_value="Haircut"
)
```

### Viewing Client History
```python
history = client.history.all()
for entry in history:
    print(f"{entry.changed_at}: {entry.action} - {entry.description}")
```

## Best Practices

1. **Data Validation**: Always validate email and phone uniqueness
2. **History Tracking**: Use the provided serializers to ensure history is tracked
3. **Preference Management**: Use consistent preference types and keys
4. **Business Association**: Always associate clients with appropriate businesses
5. **Data Cleanup**: Regularly run cleanup commands to maintain data quality

## Future Enhancements

- **Client Communication**: Integration with notification system
- **Client Analytics**: Advanced reporting and insights
- **Client Segmentation**: Group clients by various criteria
- **Import/Export**: Bulk client data management
- **Client Portal**: Self-service client management interface
