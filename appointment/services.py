from appointment.models import AppointmentService, Appointment
from datetime import datetime
from staff.models import StaffService, StaffWorkingHours
from datetime import timedelta
from django.utils import timezone
from staff.models import Staff, StaffOffDay
from django.db import transaction
from notifications.models import Notification
from notifications.services import NotificationDispatcher
from business.models import BusinessSettings
import logging
from main.utils import get_business_managers_group_name
logger = logging.getLogger(__name__)
class BusinessBookingService:
    def __init__(self, business_id, interval_minutes=15):
        self.business_id = business_id
        self.interval_minutes = interval_minutes

    def _check_staff_services(self, staff_id, service_ids):
        try:
            staff_services = StaffService.objects.filter(
                staff__id=staff_id,
                service__in=service_ids,
                is_active=True
            )

            if staff_services.count() != len(service_ids) or staff_services.count() == 0:
                return False
            return True
        except Exception as e:
            raise Exception(f"Error checking staff services: {e}")

    def _get_staff_working_hours(self, staff_id, appointment_date):
        try:
            # convert appointment_date 2025-11-21 to weekday
            weekday = datetime.strptime(
                appointment_date, '%Y-%m-%d').weekday()

            working_hours = StaffWorkingHours.objects.filter(
                staff__id=staff_id,
                day_of_week=weekday,
                is_working=True
            ).first()

            if not working_hours:
                return False

            return working_hours
        except Exception as e:
            raise Exception(f"Error getting staff working hours: {e}")

    def _check_staff_off_days(self, staff_id, appointment_date):
        try:
            day_offs = StaffOffDay.objects.filter(
                staff__id=staff_id,
                start_date__lte=appointment_date,
                end_date__gte=appointment_date
            )
            if day_offs.count() > 0:
                return True
            return False
        except Exception as e:
            raise Exception(f"Error checking staff off days: {e}")

    def _generate_time_slots(
        self,
        current_time,
        next_time,
        service_duration,
        staff_id,
        interval_minutes,
        appointment_date
    ):
        time_slots = []
        appointment_date = datetime.strptime(appointment_date, '%Y-%m-%d').date()
        print("appointment_date3", appointment_date)
        
        while (current_time + service_duration) <= next_time:
            service_end_time = current_time + service_duration

            start_time = (datetime.min + current_time).strftime('%H:%M')
            end_time = (datetime.min + service_end_time).strftime('%H:%M')
            
            # convert start_time and end_time to timezone aware datetime and set date to 2025-11-24
            start_time = timezone.make_aware(datetime.strptime(start_time, '%H:%M'))
            start_time = start_time.replace(
                year=appointment_date.year, 
                month=appointment_date.month, 
                day=appointment_date.day
            )    
                                             
            end_time = timezone.make_aware(datetime.strptime(end_time, '%H:%M'))
            end_time = end_time.replace(
                year=appointment_date.year, 
                month=appointment_date.month, 
                day=appointment_date.day
            )
            
            time_slots.append({
                'start_time': start_time,
                'end_time': end_time,
                'staff_id': staff_id,
            })
            current_time = service_end_time + \
                timedelta(minutes=interval_minutes)

        return time_slots

    def get_staff_time_slots(self, staff_id, service_ids, appointment_date, service_duration):
        try:
            # Check if business is open on the date
            # operating_hours = self._get_operating_hours()
            time_slots = []
            interval_minutes = self.interval_minutes

            if self._check_staff_off_days(staff_id, appointment_date):
                return time_slots

            # Check if staff provides the service and is active
            if not self._check_staff_services(staff_id, service_ids):
                return time_slots

            staff_working_hours = self._get_staff_working_hours(
                staff_id, appointment_date)

            if not staff_working_hours:
                return time_slots

            # convert time to timezone aware
            queryset = AppointmentService.objects.filter(
                staff_id=staff_id,
                is_active=True,
                appointment__appointment_date=appointment_date,
            )

            time_zone = timezone.get_current_timezone()

            # sort queryset by start_at
            booked_time_slots = queryset.order_by('start_at')

            staff_working_start_time = timedelta(
                hours=staff_working_hours.start_time.hour,
                minutes=staff_working_hours.start_time.minute
            )
            staff_working_end_time = timedelta(
                hours=staff_working_hours.end_time.hour,
                minutes=staff_working_hours.end_time.minute
            )

            current_time = staff_working_start_time
            total_service_duration = timedelta(minutes=int(service_duration))
            for booked_time_slot in booked_time_slots:
                booked_start_time = booked_time_slot.start_at.astimezone(
                    time_zone).time()
                booked_end_time = booked_time_slot.end_at.astimezone(
                    time_zone).time()
                booked_start_time = timedelta(
                    hours=booked_start_time.hour, minutes=booked_start_time.minute)
                booked_end_time = timedelta(
                    hours=booked_end_time.hour, minutes=booked_end_time.minute)

                latest_start_time = booked_start_time - total_service_duration

                if booked_start_time < staff_working_start_time and booked_end_time > staff_working_start_time:
                    current_time = booked_end_time
                    continue

                if booked_start_time > staff_working_end_time:
                    break

                # If there's enough time before the booking, generate slots
                if current_time <= latest_start_time:
                    slots = self._generate_time_slots(
                        current_time,
                        booked_start_time,
                        total_service_duration,
                        staff_id,
                        interval_minutes,
                        appointment_date
                    )
                    time_slots.extend(slots)

                if booked_end_time > current_time:
                    current_time = booked_end_time

            if current_time < staff_working_end_time:
                slots = self._generate_time_slots(
                    current_time,
                    staff_working_end_time,
                    total_service_duration,
                    staff_id,
                    interval_minutes,
                    appointment_date
                )
                time_slots.extend(slots)

            return time_slots
        except Exception as e:
            raise Exception(f"Error checking staff availability: {e}")

    def get_all_available_time_slots(self, business_id, service_ids, appointment_date, service_duration):
        try:
            staffs = Staff.objects.filter(business=business_id, is_active=True)
            time_slots = []

            for staff in staffs:
                available_time_slots = self.get_staff_time_slots(
                    staff_id=staff.id,
                    service_ids=service_ids,
                    appointment_date=appointment_date,
                    service_duration=service_duration,
                )

                time_slots.extend(available_time_slots)

            # remove duplicate time slots by start_time
            unique_time_slots = []
            seen_time_slots = set()
            for slot in time_slots:
                slot_key = slot['start_time']
                if slot_key not in seen_time_slots:
                    unique_time_slots.append(slot)
                    seen_time_slots.add(slot_key)

            # sort unique_time_slots by start_time
            unique_time_slots.sort(key=lambda x: x['start_time'])

            return unique_time_slots
        except Exception as e:
            raise Exception(f"Error getting all available time slots: {e}")

    def create_appointment_services(self, appointment, appointment_services):
        try:
            with transaction.atomic():
                created_appointment = Appointment.objects.create(**appointment)
                
                for appointment_service in appointment_services:
                    AppointmentService.objects.create(
                        id=appointment_service['id'],
                        appointment=created_appointment,
                        service_id=appointment_service['service'],
                        staff_id=appointment_service['staff'],
                        is_staff_request=appointment_service['is_staff_request'],
                        start_at=appointment_service['start_at'],
                        end_at=appointment_service['end_at'],
                        custom_price=appointment_service['custom_price'],
                    )
                    
                return created_appointment
        except Exception as e:
            raise Exception(f"Error creating appointment services: {e}")


