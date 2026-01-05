from appointment.models import AppointmentService, Appointment, AppointmentStatusType
from datetime import datetime
from payment.models import PaymentMethodType
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
from main.common_settings import ONLINE_BOOKING_URL
from django.db.models import Sum, Count, Value, DateField, F
from client.models import Client

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
                is_working=True,
                staff__is_online_booking_allowed=True,
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
            current_time = current_time + \
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
                staff_id, 
                appointment_date,
            )

            if not staff_working_hours:
                return time_slots

            # convert time to timezone aware
            queryset = AppointmentService.objects.filter(
                staff_id=staff_id,
                is_active=True,
                appointment__appointment_date=appointment_date,
                appointment__is_active=True
            ).exclude(
                appointment__status=AppointmentStatusType.CANCELLED.value,
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

    def find_my_upcoming_appointments(self, client_id) -> list[Appointment]:
        try:
            appointments = Appointment.objects.filter(
                client_id=client_id, 
                appointment_date__gte=timezone.now().date(),
                is_active=True,
                status=AppointmentStatusType.SCHEDULED.value,
                business_id=self.business_id
            ).order_by('appointment_date')
            
            return appointments
        except Exception as e:
            raise Exception(f"Error finding my appointments: {e}")
        
    def find_client_by_phone(self, phone) -> Client | None:
        try:
            client = Client.objects.filter(
                phone=phone, 
                is_active=True, 
                is_deleted=False,
                primary_business_id=self.business_id
            ).first()
            if not client:
                return None
            return client
        except Exception as e:
            raise Exception(f"Error finding client by phone: {e}")

    def cancel_appointment(self, appointment_id, client_id) -> Appointment | None:
        try:
            appointment = Appointment.objects.filter(
                id=appointment_id,
                client_id=client_id,
                is_active=True,
                status=AppointmentStatusType.SCHEDULED.value,
                business_id=self.business_id
            ).first()
            
            if not appointment:
                return None
            appointment.status = AppointmentStatusType.CANCELLED.value
            appointment.cancelled_at = timezone.now()
            appointment.save()
            return appointment
        except Exception as e:
            raise Exception(f"Error canceling appointment: {e}")
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
        metadata,
        business_twilio_phone_number,
    ):
        try:
            business_id = self.appointment.business.id
            title = f"Appointment Confirmed - {business_name}"
            body_message = f"Your appointment #{appointment_id} has been confirmed at {start_at} at {business_name}. If you need to cancel or reschedule your appointment, please contact us at {business_phone}."
            
            self.dispatcher.dispatchAsync(
                title=title,
                body=body_message,
                data=metadata,
                channel=Notification.Channel.SMS,
                to=client_phone,
                business_id=business_id,
                business_twilio_phone_number=business_twilio_phone_number,
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
        business_twilio_phone_number,
    ):
        try:
            title = f"Appointment Reminder - {business_name}"
            body_message = f"Your appointment #{appointment_id} at {start_at} at {business_name} is coming up soon. If you need to cancel or reschedule your appointment, please contact us at {business_phone}."
            
            self.dispatcher.dispatch_scheduled(
                title=title,
                body=body_message,
                data=metadata,
                channel=Notification.Channel.SMS,
                to=client_phone,
                business_id=business_id,
                schedule_name=schedule_name,
                schedule_time=schedule_time,
                business_twilio_phone_number=business_twilio_phone_number,
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
        business_twilio_phone_number,
    ):
        try:
            print("send rescheduled sms", client_name, client_phone, business_phone, business_name, appointment_id, business_id, start_at_str, metadata)
            body_message = f"Your appointment #{appointment_id} has been rescheduled to {start_at_str} at {business_name}. If you need to cancel or reschedule your appointment, please contact us at {business_phone}."
            title = f"Appointment Rescheduled - {business_name}"
            self.dispatcher.dispatchAsync(
                title=title,
                body=body_message,
                data=metadata,
                channel=Notification.Channel.SMS,
                to=client_phone,
                business_id=business_id,
                business_twilio_phone_number=business_twilio_phone_number,
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
        business_twilio_phone_number,
    ):
        try:
            print("send cancellation sms", client_name, client_phone, business_phone, business_name, appointment_id, business_id, start_at_str, metadata)
            body_message = f"Your appointment #{appointment_id} at {start_at_str} at {business_name} has been cancelled. Please contact us at {business_phone} if you have any questions."
            title = f"Appointment Cancelled - {business_name}"
            self.dispatcher.dispatchAsync(
                title=title,
                body=body_message,
                data=metadata,
                channel=Notification.Channel.SMS,
                to=client_phone,
                business_id=business_id,
                business_twilio_phone_number=business_twilio_phone_number,
            )
            self.dispatcher.dispatch_destroy_scheduled(
                channel=Notification.Channel.SMS,
                schedule_name=schedule_name,
            )
        except Exception as e:
            logger.error(f"Error sending cancellation SMS: {e}")
            raise Exception(f"Error sending cancellation SMS: {e}")
    
    def send_client_completed_notification(
        self,
        client_name,
        client_phone,
        business_phone,
        business_name,
        appointment_id,
        business_id,
        metadata,
        business_twilio_phone_number,
    ):
        try:
            review_url = f"{ONLINE_BOOKING_URL}/review/?appointment_id={appointment_id}&business_id={business_id}"
            body_message = f"Your appointment #{appointment_id} has been completed at {business_name}. Thank you for choosing us. Please leave a review to help us improve our services at {review_url} and contact us at {business_phone} if you have any questions."
            title = f"Appointment Completed - {business_name}"
            
            self.dispatcher.dispatchAsync(
                title=title,
                body=body_message,
                data=metadata,
                channel=Notification.Channel.SMS,
                to=client_phone,
                business_id=business_id,
                business_twilio_phone_number=business_twilio_phone_number,
            )
        except Exception as e:
            logger.error(f"Error sending completed SMS: {e}")
            raise Exception(f"Error sending completed SMS: {e}")
    
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
        
    def send_staff_and_manager_payment_notification(
        self,
        title,
        body_message,
        metadata,
        staff,
        business_id,
    ):
        try:
            self.dispatcher.dispatchAsync(
                title=title,
                body=body_message,
                data=metadata,
                channel=Notification.Channel.PUSH,
                to=staff,
            )
            
            self.dispatcher.dispatchAsync(
                title=title,
                body=body_message,
                data=metadata,
                channel=Notification.Channel.PUSH,
                group_name=get_business_managers_group_name(business_id),
                to=None,
            )
        except Exception as e:
            logger.error(f"Error sending staff payment notification: {e}")
            raise Exception(f"Error sending staff payment notification: {e}")
        
