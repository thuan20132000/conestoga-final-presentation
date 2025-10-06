#!/usr/bin/env python
"""
Script to verify and display sample data created for the receptionist app.
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
    """Display summary of sample data."""
    print("=== Receptionist App Sample Data Summary ===\n")
    
    # Business data
    businesses = Business.objects.all()
    print(f"📊 Businesses: {businesses.count()}")
    for business in businesses:
        config = business.ai_config
        print(f"  • {business.name}")
        print(f"    Phone: {business.phone_number}")
        print(f"    AI: {config.ai_name} ({config.model_name})")
        print(f"    Timezone: {business.timezone}")
    
    print(f"\n📞 Call Sessions: {CallSession.objects.count()}")
    
    # Call statistics
    completed_calls = CallSession.objects.filter(status='completed')
    failed_calls = CallSession.objects.filter(status='failed')
    in_progress_calls = CallSession.objects.filter(status='in_progress')
    
    print(f"  • Completed: {completed_calls.count()}")
    print(f"  • Failed: {failed_calls.count()}")
    print(f"  • In Progress: {in_progress_calls.count()}")
    
    if completed_calls.exists():
        avg_duration = sum(call.duration_seconds for call in completed_calls) / completed_calls.count()
        print(f"  • Average duration: {avg_duration:.1f} seconds")
    
    # Conversation data
    print(f"\n💬 Conversation Messages: {ConversationMessage.objects.count()}")
    user_messages = ConversationMessage.objects.filter(role='user')
    assistant_messages = ConversationMessage.objects.filter(role='assistant')
    print(f"  • User messages: {user_messages.count()}")
    print(f"  • Assistant messages: {assistant_messages.count()}")
    
    # Intent data
    intents = Intent.objects.all()
    print(f"\n🎯 Detected Intents: {intents.count()}")
    intent_types = {}
    for intent in intents:
        intent_types[intent.name] = intent_types.get(intent.name, 0) + 1
    
    for intent_name, count in sorted(intent_types.items()):
        print(f"  • {intent_name}: {count}")
    
    # Audio recordings
    recordings = AudioRecording.objects.all()
    print(f"\n🎵 Audio Recordings: {recordings.count()}")
    
    # System logs
    logs = SystemLog.objects.all()
    print(f"\n📋 System Logs: {logs.count()}")
    log_levels = {}
    for log in logs:
        log_levels[log.level] = log_levels.get(log.level, 0) + 1
    
    for level, count in sorted(log_levels.items()):
        print(f"  • {level}: {count}")
    
    # Sample conversations
    print(f"\n📝 Sample Conversations:")
    for business in businesses[:2]:  # Show first 2 businesses
        recent_call = CallSession.objects.filter(business=business, status='completed').first()
        if recent_call:
            print(f"\n  {business.name} - Call {recent_call.call_sid[:12]}...")
            messages = recent_call.messages.all()[:4]  # First 4 messages
            for msg in messages:
                role_icon = "👤" if msg.role == "user" else "🤖"
                content = msg.content[:60] + "..." if len(msg.content) > 60 else msg.content
                print(f"    {role_icon} {msg.role}: {content}")
            if recent_call.messages.count() > 4:
                print(f"    ... and {recent_call.messages.count() - 4} more messages")
    
    print(f"\n✅ Sample data verification complete!")
    print(f"\nTo view more details:")
    print(f"1. Django Admin: python manage.py runserver (then visit /admin/)")
    print(f"2. Django Shell: python manage.py shell")
    print(f"3. API Endpoints: (if configured)")


if __name__ == '__main__':
    main()
