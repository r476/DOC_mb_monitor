from modbus.client import *
import csv, time, datetime, telebot
from telebot import apihelper
from time import sleep

id_list = [723253749, 
           1036253569]

titles = ['Дата Время', 
          'ГПГУ 1 ', 
          'ГПГУ 2 ', 
          'ГПГУ 3 ', 
          'ГПГУ 4 ', 
          'ГПГУ 5 ', 
          'MainsImport', 
          'Мощность завода', 
          'MWh', 
          'Сумм мощность ГПГУ', 
          'BIN']

apihelper.proxy = {'https':'socks5://cx1b2j:E1caTT@186.65.117.60:9396'}
token = '1298999210:AAHQXHgqW0y0A9kjCPB3XSeBZKDNrgmK9fY'
bot = telebot.TeleBot(token)

data_file = "data.csv"

#with open(data_file, 'w') as f:
#    writer = csv.writer(f)
#    writer.writerow(titles)

# определяю знак числа
def number_sing(n):
    return (n-65535) if n & 0b1000000000000000 else n

# получаю данные
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
        sleep(30)
    return data_dict

def to_csv(data_file, order, data):
    with open(data_file, "a", newline='') as f:
        writer = csv.DictWriter(f, order)
        writer.writerow(data)

def log_to_csv(text):
   with open('msglog.log', 'a', newline='') as f:
        f.write(text + '\n')

def send_messages(id_list, text):
    try:
        for i in id_list:
            bot.send_message(i, text)
            log_to_csv(text)
            print(text)
    except:
        print('Неудачная отправка сообщения')
        sleep(30)
  
data_dict_old = get_data()

# Основной цикл
while True:
    data_dict_new = get_data() if get_data() else data_dict_old # если данные не получены, то оставляю старые значения 
    
    for k in ['ГПГУ 1 ', 'ГПГУ 2 ', 'ГПГУ 3 ', 'ГПГУ 4 ', 'ГПГУ 5 ']:
        if data_dict_old[k] > 0 and data_dict_new[k] <= 0:
            text = f'{k} остановлена {datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}'
            send_messages(id_list, text)
         
        if data_dict_old[k] <= 0 and data_dict_new[k] > 0:
            text = f'{k} включена в работу {datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}'
            send_messages(id_list, text)
            
    if data_dict_old['BIN'] != data_dict_new['BIN']:
        text = f'Похоже, что отработал МСВ. {datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}'
        send_messages(id_list, text)
            
    to_csv(data_file, titles, data_dict_new)
    data_dict_old = data_dict_new
    time.sleep(5)
