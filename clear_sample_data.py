#!/usr/bin/env python
"""
Script to clear all sample data from the receptionist app.
Use with caution - this will delete all data!
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

from receptionist.models import (
    Business, AIConfiguration, CallSession, ConversationMessage, 
    Intent, AudioRecording, SystemLog
)


def main():
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
    print(f"  python create_sample_data.py")


if __name__ == '__main__':
    main()
