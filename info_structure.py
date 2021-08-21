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
# cancella l username e usa id 
#-------------------------------------------------
def on_chat_message(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    if content_type=='text':
        chat_id=msg['chat']['id'] #chat_id identification
        name=msg["from"]["username"] #account name
        txt=msg['text'] #message sent 
        params = txt.split()[1:]
        status = t_m.status(chat_id)
        print(params)
        par_len = len(params)
       
       #ok
        if txt.startswith('/start'):
            message=["Welcome to iot service for monitoring air quality in you environments.\n Firstly you have to register to the service througt the command /register.\n To see how to use this command please type /info to check all command and their syntax.\n"]
            alert=["Remind to SAVE YOUR PASSWORD in order to avoid losing it and don't be able to log to you profile"]
            bot.sendMessage(chat_id,message)
            bot.sendMessage(chat_id,alert)
        #ok
        elif txt.startswith('/info'):
                if len(params)==0:
                    for i in t_m.commands():
                        bot.sendMessage(chat_id,i)
                else:
                    bot.sendMessage(chat_id,t_m.commands(params[0]))
        #ok
        elif txt.startswith('/login'):
            try:
                if par_len != 1:
                    raise Exception
                bot.sendMessage(chat_id,t_m.login(chat_id,params[0]))
                bot.deleteMessage(telepot.message_identifier(msg)) #deletes the message once registered
            except:
                bot.sendMessage(chat_id,"format /login <password>")
        #ok
        elif txt.startswith('/register'):
            try:
                if par_len > 2:
                    raise Exception
                bot.sendMessage(chat_id,t_m.register(chat_id,params))
            except:
                bot.sendMessage(chat_id,"format /register <username> <password>")
        #ok
        elif txt.startswith('/logout'):
            bot.sendMessage(chat_id,t_m.logout(chat_id))
        
        elif not status:
            bot.sendMessage(chat_id,'Attention you are offline, please login')
        
        elif txt.startswith('/check'):
            groupIds=t_m.get_ids(chat_id)
            if len(groupIds) > 0:
                kbs=t_m.build_keyboard(groupIds,'groupId')
                keyboard = keyboard = InlineKeyboardMarkup(inline_keyboard=[[x] for x in kbs])
                bot.sendMessage(chat_id,"Which groupId do you want to check?",reply_markup=keyboard)
            else:
                bot.sendMessage(chat_id,"No groupId in your account, please insert one.")
        
        elif not t_m.insertedId(chat_id):
            bot.sendMessage(chat_id,'Attention: before doing other actions you have to send position of groupId {}'.format(t_m.currentId(chat_id)))
        
        elif txt.startswith('/addGroupId'):
            try:
                if par_len!=1:
                    raise Exception
                elif not params[0] in t_m.get_ids(chat_id):
                    bot.sendMessage(chat_id,t_m.add_id(chat_id,params))
                else:
                    bot.sendMessage(chat_id,'groupId is already registered')
            except:
                bot.sendMessage(chat_id,t_m.commands('/addGroupId'))
            #try:
            #    if par_len != 1:
            #        raise Exception
            #    elif not params[0] in t_m.get_ids(chat_id):
            #        bot.sendMessage(chat_id,t_m.add_id(chat_id,params))
            #    else:
            #        bot.sendMessage(chat_id,f"GroupId is already present.")
            #except:
            #    bot.sendMessage(chat_id,"/addGroupId <newGroupId>")
         
        elif txt.startswith('/addDevice'):
            try:
                if par_len != 3:
                    raise Exception
                bot.sendMessage(chat_id,t_m.add_sen(chat_id,params))
            except:
                bot.sendMessage(chat_id,t_m.commands('/addDevice'))
    
        elif txt.startswith('/delete'):
            groupIds=t_m.get_ids(chat_id)
            if len(groupIds) > 0:
                kbs=t_m.build_keyboard(groupIds,'delete')
                keyboard = keyboard = InlineKeyboardMarkup(inline_keyboard=[[x] for x in kbs])
                bot.sendMessage(chat_id,"Which groupId do you want to delete?",reply_markup=keyboard)
            else:
                bot.sendMessage(chat_id,'No groupId in your account')
        
        #elif txt.startswith('/delDevice'):
        #    try:   
        #        t_m.del_sen(chat_id,params[0],params[1:])
        #    except:
        #        bot.sendMessage(chat_id,"/delDevice <groupId> <deviceToDel>")

        #elif txt.startswith('/delGroupId'):   
        #     try:
        #        t_m.del_id(chat_id,params[1])
        #     except:
        #         bot.sendMessage(chat_id,"/delGroupId <groupId>")
        
        else:
            bot.sendMessage(chat_id,"Command not supported")
    
    #capire come integrarlo 
    if content_type == 'location':
      print(msg['location'])
      t_m.coordinate(chat_id,msg['location'])
    #variabile globale location che viene modificata, se None l /IdAdd dira inserisci prima posto con location, senno inserisco coordinate con add_id
     

def on_callback_query(msg):
    query_id, chat_id, query_data = telepot.glance(msg, flavor='callback_query')
    txt=query_data.split()
    #for a given group id display all sensor associated
    print(txt)
    if txt[0]=="delete":
            if len(txt)==2:
                id_sensor=t_m.get_sensors(chat_id,txt[1])+["deleteGroupId"]
                if len(id_sensor)>0:
                    kbs=t_m.build_keyboard(id_sensor,txt[0]+' '+txt[1]) #la scelta viene aggregata a questi txt e viene passata alla prox query
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[[x] for x in kbs])
                    bot.sendMessage(chat_id,"Which device?",reply_markup=keyboard)
                else:
                    bot.sendMessage(chat_id,'No device available')
            elif txt[2]=='deleteGroupId':
                print(txt[2])
                t_m.del_id(chat_id,txt[1])
                bot.sendMessage(chat_id,'groupId {} cancelled'.format(txt[1]))
            else: # elimino sensore
                t_m.del_sen(chat_id,txt[1:])
                bot.sendMessage(chat_id,'Device {} of groupId {} cancelled'.format(txt[2],txt[1]))

    else:
        if txt[0]=='groupId':
            id_sensor=t_m.get_sensors(chat_id,txt[1])
            if len(id_sensor) > 0:
                kbs=t_m.build_keyboard(id_sensor,'devices')
                keyboard = InlineKeyboardMarkup(inline_keyboard=[[x] for x in kbs])#questo modo di scrivere mi fa fare in colonna, in riga insieme lista 
                bot.sendMessage(chat_id,"Which device?",reply_markup=keyboard)
            else:
                bot.sendMessage(chat_id,'No device available for this groupId')
        # for the selected device is ask if u want datas o thingspeak
        elif txt[0]=='devices':
            kbs=t_m.build_keyboard(['datas','thingspeak'],txt[1])
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[x] for x in kbs])
            bot.sendMessage(chat_id,"What do you want: actual datas or thingspeak?",reply_markup=keyboard)
        #one selected what do u want,choose with characteristic u want
        elif (txt[1]=='datas' or txt[1]=='thingspeak'): #contorta ma funziona,query=(id_sensore cosaVoglio) 
            txt.reverse()
            kbs=t_m.build_keyboard(['temperature','CO2','humidity'],txt[0]+' '+txt[1])
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[x] for x in kbs])
            bot.sendMessage(chat_id,"What do you want?",reply_markup=keyboard)
   
        #one decided al the path, returns what user wants 
        elif txt[2]=='temperature':
            if txt[0]=='datas':
                bot.sendMessage(chat_id,text="You selected temperature of %s" %txt[1])
            #qui dovro mettere la richiesta get per accedere ai dati reali
            else:
            #qui richiesta get per richiedere il grafico a thigspeak
                bot.sendPhoto(chat_id,'https://cdn.getyourguide.com/img/location/5a0838201565b.jpeg/92.jpg')#mandare foto
                bot.sendMessage(chat_id,text="temperature graph from %s \n" %txt[1]) 
        elif txt[2]=='CO2':
            if txt[0]=='datas':
                bot.sendMessage(chat_id,text="You selected CO2 of %s\n" %txt[1]) 
            else:
                bot.sendPhoto(chat_id,'https://www.milanretreats.com/wp-content/uploads/2020/01/milanretreats_img_slide.jpg')
                bot.sendMessage(chat_id,text="CO2 graph from %s \n" %txt[1]) 
        elif txt[2]=='humidity':
            if txt[0]=='datas':
                bot.sendMessage(chat_id,text="You selected humidity of %s" %txt[1])
            #qui dovro mettere la richiesta get per accedere ai dati reali
            else:
            #qui richiesta get per richiedere il grafico a thigspeak
                bot.sendPhoto(chat_id,'https://images.lacucinaitaliana.it/wp-content/uploads/2018/05/18183720/roma-primavera-1600x800.jpg')#mandare foto
                bot.sendMessage(chat_id,text="humidity graph from %s \n" %txt[1]) 
            
    
           
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