class BusinessStaffService:
    def __init__(self, business_id):
        self.business_id = business_id

    def get_business_active_technicians(self):
        try:
            return Staff.objects.filter(
                business_id=self.business_id,
                is_active=True,
                is_deleted=False,
                is_online_booking_allowed=True,
                role__name='Technician',
            )
        except Exception as e:
            raise Exception(f"Error getting business staffs: {e}")

class AppointmentBusinessService:
    def __init__(self, business_id):
        self.business_id = business_id

    def get_business_settings(self):
        try:
            return BusinessSettings.objects.get(business_id=self.business_id)
        except Exception as e:
            raise Exception(f"Error getting business settings: {e}")

class AppointmentNotificationService:
    def __init__(self, appointment):
        self.appointment = appointment
        self.dispatcher = NotificationDispatcher()

    def send_client_confirmation_notification(
        self,
        client_name,
        client_phone,
        business_phone,
        business_name,
        appointment_id,
        start_at,
        metadata):
        try:
            business_id = self.appointment.business.id
            title = f"Appointment Confirmed - {business_name}"
            body_message = f"Hello {client_name}, your appointment #{appointment_id} has been confirmed at {start_at} at {business_name}. If you need to cancel or reschedule your appointment, please contact us at {business_phone}."
            
            self.dispatcher.dispatchAsync(
                title=title,
                body=body_message,
                data=metadata,
                channel=Notification.Channel.SMS,
                to=client_phone,
                business_id=business_id,
            )
            
        except Exception as e:
            logger.error(f"Error sending confirmation SMS: {e}")
            raise Exception(f"Error sending confirmation SMS: {e}")

    def send_client_reminder_notification(
        self,
        client_name,
        client_phone,
        business_phone,
        business_name,
        appointment_id,
        start_at,
        metadata,
        schedule_name,
        schedule_time,
        business_id,
    ):
        try:
            title = f"Appointment Reminder - {business_name}"
            body_message = f"Hello {client_name}, your appointment #{appointment_id} at {start_at} at {business_name} is coming up soon. If you need to cancel or reschedule your appointment, please contact us at {business_phone}."
            
            self.dispatcher.dispatch_scheduled(
                title=title,
                body=body_message,
                data=metadata,
                channel=Notification.Channel.SMS,
                to=client_phone,
                business_id=business_id,
                schedule_name=schedule_name,
                schedule_time=schedule_time,
            )
        except Exception as e:
            logger.error(f"Error sending reminder SMS: {e}")
            raise Exception(f"Error sending reminder SMS: {e}")

    def send_client_rescheduled_notification(
        self,
        client_name,
        client_phone,
        business_phone,
        business_name,
        appointment_id,
        business_id,
        start_at_str,
        metadata,
    ):
        try:
            print("send rescheduled sms", client_name, client_phone, business_phone, business_name, appointment_id, business_id, start_at_str, metadata)
            body_message = f"Hello {client_name}, your appointment #{appointment_id} has been rescheduled to {start_at_str} at {business_name}. If you need to cancel or reschedule your appointment, please contact us at {business_phone}."
            title = f"Appointment Rescheduled - {business_name}"
            self.dispatcher.dispatchAsync(
                title=title,
                body=body_message,
                data=metadata,
                channel=Notification.Channel.SMS,
                to=client_phone,
                business_id=business_id,
            )
        except Exception as e:
            logger.error(f"Error sending rescheduled SMS: {e}")
            raise Exception(f"Error sending rescheduled SMS: {e}")
    
    def send_client_cancellation_notification(
        self,
        client_name,
        client_phone,
        business_phone,
        business_name,
        appointment_id,
        business_id,
        start_at_str,
        metadata,
        schedule_name,
    ):
        try:
            print("send cancellation sms", client_name, client_phone, business_phone, business_name, appointment_id, business_id, start_at_str, metadata)
            body_message = f"Hello {client_name}, your appointment #{appointment_id} at {start_at_str} at {business_name} has been cancelled. Please contact us at {business_phone} if you have any questions."
            title = f"Appointment Cancelled - {business_name}"
            self.dispatcher.dispatchAsync(
                title=title,
                body=body_message,
                data=metadata,
                channel=Notification.Channel.SMS,
                to=client_phone,
                business_id=business_id,
            )
            self.dispatcher.dispatch_destroy_scheduled(
                channel=Notification.Channel.SMS,
                schedule_name=schedule_name,
            )
        except Exception as e:
            logger.error(f"Error sending cancellation SMS: {e}")
            raise Exception(f"Error sending cancellation SMS: {e}")
    
    
    # staff notifications
    def send_staff_appointment_confirmation_notification(
        self,
        staff,
        staff_name,
        business_name,
        client_name,
        service_name,
        start_time_str,
        booking_source,
        metadata,
    ):  
        try:
            
            body_message = f"{client_name} has booked a new appointment for {service_name} at {start_time_str} with {staff_name} {booking_source}"
            title = f"New Appointment - {business_name}"
            self.dispatcher.dispatchAsync(
                title=title,
                body=body_message,
                data=metadata,
                channel=Notification.Channel.PUSH,
                to=staff,
            )
        except Exception as e:
            logger.error(f"Error sending appointment confirmation Push: {e}")
            raise Exception(f"Error sending appointment confirmation Push: {e}")
        

    def send_manager_appointment_confirmation_notification(
        self,
        staff,
        staff_name,
        business_name,
        client_name,
        service_name,
        start_time_str,
        booking_source,
        metadata,
        business_id,
    ):
        try:
            body_message = f"{client_name} has booked a new appointment for {service_name} at {start_time_str} with {staff_name} {booking_source}"
            title = f"New Appointment - {business_name}"
            self.dispatcher.dispatchAsync(
                title=title,
                body=body_message,
                data=metadata,
                channel=Notification.Channel.PUSH,
                group_name=get_business_managers_group_name(business_id),
                to=None,
            )
        except Exception as e:
            raise Exception(f"Error sending manager appointment confirmation Push: {e}")