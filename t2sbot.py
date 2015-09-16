import os
import logging
import telegram
import requests


LAST_UPDATE_ID = None
USER_NAMES = [
    val
    for key, val in os.environ.items()
    if key.startswith('USER_NAME')
]
TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
SLACK_TOKEN = os.environ['SLACK_TOKEN']
SLACK_SUB = os.environ['SLACK_SUB']
SLACK_URL = "https://{slack}.slack.com/services/hooks/slackbot?token={token}&channel=%23{channel}"
SLACK_CHANNEL = os.environ.get('SLACK_CHANNEL', 'chat')


def main():
    global LAST_UPDATE_ID

    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Telegram Bot Authorization TELEGRAM_TOKEN
    bot = telegram.Bot(TELEGRAM_TOKEN)

    # This will be our global variable to keep the latest update_id when requesting
    # for updates. It starts with the latest update_id if available.
    try:
        LAST_UPDATE_ID = bot.getUpdates()[-1].update_id
    except IndexError:
        LAST_UPDATE_ID = None

    while True:
        echo_to_slack(bot)


def echo_to_slack(bot):
    global LAST_UPDATE_ID
    global SLACK_CHANNEL

    # Request updates after the last updated_id
    for update in bot.getUpdates(offset=LAST_UPDATE_ID, timeout=10):
        chat_id = update.message.chat_id
        message = update.message.text.encode('utf-8')
        user = update.message.from_user.username

        if message and user in USER_NAMES:
            if message.startswith('/channel'):
                SLACK_CHANNEL = message.split(' ')[1].lower()
                bot.sendMessage(chat_id=chat_id, text="Channel set to %s" % SLACK_CHANNEL)
            else:
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
                    bot.sendMessage(chat_id=chat_id, text="Something went wrong...")

            # Updates global offset to get the new updates
            LAST_UPDATE_ID = update.update_id + 1


if __name__ == '__main__':
    main()