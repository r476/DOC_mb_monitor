import telebot
from telebot import apihelper
from modbus.client import *
import csv, time, datetime

apihelper.proxy = {'https':'socks5://cx1b2j:E1caTT@186.65.117.60:9396'}
token = '827576612:AAEX0IHqMW5x-oWrh8T1ZXhE-9_K8pXMTJ0'
bot = telebot.TeleBot(token)

c = client(host="192.168.127.254", unit=6) 

@bot.message_handler(commands=['wtf'])
def send_welcome(message):
    try:
        data = c.read(FC=3, ADR=287, LEN=5)
        bot.reply_to(message, f'ГПГУ 1: {data[0]} кВт\nГПГУ 2: {data[1]} кВт\nГПГУ 3: {data[2]} кВт\nГПГУ 4: {data[3]} кВт\nГПГУ 5: {data[4]} кВт\nПолная мощность: {data[0] + data[1] + data[2] + data[3] + data[4]} кВт')
    except:
        bot.reply_to(message, 'Опрос не удался')
bot.polling()
