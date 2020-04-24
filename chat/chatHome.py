# coding:utf-8
import tornado.web
import tornado.ioloop
import tornado.httpserver
import tornado.options
import os
import datetime
import json
from tornado.web import RequestHandler
from tornado.options import define, options
from tornado.websocket import WebSocketHandler

define("port", default=4000, type=int)

class ChatHome(object):
    uname_and_pwd = {'小王':'1','小李':'1'}
    rooms = {}
    rooms_and_creater = {}
    chatRegister = {}
    loged = set()


class IndexHandler(RequestHandler):
    def get(self):
        self.render("index.html",flag=False)


class LogHandler(RequestHandler):
    def get(self):
        rooms_and_creater = self.application.chathome.rooms_and_creater
        rooms_and_creater = json.dumps(rooms_and_creater)
        uname = self.get_argument('uname')
        self.render('home.html',rooms_and_creater=rooms_and_creater, uname=uname)

    def post(self):
        uname = self.get_argument('uname')
        pwd = self.get_argument('pwd')
        rooms_and_creater = self.application.chathome.rooms_and_creater
        rooms_and_creater = json.dumps(rooms_and_creater)
        uname_and_pwd = self.application.chathome.uname_and_pwd
        loged = self.application.chathome.loged
        if uname in loged:
            self.render("index.html", flag='用户已经登录！')
            return
        loged.add(uname)
        if uname in uname_and_pwd:
            if uname_and_pwd[uname] == pwd:
                self.render('home.html',rooms_and_creater=rooms_and_creater, uname=uname)
            else:
                self.render("index.html", flag='密码或用户输入错误，请重新输入')
        else:
            self.render("index.html",flag='密码或用户输入错误，请重新输入')

class RegisterHandler(RequestHandler):
    def get(self):
        self.render('register.html',flag=False)

    def post(self):
        uname = str(self.get_argument('uname'))
        pwd = str(self.get_argument('pwd1'))
        uname_and_pwd = self.application.chathome.uname_and_pwd
        if uname in uname_and_pwd:
            self.render('register.html',flag=True)
        else:
            uname_and_pwd[uname] = pwd
            self.render("index.html",flag=False)

class HomeHandler(RequestHandler):
    def get(self):
        uname = self.get_argument('uname')
        room = self.get_argument('room')
        self.render('chatclient.html',room=room,uname=uname)

class NewRoomStatus(WebSocketHandler):
    users = set()
    def open(self):
        uname = str(self.get_argument('uname'))
        self.users.add(self)
        rooms_and_creater = self.application.chathome.rooms_and_creater
        rooms_and_creater = json.dumps(rooms_and_creater)
        self.write_message(rooms_and_creater)

    def on_close(self):
        self.users.remove(self)

    def on_message(self,message):
        uname = str(self.get_argument('uname'))
        message = json.loads(message)
        room = message['room']
        operate = message['operate']
        rooms = self.application.chathome.rooms
        chatRegister = self.application.chathome.chatRegister
        rooms_and_creater = self.application.chathome.rooms_and_creater

        if operate == 'create':
            if room in rooms:
                message['val'] = "0"
                self.write_message(json.dumps(message))
            else:
                message['val'] = "1"
                rooms[room] = [uname,]
                chatRegister[room] = {}
                rooms_and_creater[room] = uname
                for u in self.users:
                    u.write_message(json.dumps(message))
        elif operate == 'delete':
            if uname == rooms_and_creater[room]:
                del rooms[room]
                del chatRegister[room]
                del rooms_and_creater[room]
                message['val'] = "1"
                for u in self.users:
                    u.write_message(json.dumps(message))
            else:
                message['val'] = "0"
                self.write_message(json.dumps(message))

class ExitHandler(RequestHandler):
    def post(self):
        uname = self.get_argument('uname')
        if uname in self.application.chathome.loged:
            self.application.chathome.loged.remove(uname)
        self.render("index.html",flag=False)



