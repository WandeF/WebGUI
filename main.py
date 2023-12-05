import pandas
from tornado.web import Application
from tornado.httpserver import HTTPServer
from tornado.ioloop import PeriodicCallback

import argparse
import yaml
import os.path
import tornado.web
import tornado.websocket
import json
import signal
import sys
import subprocess
import viswaternet as vis


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")


class DataHandler(tornado.web.RequestHandler):
    def get(self):
        with open(self.application.output_path + '/topo.json', "r") as file:
            data = json.load(file)

        # 转换数据格式以适应vis-network
        nodes = data["nodes"]
        edges = data["edges"]

        self.write({"nodes": nodes, "edges": edges})


class WebSocketPhyDataHandler(tornado.websocket.WebSocketHandler):
    connections = set()
    nodes = []
    edges = []

    def open(self):
        print("WebSocket opened")
        WebSocketPhyDataHandler.connections.add(self)
        self.topo_generate()
        self.send_data()
        self.periodic_callback = PeriodicCallback(self.send_data, 2000)
        self.periodic_callback.start()

    def on_close(self):
        print("WebSocket closed")
        WebSocketPhyDataHandler.connections.remove(self)
        if hasattr(self, 'periodic_callback') and self.periodic_callback:
            self.periodic_callback.stop()

    def topo_generate(self):
        model = vis.VisWNModel(self.application.inp_path)

        pos_dict = model.model["pos_dict"]
        pipe_list = model.model["pipe_list"]
        pump_list = model.model["G_list_pumps_only"]
        pump_name = model.model['wn'].pump_name_list
        valves_list = model.model["G_list_valves_only"]
        valve_names = model.model["valve_names"]
        nodes = []
        # 反转y坐标，原因是在Web中，规定左上角为(0, 0)，y往下是正方向
        for node, coords in pos_dict.items():
            x, y = coords
            pos_dict[node] = (x, -y)

        for node_id, pos in pos_dict.items():
            # 根据节点ID前缀设置节点颜色
            if node_id.startswith("T"):
                node_color = "green"
            elif node_id.startswith("R"):
                node_color = "blue"
            else:
                node_color = None

            # 创建节点信息
            node = {"id": node_id, "label": node_id, "x": pos[0], "y": pos[1], "fixed": {"x": True, "y": True}}

            # 如果节点有特定颜色，设置节点颜色
            if node_color:
                node["color"] = {"background": node_color}

            nodes.append(node)

        # 转换边，将管道列表转换为vis.js需要的格式
        WebSocketPhyDataHandler.edges = [
            {"from": pipe[0], "to": pipe[1], "smooth": {"type": "continuous", "midPoint": 0.5}} for pipe in
            pipe_list]

        # 将泵和阀的连接信息添加到边的列表中，并在边上添加一个新的节点
        for i in range(len(pump_list)):
            # 添加新节点
            node_id = pump_name[i]

            # 找到两个节点的坐标
            node1_coords = pos_dict.get(pump_list[i][0], (0, 0))
            node2_coords = pos_dict.get(pump_list[i][1], (0, 0))

            # 计算平均值
            x = (node1_coords[0] + node2_coords[0]) / 2
            y = (node1_coords[1] + node2_coords[1]) / 2

            node = {"id": node_id, "label": node_id, "x": x, "y": y, "fixed": {"x": True, "y": True},
                    "color": {"background": "lightblue"}}
            nodes.append(node)

        for i in range(len(valves_list)):
            # 添加新节点
            node_id = valve_names[i]

            # 找到两个节点的坐标
            node1_coords = pos_dict.get(valves_list[i][0], (0, 0))
            node2_coords = pos_dict.get(valves_list[i][1], (0, 0))

            # 计算平均值
            x = (node1_coords[0] + node2_coords[0]) / 2
            y = (node1_coords[1] + node2_coords[1]) / 2

            node = {"id": node_id, "label": node_id, "x": x, "y": y, "fixed": {"x": True, "y": True},
                    "color": {"background": "yellow"}}
            nodes.append(node)
        WebSocketPhyDataHandler.nodes = nodes

    def send_data(self):
        csv_path = self.application.output_path + '/ground_truth.csv'
        all_data = pandas.read_csv(csv_path)

        # 获取每列的最新值
        latest_data = {col: all_data[col].iloc[-1] for col in all_data.columns}
        for node in WebSocketPhyDataHandler.nodes:
            if node["id"].startswith("T"):
                level = latest_data[node["id"] + "_LEVEL"]
                node["level"] = level
                node["type"] = 'Tank'
            elif node["id"].startswith("J"):
                level = latest_data[node["id"] + "_LEVEL"]
                node["level"] = level
                node["type"] = 'Junction'
            elif node["id"].startswith("V"):
                status = latest_data[node["id"] + "_STATUS"]
                flow = latest_data[node["id"] + "_FLOW"]
                node["status"] = status
                node["flow"] = flow
                node["type"] = 'Vavle'
            elif node["id"].startswith("PU"):
                status = latest_data[node["id"] + "_STATUS"]
                flow = latest_data[node["id"] + "_FLOW"]
                node["status"] = status
                node["flow"] = flow
                node["type"] = 'PU'
            elif node["id"].startswith("v"):
                status = latest_data[node["id"] + "_STATUS"]
                flow = latest_data[node["id"] + "_FLOW"]
                node["status"] = status
                node["flow"] = flow
                node["type"] = 'Vavle'

        self.write_message({"nodes": WebSocketPhyDataHandler.nodes, "edges": WebSocketPhyDataHandler.edges})


