from tornado.web import Application, RequestHandler, url
from tornado.ioloop import IOLoop
import os
import random

award = {"1": 1, "2": 1, "3": 1}
name = []
fname = []
sname = []
tname = []


class IndexHandler(RequestHandler):
    def get(self):
        self.render("index.html")

    def post(self):
        award["1"] = int(self.get_argument("firstnumber"))
        award["2"] = int(self.get_argument("secondnumber"))
        award["3"] = int(self.get_argument("thirdnumber"))
        lists = self.get_argument("peoplelist")
        lists = lists.split()
        for l in lists:
            name.append(l)
        self.redirect("/start")


class resultHandler(RequestHandler):
    def get(self):
        self.render("start.html", award=award, fname=fname, sname=sname, tname=tname)

    def post(self):
        one = self.get_argument("onenumber")
        two = self.get_argument("twonumber")
        three = self.get_argument("threenumber")
        print(name)
        if one.isdigit():
            for i in range(int(one)):
                x = random.randint(0, len(name) - 1)
                fname.append(name[x])
                name.remove(name[x])
            award["1"] = award["1"] - int(one)
        if two.isdigit():
            for i in range(int(two)):
                x = random.randint(0, len(name) - 1)
                sname.append(name[x])
                name.remove(name[x])
            award["2"] = award["2"] - int(two)
        if three.isdigit():
            for i in range(int(three)):
                x = random.randint(0, len(name) - 1)
                tname.append(name[x])
                name.remove(name[x])
            award["3"] = award["3"] - int(three)
        self.render("start.html", award=award, fname=fname, sname=sname, tname=tname)


app = Application(
    [
        (r"/", IndexHandler),
        (r"/start", resultHandler),
    ],template_path=os.path.join(os.path.dirname(__file__),'templates')
)
app.listen(8000)
IOLoop.current().start()
