import logging
from datetime import date, datetime, timedelta

import requests
from celery import shared_task
from django.conf import settings
from django.db import transaction
from django.db.models import F, Q
from django.utils import timezone

from adminlogs.action import add_admin_log
from client_actions.models import Config, Order
from task_manager.hiddify_actions import (get_users, on_off_user,
                                          send_telegram_message, update_user)
from task_manager.models import HiddifyAccessInfo, HiddifyUser
from telegram_bot.models import Telegram_account, Telegram_Bot_Info

logger = logging.getLogger(__name__)

# ------------------ Tasks for fetching data from external API and updating the database ------------------

# Task to fetch data from external API and update the database
@shared_task()
def fetch_data_from_api():
    """ Fetch data from external API and update the database """

    try:
        hiddify_access_info = HiddifyAccessInfo.objects.latest('created_date')
    except HiddifyAccessInfo.DoesNotExist:
        logger.error("No objects found in HiddifyAccessInfo.")
        return 0
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return 0

    hiddify_api_key = hiddify_access_info.hiddify_api_key
    panel_admin_domain = hiddify_access_info.panel_admin_domain
    admin_proxy_path = hiddify_access_info.admin_proxy_path

    try:
        logger.info('Task started: fetching data from API...')
        users_data = get_users(
            hiddify_api_key, panel_admin_domain, admin_proxy_path)

        # Check if data was fetched successfully
        if not users_data:
            logger.error('Failed to fetch data from API.')
            return 'Failed to fetch data from API.'
        
        api_uuids = {item['uuid'] for item in users_data}
        updated_uuids = set()


        # Update your database
        with transaction.atomic():  # Ensure atomic DB operations
            for item in users_data:
                # Convert naive datetime to timezone-aware datetime
                last_online = item['last_online']
                last_reset_time = item['last_reset_time']
                start_date = item['start_date']

                # Convert to timezone-aware if it's a valid datetime
                if last_online:
                    last_online = timezone.make_aware(
                        datetime.fromisoformat(last_online))
                if last_reset_time:
                    last_reset_time = timezone.make_aware(
                        datetime.fromisoformat(last_reset_time))
                if start_date:
                    start_date = timezone.make_aware(
                        datetime.fromisoformat(start_date))

                # Update or create the HiddifyUser instance
                HiddifyUser.objects.update_or_create(
                    uuid=item['uuid'],  # Lookup field (unique identifier)
                    defaults={
                        'added_by_uuid': item['added_by_uuid'],
                        'current_usage_GB': item['current_usage_GB'],
                        'enable': item['enable'],
                        'is_active': item['is_active'],
                        'last_online': last_online,
                        'last_reset_time': last_reset_time,
                        'name': item['name'],
                        'package_days': item['package_days'],
                        'start_date': start_date,
                        'telegram_id': item['telegram_id'],
                        'usage_limit_GB': item['usage_limit_GB'],
                        'comment' : item['comment'],
                    }
                )
                updated_uuids.add(item['uuid'])
                
            # Find users not in the API data and mark them as disabled
            disabled_users = HiddifyUser.objects.exclude(uuid__in=updated_uuids)
            for user in disabled_users:
                user.enable = False
                user.comment = "deleted"
                user.save()
                logger.info(f"User disabled: {user.uuid} (not in API data)")
                
            logger.info('Task completed successfully.')
            return 'Database updated successfully.'

    except requests.exceptions.RequestException as e:
        logger.error(f'Error fetching data: {str(e)}')
        return f'Error fetching data: {str(e)}'

    except Exception as e:
        logger.error(f'Task failed with error: {str(e)}')
        return f'Task failed with error: {str(e)}'


