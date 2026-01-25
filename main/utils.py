from decimal import Decimal
from decimal import ROUND_HALF_UP

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
def get_business_managers_group_name(business_id):
  return f"business_{business_id}_managers"

def money_quantize(amount) -> Decimal:
  return Decimal(amount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