class NewChatStatus(WebSocketHandler):
    users = {}

    def open(self):
        uname = str(self.get_argument('uname'))
        room = str(self.get_argument('room'))
        rooms = self.application.chathome.rooms
        chatRegister = self.application.chathome.chatRegister
        for name in rooms[room]:
            if uname != name:
                msg = {'at':name}
                self.write_message(json.dumps(msg))
        if uname in rooms[room] and uname in chatRegister[room]:
            for msg in chatRegister[room][uname]:
                self.write_message(msg)
            s = '-----------历史消息-----------'
            msg = {'s': s, 'form': 'center'}
            msg = json.dumps(msg)
            self.write_message(msg)
        else:
            chatRegister[room][uname] = []
            rooms[room].append(uname)
        if room not in self.users:
            self.users[room] = {}
        self.users[room][uname] = self
        s = '(%s) %s 进入聊天室%s' % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), uname, room)
        msg = {'s': s, 'form': 'center'}
        msg = json.dumps(msg)
        for name, u in self.users[room].items():
            u.write_message(msg)
            chatRegister[room][name].append(msg)
            if name != uname:
                msgat = {'at':uname}
                u.write_message(json.dumps(msgat))

    def on_message(self, message):
        uname = str(self.get_argument('uname'))
        room = str(self.get_argument('room'))
        rooms = self.application.chathome.rooms
        chatRegister = self.application.chathome.chatRegister
        message = json.loads(message)
        s1 = '(%s) %s' % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), uname)
        s2 = message['text']

        for name, u in self.users[room].items():
            if uname == name:
                msg = {'s1': s1,'s2':s2,'form':'right'}
                msg = json.dumps(msg)
                u.write_message(msg)
                chatRegister[room][name].append(msg)
            else:
                msg = {'s1': s1, 's2': s2, 'form': 'left'}
                msg = json.dumps(msg)
                u.write_message(msg)
                chatRegister[room][name].append(msg)
        for name,u in self.users[room].items():
            if name in message['atmember']:
                s = '(%s) %s @你' % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), uname)
                msg = {'s':s,'form':'center'}
                msg = json.dumps(msg)
                u.write_message(msg)
                chatRegister[room][name].append(msg)

    def on_close(self):
        uname = str(self.get_argument('uname'))
        room = str(self.get_argument('room'))
        rooms = self.application.chathome.rooms
        chatRegister = self.application.chathome.chatRegister
        del self.users[room][uname]
        for name, u in self.users[room].items():
            s = '(%s) %s 离开聊天室%s' % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), uname,room)
            msg = {'s': s,'form':'center'}
            msg = json.dumps(msg)
            u.write_message(msg)
            chatRegister[room][name].append(msg)

    def check_origin(self, origin):
        return True  # 允许WebSocket的跨域请求

class LeaveHandler(WebSocketHandler):
    def get(self):
        rooms_and_creater = self.application.chathome.rooms_and_creater
        rooms_and_creater = json.dumps(rooms_and_creater)
        uname = self.get_argument('uname')
        self.render('home.html',rooms_and_creater=rooms_and_creater, uname=uname)

class MyApplication(tornado.web.Application):
    def __init__(self):
        self.chathome = ChatHome()
        handlers = [
            (r"/", IndexHandler),
            (r'/log',LogHandler),
            (r'/register',RegisterHandler),
            (r'/home/',HomeHandler),
            (r'/exit',ExitHandler),
            (r'/leave',LeaveHandler),
            (r'/newRoomStatus/',NewRoomStatus),
            (r'/newChatStatus/',NewChatStatus)
        ]
        settings = {
            'template_path': os.path.join(os.path.dirname(__file__), "template"),
            'static_path': os.path.join(os.path.dirname(__file__), "static"),
        }
        tornado.web.Application.__init__(self, handlers, **settings)

if __name__ == '__main__':
    app = MyApplication()
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.current().start()
