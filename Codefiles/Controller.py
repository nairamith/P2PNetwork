import eventlet
import socketio
from threading import Thread, Event
import time

port = 5000
controller_list = [""]


sio_client = socketio.Client()
sio_client_controller = socketio.Client()

sio_server = socketio.Server()
app = socketio.WSGIApp(sio_server, static_files={
    '/': {'content_type': 'text/html', 'filename': 'index.html'}
})

node_list = [{'id': 'c1', 'supernode': 3, 'purpose': 'F'}]
super_node_list = [{'supernode': 'c1', 'count': 3, 'purpose': 'F'}]
cluster_max_count = 5




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
    print("--------------------------------------")
    print(data["id"])
    print(supernode)
    print("--------------------------------------")
    if supernode == data["id"]:
        is_node_super = 1
        add_cluster(data["id"], 1, data["purpose"], data["lane"])
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
    list(filter(lambda node: node["supernode"] == data["id"], super_node_list))[0]["count"] = data["cluster_count"]
    list(filter(lambda node: node["supernode"] == data["id"], super_node_list))[0]["cluster_speed"] = data["cluster_speed"]
    send_super_node_list(data["id"])

def send_super_node_list(host):
    sio_client_supernode = socketio.Client()
    sio_client_supernode.connect(host)
    sio_client_supernode.emit("supernodes", super_node_list)
    sio_client_supernode.disconnect()


def send_average_speed():
    while 1:
        purpose_list = list(set([supernode["purpose"] for supernode in super_node_list]))
        l = [{"purpose": "dummy", "count": 0}]
        for purpose in purpose_list:
            count = len(list(filter(lambda node: node["purpose"] == purpose, node_list)))
            l.append({"purpose": purpose, "count": count})
        for controller in controller_list:
            print("******************")
            print(l)
        time.sleep(5)



thread_controller = Thread()
thread_controller = Thread(target=send_average_speed)
thread_controller.daemon = True
thread_controller.start()

while 1:
    a=2
# eventlet.wsgi.server(eventlet.listen(('', port)), app)
