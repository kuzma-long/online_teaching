# -*-coding:utf-8-*-
import json
import time

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket

chattingRoomList = [{"id": "1", "name": "湖人", "creater": "system"}, {"id": "2", "name": "曼联", "creater": "system"}]
msg_record = {}
pinfo = {}
users = []


class ChattingRoom(object):
    Clients = {}  # 用于记录客户端的连接

    def add_client(self, newer):
        # 保存新加入的客户端连接，并向聊天室其他成员发送消息
        home = str(newer.get_argument('id'))  # 获取所在聊天室id
        homeName = str(newer.get_argument('name'))  # 获取所在聊天室name
        users.append(newer.get_argument('user'))
        if home in self.Clients:
            self.Clients[home].append(newer)
        else:
            self.Clients[home] = [newer]
        message = {
            'time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())),
            'from': 'system',
            'message': '{} 加入聊天室 {}'.format(str(newer.get_argument('user')), homeName),
            'users': users
        }
        self.trigger(home, message)

    def del_client(self, lefter):
        # 用户关闭连接后，删除聊天室内对应的客户端连接
        home_id = str(lefter.get_argument('id'))  # 获取聊天室唯一标识id
        home_name = str(lefter.get_argument('name'))  # 获取所在聊天室名称
        users.remove(lefter.get_argument('user'))
        self.Clients[home_id].remove(lefter)
        if self.Clients[home_id]:
            message = {
                'time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())),
                'from': 'system',
                'message': '{} 离开聊天室 {}'.format(str(lefter.get_argument('user')), home_name),
                'users': users
            }
            self.trigger(home_id, message)

    def send_msg(self, sender, message):
        # 处理客户端提交的消息，发送给对应聊天室内所有的客户端
        home_id = str(sender.get_argument('id'))
        user = str(sender.get_argument('user'))
        message = {
            'from': user,
            'message': message,
            'time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        }
        self.trigger(home_id, message)

    def trigger(self, home_id, message):
        if home_id in msg_record:  # 如果存在相应的聊天室
            msg_record[home_id].append(message)
        else:
            msg_record[home_id] = [message]
        # 消息触发器，将最新消息返回给对应聊天室的所有成员
        for client in self.Clients[home_id]:
            client.write_message(json.dumps(message))  # 发送消息


class BaseHandler(tornado.web.RequestHandler):
    # 用于验证用户是否登陆
    def get_current_user(self):
        return self.get_secure_cookie("username")


class LoginHandler(BaseHandler):
    def get(self):
        self.render('login.html')

    def post(self):
        # 获取用户登录的用户名
        username = self.get_argument('username')
        password = self.get_argument('password')
        if pinfo.get(username) == password:
            # 将用户登录的用户名保存在cookie中，安全cookie
            self.set_secure_cookie("username", username)
            self.redirect("/")
        else:
            self.render('error.html')


class RegisterHandler(BaseHandler):
    def get(self):
        self.render('register.html')

    def post(self):
        username = self.get_argument('username')
        password = self.get_argument('password')
        pinfo[username] = password
        self.render('success.html')


class roomChooseHandler(BaseHandler):
    # 主页，选择进入聊天室
    @tornado.web.authenticated
    def get(self, *args, **kwargs):
        self.render('index.html',
                    chatHomeList=chattingRoomList,
                    session=self.current_user)

    def post(self, *args, **kwargs):
        # 创建新的聊天室
        homeDict = {}
        homeDict["name"] = self.get_argument('chatHomeName')
        homeDict["id"] = len(chattingRoomList) + 1
        homeDict["creater"] = self.current_user
        chattingRoomList.append(homeDict)
        self.render('index.html',
                    chatHomeList=chattingRoomList,
                    session=self.current_user)


class DeleteHandler(BaseHandler):
    def post(self):
        for i in chattingRoomList:
            if i["name"] == self.get_argument('chatHomeName'):
                if i["creater"] == self.current_user:
                    chattingRoomList.remove(i)
                    break
                else:
                    self.render("deleteError.html")
        self.render('index.html', chatHomeList=chattingRoomList, session=self.current_user)


class LogoutHandler(BaseHandler):
    # 用于用户退出登录
    def post(self):
        if self.get_argument("logout", None):
            self.clear_cookie("username")
        self.redirect("/login")


class roomHandler(BaseHandler):
    # 聊天室， 获取主页选择聊天室跳转的get信息渲染页面
    @tornado.web.authenticated
    def get(self, *args, **kwargs):
        home_id = self.get_argument('id')  # 聊天室id
        home_name = self.get_argument('name')  # 聊天室名称
        user = self.get_argument('user')  # 用户

        msgs = []
        # 恢复聊天记录
        if home_id in msg_record:
            flag = 0
            for rec in msg_record[home_id]:
                # 开始恢复聊天记录的地方
                if rec['from'] == 'system' and rec['message'] == user + ' 加入' + '聊天室 ' + home_name:
                    flag = 1
                    msgs.append(rec)
                    continue
                # 停止恢复聊天记录的地方
                if rec['from'] == 'system' and rec['message'] == user + ' 离开' + '聊天室 ' + home_name:
                    flag = 0
                    msgs.append(rec)
                    continue
                # 将聊天记录添加进msgs
                if flag == 1:
                    msgs.append(rec)
        self.render('home.html', id=home_id, user=user, name=home_name, msgs=msgs, users=users)


class newClient(tornado.websocket.WebSocketHandler):
    # websocket的相关处理
    def open(self):
        name = str(self.get_argument('name'))
        self.write_message(json.dumps({'time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())),  # 记录时间
                                       'from': 'system', 'message': '欢迎来到聊天室 {}'.format(name)}))  # 向新加入用户发送首次消息
        self.application.chathome.add_client(self)  # 添加新的客户端连接

    def on_close(self):
        self.application.chathome.del_client(self)  # 删除客户端连接

    def on_message(self, message):
        self.application.chathome.send_msg(self, message)  # 处理客户端提交的最新消息


class Application(tornado.web.Application):
    def __init__(self):
        self.chathome = ChattingRoom()
        handlers = [
            (r'/', roomChooseHandler),
            (r'/login', LoginHandler),
            (r'/home', roomHandler),
            (r'/newClient', newClient),
            (r'/logout', LogoutHandler),
            (r'/delete', DeleteHandler),
            (r'/register', RegisterHandler)
        ]
        settings = {
            'template_path': 'templates',
            'static_path': 'static',
            "cookie_secret": "bZJc2sWbQLKos6GkHn/VB9oXwQt8S0R0kRvJ5/xJ89E=",
            "login_url": "/login"
        }
        tornado.web.Application.__init__(self, handlers, **settings)


if __name__ == '__main__':
    tornado.options.parse_command_line()
    server = tornado.httpserver.HTTPServer(Application())
    server.listen(8000)
    print("Tornado server is ready for service: http://localhost:8000/\r")
    tornado.ioloop.IOLoop.instance().start()
