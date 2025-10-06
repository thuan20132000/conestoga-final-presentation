import random
import uuid
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from receptionist.models import (
    Business, AIConfiguration, CallSession, ConversationMessage, 
    Intent, AudioRecording, SystemLog
)


class Command(BaseCommand):
    help = 'Create sample data for the receptionist app'

    def add_arguments(self, parser):
        parser.add_argument(
            '--businesses',
            type=int,
            default=3,
            help='Number of businesses to create (default: 3)'
        )
        parser.add_argument(
            '--calls-per-business',
            type=int,
            default=5,
            help='Number of calls per business (default: 5)'
        )
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='Clear existing data before creating new sample data'
        )

    def handle(self, *args, **options):
        businesses_count = options['businesses']
        calls_per_business = options['calls_per_business']
        clear_existing = options['clear_existing']

        if clear_existing:
            self.stdout.write('Clearing existing data...')
            self.clear_existing_data()

        self.stdout.write(f'Creating {businesses_count} businesses with {calls_per_business} calls each...')
        
        # Create sample businesses
        businesses = self.create_sample_businesses(businesses_count)
        
        # Create sample data for each business
        for business in businesses:
            self.create_sample_calls(business, calls_per_business)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created sample data: {businesses_count} businesses, '
                f'{businesses_count * calls_per_business} calls'
            )
        )

    def clear_existing_data(self):
        """Clear all existing data in the correct order due to foreign key constraints."""
        SystemLog.objects.all().delete()
        AudioRecording.objects.all().delete()
        Intent.objects.all().delete()
        ConversationMessage.objects.all().delete()
        CallSession.objects.all().delete()
        AIConfiguration.objects.all().delete()
        Business.objects.all().delete()

    def create_sample_businesses(self, count):
        """Create sample businesses with AI configurations."""
        businesses_data = [
            {
                'name': 'Blissful Beauty Salon',
                'phone_number': '+1-555-0101',
                'address': '123 Main Street, Toronto, ON M5V 3A1',
                'timezone': 'America/Toronto',
                'ai_config': {
                    'ai_name': 'Sarah',
                    'greeting_message': 'Hi! Welcome to Blissful Beauty Salon. How can I help you today?',
                    'language': 'en',
                    'voice_provider': 'ElevenLabs',
                    'model_name': 'gpt-4',
                    'temperature': 0.8,
                }
            },
            {
                'name': 'Golden Nails & Spa',
                'phone_number': '+1-555-0202',
                'address': '456 Queen Street West, Toronto, ON M5V 2A9',
                'timezone': 'America/Toronto',
                'ai_config': {
                    'ai_name': 'Maya',
                    'greeting_message': 'Hello! Thank you for calling Golden Nails & Spa. What can I do for you?',
                    'language': 'en',
                    'voice_provider': 'ElevenLabs',
                    'model_name': 'gpt-4',
                    'temperature': 0.7,
                }
            },
            {
                'name': 'Style Studio Hair Salon',
                'phone_number': '+1-555-0303',
                'address': '789 Bay Street, Toronto, ON M5G 1M5',
                'timezone': 'America/Toronto',
                'ai_config': {
                    'ai_name': 'Alex',
                    'greeting_message': 'Good day! This is Style Studio Hair Salon. How may I assist you?',
                    'language': 'en',
                    'voice_provider': 'ElevenLabs',
                    'model_name': 'gpt-4',
                    'temperature': 0.6,
                }
            }
        ]

        businesses = []
        for i in range(count):
            data = businesses_data[i % len(businesses_data)]
            
            # Create business
            business = Business.objects.create(
                name=data['name'] if i < len(businesses_data) else f'Sample Business {i+1}',
                phone_number=data['phone_number'],
                address=data['address'],
                timezone=data['timezone']
            )
            
            # Create AI configuration
            AIConfiguration.objects.create(
                business=business,
                **data['ai_config']
            )
            
            businesses.append(business)
            self.stdout.write(f'Created business: {business.name}')

        return businesses

    def create_sample_calls(self, business, count):
        """Create sample call sessions with conversations and related data."""
        call_scenarios = [
            {
                'type': 'booking',
                'messages': [
                    ('user', 'Hi, I\'d like to book an appointment for a haircut'),
                    ('assistant', 'I\'d be happy to help you book an appointment! What day works best for you?'),
                    ('user', 'How about next Tuesday afternoon?'),
                    ('assistant', 'Let me check our availability for Tuesday afternoon. What time would you prefer?'),
                    ('user', 'Around 2 PM if possible'),
                    ('assistant', 'Perfect! I have 2:00 PM available on Tuesday. May I get your name and phone number?'),
                    ('user', 'My name is John Smith and my number is 416-555-1234'),
                    ('assistant', 'Great! I\'ve booked you for Tuesday at 2:00 PM. Is there anything else I can help you with?'),
                    ('user', 'No, that\'s perfect. Thank you!'),
                    ('assistant', 'You\'re welcome! We\'ll see you Tuesday at 2:00 PM. Have a great day!')
                ],
                'intents': [
                    ('book_appointment', 0.95, {'service': 'haircut', 'date': 'Tuesday', 'time': '2:00 PM'}),
                    ('provide_contact_info', 0.90, {'name': 'John Smith', 'phone': '416-555-1234'})
                ],
                'duration': random.randint(180, 480),  # 3-8 minutes
                'status': 'completed'
            },
            {
                'type': 'inquiry',
                'messages': [
                    ('user', 'What are your hours?'),
                    ('assistant', 'We\'re open Monday to Friday 9 AM to 7 PM, and Saturday 10 AM to 5 PM. We\'re closed on Sundays.'),
                    ('user', 'Do you offer hair coloring services?'),
                    ('assistant', 'Yes, we do! We offer full hair coloring, highlights, and color corrections. Would you like to book a consultation?'),
                    ('user', 'Maybe later, thanks for the info'),
                    ('assistant', 'You\'re welcome! Feel free to call back anytime to book. Have a great day!')
                ],
                'intents': [
                    ('inquire_hours', 0.92, {}),
                    ('inquire_services', 0.88, {'service': 'hair coloring'})
                ],
                'duration': random.randint(120, 300),  # 2-5 minutes
                'status': 'completed'
            },
            {
                'type': 'cancellation',
                'messages': [
                    ('user', 'I need to cancel my appointment for tomorrow'),
                    ('assistant', 'I\'d be happy to help you cancel. May I get your name and the appointment details?'),
                    ('user', 'It\'s Sarah Johnson, I have an appointment at 3 PM'),
                    ('assistant', 'I found your appointment for Sarah Johnson at 3 PM tomorrow. I\'ll cancel that for you.'),
                    ('user', 'Thank you'),
                    ('assistant', 'You\'re welcome! Is there anything else I can help you with today?'),
                    ('user', 'No, that\'s all'),
                    ('assistant', 'Have a great day!')
                ],
                'intents': [
                    ('cancel_appointment', 0.93, {'name': 'Sarah Johnson', 'time': '3:00 PM'})
                ],
                'duration': random.randint(90, 240),  # 1.5-4 minutes
                'status': 'completed'
            },
            {
                'type': 'failed_call',
                'messages': [
                    ('user', 'Hello?'),
                    ('assistant', 'Hello! How can I help you today?'),
                    ('user', 'I can barely hear you'),
                    ('assistant', 'I apologize for the audio issues. Can you hear me better now?'),
                    ('user', 'No, this is too difficult'),
                    ('assistant', 'I understand. Would you like to try calling back?')
                ],
                'intents': [
                    ('audio_issue', 0.85, {})
                ],
                'duration': random.randint(30, 120),  # 30 seconds to 2 minutes
                'status': 'failed'
            }
        ]

        for i in range(count):
            scenario = random.choice(call_scenarios)
            call_sid = f'CA{str(uuid.uuid4()).replace("-", "")[:30]}'
            
            # Random time within the last 30 days
            start_time = timezone.now() - timedelta(days=random.randint(1, 30))
            duration = scenario['duration']
            end_time = start_time + timedelta(seconds=duration)
            
            # Create call session
            call = CallSession.objects.create(
                business=business,
                direction='inbound',
                caller_number=f'+1-416-555-{random.randint(1000, 9999)}',
                receiver_number=business.phone_number,
                call_sid=call_sid,
                started_at=start_time,
                ended_at=end_time,
                duration_seconds=duration,
                status=scenario['status'],
                transcript_summary=f"Customer {scenario['type']} conversation with {business.ai_config.ai_name}"
            )
            
            # Create conversation messages
            self.create_conversation_messages(call, scenario['messages'])
            
            # Create intents
            self.create_intents(call, scenario['intents'])
            
            # Create audio recording (if call was successful)
            if scenario['status'] == 'completed':
                self.create_audio_recording(call)
            
            # Create system logs
            self.create_system_logs(call, scenario['status'])
            
            self.stdout.write(f'  Created call {call_sid} ({scenario["type"]}) - {duration}s')

    def create_conversation_messages(self, call, messages):
        """Create conversation messages for a call."""
        base_time = call.started_at
        
        for i, (role, content) in enumerate(messages):
            # Spread messages over the call duration
            message_time = base_time + timedelta(seconds=(i * call.duration_seconds / len(messages)))
            
            ConversationMessage.objects.create(
                call=call,
                role=role,
                content=content,
                timestamp=message_time,
                confidence_score=random.uniform(0.85, 0.98) if role == 'user' else None
            )

    def create_intents(self, call, intents):
        """Create intent records for a call."""
        base_time = call.started_at
        
        for i, (name, confidence, data) in enumerate(intents):
            Intent.objects.create(
                call=call,
                name=name,
                confidence=confidence,
                extracted_data=data,
                created_at=base_time + timedelta(seconds=i * 30)
            )

    def create_audio_recording(self, call):
        """Create audio recording reference."""
        AudioRecording.objects.create(
            call=call,
            audio_url=f'https://api.twilio.com/2010-04-01/Accounts/AC123/Recordings/{call.call_sid}.mp3',
            duration_seconds=call.duration_seconds,
            transcription_text=' '.join([msg.content for msg in call.messages.filter(role='user')]),
        )

    def create_system_logs(self, call, status):
        """Create system logs for a call."""
        logs = [
            ('info', 'Call initiated', {'call_sid': call.call_sid}),
            ('info', 'AI assistant activated', {'model': call.business.ai_config.model_name}),
        ]
        
        if status == 'completed':
            logs.extend([
                ('info', 'Call completed successfully', {'duration': call.duration_seconds}),
                ('info', 'Transcript generated', {'message_count': call.messages.count()}),
            ])
        elif status == 'failed':
            logs.append(('error', 'Call failed due to audio issues', {'error_type': 'audio_quality'}))
        
        base_time = call.started_at
        
        for i, (level, message, metadata) in enumerate(logs):
            SystemLog.objects.create(
                call=call,
                level=level,
                message=message,
                metadata=metadata,
                created_at=base_time + timedelta(seconds=i * 10)
            )