# Task to check if user's subscription has expired and has a pending order or not
@shared_task()
def check_subscription_expiry():
    """ Check if user's subscription has expired and has a pending order or not """
    
    try:
        hiddify_access_info = HiddifyAccessInfo.objects.latest('created_date')
    except HiddifyAccessInfo.DoesNotExist:
        logger.error("No objects found in HiddifyAccessInfo.")
        return 0
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return 0

    hiddify_api_key = hiddify_access_info.hiddify_api_key
    panel_admin_domain = hiddify_access_info.panel_admin_domain
    admin_proxy_path = hiddify_access_info.admin_proxy_path

    # get all HiddifyUser that are expired
    expired_users = HiddifyUser.objects.filter( Q(enable=False) | Q(is_active=False) )

    for expired_user in expired_users:
        # Check if user has a pending order
        try:
            config = Config.objects.get(uuid=expired_user.uuid)

        except Config.DoesNotExist:
            logger.error(
                f'The site has no config with the given uuid. uuid: {expired_user.uuid} name: {expired_user.name}')
            continue

        order = config.order_configs.filter(
            user=config.user, config=config).last()

        if order and order.pending:
            # initiate the payment process
            update_respons = update_user(
                uuid=expired_user.uuid,
                days=order.plan.duration,
                trafic=order.plan.trafic,
                hiddify_api_key=hiddify_api_key,
                admin_proxy_path=admin_proxy_path,
                panel_admin_domain=panel_admin_domain,
                )
            

            if update_respons:
                # Update the order status
                order.pending = False
                order.save()
                
                
                logger.info(
                    f'User subscription updated: {expired_user.uuid} name: {expired_user.name}')
                continue

        else:
            logger.info(
                f'User do not have a pending order: {expired_user.uuid} name: {expired_user.name}')
            continue


# Task to disable users that have not paid for their subscription
@shared_task(bind=True, max_retries=5)
def disable_not_paid_users(self):
    """ Disable users that have not paid for their subscription """
    
    try:
        hiddify_access_info = HiddifyAccessInfo.objects.latest('created_date')
    except HiddifyAccessInfo.DoesNotExist:
        logger.error("No objects found in HiddifyAccessInfo.")
        return 0
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return 0

    hiddify_api_key = hiddify_access_info.hiddify_api_key
    panel_admin_domain = hiddify_access_info.panel_admin_domain
    admin_proxy_path = hiddify_access_info.admin_proxy_path
    
    telegram_info = Telegram_Bot_Info.objects.latest('created_date')

    # Get WAITING_FOR_PAYMENT_TIMEOUT_DAYS days ago date
    waiting_for_payment_timeout_days = timezone.now() - timedelta(days=settings.WAITING_FOR_PAYMENT_TIMEOUT_DAYS)

    # Query that get uuid of active configs
    active_configs_uuids = HiddifyUser.objects.filter(enable=True).values_list('uuid', flat=True)

    # Query all orders that are older than WAITING_FOR_PAYMENT_TIMEOUT_DAYS days, still pending, and not paid
    unpaid_orders = Order.objects.filter(
        updated_date__lte=waiting_for_payment_timeout_days,  # Orders created more than WAITING_FOR_PAYMENT_TIMEOUT_DAYS days ago
        status=False,  # Order not paid
        pending=False,   # Order not pending
        config__uuid__in=active_configs_uuids
    )

    for order in unpaid_orders:
        try:
            # Disable the user account
            on_off_user(uuid=order.config.uuid, enable=False,
                        hiddify_api_key=hiddify_api_key,
                        admin_proxy_path=admin_proxy_path,
                        panel_admin_domain=panel_admin_domain
                        )
            logger.info(f'User disabled: {order.config.uuid}')
            
            hiddify_config = HiddifyUser.objects.get(uuid=order.config.uuid)
                        
            if telegram_info:
                
                # Send a message to the user about disabling their account
                try:
                    telegram_account = Telegram_account.objects.get(user=order.user)
                    message = f'⚠️ <b>اطلاع رسانی</b> ⚠️\n\n🔴 اشتراک "{hiddify_config.name}" شما به دلیل عدم پرداخت هزینه، قطع شده است.\n\nبرای فعال‌سازی مجدد، لطفاً از طریق <a href="{settings.DOMAIN_NAME}">لینک پرداخت</a> اقدام فرمایید. 🙏'
                    send_telegram_message(token=telegram_info.token, chat_id=telegram_account.telegram_user_id, message=message)
                    logger.info(f'Message sent to {order.user} about disabling user: {order.config.uuid}')
                
                except Telegram_account.DoesNotExist:
                    logger.error(f"No telegram account found for user: {order.user}")
                    continue
                
                # send admin log to telegram
                message = f'کاربری با uuid: {order.config.uuid} و نام: {hiddify_config.name} به دلیل عدم پرداخت هزینه، غیرفعال شد.'
                send_telegram_message(token=telegram_info.token, chat_id=telegram_info.admin_user_id, message=message,)
            
            
        except Exception as e:
            logger.error(f'Error disabling user: {str(e)}')
            continue


