import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
 
from pprint import pprint
import time
import datetime
import json
 
 
TOKEN= #da sostituire
command={"login":' per autentificarsi,\n' '/login username pssw',
        "register":'per registrarsi,\n /register username pssw',
        "logout":'per scolleagrsi,\n /logout',
        "check":'per visualizzare i dati del sensore o da thingspeak,\n /check',
        "devices":'mostra la lista dei dispositivi a noi associati\n /devices',
        "changeDev":'per cambiare il device di riferimento,\n /changeDev id_Dispositivo'}

#--------------------
def commands(chat_id):
    for c in command:
        bot.sendMessage(chat_id, c)
#-------------------------------------------------------------------------------
def currentDevice(name):
    users=json.load(open('users.json'))
    for us in users['Users']:
        if us['username'] == name:
            return us["currentDevice"]

def printDevices(name):
    users=json.load(open('users.json'))
    for us in users['Users']:
        if us['username'] == name:
            return us["devices"]

def change(name,id):
    users=json.load(open('users.json'))
    for us in users['Users']:
        if us['username'] == name:
            us["currentDevice"]=id
            json.dump(users,open('users.json','w'))
#---------------------------------------------------------
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
#------------------------------------------------------------------------
def on_chat_message(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    if content_type=='text':
        chat_id=msg['chat']['id']
        name=msg["from"]["username"]
        txt=msg['text']
        bot.sendMessage(chat_id,'ciao caro {}'.format(name))
        if txt.startswith('/login'):
            try:
                params = txt.split()[1:]
                login(chat_id,params[0],params[1])
            except:
                bot.sendMessage(chat_id,"format /login username pssw")
        elif txt.startswith('/register'):
            try:
                 params = txt.split()[1:]
                 register(chat_id,params[0],params[1])
            except:
                 bot.sendMessage(chat_id,"format /register username pssw")
        elif txt.startswith('/logout'):
            logout(name)
            bot.sendMessage(chat_id,"sei uscito")
        elif txt.startswith('/check') and status(name):
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text='Dati', callback_data='datas')],
                [InlineKeyboardButton(text='ThingSpeak', callback_data='thingspeak')]])
            bot.sendMessage(chat_id, 'Cosa vuoi?', reply_markup=keyboard)
        elif txt.startswith('/devices'):
            bot.sendMessage(chat_id,printDevices(name))
        elif txt.startswith('/change'):
            params = txt.split()[1:]
            change(name,params[0])
        elif txt.startswith('/info'):
            try: 
                params = txt.split()[1:]
                bot.sendMessage(chat_id,command[params[0]])
            except:
                bot.sendMessage(chat_id," devi mettere /info comando ")
        else:
            bot.sendMessage(chat_id,"Elenco dei comandi disponibili: \n")
            commands(chat_id)
            
        #elif txt.startwith('/register'):
        #    register()

def on_callback_query(msg): # come premo ritornano cose 
    query_id, chat_ID, query_data = telepot.glance(msg, flavor='callback_query')
    name=msg["from"]["username"]
    id=currentDevice(name)
    if query_data=='temperatura':
        bot.sendMessage(chat_ID,text="La temperatura rilevata da  %s di 25°\n" %id)
    elif query_data=='c02':
        bot.sendMessage(chat_ID,text="La quantita di co2 rilevata da %s è di \n" %id)   
    elif query_data=='umidita':
        bot.sendMessage(chat_ID,text="L umidita rilevata da %s è di \n" %id)
    elif query_data=="thingspeak":
         keyboard = InlineKeyboardMarkup(inline_keyboard=[
             [InlineKeyboardButton(text='Temperatura_T', callback_data='temperatura')],
             [InlineKeyboardButton(text='C02_T', callback_data='c02')],
             [InlineKeyboardButton(text='Umidita_t', callback_data='umidita')]],)
         bot.sendMessage(chat_ID, 'Cosa vuoi?', reply_markup=keyboard)
    elif query_data=="datas":
         keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='Temperatura_R', callback_data='temperatura')],
            [InlineKeyboardButton(text='C02_R', callback_data='c02')],
            [InlineKeyboardButton(text='Umidita_R', callback_data='umidita')]],)
         bot.sendMessage(chat_ID, 'Cosa vuoi?', reply_markup=keyboard)
bot = telepot.Bot(TOKEN)
MessageLoop(bot, {'chat':on_chat_message, 'callback_query':on_callback_query}).run_as_thread()
print('Listening ...')

while 1:
    time.sleep(10)