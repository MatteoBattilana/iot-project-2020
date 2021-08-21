
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton

import json

commands=['/login: for authentication \n /login username pssw',
        '/register: register to the service,\n /register username pssw',
        '/logout: \n /logout',
        '/check: to get values from the devices\n /check',
        '/addGroupId: add a new groupId to your account\n /addGroupId <groupId>',
        '/delGroupId: remove groupId from your account\n /delGroupId <groupId>',
        '/addDevice: add device to a specific groupId\n /addDevice <groupId> <newDevice> <PIN>',
        '/delete: remove a device from specific groupId or directly an entire groupId']

class Telegram_Manager:
    # init method or constructor 
    def __init__(self, fileName):
        self.users=json.load(open(fileName))
    
    #ok
    def build_keyboard(self,elements,category):
        kbs =[]
        for x in elements:
            kbs = kbs + [InlineKeyboardButton(text=x, callback_data=category+' '+x)]
        return kbs
    
    def commands(self,command=None):
        if command==None:
            return commands
        else:
            try:
                for sentence in commands:
                    if sentence.startswith(command):
                       found=True
                       break
                if found:
                    return sentence
                else:
                    raise Exception
            except:
                return 'Instruction is not supported'
                
    #ok
    def logout(self,chat_id):
        for us in self.users['Users']:
            if us['id'] == chat_id:
                us['status']= 'off'
        json.dump(self.users,open('users.json','w'))
        return 'Logged out'  
    #ok
    def status(self,chat_id):
        exist=False
        for us in self.users["Users"]:
            if us['id']==chat_id and us['status']== "on":
                exist=True
        return exist
    
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
            us={"id":chat_id,"username":value[0],"password":value[1],"status":"off","groupId":[],"currentId":""}
            self.users["Users"].append(us)
            json.dump(self.users,open('users.json','w'))
            return ' Registration is done successfully'
        else:
            return ' Your iD is already in use, please login'  
    
    #ok gets on the user,allows to use services
    def login(self,chat_id,pssw):
        auth=False
        for us in self.users['Users']:
            if us['id'] == chat_id and us['password']==pssw :
                us['status']= 'on'
                json.dump(self.users,open('users.json','w'))
                auth=True
        if auth:
            return 'Logged in successfully, welcome to service'
        else:
            return 'Incorrect password'
                
    
    #ok
    def add_id(self,chat_id,id):
        for u in self.users["Users"]:
            if u["id"]==chat_id:
                new={"groupId":id[0],"latitude":"","longitude":"","Devices":[]}
                u["groupId"].append(new)
                u["currentId"] = id[0]
                break 
        json.dump(self.users,open('users.json','w'))
        return "GroupId inserted successfully"
    #ok
    def del_id(self,chat_id,id):
        for u in self.users["Users"]:
            if u["id"]==chat_id:
                for u_gId in u["groupId"]:
                    if u_gId["groupId"] == id: #vettore 
                        u["groupId"].remove(u_gId)
        json.dump(self.users,open('users.json','w'))  

    #ok
    def add_sen(self,chat_id,datas):
        insert=False
        for u in self.users["Users"]:
            if u["id"] == chat_id:      #trovo il mio profilo
                for g_id in u["groupId"]:  #cerco il id dove aggiungere 
                    if g_id["groupId"] == datas[0]:
                        new={"Name":str(datas[1]),"Pin":datas[2]}
                        g_id["Devices"].append(new)
                        insert=True
                        break  
        json.dump(self.users,open('users.json','w'))  
        if insert:
            return 'New device inserted correctly'
        else:
            return 'Specified groupId does not exist'
        
    #ok
    def del_sen(self,chat_id,datas):
        for u in self.users["Users"]:
            if u["id"]==chat_id:      #trovo il mio profilo
                for g_id in u["groupId"]:  #cerco il id dove aggiungere 
                    if g_id["groupId"]==datas[0]:
                        for x in g_id["Devices"]:
                            if x["Name"]==datas[1]: g_id["Devices"].remove(x) 
        
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
                        for sen in g_id["Devices"]: id_list.append(sen["Name"])
        return id_list
        
    #ok needs to save last coordinates sended
    def coordinate(self,chat_id,pos):
        for u in self.users["Users"]:
            if u["id"]==chat_id:
                id=u["currentId"] #ultimo  Id inserito 
                for i in u["groupId"]: #tra tutti l id
                    if i["groupId"] == id:
                        i["latitude"]=pos["latitude"]
                        i["longitude"]=pos["longitude"]
                        u["currentId"]=""
        json.dump(self.users,open('users.json','w'))
    
    def insertedId(self,chat_id):
        inserted=False
        for u in self.users["Users"]:
            if u["id"]==chat_id and u["currentId"]=="":
                inserted=True
        return inserted

    def currentId(self,chat_id):
        for u in self.users["Users"]:
            if u["id"]==chat_id: value=u["currentId"]
        return value