import telebot
import requests

token = '1298999210:AAHQXHgqW0y0A9kjCPB3XSeBZKDNrgmK9fY'
chat_id = 723253749
text = 'Проверка связи.'
url = f'https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={text}&parse_mode=Markdown'
try:
    r = requests.post(url)
    print(r)
except Exception as e:
    print(e)
