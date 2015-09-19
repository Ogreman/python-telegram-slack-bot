import os
import logging
import telegram
import requests
import time

LAST_UPDATE_ID = None
TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
SLACK_TOKEN = os.environ['SLACK_TOKEN']
SLACK_SUB = os.environ['SLACK_SUB']
SLACK_URL = "https://{slack}.slack.com/services/hooks/slackbot?token={token}&channel=%23{channel}"
SLACK_CHANNEL = os.environ.get('SLACK_CHANNEL', 'chat')
OTHER_BOT_REG = "{url}/register".format(url=os.environ['OTHER_BOT_URL'])
OTHER_BOT_USR = "{url}/users".format(url=os.environ['OTHER_BOT_URL'])
USER_NAMES = []
FORMAT = "%(asctime)-15s: %(levelname)s: %(message)s"


logging.basicConfig(format=FORMAT, filename="t2s.log", level=logging.INFO)


def main():
    global LAST_UPDATE_ID

    # Telegram Bot Authorization TELEGRAM_TOKEN
    bot = telegram.Bot(TELEGRAM_TOKEN)

    # This will be our global variable to keep the latest update_id when requesting
    # for updates. It starts with the latest update_id if available.
    try:
        LAST_UPDATE_ID = bot.getUpdates()[-1].update_id
    except IndexError:
        LAST_UPDATE_ID = None

    while True:
        try:
            echo_to_slack(bot)
        except Exception as e:
            logging.exception('Unhandled exception: %s', str(e))
        time.sleep(0.4)


def echo_to_slack(bot):
    global LAST_UPDATE_ID
    global SLACK_CHANNEL
    global USER_NAMES

    try:
        USER_NAMES = requests.get(OTHER_BOT_USR).json().get('users', [])
    except requests.exceptions.ConnectionError:
        logging.error('Failed to connect to: %s', OTHER_BOT_USR)

    # Request updates after the last updated_id
    for update in bot.getUpdates(offset=LAST_UPDATE_ID, timeout=10):
        chat_id = update.message.chat_id
        message = update.message.text.encode('utf-8')
        user = update.message.from_user.username

        if message:
            if message.startswith('/channel') and user in USER_NAMES:
                SLACK_CHANNEL = message.split(' ')[1].lower()
                bot.sendMessage(chat_id=chat_id, text="Channel set to %s" % SLACK_CHANNEL)
            elif message.startswith('/register'):
                user_id = update.message.from_user.id
                try:
                    response = requests.post(
                        OTHER_BOT_REG,
                        data=dict(
                            username=user,
                            id=user_id
                        )
                    )
                    if response.ok:
                        logging.info('User registered: %s', user)
                        bot.sendMessage(chat_id=chat_id, text="Registered with my pal.")
                except requests.exceptions.ConnectionError:
                    logging.error('Failed to connect to: %s', OTHER_BOT_REG)
                    bot.sendMessage(chat_id=chat_id, text="Something went wrong...")
            elif user in USER_NAMES:
                try:
                    response = requests.post(
                        SLACK_URL.format(
                            slack=SLACK_SUB, 
                            token=SLACK_TOKEN,
                            channel=SLACK_CHANNEL
                        ), 
                        data="`{username} via Telegram:` {message}"
                        .format(
                            message=message,
                            username=user
                        )
                    )
                    if response.ok:
                        bot.sendMessage(chat_id=chat_id, text="Sent!")
                except requests.exceptions.ConnectionError:
                    logging.error('Failed to connect to: %s', SLACK_URL)
                    bot.sendMessage(chat_id=chat_id, text="Something went wrong...")
            elif user not in USER_NAMES:
                logging.error('Unregistered user: %s', user)
                bot.sendMessage(chat_id=chat_id, text="Register first...")

            # Updates global offset to get the new updates
            LAST_UPDATE_ID = update.update_id + 1


if __name__ == '__main__':
    main()