from django import template
import jdatetime
from django.utils import timezone
from datetime import date
import pytz
import logging


logger = logging.getLogger(__name__)


register = template.Library()

@register.filter
def abs_value(value):
    """Returns the absolute value of the given number."""
    try:
        return abs(value)
    except (TypeError, ValueError):
        return value
    
    
@register.filter
def to_jalali(datetime_field):
    
    try:
        # Define Tehran timezone
        tehran_tz = pytz.timezone('Asia/Tehran')

        # Convert the datetime to Tehran timezone if it's not already localized
        if timezone.is_naive(datetime_field):
            localized_datetime = tehran_tz.localize(datetime_field)
        else:
            localized_datetime = datetime_field.astimezone(tehran_tz)

        # Convert the datetime to Jalali
        jalali_date = jdatetime.datetime.fromgregorian(datetime=localized_datetime)

        # Format the date in Jalali format (e.g., 1402-07-25 15:30:00)
        return jalali_date.strftime('%Y/%m/%d %H:%M')
    except Exception as e:
        logger.error(f'Error changing date: {str(e)}')
        
        
def calculate_package_days(hiddify_user):
    """Calculates the remaining days for a user's package."""
    if hiddify_user.start_date:
        return hiddify_user.package_days - (date.today() - hiddify_user.start_date).days
    return None


