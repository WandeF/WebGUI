from tornado.web import Application
from tornado.httpserver import HTTPServer

import os.path
import tornado.web
import json

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")


class DataHandler(tornado.web.RequestHandler):
    def get(self):
        with open("topo.json", "r") as f:
            data = json.load(f)

        # 转换数据格式以适应vis-network
        nodes = [{"id": node["id"], "label": node["id"]} for node in data["nodes"]]
        edges = [{"from": link["source"], "to": link["target"]} for link in data["links"]]

        self.write({"nodes": nodes, "edges": edges})


class App(Application):
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/getdata", DataHandler),
        ]
        settings = dict(
            debug=True,
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            template_path=os.path.join(os.path.dirname(__file__), "templates")
        )
        Application.__init__(self, handlers, **settings)


if __name__ == "__main__":
    app = App()
    print(app)
    server = HTTPServer(app)
    server.listen(8000)
    print('http://localhost:8000')
    tornado.ioloop.IOLoop.current().start()
