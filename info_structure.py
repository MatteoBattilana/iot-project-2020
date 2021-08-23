import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from Telegram_Manager import Telegram_Manager
import re
from pprint import pprint
import time
import datetime
import json

state = {}

TOKEN="1993057758:AAEns0oHrFhPbgqrnRUU21RM-sOC6jbrb9k" #da sostituire
#-------------------
# cancella l username e usa id
#-------------------------------------------------
def on_chat_message(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)


    if content_type == 'location':
        chat_id=msg['chat']['id']
        if state[chat_id] == 'addGroupId_location':
            print(msg['location'])
            t_m.coordinate(chat_id,msg['location'])
            bot.sendMessage(chat_id, "Location correctly set!\nYou can now add devices by using the correct command")
        #variabile globale location che viene modificata, se None l /IdAdd dira inserisci prima posto con location, senno inserisco coordinate con add_id


    elif content_type=='text':
        chat_id=msg['chat']['id'] #chat_id identification
        name=msg["from"]["username"] #account name
        txt=msg['text'] #message sent
        params = txt.split()
        status = t_m.status(chat_id)
        print(params)
        par_len = len(params)

        if not txt.startswith('/') and chat_id in state:
            if state[chat_id] == 'login':
                auth, message = t_m.login(chat_id,txt)
                bot.sendMessage(chat_id,message)
                if auth == True:
                    state[chat_id] = 'start'
                    bot.deleteMessage(telepot.message_identifier(msg))
                else:
                    state[chat_id] = 'login'

            elif state[chat_id] == 'register':
                bot.sendMessage(chat_id,t_m.register(chat_id,txt))
                bot.deleteMessage(telepot.message_identifier(msg))
                state[chat_id] = 'start'

            elif state[chat_id] == 'addGroupId_name':
                if not txt in t_m.get_ids(chat_id):
                    bot.sendMessage(chat_id,t_m.add_id(chat_id,txt))
                    state[chat_id] = 'addGroupId_location'
                    bot.sendMessage(chat_id, "Please send now the location of the groupId")
                else:
                    bot.sendMessage(chat_id,'The inserted groupId is already registered. Insert a new one')

            elif state[chat_id] == 'addSensor':
                ## make request to device to check if pin is correct
                if True:
                    bot.sendMessage(chat_id,t_m.add_sen(chat_id,params))
                    state[chat_id] = 'start'

            else:
                bot.sendMessage(chat_id,"Command not supported")
                sendAllCommands(chat_id)





        elif txt.startswith('/cancel'):
            state[chat_id] = 'start'
            bot.sendMessage(chat_id,"Operation cancelled")

       #ok
        elif txt.startswith('/start'):
            message="Welcome to iot service for monitoring air quality in you environments. Firstly you have to register to the service through the command /register and a password.\nTo see how to use this command please type /info to check all commands and their syntax.\n"
            alert="Remind to SAVE YOUR PASSWORD in order to avoid losing it and don't be able to log to you profile"
            bot.sendMessage(chat_id,message)
            bot.sendMessage(chat_id,alert)
        #ok
        elif txt.startswith('/info'):
            if len(params)==0:
                sendAllCommands(chat_id)
            else:
                bot.sendMessage(chat_id,t_m.commands(params[0]))
        #ok
        elif txt.startswith('/login'):
            state[chat_id] = 'login'
            bot.sendMessage(chat_id,"Please insert the password of your account or cancel the login by typing /cancel")
             #try:
            #    bot.sendMessage(chat_id,t_m.login(chat_id,params[0]))
            #    bot.deleteMessage(telepot.message_identifier(msg)) #deletes the message once registered
    #ok
        elif txt.startswith('/register'):
            if(not t_m.just_register(chat_id)):
                state[chat_id] = 'register'
                bot.sendMessage(chat_id, "Insert the password for your account.")
            else:
                bot.sendMessage(chat_id,'Your password is already set, please use the login command')
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

        elif txt.startswith('/addgroupid'):
            state[chat_id] = 'addGroupId_name'
            bot.sendMessage(chat_id,"Please insert the name of the new groupId")

        elif txt.startswith('/adddevice'):
            groupIds=t_m.get_ids(chat_id)
            if len(groupIds) > 0:
                kbs=t_m.build_keyboard(groupIds,'addDevice')
                keyboard = keyboard = InlineKeyboardMarkup(inline_keyboard=[[x] for x in kbs])
                bot.sendMessage(chat_id,"Which groupId do you want to add a sensor?",reply_markup=keyboard)
            else:
                bot.sendMessage(chat_id,"No groupId in your account, please insert one.")


        elif txt.startswith('/delgroupid'):
            groupIds=t_m.get_ids(chat_id)
            if len(groupIds) > 0:
                kbs=t_m.build_keyboard(groupIds,'delete')
                keyboard = keyboard = InlineKeyboardMarkup(inline_keyboard=[[x] for x in kbs])
                bot.sendMessage(chat_id,"Which groupId do you want to delete?",reply_markup=keyboard)
            else:
                bot.sendMessage(chat_id,'No groupId in your account')

        else:
            bot.sendMessage(chat_id,"Command not supported")
            sendAllCommands(chat_id)

def sendAllCommands(chat_id):
    bot.sendMessage(chat_id,"List of all available commands:\n\n" + "\n".join(t_m.commands()))

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
        if txt[0]=='addDevice':
            t_m.setCurrentId(chat_id,txt[1])
            if t_m.isLocationInserted(chat_id, txt[1]):
                state[chat_id] = 'addSensor'
                bot.sendMessage(chat_id, 'Please insert the device in the following format: <id> <PIN>')
            else:
                state[chat_id] = 'addGroupId_location'
                bot.sendMessage(chat_id,'Attention: before doing other actions you have to send position of groupId {}'.format(t_m.currentId(chat_id)))

        elif txt[0]=='groupId':
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
