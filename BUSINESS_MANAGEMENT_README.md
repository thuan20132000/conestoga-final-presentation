# Business Management System

A comprehensive Django-based business management system designed to handle various types of service businesses including hair salons, nail salons, spas, dental clinics, and more.

## Features

### Core Models

1. **BusinessType** - Predefined business categories (Hair Salon, Nail Salon, Spa, Dental Clinic, etc.)
2. **Business** - Main business entity with contact information, location, and status
3. **ServiceCategory** - Organize services into logical groups
4. **Service** - Individual services offered by the business
5. **Staff** - Staff members with roles and contact information
6. **StaffService** - Many-to-many relationship between staff and services they can provide
7. **OperatingHours** - Business hours for each day of the week
8. **BusinessSettings** - Configurable settings for booking, notifications, and payments

### API Endpoints

The system provides a comprehensive REST API with the following endpoints:

#### Business Types
- `GET /api/business/business-types/` - List all business types
- `GET /api/business/business-types/{id}/` - Get specific business type

#### Businesses
- `GET /api/business/businesses/` - List all businesses (with filtering and search)
- `POST /api/business/businesses/` - Create new business
- `GET /api/business/businesses/{id}/` - Get business details
- `PUT/PATCH /api/business/businesses/{id}/` - Update business
- `DELETE /api/business/businesses/{id}/` - Delete business
- `GET /api/business/businesses/{id}/services/` - Get business services
- `GET /api/business/businesses/{id}/staff/` - Get business staff
- `GET /api/business/businesses/{id}/operating_hours/` - Get operating hours
- `GET/PUT/PATCH /api/business/businesses/{id}/settings/` - Manage business settings

#### Service Categories
- `GET /api/business/service-categories/` - List service categories
- `POST /api/business/service-categories/` - Create service category
- `GET /api/business/service-categories/{id}/` - Get service category
- `PUT/PATCH /api/business/service-categories/{id}/` - Update service category
- `DELETE /api/business/service-categories/{id}/` - Delete service category

#### Services
- `GET /api/business/services/` - List services
- `POST /api/business/services/` - Create service
- `GET /api/business/services/{id}/` - Get service
- `PUT/PATCH /api/business/services/{id}/` - Update service
- `DELETE /api/business/services/{id}/` - Delete service
- `GET /api/business/services/by_category/` - Get services grouped by category

#### Staff
- `GET /api/business/staff/` - List staff members
- `POST /api/business/staff/` - Create staff member
- `GET /api/business/staff/{id}/` - Get staff member
- `PUT/PATCH /api/business/staff/{id}/` - Update staff member
- `DELETE /api/business/staff/{id}/` - Delete staff member
- `GET/POST/DELETE /api/business/staff/{id}/services/` - Manage staff services

#### Operating Hours
- `GET /api/business/operating-hours/` - List operating hours
- `POST /api/business/operating-hours/` - Create operating hours
- `GET /api/business/operating-hours/{id}/` - Get operating hours
- `PUT/PATCH /api/business/operating-hours/{id}/` - Update operating hours
- `DELETE /api/business/operating-hours/{id}/` - Delete operating hours

### Filtering and Search

The API supports comprehensive filtering and search capabilities:

- **Business filtering**: by business_type, status, city, state_province, country
- **Service filtering**: by business, category, is_active, requires_staff
- **Staff filtering**: by business, role, is_active
- **Search**: across names, descriptions, addresses, and other text fields
- **Location search**: find businesses by city, state, or address

### Django Admin Interface

The system includes a fully configured Django admin interface with:

- Inline editing for related models
- Organized fieldsets for better UX
- Search and filtering capabilities
- Optimized queries with select_related and prefetch_related

## Sample Data

The system includes management commands to create sample data:

### Create Business Types
```bash
python manage.py create_business_types
```

This creates 10 predefined business types:
- Hair Salon
- Nail Salon
- Spa
- Dental Clinic
- Barbershop
- Beauty Clinic
- Massage Therapy
- Tattoo Studio
- Eyebrow Studio
- Fitness Studio

### Create Sample Businesses
```bash
python manage.py create_sample_businesses
```

This creates 4 complete sample businesses with:
- Complete business information
- Service categories and services
- Staff members
- Operating hours
- Business settings

## Business Types Supported

The system is designed to handle various service-based businesses:

1. **Hair Salon** - Haircuts, coloring, treatments
2. **Nail Salon** - Manicures, pedicures, nail art
3. **Spa** - Massages, facials, wellness treatments
4. **Dental Clinic** - Dental care, cleanings, treatments
5. **Barbershop** - Men's grooming services
6. **Beauty Clinic** - Cosmetic treatments, skincare
7. **Massage Therapy** - Therapeutic massage services
8. **Tattoo Studio** - Tattoo design and application
9. **Eyebrow Studio** - Eyebrow and lash services
10. **Fitness Studio** - Personal training, group classes

## Key Features

### Flexible Service Management
- Organize services into categories
- Set duration, pricing, and capacity
- Assign staff to specific services
- Mark services as active/inactive

### Staff Management
- Multiple roles (Owner, Manager, Stylist, Technician, etc.)
- Link staff to services they can provide
- Track hire dates and employment status
- Store contact information and photos

### Operating Hours
- Set different hours for each day of the week
- Support for break times
- Mark days as closed
- Flexible scheduling options

### Business Settings
- Booking preferences (advance booking limits)
- Time slot configuration
- Notification settings (email/SMS reminders)
- Payment and tax settings
- Online booking controls

### Location Support
- Full address management
- City, state/province, postal code
- Country and timezone support
- Location-based filtering

## Usage Examples

### Get all hair salons in Toronto
```bash
GET /api/business/businesses/?business_type=Hair Salon&city=Toronto
```

### Get services for a specific business
```bash
GET /api/business/businesses/1/services/
```

### Get services grouped by category
```bash
GET /api/business/services/by_category/?business=1
```

### Create a new service
```bash
POST /api/business/services/
{
    "business": 1,
    "category": 1,
    "name": "Highlights",
    "description": "Professional hair highlighting service",
    "duration_minutes": 90,
    "price": 120.00,
    "is_active": true,
    "requires_staff": true,
    "max_capacity": 1
}
```

### Assign a service to staff
```bash
POST /api/business/staff/1/services/
{
    "service_id": 1,
    "is_primary": true
}
```

## Integration with AI Receptionist

This business management system is designed to integrate with the AI receptionist system in the `receptionist` app. The business data can be used to:

- Provide accurate business information to AI
- Enable appointment booking with real service data
- Support staff scheduling and availability
- Manage client interactions with business context

## Future Enhancements

Potential future features could include:

- Appointment scheduling system
- Client management
- Payment processing integration
- Inventory management
- Marketing and promotion tools
- Analytics and reporting
- Multi-location support
- Staff scheduling and availability
- Client reviews and ratings

## Technical Details

- **Framework**: Django 5.2.7
- **API**: Django REST Framework
- **Database**: SQLite (configurable)
- **Image Support**: Pillow for logo and photo uploads
- **Filtering**: django-filter
- **Admin**: Custom Django admin interface

The system is built with scalability in mind and can easily be extended to support additional business types and features as needed.
