import base64
import logging
import re
import urllib.parse
from datetime import date
from io import BytesIO

import qrcode
import requests
from django.conf import settings
from client_actions.models import Config
from task_manager.models import HiddifyUser


logger = logging.getLogger(__name__)


def generate_qr_code(link='https://example.com'):
    # Create QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=0,
    )

    # Data to encode
    data = link
    qr.add_data(data)
    qr.make(fit=True)

    # Generate the QR code image
    img = qr.make_image(fill_color="#313131", back_color="white")

    # Convert the image to bytes
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    # Convert to base64
    img_base64 = base64.b64encode(buffer.getvalue()).decode()

    return img_base64


def get_users(hiddify_api_key,
              panel_admin_domain,
              admin_proxy_path):
    

    # Fetch data from external API
    headers = {
        'Accept': 'application/json',
        'Hiddify-API-Key': hiddify_api_key
    }
    url = f'{panel_admin_domain}/{admin_proxy_path}/api/v2/admin/user/'

    try:
        response = requests.get(url=url, headers=headers)

        if response.ok:
            data = response.json()  # Assuming JSON response

            if not data:
                logger.info("No data fetched.")
                return "No data fetched."

            logger.info("Data fetched successfully.")
            return data
        else:
            logger.error(f"Failed to fetch data from API: {response.text}")
            return False

    except Exception as e:
        logger.error(f"Error fetching data from API: {e}")
        return False


def update_user(uuid, days, trafic,
                hiddify_api_key,
                admin_proxy_path,
                panel_admin_domain,
                ):

    url = f'{panel_admin_domain}/{admin_proxy_path}/api/v2/admin/user/{uuid}/'
    # Fetch data from external API
    headers = {
        'Content-Type': "application/json",
        'Accept': 'application/json',
        'Hiddify-API-Key': hiddify_api_key
    }

    data = {
        "current_usage_GB": 0,
        "package_days": days,
        "start_date": date.today().isoformat(),
        "usage_limit_GB": trafic,
        "enable": True,
        "wg_pk": "string",
        "wg_psk": "string",
        "wg_pub": "string",
    }

    try:
        response = requests.patch(url=url, headers=headers, json=data)
        if response.ok:
            logger.info(f"User {uuid} updated successfully.")
            return True
        else:
            logger.error(f"Failed to update user {uuid}.")
            return False

    except Exception as e:
        logger.error(f"Error updating user {uuid}: {e}")
        return False


def add_new_user(name, duration, trafic,
                 hiddify_api_key,
                 admin_proxy_path,
                 panel_admin_domain,
                 ):

    url = f'{panel_admin_domain}/{admin_proxy_path}/api/v2/admin/user/'

    headers = {
        'Accept': 'application/json',
        'Hiddify-API-Key': hiddify_api_key
    }

    data = {
        "enable": True,
        "is_active": True,
        "mode": "no_reset",
        "name": name,
        "package_days": duration,
        "usage_limit_GB": trafic,
        "wg_pk": "string",
        "wg_psk": "string",
        "wg_pub": "string"
    }

    response = requests.post(url=url, headers=headers, json=data)

    if response.ok:
        logger.info(f"User {name} added successfully.")
        response_data = response.json()
        return response_data
    else:
        logger.error(f"Failed to add user {name}.")
        return False


def on_off_user(uuid, enable=True,
                hiddify_api_key=None,
                admin_proxy_path=None,
                panel_admin_domain=None,
                ):
    
    if not hiddify_api_key or not admin_proxy_path or not panel_admin_domain:
        logger.error("Error disabling user due to missing hiddify arguments")
        return False
        

    url = f'{panel_admin_domain}/{admin_proxy_path}/api/v2/admin/user/{uuid}/'

    headers = {
        'Accept': 'application/json',
        'Hiddify-API-Key': hiddify_api_key
    }

    data = {
        "enable": enable,
        "is_active" : enable,
        "wg_pk": "string",
        "wg_psk": "string",
        "wg_pub": "string",
    }

    try:
        response = requests.patch(url=url, headers=headers, json=data)

        if response.ok:
            
            logger.info(f"User {uuid} disabled successfully.")
            return True
        
        else:
            logger.error(f"Failed to disable user {uuid}.")
            return False
    except Exception as e:
        logger.error(f"Error disabling user {uuid}: {e}")
        return False


def delete_user(uuid,
                hiddify_api_key=None,
                admin_proxy_path=None,
                panel_admin_domain=None,
                ):


    if not hiddify_api_key or not admin_proxy_path or not panel_admin_domain:
        logger.error("Error deleting user due to missing hiddify arguments")
        return False
        

    url = f'{panel_admin_domain}/{admin_proxy_path}/api/v2/admin/user/{uuid}/'

    headers = {
        'Accept': 'application/json',
        'Hiddify-API-Key': hiddify_api_key
    }

    try:
        response = requests.delete(url=url, headers=headers)

        if response.ok:
            
            try:
                hiddify_user = HiddifyUser.objects.get(uuid=uuid)
                hiddify_user.delete()
            except HiddifyUser.DoesNotExist:
                logger.error(f"HiddifyUser with uuid {uuid} does not exist.")
               
            logger.info(f"User {uuid} deleted successfully.")
            return True
        else:
            logger.error(f"Failed to delete user {uuid}.")
            return False
    except Exception as e:
        logger.error(f"Error deleting user {uuid}: {e}")
        return False


def extract_uuid_from_url(url: str) -> str:
    # Pattern to match a UUID in the URL
    uuid_pattern = re.compile(r'([0-9a-fA-F-]{36})')
    # Search for the UUID in the URL
    uuid_match = uuid_pattern.search(url)
    # Return the extracted UUID if found, else None
    return uuid_match.group(1) if uuid_match else None


def send_telegram_message(token, chat_id, message):
    try:
        encoded_message = urllib.parse.quote_plus(message)
        url = f'https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={encoded_message}&parse_mode=HTML'
        response = requests.get(url)
        return response.ok
    except Exception as e:
        logger.error(f"Error sending Telegram message: {e}")
        return False
