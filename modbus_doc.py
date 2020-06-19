from modbus.client import *
import csv, time, datetime, telebot, json
import pandas as pd
from pandas.tseries.offsets import Hour, Minute, Day
import matplotlib.pyplot as plt

from time import sleep

with open('config.json', 'r') as f:
    jdata = json.load(f)

id_list = jdata['accepted_id']

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
        data_dict = {'Дата Время':datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
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
            bot.send_message(i, text, timeout)
            log_to_csv(text)
            print(text)
    except:
        print('Неудачная отправка сообщения')
        sleep(30)

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

def send_report(id_list):
    try:
        print(id_list)
        make_graph('2T', Hour(24))
        for i in id_list:
            print(f'Отправка отчета на id {i}')
            img = open('1.png', 'rb')
            bot.send_photo(i, img)
            sleep(10)
        with open('config.json', 'w') as f:
            jdata['report_today'] = True
            json.dump(jdata, f, indent=4)

    except Exception as e:
        print('\n\nНеудачная отправка send_report')
        print(e)
        sleep(10)

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
            
    if data_dict_old['BIN'] & 1 and not (data_dict_new['BIN'] & 1): # бит 1 с 1 на 0
        text = f'МСВ разомкнут, работаем в острове. {datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}'
        send_messages(id_list, text)

    if not (data_dict_old['BIN'] & 1) and data_dict_new['BIN'] & 1: # бит 1 с 0 на 1
        text = f'МСВ замкнут, работаем в нормальном режиме. {datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}'
        send_messages(id_list, text)

    # Отправка ежедневного отчёта
    if datetime.datetime.now().hour==17:
        with open('config.json', 'r') as f:
            jdata = json.load(f)
        if not jdata['report_today']:
            send_report(id_list)

    # Сброс маркера отчёта в полночь
    if datetime.datetime.now().hour==0:
        with open('config.json', 'r') as f:
            jdata = json.load(f)
        if jdata['report_today']:
            with open('config.json', 'w') as f:
                jdata['report_today'] = False
                json.dump(jdata, f, indent=4)

    to_csv(data_file, titles, data_dict_new)
    data_dict_old = data_dict_new
    time.sleep(10)
