﻿import telebot
from telebot import apihelper
from modbus.client import *
import csv, time, datetime

apihelper.proxy = {'https':'socks5://cx1b2j:E1caTT@186.65.117.60:9396'}
token = '1298999210:AAHQXHgqW0y0A9kjCPB3XSeBZKDNrgmK9fY'
bot = telebot.TeleBot(token)

def get_data():
    try:
        c = client(host="192.168.127.254", unit=7) 
        gensets = c.read(FC=3, ADR=287, LEN=5)
        mains_import = c.read(FC=3, ADR=231, LEN=1)[0]
        object_p = c.read(FC=3, ADR=272, LEN=2)[1]
        mwh = c.read(FC=3, ADR=283, LEN=2)[1]
        tot_run_p_act = c.read(FC=3, ADR=339, LEN=2)[1]
        b_in = c.read(FC=3, ADR=2, LEN=1)[0]
        data_dict = {'Дата Время':datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S'), 
            'ГПГУ 1 ': gensets[0], 
            'ГПГУ 2 ': gensets[1], 
            'ГПГУ 3 ': gensets[2], 
            'ГПГУ 4 ': gensets[3], 
            'ГПГУ 5 ': gensets[4], 
            'MainsImport': mains_import, 
            'Мощность завода': object_p, 
            'MWh': mwh, 
            'Сумм мощность ГПГУ': tot_run_p_act, 
            'BIN': b_in}
    except:
        print('Неудачная попытка опроса.')
    return data_dict

@bot.message_handler(commands=['wtf'])
def send_status(message):
    try:
        data = get_data()
        text = f"{datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\nГПГУ 1: {data['ГПГУ 1 ']} кВт\nГПГУ 2: {data['ГПГУ 2 ']} кВт\nГПГУ 3: {data['ГПГУ 3 ']} кВт\nГПГУ 4: {data['ГПГУ 4 ']} кВт\nГПГУ 5: {data['ГПГУ 5 ']} кВт\nMainsImport: {data['MainsImport']} кВт\nМощность завода: {data['Мощность завода']} кВт\nMWh: {data['MWh']}\nСумм мощность ГПГУ: {data['Сумм мощность ГПГУ']} кВт"
        bot.reply_to(message, text)
    except:
        bot.reply_to(message, 'Опрос не удался')

bot.polling(none_stop=True, timeout=300)
