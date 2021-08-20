import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from Telegram_Manager import Telegram_Manager
 
from pprint import pprint
import time
import datetime
import json

TOKEN="1916702576:AAEX4Wh-p13xxYl6aqEwiIkzQhBK-LZe2xk" #da sostituire
#-------------------
# cancella l username e usa id 
#-------------------------------------------------
def on_chat_message(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    if content_type=='text':
        #chat_id=msg['chat']['id'] #chat_id identification
        name=msg["from"]["username"] #account name
        txt=msg['text'] #message sended
        params = txt.split()[1:]
       
       #ok
        if txt.startswith('/start'):
            message=["Welcome to iot service for monitoring air quality in you environments.\n Firstly you have to register to the service througt the command /register.\n To see how to use this command please type /info to check all command and their syntax.\n"]
            allert=["Remind to SAVE YOUR PASSWORD in order to avoid losing it and don't be able to log to you profile"]
            bot.sendMessage(chat_id,message)
            bot.sendMessage(chat_id,allert)
        #ok
        elif txt.startswith('/info'):
                if len(params)==0:
                    for i in t_m.commands():
                        bot.sendMessage(chat_id,i)
                else:
                    bot.sendMessage(chat_id,t_m.commands(params[0][1:]))
        #ok
        elif txt.startswith('/login'):
            try:
                bot.sendMessage(chat_id,t_m.login(chat_id,params[0]))
                bot.deleteMessage(telepot.message_identifier(msg)) #deletes the message once registered
            except:
                bot.sendMessage(chat_id,"format /login <password>")
        #ok
        elif txt.startswith('/register'):
            try:
                    bot.sendMessage(chat_id,t_m.register(chat_id,params))
            except:
                bot.sendMessage(chat_id,"format /register <username> <password>")
        #ok
        elif txt.startswith('/logout'):
            bot.sendMessage(chat_id,t_m.logout(chat_id))
        
        elif( not t_m.status(name)):
            bot.sendMessage(chat_id,'Attention you are offline, please login')
        
        elif txt.startswith('/check') and t_m.status(name):
            groupIds=t_m.get_ids(chat_id)
            kbs=t_m.build_keyboard(groupIds,'groupId')
            keyboard = keyboard = InlineKeyboardMarkup(inline_keyboard=[[x] for x in kbs])
            bot.sendMessage(chat_id,"Which groupId do you want to check?",reply_markup=keyboard)
        
        elif txt.startswith('/addGroupId')  and t_m.status(name):
            try:
                print("debugginho")
                t_m.add_id(chat_id,params[0:])
            except:
                bot.sendMessage(chat_id,"/addGroupId <newGroupId>")
         
        elif txt.startswith('/addDevice')  and t_m.status(name):
            try:
                t_m.add_sen(chat_id,params[0],params[1],params[2])
            except:
                bot.sendMessage(chat_id,"/addDevice <groupId> <newDevice> <Pin>")
    
        elif txt.startswith('/delDevice')  and t_m.status(name):
            try:   
                 t_m.del_sen(chat_id,params[0],params[1:])
            except:
                bot.sendMessage(chat_id,"/delDevice <groupId> <deviceToDel>")
           

        elif txt.startswith('/delGroupId')  and t_m.status(name):   
             try:
                t_m.del_id(chat_id,params[0:])
             except:
                 bot.sendMessage(chat_id,"/delGroupId <groupId> ")
    
    #capire come integrarlo 
    if content_type == 'location':
      print(msg['location'])
      location=msg['location']
    #variabile globale location che viene modificata, se None l /IdAdd dira inserisci prima posto con location, senno inserisco coordinate con add_id
     
     

     
            

def on_callback_query(msg): # come premo ritornano cose 
    query_id, chat_ID, query_data = telepot.glance(msg, flavor='callback_query')
    txt=query_data.split()
    if txt[0]=='groupId':
        id_sensor=t_m.get_sensors(chat_ID,txt[1])
        kbs=t_m.build_keyboard(id_sensor,'sensors')
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[x] for x in kbs])
        bot.sendMessage(chat_ID,"Which device you are interested in?",reply_markup=keyboard)
    #vedi come cambiare queste , build_keyboard(['datas','graph'],sens_rif)
    elif txt[0]=='sensors':
        kbs=t_m.build_keyboard(['datas','thingspeak'],txt[1])
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[x] for x in kbs])
        bot.sendMessage(chat_ID,"What do you want, actual data or Thingspeak's graph?",reply_markup=keyboard)
    #sens rif, data 
    #build[temperatura,co2,umidita],'sensor tipologia)
    elif (txt[1]=='datas' or txt[1]=='thingspeak'): #contorta ma funziona,query=(id_sensore cosaVoglio) 
        txt.reverse()
        kbs=t_m.build_keyboard(['temperature','CO2','humidity'],txt[0]+' '+txt[1])
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[x] for x in kbs])
        bot.sendMessage(chat_ID,"What do you want?",reply_markup=keyboard)
    #questo si potrebbe chiudere in poche righe,magari capendo come vanno le richieste
    elif txt[2]=='temperature':
        if txt[0]=='datas':
            bot.sendMessage(chat_ID,text="You requested temperature of %s" %txt[1])
            #qui dovro mettere la richiesta get per accedere ai dati reali
        else:
            #qui richiesta get per richiedere il grafico a thigspeak
            bot.sendPhoto(chat_ID,'https://cdn.getyourguide.com/img/location/5a0838201565b.jpeg/92.jpg')#mandare foto
            bot.sendMessage(chat_ID,text="grafico temperatura di %s \n" %txt[1]) 
    elif txt[2]=='CO2':
        if txt[0]=='datas':
            bot.sendMessage(chat_ID,text="You requested CO2 of %s\n" %txt[1]) 
        else:
            bot.sendPhoto(chat_ID,'https://www.milanretreats.com/wp-content/uploads/2020/01/milanretreats_img_slide.jpg')
            bot.sendMessage(chat_ID,text="grafico c02 di %s \n" %txt[1]) 
    elif txt[2]=='humidity':
        if txt[0]=='datas':
            bot.sendMessage(chat_ID,text="You requested humidity of %s" %txt[1])
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