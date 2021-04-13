import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
 
from pprint import pprint
import time
import datetime
import json
 
 
TOKEN="" #da sostituire
 
def on_chat_message(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    if content_type=='text':
         chat_id=msg['chat']['id']
         command=msg['text']
         if command=='/start':
             bot.sendMessage(chat_id, 'Ciao utente cosa vuoi? \n') 
         elif command=='/registrati':
             bot.sendMessage(chat_id, 'ti sei registrato nella stanza numero 25\n') 
         elif  command=='/dati':
             keyboard = InlineKeyboardMarkup(inline_keyboard=[
                 [InlineKeyboardButton(text='Temperatura', callback_data='temperatura')],
                 [InlineKeyboardButton(text='C02', callback_data='c02')],
                 [InlineKeyboardButton(text='Umidita', callback_data='umidita')]],)
             bot.sendMessage(chat_id, 'Cosa vuoi?', reply_markup=keyboard)
         else :
            bot.sendMessage(chat_id, 'unico comando che conosco è /start e /dati \n')

def on_callback_query(msg): # come premo ritornano cose 
    query_id, chat_ID, query_data = telepot.glance(msg, flavor='callback_query')
    print('Callback Query:', query_id, chat_ID, query_data)
    if query_data=='temperatura':
        bot.sendMessage(chat_ID,text="La temperatura nella stanza e di 25°\n")
    elif query_data=='c02':
        bot.sendMessage(chat_ID,text="La quantita di co2 e di \n")
    elif query_data=='umidita':
        bot.sendMessage(chat_ID,text="L umidita nella stanza è pari a \n")
 
bot = telepot.Bot(TOKEN)
MessageLoop(bot, {'chat':on_chat_message, 'callback_query':on_callback_query}).run_as_thread()
print('Listening ...')
while 1:
    time.sleep(10)
