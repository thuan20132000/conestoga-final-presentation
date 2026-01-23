from decimal import Decimal
from decimal import ROUND_HALF_UP

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
def get_business_managers_group_name(business_id):
  return f"business_{business_id}_managers"

def money_quantize(amount) -> Decimal:
  return Decimal(amount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def send_html_email(subject, to_email, template, context):
  try:
    html_content = render_to_string(template, context)
    text_content = render_to_string(
        template.replace(".html", ".txt"),
        context
    )
    
    print("html_content: ", html_content)
    print("text_content: ", text_content)
    print("from_email: ", settings.DEFAULT_FROM_EMAIL)
    print("to_email: ", to_email)
    print("subject: ", subject)

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to_email],
    )

    email.attach_alternative(html_content, "text/html")
    email.send(fail_silently=False)
    
    return True
  except Exception as e:
    print("========= Error sending email: ", e)
    return False, str(e)