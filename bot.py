import requests
from time import sleep
import telegram
import os
import logging
import traceback

logger = logging.getLogger(__file__)


class TelegramLogsHandler(logging.Handler):

    def __init__(self, tg_bot, chat_id):
        super().__init__()
        self.chat_id = chat_id
        self.tg_bot = tg_bot

    def emit(self, record):
        message = self.format(record)
        self.tg_bot.send_message(chat_id=self.chat_id, text=message)


def main():
    # API токен Devman
    devman_api_key = os.environ['DEVMAN_API_KEY']

    # API токен telegram, можно получить, написав @BotFather
    tg_api_key = os.environ['TG_API_KEY']

    # ID Пользователя, которому будут приходить уведомления,
    # можно узнать, написав @userinfobot
    user_id = os.environ['TG_USER_ID']

    url = 'https://dvmn.org/api/long_polling/'

    header = {
        'Authorization': f'Token {devman_api_key}'
    }

    params = dict()

    timeout_secs = 100

    bot = telegram.Bot(token=tg_api_key)

    logger.setLevel(logging.INFO)

    logger.addHandler(TelegramLogsHandler(bot, user_id))


    while True:
        try:
            lesson_checking_response = requests.get(url,
                                                    headers=header,
                                                    params=params,
                                                    timeout=timeout_secs)
            lesson_checking_response.raise_for_status()
            checked_lessons = lesson_checking_response.json()

            if checked_lessons['status'] == 'timeout':
                params['timestamp'] = checked_lessons['timestamp_to_request']

            elif checked_lessons['status'] == 'found':
                lesson_url = checked_lessons['new_attempts'][0]['lesson_url']
                lesson_title = checked_lessons['new_attempts'][0]["lesson_title"]

                message_linked_part = f'<a href="{lesson_url}"> {lesson_title} </a>'

                if checked_lessons['new_attempts'][0]['is_negative']:
                    result_part_of_message = 'Работу не зачли, требуются улучшения.'
                else:
                    result_part_of_message = 'Работу приняли! Можно ' \
                                             'приступать к следующему уроку.'

                message = f'Урок на Девмане {message_linked_part} проверен. \n' \
                          f'{result_part_of_message}'

                bot.send_message(text=message,
                                 chat_id=user_id,
                                 parse_mode=telegram.ParseMode.HTML)

        except requests.exceptions.ReadTimeout:
            continue

        except requests.exceptions.ConnectionError:
            sleep(60)
            continue

        except Exception:
            logger.info(f'Бот Упал :(\nОшибка:')
            logger.exception(traceback.format_exc())



if __name__ == '__main__':
    main()


