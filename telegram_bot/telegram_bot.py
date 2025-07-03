import telebot
import requests
import re
import logging
import os

# Get or create a logger
logger = logging.getLogger(__name__)

# Get the Telegram bot info
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', False)
SSL_DOMAIN = os.environ.get('SSL_DOMAIN', False)

if not TOKEN or not SSL_DOMAIN:
    logger.error('No Telegram bot info found in the environment variables!')
    raise Exception('No Telegram bot info found in the environment variables!')

SSL_DOMAIN = SSL_DOMAIN.strip()
# Token of the Telegram bot
bot = telebot.TeleBot(TOKEN.strip())

# Handle the /start command
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user = message.from_user
    bot_info = bot.get_me()
    bot_name = bot_info.first_name

    params = message.text.split()
    print(params)
    
    if len(params) > 1:
        uuid = extract_uuid(params[1])
        if uuid:
            
            bot.reply_to(message, f"سلام {user.first_name} به ربات {bot_name} خوش اومدی 👋")
        
            # data that will be sent to the server
            data = {
                'message': {
                    'from': {
                        'uuid': uuid,
                        'telegram_id': user.id,
                        'username': user.username,
                        'first_name': user.first_name,
                        'last_name': user.last_name
                    }
                }
            }
            logger.error(f'data : {data}')
            try:
                # Send data to the server
                response = requests.post(
                    f'{SSL_DOMAIN}/telegram-bot/telegram-webhook/',
                    json=data,
                    timeout=15,
                    headers={'content-type': 'application/json'}
                )
                response.raise_for_status()
                
                # Parse server response
                server_response = response.json()
                if server_response.get('status') == 'success':
                    bot.send_message(message.chat.id, "ربات شما با موفقیت فعال شد 😍")
                else:
                    logger.error(f"Server returned error: {server_response}")
                    bot.send_message(message.chat.id, "خطا در ثبت اطلاعات. لطفاً بعداً تلاش کنید.")
            except requests.exceptions.Timeout:
                logger.error("Request timed out while sending data to the server.")
                bot.send_message(message.chat.id, "ارتباط با سرور بیش از حد طول کشید 😕 لطفا دوباره تلاش کنید.")
            except requests.exceptions.ConnectionError:
                logger.error("Connection error occurred while sending data to the server.")
                bot.send_message(message.chat.id, "ارتباط با سرور برقرار نشد. لطفا بعداً تلاش کنید.")
            except requests.exceptions.HTTPError as e:
                logger.error(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
                bot.send_message(message.chat.id, "خطای سرور رخ داده است. لطفاً مجدداً امتحان کنید.")
            except requests.exceptions.RequestException as e:
                logger.error(f"Error sending data to server: {e}")
                bot.send_message(message.chat.id, "ارسال اطلاعات با مشکل مواجه شد 🥲\nلطفا دوباره از طریق سایت اقدام کنید 🙏")

    else:
        bot.send_message(message.chat.id, "لطفا از طریق سایت اقدام کنید 🙏")

# Extract the UUID from the URL   
def extract_uuid(url: str) -> str:
    # Pattern to match a UUID in the URL
    uuid_pattern = re.compile(r'([0-9a-fA-F-]{36})')
    # Search for the UUID in the URL
    uuid_match = uuid_pattern.search(url)
    # Return the extracted UUID if found, else None
    return uuid_match.group(1) if uuid_match else None  

if __name__ == '__main__':
    logger.info('Telegram bot is running...')
    bot.polling()
