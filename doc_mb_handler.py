import telebot
from modbus.client import *
import csv, time, datetime
import pandas as pd
from pandas.tseries.offsets import Hour, Minute, Day
import matplotlib.pyplot as plt
from time import sleep

token = '1298999210:AAHQXHgqW0y0A9kjCPB3XSeBZKDNrgmK9fY'
bot = telebot.TeleBot(token)

def log_to_csv(message):
    date = datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')
    uid = message.from_user.id
    name = message.from_user.first_name
    text = message.text
    with open('syslog.log', 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([date, uid, name, text, ])

def number_sing(n):
    return (n-65535) if n & 0b1000000000000000 else n

def get_data():
    data_dict = {}
    try:
        c = client(host="192.168.127.254", unit=7) 
        gensets = c.read(FC=3, ADR=287, LEN=5)
        mains_import = c.read(FC=3, ADR=231, LEN=1)[0]
        object_p = c.read(FC=3, ADR=272, LEN=2)[1]
        mwh = c.read(FC=3, ADR=283, LEN=2)[1]
        tot_run_p_act = c.read(FC=3, ADR=339, LEN=2)[1]
        b_in = c.read(FC=3, ADR=2, LEN=1)[0]
        data_dict = {'Дата Время':datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S'), 
            'ГПГУ 1 ': number_sing(gensets[0]), 
            'ГПГУ 2 ': number_sing(gensets[1]), 
            'ГПГУ 3 ': number_sing(gensets[2]), 
            'ГПГУ 4 ': number_sing(gensets[3]), 
            'ГПГУ 5 ': number_sing(gensets[4]), 
            'MainsImport': number_sing(mains_import), 
            'Мощность завода': object_p, 
            'MWh': mwh, 
            'Сумм мощность ГПГУ': tot_run_p_act, 
            'BIN': b_in}
    except:
        print('Неудачная попытка опроса.')
        bot.reply_to(message, 'Опрос не удался')
    return data_dict

def make_graph(mean_int, interval):
    df = pd.read_csv('data.csv', parse_dates=['Дата Время'], index_col=['Дата Время'])

    data_mean = df.resample(mean_int).mean()
    data_sample = data_mean[data_mean.index[-1]-interval:]

    plt.figure(figsize=(12,6))
    plt.ylim([-1000, 7000])
    plt.ylabel('кВт')
#    plt.xticks(rotation=45)
    plt.grid(True)
    plt.plot(data_sample.index, data_sample['Мощность завода'], 'r-')
    plt.plot(data_sample.index, data_sample['Сумм мощность ГПГУ'], 'g-')
    plt.plot(data_sample.index, data_sample['MainsImport'], 'b-')
    plt.axhline(y=data_sample['Мощность завода'].mean(), alpha=0.5, color='r')
    plt.axhline(y=data_sample['MainsImport'].mean(), alpha=0.5, color='b')
    plt.axhline(y=data_sample['Сумм мощность ГПГУ'].mean(), alpha=0.5, color='g')
    plt.legend(['Завод', 'ГПГУ', 'Импорт'])
    plt.figtext(.13, .96, f'Средняя мощность завода на выбранном интервале: {round(data_sample["Мощность завода"].mean())} кВт')
    plt.figtext(.13, .93, f'Средняя мощность ГПГУ на выбранном интервале: {round(data_sample["Сумм мощность ГПГУ"].mean())} кВт.   Выработано {int(data_sample["MWh"][-1]-data_sample["MWh"][0])} кВт ч')
    plt.figtext(.13, .9, f'Средний импорт на выбранном интервале: {round(data_sample["MainsImport"].mean())} кВт')
    plt.savefig('1.png')

@bot.message_handler(commands=['get_data_3hour'])
def send_data_3hour(message):
    log_to_csv(message)
    make_graph('T', Hour(3))
    img = open('1.png', 'rb')
    bot.send_photo(message.from_user.id, img)

@bot.message_handler(commands=['get_data_12hour'])
def send_data_12hour(message):
    log_to_csv(message)
    make_graph('2T', Hour(12))
    img = open('1.png', 'rb')
    bot.send_photo(message.from_user.id, img)

@bot.message_handler(commands=['get_data_24hour'])
def send_data_24hour(message):
    log_to_csv(message)
    make_graph('2T', Hour(24))
    img = open('1.png', 'rb')
    bot.send_photo(message.from_user.id, img)

@bot.message_handler(commands=['get_data_3days'])
def send_data_3days(message):
    log_to_csv(message)
    make_graph('2T', Day(3))
    img = open('1.png', 'rb')
    bot.send_photo(message.from_user.id, img)

@bot.message_handler(commands=['get_data_7days'])
def send_data_7days(message):
    log_to_csv(message)
    make_graph('5T', Day(7))
    img = open('1.png', 'rb')
    bot.send_photo(message.from_user.id, img)

@bot.message_handler(commands=['get_data_14days'])
def send_data_14days(message):
    log_to_csv(message)
    make_graph('5T', Day(14))
    img = open('1.png', 'rb')
    bot.send_photo(message.from_user.id, img)

@bot.message_handler(commands=['get_data_30days'])
def send_data_30days(message):
    log_to_csv(message)
    make_graph('5T', Day(30))
    img = open('1.png', 'rb')
    bot.send_photo(message.from_user.id, img)
	
@bot.message_handler(commands=['wtf'])
def send_status(message):
    df = pd.read_csv('data.csv', parse_dates=['Дата Время'], index_col=['Дата Время'])[-10:]
    log_to_csv(message)
    text = f"*{datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')}*\n\n*ГПГУ 1: *{int(df['ГПГУ 1 '].mean())} кВт\n*ГПГУ 2: *{int(df['ГПГУ 2 '].mean())} кВт\n*ГПГУ 3: *{int(df['ГПГУ 3 '].mean())} кВт\n*ГПГУ 4: *{int(df['ГПГУ 4 '].mean())} кВт\n*ГПГУ 5: *{int(df['ГПГУ 5 '].mean())} кВт\n\n*Мощность завода: *{int(df['Мощность завода'].mean())} кВт\n*Сумм мощность ГПГУ: *{int(df['Сумм мощность ГПГУ'].mean())} кВт\n*Импорт: *{int(df['MainsImport'].mean())} кВт\n\n*MWh: *{df['MWh'][-1]}"
    bot.reply_to(message, text, parse_mode= "Markdown")

@bot.message_handler(commands=['get_csv'])
def send_csv(message):
    log_to_csv(message)
    doc = open('data.csv', 'rb')
    bot.send_document(message.from_user.id, doc)

@bot.message_handler(commands=['get_syslog'])
def send_syslog(message):
    log_to_csv(message)
    doc = open('syslog.log', 'rb')
    bot.send_document(message.from_user.id, doc)

@bot.message_handler(commands=['get_msglog'])
def send_msglog(message):
    log_to_csv(message)
    doc = open('msglog.log', 'rb')
    bot.send_document(message.from_user.id, doc)

@bot.message_handler(func=lambda message: True)
def echo_msg(message):
    log_to_csv(message)
    bot.send_message(723253749, f'Сообщение от {message.from_user.first_name}\n{message.from_user.id}\n{message.text}')

while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        sleep(5)
        print(e)
