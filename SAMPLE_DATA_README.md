# Sample Data for Receptionist App

This document explains how to create and use sample data for the receptionist AI application.

## Overview

The sample data system creates realistic test data for all models in the receptionist app:
- **Business**: Salon/company information
- **AIConfiguration**: AI behavior settings for each business
- **CallSession**: Phone call records
- **ConversationMessage**: Individual messages during calls
- **Intent**: Detected user intents (booking, inquiry, etc.)
- **AudioRecording**: Call audio file references
- **SystemLog**: System events and debugging information

## Quick Start

### Option 1: Using the simple script
```bash
cd /path/to/bookngon-ai
python create_sample_data.py
```

### Option 2: Using Django management command
```bash
cd /path/to/bookngon-ai
python manage.py create_sample_data
```

## Command Options

The `create_sample_data` management command supports several options:

```bash
# Create default sample data (3 businesses, 5 calls each)
python manage.py create_sample_data

# Create more businesses and calls
python manage.py create_sample_data --businesses 5 --calls-per-business 10

# Clear existing data before creating new data
python manage.py create_sample_data --clear-existing

# Combine options
python manage.py create_sample_data --businesses 2 --calls-per-business 8 --clear-existing
```

### Parameters

- `--businesses N`: Number of businesses to create (default: 3)
- `--calls-per-business N`: Number of calls per business (default: 5)
- `--clear-existing`: Clear all existing data before creating new data

## Sample Data Details

### Businesses Created
1. **Blissful Beauty Salon** - AI: Sarah
2. **Golden Nails & Spa** - AI: Maya  
3. **Style Studio Hair Salon** - AI: Alex

### Call Scenarios
Each call includes one of these realistic scenarios:

1. **Booking Appointment**
   - Customer books a haircut for next Tuesday at 2 PM
   - Includes contact information collection
   - Duration: 3-8 minutes

2. **Service Inquiry**
   - Customer asks about hours and services
   - AI provides information about hair coloring
   - Duration: 2-5 minutes

3. **Appointment Cancellation**
   - Customer cancels existing appointment
   - AI confirms cancellation details
   - Duration: 1.5-4 minutes

4. **Failed Call**
   - Audio quality issues
   - Customer cannot hear AI properly
   - Duration: 30 seconds - 2 minutes

### Data Relationships
- Each business has one AI configuration
- Each call belongs to one business
- Each call has multiple conversation messages
- Each call can have multiple detected intents
- Successful calls have audio recordings
- All calls have system logs for debugging

## Viewing the Data

### Django Admin Interface
1. Start the development server: `python manage.py runserver`
2. Navigate to `http://localhost:8000/admin/`
3. Login with superuser credentials
4. Browse the receptionist app models

### API Endpoints
If you have API views configured, you can query the data via REST endpoints.

### Database Queries
```python
# In Django shell: python manage.py shell
from receptionist.models import Business, CallSession

# Get all businesses
businesses = Business.objects.all()

# Get calls for a specific business
salon = Business.objects.get(name='Blissful Beauty Salon')
calls = CallSession.objects.filter(business=salon)

# Get completed calls
completed_calls = CallSession.objects.filter(status='completed')
```

## Customization

### Adding New Business Types
Edit the `businesses_data` list in `/receptionist/management/commands/create_sample_data.py`:

```python
businesses_data = [
    {
        'name': 'Your Salon Name',
        'phone_number': '+1-555-XXXX',
        'address': 'Your Address',
        'timezone': 'America/Toronto',
        'ai_config': {
            'ai_name': 'Your AI Name',
            'greeting_message': 'Your greeting',
            # ... other config
        }
    },
    # ... more businesses
]
```

### Adding New Call Scenarios
Add new scenarios to the `call_scenarios` list in the same file:

```python
{
    'type': 'your_scenario',
    'messages': [
        ('user', 'Customer message'),
        ('assistant', 'AI response'),
        # ... more messages
    ],
    'intents': [
        ('intent_name', 0.95, {'data': 'value'}),
    ],
    'duration': 300,  # seconds
    'status': 'completed'
}
```

## Troubleshooting

### Common Issues

1. **Database not migrated**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

2. **Permission errors**
   - Make sure you're running from the project root directory
   - Ensure Django can access the database

3. **Import errors**
   - Make sure the virtual environment is activated
   - Install all requirements: `pip install -r requirements.txt`

### Clearing All Data
```bash
python manage.py create_sample_data --clear-existing --businesses 0
```

This will clear all existing data without creating new data.

## Integration with Tests

The sample data can be used in your test suite:

```python
from django.test import TestCase
from django.core.management import call_command

class ReceptionistTestCase(TestCase):
    def setUp(self):
        call_command('create_sample_data', businesses=1, calls_per_business=2)
    
    def test_business_creation(self):
        from receptionist.models import Business
        self.assertEqual(Business.objects.count(), 1)
```

## Next Steps

After creating sample data, you can:

1. **Test API endpoints** with realistic data
2. **Develop frontend interfaces** using the sample data
3. **Test AI integrations** with various call scenarios
4. **Performance testing** with larger datasets
5. **Demo the application** to stakeholders

For production use, remember to:
- Use real business data instead of sample data
- Implement proper data validation
- Add data migration scripts for schema changes
- Set up proper backup and recovery procedures
