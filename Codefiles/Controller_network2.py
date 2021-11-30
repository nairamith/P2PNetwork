import eventlet
import socketio
from threading import Thread, Event
import time
from itertools import groupby
import socket

port = 33050
controller_list = [""]

controller2 = "http://localhost:5050"

peer_ip = "localhost"
peer_port = 33000
section = "T"

peer_host = "http://" + peer_ip + ":" + str(peer_port)

sio_client = socketio.Client()
sio_client_controller = socketio.Client()

sio_server = socketio.Server()
app = socketio.WSGIApp(sio_server, static_files={
    '/': {'content_type': 'text/html', 'filename': 'index.html'}
})

node_list = [{'id': 'c1', 'supernode': 3, 'purpose': 'F'}]
super_node_list = []
cluster_max_count = 5
lane_list = [1, 2, 3, 4]

dict = {"L": 70, "M": 60}


def add_node(id, supernode, purpose, lane):
    node_list.append({'id': id, 'supernode': supernode, 'purpose': purpose, "lane": lane})


def create_cluster_object(supernode, count, purpose, lane):
    return {"supernode": supernode, "count": count, "purpose": purpose, "lane": lane}


def add_node_to_cluster(supernode, num):
    list(filter(lambda node: node["supernode"] == supernode, super_node_list))[0]["count"] += num


def add_cluster(supernode, count, purpose, lane):
    super_node_list.append(create_cluster_object(supernode, count, purpose, lane))


def get_cluster_list_with_purpose(purpose):
    return list(filter(lambda node: node["purpose"] == purpose and node["count"] < cluster_max_count, super_node_list))


# ToDo: add filter depending on coordinates
def get_vacant_supernode(id, purpose):
    vacant_list = get_cluster_list_with_purpose(purpose)
    if len(vacant_list) == 0:
        return {'supernode': id, 'count': 1, 'purpose': purpose}
    else:
        return get_cluster_list_with_purpose(purpose)[0]


# Connection Message
@sio_server.event
def connect(sid, environ):
    print('connect ', sid)


# Disconnection Message
@sio_server.event
def disconnect(sid):
    print('disconnect ', sid)


#  Response to the register request sent by the nodes
@sio_server.event
def register(sid, data):
    print("=======================================================")
    print("Received registration request from ", data["id"])
    print("=======================================================")
    supernode_object = get_vacant_supernode(data["id"], data["purpose"])
    supernode = supernode_object["supernode"]
    add_node(data["id"], purpose=data["purpose"], supernode=supernode, lane=data["lane"])
    is_node_super = 0
    lane = data["lane"]

    if supernode == data["id"]:
        is_node_super = 1
        lane = get_less_active_lane()
        add_cluster(data["id"], 1, data["purpose"], lane)
    else:
        add_node_to_cluster(supernode, 1)
        lane = supernode_object["lane"]

    sio_client.connect(data["id"])
    sio_client.emit("cluster_info",
                    {"supernode": supernode, "is_super": is_node_super, "lane": lane})
    sio_client.sleep(1)
    sio_client.disconnect()


# Function to start listening on the given post
def serve_app(_sio, _app):
    app = socketio.Middleware(_sio, _app)
    eventlet.wsgi.server(eventlet.listen(('', port)), app)


thread_listening = Thread()
thread_listening = Thread(target=serve_app, args=(sio_server, app))
thread_listening.daemon = True
thread_listening.start()


@sio_server.event
def heart_beats(sid, data):
    print("Received heartbeats")
    list(filter(lambda node: node["supernode"] == data["id"], super_node_list))[0]["count"] = data["cluster_count"]
    list(filter(lambda node: node["supernode"] == data["id"], super_node_list))[0]["cluster_speed"] = data[
        "cluster_speed"]
    send_super_node_list(data["id"])


@sio_server.event
def peer_network_details(sid, data):
    print("Received peer network details")
    print(data)

    dict[data["purpose"]] = data["speed"]


sio_client_supernode = socketio.Client()


def send_super_node_list(host):
    print("==================================================")
    print("============Sending supernode List================")
    print("==================================================")
    sio_client_supernode.connect(host)
    sio_client_supernode.emit("supernodes", super_node_list)
    time.sleep(2)
    sio_client_supernode.disconnect()


def get_less_active_lane():
    lane_tuple = [(super_node["lane"], super_node["count"]) for super_node in super_node_list]
    lane_dict = {}
    for lane in lane_list:
        lane_dict[lane] = 0

    for (k, v) in lane_tuple:
        lane_dict[k] = v

    lane_agg_list = []
    for i, g in groupby(sorted(lane_dict.items()), key=lambda x: x[0]):
        lane_agg_list.append([i, sum(v[1] for v in g)])

    return min(lane_agg_list, key=lambda lane: lane[1])[0]


sio_client_supernode1 = socketio.Client()


def regulate_speed():
    while 1:
        for supernode in super_node_list:
            if supernode["purpose"] in dict:
                print(super_node_list)
                print("=============================================================")
                print("Regulating Node", supernode["supernode"], "with speed", dict[supernode["purpose"]])
                print("=============================================================")
                sio_client_supernode1.connect(url=supernode["supernode"])
                sio_client_supernode1.emit("cluster_speed", {"speed": dict[supernode["purpose"]]})
                time.sleep(1)
                sio_client_supernode1.disconnect()
                time.sleep(4)


thread_speed_control = Thread(target=regulate_speed)
thread_speed_control.daemon = True
thread_speed_control.start()


def send_average_speed():
    purpose_list = list(set([supernode["purpose"] for supernode in super_node_list]))
    print(purpose_list)
    l = {"purpose": section, "count": 0, "speed": 80}
    count = len(list(node_list))
    speed_list = [node["cluster_speed"] for node in
                  list(super_node_list)]
    avg_speed = 70
    if len(speed_list) != 0:
        avg_speed = sum(speed_list) / len(speed_list)

    l = {"purpose": section, "count": count, "speed": avg_speed}

    sio_client_controller.connect(peer_host)
    sio_client_controller.emit("peer_network_details", l)
    time.sleep(2)
    sio_client_controller.disconnect()
    time.sleep(8)


def communicate_with_peer_controller():
    while 1:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((peer_ip, peer_port))
        if result == 0:
            send_average_speed()


thread_controller = Thread()
thread_controller = Thread(target=communicate_with_peer_controller)
thread_controller.daemon = True
thread_controller.start()

while 1:
    ""

# eventlet.wsgi.server(eventlet.listen(('', port)), app)
