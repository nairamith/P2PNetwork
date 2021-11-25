import eventlet
import socketio

sio_client = socketio.Client()
sio_server = socketio.Server()
app = socketio.WSGIApp(sio_server, static_files={
    '/': {'content_type': 'text/html', 'filename': 'index.html'}
})

nodeList = [{'supernode': 'c1', 'count': 3, 'purpose': 'F'}, {'supernode': 'c2', 'count': 3, 'purpose': 'F'}]
cluster_max_count = 5


def create_cluster_object(supernode, count, purpose):
    return {"supernode": supernode, "count": count, "purpose": purpose}


def add_node_to_cluster(supernode, num):
    list(filter(lambda node: node["supernode"] == "c1", nodeList))[0]["count"] += num


def add_cluster(supernode, count, purpose):
    nodeList.append(create_cluster_object(supernode, count, purpose))


@sio_server.event
def supernode_registration(sid, data):
    add_cluster(data["ID"], 1, data["purpose"])
    print(nodeList)
    sio_client.connect(data["ID"])
    sio_client.emit("registration_response", {"is_super_node": True})
    sio_client.disconnect()



def get_cluster_list_with_purpose(purpose):
    return list(filter(lambda node: node["purpose"] == purpose and node["count"] < cluster_max_count, nodeList))


@sio_server.event
def connect(sid, environ):
    print('connect ', sid)


@sio_server.event
def SensorReading(sid, data):
    print('message ', data, sid)


@sio_server.event
def request_supernodes(sid, data):
    print(data)
    print(get_cluster_list_with_purpose("F"))
    sio_client.connect('http://localhost:5001')
    sio_client.emit("cluster_list", get_cluster_list_with_purpose(data))
    sio_client.disconnect()


@sio_server.event
def disconnect(sid):
    print('disconnect ', sid)


if __name__ == '__main__':
    eventlet.wsgi.server(eventlet.listen(('', 5000)), app)