class TicketReportService():
    def __init__(self, business_id):
        self.business_id = business_id
    
    def get_ticket_report_summary(self, from_date, to_date, staff_id):
        try:
            queryset = AppointmentService.objects.filter(
                appointment__business_id=self.business_id,
                appointment__appointment_date__gte=from_date,
                appointment__appointment_date__lte=to_date,
                appointment__status=AppointmentStatusType.CHECKED_OUT.value,
            )
            
            if staff_id:
                queryset = queryset.filter(staff_id=staff_id)
                
            staff_sales = queryset.values('staff').annotate(
                staff_first_name=F('staff__first_name'),
                staff_last_name=F('staff__last_name'),
                total_service_sales=Sum('custom_price'),
                total_service_tips=Sum('tip_amount'),
                total_services=Count('id'),
                from_date=Value(from_date, output_field=DateField()),
                to_date=Value(to_date, output_field=DateField()),
            )
            
            summary = queryset.aggregate(
                total_sales=Sum('custom_price'),
                total_tips=Sum('tip_amount'),
                total_services=Count('id'),
            )
            summary['from_date'] = from_date
            summary['to_date'] = to_date
            summary['total_staffs'] = staff_sales.count()
            
            
            return {
                'summary': summary,
                'data': staff_sales,
            }
        except Exception as e:
            raise Exception(f"Error getting ticket report: {e}")
        
    def get_ticket_report_by_dates(self, from_date, to_date, staff_id):
        try:
            queryset = AppointmentService.objects.filter(
                appointment__business_id=self.business_id,
                appointment__appointment_date__gte=from_date,
                appointment__appointment_date__lte=to_date,
                appointment__status=AppointmentStatusType.CHECKED_OUT.value,
                staff_id=staff_id,
            )
            
            queryset = queryset.order_by('-appointment__appointment_date')
            staff_sales = queryset.values('appointment__appointment_date').annotate(
                staff_first_name=F('staff__first_name'),
                staff_last_name=F('staff__last_name'),
                staff=F('staff__id'),
                total_service_sales=Sum('custom_price'),
                total_service_tips=Sum('tip_amount'),
                total_services=Count('id'),
                appointment_date=F('appointment__appointment_date'),
            )
            total_tips = queryset.aggregate(total_tips=Sum('tip_amount'))['total_tips'] or 0
            total_tips_by_cash = queryset.filter(tip_method=PaymentMethodType.CASH.value).aggregate(total_tips=Sum('tip_amount'))['total_tips'] or 0
            total_tips_by_card = total_tips - total_tips_by_cash
            
            summary = queryset.aggregate(
                total_sales=Sum('custom_price'),
                total_tips=Sum('tip_amount'),
                total_services=Count('id'),
            )
            summary['total_cash_tips'] = total_tips_by_cash
            summary['total_card_tips'] = total_tips_by_card
            summary['from_date'] = from_date
            summary['to_date'] = to_date
                
            return {
                'summary': summary,
                'data': staff_sales,
            }
        except Exception as e:
            raise Exception(f"Error getting staff ticket report summary: {e}")
        
    def get_ticket_report_by_date(self, staff_id, date) -> dict:
        try:
            queryset = AppointmentService.objects.filter(
                appointment__business_id=self.business_id,
                appointment__appointment_date=date,
                appointment__status=AppointmentStatusType.CHECKED_OUT.value,
                staff_id=staff_id,
            )
            
            queryset = queryset.order_by('-updated_at')
            staff_sales = queryset.values('appointment__appointment_date').annotate(
                staff_first_name=F('staff__first_name'),
                staff_last_name=F('staff__last_name'),
                staff=F('staff__id'),
                appointment_id=F('appointment__id'),
                service_id=F('service__id'),
                service_name=F('service__name'),
                service_duration=F('service__duration_minutes'),
                custom_price=F('custom_price'),
                tip_amount=F('tip_amount'),
                tip_method=F('tip_method'),
                client_name=F('appointment__client__first_name'),
                updated_at=F('appointment__updated_at'),
                created_at=F('appointment__created_at'),
            )
            
            # total tips
            total_tips = queryset.aggregate(total_tips=Sum('tip_amount'))['total_tips'] or 0
            total_cash_tips = queryset.filter(tip_method=PaymentMethodType.CASH.value).aggregate(total_tips=Sum('tip_amount'))['total_tips'] or 0
            total_card_tips = total_tips - total_cash_tips
            
            summary = queryset.aggregate(
                total_sales=Sum('custom_price'),
                total_tips=Sum('tip_amount'),
                total_services=Count('id'),
            )
            summary['total_cash_tips'] = total_cash_tips
            summary['total_card_tips'] = total_card_tips
            
            return {
                'summary': summary,
                'data': staff_sales,
            }
        except Exception as e:
            raise Exception(f"Error getting ticket report by date: {e}")