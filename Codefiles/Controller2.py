import eventlet
import socketio

sio_client = socketio.Client()
sio_server = socketio.Server()
app = socketio.WSGIApp(sio_server, static_files={
    '/': {'content_type': 'text/html', 'filename': 'index.html'}
})

node_list = [{'id': 'c1', 'supernode': 3, 'purpose': 'F'}]
super_node_list = [{'supernode': 'c1', 'count': 3, 'purpose': 'F'}]
cluster_max_count = 5
port=3000


def add_node(id, supernode, purpose):
    node_list.append({'id': id, 'supernode': supernode, 'purpose': purpose})


def create_cluster_object(supernode, count, purpose):
    return {"supernode": supernode, "count": count, "purpose": purpose}


def add_node_to_cluster(supernode, num):
    list(filter(lambda node: node["supernode"] == "c1", super_node_list))[0]["count"] += num


def add_cluster(supernode, count, purpose):
    super_node_list.append(create_cluster_object(supernode, count, purpose))


def get_cluster_list_with_purpose(purpose):
    return list(filter(lambda node: node["purpose"] == purpose and node["count"] < cluster_max_count, super_node_list))


# ToDo: add filter depending on coordinates
def get_vacant_supernode(id, purpose):
    vacant_list = get_cluster_list_with_purpose(purpose)
    if len(vacant_list) == 0:
        return {'supernode': id, 'count': 1, 'purpose': purpose}
    else:
        return get_cluster_list_with_purpose(purpose)[0]


# # Accept/Reject registration
# #
# @sio_server.event
# def supernode_registration(sid, data):
#     add_cluster(data["ID"], 1, data["purpose"])
#     print(super_node_list)
#     sio_client.connect(data["ID"])
#     sio_client.emit("registration_response", {"is_super_node": True})
#     sio_client.disconnect()


# Connection Message
@sio_server.event
def connect(sid, environ):
    print('connect ', sid)


# # Respond to supernodes list request from Nodes
# @sio_server.event
# def request_supernodes(sid, data):
#     print(data)
#     print(get_cluster_list_with_purpose("F"))
#     sio_client.connect(data["id"])
#     sio_client.emit("cluster_list", get_cluster_list_with_purpose(data))
#     sio_client.disconnect()


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
    supernode = get_vacant_supernode(data["id"], data["purpose"])["supernode"]
    add_node(data["id"], purpose=data["purpose"], supernode=supernode)
    is_node_super = 0
    if supernode == data["id"]:
        is_node_super = 1
        add_cluster(data["id"], 1, data["purpose"])
    else:
        add_node_to_cluster(supernode, 1)

    sio_client.connect(data["id"])
    sio_client.emit("cluster_info", {"supernode": supernode, "is_super" : is_node_super})
    sio_client.sleep(1)
    sio_client.disconnect()


@sio_server.event
def controller_info(port,count):
    print(f"The number of nodes for server at port {port} are {count} ")



if __name__ == '__main__':
    eventlet.wsgi.server(eventlet.listen(('', port)), app)
