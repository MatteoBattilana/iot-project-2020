import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
 
from pprint import pprint
import time
import datetime
import json
 
 
TOKEN="" #da sostituire
command={"login":' per autentificarsi,\n' '/login username pssw',
        "register":'per registrarsi,\n /register username pssw',
        "logout":'per scolleagrsi,\n /logout',
        "check":'per visualizzare i dati del sensore o da thingspeak,\n /check',}
#-------------------
def build_keyboard(elements,category):
    kbs =[]
    for x in elements:
        kbs = kbs + [InlineKeyboardButton(text=x, callback_data=category+' '+x)]
    return kbs

def find_id(elements,name):
    for id_obj in elements:
        if id_obj["groupId"]==name:
            break
    return id_obj
 
#--------------------
def commands(chat_id):
    for c in command:
        bot.sendMessage(chat_id, c)
#-------------------------------------------------------------------------------
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

def register(chat_id,name,pssw):
    users=json.load(open('users.json'))
    us={"id":chat_id,"username":name,"password":pssw,"status":"off","groupId":[]}
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
def add_id(chat_id,id):
    users=json.load(open('users.json'))
    bot.sendMessage(chat_id,id)
    for u in users["Users"]:
         if u["id"]==chat_id:
            vector=u["groupId"]
            for i in id:
                new={"groupId":str(i),"Sensors":[]}
                vector.append(new)
            u["groupId"]=vector
            break 
    json.dump(users,open('users.json','w'))  

def del_id(chat_id,id):
     users=json.load(open('users.json'))
     for u in users["Users"]:
         if u["id"]==chat_id:
           for u_gId in u["groupId"]:
               if u_gId["groupId"] in id:
                   u["groupId"].remove(u_gId)
     json.dump(users,open('users.json','w'))    

#----------------------------------------------------------------------------
def add_sen(chat_id,id,sensors):
    users=json.load(open('users.json'))
    for u in users["Users"]:
         if u["id"]==chat_id:      #trovo il mio profilo
           for g_id in u["groupId"]:  #cerco il id dove aggiungere 
               if g_id["groupId"]==id:
                   vector=g_id["Sensors"]
                   vector+=sensors
                   g_id["Sensors"]=vector
                   break 
    json.dump(users,open('users.json','w'))  

def del_sen(chat_id,id,sensor):
     users=json.load(open('users.json'))
     for u in users["Users"]:
         if u["id"]==chat_id:      #trovo il mio profilo
           for g_id in u["groupId"]:  #cerco il id dove aggiungere 
               if g_id["groupId"]==id:
                    bot.sendMessage(chat_id,g_id["Sensors"])
                    for x in sensor: g_id["Sensors"].remove(str(x)) 
                    bot.sendMessage(chat_id,g_id["Sensors"])
                    #g_id["Sensors"]=vector
                    #break
     json.dump(users,open('users.json','w'))

#------------------------------------------------------
def get_ids(chat_id):
     users=json.load(open('users.json'))
     id_list=[]
     for u in users["Users"]:
         if u["id"]==chat_id:      #trovo il mio profilo
           for g_id in u["groupId"]:  #cerco il id dove aggiungere 
               id_list.append(g_id["groupId"])
     return id_list

def get_sensors(chat_id,id):
     users=json.load(open('users.json'))
     for u in users["Users"]:
         if u["id"]==chat_id:      #trovo il mio profilo
           for g_id in u["groupId"]:  #cerco il id dove aggiungere 
               if g_id["groupId"]==id:
                   return g_id["Sensors"]






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
            groupIds=get_ids(chat_id)
            kbs=build_keyboard(groupIds,'groupId')
            keyboard = keyboard = InlineKeyboardMarkup(inline_keyboard=[[x] for x in kbs])
            bot.sendMessage(chat_id,"scegli",reply_markup=keyboard)
        elif txt.startswith('/Idadd')  and status(name):
                 params = txt.split()[1:]
                 add_id(chat_id,params[0:])

        elif txt.startswith('/SenAdd')  and status(name):
                 params = txt.split()[1:]
                 add_sen(chat_id,params[0],params[1:])
    
        elif txt.startswith('/Sendel')  and status(name):   
             params = txt.split()[1:]
             del_sen(chat_id,params[0],params[1:])

        elif txt.startswith('/IdDel')  and status(name):   
             params = txt.split()[1:]
             del_id(chat_id,params[0:])

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
    query_id, chat_ID, query_data = telepot.glance(msg, flavor='callback_query')
    txt=query_data.split()
    if txt[0]=='groupId':
        id_sensor=get_sensors(chat_ID,txt[1])
        kbs=build_keyboard(id_sensor,'sensors')
        keyboard = keyboard = InlineKeyboardMarkup(inline_keyboard=[[x] for x in kbs])
        bot.sendMessage(chat_ID,"scegli",reply_markup=keyboard)
    #vedi come cambiare queste , build_keyboard(['datas','graph'],sens_rif)
    elif txt[0]=='sensors':
        kbs=build_keyboard(['datas','thingspeak'],txt[1])
        keyboard = keyboard = InlineKeyboardMarkup(inline_keyboard=[[x] for x in kbs])
        bot.sendMessage(chat_ID,"scegli",reply_markup=keyboard)
    #sens rif, data 
    #build[temperatura,co2,umidita],'sensor tipologia)
    elif (txt[1]=='datas' or txt[1]=='thingspeak'): #contorta ma funziona,query=(id_sensore cosaVoglio) 
        txt.reverse()
        kbs=build_keyboard(['temperatura','c02','umidita'],txt[0]+' '+txt[1])
        keyboard = keyboard = InlineKeyboardMarkup(inline_keyboard=[[x] for x in kbs])
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
MessageLoop(bot, {'chat':on_chat_message, 'callback_query':on_callback_query}).run_as_thread()
print('Listening ...')

while 1:
    time.sleep(10)



#https://en-unnoobcomeme.blogspot.com/2017/07/usare-un-bot-telegram-per-ricevere-dati.html
#
