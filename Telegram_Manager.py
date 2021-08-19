
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton

import json

commands=['/login: for authentication \n /login username pssw',
        '/register: register to the service,\n /register username pssw',
        '/logout: \n /logout',
        '/check: to get values from the sensors\n /check',
        '/IdAdd: add groupId to your account\n /Idadd groupId',
        '/IdDel: remove groupId from your account\n /IdDel groupId',
        '/SenAdd: add sensor to a specific groupId\n /SenAdd groupId nameSens PIN',
        '/SenDel: remove sensor from specific groupId\n /SenDel groupId nameSens']

class Telegram_Manager:
    # init method or constructor 
    def __init__(self, name):
        self.users=json.load(open(name))
    
    #ok
    def build_keyboard(self,elements,category):
        kbs =[]
        for x in elements:
            kbs = kbs + [InlineKeyboardButton(text=x, callback_data=category+' '+x)]
        return kbs
    
    #ok
    def find_id(self,elements,name):
        for id_obj in elements:
            if id_obj["groupId"]==name:
                break
        return id_obj
    
    def commands(self,command=None):
        if command==None:
            return commands
        else:
            try:
                for sentence in commands:
                    if sentence.startswith(command):
                        break
                return sentence
            except:
                return 'Instruction is not supported'
                
           

    #ok
    def logout(self,chat_id):
        for us in self.users['Users']:
            if us['id'] == chat_id:
                us['status']= 'off'
        json.dump(self.users,open('users.json','w')) 
        return 'U are off, see u soon'  
    #ok
    def status(self,name):
        for us in self.users["Users"]:
            if us['username']==name and us['status']== "on":
                return True
        return False
    
    #ok check if the chat_id is already saved
    def just_register(self,chatId):
        exist=False
        for u in self.users["Users"]:
            if u["id"]==chatId: 
                exist=True
        return exist
   
    #ok register che user to 'database'
    def register(self,chat_id,value):
        if(not self.just_register(chat_id)):
            us={"id":chat_id,"username":value[0],"password":value[1],"status":"off","groupId":[]}
            self.users["Users"].append(us)
            json.dump(self.users,open('users.json','w'))
            return ' registation is done successfully'
        else:
            return ' your iD is already use, please login'  
    
    #ok gets on the user,allows to use services
    def login(self,chat_id,pssw):
        auth=False
        for us in self.users['Users']:
            if us['id'] == chat_id and us['password']==pssw :
                us['status']= 'on'
                json.dump(self.users,open('users.json','w'))
                auth=True
        if auth: return 'are u in,welcome to service'
        else: return 'pssw was incorrect'
                
    
    #ok
    def add_id(self,chat_id,id):
        for u in self.users["Users"]:
            if u["id"]==chat_id:
                vector=u["groupId"]
                for i in id:
                    new={"groupId":str(i),"Sensors":[]}
                    vector.append(new)
                u["groupId"]=vector
                break 
        json.dump(self.users,open('users.json','w'))  
    #ok
    def del_id(self,chat_id,id):
        for u in self.users["Users"]:
            if u["id"]==chat_id:
                for u_gId in u["groupId"]:
                    if u_gId["groupId"] in id: 
                        u["groupId"].remove(u_gId)
        json.dump(self.users,open('users.json','w'))    

    #ok
    def add_sen(self,chat_id,id,sensor,pin):
        for u in self.users["Users"]:
            if u["id"]==chat_id:      #trovo il mio profilo
                for g_id in u["groupId"]:  #cerco il id dove aggiungere 
                    if g_id["groupId"]==id:
                        vector=g_id["Sensors"]
                        new={"Name":str(sensor),"Pin":pin}
                        vector.append(new)
                        g_id["Sensors"]=vector
                        break  
        json.dump(self.users,open('users.json','w'))  
    #ok
    def del_sen(self,chat_id,id,sensor):
        for u in self.users["Users"]:
            if u["id"]==chat_id:      #trovo il mio profilo
                for g_id in u["groupId"]:  #cerco il id dove aggiungere 
                    if g_id["groupId"]==id:
                        for x in g_id["Sensors"]:
                            if x["Name"] in sensor: g_id["Sensors"].remove(x) 
        
        json.dump(self.users,open('users.json','w'))
    #ok
    def get_ids(self,chat_id):
        id_list=[]
        for u in self.users["Users"]:
            if u["id"]==chat_id:      #trovo il mio profilo
                for g_id in u["groupId"]:  #cerco il id dove aggiungere 
                    id_list.append(g_id["groupId"])
        return id_list
    #ok
    def get_sensors(self,chat_id,id):
        id_list=[]
        for u in self.users["Users"]:
            if u["id"]==chat_id:      #trovo il mio profilo
                for g_id in u["groupId"]:  #cerco il id dove aggiungere 
                    if g_id["groupId"]==id:
                        for sen in g_id["Sensors"]: id_list.append(sen["Name"])
        return id_list
                  