import telebot
from telebot import apihelper
from modbus.client import *
import csv, time, datetime
from pandas.tseries.offsets import Hour, Minute, Day
import matplotlib.pyplot as plt

apihelper.proxy = {'https':'socks5://cx1b2j:E1caTT@186.65.117.60:9396'}
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
    df = pd.read_csv('data.csv', encoding='Windows-1251')
    df['Дата Время'] = pd.to_datetime(df['Дата Время'])
    df.index = pd.to_datetime(df['Дата Время'])

    data_mean = df.resample(mean_int).mean()
    data_sample = data_mean[data_mean.index[-1]-interval:]

    plt.figure(figsize=(15,15))
    plt.ylim([-1000, 7000])
    plt.ylabel('кВт')
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.plot(data_sample.index, data_sample['Мощность завода'], '-')
    plt.plot(data_sample.index, data_sample['MainsImport'], '-')
    plt.plot(data_sample.index, data_sample['Сумм мощность ГПГУ'], '-')
    plt.legend(['Завод', 'Импорт', 'ГПГУ'])
    plt.savefig('1.png')

@bot.message_handler(commands=['get_data_3hour'])
def send_data_3hour(message):
	make_graph('T', Hour(3))
	img = open('1.png', 'rb')
	bot.send_photo(message.from_user.id, img)

@bot.message_handler(commands=['get_data_12hour'])
def send_data_12hour(message):
	make_graph('2T', Hour(12))
	img = open('1.png', 'rb')
	bot.send_photo(message.from_user.id, img)

@bot.message_handler(commands=['get_data_24hour'])
def send_data_24hour(message):
	make_graph('2T', Hour(24))
	img = open('1.png', 'rb')
	bot.send_photo(message.from_user.id, img)

@bot.message_handler(commands=['get_data_3days'])
def send_data_3days(message):
	make_graph('2T', Day(3))
	img = open('1.png', 'rb')
	bot.send_photo(message.from_user.id, img)

@bot.message_handler(commands=['get_data_7days'])
def send_data_7days(message):
	make_graph('5T', Day(7))
	img = open('1.png', 'rb')
	bot.send_photo(message.from_user.id, img)

@bot.message_handler(commands=['get_data_14days'])
def send_data_14days(message):
	make_graph('5T', Day(14))
	img = open('1.png', 'rb')
	bot.send_photo(message.from_user.id, img)

@bot.message_handler(commands=['get_data_30days'])
def send_data_30days(message):
	make_graph('5T', Day(30))
	img = open('1.png', 'rb')
	bot.send_photo(message.from_user.id, img)
	
@bot.message_handler(commands=['wtf'])
def send_status(message):
    log_to_csv(message)
    data = get_data()
    if data:
        text = f"{datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\nГПГУ 1: {data['ГПГУ 1 ']} кВт\nГПГУ 2: {data['ГПГУ 2 ']} кВт\nГПГУ 3: {data['ГПГУ 3 ']} кВт\nГПГУ 4: {data['ГПГУ 4 ']} кВт\nГПГУ 5: {data['ГПГУ 5 ']} кВт\nMainsImport: {data['MainsImport']} кВт\nМощность завода: {data['Мощность завода']} кВт\nMWh: {data['MWh']}\nСумм мощность ГПГУ: {data['Сумм мощность ГПГУ']} кВт"
        bot.reply_to(message, text)

@bot.message_handler(commands=['get_csv'])
def send_csv(message):
    doc = open('data.csv', 'rb')
    bot.send_document(message.from_user.id, doc)

@bot.message_handler(commands=['get_syslog'])
def send_syslog(message):
    doc = open('syslog.log', 'rb')
    bot.send_document(message.from_user.id, doc)

@bot.message_handler(commands=['get_msglog'])
def send_msglog(message):
    doc = open('msglog.log', 'rb')
    bot.send_document(message.from_user.id, doc)

@bot.message_handler(func=lambda message: True)
def echo_msg(message):
	bot.send_message(723253749, f'Сообщение от {message.from_user.first_name}\n{message.from_user.id}\n{message.text}')

while True:
	try:
		bot.polling(none_stop=True, timeout=300)
	except:
		print('ой... ошибчк...')
