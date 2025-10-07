#!/usr/bin/env python
"""
Script to clear or create sample data for the receptionist app.
Use with caution - clearing will delete all data!
"""

import os
import sys
import django
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
django.setup()

from django.core.management import call_command

from receptionist.models import (
    Business, AIConfiguration, CallSession, ConversationMessage, 
    Intent, AudioRecording, SystemLog
)

def clear_sample_data():
    """Clear all sample data."""
    print("⚠️  WARNING: This will delete ALL data in the receptionist app!")
    
    # Get current counts
    business_count = Business.objects.count()
    call_count = CallSession.objects.count()
    message_count = ConversationMessage.objects.count()
    
    if business_count == 0:
        print("✅ No data found to clear.")
        return
    
    print(f"\nCurrent data:")
    print(f"  • Businesses: {business_count}")
    print(f"  • Calls: {call_count}")
    print(f"  • Messages: {message_count}")
    
    # Confirmation
    response = input(f"\nAre you sure you want to delete all this data? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("❌ Operation cancelled.")
        return
    
    print("\n🗑️  Clearing data...")
    
    # Delete in correct order due to foreign key constraints
    deleted_counts = {
        'system_logs': SystemLog.objects.count(),
        'audio_recordings': AudioRecording.objects.count(),
        'intents': Intent.objects.count(),
        'conversation_messages': ConversationMessage.objects.count(),
        'call_sessions': CallSession.objects.count(),
        'ai_configurations': AIConfiguration.objects.count(),
        'businesses': Business.objects.count(),
    }
    
    SystemLog.objects.all().delete()
    print(f"  ✅ Deleted {deleted_counts['system_logs']} system logs")
    
    AudioRecording.objects.all().delete()
    print(f"  ✅ Deleted {deleted_counts['audio_recordings']} audio recordings")
    
    Intent.objects.all().delete()
    print(f"  ✅ Deleted {deleted_counts['intents']} intents")
    
    ConversationMessage.objects.all().delete()
    print(f"  ✅ Deleted {deleted_counts['conversation_messages']} conversation messages")
    
    CallSession.objects.all().delete()
    print(f"  ✅ Deleted {deleted_counts['call_sessions']} call sessions")
    
    AIConfiguration.objects.all().delete()
    print(f"  ✅ Deleted {deleted_counts['ai_configurations']} AI configurations")
    
    Business.objects.all().delete()
    print(f"  ✅ Deleted {deleted_counts['businesses']} businesses")
    
    total_deleted = sum(deleted_counts.values())
    print(f"\n✅ Successfully cleared {total_deleted} total records!")
    print(f"\nTo create new sample data, run:")
    print(f"  python {os.path.basename(__file__)} --create")


def create_sample_data():
    """Create sample data for the receptionist app."""
    print("Creating sample data for receptionist app...")

    # Call management commands to create sample data
    call_command('create_business_types')
    call_command('create_sample_businesses')
    call_command('create_sample_services')
    call_command('create_sample_staff_role')
    call_command('create_sample_staff',
                 per_business=3,
                 assign_services=True)
    call_command('create_sample_notifications', per_business=10, push_devices_per_business=3)

    print("Sample data creation completed!")
    print("\nYou can now:")
    print("1. Check the Django admin interface at /admin/")
    print("2. Use the REST API endpoints to query the data")
    print("3. Run the sample data command again with different parameters")


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Clear or create sample data for the receptionist app."
    )
    parser.add_argument(
        '--clear', action='store_true', help='Clear all sample data'
    )
    parser.add_argument(
        '--create', action='store_true', help='Create sample data'
    )
    args = parser.parse_args()

    if args.clear:
        clear_sample_data()
    elif args.create:
        create_sample_data()
    else:
        print("No action specified. Use --clear to clear data or --create to create sample data.")
        print("Example:")
        print(f"  python {os.path.basename(__file__)} --clear")
        print(f"  python {os.path.basename(__file__)} --create")


if __name__ == '__main__':
    main()
