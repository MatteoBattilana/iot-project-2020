
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton

import json
# login - Authenticate the user
# register - Register to the service
# logout - Logout from the current session
# check - Get values from the devices
# addgroupid - Add a new groupId to your account
# adddevice - Add device to a specific groupId
# delete - Remove a device from specific groupId or directly an entire groupId
# cancel - Cancel the current operation
# info - Command list

commands=['- /login: for authentication',
        '- /register: register to the service',
        '- /logout: logout from the current session',
        '- /check: to get values from the devices',
        '- /addgroupid: add a new groupId to your account',
        '- /adddevice: add device to a specific groupId',
        '- /delete: remove a device from specific groupId or directly an entire groupId',
        '- /cancel: cancel the current operation']

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
        for us in self.users['users']:
            if us['id'] == chat_id:
                us['status']= 'off'
        json.dump(self.users,open('users.json','w'))
        return 'Logged out'
    #ok
    def status(self,chat_id):
        exist=False
        for us in self.users["users"]:
            if us['id']==chat_id and us['status']== "on":
                exist=True
        return exist

    #ok check if the chat_id is already saved
    def just_register(self,chatId):
        exist=False
        for u in self.users["users"]:
            if u["id"]==chatId and u["password"]:
                exist=True
        return exist

    def delete_user(self,chatId):
        for u in self.users["users"][:]:
            if u["id"]==chatId:
                print(str(u))
                self.users["users"].remove(u)

    #ok register che user to 'database'
    def register(self,chat_id,value):
        if(not self.just_register(chat_id)):
            self.delete_user(chat_id)
            us={"id":chat_id,"password":value[0],"status":"on","state":"start","groupId":[],"currentId":"","currentDeviceId":""}
            self.users["users"].append(us)
            json.dump(self.users,open('users.json','w'))
            return ' Registration is done successfully'
        else:
            return 'Your password is already set, please the login command'

    #ok gets on the user,allows to use services
    def login(self,chat_id,pssw):
        auth=False
        for us in self.users['users']:
            if us['id'] == chat_id and us['password']==pssw :
                us['status']= 'on'
                json.dump(self.users,open('users.json','w'))
                auth=True
        if auth:
            return auth,'Logged in successfully, welcome to service. You can now use all available commands'
        else:
            return auth,'Incorrect password, please insert the correct one'


    #ok
    def add_id(self,chat_id,id):
        for u in self.users["users"]:
            if u["id"]==chat_id:
                new={"groupId":id+"_"+str(chat_id),"name":id,"latitude":"","longitude":"","devices":[]}
                u["groupId"].append(new)
                u["currentId"] = id+"_"+str(chat_id)
                break
        json.dump(self.users,open('users.json','w'))
        return id + " groupId inserted successfully"
    #ok
    def del_id(self,chat_id,id):
        for u in self.users["users"]:
            if u["id"]==chat_id:
                for u_gId in u["groupId"]:
                    if u_gId["groupId"] == id + "_" + str(chat_id): #vettore
                        u["groupId"].remove(u_gId)
        json.dump(self.users,open('users.json','w'))

    def getCurrentGroupId(self, chat_id):
        for u in self.users["users"]:
            if u["id"] == chat_id:
                return u["currentId"]
        return ""

    def getCurrentDeviceId(self, chat_id):
        for u in self.users["users"]:
            if u["id"] == chat_id and "currentDeviceId" in u:
                return u["currentDeviceId"]
        return ""

    def getCurrentGroupIdName(self, chat_id):
        for u in self.users["users"]:
            if u["id"] == chat_id:
                cId = u["currentId"]
                for group in u["groupId"]:
                    if group["groupId"] == cId:
                        return group["name"]
        return ""

    def isDeviceAlreadyPresent(self, deviceId):
        for u in self.users["users"]:
            for g_id in u["groupId"]:  #cerco il id dove aggiungere
                for dev in g_id["devices"]:
                    if dev["name"] == deviceId:
                        return True

        return False


    def setDevicePosition(self, chat_id, deviceId, position):
        for u in self.users["users"]:
            if u["id"] == chat_id:      #trovo il mio profilo
                for g_id in u["groupId"]:  #cerco il id dove aggiungere
                    for dev in g_id["devices"]:
                        if dev["name"] == deviceId:
                            dev["position"] = position
                            break
        json.dump(self.users,open('users.json','w'))

    #ok
    def add_sen(self,chat_id,datas):
        insert=False
        for u in self.users["users"]:
            if u["id"] == chat_id:      #trovo il mio profilo
                for g_id in u["groupId"]:  #cerco il id dove aggiungere
                    print(g_id)
                    if g_id["groupId"] == u["currentId"]:
                        new={"name":str(datas[0]),"pin":datas[1],"position":""}
                        g_id["devices"].append(new)
                        insert=True
                        break
        json.dump(self.users,open('users.json','w'))
        if insert:
            return 'New device inserted correctly'
        else:
            return 'Specified groupId does not exist'

    #ok
    def del_sen(self,chat_id,datas):
        for u in self.users["users"]:
            if u["id"]==chat_id:      #trovo il mio profilo
                for g_id in u["groupId"]:  #cerco il id dove aggiungere
                    if g_id["groupId"]==datas[0] + "_" + str(chat_id):
                        for x in g_id["devices"]:
                            if x["name"]==datas[1]:
                                g_id["devices"].remove(x)
                                if u["currentDeviceId"] == datas[1]:
                                    u["currentDeviceId"] = ""

        json.dump(self.users,open('users.json','w'))

    def getChatId(self,groupId):
        for i in self.users["users"]:
            for gr in i["groupId"]:
                if gr["groupId"] == groupId:
                    return i["id"]
        return None

    #ok
    def get_ids(self,chat_id=None):
        id_list=[]
        for u in self.users["users"]:
            if u["id"]==chat_id or not chat_id:      #trovo il mio profilo
                for g_id in u["groupId"]:  #cerco il id dove aggiungere
                    id_list.append(g_id["groupId"])
        return id_list

    def get_ids_name(self,chat_id=None):
        id_list=[]
        for u in self.users["users"]:
            if u["id"]==chat_id or not chat_id:      #trovo il mio profilo
                for g_id in u["groupId"]:  #cerco il id dove aggiungere
                    id_list.append(g_id["name"])
        return id_list
    #ok
    def get_sensors(self,chat_id,id):
        id_list=[]
        for u in self.users["users"]:
            if u["id"]==chat_id:      #trovo il mio profilo
                for g_id in u["groupId"]:  #cerco il id dove aggiungere
                    if g_id["groupId"]==id+"_"+str(chat_id):
                        for sen in g_id["devices"]: id_list.append(sen["name"])
        return id_list

    #ok needs to save last coordinates sended
    def coordinate(self,chat_id,pos):
        for u in self.users["users"]:
            if u["id"]==chat_id:
                id=u["currentId"] #ultimo  Id inserito
                for i in u["groupId"]: #tra tutti l id
                    if i["groupId"] == id:
                        i["latitude"]=pos["latitude"]
                        i["longitude"]=pos["longitude"]
                        u["currentId"]=""
        json.dump(self.users,open('users.json','w'))

    def isLocationInserted(self,chat_id, groupId):
        inserted=False
        for u in self.users["users"]:
            if u["id"]==chat_id:
                for gr_id in u["groupId"]:
                    if gr_id["groupId"] == groupId + "_" + str(chat_id) and gr_id["latitude"] != "":
                        inserted=True
        return inserted

    def currentId(self,chat_id):
        for u in self.users["users"]:
            if u["id"]==chat_id: value=u["currentId"]
        return value

    def setCurrentId(self,chat_id,id):
        for u in self.users["users"]:
            if u["id"]==chat_id:
                u["currentId"] = id + "_" + str(chat_id)

    def setCurrentDeviceId(self,chat_id,id):
        for u in self.users["users"]:
            if u["id"]==chat_id:
                u["currentDeviceId"] = id

    def getState(self,chat_id):
        for us in self.users['users']:
            if us['id'] == chat_id and 'state' in us:
                return us['state']
        return 'start'

    def setState(self,chat_id,state):
        found = False
        for us in self.users['users']:
            if us['id'] == chat_id:
                found = True
                us['state'] = state
        if not found:
            us={"id":chat_id,"password":"","status":"off","state":state,"groupId":[],"currentId":"","currentDeviceId":""}
            self.users["users"].append(us)

        json.dump(self.users,open('users.json','w'))
