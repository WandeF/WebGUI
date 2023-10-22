from tornado.web import Application
from tornado.httpserver import HTTPServer

import argparse
import yaml
import os.path
import tornado.web
import json
import signal
import sys
import subprocess


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")


class DataHandler(tornado.web.RequestHandler):
    def get(self):
        with open(self.application.output_path+'/topo.json', "r") as file:
            data = json.load(file)

        # 转换数据格式以适应vis-network
        nodes = [{"id": node["id"], "label": node["id"]} for node in data["nodes"]]
        edges = [{"from": link["source"], "to": link["target"]} for link in data["links"]]

        self.write({"nodes": nodes, "edges": edges})


class App(Application):
    def __init__(self, output_path):
        self.output_path = output_path
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


def signal_handler(sig, frame):
    print("\nCaught interrupt signal. Cleaning up...")
    try:
        # 获取占用端口8000的进程的PID
        cmd = "lsof -t -i:8000"
        pid = subprocess.check_output(cmd, shell=True).decode('utf-8').strip()
        if pid:
            # 杀死该进程
            os.kill(int(pid), signal.SIGKILL)
            print(f"Killed process with PID {pid} on port 8000.")
        else:
            print("No process found on port 8000.")
    except Exception as e:
        print(f"Error killing process on port 8000: {e}")

    sys.exit(0)


def get_data_from_yaml(intermediate_path):
    with open(intermediate_path, 'r') as file:
        data = yaml.safe_load(file)
        return data.get('output_path', None)


def run_server():
    # 设置命令行参数解析
    parser = argparse.ArgumentParser(description="Run the webgui application.")
    parser.add_argument("intermediate_path", help="Path to the intermediate yaml file.")
    args = parser.parse_args()

    output_path = get_data_from_yaml(args.intermediate_path)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGTSTP, signal_handler)

    app = App(output_path)
    server = HTTPServer(app)
    server.listen(8000)
    print('Server started at http://localhost:8000')
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    run_server()
