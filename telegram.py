import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
 
from pprint import pprint
import time
import datetime
import json
 
 
TOKEN="" #da sostituire
 
def logout(name):
    users=json.load(open('users.json'))
    for us in users['Users']:
            if us['username'] == name:
                us['status']= 'off'
                json.dump(users,open('users.json','w'))   

def status(name):
    users=json.load(open('users.json'))['Users']
    for us in users:
         if us['username']==name and us['status']== "on":
             return True
    return False

def register(name,pssw):
    users=json.load(open('users.json'))
    us={"username":name,"password":pssw,"status":"off"}
    users["Users"].append(us)
    json.dump(users,open('users.json','w'))  

def login(chat_id,name,pssw):
    users=json.load(open('users.json'))
    for us in users['Users']:
            if us['username'] == name and us['password']==pssw :
                us['status']= 'on'
                bot.sendMessage(chat_id,"sei registrato")
                json.dump(users,open('users.json','w'))   
                return True
    bot.sendMessage(chat_id,"errore nella compilazione")
    return False

def on_chat_message(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    if content_type=='text':
        chat_id=msg['chat']['id']
        name=msg["from"]["username"]
        txt=msg['text']
        bot.sendMessage(chat_id,'ciao caro {}'.format(name))
        if txt.startswith('/login'):
            params = txt.split()[1:]
            login(chat_id,params[0],params[1])
        elif txt.startswith('/register'):
            params = txt.split()[1:]
            register(chat_id,params[0],params[1])
        elif txt.startswith('/check') and status(name):
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text='Temperatura', callback_data='temperatura')],
                [InlineKeyboardButton(text='C02', callback_data='c02')],
                [InlineKeyboardButton(text='Umidita', callback_data='umidita')]],)
            bot.sendMessage(chat_id, 'sei on , puoi controllare', reply_markup=keyboard)
        elif txt.startswith('/logout'):
            logout(name)
            bot.sendMessage(chat_id,"sei uscito")
        else:
            bot.sendMessage(chat_id,"comando non riconosciuto, l unici comandi che son disponibili sono /login /logout /check /register")
        #elif txt.startwith('/register'):
        #    register()

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
