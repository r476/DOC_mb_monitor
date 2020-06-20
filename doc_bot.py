from modbus.client import *
import csv, time, datetime, telebot, json, requests
import pandas as pd
from pandas.tseries.offsets import Hour, Minute, Day
import matplotlib.pyplot as plt 

def get_updates():
    updates_list =[]
    return_json = []

    with open('req.json', 'r') as f:
        updates = json.load(f)
        for u in updates['result']:
            updates_list.append(u['update_id'])
            
    method = 'getUpdates'
    r = requests.get(f'https://api.telegram.org/bot{token}/{method}')
            
    for u in r.json()['result']:
        if u['update_id'] not in updates_list:
            return_json.append(u)
        
    with open('req.json', 'w') as f:
        json.dump(r.json(), f, indent=4)
        
    return return_json

def get_id_list():
    with open('config.json', 'r') as f:
        return json.load(f)['accepted_id']
     
# определяю знак числа из модбас регистра
def number_sing(n):
    return (n-65535) if n & 0b1000000000000000 else n
    
# получаю данные с IM
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
        print('Неудачная попытка опроса IM.')
        sleep(10)
    return data_dict

# запись данных в CSV
def to_csv(data_file, order, data):
    with open(data_file, "a", newline='') as f:
        writer = csv.DictWriter(f, order)
        writer.writerow(data)

# запись в лог
def log_to_csv(text):
    with open('msglog.log', 'a', newline='') as f:
        f.write(text + '\n')

# рассылка сообщений по списку ID
def send_messages(id_list, text):
    try:
        for i in id_list:
            url = f'https://api.telegram.org/bot{token}/sendMessage?chat_id={i}&text={text}&parse_mode=Markdown'
            r= requests.post(url)
            log_to_csv(text)
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

# отправка отчета в виде графика с подписями
def send_report(id_list):
    try:
        make_graph('2T', Hour(24))
        for i in id_list:
            url = "https://api.telegram.org/bot827576612:AAEX0IHqMW5x-oWrh8T1ZXhE-9_K8pXMTJ0/sendPhoto"
            files = {'photo': open('1.png', 'rb')}
            data = {'chat_id' : i}
            requests.post(url, files=files, data=data)
            
        with open('config.json', 'r') as f:
            jdata = json.load(f)
            
        with open('config.json', 'w') as f:
            jdata['report_today'] = True
            json.dump(jdata, f, indent=4)

    except Exception as e:
        print('\n\nНеудачная отправка send_report\n\n')
        print(e)
        sleep(10)
        
# отправка изображений
def send_photo(id_list, text):
    try:
        for i in id_list:
            url = f'https://api.telegram.org/bot{token}/sendMessage?chat_id={i}&text={text}'
            r= requests.post(url)
            log_to_csv(text)
    except:
        print('Неудачная отправка сообщения')
        sleep(30)
        
def reset_report_marker():
    with open('config.json', 'r') as f:
        jdata = json.load(f)
    if jdata['report_today']:
        with open('config.json', 'w') as f:
            jdata['report_today'] = False
            json.dump(jdata, f, indent=4)
            
def is_report_marker_on():
    with open('config.json', 'r') as f:
        jdata = json.load(f)
        return False if not jdata['report_today'] else True
    
def handler_updates(message):
    message_id = message['message']['from']['id']
    text = message['message']['text']
    print(message_id)
    print(text)
    if text == '/wtf':
        log_to_csv(str(message))
        df = pd.read_csv(data_file, parse_dates=['Дата Время'], index_col=['Дата Время'])[-5:]
        text = f"*{datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')}*\n\n*ГПГУ 1: *{int(df['ГПГУ 1 '].mean())} кВт\n*ГПГУ 2: *{int(df['ГПГУ 2 '].mean())} кВт\n*ГПГУ 3: *{int(df['ГПГУ 3 '].mean())} кВт\n*ГПГУ 4: *{int(df['ГПГУ 4 '].mean())} кВт\n*ГПГУ 5: *{int(df['ГПГУ 5 '].mean())} кВт\n\n*Мощность завода: *{int(df['Мощность завода'].mean())} кВт\n*Сумм мощность ГПГУ: *{int(df['Сумм мощность ГПГУ'].mean())} кВт\n*Импорт: *{int(df['MainsImport'].mean())} кВт\n\n*MWh: *{df['MWh'][-1]}"
        print(text)
        send_messages([message_id], text)

id_list = [723253749] #get_id_list()

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

#token = '1298999210:AAHQXHgqW0y0A9kjCPB3XSeBZKDNrgmK9fY'
token = '827576612:AAEX0IHqMW5x-oWrh8T1ZXhE-9_K8pXMTJ0'
data_file = "data.csv"

# блок кода для инициации файла csv
#with open(data_file, 'w') as f:
#    writer = csv.writer(f)
#    writer.writerow(titles)

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
        if not is_report_marker_on():
            send_report(id_list)

    # Сброс маркера отчёта в полночь
    if datetime.datetime.now().hour==0:
        if is_report_marker_on():
            reset_report_marker()

    to_csv(data_file, titles, data_dict_new)
    data_dict_old = data_dict_new
    
    #обработка telegram запросов 
    updates = get_updates()
    if updates:
        for message in updates:
            handler_updates(message)
    
    time.sleep(10)