# Task to send payment reminder message to users
@shared_task()
def send_payment_reminder_messsage():
    """ Send message trough telegram bot """

    update_link = settings.DOMAIN_NAME
    telegram_info = Telegram_Bot_Info.objects.latest('created_date')
    if not telegram_info:
        logger.error("No objects found in Telegram_Bot_Info.")
        return 0

    # Get warning days ago date
    Warning_days = timezone.now() - timedelta(days=settings.WARNING_FOR_PAYMENT_TIMEOUT_DAYS)

    # Query all orders that are older than WARNING_FOR_PAYMENT_TIMEOUT_DAYS days, still pending, and not paid
    unpaid_orders = Order.objects.filter(
        updated_date__lte=Warning_days,  # Orders created more than WARNING_FOR_PAYMENT_TIMEOUT_DAYS days ago
        status=False,  # Order not paid
        pending=False   # Order not pending
    )

    for unpaid_order in unpaid_orders:
        try:
            # Get the user's telegram account
            telegram_account = Telegram_account.objects.get(
                user=unpaid_order.user)
            
            #get the congig name
            config = HiddifyUser.objects.get(uuid=unpaid_order.config.uuid)

            # calculate the remaining days
            remaining_days = settings.WAITING_FOR_PAYMENT_TIMEOUT_DAYS - (date.today() - unpaid_order.created_date.date()).days

            if remaining_days > 0:
                # Create the message
                message = f'🔔 <b>یادآوری پرداخت اشتراک</b> 🔔\n\n⏳ مهلت پرداخت اشتراک "{config.name}" رو به اتمامه! فقط <b>{remaining_days} روز</b> دیگه فرصت دارید.\n\n📦 پلن انتخابی شما: <b>{unpaid_order.plan}</b>\n\nبرای پرداخت هزینه اشتراک، لطفاً روی <a href="{update_link}">لینک پرداخت</a> کلیک کنید. 🙏'
            else:
                message = f'🔔🔴 <b>یادآوری پرداخت اشتراک</b> 🔴🔔\n\n⏳ مهلت پرداخت اشتراک "{config.name}" به پایان رسیده است! لطفاً هر چه سریع‌تر اقدام کنید.\n\n📦 پلن انتخابی شما: <b>{unpaid_order.plan}</b>\n\nبرای پرداخت و فعال‌سازی اشتراک، لطفاً روی <a href="{update_link}">لینک پرداخت</a> کلیک کنید. 🙏'
            
                
            # Send the payment reminder message
            send_telegram_message(
                token=telegram_info.token,
                chat_id=telegram_account.telegram_user_id,
                message=message,
            )
            logger.info(f'Message sent to {unpaid_order.user}')
            continue
        
        except Telegram_account.DoesNotExist:
            logger.error(f"No telegram account found for user: {unpaid_order.user}")
            continue

        except HiddifyUser.DoesNotExist:
            logger.error(f"No config_hiddify found for uuid: {unpaid_order.config.uuid}")
            add_admin_log(f'No config_hiddify found for user that order something with uuid: {unpaid_order.config.uuid} in tasks.py', 'user', unpaid_order.user)
            continue

        except Exception as e:
            logger.error(f'Error sending message: {str(e)}')
            add_admin_log(f'Error sending message: {str(e)} in tasks.py function : send_payment_reminder_messsage ', 'user', unpaid_order.user)
            continue