# class PhyDataHandler(tornado.web.RequestHandler):
#     def get(self):
#         model = vis.VisWNModel(self.application.inp_path)
#
#         pos_dict = model.model["pos_dict"]
#         pipe_list = model.model["pipe_list"]
#         pump_list = model.model["G_list_pumps_only"]
#         valves_list = model.model["G_list_valves_only"]
#         valve_names = model.model["valve_names"]
#
#         # 反转y坐标，原因是在Web中，规定左上角为(0, 0)，y往下是正方向
#         for node, coords in pos_dict.items():
#             x, y = coords
#             pos_dict[node] = (x, -y)
#
#         nodes = []
#
#         for node_id, pos in pos_dict.items():
#             # 根据节点ID前缀设置节点颜色
#             if node_id.startswith("T"):
#                 node_color = "green"
#             elif node_id.startswith("R"):
#                 node_color = "blue"
#             else:
#                 node_color = None
#
#             # 创建节点信息
#             node = {"id": node_id, "label": node_id, "x": pos[0], "y": pos[1], "fixed": {"x": True, "y": True}}
#
#             # 如果节点有特定颜色，设置节点颜色
#             if node_color:
#                 node["color"] = {"background": node_color}
#
#             nodes.append(node)
#
#         # 转换边，将管道列表转换为vis.js需要的格式
#         edges = [{"from": pipe[0], "to": pipe[1], "smooth": {"type": "continuous", "midPoint": 0.5}} for pipe in
#                  pipe_list]
#
#         # 将泵和阀的连接信息添加到边的列表中，并在边上添加一个新的节点
#         for i in range(len(pump_list)):
#             # 添加新节点
#             node_id = f"PU{i + 1}"
#
#             # 找到两个节点的坐标
#             node1_coords = pos_dict.get(pump_list[i][0], (0, 0))
#             node2_coords = pos_dict.get(pump_list[i][1], (0, 0))
#
#             # 计算平均值
#             x = (node1_coords[0] + node2_coords[0]) / 2
#             y = (node1_coords[1] + node2_coords[1]) / 2
#
#             node = {"id": node_id, "label": node_id, "x": x, "y": y, "fixed": {"x": True, "y": True},
#                     "color": {"background": "lightblue"}}
#             nodes.append(node)
#
#         for i in range(len(valves_list)):
#             # 添加新节点
#             node_id = valve_names[i]
#
#             # 找到两个节点的坐标
#             node1_coords = pos_dict.get(valves_list[i][0], (0, 0))
#             node2_coords = pos_dict.get(valves_list[i][1], (0, 0))
#
#             # 计算平均值
#             x = (node1_coords[0] + node2_coords[0]) / 2
#             y = (node1_coords[1] + node2_coords[1]) / 2
#
#             node = {"id": node_id, "label": node_id, "x": x, "y": y, "fixed": {"x": True, "y": True},
#                     "color": {"background": "yellow"}}
#             nodes.append(node)
#
#         # 将节点和边的信息以JSON格式返回给前端
#         self.write({"nodes": nodes, "edges": edges})


class App(Application):
    def __init__(self, data):
        self.output_path = data[0]
        self.inp_path = data[1]
        handlers = [
            (r"/", MainHandler),
            (r"/getdata", DataHandler),
            (r"/getphydata", WebSocketPhyDataHandler)
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
        yaml_data = yaml.safe_load(file)
        data = [yaml_data.get('output_path', None), yaml_data.get('inp_file', None)]
        return data


def run_server():
    # 设置命令行参数解析
    parser = argparse.ArgumentParser(description="Run the webgui application.")
    parser.add_argument("intermediate_path", help="Path to the intermediate yaml file.")
    args = parser.parse_args()

    data = get_data_from_yaml(args.intermediate_path)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGTSTP, signal_handler)

    app = App(data)
    server = HTTPServer(app)
    server.listen(8000)
    print('Server started at http://localhost:8000')
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    run_server()
