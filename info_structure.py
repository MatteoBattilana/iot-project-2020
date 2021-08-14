import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from Telegram_Manager import Telegram_Manager
 
from pprint import pprint
import time
import datetime
import json
 
 
TOKEN="" #da sostituire
#-------------------
#-------------------------------------------------
def on_chat_message(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    if content_type=='text':
        chat_id=msg['chat']['id'] #chat_id identification
        name=msg["from"]["username"] #account name
        txt=msg['text'] #message sended
        bot.sendMessage(chat_id,'Hello  {}'.format(name))
        
        #description of different commands
        if txt.startswith('/login'):
            try:
                params = txt.split()[1:]
                t_m.login(chat_id,params[0],params[1])
                bot.deleteMessage(telepot.message_identifier(msg)) #delites the message once registered
            except:
                bot.sendMessage(chat_id,"format /login username pssw")
        
        elif txt.startswith('/register'):
            try:
                params = txt.split()[1:]
                t_m.register(chat_id,params)
            except:
                bot.sendMessage(chat_id,"format /register username pssw")

           
        elif txt.startswith('/logout'):
            t_m.logout(name)
            bot.sendMessage(chat_id,"logout")
        
        elif txt.startswith('/check') and t_m.status(name):
            groupIds=t_m.get_ids(chat_id)
            kbs=t_m.build_keyboard(groupIds,'groupId')
            keyboard = keyboard = InlineKeyboardMarkup(inline_keyboard=[[x] for x in kbs])
            bot.sendMessage(chat_id,"scegli",reply_markup=keyboard)
        
        elif txt.startswith('/IdAdd')  and t_m.status(name):
      
                params = txt.split()[1:]
                t_m.add_id(chat_id,params[0:])
         
        elif txt.startswith('/SenAdd')  and t_m.status(name):
            try:
                params = txt.split()[1:]
                t_m.add_sen(chat_id,params[0],params[1],params[2])
            except:
                bot.sendMessage(chat_id,"/SenAdd groupId nameSen Pin")
    
        elif txt.startswith('/SenDel')  and t_m.status(name):
            try:   
                 params = txt.split()[1:]
                 t_m.del_sen(chat_id,params[0],params[1:])
            except:
                bot.sendMessage(chat_id,"/SenDel groupId nameSen")
           

        elif txt.startswith('/IdDel')  and t_m.status(name):   
             try:
                 params = txt.split()[1:]
                 t_m.del_id(chat_id,params[0:])
             except:
                 bot.sendMessage(chat_id,"/IdDel groupId ")

        elif txt.startswith('/info'):
                params = txt.split()
                for i in t_m.commands(chat_id):
                    bot.sendMessage(chat_id,i)
            

def on_callback_query(msg): # come premo ritornano cose 
    query_id, chat_ID, query_data = telepot.glance(msg, flavor='callback_query')
    txt=query_data.split()
    if txt[0]=='groupId':
        id_sensor=t_m.get_sensors(chat_ID,txt[1])
        kbs=t_m.build_keyboard(id_sensor,'sensors')
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[x] for x in kbs])
        bot.sendMessage(chat_ID,"scegli",reply_markup=keyboard)
    #vedi come cambiare queste , build_keyboard(['datas','graph'],sens_rif)
    elif txt[0]=='sensors':
        kbs=t_m.build_keyboard(['datas','thingspeak'],txt[1])
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[x] for x in kbs])
        bot.sendMessage(chat_ID,"scegli",reply_markup=keyboard)
    #sens rif, data 
    #build[temperatura,co2,umidita],'sensor tipologia)
    elif (txt[1]=='datas' or txt[1]=='thingspeak'): #contorta ma funziona,query=(id_sensore cosaVoglio) 
        txt.reverse()
        kbs=t_m.build_keyboard(['temperatura','c02','umidita'],txt[0]+' '+txt[1])
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[x] for x in kbs])
        bot.sendMessage(chat_ID,"scegli",reply_markup=keyboard)
    #questo si potrebbe chiudere in poche righe,magari capendo come vanno le richieste
    elif txt[2]=='temperatura':
        if txt[0]=='datas':
            bot.sendMessage(chat_ID,text="hai richiesto La temperatura di %s" %txt[1])
            #qui dovro mettere la richiesta get per accedere ai dati reali
        else:
            #qui richiesta get per richiedere il grafico a thigspeak
            bot.sendPhoto(chat_ID,'https://cdn.getyourguide.com/img/location/5a0838201565b.jpeg/92.jpg')#mandare foto
            bot.sendMessage(chat_ID,text="grafico temperatura di %s \n" %txt[1]) 
    elif txt[2]=='c02':
        if txt[0]=='datas':
            bot.sendMessage(chat_ID,text="hai richiesto la co2 di %s\n" %txt[1]) 
        else:
            bot.sendPhoto(chat_ID,'https://www.milanretreats.com/wp-content/uploads/2020/01/milanretreats_img_slide.jpg')
            bot.sendMessage(chat_ID,text="grafico c02 di %s \n" %txt[1]) 
    elif txt[2]=='umidita':
        if txt[0]=='datas':
            bot.sendMessage(chat_ID,text="hai richiesto umidita di %s" %txt[1])
            #qui dovro mettere la richiesta get per accedere ai dati reali
        else:
            #qui richiesta get per richiedere il grafico a thigspeak
            bot.sendPhoto(chat_ID,'https://images.lacucinaitaliana.it/wp-content/uploads/2018/05/18183720/roma-primavera-1600x800.jpg')#mandare foto
            bot.sendMessage(chat_ID,text="grafico umidita di %s \n" %txt[1]) 
    
           
bot = telepot.Bot(TOKEN)
t_m=Telegram_Manager('users.json')
MessageLoop(bot, {'chat':on_chat_message, 'callback_query':on_callback_query}).run_as_thread()
print('Listening ...')

while 1:
    #qui si puo mettere il richiamo della control strategi con periodicita messa nel sleep
    # poi richiamare il onMessage con un messaggio prestabilito  
    time.sleep(10)



#https://en-unnoobcomeme.blogspot.com/2017/07/usare-un-bot-telegram-per-ricevere-dati.html
#