# Task to send a warning message to users that have not enough days to their subscription and current_usage_GB is more than usage_limit_GB
@shared_task()
def send_warning_message():
    """ send warning message to users that have not enough days to their subscription and current_usage_GB is more than usage_limit_GB """

    telegram_info = Telegram_Bot_Info.objects.latest('created_date')
    if not telegram_info:
        logger.error("No objects found in Telegram_Bot_Info.")
        return 0
    
    # Calculate the threshold for "less than WARNING_FOR_CONFIG_TIMEOUT_DAYS days from now"
    warning_for_config_timeout_days = timezone.now().date() + timedelta(days=settings.WARNING_FOR_CONFIG_TIMEOUT_DAYS)

    # Query for hiddify_accounts
    hiddify_accounts = HiddifyUser.objects.filter(
        Q(
            usage_limit_GB__isnull=False,  # Ensure usage_limit_GB is not null
            current_usage_GB__isnull=False,  # Ensure current_usage_GB is not null
            usage_limit_GB__lte=F('current_usage_GB') + settings.WARNING_FOR_USAGE_GB  # Difference is less than WARNING_FOR_USAGE_GB
        ) | Q(
            end_date__isnull=False,  # Ensure end_date exists
            end_date__lte=warning_for_config_timeout_days  # end_date is within WARNING_FOR_CONFIG_TIMEOUT_DAYS days
        )
    )

    for hiddify_account in hiddify_accounts:

        try:

            # get the users
            config = Config.objects.get(uuid=hiddify_account.uuid)

            # check if the config.user has an telegram_account or not
            if not config.user.telegram_account.exists():
                logger.warning(f"User {config.user} does not have a valid telegram_account.")
                continue
            
            telegram_account = Telegram_account.objects.get(user=config.user)

            # remind days
            remining_trafic = round(hiddify_account.usage_limit_GB - hiddify_account.current_usage_GB, 2)
            remind_days = (hiddify_account.end_date - timezone.now().date()).days
            update_link = settings.DOMAIN_NAME

            if remind_days < 0:
                message = f'🔴 <b>هشدار: اشتراک شما منقضی شده است!</b> 🔴\n\n👤 اکانت: {hiddify_account.name}\n\n⏳ زمان باقی مانده: <b>{remind_days} روز</b>\n\n📊 مصرف فعلی: <b>{round(hiddify_account.current_usage_GB, 2)} GB</b> از <b>{hiddify_account.usage_limit_GB} GB</b>\n\n🚦 ترافیک باقیمانده: <b>{remining_trafic} GB</b>\n\nبرای جلوگیری از قطعی، لطفاً روی <a href="{update_link}">لینک تمدید</a> کلیک کنید. 🙏'

            elif remining_trafic >= 10 :
                message = f'🔄 <b>یادآوری تمدید اشتراک</b> 🔄\n\n👤 اکانت: {hiddify_account.name}\n\n⏳ زمان باقی مانده: <b>{remind_days} روز</b>\n\nبرای جلوگیری از قطعی، لطفاً روی <a href="{update_link}">لینک تمدید</a> کلیک کنید. 🙏'            
            else:
                message = f'🔄 <b>یادآوری تمدید اشتراک</b> 🔄\n\n👤 اکانت: {hiddify_account.name}\n\n⏳ زمان باقی مانده: <b>{remind_days} روز</b>\n\n📊 مصرف فعلی: <b>{round(hiddify_account.current_usage_GB, 2)} GB</b> از <b>{hiddify_account.usage_limit_GB} GB</b>\n\n🚦 ترافیک باقیمانده: <b>{remining_trafic} GB</b>\n\nبرای جلوگیری از قطعی، لطفاً روی <a href="{update_link}">لینک تمدید</a> کلیک کنید. 🙏'                        
            
            # Send the warning message
            send_telegram_message(
                token=telegram_info.token,
                chat_id=telegram_account.telegram_user_id,
                message=message,
            )
            logger.info(f'Message sent to {config.user}')

        except Config.DoesNotExist:
            logger.error(f"No user found for uuid: {hiddify_account.uuid}")
            continue

        except Config.Telegram_account:
            logger.error(f"No telegram info found for uuid: {hiddify_account.uuid}")
            continue

        except Exception as e:
            logger.error(f'Error sending message: {str(e)}')
            add_admin_log(f'Error sending message: {str(e)} in tasks.py function : send_warning_message', 'user', config.user)
            continue
